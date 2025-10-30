from pydantic import BaseModel, EmailStr, validator, field_validator
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
    wallet_address: str
    created_at: datetime  
    is_verified: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return v.strip() if v else v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v
    
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v