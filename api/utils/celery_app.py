from celery import Celery
from api.utils.settings import settings
from api.utils.email_utils import email_utils
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "kanec",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(bind=True, max_retries=3)
def send_otp_email_task(self, email: str, otp_code: str, user_name: str):
    """Celery task to send OTP email"""
    try:
        # Since we're in a sync context, we'll use sync email sending
        email_utils.send_otp_email_sync(email, otp_code, user_name)
        logger.info(f"OTP email sent successfully to {email}")
        return {"status": "success", "email": email}
    except Exception as exc:
        logger.error(f"Failed to send OTP email to {email}: {str(exc)}")
        # Retry after 30 seconds
        raise self.retry(countdown=30, exc=exc)