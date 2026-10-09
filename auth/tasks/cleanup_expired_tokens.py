import logging
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

from auth.database import SessionLocal
from auth.services.password_reset_service import PasswordResetService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def cleanup_expired_password_reset_tokens(self):
    """Celery task to clean up expired password reset tokens.
    
    Runs daily to remove tokens that have expired.
    """
    db = SessionLocal()
    try:
        deleted_count = PasswordResetService.cleanup_expired_tokens(db)
        logger.info(f"Cleanup task completed. Deleted {deleted_count} expired tokens")
        return {"status": "success", "deleted_count": deleted_count}
    
    except Exception as exc:
        logger.error(f"Error in cleanup_expired_password_reset_tokens: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    
    finally:
        db.close()
