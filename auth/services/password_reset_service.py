import logging
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from auth.models.password_reset_token import PasswordResetToken
from auth.models.user import User
from auth.utils.token_generator import TokenGenerator
from auth.services.email_service import EmailService
from auth.utils.password_utils import hash_password, verify_password

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for managing password reset operations."""

    @staticmethod
    def generate_reset_token(db: Session, user_id: int) -> Optional[str]:
        """Generate a password reset token for a user.
        
        Args:
            db: Database session.
            user_id: User ID.
            
        Returns:
            str: Generated token, or None if generation failed.
        """
        try:
            token, expires_at = TokenGenerator.generate_token_with_expiration()
            
            reset_token = PasswordResetToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at
            )
            
            db.add(reset_token)
            db.commit()
            
            logger.info(f"Password reset token generated for user {user_id}")
            return token
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to generate reset token for user {user_id}: {str(e)}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error generating reset token: {str(e)}")
            return None

    @staticmethod
    def validate_token(db: Session, token: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Validate a password reset token.
        
        Args:
            db: Database session.
            token: Token to validate.
            
        Returns:
            Tuple[bool, Optional[int], Optional[str]]: (is_valid, user_id, email)
        """
        if not TokenGenerator.validate_token_format(token):
            return False, None, None
        
        try:
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not reset_token:
                logger.warning(f"Token not found: {token[:10]}...")
                return False, None, None
            
            if not reset_token.is_valid():
                logger.warning(f"Token invalid or expired: {token[:10]}...")
                return False, None, None
            
            user = db.query(User).filter(User.id == reset_token.user_id).first()
            if not user:
                logger.warning(f"User not found for token: {token[:10]}...")
                return False, None, None
            
            logger.info(f"Token validated successfully for user {reset_token.user_id}")
            return True, reset_token.user_id, user.email
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return False, None, None

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password using a valid token.
        
        Args:
            db: Database session.
            token: Password reset token.
            new_password: New password.
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            is_valid, user_id, email = PasswordResetService.validate_token(db, token)
            
            if not is_valid or not user_id:
                return False, "Invalid or expired token"
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"
            
            # Hash and update password
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            if reset_token:
                reset_token.is_used = True
                reset_token.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Send confirmation email
            EmailService.send_password_reset_confirmation_email(email, user.name)
            
            logger.info(f"Password reset successfully for user {user_id}")
            return True, "Password has been reset successfully"
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting password: {str(e)}")
            return False, "An error occurred while resetting password"

    @staticmethod
    def initiate_password_reset(db: Session, email: str) -> Tuple[bool, str]:
        """Initiate password reset flow for a user.
        
        Args:
            db: Database session.
            email: User email address.
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Return generic message to prevent user enumeration
                logger.info(f"Password reset requested for non-existent email: {email}")
                return True, "If an account exists with this email, a password reset link has been sent"
            
            # Generate reset token
            token = PasswordResetService.generate_reset_token(db, user.id)
            
            if not token:
                return False, "Failed to generate reset token"
            
            # Send email
            email_sent = EmailService.send_password_reset_email(email, token, user.name)
            
            if not email_sent:
                logger.warning(f"Failed to send reset email to {email}")
                return False, "Failed to send reset email. Please try again later"
            
            logger.info(f"Password reset initiated for user {user.id}")
            return True, "If an account exists with this email, a password reset link has been sent"
            
        except Exception as e:
            logger.error(f"Error initiating password reset: {str(e)}")
            return False, "An error occurred. Please try again later"

    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Delete expired password reset tokens.
        
        Args:
            db: Database session.
            
        Returns:
            int: Number of tokens deleted.
        """
        try:
            deleted_count = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} expired password reset tokens")
            return deleted_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0
