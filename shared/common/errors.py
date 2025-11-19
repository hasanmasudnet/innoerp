"""
Common error classes and error handling utilities
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class InnoERPException(Exception):
    """Base exception for innoERP"""
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class TenantNotFoundError(InnoERPException):
    """Raised when tenant is not found"""
    pass


class TenantInactiveError(InnoERPException):
    """Raised when tenant is inactive"""
    pass


class UnauthorizedError(InnoERPException):
    """Raised when user is not authorized"""
    pass


class ValidationError(InnoERPException):
    """Raised when validation fails"""
    pass


class ResourceNotFoundError(InnoERPException):
    """Raised when a resource is not found"""
    pass


def handle_exception(error: Exception) -> HTTPException:
    """Convert innoERP exceptions to HTTP exceptions"""
    if isinstance(error, TenantNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Tenant not found", "message": error.message}
        )
    elif isinstance(error, TenantInactiveError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Tenant inactive", "message": error.message}
        )
    elif isinstance(error, UnauthorizedError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "message": error.message}
        )
    elif isinstance(error, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Validation error", "message": error.message, "details": error.details}
        )
    elif isinstance(error, ResourceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Resource not found", "message": error.message}
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(error)}
        )

