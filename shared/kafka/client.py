"""
Kafka client wrapper for producers and consumers
"""
from typing import Optional, Callable, List
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from datetime import datetime
from uuid import UUID
from shared.kafka.schemas import BaseEvent

logger = logging.getLogger(__name__)


class KafkaProducerWrapper:
    """Wrapper for Kafka producer with error handling and retry logic"""
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        value_serializer: Optional[Callable] = None
    ):
        self.bootstrap_servers = bootstrap_servers
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=value_serializer or (lambda v: json.dumps(v).encode('utf-8')),
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1,
            enable_idempotence=True
        )
    
    def send_event(
        self,
        topic: str,
        event: BaseEvent,
        key: Optional[str] = None
    ) -> bool:
        """
        Send event to Kafka topic
        
        Args:
            topic: Kafka topic name
            event: Event object (BaseEvent or subclass)
            key: Optional partition key
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Convert event to dict (Pydantic v2)
            try:
                event_dict = event.model_dump(mode='json')  # Pydantic v2 - converts UUIDs to strings
            except AttributeError:
                # Fallback for Pydantic v1
                event_dict = event.dict()
            
            # Use organization_id as key if not provided
            if not key:
                key = str(event.organization_id)
            
            future = self.producer.send(
                topic,
                value=event_dict,
                key=key.encode('utf-8') if key else None
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Event sent to topic {topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send event to {topic}: {e}")
            return False
    
    def close(self):
        """Close the producer"""
        self.producer.close()


class KafkaConsumerWrapper:
    """Wrapper for Kafka consumer with error handling"""
    
    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: str = "localhost:9092",
        value_deserializer: Optional[Callable] = None
    ):
        self.topics = topics
        self.group_id = group_id
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=value_deserializer or (lambda m: json.loads(m.decode('utf-8'))),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=1000
        )
    
    def consume(
        self,
        handler: Callable[[dict], None],
        max_messages: Optional[int] = None
    ):
        """
        Consume messages from topics and call handler
        
        Args:
            handler: Function to handle each message
            max_messages: Maximum number of messages to consume (None for unlimited)
        """
        message_count = 0
        try:
            for message in self.consumer:
                try:
                    handler(message.value)
                    message_count += 1
                    
                    if max_messages and message_count >= max_messages:
                        break
                        
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    # Could send to dead letter queue here
                    
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.consumer.close()
    
    def close(self):
        """Close the consumer"""
        self.consumer.close()

