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
    location: Optional[str]
    verified: bool
    wallet_address: str  
    image: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True