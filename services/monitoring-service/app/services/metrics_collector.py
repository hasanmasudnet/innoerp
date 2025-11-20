"""
Service health and metrics collector
"""
import logging
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect service health and metrics"""
    
    def __init__(self):
        self.services = {
            "api-gateway": settings.api_gateway_url,
            "tenant-service": settings.tenant_service_url,
            "auth-service": settings.auth_service_url,
            "user-service": settings.user_service_url,
        }
        self._metrics_cache = {}
        self._cache_ttl = 5  # Cache for 5 seconds
    
    async def check_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = datetime.utcnow()
                response = await client.get(f"{url}/health")
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return {
                    "name": service_name,
                    "url": url,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": round(duration, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.error(f"Error checking health for {service_name}: {e}")
            return {
                "name": service_name,
                "url": url,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def get_all_services_health(self) -> List[Dict[str, Any]]:
        """Check health of all services"""
        tasks = [
            self.check_service_health(name, url)
            for name, url in self.services.items()
        ]
        results = await asyncio.gather(*tasks)
        return list(results)
    
    def get_service_health_sync(self) -> List[Dict[str, Any]]:
        """Synchronous version of get_all_services_health"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_all_services_health())
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get aggregated service metrics"""
        health_data = self.get_service_health_sync()
        
        healthy_count = sum(1 for s in health_data if s.get("status") == "healthy")
        total_count = len(health_data)
        
        avg_response_time = 0
        response_times = [s.get("response_time_ms", 0) for s in health_data if "response_time_ms" in s]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "total_services": total_count,
            "healthy_services": healthy_count,
            "unhealthy_services": total_count - healthy_count,
            "average_response_time_ms": round(avg_response_time, 2),
            "services": health_data,
        }
    
    def get_service_uptime(self, service_name: str) -> Dict[str, Any]:
        """Get uptime information for a service (simplified)"""
        # In a real implementation, this would track uptime over time
        health = self.get_service_health_sync()
        service_health = next((s for s in health if s["name"] == service_name), None)
        
        if not service_health:
            return {
                "service": service_name,
                "uptime_percentage": 0,
                "status": "unknown",
            }
        
        # Simplified - in production, track uptime over time windows
        return {
            "service": service_name,
            "uptime_percentage": 100.0 if service_health["status"] == "healthy" else 0.0,
            "status": service_health["status"],
            "last_check": service_health.get("timestamp"),
        }

