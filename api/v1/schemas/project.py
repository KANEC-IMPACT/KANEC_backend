from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProjectCreate(BaseModel):
    title: str
    description: str
    category: str
    target_amount: float
    location: Optional[str] = None
    verified: bool = False

class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    target_amount: float
    amount_raised: float
    backers_count: int
    location: Optional[str]
    verified: bool
    wallet_address: str  
    image: Optional[str] = None  # This will be a URL to fetch the image
    image_mime_type: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# New schema for the database model (internal use)
class ProjectDB(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    target_amount: float
    amount_raised: float
    backers_count: int
    location: Optional[str]
    verified: bool
    wallet_address: str  
    image: Optional[bytes] = None  # Binary data for DB
    image_mime_type: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True