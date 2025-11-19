"""
Business logic layer for user service
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from shared.common.errors import ResourceNotFoundError, ValidationError, UnauthorizedError
from app.repositories import (
    UserRepository, UserOrganizationRepository, InvitationRepository
)
from app.models import (
    UserProfileUpdate,
    UserResponse, UserOrganizationResponse, UserWithOrganizationsResponse
)
from app.kafka.producer import publish_user_event
from shared.kafka.schemas import UserUpdatedEvent, UserRoleChangedEvent
from shared.database.enums import InvitationStatus, UserType
from app.utils import get_password_hash


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def get_user(
        db: Session,
        user_id: UUID
    ) -> UserResponse:
        """Get user by ID"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        return UserResponse.from_orm(user)
    
    @staticmethod
    def update_profile(
        db: Session,
        user_id: UUID,
        profile_data: UserProfileUpdate
    ) -> UserResponse:
        """Update user profile"""
        update_dict = profile_data.dict(exclude_unset=True)
        user = UserRepository.update_profile(db, user_id, update_dict)
        
        # Publish event
        event = UserUpdatedEvent(
            organization_id=None,  # Profile update is not org-specific
            user_id=user.id,
            payload={
                "user_id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        )
        publish_user_event("user.updated", event)
        
        return UserResponse.from_orm(user)
    
    @staticmethod
    def get_user_with_organizations(
        db: Session,
        user_id: UUID
    ) -> UserWithOrganizationsResponse:
        """Get user with all organizations"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        user_orgs = UserOrganizationRepository.list_by_user(db, user_id)
        
        response = UserWithOrganizationsResponse.from_orm(user)
        response.organizations = [UserOrganizationResponse.from_orm(uo) for uo in user_orgs]
        
        return response
    
    @staticmethod
    def list_users_by_organization(
        db: Session,
        organization_id: UUID
    ) -> List[UserResponse]:
        """List all users in organization"""
        user_orgs = UserOrganizationRepository.list_by_organization(db, organization_id)
        users = [UserRepository.get_by_id(db, uo.user_id) for uo in user_orgs]
        return [UserResponse.from_orm(u) for u in users if u]
    
    @staticmethod
    def update_user_role(
        db: Session,
        user_id: UUID,
        organization_id: UUID,
        role: str
    ) -> UserOrganizationResponse:
        """Update user role in organization"""
        user_org = UserOrganizationRepository.update_role(db, user_id, organization_id, role)
        
        # Publish event
        event = UserRoleChangedEvent(
            organization_id=organization_id,
            user_id=user_id,
            payload={
                "user_id": str(user_id),
                "organization_id": str(organization_id),
                "role": role
            }
        )
        publish_user_event("user.role.changed", event)
        
        return UserOrganizationResponse.from_orm(user_org)


class InvitationService:
    """Service for invitation operations"""
    
    @staticmethod
    def send_invitation(
        db: Session,
        organization_id: UUID,
        email: str,
        invited_by_user_id: UUID,
        user_type: str,
        module_type: Optional[str] = None,
        invitation_metadata: Optional[dict] = None
    ):
        """Send invitation to user"""
        # Validate user_type
        valid_types = [ut.value for ut in UserType]
        if user_type not in valid_types:
            raise ValidationError(f"Invalid user_type. Must be one of: {', '.join(valid_types)}")
        
        # Check if user already exists in organization
        user = UserRepository.get_by_email(db, email)
        if user and user.organization_id == organization_id:
            raise ValidationError(f"User with email '{email}' already exists in this organization")
        
        # Create invitation
        invitation = InvitationRepository.create(
            db=db,
            organization_id=organization_id,
            email=email,
            invited_by_user_id=invited_by_user_id,
            user_type=user_type,
            module_type=module_type,
            invitation_metadata=invitation_metadata
        )
        
        # TODO: Send email notification with invitation link
        # For now, return invitation with token
        
        return invitation
    
    @staticmethod
    def accept_invitation(
        db: Session,
        token: str,
        password: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ):
        """Accept invitation and create user account"""
        invitation = InvitationRepository.get_by_token(db, token)
        if not invitation:
            raise ResourceNotFoundError("Invitation not found")
        
        # Check if invitation is valid
        if invitation.status != InvitationStatus.PENDING.value:
            raise ValidationError(f"Invitation is {invitation.status}")
        
        # Check if expired
        if invitation.expires_at < datetime.utcnow():
            InvitationRepository.mark_expired(db, invitation.id)
            raise ValidationError("Invitation has expired")
        
        # Check if user already exists
        user = UserRepository.get_by_email(db, invitation.email)
        if user and user.organization_id == invitation.organization_id:
            raise ValidationError("User already exists for this invitation")
        
        # Generate username if not provided
        if not username:
            username = invitation.email.split('@')[0]
            # Make unique by appending number if needed
            base_username = username
            counter = 1
            while UserRepository.get_by_username(db, username, invitation.organization_id):
                username = f"{base_username}{counter}"
                counter += 1
        
        # Create user account
        from app.schemas import User
        user = User(
            organization_id=invitation.organization_id,
            email=invitation.email,
            username=username,
            password_hash=get_password_hash(password),
            user_type=invitation.user_type,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create user-organization relationship
        from app.schemas import UserOrganization
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.user_type  # Use user_type as default role
        )
        db.add(user_org)
        
        # Mark invitation as accepted
        InvitationRepository.update_status(
            db, invitation.id, InvitationStatus.ACCEPTED.value, datetime.utcnow()
        )
        
        db.commit()
        
        # TODO: Publish UserInvitedEvent
        
        return user
    
    @staticmethod
    def list_invitations(
        db: Session,
        organization_id: UUID,
        status: Optional[str] = None
    ) -> List:
        """List invitations for organization"""
        return InvitationRepository.list_by_organization(db, organization_id, status)
    
    @staticmethod
    def revoke_invitation(
        db: Session,
        invitation_id: UUID,
        organization_id: UUID
    ):
        """Revoke invitation"""
        invitation = InvitationRepository.get_by_id(db, invitation_id)
        if not invitation:
            raise ResourceNotFoundError(f"Invitation {invitation_id} not found")
        
        if invitation.organization_id != organization_id:
            raise UnauthorizedError("Cannot revoke invitation from different organization")
        
        if invitation.status != InvitationStatus.PENDING.value:
            raise ValidationError(f"Cannot revoke invitation with status {invitation.status}")
        
        return InvitationRepository.revoke(db, invitation_id)


class UserRelationshipService:
    """Service for user relationship operations"""
    
    @staticmethod
    def update_user_type(
        db: Session,
        user_id: UUID,
        organization_id: UUID,
        new_user_type: str
    ) -> UserResponse:
        """Update user type"""
        # Validate user_type
        valid_types = [ut.value for ut in UserType]
        if new_user_type not in valid_types:
            raise ValidationError(f"Invalid user_type. Must be one of: {', '.join(valid_types)}")
        
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        if user.organization_id != organization_id:
            raise UnauthorizedError("User does not belong to this organization")
        
        user.user_type = new_user_type
        db.commit()
        db.refresh(user)
        
        # TODO: Publish UserTypeChangedEvent
        
        return UserResponse.from_orm(user)
    
    @staticmethod
    def get_user_relationships(
        db: Session,
        user_id: UUID,
        organization_id: UUID
    ) -> dict:
        """Get all module-specific relationships for user"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        if user.organization_id != organization_id:
            raise UnauthorizedError("User does not belong to this organization")
        
        # TODO: Query module-specific relationship tables when services are implemented
        # For now, return empty structure
        return {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "user_type": user.user_type,
            "relationships": {
                "project": [],  # Will be populated when project-service is implemented
                "finance": []   # Will be populated when finance-service is implemented
            }
        }

