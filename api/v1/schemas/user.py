# api/v1/schemas/user.py

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """
    Schema for user registration input.
    """
    name: str
    email: EmailStr
    password: str
    role: str
    walletAddress: Optional[str] = None

    @validator("role")
    def validate_role(cls, value):
        """
        Ensure the role is one of the allowed values.
        """
        allowed_roles = ["donor", "admin", "org"]
        if value not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return value

    @validator("password")
    def validate_password(cls, value):
        """
        Ensure password meets minimum requirements.
        """
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

class Login(BaseModel):
    """
    Schema for user login input.
    """
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """
    Schema for user response data (used in register response).
    """
    id: int
    name: str
    email: EmailStr
    role: str
    walletAddress: Optional[str]
    createdAt: datetime

    class Config:
        orm_mode = True  # Enable ORM mode to work with SQLAlchemy models