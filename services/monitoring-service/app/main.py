"""
Main FastAPI application for monitoring service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import monitoring
from shared.common.logging import get_logger, log_entry_exit
from shared.common.middleware import RequestLoggingMiddleware

# Initialize logger with EALogger
app_name = "monitoring-service"
logger = get_logger(__name__, app_name=app_name)

# Create FastAPI app
app = FastAPI(
    title="Monitoring Service",
    description="Monitoring and observability service for innoERP",
    version=settings.service_version
)

# Request logging middleware (must be first)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitoring.router, prefix=settings.api_prefix)


@app.get("/health")
@log_entry_exit(app_name=app_name)
def health_check():
    """Health check endpoint"""
    logger.info(
        "Health check requested",
        "health_check",
        "GET",
        "",
        app_name
    )
    return {"status": "healthy", "service": settings.service_name}


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(
        f"{settings.service_name} starting up...",
        "startup",
        "startup",
        "",
        app_name
    )
    logger.info(
        f"Elasticsearch: {settings.elasticsearch_url}",
        "startup",
        "startup",
        "",
        app_name,
        extra={"elasticsearch_url": settings.elasticsearch_url}
    )
    logger.info(
        f"Kafka: {settings.kafka_bootstrap_servers}",
        "startup",
        "startup",
        "",
        app_name,
        extra={"kafka_bootstrap_servers": settings.kafka_bootstrap_servers}
    )
    logger.info(
        f"Redis: {settings.redis_host}:{settings.redis_port}",
        "startup",
        "startup",
        "",
        app_name,
        extra={"redis_host": settings.redis_host, "redis_port": settings.redis_port}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info(
        f"{settings.service_name} shutting down...",
        "shutdown",
        "shutdown",
        "",
        app_name
    )

