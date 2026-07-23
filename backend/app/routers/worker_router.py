"""
Worker endpoints — profile management, location, and job discovery.
"""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.worker_schema import (
    WorkerProfileUpdateSchema,
    WorkerLocationSchema,
    WorkerResponseSchema,
)
from app.services import worker_service
from app.database.connection import get_database
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/worker", tags=["Workers"])


@router.get("/profile", response_model=WorkerResponseSchema)
async def get_my_worker_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get the current worker's profile."""
    return await worker_service.get_worker_profile(db, current_user["_id"])


@router.put("/profile", response_model=WorkerResponseSchema)
async def update_my_worker_profile(
    payload: WorkerProfileUpdateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Update skills, experience, rate, and availability."""
    return await worker_service.update_worker_profile(db, current_user["_id"], payload)


@router.post("/location")
async def update_location(
    payload: WorkerLocationSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Update the worker's GPS coordinates."""
    return await worker_service.update_worker_location(db, current_user["_id"], payload)


@router.get("/available-jobs")
async def get_available_jobs(
    service_type: str = Query(None, description="Filter by service type"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get pending service requests available for workers to accept."""
    return await worker_service.get_available_jobs(db, current_user["_id"], service_type)


@router.get("/nearby")
async def get_nearby_workers(
    service_type: str = Query(..., description="Type of service required"),
    customer_lat: float = Query(...),
    customer_lon: float = Query(...),
    radius_km: float = Query(50, description="Search radius in km"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get nearby available workers for a given service type."""
    return await worker_service.get_nearby_workers(
        db, service_type, customer_lat, customer_lon, radius_km
    )
