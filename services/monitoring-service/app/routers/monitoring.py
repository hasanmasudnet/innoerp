"""
Monitoring API routes
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import asyncio
import logging

from app.services.kafka_monitor import KafkaMonitor
from app.services.redis_monitor import RedisMonitor
from app.services.log_aggregator import LogAggregator
from app.services.metrics_collector import MetricsCollector
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Initialize services
kafka_monitor = KafkaMonitor(settings.kafka_bootstrap_servers)
redis_monitor = RedisMonitor(
    redis_host=settings.redis_host,
    redis_port=settings.redis_port,
    redis_db=settings.redis_db,
    redis_url=settings.redis_url if settings.redis_url else ""
)
log_aggregator = LogAggregator()
metrics_collector = MetricsCollector()


# Request/Response models
class LogSearchRequest(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    query: Optional[str] = None
    size: int = 100
    from_: int = 0


# Logs endpoints
@router.get("/logs")
def search_logs(
    service: Optional[str] = Query(None, description="Filter by service name"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO format)"),
    query: Optional[str] = Query(None, description="Search query"),
    size: int = Query(100, ge=1, le=1000, description="Number of results"),
    from_: int = Query(0, ge=0, description="Offset"),
):
    """Search logs from Elasticsearch"""
    try:
        result = log_aggregator.search_logs(
            service=service,
            level=level,
            start_time=start_time,
            end_time=end_time,
            query=query,
            size=size,
            from_=from_,
        )
        return result
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stream")
async def stream_logs(
    service: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
):
    """Stream logs in real-time using Server-Sent Events"""
    async def generate():
        try:
            while True:
                # Get recent logs (last 10 seconds)
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(seconds=10)
                
                result = log_aggregator.search_logs(
                    service=service,
                    level=level,
                    start_time=start_time,
                    end_time=end_time,
                    size=50,
                )
                
                for log in result.get("logs", []):
                    yield f"data: {json.dumps(log)}\n\n"
                
                await asyncio.sleep(2)  # Poll every 2 seconds
        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/logs/statistics")
def get_log_statistics(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
):
    """Get log statistics"""
    try:
        result = log_aggregator.get_log_statistics(start_time, end_time)
        return result
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/errors")
def get_error_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
):
    """Get error log summary"""
    try:
        result = log_aggregator.get_error_summary(hours=hours)
        return {"errors": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Kafka endpoints
@router.get("/kafka/topics")
def get_kafka_topics():
    """Get list of Kafka topics"""
    try:
        topics = kafka_monitor.get_topics()
        return {"topics": topics, "count": len(topics)}
    except Exception as e:
        logger.error(f"Error getting Kafka topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kafka/topics/{topic_name}")
def get_topic_details(topic_name: str):
    """Get details for a specific topic"""
    try:
        metrics = kafka_monitor.get_topic_metrics(topic_name)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Topic {topic_name} not found")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kafka/consumers")
def get_consumer_groups():
    """Get consumer group information"""
    try:
        groups = kafka_monitor.get_consumer_groups()
        return {"consumer_groups": groups, "count": len(groups)}
    except Exception as e:
        logger.error(f"Error getting consumer groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kafka/consumers/{group_id}/lag")
def get_consumer_lag(group_id: str, topic: Optional[str] = None):
    """Get consumer lag for a group"""
    try:
        lag = kafka_monitor.get_consumer_lag(group_id, topic)
        return {"group_id": group_id, "topic": topic, "lag": lag}
    except Exception as e:
        logger.error(f"Error getting consumer lag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kafka/metrics")
def get_kafka_metrics():
    """Get overall Kafka metrics"""
    try:
        metrics = kafka_monitor.get_kafka_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting Kafka metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Redis endpoints
@router.get("/redis/stats")
def get_redis_stats():
    """Get Redis statistics"""
    try:
        stats = redis_monitor.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting Redis stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/keys")
def get_redis_keys(pattern: Optional[str] = Query("*", description="Key pattern")):
    """Get Redis key patterns and counts"""
    try:
        if pattern == "*":
            patterns = redis_monitor.get_key_patterns()
            return {"patterns": patterns}
        else:
            count = redis_monitor.get_key_count_by_pattern(pattern)
            return {"pattern": pattern, "count": count}
    except Exception as e:
        logger.error(f"Error getting Redis keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/cache-stats")
def get_cache_stats():
    """Get cache hit/miss statistics"""
    try:
        stats = redis_monitor.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/metrics")
def get_redis_metrics():
    """Get all Redis metrics"""
    try:
        metrics = redis_monitor.get_redis_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting Redis metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Service health endpoints
@router.get("/services/health")
def get_service_health():
    """Get health status of all services"""
    try:
        health = metrics_collector.get_service_health_sync()
        return {"services": health}
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/metrics")
def get_service_metrics():
    """Get service metrics"""
    try:
        metrics = metrics_collector.get_service_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting service metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}/uptime")
def get_service_uptime(service_name: str):
    """Get uptime information for a service"""
    try:
        uptime = metrics_collector.get_service_uptime(service_name)
        return uptime
    except Exception as e:
        logger.error(f"Error getting service uptime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard endpoint
@router.get("/dashboard")
def get_dashboard_data():
    """Get aggregated dashboard data"""
    try:
        # Get all metrics in parallel
        service_health = metrics_collector.get_service_health_sync()
        service_metrics = metrics_collector.get_service_metrics()
        kafka_metrics = kafka_monitor.get_kafka_metrics()
        redis_metrics = redis_monitor.get_redis_metrics()
        log_stats = log_aggregator.get_log_statistics(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow()
        )
        
        return {
            "services": {
                "health": service_health,
                "metrics": service_metrics,
            },
            "kafka": kafka_metrics,
            "redis": redis_metrics,
            "logs": log_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

