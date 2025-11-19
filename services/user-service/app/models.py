"""
Pydantic models for user service API
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class UserProfileUpdate(BaseModel):
    """Request model for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    """Response model for user"""
    id: UUID
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserOrganizationResponse(BaseModel):
    """Response model for user-organization relationship"""
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserWithOrganizationsResponse(UserResponse):
    """User response with organizations"""
    organizations: List[UserOrganizationResponse] = []

