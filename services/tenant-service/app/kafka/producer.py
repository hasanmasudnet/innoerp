"""
Kafka producer for tenant service events
"""
import os
import logging
from typing import Optional
from uuid import UUID
from shared.kafka.client import KafkaProducerWrapper
from shared.kafka.schemas import (
    BaseEvent, ModuleAssignedEvent, ModuleUnassignedEvent,
    ModulesBulkAssignedEvent, IndustryTemplateAppliedEvent,
    ModuleConfigUpdatedEvent, ModuleRegisteredEvent, ModuleUpdatedEvent
)

logger = logging.getLogger(__name__)

# Initialize producer
producer = KafkaProducerWrapper(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
)


def publish_tenant_event(topic: str, event: BaseEvent):
    """Publish tenant event to Kafka"""
    producer.send_event(topic, event)


def publish_module_event(event_type: str, event_data: dict, organization_id: UUID, user_id: Optional[UUID] = None):
    """
    Publish module-related event to Kafka
    
    Args:
        event_type: Event type (e.g., "module.assigned", "module.unassigned")
        event_data: Event payload data
        organization_id: Organization ID
        user_id: User ID who performed the action (optional)
    
    Topic naming: tenant.module.{action}
    Partition key: organization_id for ordering
    """
    topic = f"tenant.module.{event_type.split('.')[-1]}"  # e.g., "tenant.module.assigned"
    
    # Create appropriate event based on type
    event_classes = {
        "module.assigned": ModuleAssignedEvent,
        "module.unassigned": ModuleUnassignedEvent,
        "module.bulk_assigned": ModulesBulkAssignedEvent,
        "industry.template_applied": IndustryTemplateAppliedEvent,
        "module.config_updated": ModuleConfigUpdatedEvent,
        "module.registered": ModuleRegisteredEvent,
        "module.updated": ModuleUpdatedEvent,
    }
    
    event_class = event_classes.get(event_type)
    if not event_class:
        logger.warning(f"Unknown event type: {event_type}, using BaseEvent")
        event_class = BaseEvent
    
    event = event_class(
        organization_id=organization_id,
        user_id=user_id,
        payload=event_data
    )
    
    # Use organization_id as partition key for ordering
    key = str(organization_id)
    
    try:
        success = producer.send_event(topic, event, key=key)
        if success:
            logger.info(f"Published {event_type} event to {topic} for org {organization_id}")
        else:
            logger.error(f"Failed to publish {event_type} event to {topic}")
        return success
    except Exception as e:
        logger.error(f"Error publishing {event_type} event: {e}")
        return False

