"""
Simple in-memory cache with TTL support
"""
from typing import Any, Optional
from datetime import datetime, timedelta
import threading


class CacheEntry:
    """Cache entry with value and expiration time"""
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at


class SimpleCache:
    """Thread-safe in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 86400):  # 24 hours default
        self._cache = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, returns None if not found or expired"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional custom TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str):
        """Delete value from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self):
        """Remove all expired entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]


# Global cache instance for hazard risk data
hazard_cache = SimpleCache(default_ttl=86400)  # 24 hours
