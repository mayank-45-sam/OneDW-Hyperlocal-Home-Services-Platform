"""
Booking endpoints — create, retrieve, and update booking status.
"""
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.booking_schema import (
    BookingCreateSchema,
    BookingStatusUpdateSchema,
    BookingResponseSchema,
)
from app.services import booking_service
from app.database.connection import get_database
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/booking", tags=["Bookings"])


@router.post("/create", response_model=BookingResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Create a new booking for a service request."""
    return await booking_service.create_booking(db, payload, current_user["_id"])


@router.get("/my-bookings", response_model=list[BookingResponseSchema])
async def get_my_bookings(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get all bookings for the logged-in customer."""
    return await booking_service.get_customer_bookings(db, current_user["_id"])


@router.get("/worker-bookings", response_model=list[BookingResponseSchema])
async def get_worker_bookings(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get all bookings assigned to the logged-in worker."""
    return await booking_service.get_worker_bookings(db, current_user["_id"])


@router.get("/{booking_id}", response_model=BookingResponseSchema)
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Fetch a single booking by ID."""
    return await booking_service.get_booking_by_id(db, booking_id, current_user["_id"])


@router.put("/{booking_id}/status", response_model=BookingResponseSchema)
async def update_booking_status(
    booking_id: str,
    payload: BookingStatusUpdateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Advance a booking to the next status step."""
    return await booking_service.update_booking_status(
        db, booking_id, payload, current_user["_id"]
    )
