"""
Pydantic schemas for bookings — creation, status updates, and API responses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BookingCreateSchema(BaseModel):
    request_id: str = Field(..., description="ID of the service request being booked")
    worker_id: str = Field(..., description="ID of the assigned worker")


class BookingStatusUpdateSchema(BaseModel):
    status: str = Field(
        ...,
        description="One of: pending, accepted, worker_on_the_way, started, completed, cancelled",
    )


class BookingResponseSchema(BaseModel):
    id: str
    request_id: str
    customer_id: str
    worker_id: str
    service_type: str
    location: str
    preferred_date: str
    preferred_time: str
    status: str
    worker_name: Optional[str] = None
    worker_phone: Optional[str] = None
    worker_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
