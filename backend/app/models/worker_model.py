"""
MongoDB document shape for the 'workers' collection (extends users).
"""
from datetime import datetime, timezone
from typing import List


def build_worker_profile_document(user_id: str) -> dict:
    """Create a default worker profile linked to a user account."""
    return {
        "user_id": user_id,
        "skills": [],
        "experience_years": 0,
        "hourly_rate": 0.0,
        "bio": "",
        "is_available": True,
        "average_rating": 0.0,
        "total_jobs": 0,
        "latitude": None,
        "longitude": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
