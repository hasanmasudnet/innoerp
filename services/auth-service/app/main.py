"""
Main FastAPI application for auth service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth
from shared.common.logging import setup_logger

# Setup logger
logger = setup_logger(settings.service_name, level="INFO")

# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization service",
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
app.include_router(auth.router, prefix=settings.api_prefix)


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

