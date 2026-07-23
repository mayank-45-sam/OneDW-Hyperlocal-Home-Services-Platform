"""
Rating endpoints — submit and retrieve worker ratings.
"""
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.rating_schema import RatingCreateSchema, RatingResponseSchema
from app.services import rating_service
from app.database.connection import get_database
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/rating", tags=["Ratings"])


@router.post("/create", response_model=RatingResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_rating(
    payload: RatingCreateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Submit a star rating and optional comment for a completed booking."""
    return await rating_service.create_rating(db, payload, current_user["_id"])


@router.get("/worker/{worker_id}", response_model=list[RatingResponseSchema])
async def get_worker_ratings(
    worker_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get all ratings for a specific worker."""
    return await rating_service.get_worker_ratings(db, worker_id)


@router.get("/my-ratings", response_model=list[RatingResponseSchema])
async def get_my_ratings(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get all ratings submitted by the current customer."""
    return await rating_service.get_my_ratings(db, current_user["_id"])
