"""Rate limiter for API endpoints."""

import time
from collections import defaultdict
from typing import Dict, Tuple
from loguru import logger


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Dictionary to store request timestamps per key (e.g., email)
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = False  # Simple flag for thread safety (can be improved with threading.Lock)
    
    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Unique identifier (e.g., email address)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()
        
        # Clean up old requests outside the time window
        self.requests[key] = [
            timestamp 
            for timestamp in self.requests[key] 
            if current_time - timestamp < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= self.max_requests:
            remaining = 0
            logger.warning(f"Rate limit exceeded for key: {key} ({len(self.requests[key])}/{self.max_requests} requests in {self.window_seconds}s)")
            return False, remaining
        
        # Add current request timestamp
        self.requests[key].append(current_time)
        remaining = self.max_requests - len(self.requests[key])
        
        return True, remaining
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        current_time = time.time()
        
        # Clean up old requests
        self.requests[key] = [
            timestamp 
            for timestamp in self.requests[key] 
            if current_time - timestamp < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[key]))


# Global rate limiter instance for oracle-auth endpoint
# 15 requests per minute per email
oracle_auth_rate_limiter = RateLimiter(max_requests=15, window_seconds=60)

