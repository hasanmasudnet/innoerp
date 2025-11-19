"""
Main FastAPI application for API gateway
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, SERVICE_REGISTRY
from app.routers import proxy
from shared.common.logging import setup_logger

# Setup logger
logger = setup_logger(settings.service_name, level="INFO")

# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Main API gateway for innoERP",
    version=settings.service_version
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(proxy.router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "services": list(SERVICE_REGISTRY.keys())
    }


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(f"{settings.service_name} starting up...")
    logger.info(f"Registered services: {list(SERVICE_REGISTRY.keys())}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info(f"{settings.service_name} shutting down...")

