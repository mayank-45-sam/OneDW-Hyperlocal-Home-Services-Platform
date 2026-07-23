"""
Pydantic schemas for worker profiles, location updates, and API responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WorkerProfileUpdateSchema(BaseModel):
    """Fields that a worker can update on their profile."""
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    hourly_rate: Optional[float] = None
    bio: Optional[str] = None
    is_available: Optional[bool] = None


class WorkerLocationSchema(BaseModel):
    """Payload for a worker updating their current GPS location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class WorkerResponseSchema(BaseModel):
    """Public worker profile returned from the API."""
    id: str
    name: str
    email: str
    phone: str
    skills: List[str]
    experience_years: int
    hourly_rate: float
    bio: str
    is_available: bool
    average_rating: float
    total_jobs: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
