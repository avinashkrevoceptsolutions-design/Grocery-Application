import bcrypt
from typing import Tuple


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password.
        
    Returns:
        str: Hashed password.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        password: Plain text password.
        password_hash: Hashed password.
        
    Returns:
        bool: True if password matches hash, False otherwise.
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
