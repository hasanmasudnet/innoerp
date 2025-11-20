"""
Module management API routes
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from shared.database.base import get_db
from app.models import (
    OrganizationModuleCreate, OrganizationModuleUpdate, OrganizationModuleResponse,
    ModuleAssignmentRequest, BulkModuleAssignmentRequest, IndustryTemplateApplicationRequest
)
from typing import Dict
from app.services import ModuleService
from shared.common.errors import handle_exception

router = APIRouter(prefix="/modules", tags=["modules"])


@router.post("/organization/{organization_id}", response_model=OrganizationModuleResponse, status_code=status.HTTP_201_CREATED)
def enable_module(
    organization_id: UUID,
    module_data: OrganizationModuleCreate,
    db: Session = Depends(get_db)
):
    """Enable module for organization"""
    try:
        return ModuleService.enable_module(db, organization_id, module_data)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/organization/{organization_id}/{module_id}", response_model=OrganizationModuleResponse)
def update_module(
    organization_id: UUID,
    module_id: str,
    module_data: OrganizationModuleUpdate,
    db: Session = Depends(get_db)
):
    """Update module configuration"""
    try:
        return ModuleService.update_module(db, organization_id, module_id, module_data)
    except Exception as e:
        raise handle_exception(e)


@router.get("/organization/{organization_id}", response_model=List[OrganizationModuleResponse])
def list_modules(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """List all modules for organization"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Listing modules for organization {organization_id}")
        modules = ModuleService.list_modules(db, organization_id)
        logger.info(f"Found {len(modules)} modules for organization {organization_id}")
        return modules
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing modules for organization {organization_id}: {e}", exc_info=True)
        raise handle_exception(e)


@router.get("/available")
def get_available_modules(db: Session = Depends(get_db)):
    """Get list of all available modules in the system (from ModuleRegistry - no hardcoding)"""
    try:
        return ModuleService.get_available_modules(db)
    except Exception as e:
        raise handle_exception(e)


@router.post("/assign/{organization_id}", response_model=OrganizationModuleResponse, status_code=status.HTTP_201_CREATED)
def assign_module(
    organization_id: UUID,
    assignment: ModuleAssignmentRequest,
    db: Session = Depends(get_db)
):
    """Assign module to organization (super admin)"""
    try:
        from app.models import ModuleAssignmentRequest
        return ModuleService.assign_module(
            db, organization_id, assignment.module_id, assignment.config
        )
    except Exception as e:
        raise handle_exception(e)


@router.post("/unassign/{organization_id}/{module_id}", status_code=status.HTTP_200_OK)
def unassign_module(
    organization_id: UUID,
    module_id: str,
    db: Session = Depends(get_db)
):
    """Unassign module from organization (super admin)"""
    try:
        ModuleService.unassign_module(db, organization_id, module_id)
        return {"message": f"Module {module_id} unassigned from organization"}
    except Exception as e:
        raise handle_exception(e)


@router.post("/bulk-assign/{organization_id}", response_model=List[OrganizationModuleResponse], status_code=status.HTTP_201_CREATED)
def bulk_assign_modules(
    organization_id: UUID,
    assignment: BulkModuleAssignmentRequest,
    db: Session = Depends(get_db)
):
    """Bulk assign modules to organization (super admin)"""
    try:
        from app.models import BulkModuleAssignmentRequest
        return ModuleService.bulk_assign_modules(
            db, organization_id, assignment.module_ids, assignment.industry_code
        )
    except Exception as e:
        raise handle_exception(e)


@router.post("/apply-industry/{organization_id}", response_model=List[OrganizationModuleResponse], status_code=status.HTTP_201_CREATED)
def apply_industry_template(
    organization_id: UUID,
    request: IndustryTemplateApplicationRequest,
    db: Session = Depends(get_db)
):
    """Apply industry template to organization (super admin)"""
    try:
        from app.models import IndustryTemplateApplicationRequest
        return ModuleService.assign_from_industry(
            db, organization_id, request.industry_code
        )
    except Exception as e:
        raise handle_exception(e)


@router.get("/industry/{industry_code}", response_model=List[Dict])
def get_industry_modules(
    industry_code: str,
    db: Session = Depends(get_db)
):
    """Get modules for industry (cached)"""
    try:
        from app.services import IndustryTemplateService
        from typing import Dict
        modules = IndustryTemplateService.get_modules(db, industry_code)
        return [
            {
                "module_id": m.module_id,
                "is_required": m.is_required,
                "default_config": m.default_config,
                "display_order": m.display_order
            }
            for m in modules
        ]
    except Exception as e:
        raise handle_exception(e)

