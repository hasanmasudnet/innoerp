"""
Redis monitoring service
"""
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisMonitor:
    """Monitor Redis statistics and metrics"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6380, redis_db: int = 0, redis_url: str = ""):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_url = redis_url
        self._is_noop = not REDIS_AVAILABLE
        self.redis_client = None
        
        if REDIS_AVAILABLE:
            try:
                if redis_url:
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                else:
                    self.redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        db=redis_db,
                        decode_responses=True
                    )
                # Test connection
                self.redis_client.ping()
                self._is_noop = False
                logger.info(f"Redis connected to {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis at {redis_host}:{redis_port}: {e}")
                self._is_noop = True
                self.redis_client = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis server statistics"""
        if self._is_noop or not self.redis_client:
            return {
                "connected": False,
                "error": f"Redis not available. Connection: {self.redis_host}:{self.redis_port}",
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
            }
        
        try:
            # Test connection first
            self.redis_client.ping()
            info = self.redis_client.info()
            
            return {
                "connected": True,
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "redis_version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            # Check if it's a connection error
            error_str = str(e).lower()
            if 'connection' in error_str or 'refused' in error_str or 'timeout' in error_str:
                logger.error(f"Redis connection error: {e}")
                return {
                    "connected": False,
                    "error": f"Connection failed: {str(e)}",
                    "redis_host": self.redis_host,
                    "redis_port": self.redis_port,
                }
            else:
                logger.error(f"Error getting Redis stats: {e}")
                return {
                    "connected": False,
                    "error": str(e),
                    "redis_host": self.redis_host,
                    "redis_port": self.redis_port,
                }
    
    def get_key_count_by_pattern(self, pattern: str = "*") -> int:
        """Get count of keys matching pattern"""
        if self._is_noop:
            return 0
        
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            return len(keys) if keys else 0
        except Exception as e:
            logger.error(f"Error counting keys with pattern {pattern}: {e}")
            return 0
    
    def get_key_patterns(self) -> List[Dict[str, Any]]:
        """Get key counts by common patterns"""
        if self._is_noop:
            return []
        
        patterns = [
            "organizations:*",
            "modules:*",
            "industries:*",
            "cache:*",
            "*",
        ]
        
        results = []
        for pattern in patterns:
            try:
                count = self.get_key_count_by_pattern(pattern)
                results.append({
                    "pattern": pattern,
                    "count": count,
                })
            except Exception as e:
                logger.warning(f"Error getting count for pattern {pattern}: {e}")
                results.append({
                    "pattern": pattern,
                    "count": 0,
                    "error": str(e),
                })
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache hit/miss statistics"""
        stats = self.get_stats()
        
        if not stats.get("connected"):
            return {
                "hit_rate": 0.0,
                "miss_rate": 0.0,
                "total_requests": 0,
                "hits": 0,
                "misses": 0,
            }
        
        hits = stats.get("keyspace_hits", 0)
        misses = stats.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return {
                "hit_rate": 0.0,
                "miss_rate": 0.0,
                "total_requests": 0,
                "hits": 0,
                "misses": 0,
            }
        
        hit_rate = (hits / total) * 100
        miss_rate = (misses / total) * 100
        
        return {
            "hit_rate": round(hit_rate, 2),
            "miss_rate": round(miss_rate, 2),
            "total_requests": total,
            "hits": hits,
            "misses": misses,
        }
    
    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self._is_noop:
            return {
                "available": False,
            }
        
        if not self.redis_client:
            return {
                "available": False,
            }
        
        try:
            info = self.redis_client.info("clients")
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "client_recent_max_input_buffer": info.get("client_recent_max_input_buffer", 0),
                "client_recent_max_output_buffer": info.get("client_recent_max_output_buffer", 0),
            }
        except Exception as e:
            logger.error(f"Error getting connection pool stats: {e}")
            return {
                "available": False,
                "error": str(e),
            }
    
    def get_command_stats(self) -> Dict[str, Any]:
        """Get command statistics"""
        if self._is_noop:
            return {}
        
        if not self.redis_client:
            return {}
        
        try:
            info = self.redis_client.info("commandstats")
            
            # Parse command stats
            command_stats = {}
            for key, value in info.items():
                if key.startswith("cmdstat_"):
                    command = key.replace("cmdstat_", "")
                    command_stats[command] = {
                        "calls": value.get("calls", 0),
                        "usec": value.get("usec", 0),
                        "usec_per_call": value.get("usec_per_call", 0),
                    }
            
            return command_stats
        except Exception as e:
            logger.error(f"Error getting command stats: {e}")
            return {}
    
    def get_redis_metrics(self) -> Dict[str, Any]:
        """Get all Redis metrics"""
        return {
            "stats": self.get_stats(),
            "cache_stats": self.get_cache_stats(),
            "key_patterns": self.get_key_patterns(),
            "connection_pool": self.get_connection_pool_stats(),
            "command_stats": self.get_command_stats(),
        }

