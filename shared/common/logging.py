"""
EALogger integration wrapper for innoERP services
Provides backward compatibility and EALogger integration
"""
import logging
from typing import Optional
from uuid import UUID
from contextvars import ContextVar

# Try to import EALogger
try:
    from EALogger.logging_setup import get_logger as ea_get_logger
    from EALogger.decorators import log_entry_exit as ea_log_entry_exit
    EALOGGER_AVAILABLE = True
except ImportError:
    EALOGGER_AVAILABLE = False
    ea_get_logger = None
    ea_log_entry_exit = None

# Context variables for request tracking (for backward compatibility)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
organization_id_var: ContextVar[Optional[UUID]] = ContextVar('organization_id', default=None)
user_id_var: ContextVar[Optional[UUID]] = ContextVar('user_id', default=None)
service_name_var: ContextVar[Optional[str]] = ContextVar('service_name', default=None)


def get_logger(module_name: str, app_name: str):
    """
    Get logger using EALogger if available, otherwise fallback to standard logging
    
    Args:
        module_name: Name of the module (usually __name__)
        app_name: Name of the application/service (e.g., 'auth-service')
    
    Returns:
        Logger instance
    """
    if EALOGGER_AVAILABLE:
        return ea_get_logger(module_name, app_name=app_name)
    else:
        # Fallback to standard logging
        logger = logging.getLogger(module_name)
        if not logger.handlers:
            import sys
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


def log_entry_exit(app_name: str):
    """
    Decorator for logging function entry/exit using EALogger
    
    Args:
        app_name: Name of the application/service
    
    Returns:
        Decorator function
    """
    if EALOGGER_AVAILABLE:
        return ea_log_entry_exit(app_name=app_name)
    else:
        # Fallback: no-op decorator
        def decorator(func):
            return func
        return decorator


def set_request_context(
    request_id: Optional[str] = None,
    organization_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
):
    """Set request context for logging (backward compatibility)"""
    if request_id:
        request_id_var.set(request_id)
    if organization_id:
        organization_id_var.set(organization_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context (backward compatibility)"""
    request_id_var.set(None)
    organization_id_var.set(None)
    user_id_var.set(None)


# Backward compatibility: keep setup_logger for existing code
def setup_logger(service_name: str, level: str = "INFO", log_format: str = "json"):
    """
    Setup logger (backward compatibility wrapper)
    Now uses EALogger if available
    """
    logger = get_logger(service_name, app_name=service_name)
    service_name_var.set(service_name)
    return logger
