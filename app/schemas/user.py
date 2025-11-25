from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


# -----------------------------
# BASE SCHEMA
# -----------------------------
class UserBase(BaseModel):
    username: str
    email: EmailStr


# -----------------------------
# REQUIRED BY TESTS
# -----------------------------
class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserRead(UserBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# YOUR ORIGINAL SCHEMAS
# -----------------------------
class UserResponse(BaseModel):
    """Schema for user response data"""
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "johndoe",
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-08T12:00:00",
                },
            }
        }
    )


class TokenData(BaseModel):
    """Schema for JWT token payload"""
    user_id: Optional[UUID] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe123",
                "password": "SecurePass123",
            }
        }
    )
