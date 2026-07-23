"""
MongoDB document shape for the 'requests' collection.
"""
from datetime import datetime, timezone


def build_request_document(payload: dict, customer_id: str) -> dict:
    """Construct a new service request document ready for insertion."""
    return {
        "service_type": payload["service_type"],
        "location": payload["location"],
        "latitude": payload["latitude"],
        "longitude": payload["longitude"],
        "description": payload["description"],
        "preferred_date": payload["preferred_date"],
        "preferred_time": payload["preferred_time"],
        "customer_id": customer_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }