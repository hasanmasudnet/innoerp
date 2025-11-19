"""
Shared enums for innoERP
"""
from enum import Enum


class UserType(str, Enum):
    """User types within an organization"""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    CLIENT = "client"
    SUPPLIER = "supplier"


class ModuleType(str, Enum):
    """Available modules in the system"""
    PROJECT = "project"
    FINANCE = "finance"
    HR = "hr"
    ATTENDANCE = "attendance"
    LEAVE = "leave"
    CRM = "crm"
    CAREER = "career"
    PORTFOLIO = "portfolio"
    PRODUCTS = "products"
    CONTACT = "contact"


class RelationshipType(str, Enum):
    """Relationship types for module-specific relationships"""
    EMPLOYEE = "employee"
    CLIENT = "client"
    SUPPLIER = "supplier"
    VENDOR = "vendor"


class InvitationStatus(str, Enum):
    """Invitation status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"

