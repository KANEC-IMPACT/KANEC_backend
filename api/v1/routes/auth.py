from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from api.db.database import get_db
from api.v1.services.auth import register_user, login_user, get_current_user, login_user_swagger, ENCRYPTION_KEY, update_user_profile, change_user_password, delete_user_account
from api.v1.services.hedera import get_wallet_balance, decrypt_private_key
from api.v1.schemas.user import UserCreate, Login, UserResponse, UserUpdate, PasswordChange, ForgotPasswordRequest, ResetPassword

from api.v1.models.user import User
from api.v1.services.otp import otp_service
import logging

logger = logging.getLogger(__name__)


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

@auth.post("/login", response_model=dict)
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

@auth.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    """
    try:
        updated_user = await update_user_profile(db, current_user, user_update)
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password
    """
    try:
        await change_user_password(db, current_user, password_change)
        return {
            "message": "Password changed successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's account
    """
    try:
        await delete_user_account(db, current_user, password)
        return {
            "message": "Account deleted successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth.patch("/profile", response_model=UserResponse)
async def partial_update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Partially update current user's profile information
    """
    try:
        updated_user = await update_user_profile(db, current_user, user_update)
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@auth.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset OTP
    """
    try:
        await otp_service.send_password_reset_otp(db, request.email)
        return {
            "message": "If the email exists, a password reset OTP has been sent"
        }
    except Exception as e:
        logger.error(f"Error in forgot password for {request.email}: {str(e)}")
        return {
            "message": "If the email exists, a password reset OTP has been sent"
        }

@auth.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: ResetPassword,
    db: Session = Depends(get_db)
):
    """
    Reset password with OTP verification
    """
    try:
        await otp_service.verify_password_reset_otp(db, reset_data.email, reset_data.otp_code)
        
        await otp_service.complete_password_reset(db, reset_data.email, reset_data.new_password)
        
        return {
            "message": "Password reset successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )