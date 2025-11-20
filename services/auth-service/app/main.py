"""
Main FastAPI application for auth service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth
from shared.common.logging import get_logger, log_entry_exit
from shared.common.middleware import RequestLoggingMiddleware

# Initialize logger with EALogger
app_name = "auth-service"
logger = get_logger(__name__, app_name=app_name)

# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization service",
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
app.include_router(auth.router, prefix=settings.api_prefix)


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

