from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.hedera import trace_transaction

router = APIRouter(prefix="/trace", tags=["trace"])

@router.get("/trace/{tx_hash}")
async def trace_donation(tx_hash: str, db: Session = Depends(get_db)):
    """
    Trace a donation by its transaction hash.
    """
    try:
        return await trace_transaction(tx_hash, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))