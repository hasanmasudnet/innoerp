"""
Main FastAPI application for tenant service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.routers import organizations, subscriptions, modules, industries, module_registry
from shared.common.logging import get_logger, log_entry_exit
from shared.common.middleware import RequestLoggingMiddleware

# Initialize logger with EALogger
app_name = "tenant-service"
logger = get_logger(__name__, app_name=app_name)

# Create FastAPI app
app = FastAPI(
    title="Tenant Service",
    description="Organization and subscription management service",
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
try:
    app.include_router(organizations.router, prefix=settings.api_prefix)
    app.include_router(organizations.org_router, prefix=settings.api_prefix)  # Backward compatibility
    app.include_router(subscriptions.router, prefix=settings.api_prefix)
    app.include_router(modules.router, prefix=settings.api_prefix)
    app.include_router(industries.router, prefix=settings.api_prefix)
    app.include_router(module_registry.router, prefix=settings.api_prefix)
    logger.info("All routers registered successfully")
except Exception as e:
    logger.error(f"Error registering routers: {e}", exc_info=True)
    raise

# Media directory setup (files served through protected endpoint, not static)
media_dir = Path("media")
media_dir.mkdir(exist_ok=True)
branding_dir = media_dir / "branding"
branding_dir.mkdir(exist_ok=True)


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
    
    # Log all registered routes for debugging
    logger.info(
        "Registered API Routes",
        "startup",
        "startup",
        "",
        app_name,
        extra={"routes": [
            {"methods": list(route.methods or []), "path": route.path}
            for route in app.routes
            if hasattr(route, 'path') and hasattr(route, 'methods')
        ]}
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

