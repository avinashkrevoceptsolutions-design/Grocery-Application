import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class ForgotPasswordHandler:
    def __init__(self, db_session: Session, email_service, token_expiration_hours: int = 24):
        self.db_session = db_session
        self.email_service = email_service
        self.token_expiration_hours = token_expiration_hours
    
    def handle_forgot_password(self, email: str, reset_link_template: str) -> Dict[str, Any]:
        """
        Handle forgot password request
        Args:
            email: User's email address
            reset_link_template: Template URL for reset link (e.g., 'https://app.com/reset?token={token}')
        Returns:
            Dictionary with status and message
        """
        try:
            from auth.models.user import User
            from auth.models.password_reset_token import PasswordResetToken
            
            # Validate email format
            if not self._is_valid_email(email):
                logger.warning(f"Invalid email format: {email}")
                return {
                    "success": False,
                    "message": "Invalid email format"
                }
            
            # Find user by email
            user = self.db_session.query(User).filter(User.email == email).first()
            
            if not user:
                # Return success to prevent email enumeration
                logger.info(f"Password reset requested for non-existent email: {email}")
                return {
                    "success": True,
                    "message": "If the email exists, a password reset link has been sent"
                }
            
            # Generate secure token
            reset_token = secrets.token_urlsafe(32)
            token_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiration_hours)
            
            # Create password reset token record
            password_reset = PasswordResetToken(
                id=token_id,
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )
            
            self.db_session.add(password_reset)
            self.db_session.commit()
            
            # Generate reset link
            reset_link = reset_link_template.format(token=reset_token)
            
            # Send email
            email_sent = self.email_service.send_password_reset_email(
                recipient_email=user.email,
                reset_link=reset_link,
                user_name=user.username
            )
            
            if not email_sent:
                logger.error(f"Failed to send reset email to {user.email}")
                return {
                    "success": False,
                    "message": "Failed to send reset email. Please try again later"
                }
            
            logger.info(f"Password reset token created for user: {user.id}")
            return {
                "success": True,
                "message": "Password reset link has been sent to your email"
            }
        
        except SQLAlchemyError as e:
            logger.error(f"Database error in forgot_password: {str(e)}")
            self.db_session.rollback()
            return {
                "success": False,
                "message": "An error occurred. Please try again later"
            }
        except Exception as e:
            logger.error(f"Unexpected error in forgot_password: {str(e)}")
            return {
                "success": False,
                "message": "An unexpected error occurred"
            }
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
