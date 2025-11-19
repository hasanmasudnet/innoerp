"""
SQLAlchemy database models for tenant service
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database.base import BaseModel, TenantMixin
import uuid


class Organization(BaseModel):
    """Organization/Tenant model"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    subdomain = Column(String(100), unique=True, nullable=True, index=True)
    owner_email = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Stripe
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    subscription = relationship("OrganizationSubscription", back_populates="organization", uselist=False)
    modules = relationship("OrganizationModule", back_populates="organization")


class SubscriptionPlan(BaseModel):
    """Subscription plan model"""
    __tablename__ = "subscription_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # Basic, Pro, Enterprise
    stripe_price_id = Column(String(255), nullable=False, unique=True)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    max_users = Column(Numeric(10, 0), nullable=True)
    max_projects = Column(Numeric(10, 0), nullable=True)
    features = Column(JSON, nullable=False, default=list)
    limits = Column(JSON, nullable=False, default=dict)  # Additional limits
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    subscriptions = relationship("OrganizationSubscription", back_populates="plan")


class OrganizationSubscription(BaseModel):
    """Organization subscription model"""
    __tablename__ = "organization_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(20), nullable=False)  # active, canceled, past_due, trialing
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


class OrganizationModule(BaseModel):
    """Organization module configuration"""
    __tablename__ = "organization_modules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    module_id = Column(String(100), nullable=False)  # project, employee, attendance, etc.
    is_enabled = Column(Boolean, default=True, nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    enabled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="modules")
    
    __table_args__ = (
        {"schema": "public"},
    )


class OrganizationBranding(BaseModel):
    """Organization branding and theme configuration"""
    __tablename__ = "organization_branding"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    company_name = Column(String(255), nullable=True)
    primary_color = Column(String(7), nullable=False, default='#1976d2')
    secondary_color = Column(String(7), nullable=False, default='#dc004e')
    accent_color = Column(String(7), nullable=False, default='#00a86b')
    
    # Typography
    font_family = Column(String(100), nullable=True, default='Inter')
    heading_font = Column(String(100), nullable=True, default='Inter')
    
    # Layout
    sidebar_style = Column(String(50), nullable=True, default='default')
    header_style = Column(String(50), nullable=True, default='default')
    dashboard_layout = Column(String(50), nullable=True, default='grid')
    
    # Custom CSS
    custom_css = Column(String, nullable=True)
    
    # Theme preset
    theme_preset = Column(String(50), nullable=True, default='base')
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

