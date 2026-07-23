"""
Pydantic schemas for user registration, login, and API responses.
Schemas define the request/response contract — separate from DB models.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    role: Literal["customer", "worker"] = "customer"


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    role: str


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseSchema