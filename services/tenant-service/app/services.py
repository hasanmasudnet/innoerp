"""
Business logic layer for tenant service
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from shared.common.errors import ResourceNotFoundError, TenantInactiveError
from app.repositories import (
    OrganizationRepository,
    SubscriptionPlanRepository,
    OrganizationSubscriptionRepository,
    OrganizationModuleRepository,
    OrganizationBrandingRepository
)
from app.models import (
    OrganizationCreate, OrganizationUpdate,
    OrganizationResponse,
    OrganizationSubscriptionResponse,
    SubscriptionPlanCreate, SubscriptionPlanResponse,
    OrganizationModuleCreate, OrganizationModuleUpdate,
    OrganizationModuleResponse
)
from app.kafka.producer import publish_tenant_event
from shared.kafka.schemas import TenantCreatedEvent, TenantUpdatedEvent


class OrganizationService:
    """Service for organization operations"""
    
    @staticmethod
    def check_subdomain_available(db: Session, subdomain: str) -> bool:
        """Check if subdomain is available"""
        return OrganizationRepository.check_subdomain_available(db, subdomain)
    
    @staticmethod
    def get_tenant_stats(db: Session) -> Dict[str, Any]:
        """Get tenant statistics for super admin"""
        from app.schemas import OrganizationSubscription
        
        total = OrganizationRepository.count_all(db)
        all_orgs = OrganizationRepository.list_all(db, skip=0, limit=10000)  # Get all
        
        active_count = sum(1 for org in all_orgs if org.is_active)
        trial_count = sum(1 for org in all_orgs if org.trial_ends_at and org.trial_ends_at > datetime.utcnow())
        expired_count = sum(1 for org in all_orgs if org.trial_ends_at and org.trial_ends_at <= datetime.utcnow())
        
        # Count subscriptions
        from app.schemas import OrganizationSubscription
        subscriptions = db.query(OrganizationSubscription).all()
        subs_active = sum(1 for sub in subscriptions if sub.status == 'active')
        subs_trial = sum(1 for sub in subscriptions if sub.status == 'trial')
        subs_expired = sum(1 for sub in subscriptions if sub.status in ['expired', 'cancelled'])
        
        return {
            "total_tenants": total,
            "active_tenants": active_count,
            "trial_tenants": trial_count,
            "expired_tenants": expired_count,
            "subscriptions_active": subs_active,
            "subscriptions_trial": subs_trial,
            "subscriptions_expired": subs_expired,
        }
    
    @staticmethod
    def list_all_organizations(db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationResponse]:
        """List all organizations (for super admin)"""
        orgs = OrganizationRepository.list_all(db, skip, limit)
        return [OrganizationResponse.from_orm(org) for org in orgs]
    
    @staticmethod
    def create_organization(
        db: Session,
        org_data: OrganizationCreate,
        trial_days: int = 14
    ) -> OrganizationResponse:
        """Create new organization with trial period"""
        org = OrganizationRepository.create(db, org_data)
        
        # Set trial end date
        if trial_days > 0:
            org.trial_ends_at = datetime.utcnow() + timedelta(days=trial_days)
            db.commit()
            db.refresh(org)
        
        # Publish event
        event = TenantCreatedEvent(
            organization_id=org.id,
            payload={
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "subdomain": org.subdomain,
                "owner_email": org.owner_email
            }
        )
        publish_tenant_event("tenant.created", event)
        
        return OrganizationResponse.from_orm(org)
    
    @staticmethod
    def get_organization(db: Session, organization_id: UUID) -> OrganizationResponse:
        """Get organization by ID"""
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        if not org.is_active:
            raise TenantInactiveError(f"Organization {organization_id} is inactive")
        
        return OrganizationResponse.from_orm(org)
    
    @staticmethod
    def get_organization_by_slug(db: Session, slug: str) -> OrganizationResponse:
        """Get organization by slug"""
        org = OrganizationRepository.get_by_slug(db, slug)
        if not org:
            raise ResourceNotFoundError(f"Organization with slug '{slug}' not found")
        
        if not org.is_active:
            raise TenantInactiveError(f"Organization with slug '{slug}' is inactive")
        
        return OrganizationResponse.from_orm(org)
    
    @staticmethod
    def get_organization_by_subdomain(db: Session, subdomain: str) -> OrganizationResponse:
        """Get organization by subdomain"""
        org = OrganizationRepository.get_by_subdomain(db, subdomain)
        if not org:
            raise ResourceNotFoundError(f"Organization with subdomain '{subdomain}' not found")
        
        if not org.is_active:
            raise TenantInactiveError(f"Organization with subdomain '{subdomain}' is inactive")
        
        return OrganizationResponse.from_orm(org)
    
    @staticmethod
    def update_organization(
        db: Session,
        organization_id: UUID,
        org_data: OrganizationUpdate
    ) -> OrganizationResponse:
        """Update organization"""
        org = OrganizationRepository.update(db, organization_id, org_data)
        
        # Publish event
        event = TenantUpdatedEvent(
            organization_id=org.id,
            payload={
                "id": str(org.id),
                "name": org.name,
                "is_active": org.is_active
            }
        )
        publish_tenant_event("tenant.updated", event)
        
        return OrganizationResponse.from_orm(org)
    
    @staticmethod
    def set_stripe_customer(
        db: Session,
        organization_id: UUID,
        stripe_customer_id: str
    ) -> OrganizationResponse:
        """Set Stripe customer ID for organization"""
        org = OrganizationRepository.set_stripe_customer_id(db, organization_id, stripe_customer_id)
        return OrganizationResponse.from_orm(org)
    
    @staticmethod
    def get_tenant_details(db: Session, organization_id: UUID) -> Dict[str, Any]:
        """Get comprehensive tenant details for super admin"""
        from app.models import TenantDetailResponse, TenantUsageResponse
        from app.repositories import OrganizationModuleRepository, OrganizationBrandingRepository
        
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        # Get subscription
        subscription = SubscriptionService.get_subscription(db, organization_id)
        
        # Get branding
        branding = BrandingService.get_branding(db, organization_id)
        branding_response = None
        if branding:
            from app.models import OrganizationBrandingResponse
            branding_response = OrganizationBrandingResponse.model_validate(branding)
        
        # Get modules
        modules = OrganizationModuleRepository.list_by_organization(db, organization_id)
        from app.models import OrganizationModuleResponse
        modules_response = [OrganizationModuleResponse.model_validate(m) for m in modules]
        
        # Get usage statistics (placeholder - would need user-service integration)
        usage = TenantUsageResponse(
            total_users=0,  # TODO: Get from user-service
            active_users=0,  # TODO: Get from user-service
            total_projects=None,  # TODO: Get from project-service
            storage_used_mb=None,
            api_calls_this_month=None,
            last_active=None
        )
        
        return {
            "organization": OrganizationResponse.model_validate(org),
            "subscription": subscription,
            "branding": branding_response,
            "modules": modules_response,
            "usage": usage
        }
    
    @staticmethod
    def update_tenant_status(
        db: Session,
        organization_id: UUID,
        is_active: bool
    ) -> OrganizationResponse:
        """Activate or deactivate tenant"""
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        org.is_active = is_active
        db.commit()
        db.refresh(org)
        
        # Publish event
        event = TenantUpdatedEvent(
            organization_id=org.id,
            payload={
                "id": str(org.id),
                "name": org.name,
                "is_active": org.is_active
            }
        )
        publish_tenant_event("tenant.updated", event)
        
        return OrganizationResponse.model_validate(org)
    
    @staticmethod
    def extend_trial(
        db: Session,
        organization_id: UUID,
        days: int
    ) -> OrganizationResponse:
        """Extend trial period for tenant"""
        from datetime import timedelta
        
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        if org.trial_ends_at:
            # Extend existing trial
            org.trial_ends_at = org.trial_ends_at + timedelta(days=days)
        else:
            # Set new trial end date
            org.trial_ends_at = datetime.utcnow() + timedelta(days=days)
        
        db.commit()
        db.refresh(org)
        
        return OrganizationResponse.model_validate(org)


class SubscriptionService:
    """Service for subscription operations"""
    
    @staticmethod
    def get_subscription(
        db: Session,
        organization_id: UUID
    ) -> Optional[OrganizationSubscriptionResponse]:
        """Get organization subscription"""
        subscription = OrganizationSubscriptionRepository.get_by_organization_id(db, organization_id)
        if not subscription:
            return None
        
        return OrganizationSubscriptionResponse.model_validate(subscription)
    
    @staticmethod
    def list_subscriptions(
        db: Session,
        status: Optional[str] = None,
        plan_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrganizationSubscriptionResponse]:
        """List all subscriptions with filters"""
        from app.schemas import OrganizationSubscription
        from sqlalchemy import and_
        
        query = db.query(OrganizationSubscription)
        
        if status:
            query = query.filter(OrganizationSubscription.status == status)
        if plan_id:
            query = query.filter(OrganizationSubscription.plan_id == plan_id)
        if organization_id:
            query = query.filter(OrganizationSubscription.organization_id == organization_id)
        
        subscriptions = query.offset(skip).limit(limit).all()
        return [OrganizationSubscriptionResponse.model_validate(sub) for sub in subscriptions]
    
    @staticmethod
    def get_subscription_by_id(
        db: Session,
        subscription_id: UUID
    ) -> Optional[OrganizationSubscriptionResponse]:
        """Get subscription by ID"""
        from app.schemas import OrganizationSubscription
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.id == subscription_id
        ).first()
        if not subscription:
            return None
        return OrganizationSubscriptionResponse.model_validate(subscription)
    
    @staticmethod
    def update_subscription(
        db: Session,
        organization_id: UUID,
        plan_id: UUID,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool = False
    ) -> OrganizationSubscriptionResponse:
        """Update organization subscription"""
        subscription = OrganizationSubscriptionRepository.create_or_update(
            db,
            organization_id,
            plan_id,
            status,
            current_period_start,
            current_period_end,
            cancel_at_period_end
        )
        
        # Publish event
        from shared.kafka.schemas import SubscriptionChangedEvent
        event = SubscriptionChangedEvent(
            organization_id=organization_id,
            payload={
                "subscription_id": str(subscription.id),
                "plan_id": str(plan_id),
                "status": status
            }
        )
        publish_tenant_event("subscription.changed", event)
        
        return OrganizationSubscriptionResponse.model_validate(subscription)


class SubscriptionPlanService:
    """Service for subscription plan management"""
    
    @staticmethod
    def create_plan(
        db: Session,
        plan_data: SubscriptionPlanCreate
    ) -> SubscriptionPlanResponse:
        """Create new subscription plan"""
        from app.models import SubscriptionPlanResponse
        plan = SubscriptionPlanRepository.create(db, plan_data)
        return SubscriptionPlanResponse.model_validate(plan)
    
    @staticmethod
    def update_plan(
        db: Session,
        plan_id: UUID,
        plan_data: dict
    ) -> SubscriptionPlanResponse:
        """Update subscription plan"""
        from app.models import SubscriptionPlanResponse
        plan = SubscriptionPlanRepository.update(db, plan_id, plan_data)
        return SubscriptionPlanResponse.model_validate(plan)
    
    @staticmethod
    def list_plans(
        db: Session,
        active_only: bool = False
    ) -> List[SubscriptionPlanResponse]:
        """List all subscription plans"""
        from app.models import SubscriptionPlanResponse
        plans = SubscriptionPlanRepository.list_all(db, active_only=active_only)
        return [SubscriptionPlanResponse.model_validate(plan) for plan in plans]
    
    @staticmethod
    def get_plan(
        db: Session,
        plan_id: UUID
    ) -> Optional[SubscriptionPlanResponse]:
        """Get subscription plan by ID"""
        from app.models import SubscriptionPlanResponse
        plan = SubscriptionPlanRepository.get_by_id(db, plan_id)
        if not plan:
            return None
        return SubscriptionPlanResponse.model_validate(plan)


class ModuleService:
    """Service for module management"""
    
    @staticmethod
    def enable_module(
        db: Session,
        organization_id: UUID,
        module_data: OrganizationModuleCreate
    ) -> OrganizationModuleResponse:
        """Enable module for organization"""
        module = OrganizationModuleRepository.create_or_update(db, organization_id, module_data)
        return OrganizationModuleResponse.model_validate(module)
    
    @staticmethod
    def update_module(
        db: Session,
        organization_id: UUID,
        module_id: str,
        module_data: OrganizationModuleUpdate
    ) -> OrganizationModuleResponse:
        """Update module configuration"""
        module = OrganizationModuleRepository.update(db, organization_id, module_id, module_data)
        return OrganizationModuleResponse.model_validate(module)
    
    @staticmethod
    def list_modules(db: Session, organization_id: UUID) -> list[OrganizationModuleResponse]:
        """List all modules for organization"""
        modules = OrganizationModuleRepository.list_by_organization(db, organization_id)
        return [OrganizationModuleResponse.model_validate(m) for m in modules]
    
    @staticmethod
    def get_available_modules() -> List[Dict[str, Any]]:
        """Get list of all available modules in the system"""
        # This would typically come from a configuration file or database
        return [
            {"id": "projects", "name": "Project Management", "description": "Manage projects, tasks, and teams"},
            {"id": "hr", "name": "HR Management", "description": "Employee management, attendance, leave"},
            {"id": "finance", "name": "Finance", "description": "Accounting, invoicing, expenses"},
            {"id": "crm", "name": "CRM", "description": "Customer relationship management"},
            {"id": "inventory", "name": "Inventory", "description": "Stock management and tracking"},
        ]


class BrandingService:
    """Service for organization branding operations"""
    
    @staticmethod
    def get_branding(db: Session, organization_id: UUID):
        """Get organization branding"""
        from app.schemas import OrganizationBranding
        branding = OrganizationBrandingRepository.get_by_organization_id(db, organization_id)
        if not branding:
            # Return None if not found (frontend will handle defaults)
            return None
        return branding
    
    @staticmethod
    def update_branding(db: Session, organization_id: UUID, branding_data: dict):
        """Update organization branding"""
        from app.schemas import OrganizationBranding
        # Ensure organization exists
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        # Set defaults for required fields if not provided
        if 'primary_color' not in branding_data or not branding_data['primary_color']:
            branding_data['primary_color'] = '#1976d2'
        if 'secondary_color' not in branding_data or not branding_data['secondary_color']:
            branding_data['secondary_color'] = '#dc004e'
        if 'accent_color' not in branding_data or not branding_data['accent_color']:
            branding_data['accent_color'] = '#00a86b'
        
        # Update or create branding
        branding = OrganizationBrandingRepository.create_or_update(db, organization_id, branding_data)
        return branding

