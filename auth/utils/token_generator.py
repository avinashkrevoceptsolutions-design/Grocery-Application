import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Tuple

class TokenGenerator:
    """Utility class for generating and validating secure tokens"""
    
    TOKEN_LENGTH = 32  # 32 bytes = 256 bits of entropy
    DEFAULT_EXPIRY_HOURS = 24
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(TokenGenerator.TOKEN_LENGTH)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def get_expiry_time(hours: int = DEFAULT_EXPIRY_HOURS) -> datetime:
        """Get token expiry time"""
        return datetime.utcnow() + timedelta(hours=hours)
    
    @staticmethod
    def is_token_expired(expiry_time: datetime) -> bool:
        """Check if token has expired"""
        return datetime.utcnow() > expiry_time
    
    @staticmethod
    def generate_reset_token() -> Tuple[str, datetime]:
        """Generate a password reset token with expiry time"""
        token = TokenGenerator.generate_token()
        expiry = TokenGenerator.get_expiry_time()
        return token, expiry