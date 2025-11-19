"""
Repository layer for auth service
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from shared.common.errors import ResourceNotFoundError, ValidationError
from app.schemas import User, UserOrganization, RefreshToken
from app.models import UserCreate
from app.utils import get_password_hash
from app.config import settings


class UserRepository:
    """Repository for user operations"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str, organization_id: UUID) -> Optional[User]:
        """Get user by email and organization (tenant-scoped)"""
        return db.query(User).filter(
            and_(
                User.email == email,
                User.organization_id == organization_id
            )
        ).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str, organization_id: UUID) -> Optional[User]:
        """Get user by username and organization (tenant-scoped)"""
        return db.query(User).filter(
            and_(
                User.username == username,
                User.organization_id == organization_id
            )
        ).first()
    
    @staticmethod
    def create(db: Session, user_data: UserCreate) -> User:
        """Create new user (tenant-scoped)"""
        # Check if email exists in this organization
        if UserRepository.get_by_email(db, user_data.email, user_data.organization_id):
            raise ValidationError(f"User with email '{user_data.email}' already exists in this organization")
        
        # Check if username exists in this organization
        if UserRepository.get_by_username(db, user_data.username, user_data.organization_id):
            raise ValidationError(f"User with username '{user_data.username}' already exists in this organization")
        
        # Create user (tenant-scoped)
        user = User(
            organization_id=user_data.organization_id,
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            user_type=user_data.user_type if hasattr(user_data, 'user_type') else 'employee',
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=user_data.is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create user-organization relationship
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=user_data.organization_id,
            role=user_data.role
        )
        db.add(user_org)
        db.commit()
        
        return user
    
    @staticmethod
    def authenticate(db: Session, email: str, password: str, organization_id: Optional[UUID] = None) -> Optional[User]:
        """Authenticate user (tenant-scoped or super admin)"""
        from app.utils import verify_password
        
        # If organization_id provided, use tenant-scoped authentication
        if organization_id:
            user = UserRepository.get_by_email(db, email, organization_id)
        else:
            # For super admin login, find user by email only (must be superuser)
            user = db.query(User).filter(User.email == email).first()
            if user and not user.is_superuser:
                # Non-superuser trying to login without organization_id
                return None
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        return user


class UserOrganizationRepository:
    """Repository for user-organization operations"""
    
    @staticmethod
    def get_by_user_and_org(
        db: Session,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[UserOrganization]:
        """Get user-organization relationship"""
        return db.query(UserOrganization).filter(
            and_(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == organization_id
            )
        ).first()
    
    @staticmethod
    def list_by_user(db: Session, user_id: UUID) -> list[UserOrganization]:
        """List all organizations for user"""
        return db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.is_active == True
        ).all()
    
    @staticmethod
    def list_by_organization(db: Session, organization_id: UUID) -> list[UserOrganization]:
        """List all users for organization"""
        return db.query(UserOrganization).filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.is_active == True
        ).all()


class RefreshTokenRepository:
    """Repository for refresh token operations"""
    
    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        token: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Create refresh token"""
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token
    
    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string"""
        return db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
    
    @staticmethod
    def revoke_token(db: Session, token: str) -> bool:
        """Revoke refresh token"""
        refresh_token = RefreshTokenRepository.get_by_token(db, token)
        if not refresh_token:
            return False
        
        refresh_token.is_revoked = True
        db.commit()
        return True
    
    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: UUID):
        """Revoke all refresh tokens for user"""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        db.commit()

