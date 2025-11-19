"""
Repository layer for user service
Note: This service uses the same database tables as auth-service
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from shared.common.errors import ResourceNotFoundError, ValidationError
from app.schemas import User, UserOrganization, Invitation
from shared.database.enums import InvitationStatus


class UserRepository:
    """Repository for user operations"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str, organization_id: Optional[UUID] = None) -> Optional[User]:
        """Get user by email (optionally filtered by organization)"""
        query = db.query(User).filter(User.email == email)
        if organization_id:
            query = query.filter(User.organization_id == organization_id)
        return query.first()
    
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
    def update_profile(
        db: Session,
        user_id: UUID,
        profile_data: dict
    ) -> User:
        """Update user profile"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        # Check email uniqueness if changing email
        if 'email' in profile_data and profile_data['email'] != user.email:
            existing = UserRepository.get_by_email(db, profile_data['email'])
            if existing:
                raise ValidationError(f"Email '{profile_data['email']}' already exists")
        
        for key, value in profile_data.items():
            if value is not None:
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
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
    def list_by_user(db: Session, user_id: UUID) -> List[UserOrganization]:
        """List all organizations for user"""
        return db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id
        ).all()
    
    @staticmethod
    def list_by_organization(db: Session, organization_id: UUID) -> List[UserOrganization]:
        """List all users for organization"""
        return db.query(UserOrganization).filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.is_active == True
        ).all()
    
    @staticmethod
    def update_role(
        db: Session,
        user_id: UUID,
        organization_id: UUID,
        role: str
    ) -> UserOrganization:
        """Update user role in organization"""
        user_org = UserOrganizationRepository.get_by_user_and_org(db, user_id, organization_id)
        if not user_org:
            raise ResourceNotFoundError("User-organization relationship not found")
        
        user_org.role = role
        db.commit()
        db.refresh(user_org)
        return user_org


class InvitationRepository:
    """Repository for invitation operations"""
    
    @staticmethod
    def create(
        db: Session,
        organization_id: UUID,
        email: str,
        invited_by_user_id: UUID,
        user_type: str,
        module_type: Optional[str] = None,
        expires_in_days: int = 7,
        invitation_metadata: Optional[dict] = None
    ) -> Invitation:
        """Create new invitation"""
        # Check for existing pending invitation
        existing = db.query(Invitation).filter(
            and_(
                Invitation.organization_id == organization_id,
                Invitation.email == email,
                Invitation.status == InvitationStatus.PENDING.value
            )
        ).first()
        
        if existing:
            raise ValidationError(f"Pending invitation already exists for {email}")
        
        invitation = Invitation(
            organization_id=organization_id,
            email=email,
            invited_by_user_id=invited_by_user_id,
            user_type=user_type,
            module_type=module_type,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            invitation_metadata=invitation_metadata
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation
    
    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[Invitation]:
        """Get invitation by token"""
        return db.query(Invitation).filter(
            Invitation.invitation_token == token
        ).first()
    
    @staticmethod
    def get_by_id(db: Session, invitation_id: UUID) -> Optional[Invitation]:
        """Get invitation by ID"""
        return db.query(Invitation).filter(Invitation.id == invitation_id).first()
    
    @staticmethod
    def list_by_organization(
        db: Session,
        organization_id: UUID,
        status: Optional[str] = None
    ) -> List[Invitation]:
        """List invitations for organization"""
        query = db.query(Invitation).filter(
            Invitation.organization_id == organization_id
        )
        if status:
            query = query.filter(Invitation.status == status)
        return query.order_by(Invitation.created_at.desc()).all()
    
    @staticmethod
    def update_status(
        db: Session,
        invitation_id: UUID,
        status: str,
        accepted_at: Optional[datetime] = None
    ) -> Invitation:
        """Update invitation status"""
        invitation = InvitationRepository.get_by_id(db, invitation_id)
        if not invitation:
            raise ResourceNotFoundError(f"Invitation {invitation_id} not found")
        
        invitation.status = status
        if accepted_at:
            invitation.accepted_at = accepted_at
        db.commit()
        db.refresh(invitation)
        return invitation
    
    @staticmethod
    def revoke(db: Session, invitation_id: UUID) -> Invitation:
        """Revoke invitation"""
        return InvitationRepository.update_status(
            db, invitation_id, InvitationStatus.REVOKED.value
        )
    
    @staticmethod
    def mark_expired(db: Session, invitation_id: UUID) -> Invitation:
        """Mark invitation as expired"""
        return InvitationRepository.update_status(
            db, invitation_id, InvitationStatus.EXPIRED.value
        )

