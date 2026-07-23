"""
Business logic for worker profiles, location, and job management.
"""
import math
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone

from app.schemas.worker_schema import WorkerProfileUpdateSchema, WorkerLocationSchema
from app.models.worker_model import build_worker_profile_document


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates using Haversine formula."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _to_oid(worker_id: str) -> ObjectId:
    try:
        return ObjectId(worker_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid worker ID format.")


def _serialize_worker(user: dict, profile: dict) -> dict:
    """Merge user document + worker profile into a single API response dict."""
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "skills": profile.get("skills", []),
        "experience_years": profile.get("experience_years", 0),
        "hourly_rate": profile.get("hourly_rate", 0.0),
        "bio": profile.get("bio", ""),
        "is_available": profile.get("is_available", True),
        "average_rating": profile.get("average_rating", 0.0),
        "total_jobs": profile.get("total_jobs", 0),
        "latitude": profile.get("latitude"),
        "longitude": profile.get("longitude"),
        "created_at": user.get("created_at"),
    }


async def _ensure_worker_profile(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    """Get worker profile or auto-create it if missing."""
    profile = await db.workers.find_one({"user_id": user_id})
    if profile is None:
        doc = build_worker_profile_document(user_id)
        result = await db.workers.insert_one(doc)
        doc["_id"] = result.inserted_id
        profile = doc
    return profile


async def get_worker_profile(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    """Fetch the current user's worker profile."""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    profile = await _ensure_worker_profile(db, user_id)
    return _serialize_worker(user, profile)


async def update_worker_profile(
    db: AsyncIOMotorDatabase, user_id: str, payload: WorkerProfileUpdateSchema
) -> dict:
    """Update a worker's profile fields."""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.workers.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True,
        )

    profile = await db.workers.find_one({"user_id": user_id})
    return _serialize_worker(user, profile)


async def update_worker_location(
    db: AsyncIOMotorDatabase, user_id: str, payload: WorkerLocationSchema
) -> dict:
    """Update a worker's GPS location."""
    await db.workers.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    return {"message": "Location updated.", "latitude": payload.latitude, "longitude": payload.longitude}


async def get_available_jobs(
    db: AsyncIOMotorDatabase, user_id: str, service_type: str = None, radius_km: float = 50
) -> list[dict]:
    """
    Fetch pending requests that are not yet assigned to a worker.
    Optionally filter by service_type; returns all within radius_km of worker.
    """
    profile = await db.workers.find_one({"user_id": user_id})
    worker_lat = profile.get("latitude") if profile else None
    worker_lon = profile.get("longitude") if profile else None

    query: dict = {"status": "pending", "worker_id": {"$exists": False}}
    if service_type:
        query["service_type"] = {"$regex": service_type, "$options": "i"}

    cursor = db.requests.find(query).sort("created_at", -1)
    requests = await cursor.to_list(length=None)

    result = []
    for req in requests:
        req["id"] = str(req["_id"])
        del req["_id"]

        # Calculate distance if worker has a location
        if worker_lat and worker_lon and req.get("latitude") and req.get("longitude"):
            req["distance_km"] = round(
                _haversine_km(worker_lat, worker_lon, req["latitude"], req["longitude"]), 2
            )
        else:
            req["distance_km"] = None

        result.append(req)

    # Sort by distance if available
    result.sort(key=lambda r: r.get("distance_km") or float("inf"))
    return result


async def get_nearby_workers(
    db: AsyncIOMotorDatabase,
    service_type: str,
    customer_lat: float,
    customer_lon: float,
    radius_km: float = 200,
) -> list[dict]:
    """
    Find available workers with skills matching the service type.
    Returns workers with computed distance_km, sorted by distance.
    Falls back to returning all available workers if no skill match found.
    """
    all_workers = await db.workers.find({"is_available": True}).to_list(length=None)
    service_lower = service_type.lower().strip()

    def _skill_matches(skills: list) -> bool:
        """Broad skill match — checks substrings in both directions."""
        for skill in skills:
            s = skill.lower()
            if service_lower in s or s in service_lower:
                return True
        # Also match first word of service (e.g., "AC" in "AC Repair")
        first_word = service_lower.split()[0]
        return any(first_word in skill.lower() for skill in skills)

    def _build_result(profile: dict, user: dict, dist: float) -> dict:
        return {
            "worker_id": str(user["_id"]),
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "phone": user.get("phone", ""),
            "skills": profile.get("skills", []),
            "experience_years": profile.get("experience_years", 0),
            "hourly_rate": profile.get("hourly_rate", 0.0),
            "bio": profile.get("bio", ""),
            "average_rating": profile.get("average_rating", 0.0),
            "total_jobs": profile.get("total_jobs", 0),
            "latitude": profile.get("latitude"),
            "longitude": profile.get("longitude"),
            "distance_km": round(dist, 2),
            "is_available": profile.get("is_available", True),
        }

    skill_matched = []
    all_available = []

    for profile in all_workers:
        user_id = profile.get("user_id")
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            user = None
        if not user:
            continue

        worker_lat = profile.get("latitude")
        worker_lon = profile.get("longitude")

        if worker_lat and worker_lon:
            dist = _haversine_km(customer_lat, customer_lon, worker_lat, worker_lon)
        else:
            dist = 0  # No location — treat as local/nearby

        entry = _build_result(profile, user, dist)

        # Collect all available workers (for fallback)
        if dist <= radius_km or not (worker_lat and worker_lon):
            all_available.append(entry)

        # Collect only skill-matched workers
        if _skill_matches(profile.get("skills", [])):
            if dist <= radius_km or not (worker_lat and worker_lon):
                skill_matched.append(entry)

    # Use skill-matched if any found, else fall back to all available
    result = skill_matched if skill_matched else all_available

    result.sort(key=lambda w: w["distance_km"])
    return result

