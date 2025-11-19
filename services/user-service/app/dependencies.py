"""
Dependencies for user service
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from shared.database.base import get_db
from app.utils import decode_token
from app.repositories import UserRepository, UserOrganizationRepository

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UUID:
    """Dependency to get current user ID from token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = UUID(payload.get("sub"))
    
    # Verify user exists
    user = UserRepository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user_id


async def get_current_organization_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[UUID]:
    """Dependency to get current organization ID from token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    org_id = payload.get("organization_id")
    return UUID(org_id) if org_id else None

