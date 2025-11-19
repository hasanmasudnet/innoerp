"""
Configuration for tenant service
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Service
    service_name: str = "tenant-service"
    service_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database (from .env - local PostgreSQL server)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/innoerp"
    )
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )
    
    # Stripe
    stripe_secret_key: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

