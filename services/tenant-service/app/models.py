"""
Pydantic models for tenant service API
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# Organization models
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    subdomain: Optional[str] = Field(None, min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    owner_email: EmailStr
    owner_name: str = Field(..., min_length=1, max_length=255)


class OrganizationCreate(OrganizationBase):
    """Request model for creating organization"""
    pass


class TenantSignupRequest(BaseModel):
    """Request model for tenant signup"""
    business_name: str = Field(..., min_length=1, max_length=255)
    subdomain: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    owner_email: EmailStr
    owner_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6)


class SubdomainCheckRequest(BaseModel):
    """Request model for subdomain availability check"""
    subdomain: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")


class SubdomainCheckResponse(BaseModel):
    """Response model for subdomain check"""
    available: bool
    subdomain: str
    message: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Request model for updating organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Response model for organization"""
    id: UUID
    is_active: bool
    trial_ends_at: Optional[datetime]
    stripe_customer_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantStatsResponse(BaseModel):
    """Response model for tenant statistics"""
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    expired_tenants: int
    subscriptions_active: int
    subscriptions_trial: int
    subscriptions_expired: int


# Subscription Plan models
class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    stripe_price_id: str
    price_monthly: Decimal
    max_users: Optional[int] = None
    max_projects: Optional[int] = None
    features: List[str] = Field(default_factory=list)
    limits: Dict[str, Any] = Field(default_factory=dict)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Request model for creating subscription plan"""
    pass


class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Response model for subscription plan"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Subscription models
class OrganizationSubscriptionResponse(BaseModel):
    """Response model for organization subscription"""
    id: UUID
    organization_id: UUID
    plan_id: UUID
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    plan: SubscriptionPlanResponse
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Module configuration models
class OrganizationModuleBase(BaseModel):
    module_id: str = Field(..., min_length=1, max_length=100)
    is_enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class OrganizationModuleCreate(OrganizationModuleBase):
    """Request model for creating organization module"""
    pass


class OrganizationModuleUpdate(BaseModel):
    """Request model for updating organization module"""
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class OrganizationModuleResponse(OrganizationModuleBase):
    """Response model for organization module"""
    id: UUID
    organization_id: UUID
    enabled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Branding models
class OrganizationBrandingUpdate(BaseModel):
    """Request model for updating organization branding"""
    company_name: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    font_family: Optional[str] = Field(None, max_length=100)
    heading_font: Optional[str] = Field(None, max_length=100)
    theme_preset: Optional[str] = Field(None, max_length=50)
    custom_css: Optional[str] = None


class OrganizationBrandingResponse(BaseModel):
    """Response model for organization branding"""
    id: UUID
    organization_id: UUID
    company_name: Optional[str]
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: str
    secondary_color: str
    accent_color: str
    font_family: Optional[str]
    heading_font: Optional[str]
    theme_preset: Optional[str]
    custom_css: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Tenant Detail models for super admin
class TenantUsageResponse(BaseModel):
    """Response model for tenant usage statistics"""
    total_users: int
    active_users: int
    total_projects: Optional[int] = None
    storage_used_mb: Optional[float] = None
    api_calls_this_month: Optional[int] = None
    last_active: Optional[datetime] = None


class TenantDetailResponse(BaseModel):
    """Comprehensive tenant information for super admin"""
    organization: OrganizationResponse
    subscription: Optional[OrganizationSubscriptionResponse] = None
    branding: Optional[OrganizationBrandingResponse] = None
    modules: List[OrganizationModuleResponse] = Field(default_factory=list)
    usage: Optional[TenantUsageResponse] = None


class TenantStatusUpdate(BaseModel):
    """Request model for updating tenant status"""
    is_active: bool


class TenantTrialUpdate(BaseModel):
    """Request model for extending trial"""
    days: int = Field(..., gt=0, le=365)


# Subscription Plan management
class SubscriptionPlanUpdate(BaseModel):
    """Request model for updating subscription plan"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    stripe_price_id: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    max_users: Optional[int] = None
    max_projects: Optional[int] = None
    features: Optional[List[str]] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# Subscription Orders and Payments
class SubscriptionOrderResponse(BaseModel):
    """Response model for subscription order/change history"""
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    order_type: str  # new, upgrade, downgrade, cancel, renew
    plan_id: UUID
    plan_name: str
    amount: Decimal
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentTransactionResponse(BaseModel):
    """Response model for payment transaction details"""
    id: UUID
    organization_id: UUID
    subscription_id: Optional[UUID] = None
    amount: Decimal
    currency: str
    status: str  # succeeded, pending, failed, refunded
    stripe_payment_intent_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Subscription list with filters
class SubscriptionListFilters(BaseModel):
    """Filters for listing subscriptions"""
    status: Optional[str] = None
    plan_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 100
