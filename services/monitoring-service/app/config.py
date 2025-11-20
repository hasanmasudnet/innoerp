"""
Configuration for monitoring service
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    service_name: str = "monitoring-service"
    service_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_prefix: str = "innoerp"
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0
    redis_url: str = ""
    
    # Service URLs for health checks
    api_gateway_url: str = "http://localhost:8000"
    tenant_service_url: str = "http://localhost:8001"
    auth_service_url: str = "http://localhost:8002"
    user_service_url: str = "http://localhost:8003"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

