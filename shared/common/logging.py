"""
Structured logging utilities for EFK stack integration
"""
import json
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
organization_id_var: ContextVar[Optional[UUID]] = ContextVar('organization_id', default=None)
user_id_var: ContextVar[Optional[UUID]] = ContextVar('user_id', default=None)
service_name_var: ContextVar[Optional[str]] = ContextVar('service_name', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs compatible with EFK stack"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": getattr(record, 'service_name', service_name_var.get('unknown')),
            "organization_id": str(organization_id_var.get()) if organization_id_var.get() else None,
            "user_id": str(user_id_var.get()) if user_id_var.get() else None,
            "request_id": request_id_var.get(),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, 'metadata'):
            log_data["metadata"] = record.metadata
        
        return json.dumps(log_data)


def setup_logger(
    service_name: str,
    level: str = "INFO",
    log_format: str = "json"
) -> logging.Logger:
    """
    Setup structured logger for a service
    
    Args:
        service_name: Name of the service (e.g., 'auth-service')
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    if log_format == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set service name in context
    service_name_var.set(service_name)
    
    return logger


def set_request_context(
    request_id: Optional[str] = None,
    organization_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
):
    """Set request context for logging"""
    if request_id:
        request_id_var.set(request_id)
    if organization_id:
        organization_id_var.set(organization_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context"""
    request_id_var.set(None)
    organization_id_var.set(None)
    user_id_var.set(None)

