"""
Module management API routes
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from shared.database.base import get_db
from app.models import (
    OrganizationModuleCreate, OrganizationModuleUpdate, OrganizationModuleResponse
)
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
        return ModuleService.list_modules(db, organization_id)
    except Exception as e:
        raise handle_exception(e)


@router.get("/available")
def get_available_modules():
    """Get list of all available modules in the system"""
    try:
        return ModuleService.get_available_modules()
    except Exception as e:
        raise handle_exception(e)

