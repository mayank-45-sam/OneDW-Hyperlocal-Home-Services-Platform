"""
MongoDB document shape for the 'users' collection.
This is a plain dict-shaping helper, not an ORM model, since Motor is schemaless.
"""
from datetime import datetime, timezone


def build_user_document(name: str, email: str, phone: str, hashed_password: str, role: str) -> dict:
    """Construct a new user document ready for insertion into MongoDB."""
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "password": hashed_password,
        "role": role,
        "is_verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }