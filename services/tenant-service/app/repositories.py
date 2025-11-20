"""
Repository layer for tenant service
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from shared.common.errors import ResourceNotFoundError, ValidationError
from app.schemas import (
    Organization, SubscriptionPlan, OrganizationSubscription, OrganizationModule, OrganizationBranding,
    ModuleRegistry, IndustryTemplate, IndustryModuleTemplate
)
from app.models import (
    OrganizationCreate, OrganizationUpdate,
    SubscriptionPlanCreate,
    OrganizationModuleCreate, OrganizationModuleUpdate
)


class OrganizationRepository:
    """Repository for organization operations"""
    
    @staticmethod
    def get_by_id(db: Session, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        return db.query(Organization).filter(Organization.id == organization_id).first()
    
    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        return db.query(Organization).filter(Organization.slug == slug).first()
    
    @staticmethod
    def get_by_subdomain(db: Session, subdomain: str) -> Optional[Organization]:
        """Get organization by subdomain"""
        return db.query(Organization).filter(Organization.subdomain == subdomain).first()
    
    @staticmethod
    def get_by_stripe_customer_id(db: Session, customer_id: str) -> Optional[Organization]:
        """Get organization by Stripe customer ID"""
        return db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
    
    @staticmethod
    def check_subdomain_available(db: Session, subdomain: str) -> bool:
        """Check if subdomain is available"""
        if not subdomain:
            return False
        existing = db.query(Organization).filter(Organization.subdomain == subdomain).first()
        return existing is None
    
    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
        """List all organizations (for super admin)"""
        return db.query(Organization).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_all(db: Session) -> int:
        """Count total organizations"""
        return db.query(Organization).count()
    
    @staticmethod
    def create(db: Session, org_data: OrganizationCreate) -> Organization:
        """Create new organization"""
        # Check if slug already exists
        if OrganizationRepository.get_by_slug(db, org_data.slug):
            raise ValidationError(f"Organization with slug '{org_data.slug}' already exists")
        
        # Check if subdomain already exists
        if org_data.subdomain and OrganizationRepository.get_by_subdomain(db, org_data.subdomain):
            raise ValidationError(f"Organization with subdomain '{org_data.subdomain}' already exists")
        
        org = Organization(**org_data.dict())
        db.add(org)
        db.commit()
        db.refresh(org)
        return org
    
    @staticmethod
    def update(db: Session, organization_id: UUID, org_data: OrganizationUpdate) -> Organization:
        """Update organization"""
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        update_data = org_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(org, key, value)
        
        db.commit()
        db.refresh(org)
        return org
    
    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
        """List all organizations"""
        return db.query(Organization).offset(skip).limit(limit).all()
    
    @staticmethod
    def set_stripe_customer_id(db: Session, organization_id: UUID, customer_id: str) -> Organization:
        """Set Stripe customer ID for organization"""
        org = OrganizationRepository.get_by_id(db, organization_id)
        if not org:
            raise ResourceNotFoundError(f"Organization {organization_id} not found")
        
        org.stripe_customer_id = customer_id
        db.commit()
        db.refresh(org)
        return org


class SubscriptionPlanRepository:
    """Repository for subscription plan operations"""
    
    @staticmethod
    def get_by_id(db: Session, plan_id: UUID) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID"""
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by name"""
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.name == name).first()
    
    @staticmethod
    def create(db: Session, plan_data: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Create new subscription plan"""
        plan = SubscriptionPlan(**plan_data.dict())
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    
    @staticmethod
    def update(db: Session, plan_id: UUID, plan_data: dict) -> SubscriptionPlan:
        """Update subscription plan"""
        plan = SubscriptionPlanRepository.get_by_id(db, plan_id)
        if not plan:
            raise ResourceNotFoundError(f"Subscription plan {plan_id} not found")
        
        update_data = {k: v for k, v in plan_data.items() if v is not None}
        for key, value in update_data.items():
            setattr(plan, key, value)
        
        db.commit()
        db.refresh(plan)
        return plan
    
    @staticmethod
    def list_all(db: Session, active_only: bool = True) -> List[SubscriptionPlan]:
        """List all subscription plans"""
        query = db.query(SubscriptionPlan)
        if active_only:
            query = query.filter(SubscriptionPlan.is_active == True)
        return query.all()


class OrganizationSubscriptionRepository:
    """Repository for organization subscription operations"""
    
    @staticmethod
    def get_by_organization_id(db: Session, organization_id: UUID) -> Optional[OrganizationSubscription]:
        """Get subscription by organization ID"""
        return db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id
        ).first()
    
    @staticmethod
    def create_or_update(
        db: Session,
        organization_id: UUID,
        plan_id: UUID,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool = False
    ) -> OrganizationSubscription:
        """Create or update organization subscription"""
        subscription = OrganizationSubscriptionRepository.get_by_organization_id(db, organization_id)
        
        if subscription:
            subscription.plan_id = plan_id
            subscription.status = status
            subscription.current_period_start = current_period_start
            subscription.current_period_end = current_period_end
            subscription.cancel_at_period_end = cancel_at_period_end
        else:
            subscription = OrganizationSubscription(
                organization_id=organization_id,
                plan_id=plan_id,
                status=status,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end
            )
            db.add(subscription)
        
        db.commit()
        db.refresh(subscription)
        return subscription


class OrganizationModuleRepository:
    """Repository for organization module operations"""
    
    @staticmethod
    def get_by_org_and_module(
        db: Session,
        organization_id: UUID,
        module_id: str
    ) -> Optional[OrganizationModule]:
        """Get module configuration for organization"""
        return db.query(OrganizationModule).filter(
            and_(
                OrganizationModule.organization_id == organization_id,
                OrganizationModule.module_id == module_id
            )
        ).first()
    
    @staticmethod
    def list_by_organization(db: Session, organization_id: UUID) -> List[OrganizationModule]:
        """List all modules for organization"""
        return db.query(OrganizationModule).filter(
            OrganizationModule.organization_id == organization_id
        ).all()
    
    @staticmethod
    def create_or_update(
        db: Session,
        organization_id: UUID,
        module_data: OrganizationModuleCreate
    ) -> OrganizationModule:
        """Create or update organization module"""
        module = OrganizationModuleRepository.get_by_org_and_module(
            db, organization_id, module_data.module_id
        )
        
        if module:
            module.is_enabled = module_data.is_enabled
            module.config = module_data.config
        else:
            module = OrganizationModule(
                organization_id=organization_id,
                **module_data.dict()
            )
            if module_data.is_enabled:
                from datetime import datetime
                module.enabled_at = datetime.utcnow()
            db.add(module)
        
        db.commit()
        db.refresh(module)
        return module
    
    @staticmethod
    def update(
        db: Session,
        organization_id: UUID,
        module_id: str,
        module_data: OrganizationModuleUpdate
    ) -> OrganizationModule:
        """Update organization module"""
        module = OrganizationModuleRepository.get_by_org_and_module(db, organization_id, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found for organization {organization_id}")
        
        update_data = module_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(module, key, value)
        
        # Set enabled_at if enabling for first time
        if 'is_enabled' in update_data and update_data['is_enabled'] and not module.enabled_at:
            from datetime import datetime
            module.enabled_at = datetime.utcnow()
        
        db.commit()
        db.refresh(module)
        return module


class OrganizationBrandingRepository:
    """Repository for organization branding operations"""
    
    @staticmethod
    def get_by_organization_id(db: Session, organization_id: UUID) -> Optional[OrganizationBranding]:
        """Get branding by organization ID"""
        return db.query(OrganizationBranding).filter(
            OrganizationBranding.organization_id == organization_id
        ).first()
    
    @staticmethod
    def create_or_update(
        db: Session,
        organization_id: UUID,
        branding_data: dict
    ) -> OrganizationBranding:
        """Create or update organization branding"""
        branding = OrganizationBrandingRepository.get_by_organization_id(db, organization_id)
        
        if branding:
            # Update existing branding
            update_data = {k: v for k, v in branding_data.items() if v is not None}
            for key, value in update_data.items():
                setattr(branding, key, value)
            branding.updated_at = datetime.utcnow()
        else:
            # Create new branding
            branding = OrganizationBranding(
                organization_id=organization_id,
                **{k: v for k, v in branding_data.items() if v is not None}
            )
            db.add(branding)
        
        db.commit()
        db.refresh(branding)
        return branding


class ModuleRegistryRepository:
    """Repository for module registry operations"""
    
    @staticmethod
    def get_by_id(db: Session, module_id: str) -> Optional[ModuleRegistry]:
        """Get module by ID"""
        return db.query(ModuleRegistry).filter(ModuleRegistry.module_id == module_id).first()
    
    @staticmethod
    def list_all(db: Session, active_only: bool = False) -> List[ModuleRegistry]:
        """List all modules in registry"""
        query = db.query(ModuleRegistry)
        if active_only:
            query = query.filter(ModuleRegistry.is_active == True)
        return query.order_by(ModuleRegistry.module_name).all()
    
    @staticmethod
    def create(db: Session, module_data: dict) -> ModuleRegistry:
        """Create new module in registry"""
        module = ModuleRegistry(**module_data)
        db.add(module)
        db.commit()
        db.refresh(module)
        return module
    
    @staticmethod
    def update(db: Session, module_id: str, module_data: dict) -> ModuleRegistry:
        """Update module in registry"""
        module = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        
        update_data = {k: v for k, v in module_data.items() if v is not None}
        for key, value in update_data.items():
            setattr(module, key, value)
        
        db.commit()
        db.refresh(module)
        return module
    
    @staticmethod
    def delete(db: Session, module_id: str) -> bool:
        """Soft delete module (set is_active=False)"""
        module = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        
        module.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def activate(db: Session, module_id: str) -> ModuleRegistry:
        """Activate module"""
        module = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        
        module.is_active = True
        db.commit()
        db.refresh(module)
        return module
    
    @staticmethod
    def deactivate(db: Session, module_id: str) -> ModuleRegistry:
        """Deactivate module"""
        module = ModuleRegistryRepository.get_by_id(db, module_id)
        if not module:
            raise ResourceNotFoundError(f"Module {module_id} not found in registry")
        
        module.is_active = False
        db.commit()
        db.refresh(module)
        return module
    
    @staticmethod
    def validate_modules_exist(db: Session, module_ids: List[str]) -> tuple[List[str], List[str]]:
        """Validate modules exist in registry. Returns (valid_modules, invalid_modules)"""
        modules = db.query(ModuleRegistry).filter(
            and_(
                ModuleRegistry.module_id.in_(module_ids),
                ModuleRegistry.is_active == True
            )
        ).all()
        
        valid_ids = {m.module_id for m in modules}
        invalid_ids = [mid for mid in module_ids if mid not in valid_ids]
        
        return (list(valid_ids), invalid_ids)


class IndustryTemplateRepository:
    """Repository for industry template operations"""
    
    @staticmethod
    def get_by_code(db: Session, industry_code: str) -> Optional[IndustryTemplate]:
        """Get industry template by code"""
        return db.query(IndustryTemplate).filter(IndustryTemplate.industry_code == industry_code).first()
    
    @staticmethod
    def list_all(db: Session, active_only: bool = False) -> List[IndustryTemplate]:
        """List all industry templates"""
        query = db.query(IndustryTemplate)
        if active_only:
            query = query.filter(IndustryTemplate.is_active == True)
        return query.order_by(IndustryTemplate.industry_name).all()
    
    @staticmethod
    def create(db: Session, template_data: dict) -> IndustryTemplate:
        """Create new industry template"""
        template = IndustryTemplate(**template_data)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def update(db: Session, industry_code: str, template_data: dict) -> IndustryTemplate:
        """Update industry template"""
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        update_data = {k: v for k, v in template_data.items() if v is not None}
        for key, value in update_data.items():
            setattr(template, key, value)
        
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def delete(db: Session, industry_code: str) -> bool:
        """Soft delete industry template"""
        template = IndustryTemplateRepository.get_by_code(db, industry_code)
        if not template:
            raise ResourceNotFoundError(f"Industry template {industry_code} not found")
        
        template.is_active = False
        db.commit()
        return True


class IndustryModuleTemplateRepository:
    """Repository for industry module template operations"""
    
    @staticmethod
    def get_modules_for_industry(db: Session, industry_code: str) -> List[IndustryModuleTemplate]:
        """Get all modules for an industry template"""
        return db.query(IndustryModuleTemplate).join(
            IndustryTemplate
        ).filter(
            IndustryTemplate.industry_code == industry_code
        ).order_by(IndustryModuleTemplate.display_order).all()
    
    @staticmethod
    def add_module_to_industry(
        db: Session,
        template_id: UUID,
        module_id: str,
        is_required: bool = False,
        default_config: dict = None,
        display_order: int = 0
    ) -> IndustryModuleTemplate:
        """Add module to industry template"""
        template = IndustryModuleTemplate(
            template_id=template_id,
            module_id=module_id,
            is_required=is_required,
            default_config=default_config or {},
            display_order=display_order
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def remove_module_from_industry(db: Session, template_id: UUID, module_id: str) -> bool:
        """Remove module from industry template"""
        template = db.query(IndustryModuleTemplate).filter(
            and_(
                IndustryModuleTemplate.template_id == template_id,
                IndustryModuleTemplate.module_id == module_id
            )
        ).first()
        
        if template:
            db.delete(template)
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_module_in_industry(
        db: Session,
        template_id: UUID,
        module_id: str,
        is_required: bool = None,
        default_config: dict = None,
        display_order: int = None
    ) -> IndustryModuleTemplate:
        """Update module in industry template"""
        template = db.query(IndustryModuleTemplate).filter(
            and_(
                IndustryModuleTemplate.template_id == template_id,
                IndustryModuleTemplate.module_id == module_id
            )
        ).first()
        
        if not template:
            raise ResourceNotFoundError(f"Module {module_id} not found in template {template_id}")
        
        if is_required is not None:
            template.is_required = is_required
        if default_config is not None:
            template.default_config = default_config
        if display_order is not None:
            template.display_order = display_order
        
        db.commit()
        db.refresh(template)
        return template

