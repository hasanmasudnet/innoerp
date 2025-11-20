"""
Shared middleware for request/response logging
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
from shared.common.logging import get_logger, set_request_context, clear_request_context, service_name_var

# Get logger - will use EALogger if available
logger = get_logger(__name__, app_name="middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Set request context
        set_request_context(request_id=request_id)
        
        # Start time
        start_time = time.time()
        
        # Log request
        app_name = service_name_var.get() or "unknown-service"
        logger.info(
            f"Request: {request.method} {request.url.path}",
            "request",
            request.method,
            "",
            app_name,
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            app_name = service_name_var.get() or "unknown-service"
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code}",
                "response",
                request.method,
                "",
                app_name,
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            # Add request ID to response header
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            app_name = service_name_var.get() or "unknown-service"
            logger.error(
                f"Request error: {request.method} {request.url.path}",
                "request_error",
                request.method,
                "",
                app_name,
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                }
            )
            raise
        finally:
            # Clear request context
            clear_request_context()

