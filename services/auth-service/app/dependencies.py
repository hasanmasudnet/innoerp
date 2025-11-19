"""
Dependencies for auth service
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from shared.database.base import get_db
from app.utils import decode_token
from app.repositories import UserRepository, UserOrganizationRepository
from shared.common.errors import UnauthorizedError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[UUID, Optional[UUID]]:
    """
    Dependency to get current authenticated user
    
    Returns:
        Tuple of (user_id, organization_id)
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = UUID(payload.get("sub"))
    organization_id = UUID(payload.get("organization_id")) if payload.get("organization_id") else None
    
    # Verify user exists and is active
    user = UserRepository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user belongs to organization if specified
    if organization_id:
        user_org = UserOrganizationRepository.get_by_user_and_org(db, user_id, organization_id)
        if not user_org or not user_org.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to this organization",
            )
    
    return user_id, organization_id

