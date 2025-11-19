"""
User API routes
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from shared.database.base import get_db
from app.models import UserProfileUpdate, UserResponse, UserWithOrganizationsResponse, UserOrganizationResponse
from app.services import UserService, InvitationService, UserRelationshipService
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.dependencies import get_current_user_id, get_current_organization_id
from shared.common.errors import handle_exception

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserWithOrganizationsResponse)
def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user with organizations"""
    try:
        return UserService.get_user_with_organizations(db, user_id)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    profile_data: UserProfileUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        return UserService.update_profile(db, user_id, profile_data)
    except Exception as e:
        raise handle_exception(e)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get user by ID"""
    try:
        return UserService.get_user(db, user_id)
    except Exception as e:
        raise handle_exception(e)


@router.get("/organization/{organization_id}", response_model=List[UserResponse])
def list_users_by_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """List all users in organization"""
    try:
        # Verify user belongs to organization
        if current_org_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access users from different organization"
            )
        return UserService.list_users_by_organization(db, organization_id)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{user_id}/organization/{organization_id}/role", response_model=UserOrganizationResponse)
def update_user_role(
    user_id: UUID,
    organization_id: UUID,
    role: str,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """Update user role in organization"""
    try:
        # Verify user belongs to organization
        if current_org_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify users from different organization"
            )
        return UserService.update_user_role(db, user_id, organization_id, role)
    except Exception as e:
        raise handle_exception(e)


# Invitation models
class InvitationCreate(BaseModel):
    """Request model for creating invitation"""
    email: EmailStr
    user_type: str = Field(..., description="admin, manager, employee, client, supplier")
    module_type: Optional[str] = None
    invitation_metadata: Optional[dict] = None


class InvitationAccept(BaseModel):
    """Request model for accepting invitation"""
    password: str = Field(..., min_length=8)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class InvitationResponse(BaseModel):
    """Response model for invitation"""
    id: UUID
    organization_id: UUID
    email: EmailStr
    user_type: str
    module_type: Optional[str] = None
    invitation_token: str
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Invitation endpoints
@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def send_invitation(
    invitation_data: InvitationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """Send invitation to user"""
    try:
        invitation = InvitationService.send_invitation(
            db=db,
            organization_id=current_org_id,
            email=invitation_data.email,
            invited_by_user_id=current_user_id,
            user_type=invitation_data.user_type,
            module_type=invitation_data.module_type,
            invitation_metadata=invitation_data.invitation_metadata
        )
        return InvitationResponse.model_validate(invitation)
    except Exception as e:
        raise handle_exception(e)


@router.get("/invitations", response_model=List[InvitationResponse])
def list_invitations(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """List invitations for organization"""
    try:
        invitations = InvitationService.list_invitations(
            db=db,
            organization_id=current_org_id,
            status=status_filter
        )
        return [InvitationResponse.model_validate(inv) for inv in invitations]
    except Exception as e:
        raise handle_exception(e)


@router.post("/invitations/{token}/accept", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def accept_invitation(
    token: str,
    accept_data: InvitationAccept,
    db: Session = Depends(get_db)
):
    """Accept invitation and create user account"""
    try:
        user = InvitationService.accept_invitation(
            db=db,
            token=token,
            password=accept_data.password,
            username=accept_data.username,
            first_name=accept_data.first_name,
            last_name=accept_data.last_name
        )
        return UserResponse.model_validate(user)
    except Exception as e:
        raise handle_exception(e)


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """Revoke invitation"""
    try:
        InvitationService.revoke_invitation(
            db=db,
            invitation_id=invitation_id,
            organization_id=current_org_id
        )
        return None
    except Exception as e:
        raise handle_exception(e)


# User relationship endpoints
class UserTypeUpdate(BaseModel):
    """Request model for updating user type"""
    user_type: str = Field(..., description="admin, manager, employee, client, supplier")


@router.patch("/{user_id}/type", response_model=UserResponse)
def update_user_type(
    user_id: UUID,
    type_data: UserTypeUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """Update user type"""
    try:
        return UserRelationshipService.update_user_type(
            db=db,
            user_id=user_id,
            organization_id=current_org_id,
            new_user_type=type_data.user_type
        )
    except Exception as e:
        raise handle_exception(e)


@router.get("/{user_id}/relationships")
def get_user_relationships(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_org_id: UUID = Depends(get_current_organization_id)
):
    """Get all module-specific relationships for user"""
    try:
        return UserRelationshipService.get_user_relationships(
            db=db,
            user_id=user_id,
            organization_id=current_org_id
        )
    except Exception as e:
        raise handle_exception(e)

