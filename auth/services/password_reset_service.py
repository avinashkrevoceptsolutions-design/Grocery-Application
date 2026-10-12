from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from auth.models.password_reset_token import PasswordResetToken
from auth.models.user import User
from auth.utils.token_generator import TokenGenerator
from auth.services.email_service import EmailService
from auth.utils.password_utils import hash_password

logger = logging.getLogger(__name__)

class PasswordResetService:
    """Service for managing password reset functionality"""
    
    def __init__(self, db_session: Session, email_service: EmailService):
        self.db = db_session
        self.email_service = email_service
    
    def generate_reset_token(self, user_id: int, email: str) -> Tuple[bool, str]:
        """
        Generate a password reset token for a user.
        Invalidates any previous active reset tokens.
        
        Args:
            user_id: ID of the user requesting password reset
            email: Email address of the user
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Invalidate previous active tokens for this user
            self._invalidate_previous_tokens(user_id)
            
            # Generate new token
            token, expires_at = TokenGenerator.generate_reset_token()
            
            # Create password reset token record
            reset_token = PasswordResetToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                is_used=False
            )
            
            self.db.add(reset_token)
            self.db.commit()
            
            # Send reset email
            reset_url = self._build_reset_url(token)
            email_sent = self.email_service.send_password_reset_email(
                email=email,
                reset_url=reset_url,
                expiry_hours=24
            )
            
            if email_sent:
                logger.info(f"Password reset token generated for user {user_id}")
                return True, "Password reset instructions sent to your email"
            else:
                logger.error(f"Failed to send password reset email for user {user_id}")
                return False, "Failed to send reset email. Please try again."
                
        except Exception as e:
            logger.error(f"Error generating password reset token: {str(e)}")
            self.db.rollback()
            return False, "An error occurred. Please try again later."
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[dict]]:
        """
        Validate a password reset token.
        
        Args:
            token: The reset token to validate
            
        Returns:
            Tuple of (is_valid: bool, user_info: dict or None)
        """
        try:
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not reset_token:
                logger.warning(f"Invalid reset token provided")
                return False, None
            
            if reset_token.is_used:
                logger.warning(f"Attempted to use already-used reset token for user {reset_token.user_id}")
                return False, None
            
            if reset_token.is_expired():
                logger.warning(f"Expired reset token used for user {reset_token.user_id}")
                return False, None
            
            # Fetch user information
            user = self.db.query(User).filter(User.id == reset_token.user_id).first()
            
            if not user:
                logger.error(f"User not found for reset token")
                return False, None
            
            return True, {
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'expires_at': reset_token.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating password reset token: {str(e)}")
            return False, None
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password using a valid reset token.
        
        Args:
            token: The reset token
            new_password: The new password
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate token
            is_valid, user_info = self.validate_token(token)
            
            if not is_valid or not user_info:
                logger.warning(f"Attempt to reset password with invalid token")
                return False, "Invalid or expired reset token"
            
            user_id = user_info['user_id']
            
            # Fetch user
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.error(f"User not found for password reset")
                return False, "An error occurred. Please try again."
            
            # Update password
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            reset_token.is_used = True
            
            self.db.commit()
            
            # Log the password reset
            logger.info(f"Password successfully reset for user {user_id}")
            
            return True, "Password reset successful. Please log in with your new password."
            
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            self.db.rollback()
            return False, "An error occurred while resetting password."
    
    def cleanup_expired_tokens(self) -> int:
        """
        Delete expired password reset tokens from database.
        Should be run periodically via background job.
        
        Returns:
            Number of tokens deleted
        """
        try:
            expired_count = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at <= datetime.utcnow()
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {expired_count} expired password reset tokens")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            self.db.rollback()
            return 0
    
    def _invalidate_previous_tokens(self, user_id: int) -> None:
        """
        Invalidate all active reset tokens for a user.
        
        Args:
            user_id: ID of the user
        """
        self.db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        ).update({PasswordResetToken.is_used: True})
        
        self.db.commit()
    
    def _build_reset_url(self, token: str, frontend_base_url: str = None) -> str:
        """
        Build the password reset URL to be sent via email.
        
        Args:
            token: The reset token
            frontend_base_url: Base URL of frontend (from config)
            
        Returns:
            Complete reset URL
        """
        if frontend_base_url is None:
            frontend_base_url = "http://localhost:3000"  # Default for dev
        
        return f"{frontend_base_url}/reset-password?token={token}"