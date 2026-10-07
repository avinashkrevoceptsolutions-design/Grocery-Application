import secrets
import string
from typing import Tuple


class TokenGenerator:
    """Utility class for generating secure tokens."""

    @staticmethod
    def generate_reset_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token for password reset.
        
        Args:
            length: Length of the token (default 32 characters)
            
        Returns:
            A secure random token string
        """
        if length < 32:
            raise ValueError("Token length must be at least 32 characters")
        
        # Use URL-safe characters for token
        alphabet = string.ascii_letters + string.digits + "-_"
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        return token

    @staticmethod
    def generate_secure_random(length: int = 32) -> str:
        """
        Generate a cryptographically secure random string.
        
        Args:
            length: Length of the random string
            
        Returns:
            A secure random string
        """
        return secrets.token_urlsafe(length)
