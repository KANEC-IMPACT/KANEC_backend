from typing import Optional, List
from sqlalchemy.orm import Session
from api.v1.models.donation import Donation, DonationStatus
from api.v1.schemas.donation import DonationCreate, UserDonationResponse
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

async def get_user_completed_donations(db: Session, user_id: UUID) -> List[UserDonationResponse]:
    """
    Get all completed donations made by a user with project details
    """
    donations = db.query(Donation).join(
        Donation.project
    ).filter(
        Donation.donor_id == user_id,
        Donation.status == DonationStatus.completed
    ).order_by(
        Donation.created_at.desc()
    ).all()
    
    donation_responses = []
    for donation in donations:
        donation_responses.append(UserDonationResponse(
            id=donation.id,
            project_name=donation.project.title,
            amount=donation.amount,
            tx_hash=donation.tx_hash,
            status=donation.status,
            donated_at=donation.created_at,
            project_category=donation.project.category
        ))
    
    return donation_responses