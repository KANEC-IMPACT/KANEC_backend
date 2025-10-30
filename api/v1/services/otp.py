import random
from datetime import datetime
from sqlalchemy.orm import Session
from api.v1.models.user import User
from api.utils.redis_utils import redis_client
from api.utils.celery_app import send_otp_email_task
import logging

logger = logging.getLogger(__name__)

class OTPService:
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP code"""
        return str(random.randint(100000, 999999))

    @staticmethod
    async def send_verification_otp(db: Session, user: User) -> bool:
        """Generate and send OTP to user's email using Celery"""
        try:
            # Generate OTP
            otp_code = OTPService.generate_otp()
            
            # Store OTP in Redis (10 minutes expiration)
            stored = await redis_client.set_otp(user.email, otp_code, expires_in=600)
            
            if not stored:
                logger.warning(f"Failed to store OTP in Redis for {user.email}, but continuing with email send")
            
            # Send email via Celery task
            send_otp_email_task.delay(
                email=user.email,
                otp_code=otp_code,
                user_name=user.name
            )
            
            logger.info(f"OTP task queued for {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue OTP task for {user.email}: {str(e)}")
            raise

    @staticmethod
    async def verify_otp(db: Session, email: str, otp_code: str) -> bool:
        """Verify OTP code for user using Redis"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if OTP is valid in Redis
        is_valid = await redis_client.is_otp_valid(email, otp_code)
        if not is_valid:
            raise ValueError("Invalid or expired OTP code")
        
        # Mark user as verified and clear OTP from Redis
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Delete OTP from Redis after successful verification
        await redis_client.delete_otp(email)
        
        logger.info(f"User {email} verified successfully")
        return True

    @staticmethod
    async def resend_otp(db: Session, email: str) -> bool:
        """Resend OTP to user"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        
        if user.is_verified:
            raise ValueError("User is already verified")
        
        return await OTPService.send_verification_otp(db, user)

# Create global instance
otp_service = OTPService()