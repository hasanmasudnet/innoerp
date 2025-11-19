"""
Proxy router for forwarding requests to services
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import Response
from typing import Optional
import httpx
from app.config import SERVICE_REGISTRY
from app.middleware.auth import get_current_user_from_token
from app.middleware.tenant import extract_subdomain, get_tenant_from_subdomain
from shared.common.logging import set_request_context
from uuid import UUID

router = APIRouter()


async def proxy_request(
    request: Request,
    service_name: str,
    path: str,
    require_auth: bool = True
) -> Response:
    """
    Proxy request to backend service
    
    Args:
        request: FastAPI request object
        service_name: Name of the service to proxy to
        path: Path to forward (without service prefix)
        require_auth: Whether authentication is required
    """
    # Get service URL
    service_url = SERVICE_REGISTRY.get(service_name)
    if not service_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service {service_name} not available"
        )
    
    # Extract tenant from subdomain
    subdomain = extract_subdomain(request)
    organization_id = None
    if subdomain:
        organization_id = await get_tenant_from_subdomain(subdomain)
        if organization_id:
            set_request_context(organization_id=organization_id)
    
    # Get authentication token
    auth_header = request.headers.get("authorization")
    token = None
    user_info = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user_info = await get_current_user_from_token(token)
        if user_info:
            set_request_context(
                user_id=UUID(user_info["user_id"]),
                organization_id=UUID(user_info["organization_id"]) if user_info.get("organization_id") else organization_id
            )
    
    # Check authentication requirement
    if require_auth and not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Build target URL
    target_url = f"{service_url}{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Add organization header if we have it
    if organization_id:
        headers["X-Organization-ID"] = str(organization_id)
    
    # Forward request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                timeout=30.0
            )
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service {service_name} unavailable: {str(e)}"
        )


# Route definitions
@router.api_route("/{service_name:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(
    request: Request,
    service_name: str
):
    """
    Proxy all requests to appropriate services
    
    Service routing:
    - /api/v1/tenants/* -> tenant-service
    - /api/v1/auth/* -> auth-service
    - /api/v1/users/* -> user-service
    - /api/v1/projects/* -> project-service
    - /api/v1/employees/* -> employee-service
    """
    # Extract path after service name
    path = request.url.path
    
    # Determine service from path
    if path.startswith("/api/v1/tenants") or path.startswith("/api/v1/organizations"):
        service = "tenants"
        service_path = path.replace("/api/v1/tenants", "").replace("/api/v1/organizations", "")
    elif path.startswith("/api/v1/auth"):
        service = "auth"
        service_path = path.replace("/api/v1/auth", "")
        require_auth = path not in ["/api/v1/auth/login", "/api/v1/auth/register"]
    elif path.startswith("/api/v1/users"):
        service = "users"
        service_path = path.replace("/api/v1/users", "")
    elif path.startswith("/api/v1/projects"):
        service = "projects"
        service_path = path.replace("/api/v1/projects", "")
    elif path.startswith("/api/v1/employees"):
        service = "employees"
        service_path = path.replace("/api/v1/employees", "")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Ensure path starts with /
    if not service_path.startswith("/"):
        service_path = "/" + service_path
    
    # Add service prefix
    service_path = f"/api/v1{service_path}"
    
    # Determine if auth is required (default True)
    require_auth = service not in ["auth"] or path not in ["/api/v1/auth/login", "/api/v1/auth/register"]
    
    return await proxy_request(request, service, service_path, require_auth)

