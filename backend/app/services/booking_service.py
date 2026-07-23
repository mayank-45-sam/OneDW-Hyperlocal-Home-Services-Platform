"""
Business logic for booking lifecycle management.
Handles creation, retrieval, and status transitions.
"""
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone

from app.schemas.booking_schema import BookingCreateSchema, BookingStatusUpdateSchema
from app.models.booking_model import build_booking_document

VALID_TRANSITIONS = {
    "pending": ["accepted", "cancelled"],
    "accepted": ["worker_on_the_way", "cancelled"],
    "worker_on_the_way": ["started", "cancelled"],
    "started": ["completed"],
    "completed": [],
    "cancelled": [],
}


def _to_oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")


def _serialize_booking(doc: dict, worker_info: dict = None) -> dict:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    if worker_info:
        doc["worker_name"] = worker_info.get("name")
        doc["worker_phone"] = worker_info.get("phone")
        doc["worker_rating"] = worker_info.get("average_rating")
    return doc


async def create_booking(
    db: AsyncIOMotorDatabase, payload: BookingCreateSchema, customer_id: str
) -> dict:
    """Create a booking from an accepted service request."""
    # Validate request exists and belongs to customer
    request = await db.requests.find_one(
        {"_id": _to_oid(payload.request_id), "customer_id": customer_id}
    )
    if not request:
        raise HTTPException(status_code=404, detail="Service request not found.")

    if request.get("status") not in ("pending", "accepted"):
        raise HTTPException(
            status_code=400, detail="Request is already booked or completed."
        )

    # Check worker exists
    worker_user = await db.users.find_one({"_id": _to_oid(payload.worker_id)})
    if not worker_user:
        raise HTTPException(status_code=404, detail="Worker not found.")

    doc = build_booking_document(
        request_id=payload.request_id,
        customer_id=customer_id,
        worker_id=payload.worker_id,
        service_type=request["service_type"],
        location=request["location"],
        preferred_date=request["preferred_date"],
        preferred_time=request["preferred_time"],
    )
    result = await db.bookings.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Mark request as accepted + attach worker
    await db.requests.update_one(
        {"_id": _to_oid(payload.request_id)},
        {"$set": {"status": "accepted", "worker_id": payload.worker_id}},
    )

    worker_profile = await db.workers.find_one({"user_id": payload.worker_id})
    worker_info = {
        "name": worker_user.get("name"),
        "phone": worker_user.get("phone"),
        "average_rating": (worker_profile or {}).get("average_rating", 0.0),
    }
    return _serialize_booking(doc, worker_info)


async def get_customer_bookings(db: AsyncIOMotorDatabase, customer_id: str) -> list[dict]:
    """Get all bookings for the current customer, with worker info."""
    cursor = db.bookings.find({"customer_id": customer_id}).sort("created_at", -1)
    bookings = await cursor.to_list(length=None)
    result = []
    for b in bookings:
        worker_user = await db.users.find_one({"_id": _to_oid(b["worker_id"])})
        worker_profile = await db.workers.find_one({"user_id": b["worker_id"]})
        worker_info = {
            "name": (worker_user or {}).get("name"),
            "phone": (worker_user or {}).get("phone"),
            "average_rating": (worker_profile or {}).get("average_rating", 0.0),
        }
        result.append(_serialize_booking(b, worker_info))
    return result


async def get_worker_bookings(db: AsyncIOMotorDatabase, worker_id: str) -> list[dict]:
    """Get all bookings assigned to the current worker."""
    cursor = db.bookings.find({"worker_id": worker_id}).sort("created_at", -1)
    bookings = await cursor.to_list(length=None)
    return [_serialize_booking(b) for b in bookings]


async def get_booking_by_id(
    db: AsyncIOMotorDatabase, booking_id: str, user_id: str
) -> dict:
    """Fetch a single booking visible to customer or worker."""
    booking = await db.bookings.find_one({"_id": _to_oid(booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking["customer_id"] != user_id and booking["worker_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    worker_user = await db.users.find_one({"_id": _to_oid(booking["worker_id"])})
    worker_profile = await db.workers.find_one({"user_id": booking["worker_id"]})
    worker_info = {
        "name": (worker_user or {}).get("name"),
        "phone": (worker_user or {}).get("phone"),
        "average_rating": (worker_profile or {}).get("average_rating", 0.0),
    }
    return _serialize_booking(booking, worker_info)


async def update_booking_status(
    db: AsyncIOMotorDatabase,
    booking_id: str,
    payload: BookingStatusUpdateSchema,
    user_id: str,
) -> dict:
    """Advance the booking status along valid transition paths."""
    booking = await db.bookings.find_one({"_id": _to_oid(booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking["customer_id"] != user_id and booking["worker_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    current = booking["status"]
    new_status = payload.status
    allowed = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{new_status}'. Allowed: {allowed}",
        )

    await db.bookings.update_one(
        {"_id": _to_oid(booking_id)},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}},
    )

    # Sync status to request
    await db.requests.update_one(
        {"_id": _to_oid(booking["request_id"])},
        {"$set": {"status": new_status}},
    )

    # If completed, increment worker total_jobs
    if new_status == "completed":
        await db.workers.update_one(
            {"user_id": booking["worker_id"]},
            {"$inc": {"total_jobs": 1}},
        )

    updated = await db.bookings.find_one({"_id": _to_oid(booking_id)})
    return _serialize_booking(updated)
