"""
Tenant middleware for API gateway
"""
from fastapi import Request
from typing import Optional
from uuid import UUID
import httpx
from app.config import settings


async def get_tenant_from_subdomain(subdomain: str) -> Optional[UUID]:
    """
    Get tenant organization ID from subdomain
    
    Returns:
        Organization ID if found, None otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.tenant_service_url}/api/v1/organizations/subdomain/{subdomain}",
                timeout=5.0
            )
            if response.status_code == 200:
                org_data = response.json()
                return UUID(org_data.get("id"))
            return None
    except Exception:
        return None


def extract_subdomain(request: Request) -> Optional[str]:
    """
    Extract subdomain from request host
    
    Returns:
        Subdomain if found, None otherwise
    """
    host = request.headers.get("host", "")
    if not host:
        return None
    
    parts = host.split(".")
    if len(parts) >= 3:
        subdomain = parts[0]
        if subdomain not in ["www", "api", "admin"]:
            return subdomain
    return None

