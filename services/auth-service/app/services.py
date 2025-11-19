"""
Business logic layer for auth service
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from shared.common.errors import UnauthorizedError, ValidationError
from app.repositories import (
    UserRepository, UserOrganizationRepository, RefreshTokenRepository
)
from app.models import (
    LoginRequest, RegisterRequest, TokenResponse,
    UserResponse, CurrentUserResponse, UserOrganizationResponse
)
from app.utils import (
    create_access_token, create_refresh_token, decode_token
)
from app.config import settings
from app.kafka.producer import publish_auth_event
from shared.kafka.schemas import UserAuthenticatedEvent, UserCreatedEvent


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def login(
        db: Session,
        login_data: LoginRequest
    ) -> TokenResponse:
        """Authenticate user and return tokens"""
        # For super admin login, organization_id is optional
        # For regular users, organization_id is required
        user = UserRepository.authenticate(
            db, 
            login_data.email, 
            login_data.password, 
            login_data.organization_id
        )
        if not user:
            raise UnauthorizedError("Invalid email or password")
        
        # For super admin login without organization_id
        if not login_data.organization_id:
            if not user.is_superuser:
                raise UnauthorizedError("Super admin access required. Please provide organization_id for tenant login.")
            # Super admin login - use None for organization_id
            org_id = None
        else:
            # Regular tenant-scoped login
            # Verify user belongs to organization (should already be verified by tenant-scoped query)
            user_org = UserOrganizationRepository.get_by_user_and_org(
                db, user.id, login_data.organization_id
            )
            if not user_org or not user_org.is_active:
                raise UnauthorizedError("User does not belong to this organization")
            org_id = login_data.organization_id
        
        # Create tokens
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_superuser": user.is_superuser
        }
        
        # Only include organization_id in token if it exists
        if org_id:
            access_token_data["organization_id"] = str(org_id)
        
        refresh_token_data = {
            "sub": str(user.id)
        }
        
        # Include organization_id in refresh token if it exists
        if org_id:
            refresh_token_data["organization_id"] = str(org_id)
        
        access_token = create_access_token(access_token_data)
        refresh_token_str = create_refresh_token(refresh_token_data)
        
        # Store refresh token
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        RefreshTokenRepository.create(db, user.id, refresh_token_str, expires_at)
        
        # Publish event (wrap in try/except to not fail login if Kafka is down)
        try:
            # For super admin, use user's organization_id if available, or skip event
            event_org_id = org_id if org_id else (user.organization_id if user.organization_id else None)
            if event_org_id:
                event = UserAuthenticatedEvent(
                    organization_id=event_org_id,
                    user_id=user.id,
                    payload={
                        "user_id": str(user.id),
                        "email": user.email,
                        "organization_id": str(event_org_id),
                        "is_superuser": user.is_superuser
                    }
                )
                publish_auth_event("user.authenticated", event)
        except Exception as e:
            # Log error but don't fail login
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to publish auth event: {e}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    @staticmethod
    def refresh_token(
        db: Session,
        refresh_token: str
    ) -> TokenResponse:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid refresh token")
        
        # Check if token exists in database
        token_record = RefreshTokenRepository.get_by_token(db, refresh_token)
        if not token_record:
            raise UnauthorizedError("Refresh token not found or expired")
        
        user_id = UUID(payload.get("sub"))
        organization_id_str = payload.get("organization_id")
        
        # Get user
        user = UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        
        # For super admin, organization_id might not be in token
        if organization_id_str:
            organization_id = UUID(organization_id_str)
            # Verify user belongs to organization (for tenant users)
            if not user.is_superuser:
                user_org = UserOrganizationRepository.get_by_user_and_org(
                    db, user_id, organization_id
                )
                if not user_org or not user_org.is_active:
                    raise UnauthorizedError("User does not belong to this organization")
        else:
            # Super admin without organization_id
            if not user.is_superuser:
                raise UnauthorizedError("Invalid token: organization_id required for non-superuser")
            organization_id = None
        
        # Create new access token
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_superuser": user.is_superuser
        }
        
        # Only include organization_id if it exists
        if organization_id:
            access_token_data["organization_id"] = str(organization_id)
        
        access_token = create_access_token(access_token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Reuse same refresh token
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    @staticmethod
    def logout(db: Session, refresh_token: str) -> bool:
        """Logout user by revoking refresh token"""
        return RefreshTokenRepository.revoke_token(db, refresh_token)
    
    @staticmethod
    def register(
        db: Session,
        register_data: RegisterRequest
    ) -> UserResponse:
        """Register new user"""
        user = UserRepository.create(db, register_data)
        
        # Publish event (wrap in try/except to not fail registration if Kafka is down)
        try:
            event = UserCreatedEvent(
                organization_id=register_data.organization_id,
                user_id=user.id,
                payload={
                    "user_id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "organization_id": str(register_data.organization_id)
                }
            )
            publish_auth_event("user.created", event)
        except Exception as e:
            # Log error but don't fail registration
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to publish user created event: {e}")
        
        return UserResponse.model_validate(user)


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def get_current_user(
        db: Session,
        user_id: UUID,
        organization_id: Optional[UUID] = None
    ) -> CurrentUserResponse:
        """Get current user with organization info"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        # Get user organizations
        user_orgs = UserOrganizationRepository.list_by_user(db, user_id)
        
        response = CurrentUserResponse.model_validate(user)
        response.organizations = [UserOrganizationResponse.model_validate(uo) for uo in user_orgs]
        
        if organization_id:
            response.current_organization_id = organization_id
        elif user_orgs:
            response.current_organization_id = user_orgs[0].organization_id
        
        return response

