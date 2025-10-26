# api/v1/schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from api.v1.models.user import UserRole
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.DONOR
    wallet_address: Optional[str] = None

    @validator("wallet_address")
    def validate_wallet_address(cls, v):
        if v and not v.startswith("0.0."):
            raise ValueError("Invalid Hedera account ID format")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class Login(BaseModel):
    email: EmailStr
    password: str

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    wallet_address: Optional[str]
    created_at: datetime  # Datetime as string for response

    class Config:
        from_attributes = True