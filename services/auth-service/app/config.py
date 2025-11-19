"""
Configuration for auth service
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Service
    service_name: str = "auth-service"
    service_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
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
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

