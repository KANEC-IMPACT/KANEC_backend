import random
from datetime import datetime
from sqlalchemy.orm import Session
from api.v1.models.user import User
from api.utils.redis_utils import redis_client
from api.utils.celery_app import send_otp_email_task, send_password_reset_email_task
from api.utils.email_utils import email_utils
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
            otp_code = OTPService.generate_otp()
            
            stored = await redis_client.set_otp(user.email, otp_code, expires_in=600)
            
            if not stored:
                logger.warning(f"Failed to store OTP in Redis for {user.email}, but continuing with email send")
            
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
        
        is_valid = await redis_client.is_otp_valid(email, otp_code)
        if not is_valid:
            raise ValueError("Invalid or expired OTP code")
        
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        db.commit()
        
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
    
    @staticmethod
    async def send_password_reset_otp(db: Session, email: str) -> bool:
        """Generate and send password reset OTP to user's email"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True  
        
        try:
            otp_code = OTPService.generate_otp()
            
            key = f"password_reset:{email}"
            stored = await redis_client.set_otp(key, otp_code, expires_in=600)  # 10 minutes
            
            if not stored:
                logger.warning(f"Failed to store password reset OTP in Redis for {email}")
            
            send_password_reset_email_task.delay(
                email=user.email,
                otp_code=otp_code,
                user_name=user.name
            )
            
            logger.info(f"Password reset OTP task queued for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue password reset OTP task for {email}: {str(e)}")
            raise

    @staticmethod
    async def verify_password_reset_otp(db: Session, email: str, otp_code: str) -> bool:
        """Verify password reset OTP code"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        
        key = f"password_reset:{email}"
        is_valid = await redis_client.is_otp_valid(key, otp_code)
        
        if not is_valid:
            raise ValueError("Invalid or expired OTP code")
        
        logger.info(f"Password reset OTP verified for {email}")
        return True

    @staticmethod
    async def complete_password_reset(db: Session, email: str, new_password: str) -> bool:
        """Complete password reset after OTP verification"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        
        from api.v1.services.auth import pwd_context
        hashed_password = pwd_context.hash(new_password)
        user.password = hashed_password
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        key = f"password_reset:{email}"
        await redis_client.delete_otp(key)
        
        logger.info(f"Password reset completed for {email}")
        return True

otp_service = OTPService()