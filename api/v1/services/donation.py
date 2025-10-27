from typing import Optional
from sqlalchemy.orm import Session
from api.v1.models.donation import Donation, DonationStatus
from api.v1.schemas.donation import DonationCreate
from datetime import datetime, timezone
from uuid import UUID

async def create_donation(db: Session, donation: DonationCreate, tx_hash: Optional[str], user_id: UUID, status: str = "completed") -> Donation:
    new_donation = Donation(
        project_id=donation.project_id,
        donor_id=user_id,
        amount=donation.amount,
        tx_hash=tx_hash,
        status=DonationStatus[status],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_donation)
    db.commit()
    db.refresh(new_donation)
    return new_donation