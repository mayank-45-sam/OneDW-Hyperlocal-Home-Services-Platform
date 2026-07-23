"""
Pydantic schemas for service requests raised by customers.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RequestCreateSchema(BaseModel):
    service_type: str = Field(..., min_length=2, max_length=50)
    location: str = Field(..., min_length=3, max_length=200)
    latitude: float
    longitude: float
    description: str = Field(..., min_length=5, max_length=1000)
    preferred_date: str = Field(..., description="Format: YYYY-MM-DD")
    preferred_time: str = Field(..., description="Format: HH:MM")


class RequestUpdateSchema(BaseModel):
    """All fields optional — only provided fields are updated."""
    service_type: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    status: Optional[str] = None


class RequestResponseSchema(BaseModel):
    id: str
    service_type: str
    location: str
    latitude: float
    longitude: float
    description: str
    preferred_date: str
    preferred_time: str
    customer_id: str
    status: str
    created_at: datetime