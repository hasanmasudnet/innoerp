"""
Industry template management API routes
"""
import logging
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from shared.database.base import get_db
from app.models import (
    IndustryTemplateCreate, IndustryTemplateUpdate, IndustryTemplateResponse,
    IndustryModuleTemplateResponse, IndustryModuleTemplateCreate, IndustryModuleTemplateUpdate
)
from pydantic import BaseModel, Field
from app.services import IndustryTemplateService
from shared.common.errors import handle_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/industries", tags=["industries"])


@router.get("/test")
def test_industries_route():
    """Test endpoint to verify industries router is accessible"""
    return {"message": "Industries router is working", "status": "ok"}


@router.get("", response_model=List[IndustryTemplateResponse])
def list_industries(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all industry templates"""
    try:
        logger.info(f"Listing industries (active_only={active_only})")
        industries = IndustryTemplateService.list_all(db, active_only=active_only)
        logger.info(f"Found {len(industries)} industries")
        return industries
    except Exception as e:
        logger.error(f"Error listing industries: {e}", exc_info=True)
        raise handle_exception(e)


@router.get("/{industry_code}", response_model=IndustryTemplateResponse)
def get_industry(
    industry_code: str,
    db: Session = Depends(get_db)
):
    """Get industry template details"""
    try:
        return IndustryTemplateService.get_by_code(db, industry_code)
    except Exception as e:
        raise handle_exception(e)


@router.get("/{industry_code}/modules", response_model=List[IndustryModuleTemplateResponse])
def get_industry_modules(
    industry_code: str,
    db: Session = Depends(get_db)
):
    """Get modules for industry template"""
    try:
        logger.info(f"Getting modules for industry: {industry_code}")
        modules = IndustryTemplateService.get_modules(db, industry_code)
        logger.info(f"Found {len(modules)} modules for industry {industry_code}")
        return modules
    except Exception as e:
        logger.error(f"Error getting modules for industry {industry_code}: {e}", exc_info=True)
        raise handle_exception(e)


@router.post("", response_model=IndustryTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_industry(
    template_data: IndustryTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create industry template (super admin)"""
    try:
        return IndustryTemplateService.create_template(db, template_data)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{industry_code}", response_model=IndustryTemplateResponse)
def update_industry(
    industry_code: str,
    template_data: IndustryTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update industry template (super admin)"""
    try:
        return IndustryTemplateService.update_template(db, industry_code, template_data)
    except Exception as e:
        raise handle_exception(e)


@router.delete("/{industry_code}", status_code=status.HTTP_200_OK)
def delete_industry(
    industry_code: str,
    db: Session = Depends(get_db)
):
    """Delete industry template (super admin)"""
    try:
        IndustryTemplateService.delete_template(db, industry_code)
        return {"message": f"Industry template {industry_code} deleted"}
    except Exception as e:
        raise handle_exception(e)


# Module management for industries
class AddModuleToIndustryRequest(BaseModel):
    module_id: str = Field(..., min_length=1, max_length=100)
    is_required: bool = False
    default_config: Dict[str, Any] = Field(default_factory=dict)
    display_order: int = Field(default=0, ge=0)


@router.post("/{industry_code}/modules", response_model=IndustryModuleTemplateResponse, status_code=status.HTTP_201_CREATED)
def add_module_to_industry(
    industry_code: str,
    module_data: AddModuleToIndustryRequest,
    db: Session = Depends(get_db)
):
    """Add a module to an industry template"""
    try:
        logger.info(f"Adding module {module_data.module_id} to industry {industry_code}")
        result = IndustryTemplateService.add_module_to_industry(
            db, industry_code, module_data.module_id, 
            module_data.is_required, module_data.default_config, module_data.display_order
        )
        logger.info(f"Successfully added module {module_data.module_id} to industry {industry_code}")
        return result
    except Exception as e:
        logger.error(f"Error adding module {module_data.module_id} to industry {industry_code}: {e}", exc_info=True)
        raise handle_exception(e)


@router.delete("/{industry_code}/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_module_from_industry(
    industry_code: str,
    module_id: str,
    db: Session = Depends(get_db)
):
    """Remove a module from an industry template"""
    try:
        IndustryTemplateService.remove_module_from_industry(db, industry_code, module_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{industry_code}/modules/{module_id}", response_model=IndustryModuleTemplateResponse)
def update_module_in_industry(
    industry_code: str,
    module_id: str,
    module_data: IndustryModuleTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update module settings in industry template"""
    try:
        return IndustryTemplateService.update_module_in_industry(
            db, industry_code, module_id, module_data
        )
    except Exception as e:
        raise handle_exception(e)

