import secrets
import string
from datetime import datetime, timedelta
from typing import Tuple


class TokenGenerator:
    """Secure token generation utility."""

    TOKEN_LENGTH = 32
    TOKEN_EXPIRATION_HOURS = 24

    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure random token.
        
        Returns:
            str: A 32-byte random token encoded as hex string.
        """
        return secrets.token_urlsafe(TokenGenerator.TOKEN_LENGTH)

    @staticmethod
    def generate_token_with_expiration() -> Tuple[str, datetime]:
        """Generate a token with its expiration datetime.
        
        Returns:
            Tuple[str, datetime]: Generated token and expiration datetime.
        """
        token = TokenGenerator.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=TokenGenerator.TOKEN_EXPIRATION_HOURS)
        return token, expires_at

    @staticmethod
    def validate_token_format(token: str) -> bool:
        """Validate token format.
        
        Args:
            token: Token to validate.
            
        Returns:
            bool: True if token format is valid.
        """
        if not token or not isinstance(token, str):
            return False
        if len(token) < 20:
            return False
        return True
