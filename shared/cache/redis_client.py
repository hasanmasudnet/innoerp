"""
Redis client wrapper with connection pool
"""
import json
import logging
import os
from typing import Optional, Any, List, Union
from pathlib import Path

# Try to import redis, fallback to NoOp if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore
    logger = logging.getLogger(__name__)
    logger.warning("Redis module not installed. Caching will be disabled. Install with: pip install redis")

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass
except Exception as e:
    print(f"[WARN] Could not load .env file: {e}")

logger = logging.getLogger(__name__)

# Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))  # Using 6380 to avoid conflicts
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_URL = os.getenv("REDIS_URL", None)

# Global Redis connection pool
_redis_pool = None
_redis_client = None


class NoOpRedisClient:
    """No-op Redis client when Redis is not available"""
    
    def get(self, key: str) -> Optional[Any]:
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        return False
    
    def delete(self, key: str) -> bool:
        return False
    
    def delete_pattern(self, pattern: str) -> int:
        return 0
    
    def exists(self, key: str) -> bool:
        return False
    
    def expire(self, key: str, ttl: int) -> bool:
        return False
    
    def flush_db(self) -> bool:
        return False
    
    def ping(self) -> bool:
        return False
    
    def keys(self, pattern: str) -> List[str]:
        return []


def get_redis_client() -> Union[Any, NoOpRedisClient]:
    """Get or create Redis client with connection pool, or NoOp client if Redis unavailable"""
    global _redis_pool, _redis_client
    
    if not REDIS_AVAILABLE:
        logger.debug("Redis not available, using NoOp client")
        return NoOpRedisClient()
    
    if _redis_client is None:
        try:
            if REDIS_URL:
                _redis_pool = redis.ConnectionPool.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    max_connections=50
                )
            else:
                _redis_pool = redis.ConnectionPool(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    max_connections=50
                )
            
            _redis_client = redis.Redis(connection_pool=_redis_pool)
            
            # Test connection
            try:
                _redis_client.ping()
                logger.info(f"Redis connected to {REDIS_HOST}:{REDIS_PORT}")
            except redis.ConnectionError as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
                return NoOpRedisClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}. Caching will be disabled.")
            return NoOpRedisClient()
    
    return _redis_client


class RedisClient:
    """Redis client wrapper with helper methods"""
    
    def __init__(self):
        self.client = get_redis_client()
        self._is_noop = isinstance(self.client, NoOpRedisClient)
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if self._is_noop:
            return None
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value
        except Exception as e:
            logger.debug(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cached value with TTL (default 5 minutes)"""
        if self._is_noop:
            return False
        try:
            # Serialize to JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            return self.client.setex(key, ttl, value)
        except Exception as e:
            logger.debug(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        if self._is_noop:
            return False
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.debug(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (e.g., 'org:123:*')"""
        if self._is_noop:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Redis DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self._is_noop:
            return False
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.debug(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        if self._is_noop:
            return False
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.debug(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    def flush_db(self) -> bool:
        """Flush current database (use with caution!)"""
        if self._is_noop:
            return False
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.debug(f"Redis FLUSHDB error: {e}")
            return False
    
    def ping(self) -> bool:
        """Test Redis connection"""
        if self._is_noop:
            return False
        try:
            return self.client.ping()
        except Exception:
            return False
