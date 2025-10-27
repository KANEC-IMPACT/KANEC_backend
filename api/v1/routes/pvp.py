from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.hedera import donate_hbar_from_user, get_wallet_balance, transfer_hbar_p2p
from api.v1.services.auth import get_current_user
from api.v1.models.user import User
from api.v1.schemas.pvp import P2PTransferRequest, P2PTransferResponse
from uuid import UUID

p2p = APIRouter(prefix="/p2p", tags=["p2p-transfers"])

@p2p.post("/transfer", response_model=P2PTransferResponse)
async def transfer_hbar(
    transfer: P2PTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transfer HBAR from current user's wallet to another wallet.
    """
    if not current_user.wallet_address or not current_user.encrypted_private_key:
        raise HTTPException(status_code=400, detail="User wallet not configured")
    
    if not transfer.recipient_wallet.startswith("0.0."):
        raise HTTPException(status_code=400, detail="Invalid recipient wallet format. Must start with '0.0.'")
    
    if current_user.wallet_address == transfer.recipient_wallet:
        raise HTTPException(status_code=400, detail="Cannot send HBAR to your own wallet")
    
    if transfer.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    if transfer.amount > 10000:  
        raise HTTPException(status_code=400, detail="Amount too large. Maximum transfer is 10,000 HBAR")
    
    user_balance = await get_wallet_balance(current_user.wallet_address)
    if user_balance < transfer.amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. You have {user_balance:.2f} HBAR, but trying to send {transfer.amount:.2f} HBAR"
        )
    
    try:
        tx_hash = await transfer_hbar_p2p(
            sender_user_id=current_user.id,
            recipient_wallet=transfer.recipient_wallet,
            amount_hbar=transfer.amount,
            db=db,
            memo=transfer.memo
        )
        
        return P2PTransferResponse(
            transaction_hash=tx_hash,
            from_wallet=current_user.wallet_address,
            to_wallet=transfer.recipient_wallet,
            amount=transfer.amount,
            status="completed",
            memo=transfer.memo
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transfer failed: {str(e)}")
    

@p2p.get("/balance")
async def get_user_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's HBAR balance.
    """
    if not current_user.wallet_address:
        raise HTTPException(status_code=400, detail="User wallet not configured")
    
    try:
        balance = await get_wallet_balance(current_user.wallet_address)
        
        return {
            "wallet_address": current_user.wallet_address,
            "balance_hbar": balance,
            "balance_tinybars": int(balance * 100_000_000)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get balance: {str(e)}")

@p2p.post("/validate-wallet")
async def validate_wallet(wallet_address: str):
    """
    Validate if a wallet address exists and is valid.
    """
    if not wallet_address.startswith("0.0."):
        return {"valid": False, "error": "Invalid format. Hedera wallets start with '0.0.'"}
    
    try:
        from api.v1.services.hedera import get_wallet_balance
        balance = await get_wallet_balance(wallet_address)
        
        return {
            "valid": True,
            "wallet_address": wallet_address,
            "exists": True,
            "balance_hbar": balance
        }
        
    except Exception as e:
        return {
            "valid": True,
            "wallet_address": wallet_address,
            "exists": False,
            "balance_hbar": 0.0
        }