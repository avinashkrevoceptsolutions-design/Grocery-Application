from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
import logging

logger = logging.getLogger(__name__)

class ResetPasswordHandler:
    def __init__(self, db_session: Session, email_service):
        self.db_session = db_session
        self.email_service = email_service
    
    def handle_reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Handle password reset with token
        Args:
            token: Reset token from email link
            new_password: New password to set
        Returns:
            Dictionary with status and message
        """
        try:
            from auth.models.user import User
            from auth.models.password_reset_token import PasswordResetToken
            
            # Validate password
            validation_result = self._validate_password(new_password)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"]
                }
            
            # Find reset token
            reset_token_record = self.db_session.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not reset_token_record:
                logger.warning(f"Invalid reset token attempted: {token}")
                return {
                    "success": False,
                    "message": "Invalid or expired reset token"
                }
            
            # Check if token is valid
            if not reset_token_record.is_valid():
                logger.warning(f"Invalid/expired reset token used: {token}")
                return {
                    "success": False,
                    "message": "Invalid or expired reset token"
                }
            
            # Get user
            user = self.db_session.query(User).filter(
                User.id == reset_token_record.user_id
            ).first()
            
            if not user:
                logger.error(f"User not found for reset token: {token}")
                return {
                    "success": False,
                    "message": "Invalid reset token"
                }
            
            # Hash new password
            password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Update user password
            user.password_hash = password_hash
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token_record.is_used = '1'
            
            self.db_session.commit()
            
            # Send confirmation email
            self.email_service.send_password_changed_email(
                recipient_email=user.email,
                user_name=user.username
            )
            
            logger.info(f"Password successfully reset for user: {user.id}")
            return {
                "success": True,
                "message": "Password has been reset successfully. You can now log in with your new password."
            }
        
        except SQLAlchemyError as e:
            logger.error(f"Database error in reset_password: {str(e)}")
            self.db_session.rollback()
            return {
                "success": False,
                "message": "An error occurred. Please try again later"
            }
        except Exception as e:
            logger.error(f"Unexpected error in reset_password: {str(e)}")
            return {
                "success": False,
                "message": "An unexpected error occurred"
            }
    
    @staticmethod
    def _validate_password(password: str) -> Dict[str, Any]:
        """
        Validate password strength
        Returns:
            Dictionary with valid flag and message
        """
        if not password or len(password) < 8:
            return {
                "valid": False,
                "message": "Password must be at least 8 characters long"
            }
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return {
                "valid": False,
                "message": "Password must contain uppercase, lowercase, and numeric characters"
            }
        
        return {
            "valid": True,
            "message": "Password is valid"
        }
