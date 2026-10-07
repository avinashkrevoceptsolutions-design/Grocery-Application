import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models.password_reset_token import PasswordResetToken
from src.models.user import User
from src.utils.token_generator import TokenGenerator
from src.utils.email_service import EmailServiceBase
from src.config.settings import settings
from passlib.context import CryptContext
import hmac
import hashlib

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordResetService:
    """Service for handling password reset operations."""

    def __init__(self, db: Session, email_service: EmailServiceBase):
        self.db = db
        self.email_service = email_service
        self.token_expiration_hours = settings.PASSWORD_RESET_TOKEN_EXPIRATION_HOURS
        self.reset_link_base_url = settings.PASSWORD_RESET_LINK_BASE_URL

    async def generate_reset_token(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a password reset token for the given email.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, message, token)
        """
        try:
            # Check if user exists (prevent user enumeration via timing attacks)
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                # Return generic message to prevent user enumeration
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True, "If an account exists with this email, a reset link will be sent.", None

            # Check rate limiting
            recent_tokens = self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.created_at > datetime.utcnow() - timedelta(hours=1)
                )
            ).count()

            if recent_tokens >= settings.PASSWORD_RESET_MAX_REQUESTS_PER_HOUR:
                logger.warning(f"Rate limit exceeded for user: {user.id}")
                return False, "Too many password reset requests. Please try again later.", None

            # Invalidate previous tokens
            self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.is_used == False
                )
            ).update({PasswordResetToken.is_used: True})

            # Generate new token
            token = TokenGenerator.generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiration_hours)

            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )

            self.db.add(reset_token)
            self.db.commit()

            # Send email
            reset_link = f"{self.reset_link_base_url}?token={token}"
            email_sent = await self.email_service.send_password_reset_email(
                email=user.email,
                reset_link=reset_link,
                user_name=user.full_name or user.email
            )

            if not email_sent:
                logger.error(f"Failed to send password reset email to {email}")
                return False, "Failed to send reset email. Please try again later.", None

            logger.info(f"Password reset token generated for user: {user.id}")
            return True, "If an account exists with this email, a reset link will be sent.", token

        except Exception as e:
            logger.error(f"Error generating reset token: {str(e)}")
            self.db.rollback()
            return False, "An error occurred. Please try again later.", None

    def validate_reset_token(self, token: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a password reset token.
        
        Args:
            token: The reset token to validate
            
        Returns:
            Tuple of (is_valid, message, user_id)
        """
        try:
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()

            if not reset_token:
                logger.warning(f"Invalid reset token provided")
                return False, "Invalid or expired reset token.", None

            if reset_token.is_used:
                logger.warning(f"Already used reset token: {reset_token.id}")
                return False, "This reset link has already been used.", None

            if reset_token.is_expired():
                logger.warning(f"Expired reset token: {reset_token.id}")
                return False, "This reset link has expired. Please request a new one.", None

            return True, "Token is valid.", reset_token.user_id

        except Exception as e:
            logger.error(f"Error validating reset token: {str(e)}")
            return False, "An error occurred. Please try again later.", None

    async def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password using a valid reset token.
        
        Args:
            token: The reset token
            new_password: The new password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate token
            is_valid, message, user_id = self.validate_reset_token(token)
            if not is_valid:
                return False, message

            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found for reset token: {user_id}")
                return False, "An error occurred. Please try again later."

            # Validate password strength
            if not self._validate_password_strength(new_password):
                return False, "Password does not meet security requirements. Minimum 8 characters with uppercase, lowercase, and numbers."

            # Update password
            user.hashed_password = pwd_context.hash(new_password)
            user.updated_at = datetime.utcnow()

            # Mark token as used
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            reset_token.mark_as_used()

            self.db.commit()

            logger.info(f"Password reset successfully for user: {user_id}")
            return True, "Password has been reset successfully."

        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            self.db.rollback()
            return False, "An error occurred. Please try again later."

    def cleanup_expired_tokens(self) -> int:
        """
        Delete expired password reset tokens.
        
        Returns:
            Number of tokens deleted
        """
        try:
            deleted_count = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).delete()
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} expired password reset tokens")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            self.db.rollback()
            return 0

    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements, False otherwise
        """
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True
