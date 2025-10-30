from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from api.v1.models.donation import DonationStatus
from typing import Optional

class DonationCreate(BaseModel):
    project_id: UUID
    amount: float

class DonationResponse(BaseModel):
    id: UUID
    project_id: UUID
    donor_id: UUID
    amount: float
    tx_hash: str
    status: DonationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserDonationResponse(BaseModel):
    id: UUID
    project_name: str
    amount: float
    tx_hash: str
    status: DonationStatus
    donated_at: datetime
    project_category: str

    class Config:
        from_attributes = True