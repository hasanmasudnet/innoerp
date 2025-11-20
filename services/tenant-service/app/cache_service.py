"""
Cache service with decorators and cache key patterns
"""
import functools
import hashlib
import json
import logging
from typing import Callable, Any, Optional
from uuid import UUID
from shared.cache.redis_client import RedisClient

logger = logging.getLogger(__name__)

# Cache TTLs (in seconds)
CACHE_TTL_ORG_MODULES = 300  # 5 minutes
CACHE_TTL_INDUSTRY_MODULES = 3600  # 1 hour
CACHE_TTL_MODULE_CONFIG = 600  # 10 minutes
CACHE_TTL_ORG_INFO = 300  # 5 minutes
CACHE_TTL_MODULE_REGISTRY = 600  # 10 minutes


def _generate_cache_key(pattern: str, **kwargs) -> str:
    """Generate cache key from pattern and kwargs"""
    # Replace placeholders in pattern
    key = pattern
    for k, v in kwargs.items():
        placeholder = f"{{{k}}}"
        if placeholder in key:
            # Convert UUID to string
            if isinstance(v, UUID):
                v = str(v)
            key = key.replace(placeholder, str(v))
    
    return key


class CacheService:
    """Cache service with helper methods"""
    
    def __init__(self):
        self.redis = RedisClient()
    
    # Cache key patterns
    ORG_MODULES_KEY = "org:{organization_id}:modules"
    INDUSTRY_MODULES_KEY = "industry:{industry_code}:modules"
    MODULE_CONFIG_KEY = "module:{module_id}:config"
    ORG_INFO_KEY = "org:{organization_id}:info"
    MODULE_REGISTRY_KEY = "modules:registry:all"
    INDUSTRY_TEMPLATE_KEY = "industry:{industry_code}:template"
    ALL_INDUSTRIES_KEY = "industries:all"
    
    def get_org_modules(self, organization_id: UUID) -> Optional[Any]:
        """Get cached organization modules"""
        key = _generate_cache_key(self.ORG_MODULES_KEY, organization_id=organization_id)
        return self.redis.get(key)
    
    def set_org_modules(self, organization_id: UUID, modules: Any, ttl: int = CACHE_TTL_ORG_MODULES) -> bool:
        """Cache organization modules"""
        key = _generate_cache_key(self.ORG_MODULES_KEY, organization_id=organization_id)
        return self.redis.set(key, modules, ttl)
    
    def invalidate_org_modules(self, organization_id: UUID) -> bool:
        """Invalidate organization modules cache"""
        key = _generate_cache_key(self.ORG_MODULES_KEY, organization_id=organization_id)
        return self.redis.delete(key)
    
    def invalidate_org_cache(self, organization_id: UUID) -> int:
        """Invalidate all cache for an organization"""
        pattern = f"org:{organization_id}:*"
        return self.redis.delete_pattern(pattern)
    
    def get_industry_modules(self, industry_code: str) -> Optional[Any]:
        """Get cached industry modules"""
        key = _generate_cache_key(self.INDUSTRY_MODULES_KEY, industry_code=industry_code)
        return self.redis.get(key)
    
    def set_industry_modules(self, industry_code: str, modules: Any, ttl: int = CACHE_TTL_INDUSTRY_MODULES) -> bool:
        """Cache industry modules"""
        key = _generate_cache_key(self.INDUSTRY_MODULES_KEY, industry_code=industry_code)
        return self.redis.set(key, modules, ttl)
    
    def invalidate_industry_modules(self, industry_code: str) -> bool:
        """Invalidate industry modules cache"""
        key = _generate_cache_key(self.INDUSTRY_MODULES_KEY, industry_code=industry_code)
        return self.redis.delete(key)
    
    def get_module_registry(self) -> Optional[Any]:
        """Get cached module registry"""
        return self.redis.get(self.MODULE_REGISTRY_KEY)
    
    def set_module_registry(self, modules: Any, ttl: int = CACHE_TTL_MODULE_REGISTRY) -> bool:
        """Cache module registry"""
        return self.redis.set(self.MODULE_REGISTRY_KEY, modules, ttl)
    
    def invalidate_module_registry(self) -> bool:
        """Invalidate module registry cache"""
        return self.redis.delete(self.MODULE_REGISTRY_KEY)
    
    def get_org_info(self, organization_id: UUID) -> Optional[Any]:
        """Get cached organization info"""
        key = _generate_cache_key(self.ORG_INFO_KEY, organization_id=organization_id)
        return self.redis.get(key)
    
    def set_org_info(self, organization_id: UUID, info: Any, ttl: int = CACHE_TTL_ORG_INFO) -> bool:
        """Cache organization info"""
        key = _generate_cache_key(self.ORG_INFO_KEY, organization_id=organization_id)
        return self.redis.set(key, info, ttl)
    
    def invalidate_org_info(self, organization_id: UUID) -> bool:
        """Invalidate organization info cache"""
        key = _generate_cache_key(self.ORG_INFO_KEY, organization_id=organization_id)
        return self.redis.delete(key)
    
    def get_industry_template(self, industry_code: str) -> Optional[Any]:
        """Get cached industry template"""
        key = _generate_cache_key(self.INDUSTRY_TEMPLATE_KEY, industry_code=industry_code)
        return self.redis.get(key)
    
    def set_industry_template(self, industry_code: str, template: Any, ttl: int = CACHE_TTL_INDUSTRY_MODULES) -> bool:
        """Cache industry template"""
        key = _generate_cache_key(self.INDUSTRY_TEMPLATE_KEY, industry_code=industry_code)
        return self.redis.set(key, template, ttl)
    
    def invalidate_industry_template(self, industry_code: str) -> bool:
        """Invalidate industry template cache"""
        key = _generate_cache_key(self.INDUSTRY_TEMPLATE_KEY, industry_code=industry_code)
        return self.redis.delete(key)
    
    def invalidate_all_industries(self) -> bool:
        """Invalidate all industries cache"""
        return self.redis.delete(self.ALL_INDUSTRIES_KEY)
    
    def invalidate_all_industry_cache(self) -> int:
        """Invalidate all industry-related cache"""
        return self.redis.delete_pattern("industry:*")


# Global cache service instance
_cache_service = CacheService()


def cache_result(ttl: int = 300, key_pattern: Optional[str] = None, cache_key_func: Optional[Callable] = None):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_pattern: Cache key pattern with placeholders (e.g., "org:{org_id}:modules")
        cache_key_func: Function to generate cache key from function args
    
    Usage:
        @cache_result(ttl=300, key_pattern="org:{organization_id}:modules")
        def get_modules(organization_id: UUID):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            elif key_pattern:
                # Extract args to match pattern placeholders
                # This is a simple implementation - may need refinement
                cache_key = key_pattern
                # Try to match function parameter names with kwargs
                for k, v in kwargs.items():
                    placeholder = f"{{{k}}}"
                    if placeholder in cache_key:
                        if isinstance(v, UUID):
                            v = str(v)
                        cache_key = cache_key.replace(placeholder, str(v))
            else:
                # Generate key from function name and args
                key_parts = [func.__name__]
                key_parts.extend(str(v) for v in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached = _cache_service.redis.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached
            
            # Cache miss - execute function
            logger.debug(f"Cache MISS for key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                _cache_service.redis.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

