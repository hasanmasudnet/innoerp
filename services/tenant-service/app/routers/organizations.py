"""
Organization API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pathlib import Path
import os
import shutil
from shared.database.base import get_db
from app.models import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    TenantSignupRequest, SubdomainCheckRequest, SubdomainCheckResponse,
    TenantStatsResponse, OrganizationBrandingUpdate, OrganizationBrandingResponse,
    TenantStatusUpdate, TenantTrialUpdate, OrganizationSubscriptionResponse
)
from app.services import OrganizationService, BrandingService
from shared.common.errors import handle_exception
import re

router = APIRouter(prefix="/tenants", tags=["tenants"])

# Also create organizations router for backward compatibility
org_router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """Create new organization"""
    try:
        return OrganizationService.create_organization(db, org_data)
    except Exception as e:
        raise handle_exception(e)


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get organization by ID"""
    try:
        return OrganizationService.get_organization(db, organization_id)
    except Exception as e:
        raise handle_exception(e)


@router.get("/slug/{slug}", response_model=OrganizationResponse)
def get_organization_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get organization by slug"""
    try:
        return OrganizationService.get_organization_by_slug(db, slug)
    except Exception as e:
        raise handle_exception(e)


@router.get("/subdomain/{subdomain}", response_model=OrganizationResponse)
def get_organization_by_subdomain(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """Get organization by subdomain"""
    try:
        return OrganizationService.get_organization_by_subdomain(db, subdomain)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: UUID,
    org_data: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization"""
    try:
        return OrganizationService.update_organization(db, organization_id, org_data)
    except Exception as e:
        raise handle_exception(e)


@router.post("/check-subdomain", response_model=SubdomainCheckResponse)
def check_subdomain(
    request: SubdomainCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if subdomain is available"""
    try:
        # Normalize subdomain to lowercase
        normalized_subdomain = request.subdomain.lower().strip()
        
        # Validate subdomain format
        if not normalized_subdomain:
            return SubdomainCheckResponse(
                available=False,
                subdomain=request.subdomain,
                message="Subdomain cannot be empty"
            )
        
        if len(normalized_subdomain) < 3:
            return SubdomainCheckResponse(
                available=False,
                subdomain=request.subdomain,
                message="Subdomain must be at least 3 characters"
            )
        
        if len(normalized_subdomain) > 100:
            return SubdomainCheckResponse(
                available=False,
                subdomain=request.subdomain,
                message="Subdomain must be less than 100 characters"
            )
        
        if not re.match(r'^[a-z0-9-]+$', normalized_subdomain):
            return SubdomainCheckResponse(
                available=False,
                subdomain=request.subdomain,
                message="Subdomain can only contain lowercase letters, numbers, and hyphens"
            )
        
        # Check if subdomain starts or ends with hyphen
        if normalized_subdomain.startswith('-') or normalized_subdomain.endswith('-'):
            return SubdomainCheckResponse(
                available=False,
                subdomain=request.subdomain,
                message="Subdomain cannot start or end with a hyphen"
            )
        
        available = OrganizationService.check_subdomain_available(db, normalized_subdomain)
        return SubdomainCheckResponse(
            available=available,
            subdomain=normalized_subdomain,
            message="Available" if available else "Subdomain already taken"
        )
    except Exception as e:
        return SubdomainCheckResponse(
            available=False,
            subdomain=request.subdomain,
            message=f"Error checking subdomain: {str(e)}"
        )


@router.post("/signup", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def tenant_signup(
    signup_data: TenantSignupRequest,
    db: Session = Depends(get_db)
):
    """Create new tenant organization with subdomain"""
    try:
        # Check subdomain availability
        if not OrganizationService.check_subdomain_available(db, signup_data.subdomain):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subdomain '{signup_data.subdomain}' is already taken"
            )
        
        # Generate slug from business name
        slug = signup_data.business_name.lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        
        # Create organization
        org_data = OrganizationCreate(
            name=signup_data.business_name,
            slug=slug,
            subdomain=signup_data.subdomain,
            owner_email=signup_data.owner_email,
            owner_name=signup_data.owner_name
        )
        
        org = OrganizationService.create_organization(db, org_data, trial_days=14, industry_code=signup_data.industry_code)
        
        # Auto-assign modules from industry template if provided
        if signup_data.industry_code:
            try:
                from app.services import ModuleService
                ModuleService.assign_from_industry(db, org.id, signup_data.industry_code)
            except Exception as e:
                # Log error but don't fail signup if module assignment fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to assign modules from industry {signup_data.industry_code}: {e}")
        
        # TODO: Create admin user account using auth-service
        # This should be done via API call to auth-service or user-service
        
        return org
    except Exception as e:
        raise handle_exception(e)


@router.get("/stats", response_model=TenantStatsResponse)
def get_tenant_stats(
    db: Session = Depends(get_db)
):
    """Get tenant statistics (super admin only)"""
    try:
        stats = OrganizationService.get_tenant_stats(db)
        return TenantStatsResponse(**stats)
    except Exception as e:
        raise handle_exception(e)


@router.get("", response_model=List[OrganizationResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all tenants (super admin only)"""
    try:
        return OrganizationService.list_all_organizations(db, skip, limit)
    except Exception as e:
        raise handle_exception(e)


@router.get("/{organization_id}/branding", response_model=OrganizationBrandingResponse)
def get_organization_branding(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get organization branding"""
    try:
        branding = BrandingService.get_branding(db, organization_id)
        if not branding:
            # Return default branding if not found (as dict, not SQLAlchemy model)
            from datetime import datetime
            from uuid import uuid4
            default_branding_dict = {
                "id": str(uuid4()),
                "organization_id": str(organization_id),
                "primary_color": "#1976d2",
                "secondary_color": "#dc004e",
                "accent_color": "#00a86b",
                "font_family": "Inter",
                "theme_preset": "base",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            return OrganizationBrandingResponse(**default_branding_dict)
        
        # Convert SQLAlchemy model to Pydantic response
        # Handle UUID conversion properly
        try:
            return OrganizationBrandingResponse.model_validate(branding)
        except Exception as validation_error:
            # Fallback: manual conversion if model_validate fails
            branding_dict = {
                "id": str(branding.id),
                "organization_id": str(branding.organization_id),
                "company_name": getattr(branding, 'company_name', None),
                "logo_url": getattr(branding, 'logo_url', None),
                "favicon_url": getattr(branding, 'favicon_url', None),
                "primary_color": branding.primary_color or "#1976d2",
                "secondary_color": branding.secondary_color or "#dc004e",
                "accent_color": branding.accent_color or "#00a86b",
                "font_family": getattr(branding, 'font_family', None) or "Inter",
                "heading_font": getattr(branding, 'heading_font', None),
                "theme_preset": getattr(branding, 'theme_preset', None) or "base",
                "custom_css": getattr(branding, 'custom_css', None),
                "created_at": branding.created_at,
                "updated_at": branding.updated_at,
            }
            return OrganizationBrandingResponse(**branding_dict)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise handle_exception(e)


@router.put("/{organization_id}/branding", response_model=OrganizationBrandingResponse)
def update_organization_branding(
    organization_id: UUID,
    branding_data: OrganizationBrandingUpdate,
    db: Session = Depends(get_db)
):
    """Update organization branding"""
    try:
        branding = BrandingService.update_branding(
            db,
            organization_id,
            branding_data.model_dump(exclude_unset=True)
        )
        return OrganizationBrandingResponse.model_validate(branding)
    except Exception as e:
        raise handle_exception(e)


@router.post("/{organization_id}/branding/upload-logo")
async def upload_logo(
    organization_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload logo file for organization"""
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/svg+xml', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate file size (max 5MB)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 5MB limit"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("media/branding")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        filename = f"{organization_id}_logo{file_ext}"
        file_path = upload_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Generate protected URL (served through authenticated endpoint)
        file_url = f"/api/v1/tenants/branding/media/{filename}"
        
        # Update branding with logo URL
        branding = BrandingService.update_branding(
            db,
            organization_id,
            {"logo_url": file_url}
        )
        
        return JSONResponse({
            "logo_url": file_url,
            "message": "Logo uploaded successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise handle_exception(e)


@router.post("/{organization_id}/branding/upload-favicon")
async def upload_favicon(
    organization_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload favicon file for organization"""
    try:
        # Validate file type
        allowed_types = ['image/x-icon', 'image/png', 'image/svg+xml']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate file size (max 1MB for favicon)
        file_content = await file.read()
        if len(file_content) > 1 * 1024 * 1024:  # 1MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 1MB limit"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("media/branding")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        filename = f"{organization_id}_favicon{file_ext}"
        file_path = upload_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Generate protected URL (served through authenticated endpoint)
        file_url = f"/api/v1/tenants/branding/media/{filename}"
        
        # Update branding with favicon URL
        branding = BrandingService.update_branding(
            db,
            organization_id,
            {"favicon_url": file_url}
        )
        
        return JSONResponse({
            "favicon_url": file_url,
            "message": "Favicon uploaded successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise handle_exception(e)


@router.get("/branding/media/{filename:path}")
async def get_branding_media(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Protected endpoint to serve uploaded branding files.
    Only accessible to authenticated users (via API Gateway or direct auth).
    This prevents direct URL access to uploaded files.
    """
    try:
        # Validate filename format (should be {org_id}_logo.{ext} or {org_id}_favicon.{ext})
        if not filename or '..' in filename or '/' in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        file_path = Path("media/branding") / filename
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Determine content type based on extension
        ext = file_path.suffix.lower()
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
            '.ico': 'image/x-icon',
        }
        media_type = content_type_map.get(ext, 'application/octet-stream')
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise handle_exception(e)


# Super admin endpoints for tenant management
@router.get("/{organization_id}/details", response_model=dict)
def get_tenant_details(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get comprehensive tenant details for super admin"""
    try:
        return OrganizationService.get_tenant_details(db, organization_id)
    except Exception as e:
        raise handle_exception(e)


@router.get("/{organization_id}/subscription", response_model=Optional[OrganizationSubscriptionResponse])
def get_tenant_subscription(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get tenant subscription details"""
    try:
        from app.services import SubscriptionService
        return SubscriptionService.get_subscription(db, organization_id)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{organization_id}/status", response_model=OrganizationResponse)
def update_tenant_status(
    organization_id: UUID,
    status_update: TenantStatusUpdate,
    db: Session = Depends(get_db)
):
    """Activate or deactivate tenant"""
    try:
        from app.models import TenantStatusUpdate
        return OrganizationService.update_tenant_status(db, organization_id, status_update.is_active)
    except Exception as e:
        raise handle_exception(e)


@router.patch("/{organization_id}/trial", response_model=OrganizationResponse)
def extend_tenant_trial(
    organization_id: UUID,
    trial_update: TenantTrialUpdate,
    db: Session = Depends(get_db)
):
    """Extend trial period for tenant"""
    try:
        from app.models import TenantTrialUpdate
        return OrganizationService.extend_trial(db, organization_id, trial_update.days)
    except Exception as e:
        raise handle_exception(e)


@router.get("/{organization_id}/usage", response_model=dict)
def get_tenant_usage(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get tenant usage statistics"""
    try:
        from app.models import TenantUsageResponse
        # This would typically call user-service and project-service
        # For now, return placeholder
        return TenantUsageResponse(
            total_users=0,
            active_users=0,
            total_projects=None,
            storage_used_mb=None,
            api_calls_this_month=None,
            last_active=None
        ).dict()
    except Exception as e:
        raise handle_exception(e)


# Register organizations router with same routes for backward compatibility
for route in router.routes:
    org_router.routes.append(route)

