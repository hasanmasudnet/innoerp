"""
Kafka producer for tenant service events
"""
import os
from shared.kafka.client import KafkaProducerWrapper
from shared.kafka.schemas import BaseEvent

# Initialize producer
producer = KafkaProducerWrapper(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
)


def publish_tenant_event(topic: str, event: BaseEvent):
    """Publish tenant event to Kafka"""
    producer.send_event(topic, event)

