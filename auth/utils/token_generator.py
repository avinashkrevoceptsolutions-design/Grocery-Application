import secrets
import string
from datetime import datetime, timedelta
from typing import Tuple

class TokenGenerator:
    """Generates cryptographically strong tokens for password reset"""
    
    # Token configuration
    TOKEN_LENGTH = 64
    TOKEN_ALPHABET = string.ascii_letters + string.digits
    DEFAULT_EXPIRY_HOURS = 24
    
    @staticmethod
    def generate_reset_token(expiry_hours: int = DEFAULT_EXPIRY_HOURS) -> Tuple[str, datetime]:
        """
        Generate a cryptographically strong reset token.
        
        Args:
            expiry_hours: Number of hours until token expires (default: 24)
            
        Returns:
            Tuple of (token_string, expiry_datetime)
        """
        # Generate random token using secrets module (cryptographically strong)
        token = secrets.token_urlsafe(TokenGenerator.TOKEN_LENGTH)
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        return token, expires_at
    
    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """
        Generate a numeric code for alternative verification.
        
        Args:
            length: Length of numeric code
            
        Returns:
            Random numeric string
        """
        return ''.join(secrets.choice(string.digits) for _ in range(length))