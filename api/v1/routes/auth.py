from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from api.db.database import get_db
from api.v1.services.auth import register_user, login_user, get_current_user, login_user_swagger, ENCRYPTION_KEY
from api.v1.services.hedera import get_wallet_balance, decrypt_private_key
from api.v1.schemas.user import UserCreate, Login, UserResponse
from api.v1.models.user import User
from api.v1.services.otp import otp_service

auth = APIRouter(prefix="/auth", tags=["auth"])

@auth.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)
async def register_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        response = await register_user(db, user)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@auth.post("/login", response_model=UserResponse)
async def login_user_endpoint(login: Login, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    """
    try:
        response = await login_user(db, login)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@auth.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's details.
    """
    return UserResponse.from_orm(current_user)

@auth.post("/login_swagger", response_model=dict)
async def login_user_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT token (OAuth2 password flow).
    """
    try:
        response = await login_user_swagger(db, form_data)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    
@auth.get("/profile", response_model=dict)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile with wallet balance.
    """
    balance = await get_wallet_balance(current_user.wallet_address)
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value,
        "wallet_address": current_user.wallet_address,
        "balance_hbar": balance,
        "created_at": current_user.created_at
    }


@auth.get("/export-wallet")
async def export_wallet(current_user: User = Depends(get_current_user)):
    """
    Allow users to export their private key (advanced feature).
    """
    # Decrypt and return private key
    decrypted_key = decrypt_private_key(current_user.encrypted_private_key, ENCRYPTION_KEY)
    
    return {
        "warning": "KEEP THIS PRIVATE KEY SECRET! Anyone with this key can access your funds.",
        "wallet_address": current_user.wallet_address,
        "private_key": decrypted_key,
        "backup_instructions": "Write this down and store it securely. Do not share with anyone."
    }


@auth.post("/verify-email", status_code=status.HTTP_200_OK, response_model=dict)
async def verify_email(
    email: str, 
    otp_code: str, 
    db: Session = Depends(get_db)
):
    """
    Verify user email with OTP code.
    """
    try:
        await otp_service.verify_otp(db, email, otp_code)
        return {
            "message": "Email verified successfully",
            "is_verified": True
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )

@auth.post("/resend-verification", status_code=status.HTTP_200_OK, response_model=dict)
async def resend_verification(
    email: str, 
    db: Session = Depends(get_db)
):
    """
    Resend verification OTP code.
    """
    try:
        await otp_service.resend_otp(db, email)
        return {
            "message": "Verification code sent successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )

# Add a new endpoint to check verification status
@auth.get("/verification-status", response_model=dict)
async def get_verification_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Check if a user's email is verified.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "email": user.email,
        "is_verified": user.is_verified
    }