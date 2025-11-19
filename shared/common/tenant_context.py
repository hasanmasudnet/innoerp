"""
Tenant context management for multi-tenancy
"""
from typing import Optional
from uuid import UUID
from contextvars import ContextVar
from fastapi import Request, Header
from shared.common.errors import TenantNotFoundError, TenantInactiveError

# Context variable to store current tenant
current_tenant_var: ContextVar[Optional[UUID]] = ContextVar('current_tenant', default=None)


class TenantContext:
    """Manages tenant context for requests"""
    
    @staticmethod
    def set_tenant(organization_id: UUID):
        """Set the current tenant in context"""
        current_tenant_var.set(organization_id)
    
    @staticmethod
    def get_tenant() -> Optional[UUID]:
        """Get the current tenant from context"""
        return current_tenant_var.get()
    
    @staticmethod
    def clear_tenant():
        """Clear the current tenant from context"""
        current_tenant_var.set(None)
    
    @staticmethod
    async def extract_from_request(request: Request) -> Optional[UUID]:
        """
        Extract tenant from request (subdomain, header, or path)
        
        Priority:
        1. X-Organization-ID header
        2. Subdomain from host
        3. Path parameter
        
        Returns:
            Organization ID if found, None otherwise
        """
        # Check header first
        org_id_header = request.headers.get("X-Organization-ID")
        if org_id_header:
            try:
                return UUID(org_id_header)
            except ValueError:
                pass
        
        # Check subdomain
        host = request.headers.get("host", "")
        if host:
            subdomain = host.split(".")[0]
            if subdomain and subdomain != "www" and subdomain != "api":
                # This would need to be resolved via tenant service
                # For now, return None and let the service handle it
                pass
        
        return None
    
    @staticmethod
    def require_tenant() -> UUID:
        """
        Require tenant to be set, raise error if not
        
        Raises:
            TenantNotFoundError: If tenant is not set
        """
        tenant = current_tenant_var.get()
        if not tenant:
            raise TenantNotFoundError("Tenant context not set")
        return tenant

