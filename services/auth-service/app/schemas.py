"""
SQLAlchemy database models for auth service
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database.base import BaseModel
from shared.database.enums import UserType
import uuid


class User(BaseModel):
    """User model - tenant-scoped"""
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
    
    # Relationships
    organizations = relationship("UserOrganization", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")


class UserOrganization(BaseModel):
    """User-Organization relationship"""
    __tablename__ = "user_organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # FK to organizations table
    role = Column(String(50), nullable=False)  # admin, employee, client
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="organizations")


class RefreshToken(BaseModel):
    """Refresh token model"""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

