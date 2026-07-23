"""
Service request endpoints — create, list, retrieve, update, and delete
customer requests. All endpoints require a valid JWT.
"""
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.request_schema import (
    RequestCreateSchema,
    RequestUpdateSchema,
    RequestResponseSchema,
)
from app.services import request_service
from app.database.connection import get_database
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/request", tags=["Service Requests"])


@router.post("/create", response_model=RequestResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_service_request(
    payload: RequestCreateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Create a new service request for the logged-in customer."""
    return await request_service.create_request(db, payload, current_user["_id"])


@router.get("/my-requests", response_model=list[RequestResponseSchema])
async def get_my_requests(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """List all service requests raised by the logged-in customer."""
    return await request_service.get_customer_requests(db, current_user["_id"])


@router.get("/{request_id}", response_model=RequestResponseSchema)
async def get_single_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Fetch a single request by its ID."""
    return await request_service.get_request_by_id(db, request_id, current_user["_id"])


@router.put("/{request_id}", response_model=RequestResponseSchema)
async def update_service_request(
    request_id: str,
    payload: RequestUpdateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Update an existing service request."""
    return await request_service.update_request(db, request_id, payload, current_user["_id"])


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Delete a service request."""
    await request_service.delete_request(db, request_id, current_user["_id"])


@router.get("/admin/stats", tags=["Admin"])
async def get_platform_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Return high-level platform statistics (admin use)."""
    total_users = await db.users.count_documents({})
    total_workers = await db.users.count_documents({"role": "worker"})
    total_customers = await db.users.count_documents({"role": "customer"})
    total_requests = await db.requests.count_documents({})
    total_bookings = await db.bookings.count_documents({})
    completed_bookings = await db.bookings.count_documents({"status": "completed"})
    pending_requests = await db.requests.count_documents({"status": "pending"})

    return {
        "total_users": total_users,
        "total_workers": total_workers,
        "total_customers": total_customers,
        "total_requests": total_requests,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "pending_requests": pending_requests,
    }