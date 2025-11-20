"""
Configuration for API gateway
"""
import os
from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """Application settings"""
    
    # Service
    service_name: str = "api-gateway"
    service_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Service URLs
    tenant_service_url: str = os.getenv("TENANT_SERVICE_URL", "http://localhost:8001")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://localhost:8003")
    project_service_url: str = os.getenv("PROJECT_SERVICE_URL", "http://localhost:8004")
    employee_service_url: str = os.getenv("EMPLOYEE_SERVICE_URL", "http://localhost:8005")
    monitoring_service_url: str = os.getenv("MONITORING_SERVICE_URL", "http://localhost:8006")
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Service registry
SERVICE_REGISTRY: Dict[str, str] = {
    "tenants": settings.tenant_service_url,
    "auth": settings.auth_service_url,
    "users": settings.user_service_url,
    "projects": settings.project_service_url,
    "employees": settings.employee_service_url,
    "monitoring": settings.monitoring_service_url,
}

