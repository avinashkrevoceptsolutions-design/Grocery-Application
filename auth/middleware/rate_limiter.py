from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Callable
import logging
from flask import request, jsonify

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter for preventing brute force attacks"""
    
    def __init__(self):
        # Store: {identifier: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 5,
        window_seconds: int = 3600
    ) -> bool:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            identifier: Unique identifier (IP, email, user_id)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed, False if rate limited
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > cutoff_time
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < max_requests:
            self.requests[identifier].append(now)
            return True
        
        logger.warning(f"Rate limit exceeded for identifier: {identifier}")
        return False
    
    def get_remaining_requests(
        self,
        identifier: str,
        max_requests: int = 5,
        window_seconds: int = 3600
    ) -> int:
        """
        Get number of remaining requests before rate limit.
        
        Args:
            identifier: Unique identifier
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=window_seconds)
        
        active_requests = len([
            ts for ts in self.requests[identifier]
            if ts > cutoff_time
        ])
        
        return max(0, max_requests - active_requests)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    max_requests: int = 5,
    window_seconds: int = 3600,
    key_func: Optional[Callable] = None
):
    """
    Decorator to apply rate limiting to API endpoints.
    
    Args:
        max_requests: Maximum requests allowed in time window
        window_seconds: Time window in seconds
        key_func: Function to extract rate limit key from request
                  (default: uses IP address)
    
    Example:
        @app.route('/auth/forgot-password', methods=['POST'])
        @rate_limit(max_requests=5, window_seconds=3600)
        def forgot_password():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine the key for rate limiting
            if key_func:
                key = key_func()
            else:
                # Use combination of IP address for generic rate limiting
                key = request.remote_addr
            
            # Check rate limit
            if not _rate_limiter.is_allowed(
                identifier=key,
                max_requests=max_requests,
                window_seconds=window_seconds
            ):
                remaining = _rate_limiter.get_remaining_requests(
                    identifier=key,
                    max_requests=max_requests,
                    window_seconds=window_seconds
                )
                
                return jsonify({
                    'error': 'Too many requests. Please try again later.',
                    'retry_after': window_seconds
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter