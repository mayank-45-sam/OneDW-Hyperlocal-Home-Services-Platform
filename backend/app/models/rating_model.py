"""
MongoDB document shape for the 'ratings' collection.
"""
from datetime import datetime, timezone
from typing import Optional


def build_rating_document(
    booking_id: str,
    customer_id: str,
    worker_id: str,
    stars: int,
    comment: Optional[str],
) -> dict:
    """Construct a new rating document ready for insertion."""
    return {
        "booking_id": booking_id,
        "customer_id": customer_id,
        "worker_id": worker_id,
        "stars": stars,
        "comment": comment or "",
        "created_at": datetime.now(timezone.utc),
    }
