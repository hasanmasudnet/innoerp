"""
Kafka consumer service for module events
"""
import os
import logging
from typing import Dict, Any
from uuid import UUID
from confluent_kafka import Consumer, KafkaError
from shared.kafka.schemas import (
    ModuleAssignedEvent, ModuleUnassignedEvent, ModulesBulkAssignedEvent,
    IndustryTemplateAppliedEvent, ModuleConfigUpdatedEvent
)
from shared.database.base import SessionLocal
from app.repositories import OrganizationModuleRepository, ModuleRegistryRepository
from app.cache_service import _cache_service

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "tenant-service-module-consumer")


def handle_module_assigned(event: ModuleAssignedEvent):
    """Handle module assigned event - update database, invalidate cache"""
    try:
        db = SessionLocal()
        try:
            # Event already processed by producer, but ensure cache is invalidated
            org_id = event.organization_id
            _cache_service.invalidate_org_modules(org_id)
            logger.info(f"Module assigned event processed for org {org_id}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error handling module assigned event: {e}")


def handle_module_unassigned(event: ModuleUnassignedEvent):
    """Handle module unassigned event - update database, invalidate cache"""
    try:
        db = SessionLocal()
        try:
            # Event already processed by producer, but ensure cache is invalidated
            org_id = event.organization_id
            _cache_service.invalidate_org_modules(org_id)
            logger.info(f"Module unassigned event processed for org {org_id}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error handling module unassigned event: {e}")


def handle_bulk_assigned(event: ModulesBulkAssignedEvent):
    """Handle bulk module assignment event - batch update database"""
    try:
        db = SessionLocal()
        try:
            # Event already processed by producer, but ensure cache is invalidated
            org_id = event.organization_id
            _cache_service.invalidate_org_modules(org_id)
            logger.info(f"Bulk module assignment event processed for org {org_id}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error handling bulk assignment event: {e}")


def handle_industry_template_applied(event: IndustryTemplateAppliedEvent):
    """Handle industry template applied event"""
    try:
        db = SessionLocal()
        try:
            # Invalidate caches
            org_id = event.organization_id
            industry_code = event.payload.get("industry_code")
            
            _cache_service.invalidate_org_modules(org_id)
            if industry_code:
                _cache_service.invalidate_industry_modules(industry_code)
            
            logger.info(f"Industry template applied event processed for org {org_id}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error handling industry template applied event: {e}")


def handle_module_config_updated(event: ModuleConfigUpdatedEvent):
    """Handle module config updated event"""
    try:
        db = SessionLocal()
        try:
            org_id = event.organization_id
            _cache_service.invalidate_org_modules(org_id)
            logger.info(f"Module config updated event processed for org {org_id}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error handling module config updated event: {e}")


# Event handler mapping
EVENT_HANDLERS = {
    "module.assigned": handle_module_assigned,
    "module.unassigned": handle_module_unassigned,
    "module.bulk_assigned": handle_bulk_assigned,
    "industry.template_applied": handle_industry_template_applied,
    "module.config_updated": handle_module_config_updated,
}


def consume_module_events():
    """Consume module events from Kafka"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
    })
    
    # Subscribe to module event topics
    topics = [
        'tenant.module.assigned',
        'tenant.module.unassigned',
        'tenant.module.bulk_assigned',
        'tenant.module.template_applied',
        'tenant.module.config_updated',
    ]
    
    consumer.subscribe(topics)
    logger.info(f"Subscribed to topics: {topics}")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
            
            try:
                # Parse event
                import json
                event_data = json.loads(msg.value().decode('utf-8'))
                event_type = event_data.get('event_type')
                
                # Route to appropriate handler
                handler = EVENT_HANDLERS.get(event_type)
                if handler:
                    # Create event object from data
                    if event_type == "module.assigned":
                        event = ModuleAssignedEvent(**event_data)
                    elif event_type == "module.unassigned":
                        event = ModuleUnassignedEvent(**event_data)
                    elif event_type == "module.bulk_assigned":
                        event = ModulesBulkAssignedEvent(**event_data)
                    elif event_type == "industry.template_applied":
                        event = IndustryTemplateAppliedEvent(**event_data)
                    elif event_type == "module.config_updated":
                        event = ModuleConfigUpdatedEvent(**event_data)
                    else:
                        logger.warning(f"Unknown event type: {event_type}")
                        continue
                    
                    handler(event)
                else:
                    logger.warning(f"No handler for event type: {event_type}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        logger.info("Consumer interrupted")
    finally:
        consumer.close()


if __name__ == "__main__":
    # Run consumer (typically run as a separate process/service)
    logging.basicConfig(level=logging.INFO)
    consume_module_events()

