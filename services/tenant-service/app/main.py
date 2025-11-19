"""
Main FastAPI application for tenant service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.routers import organizations, subscriptions, modules
from shared.common.logging import setup_logger

# Setup logger
logger = setup_logger(settings.service_name, level="INFO")

# Create FastAPI app
app = FastAPI(
    title="Tenant Service",
    description="Organization and subscription management service",
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
app.include_router(organizations.router, prefix=settings.api_prefix)
app.include_router(organizations.org_router, prefix=settings.api_prefix)  # Backward compatibility
app.include_router(subscriptions.router, prefix=settings.api_prefix)
app.include_router(modules.router, prefix=settings.api_prefix)

# Media directory setup (files served through protected endpoint, not static)
media_dir = Path("media")
media_dir.mkdir(exist_ok=True)
branding_dir = media_dir / "branding"
branding_dir.mkdir(exist_ok=True)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.service_name}


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info(f"{settings.service_name} starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info(f"{settings.service_name} shutting down...")

