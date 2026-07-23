"""
Pydantic schemas for ratings submitted by customers after service completion.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RatingCreateSchema(BaseModel):
    booking_id: str = Field(..., description="ID of the completed booking")
    worker_id: str = Field(..., description="ID of the worker being rated")
    stars: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    comment: Optional[str] = Field(None, max_length=500)


class RatingResponseSchema(BaseModel):
    id: str
    booking_id: str
    customer_id: str
    worker_id: str
    stars: int
    comment: Optional[str] = None
    created_at: datetime
