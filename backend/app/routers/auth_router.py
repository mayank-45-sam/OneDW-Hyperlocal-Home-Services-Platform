"""
Auth endpoints: register and login.
Thin layer — delegates all logic to the service layer.
"""
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema, TokenResponseSchema
from app.services.auth_service import register_user, login_user
from app.database.connection import get_database

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterSchema, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Register a new customer or worker account."""
    return await register_user(db, payload)


@router.post("/login", response_model=TokenResponseSchema)
async def login(payload: UserLoginSchema, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Authenticate and receive a JWT access token."""
    return await login_user(db, payload)    