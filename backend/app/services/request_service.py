"""
Business logic for customer service requests.
Handles creation, retrieval, update, and deletion — all scoped to the
requesting customer for authorization safety.
"""
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

from app.schemas.request_schema import RequestCreateSchema, RequestUpdateSchema
from app.models.request_model import build_request_document


def _serialize_request(doc: dict) -> dict:
    """Convert a MongoDB document into a JSON-safe response dict."""
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


def _to_object_id(request_id: str) -> ObjectId:
    """Safely convert a string to ObjectId, raising 400 on bad format."""
    try:
        return ObjectId(request_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID format.",
        )


async def create_request(
    db: AsyncIOMotorDatabase, payload: RequestCreateSchema, customer_id: str
) -> dict:
    """Create a new service request for the authenticated customer."""
    doc = build_request_document(payload.model_dump(), customer_id)
    result = await db.requests.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_request(doc)


async def get_customer_requests(db: AsyncIOMotorDatabase, customer_id: str) -> list[dict]:
    """Fetch all requests belonging to the authenticated customer, newest first."""
    cursor = db.requests.find({"customer_id": customer_id}).sort("created_at", -1)
    requests = await cursor.to_list(length=None)
    return [_serialize_request(r) for r in requests]


async def get_request_by_id(
    db: AsyncIOMotorDatabase, request_id: str, customer_id: str
) -> dict:
    """Fetch a single request by ID, ensuring it belongs to the requester."""
    obj_id = _to_object_id(request_id)
    doc = await db.requests.find_one({"_id": obj_id, "customer_id": customer_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found.",
        )
    return _serialize_request(doc)


async def update_request(
    db: AsyncIOMotorDatabase,
    request_id: str,
    payload: RequestUpdateSchema,
    customer_id: str,
) -> dict:
    """Update fields on an existing request. Only the owner can update it."""
    obj_id = _to_object_id(request_id)

    existing = await db.requests.find_one({"_id": obj_id, "customer_id": customer_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found.",
        )

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update.",
        )

    await db.requests.update_one({"_id": obj_id}, {"$set": update_data})
    updated_doc = await db.requests.find_one({"_id": obj_id})
    return _serialize_request(updated_doc)


async def delete_request(
    db: AsyncIOMotorDatabase, request_id: str, customer_id: str
) -> None:
    """Delete a request. Only the owner can delete it."""
    obj_id = _to_object_id(request_id)

    result = await db.requests.delete_one({"_id": obj_id, "customer_id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found.",
        )