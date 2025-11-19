"""
Pydantic models for auth service API
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Authentication models
class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str
    organization_id: Optional[UUID] = None  # Optional - required for tenant users, optional for super admins


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class RegisterRequest(BaseModel):
    """Registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: UUID  # Required for registration


# User models
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Request model for creating user"""
    password: str = Field(..., min_length=8)
    organization_id: UUID
    user_type: str = "employee"  # admin, manager, employee, client, supplier
    role: str = "employee"  # admin, employee, client (for UserOrganization)


class UserResponse(UserBase):
    """Response model for user"""
    id: UUID
    organization_id: UUID
    user_type: str  # admin, manager, employee, client, supplier
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class UserOrganizationResponse(BaseModel):
    """Response model for user-organization relationship"""
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class CurrentUserResponse(UserResponse):
    """Response model for current user with organization info"""
    current_organization_id: Optional[UUID] = None
    organizations: List[UserOrganizationResponse] = []

