"""
Business logic for customer ratings — submission and aggregation.
"""
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone

from app.schemas.rating_schema import RatingCreateSchema
from app.models.rating_model import build_rating_document


def _to_oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")


def _serialize_rating(doc: dict) -> dict:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


async def create_rating(
    db: AsyncIOMotorDatabase, payload: RatingCreateSchema, customer_id: str
) -> dict:
    """Submit a rating for a completed booking."""
    # Verify the booking exists and belongs to this customer
    booking = await db.bookings.find_one(
        {"_id": _to_oid(payload.booking_id), "customer_id": customer_id}
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Can only rate completed bookings.")

    # Prevent duplicate ratings for the same booking
    existing = await db.ratings.find_one(
        {"booking_id": payload.booking_id, "customer_id": customer_id}
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already rated this booking.")

    doc = build_rating_document(
        booking_id=payload.booking_id,
        customer_id=customer_id,
        worker_id=payload.worker_id,
        stars=payload.stars,
        comment=payload.comment,
    )
    result = await db.ratings.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Recompute worker's average rating
    await _update_worker_average_rating(db, payload.worker_id)

    return _serialize_rating(doc)


async def _update_worker_average_rating(db: AsyncIOMotorDatabase, worker_id: str):
    """Recalculate and persist the worker's average star rating."""
    cursor = db.ratings.find({"worker_id": worker_id})
    all_ratings = await cursor.to_list(length=None)
    if all_ratings:
        avg = sum(r["stars"] for r in all_ratings) / len(all_ratings)
        await db.workers.update_one(
            {"user_id": worker_id},
            {"$set": {"average_rating": round(avg, 2), "updated_at": datetime.now(timezone.utc)}},
        )


async def get_worker_ratings(db: AsyncIOMotorDatabase, worker_id: str) -> list[dict]:
    """Get all ratings for a specific worker."""
    cursor = db.ratings.find({"worker_id": worker_id}).sort("created_at", -1)
    ratings = await cursor.to_list(length=None)
    return [_serialize_rating(r) for r in ratings]


async def get_my_ratings(db: AsyncIOMotorDatabase, customer_id: str) -> list[dict]:
    """Get all ratings submitted by the current customer."""
    cursor = db.ratings.find({"customer_id": customer_id}).sort("created_at", -1)
    ratings = await cursor.to_list(length=None)
    return [_serialize_rating(r) for r in ratings]
