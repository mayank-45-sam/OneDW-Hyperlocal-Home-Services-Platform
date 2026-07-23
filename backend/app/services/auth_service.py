"""
Business logic for authentication: registration and login.
Keeps routers thin — routers only handle HTTP concerns.
"""
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from app.models.user_model import build_user_document
from app.utils.security import hash_password, verify_password, create_access_token


async def register_user(db: AsyncIOMotorDatabase, payload: UserRegisterSchema) -> dict:
    """Register a new user. Raises 409 if the email is already taken."""
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user_doc = build_user_document(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hashed_pw,
        role=payload.role,
    )
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token(data={"sub": user_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "role": payload.role,
        },
    }


async def login_user(db: AsyncIOMotorDatabase, payload: UserLoginSchema) -> dict:
    """Authenticate a user and issue a JWT. Raises 401 on invalid credentials."""
    user = await db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user_id = str(user["_id"])
    token = create_access_token(data={"sub": user_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"],
        },
    }