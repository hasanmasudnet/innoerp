"""
Module registry management API routes (super admin only)
"""
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from shared.database.base import get_db
from app.models import (
    ModuleRegistryCreate, ModuleRegistryUpdate, ModuleRegistryResponse
)
from app.services import ModuleRegistryService
from shared.common.errors import handle_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/module-registry", tags=["module-registry"])


@router.get("", response_model=List[ModuleRegistryResponse])
def list_modules(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all registered modules (super admin)"""
    try:
        modules = ModuleRegistryService.list_all(db, active_only=active_only)
        return modules
    except Exception as e:
        logger.error(f"Error listing modules: {e}", exc_info=True)
        raise handle_exception(e)


@router.get("/{module_id}", response_model=ModuleRegistryResponse)
def get_module(
    module_id: str,
    db: Session = Depends(get_db)
):
    """Get module details (super admin)"""
    try:
        return ModuleRegistryService.get_by_id(db, module_id)
    except Exception as e:
        raise handle_exception(e)


@router.post("", response_model=ModuleRegistryResponse, status_code=status.HTTP_201_CREATED)
def register_module(
    module_data: ModuleRegistryCreate,
    db: Session = Depends(get_db)
):
    """Register new module in system (super admin)"""
    try:
        return ModuleRegistryService.register_module(db, module_data)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{module_id}", response_model=ModuleRegistryResponse)
def update_module(
    module_id: str,
    module_data: ModuleRegistryUpdate,
    db: Session = Depends(get_db)
):
    """Update module metadata (super admin)"""
    try:
        return ModuleRegistryService.update_module(db, module_id, module_data)
    except Exception as e:
        raise handle_exception(e)


@router.delete("/{module_id}", status_code=status.HTTP_200_OK)
def delete_module(
    module_id: str,
    db: Session = Depends(get_db)
):
    """Delete module from registry (super admin)"""
    try:
        ModuleRegistryService.delete_module(db, module_id)
        return {"message": f"Module {module_id} deleted"}
    except Exception as e:
        raise handle_exception(e)


@router.post("/{module_id}/activate", response_model=ModuleRegistryResponse)
def activate_module(
    module_id: str,
    db: Session = Depends(get_db)
):
    """Activate module system-wide (super admin)"""
    try:
        return ModuleRegistryService.activate_module(db, module_id)
    except Exception as e:
        raise handle_exception(e)


@router.post("/{module_id}/deactivate", response_model=ModuleRegistryResponse)
def deactivate_module(
    module_id: str,
    db: Session = Depends(get_db)
):
    """Deactivate module system-wide (super admin)"""
    try:
        return ModuleRegistryService.deactivate_module(db, module_id)
    except Exception as e:
        raise handle_exception(e)

