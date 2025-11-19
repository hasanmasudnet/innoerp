"""
Kafka event schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any


class BaseEvent(BaseModel):
    """Base event schema for all Kafka events"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    organization_id: UUID
    user_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() + "Z",
            UUID: str
        }
    }


# Tenant events
class TenantCreatedEvent(BaseEvent):
    event_type: str = "tenant.created"
    payload: Dict[str, Any]  # Contains tenant data


class TenantUpdatedEvent(BaseEvent):
    event_type: str = "tenant.updated"
    payload: Dict[str, Any]  # Contains updated tenant data


class TenantDeletedEvent(BaseEvent):
    event_type: str = "tenant.deleted"
    payload: Dict[str, Any]  # Contains tenant ID


class SubscriptionChangedEvent(BaseEvent):
    event_type: str = "subscription.changed"
    payload: Dict[str, Any]  # Contains subscription data


# User events
class UserCreatedEvent(BaseEvent):
    event_type: str = "user.created"
    payload: Dict[str, Any]  # Contains user data


class UserUpdatedEvent(BaseEvent):
    event_type: str = "user.updated"
    payload: Dict[str, Any]  # Contains updated user data


class UserDeletedEvent(BaseEvent):
    event_type: str = "user.deleted"
    payload: Dict[str, Any]  # Contains user ID


class UserAuthenticatedEvent(BaseEvent):
    event_type: str = "user.authenticated"
    payload: Dict[str, Any]  # Contains authentication details


class UserRoleChangedEvent(BaseEvent):
    event_type: str = "user.role.changed"
    payload: Dict[str, Any]  # Contains role change data


class UserInvitedEvent(BaseEvent):
    event_type: str = "user.invited"
    payload: Dict[str, Any]  # Contains invitation data (email, user_type, module_type, token)


class UserTypeChangedEvent(BaseEvent):
    event_type: str = "user.type.changed"
    payload: Dict[str, Any]  # Contains user type change data (old_type, new_type)


class UserRelationshipCreatedEvent(BaseEvent):
    event_type: str = "user.relationship.created"
    payload: Dict[str, Any]  # Contains relationship data (module_type, relationship_type, role)


# Project events
class ProjectCreatedEvent(BaseEvent):
    event_type: str = "project.created"
    payload: Dict[str, Any]  # Contains project data


class ProjectUpdatedEvent(BaseEvent):
    event_type: str = "project.updated"
    payload: Dict[str, Any]  # Contains updated project data


class TaskCreatedEvent(BaseEvent):
    event_type: str = "task.created"
    payload: Dict[str, Any]  # Contains task data


class TaskUpdatedEvent(BaseEvent):
    event_type: str = "task.updated"
    payload: Dict[str, Any]  # Contains updated task data
