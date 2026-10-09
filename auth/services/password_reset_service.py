from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging
from sqlalchemy.orm import Session
from auth.models.user import User
from auth.models.password_reset_token import PasswordResetToken
from auth.utils.token_generator import TokenGenerator
from auth.services.email_service import EmailService

logger = logging.getLogger(__name__)

class PasswordResetService:
    """Service for handling password reset operations"""
    
    RATE_LIMIT_ATTEMPTS = 5
    RATE_LIMIT_WINDOW_MINUTES = 60
    
    def __init__(self, db: Session, email_service: EmailService):
        self.db = db
        self.email_service = email_service
    
    def request_password_reset(self, email: str, reset_link_base: str) -> Dict[str, any]:
        """Request a password reset token"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                logger.warning(f'Password reset requested for non-existent email: {email}')
                return {
                    'success': True,
                    'message': 'If an account exists with this email, a password reset link has been sent.'
                }
            
            if self._is_rate_limited(user):
                logger.warning(f'Password reset rate limit exceeded for user: {user.id}')
                return {
                    'success': False,
                    'message': 'Too many password reset attempts. Please try again later.'
                }
            
            token, expiry = TokenGenerator.generate_reset_token()
            
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=TokenGenerator.hash_token(token),
                expires_at=expiry
            )
            
            user.password_reset_attempts += 1
            user.password_reset_last_attempt = datetime.utcnow()
            
            self.db.add(reset_token)
            self.db.commit()
            
            reset_link = f"{reset_link_base}?token={token}"
            self.email_service.send_password_reset_email(user.email, reset_link)
            
            logger.info(f'Password reset token generated for user: {user.id}')
            
            return {
                'success': True,
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }
        
        except Exception as e:
            logger.error(f'Error requesting password reset: {str(e)}')
            return {
                'success': False,
                'message': 'An error occurred while processing your request.'
            }
    
    def validate_reset_token(self, token: str) -> Dict[str, any]:
        """Validate a password reset token"""
        try:
            token_hash = TokenGenerator.hash_token(token)
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token_hash
            ).first()
            
            if not reset_token:
                logger.warning(f'Invalid password reset token provided')
                return {
                    'success': False,
                    'message': 'Invalid or expired reset token.',
                    'token_valid': False
                }
            
            if not reset_token.is_valid():
                logger.warning(f'Expired or used password reset token: {reset_token.id}')
                return {
                    'success': False,
                    'message': 'This reset link has expired or has already been used.',
                    'token_valid': False
                }
            
            logger.info(f'Password reset token validated for user: {reset_token.user_id}')
            
            return {
                'success': True,
                'message': 'Token is valid.',
                'token_valid': True
            }
        
        except Exception as e:
            logger.error(f'Error validating reset token: {str(e)}')
            return {
                'success': False,
                'message': 'An error occurred while validating the token.',
                'token_valid': False
            }
    
    def reset_password(self, token: str, new_password: str, password_hasher) -> Dict[str, any]:
        """Reset user password with valid token"""
        try:
            token_hash = TokenGenerator.hash_token(token)
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token_hash
            ).first()
            
            if not reset_token or not reset_token.is_valid():
                logger.warning(f'Invalid or expired token used for password reset')
                return {
                    'success': False,
                    'message': 'Invalid or expired reset token.'
                }
            
            user = self.db.query(User).filter(User.id == reset_token.user_id).first()
            
            if not user:
                logger.error(f'User not found for password reset: {reset_token.user_id}')
                return {
                    'success': False,
                    'message': 'An error occurred while resetting your password.'
                }
            
            user.password_hash = password_hasher.hash(new_password)
            user.password_reset_attempts = 0
            user.password_reset_last_attempt = None
            
            reset_token.mark_as_used()
            
            self.db.commit()
            
            self._invalidate_all_sessions(user.id)
            
            logger.info(f'Password reset successful for user: {user.id}')
            
            return {
                'success': True,
                'message': 'Your password has been reset successfully. Please log in with your new password.'
            }
        
        except Exception as e:
            logger.error(f'Error resetting password: {str(e)}')
            self.db.rollback()
            return {
                'success': False,
                'message': 'An error occurred while resetting your password.'
            }
    
    def _is_rate_limited(self, user: User) -> bool:
        """Check if user has exceeded rate limit for password reset requests"""
        if not user.password_reset_last_attempt:
            return False
        
        time_since_last_attempt = datetime.utcnow() - user.password_reset_last_attempt
        window = timedelta(minutes=self.RATE_LIMIT_WINDOW_MINUTES)
        
        if time_since_last_attempt < window:
            return user.password_reset_attempts >= self.RATE_LIMIT_ATTEMPTS
        
        return False
    
    def _invalidate_all_sessions(self, user_id: int) -> None:
        """Invalidate all active sessions for a user after password reset"""
        try:
            logger.info(f'Invalidating all sessions for user: {user_id}')
        except Exception as e:
            logger.error(f'Error invalidating sessions: {str(e)}')