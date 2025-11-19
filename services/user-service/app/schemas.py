"""
SQLAlchemy database models for user service
Note: These are the same as auth-service, imported here for reference
"""
# In a real microservices setup, these would be in a shared package
# For now, we'll import from the same database
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.base import BaseModel
from shared.database.enums import UserType, ModuleType, InvitationStatus, RelationshipType
import uuid
import secrets

# These schemas match auth-service
# In production, they should be in shared/database/schemas.py

class User(BaseModel):
    """User model - tenant-scoped, same as auth-service"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Tenant-scoped
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(20), nullable=False, default=UserType.EMPLOYEE.value)  # admin, manager, employee, client, supplier
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Unique constraints per organization
    __table_args__ = (
        UniqueConstraint('organization_id', 'email', name='uq_user_org_email'),
        UniqueConstraint('organization_id', 'username', name='uq_user_org_username'),
    )
    
    organizations = relationship("UserOrganization", back_populates="user")


class UserOrganization(BaseModel):
    """User-Organization relationship - same as auth-service"""
    __tablename__ = "user_organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    user = relationship("User", back_populates="organizations")


class Invitation(BaseModel):
    """Invitation model for inviting users to organizations"""
    __tablename__ = "invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    invited_by_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_type = Column(String(20), nullable=False)  # admin, manager, employee, client, supplier
    module_type = Column(String(50), nullable=True)  # PROJECT, FINANCE, etc. - nullable for org-wide
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default=InvitationStatus.PENDING.value)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    invitation_metadata = Column(JSON, nullable=True)  # Additional context (project_id, etc.) - renamed from 'metadata' (SQLAlchemy reserved)
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'email', 'status', name='uq_invitation_org_email_status'),
    )
    
    def __init__(self, **kwargs):
        if 'invitation_token' not in kwargs:
            kwargs['invitation_token'] = secrets.token_urlsafe(32)
        super().__init__(**kwargs)


# Module-specific relationship tables
# These will be moved to their respective services when implemented

class UserProjectRelationship(BaseModel):
    """User-Project relationship for project module"""
    __tablename__ = "user_project_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Nullable for org-level access
    relationship_type = Column(String(20), nullable=False)  # employee, client
    role = Column(String(50), nullable=False)  # viewer, editor, manager
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', name='uq_user_project'),
    )


class UserFinanceRelationship(BaseModel):
    """User-Finance relationship for finance module"""
    __tablename__ = "user_finance_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    relationship_type = Column(String(20), nullable=False)  # employee, supplier, vendor
    role = Column(String(50), nullable=False)  # viewer, editor, manager
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'organization_id', 'relationship_type', name='uq_user_finance'),
    )

