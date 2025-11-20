"""
Business logic layer for tenant service
"""
from typing import Optional, Dict, Any, List
import logging
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from shared.common.errors import ResourceNotFoundError, TenantInactiveError, ValidationError
from app.repositories import (
    OrganizationRepository,
    SubscriptionPlanRepository,
    OrganizationSubscriptionRepository,
    OrganizationModuleRepository,
    OrganizationBrandingRepository,
    ModuleRegistryRepository,
    IndustryTemplateRepository,
    IndustryModuleTemplateRepository
)
from app.models import (
    OrganizationCreate, OrganizationUpdate,
    OrganizationResponse,
    OrganizationSubscriptionResponse,
    SubscriptionPlanCreate, SubscriptionPlanResponse,
    OrganizationModuleCreate, OrganizationModuleUpdate,
    OrganizationModuleResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    ModuleRegistryCreate, ModuleRegistryUpdate, ModuleRegistryResponse,
    IndustryTemplateCreate, IndustryTemplateUpdate, IndustryTemplateResponse,
    IndustryModuleTemplateCreate, IndustryModuleTemplateUpdate, IndustryModuleTemplateResponse,
    ModuleAssignmentRequest, BulkModuleAssignmentRequest, IndustryTemplateApplicationRequest
)
from app.kafka.producer import publish_tenant_event, publish_module_event
from shared.kafka.schemas import TenantCreatedEvent, TenantUpdatedEvent

logger = logging.getLogger(__name__)


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
        trial_days: int = 14,
        industry_code: Optional[str] = None
    ) -> OrganizationResponse:
        """Create new organization with trial period"""
        org = OrganizationRepository.create(db, org_data)
        
        # Set industry if provided
        if industry_code:
            template = IndustryTemplateRepository.get_by_code(db, industry_code)
            if template:
                org.industry_code = industry_code
                org.industry_name = template.industry_name
        
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
                "owner_email": org.owner_email,
                "industry_code": org.industry_code
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
        """List all modules for organization (cached)"""
        try:
            from app.cache_service import _cache_service
            
            # Try cache
            cached = _cache_service.get_org_modules(organization_id)
            if cached is not None:
                return [OrganizationModuleResponse.model_validate(m) for m in cached]
        except Exception as e:
            logger.warning(f"Cache lookup failed, falling back to DB: {e}")
        
        # Cache miss or error - query DB
        modules = OrganizationModuleRepository.list_by_organization(db, organization_id)
        result = []
        for m in modules:
            try:
                result.append(OrganizationModuleResponse.model_validate(m))
            except Exception as e:
                logger.error(f"Error validating module {m.module_id if hasattr(m, 'module_id') else 'unknown'}: {e}")
                # Try to create response manually as fallback
                try:
                    result.append(OrganizationModuleResponse(
                        id=str(m.id),
                        organization_id=str(m.organization_id),
                        module_id=m.module_id,
                        is_enabled=m.is_enabled,
                        config=m.config if hasattr(m, 'config') else {},
                        enabled_at=m.enabled_at if hasattr(m, 'enabled_at') else None,
                        created_at=m.created_at,
                        updated_at=m.updated_at
                    ))
                except Exception as e2:
                    logger.error(f"Failed to create response for module: {e2}")
                    continue
        
        # Try to cache result (ignore errors)
        try:
            from app.cache_service import _cache_service
            _cache_service.set_org_modules(organization_id, [m.model_dump() for m in result])
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
        
        return result
    
    @staticmethod
    def _get_module_metadata(m) -> dict:
        """Helper to safely get metadata value from SQLAlchemy model, avoiding MetaData() conflict"""
        metadata_value = {}
        try:
            from sqlalchemy import inspect as sql_inspect
            inst = sql_inspect(m)
            # Get the column value from instance state
            if 'metadata_' in inst.attrs:
                attr = inst.attrs['metadata_']
                if hasattr(attr, 'value'):
                    val = attr.value
                    if isinstance(val, dict):
                        metadata_value = val
        except:
            pass
        # Fallback: try __dict__
        if not metadata_value and hasattr(m, '__dict__'):
            if 'metadata_' in m.__dict__:
                val = m.__dict__['metadata_']
                if isinstance(val, dict):
                    metadata_value = val
        return metadata_value if metadata_value else {}
    
    @staticmethod
    def get_available_modules(db: Session) -> List[Dict[str, Any]]:
        """Get list of all available modules in the system - from ModuleRegistry (NO HARDCODING)"""
        modules = ModuleRegistryService.list_all(db, active_only=True)
        return [
            {
                "id": m.module_id,
                "name": m.module_name,
                "description": m.description or "",
                "category": m.category,
                "service_name": m.service_name,
                "api_endpoint": m.api_endpoint,
                "version": m.version,
                "metadata": ModuleService._get_module_metadata(m)
            }
            for m in modules
        ]
    
    @staticmethod
    def assign_module(
        db: Session,
        organization_id: UUID,
        module_id: str,
        config: Dict[str, Any] = None,
        user_id: Optional[UUID] = None
    ) -> OrganizationModuleResponse:
        """Assign module to organization via Kafka (validates module exists in registry)"""
        # Validate module exists in registry
        module_registry = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module_registry:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        if not module_registry.is_active:
            raise ValidationError(f"Module {module_id} is not active")
        
        # Create module assignment
        module_data = OrganizationModuleCreate(
            module_id=module_id,
            is_enabled=True,
            config=config or {}
        )
        module = OrganizationModuleRepository.create_or_update(db, organization_id, module_data)
        
        # Publish Kafka event
        publish_module_event(
            "module.assigned",
            {
                "module_id": module_id,
                "organization_id": str(organization_id),
                "config": config or {},
                "assigned_by": str(user_id) if user_id else None
            },
            organization_id=organization_id,
            user_id=user_id
        )
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_org_modules(organization_id)
        
        return OrganizationModuleResponse.model_validate(module)
    
    @staticmethod
    def unassign_module(
        db: Session,
        organization_id: UUID,
        module_id: str,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Unassign module from organization via Kafka"""
        module = OrganizationModuleRepository.get_by_org_and_module(db, organization_id, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not assigned to organization {organization_id}")
        
        # Delete module assignment
        db.delete(module)
        db.commit()
        
        # Publish Kafka event
        publish_module_event(
            "module.unassigned",
            {
                "module_id": module_id,
                "organization_id": str(organization_id),
                "unassigned_by": str(user_id) if user_id else None
            },
            organization_id=organization_id,
            user_id=user_id
        )
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_org_modules(organization_id)
        
        return True
    
    @staticmethod
    def bulk_assign_modules(
        db: Session,
        organization_id: UUID,
        module_ids: List[str],
        industry_code: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> List[OrganizationModuleResponse]:
        """Bulk assign modules via Kafka (validates all modules exist)"""
        # Validate all modules exist in registry
        valid_ids, invalid_ids = ModuleRegistryRepository.validate_modules_exist(db, module_ids)
        if invalid_ids:
            raise ValidationError(f"Invalid modules: {invalid_ids}")
        
        # Get industry template configs if provided
        default_configs = {}
        if industry_code:
            template = IndustryTemplateRepository.get_by_code(db, industry_code)
            if template:
                module_templates = IndustryModuleTemplateRepository.get_modules_for_industry(db, industry_code)
                default_configs = {mt.module_id: mt.default_config for mt in module_templates}
        
        # Assign each module
        assigned_modules = []
        for module_id in valid_ids:
            config = default_configs.get(module_id, {})
            module_data = OrganizationModuleCreate(
                module_id=module_id,
                is_enabled=True,
                config=config
            )
            module = OrganizationModuleRepository.create_or_update(db, organization_id, module_data)
            assigned_modules.append(OrganizationModuleResponse.model_validate(module))
        
        # Publish bulk assignment event
        publish_module_event(
            "module.bulk_assigned",
            {
                "module_ids": valid_ids,
                "organization_id": str(organization_id),
                "industry_code": industry_code,
                "assigned_by": str(user_id) if user_id else None
            },
            organization_id=organization_id,
            user_id=user_id
        )
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_org_modules(organization_id)
        
        return assigned_modules
    
    @staticmethod
    def assign_from_industry(
        db: Session,
        organization_id: UUID,
        industry_code: str,
        user_id: Optional[UUID] = None
    ) -> List[OrganizationModuleResponse]:
        """Auto-assign modules from industry template (validates modules in registry)"""
        # Use IndustryTemplateService to apply template
        return IndustryTemplateService.apply_to_organization(db, organization_id, industry_code, user_id)


class ModuleRegistryService:
    """Service for managing system-wide module registry"""
    
    @staticmethod
    def register_module(db: Session, module_data: ModuleRegistryCreate, user_id: Optional[UUID] = None) -> ModuleRegistryResponse:
        """Register new module in system (super admin)"""
        # Check if module already exists
        existing = ModuleRegistryRepository.get_by_id(db, module_data.module_id)
        if existing:
            raise ValidationError(f"Module {module_data.module_id} already exists in registry")
        
        module = ModuleRegistryRepository.create(db, module_data.dict())
        
        # Publish event
        publish_module_event(
            "module.registered",
            {
                "module_id": module.module_id,
                "module_name": module.module_name,
                "service_name": module.service_name,
                "registered_by": str(user_id) if user_id else None
            },
            organization_id=UUID('00000000-0000-0000-0000-000000000000'),  # System event
            user_id=user_id
        )
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_module_registry()
        
        return ModuleRegistryResponse.model_validate(module)
    
    @staticmethod
    def list_all(db: Session, active_only: bool = True) -> List[ModuleRegistryResponse]:
        """Get all registered modules (cached)"""
        try:
            from app.cache_service import _cache_service
            
            # Try cache first
            if active_only:
                cache_key = "modules:registry:active"
            else:
                cache_key = "modules:registry:all"
            
            cached = _cache_service.redis.get(cache_key)
            if cached is not None:
                return [ModuleRegistryResponse.model_validate(m) for m in cached]
        except Exception as e:
            logger.warning(f"Cache lookup failed, falling back to DB: {e}")
        
        # Cache miss or error - query DB
        modules = ModuleRegistryRepository.list_all(db, active_only=active_only)
        result = []
        for m in modules:
            try:
                # Get metadata value - use SQLAlchemy instance state to get actual column value
                # This avoids the MetaData() object conflict
                metadata_value = {}
                from sqlalchemy import inspect as sql_inspect
                inst = sql_inspect(m)
                # Get the column value from instance state
                if 'metadata_' in inst.attrs:
                    attr = inst.attrs['metadata_']
                    if hasattr(attr, 'value'):
                        val = attr.value
                        if isinstance(val, dict):
                            metadata_value = val
                # Fallback: try __dict__
                if not metadata_value and hasattr(m, '__dict__'):
                    if 'metadata_' in m.__dict__:
                        val = m.__dict__['metadata_']
                        if isinstance(val, dict):
                            metadata_value = val
                
                # Create a dict with the correct field names for Pydantic
                # Pydantic expects 'metadata' but SQLAlchemy has 'metadata_'
                # Get all attributes and map metadata_ to metadata
                module_dict = {
                    'module_id': m.module_id,
                    'module_name': m.module_name,
                    'description': getattr(m, 'description', None),
                    'category': getattr(m, 'category', None),
                    'is_active': m.is_active,
                    'service_name': getattr(m, 'service_name', None),
                    'api_endpoint': getattr(m, 'api_endpoint', None),
                    'version': getattr(m, 'version', None),
                    'metadata': metadata_value,  # Use 'metadata' for Pydantic (mapped from metadata_)
                    'created_at': m.created_at,
                    'updated_at': m.updated_at
                }
                
                # Convert dict to Pydantic response
                result.append(ModuleRegistryResponse.model_validate(module_dict))
            except Exception as e:
                logger.error(f"Error validating module {m.module_id if hasattr(m, 'module_id') else 'unknown'}: {e}")
                # Try to create response manually as fallback
                try:
                    # Get metadata value - access the column directly by name
                    # SQLAlchemy stores column values in __dict__ or we can use getattr with the mapped column
                    metadata_value = {}
                    if hasattr(m, '__table__'):
                        # Access the column value directly from the instance dict
                        # The column is stored with the Python attribute name (metadata_)
                        if 'metadata_' in m.__dict__:
                            metadata_val = m.__dict__['metadata_']
                            metadata_value = metadata_val if isinstance(metadata_val, dict) else {}
                        # Fallback: try to get from column directly
                        elif hasattr(m.__table__.columns, 'metadata'):
                            col = m.__table__.columns['metadata']
                            # Get value using column key
                            metadata_value = getattr(m, col.key, {}) if isinstance(getattr(m, col.key, {}), dict) else {}
                    # Final fallback
                    if not metadata_value:
                        metadata_value = {}
                    
                    result.append(ModuleRegistryResponse(
                        module_id=m.module_id,
                        module_name=m.module_name,
                        description=m.description,
                        category=m.category,
                        is_active=m.is_active,
                        service_name=m.service_name,
                        api_endpoint=m.api_endpoint,
                        version=m.version,
                        metadata=metadata_value,
                        created_at=m.created_at,
                        updated_at=m.updated_at
                    ))
                except Exception as e2:
                    logger.error(f"Failed to create response for module: {e2}")
                    continue
        
        # Try to cache result (ignore errors)
        try:
            from app.cache_service import _cache_service
            _cache_service.redis.set(cache_key, [m.model_dump() for m in result], ttl=600)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
        
        return result
    
    @staticmethod
    def get_by_id(db: Session, module_id: str) -> ModuleRegistryResponse:
        """Get module details"""
        module = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        return ModuleRegistryResponse.model_validate(module)
    
    @staticmethod
    def update_module(db: Session, module_id: str, module_data: ModuleRegistryUpdate, user_id: Optional[UUID] = None) -> ModuleRegistryResponse:
        """Update module metadata (super admin)"""
        module = ModuleRegistryRepository.update(db, module_id, module_data.dict(exclude_unset=True))
        
        # Publish event
        publish_module_event(
            "module.updated",
            {
                "module_id": module.module_id,
                "updates": module_data.dict(exclude_unset=True),
                "updated_by": str(user_id) if user_id else None
            },
            organization_id=UUID('00000000-0000-0000-0000-000000000000'),  # System event
            user_id=user_id
        )
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_module_registry()
        
        return ModuleRegistryResponse.model_validate(module)
    
    @staticmethod
    def delete_module(db: Session, module_id: str) -> bool:
        """Soft delete module (super admin)"""
        ModuleRegistryRepository.delete(db, module_id)
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_module_registry()
        
        return True
    
    @staticmethod
    def activate_module(db: Session, module_id: str) -> ModuleRegistryResponse:
        """Activate module system-wide"""
        module = ModuleRegistryRepository.activate(db, module_id)
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_module_registry()
        
        return ModuleRegistryResponse.model_validate(module)
    
    @staticmethod
    def deactivate_module(db: Session, module_id: str) -> ModuleRegistryResponse:
        """Deactivate module system-wide"""
        module = ModuleRegistryRepository.deactivate(db, module_id)
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_module_registry()
        
        return ModuleRegistryResponse.model_validate(module)
    
    @staticmethod
    def validate_modules_exist(db: Session, module_ids: List[str]) -> tuple[List[str], List[str]]:
        """Validate modules exist in registry. Returns (valid_modules, invalid_modules)"""
        return ModuleRegistryRepository.validate_modules_exist(db, module_ids)


class IndustryTemplateService:
    """Service for industry template operations"""
    
    @staticmethod
    def list_all(db: Session, active_only: bool = True) -> List[IndustryTemplateResponse]:
        """Get all industry templates (cached)"""
        try:
            from app.cache_service import _cache_service
            
            cache_key = "industries:all" if not active_only else "industries:all:active"
            cached = _cache_service.redis.get(cache_key)
            if cached is not None:
                return [IndustryTemplateResponse.model_validate(t) for t in cached]
        except Exception as e:
            logger.warning(f"Cache lookup failed, falling back to DB: {e}")
        
        templates = IndustryTemplateRepository.list_all(db, active_only=active_only)
        result = []
        for t in templates:
            try:
                # Convert SQLAlchemy model to Pydantic response
                result.append(IndustryTemplateResponse.model_validate(t))
            except Exception as e:
                logger.error(f"Error validating industry template {t.industry_code if hasattr(t, 'industry_code') else 'unknown'}: {e}")
                # Try to create response manually as fallback
                try:
                    result.append(IndustryTemplateResponse(
                        industry_code=t.industry_code,
                        industry_name=t.industry_name,
                        description=t.description,
                        is_active=t.is_active,
                        created_at=t.created_at,
                        updated_at=t.updated_at
                    ))
                except Exception as e2:
                    logger.error(f"Failed to create response for industry template: {e2}")
                    continue
        
        # Try to cache result (ignore errors)
        try:
            from app.cache_service import _cache_service
            cache_key = "industries:all" if not active_only else "industries:all:active"
            _cache_service.redis.set(cache_key, [t.model_dump() for t in result], ttl=3600)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
        
        return result
    
    @staticmethod
    def get_by_code(db: Session, industry_code: str) -> IndustryTemplateResponse:
        """Get industry template by code (cached)"""
        from app.cache_service import _cache_service
        
        cached = _cache_service.get_industry_template(industry_code)
        if cached:
            return IndustryTemplateResponse.model_validate(cached)
        
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        result = IndustryTemplateResponse.model_validate(template)
        _cache_service.set_industry_template(industry_code, result.model_dump())
        
        return result
    
    @staticmethod
    def get_modules(db: Session, industry_code: str) -> List[IndustryModuleTemplateResponse]:
        """Get modules for industry (cached, validates modules exist in registry)"""
        from app.cache_service import _cache_service
        
        # Try cache
        cached = _cache_service.get_industry_modules(industry_code)
        if cached is not None:
            return [IndustryModuleTemplateResponse.model_validate(m) for m in cached]
        
        # Validate industry exists
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        # Get modules
        module_templates = IndustryModuleTemplateRepository.get_modules_for_industry(db, industry_code)
        
        # Validate all modules exist in registry
        module_ids = [mt.module_id for mt in module_templates]
        valid_ids, invalid_ids = ModuleRegistryRepository.validate_modules_exist(db, module_ids)
        
        if invalid_ids:
            logger.warning(f"Industry {industry_code} has invalid modules: {invalid_ids}")
            # Filter out invalid modules
            module_templates = [mt for mt in module_templates if mt.module_id in valid_ids]
        
        result = []
        for mt in module_templates:
            try:
                result.append(IndustryModuleTemplateResponse.model_validate(mt))
            except Exception as e:
                logger.error(f"Error validating industry module template {mt.module_id}: {e}")
                # Try to create response manually as fallback
                try:
                    result.append(IndustryModuleTemplateResponse(
                        id=mt.id,
                        template_id=mt.template_id,
                        module_id=mt.module_id,
                        is_required=mt.is_required,
                        default_config=mt.default_config if hasattr(mt, 'default_config') else {},
                        display_order=mt.display_order if hasattr(mt, 'display_order') else 0,
                        created_at=mt.created_at,
                        updated_at=mt.updated_at
                    ))
                except Exception as e2:
                    logger.error(f"Failed to create response for module {mt.module_id}: {e2}")
                    continue
        
        # Cache result
        try:
            _cache_service.set_industry_modules(industry_code, [m.model_dump() for m in result])
        except Exception as e:
            logger.warning(f"Failed to cache industry modules: {e}")
        
        return result
    
    @staticmethod
    def create_template(db: Session, template_data: IndustryTemplateCreate) -> IndustryTemplateResponse:
        """Create new industry template (super admin)"""
        # Check if code already exists
        existing = IndustryTemplateRepository.get_by_code(db, template_data.industry_code)
        if existing:
            raise ValidationError(f"Industry template {template_data.industry_code} already exists")
        
        template = IndustryTemplateRepository.create(db, template_data.dict())
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_all_industries()
        
        return IndustryTemplateResponse.model_validate(template)
    
    @staticmethod
    def update_template(db: Session, industry_code: str, template_data: IndustryTemplateUpdate) -> IndustryTemplateResponse:
        """Update industry template"""
        template = IndustryTemplateRepository.update(db, industry_code, template_data.dict(exclude_unset=True))
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_industry_template(industry_code)
        _cache_service.invalidate_all_industries()
        
        return IndustryTemplateResponse.model_validate(template)
    
    @staticmethod
    def delete_template(db: Session, industry_code: str) -> bool:
        """Soft delete industry template"""
        IndustryTemplateRepository.delete(db, industry_code)
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_industry_template(industry_code)
        _cache_service.invalidate_all_industries()
        
        return True
    
    @staticmethod
    def apply_to_organization(db: Session, organization_id: UUID, industry_code: str, user_id: Optional[UUID] = None) -> List[OrganizationModuleResponse]:
        """Apply industry template to organization (via Kafka)"""
        # Validate industry exists
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        # Get modules for industry
        module_templates = IndustryModuleTemplateRepository.get_modules_for_industry(db, industry_code)
        
        if not module_templates:
            raise ValidationError(f"Industry template {industry_code} has no modules assigned")
        
        # Validate all modules exist in registry
        module_ids = [mt.module_id for mt in module_templates]
        valid_ids, invalid_ids = ModuleRegistryRepository.validate_modules_exist(db, module_ids)
        
        if invalid_ids:
            raise ValidationError(f"Industry template contains invalid modules: {invalid_ids}")
        
        # Update organization industry info
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        org.industry_code = industry_code
        org.industry_name = template.industry_name
        db.commit()
        
        # Assign modules via Kafka (bulk assignment)
        assigned_modules = ModuleService.bulk_assign_modules(
            db, organization_id, valid_ids, industry_code, user_id
        )
        
        return assigned_modules
    
    @staticmethod
    def add_module_to_industry(
        db: Session,
        industry_code: str,
        module_id: str,
        is_required: bool = False,
        default_config: dict = None,
        display_order: int = 0
    ) -> IndustryModuleTemplateResponse:
        """Add module to industry template"""
        # Validate industry exists
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        # Validate module exists in registry
        module = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        
        # Check if module already assigned
        existing = IndustryModuleTemplateRepository.get_modules_for_industry(db, industry_code)
        if any(mt.module_id == module_id for mt in existing):
            raise ValidationError(f"Module {module_id} is already assigned to industry {industry_code}")
        
        # Add module
        module_template = IndustryModuleTemplateRepository.add_module_to_industry(
            db, template.id, module_id, is_required, default_config or {}, display_order
        )
        
        # Invalidate cache
        try:
            from app.cache_service import _cache_service
            _cache_service.invalidate_industry_template(industry_code)
            _cache_service.invalidate_industry_modules(industry_code)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
        
        try:
            return IndustryModuleTemplateResponse.model_validate(module_template)
        except Exception as e:
            logger.error(f"Error validating module template response: {e}")
            # Create response manually as fallback
            return IndustryModuleTemplateResponse(
                id=module_template.id,
                template_id=module_template.template_id,
                module_id=module_template.module_id,
                is_required=module_template.is_required,
                default_config=module_template.default_config if hasattr(module_template, 'default_config') else {},
                display_order=module_template.display_order if hasattr(module_template, 'display_order') else 0,
                created_at=module_template.created_at,
                updated_at=module_template.updated_at
            )
    
    @staticmethod
    def remove_module_from_industry(db: Session, industry_code: str, module_id: str) -> bool:
        """Remove module from industry template"""
        # Validate industry exists
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        # Remove module
        removed = IndustryModuleTemplateRepository.remove_module_from_industry(db, template.id, module_id)
        if not removed:
            raise ResourceNotFoundError(f"Module {module_id} not found in industry {industry_code}")
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_industry_template(industry_code)
        _cache_service.invalidate_industry_modules(industry_code)
        
        return True
    
    @staticmethod
    def update_module_in_industry(
        db: Session,
        industry_code: str,
        module_id: str,
        module_data: IndustryModuleTemplateUpdate
    ) -> IndustryModuleTemplateResponse:
        """Update module settings in industry template"""
        # Validate industry exists
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        # Update module
        module_template = IndustryModuleTemplateRepository.update_module_in_industry(
            db, template.id, module_id,
            is_required=module_data.is_required if hasattr(module_data, 'is_required') else None,
            default_config=module_data.default_config if hasattr(module_data, 'default_config') else None,
            display_order=module_data.display_order if hasattr(module_data, 'display_order') else None
        )
        
        # Invalidate cache
        from app.cache_service import _cache_service
        _cache_service.invalidate_industry_template(industry_code)
        _cache_service.invalidate_industry_modules(industry_code)
        
        return IndustryModuleTemplateResponse.model_validate(module_template)


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

