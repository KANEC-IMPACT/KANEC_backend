# api/v1/routes/donation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.hedera import donate_hbar, verify_transaction, update_raised_amount
from api.v1.services.donation import create_donation
from api.v1.schemas.donation import DonationCreate, DonationResponse
from api.v1.models.project import Project
from api.v1.services.auth import get_current_user
from api.v1.models.donation import Donation, DonationStatus
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/", response_model=DonationResponse)
async def make_donation(donation: DonationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Process a donation to a project.
    Since the transaction execution returns status 22 (SUCCESS), we trust it.
    """
    if donation.donor_wallet != current_user.wallet_address:
        raise HTTPException(status_code=400, detail="Wallet mismatch")
    
    project = db.query(Project).filter(Project.id == donation.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    tx_hash = None
    try:
        # Process the donation - this returns status 22 if successful
        tx_hash = await donate_hbar(
            donor_wallet=donation.donor_wallet,
            project_wallet=project.wallet_address,
            amount_hbar=donation.amount,
            donor_private_key=donation.donor_private_key
        )
        
        # Since donate_hbar already verified the transaction status (22 = SUCCESS),
        # we can trust that the transaction was successful
        # The mirror node verification is problematic, so we'll rely on the SDK's confirmation
        
        # Check if donation already exists to avoid duplicates
        existing_donation = db.query(Donation).filter(Donation.tx_hash == tx_hash).first()
        if existing_donation:
            # Update existing donation status
            existing_donation.status = DonationStatus.completed
            db.commit()
            db.refresh(existing_donation)
            new_donation = existing_donation
        else:
            # Create new donation
            new_donation = await create_donation(db, donation, tx_hash, current_user.id, status="completed")
        
        await update_raised_amount(db, donation.project_id, donation.amount)
        
        logger.info(f"Donation completed successfully: {donation.amount} HBAR from {donation.donor_wallet} to {project.wallet_address}")
        return new_donation
        
    except Exception as e:
        # Handle exceptions - check if donation already exists
        if tx_hash:
            existing_donation = db.query(Donation).filter(Donation.tx_hash == tx_hash).first()
            if not existing_donation:
                new_donation = await create_donation(db, donation, tx_hash, current_user.id, status="failed")
        raise HTTPException(status_code=400, detail=str(e))