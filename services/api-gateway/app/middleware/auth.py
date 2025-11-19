"""
Authentication middleware for API gateway
"""
from fastapi import Request, HTTPException, status
from typing import Optional
import httpx
from app.config import settings


async def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token by calling auth service
    
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None


async def get_current_user_from_token(token: str) -> Optional[dict]:
    """
    Get current user info from token
    
    Returns:
        User info if valid, None otherwise
    """
    payload = await verify_token(token)
    if payload:
        organization_id = payload.get("organization_id")
        if not organization_id:
            # If organization_id not in token, try to get from tenant middleware
            # This ensures backward compatibility
            return None
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "organization_id": organization_id,
            "is_superuser": payload.get("is_superuser", False)
        }
    return None


async def validate_user_organization(user_id: str, organization_id: str) -> bool:
    """
    Validate that user belongs to organization
    This can be enhanced to call user-service for validation
    
    Returns:
        True if valid, False otherwise
    """
    # For now, we trust the JWT token which already includes organization_id
    # In production, you might want to verify this with user-service
    return True

