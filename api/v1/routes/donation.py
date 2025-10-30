from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.hedera import donate_hbar, verify_transaction, update_raised_amount, donate_hbar_from_user, get_wallet_balance
from api.v1.services.donation import create_donation, get_user_completed_donations
from api.v1.schemas.donation import DonationCreate, DonationResponse, UserDonationResponse
from api.v1.models.project import Project
from api.v1.services.auth import get_current_user
from api.v1.models.donation import Donation, DonationStatus
from typing import List
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/", response_model=DonationResponse)
async def make_donation(donation: DonationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Process a donation to a project using the current user's wallet.
    """
    project = db.query(Project).filter(Project.id == donation.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has a wallet
    if not current_user.wallet_address or not current_user.encrypted_private_key:
        raise HTTPException(status_code=400, detail="User wallet not configured")
    
    # Check user balance
    user_balance = await get_wallet_balance(current_user.wallet_address)
    if user_balance < donation.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    tx_hash = None
    try:
        # Use the new function that gets private key from database
        tx_hash = await donate_hbar_from_user(
            user_id=current_user.id,
            project_wallet=project.wallet_address,
            amount_hbar=donation.amount,
            db=db
        )
        
        # Create donation record
        new_donation = await create_donation(db, donation, tx_hash, current_user.id, status="completed")
        await update_raised_amount(db, donation.project_id, donation.amount)
        
        logger.info(f"Donation completed: {donation.amount} HBAR from user {current_user.id} to project {project.id}")
        return new_donation
        
    except Exception as e:
        if tx_hash:
            existing_donation = db.query(Donation).filter(Donation.tx_hash == tx_hash).first()
            if not existing_donation:
                new_donation = await create_donation(db, donation, tx_hash, current_user.id, status="failed")
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/my-donations", response_model=List[UserDonationResponse])
async def get_my_donations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get all completed donations made by the current authenticated user
    Returns project name, amount, transaction hash, status, date, and project category
    """
    try:
        donations = await get_user_completed_donations(db, current_user.id)
        return donations
    except Exception as e:
        logger.error(f"Error fetching donations for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch donations"
        )