"""
Kafka monitoring service
"""
import logging
from typing import List, Dict, Any, Optional
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.admin import ConfigResource, ConfigResourceType
from kafka.errors import KafkaError
import os

logger = logging.getLogger(__name__)


class KafkaMonitor:
    """Monitor Kafka topics, consumers, and metrics"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self._admin_client = None
        self._consumer = None
    
    def _get_admin_client(self):
        """Get or create admin client"""
        if self._admin_client is None:
            try:
                self._admin_client = KafkaAdminClient(
                    bootstrap_servers=self.bootstrap_servers,
                    client_id='monitoring-service'
                )
            except Exception as e:
                logger.error(f"Failed to create Kafka admin client: {e}")
                raise
        return self._admin_client
    
    def _get_consumer(self):
        """Get or create consumer for metadata"""
        if self._consumer is None:
            try:
                self._consumer = KafkaConsumer(
                    bootstrap_servers=self.bootstrap_servers,
                    consumer_timeout_ms=1000
                )
            except Exception as e:
                logger.error(f"Failed to create Kafka consumer: {e}")
                raise
        return self._consumer
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """Get list of all topics with details"""
        try:
            admin_client = self._get_admin_client()
            consumer = self._get_consumer()
            
            # Get topic metadata
            metadata = consumer.list_consumer_groups()
            cluster_metadata = consumer.list_topics()
            
            topics = []
            for topic_name, topic_metadata in cluster_metadata.topics.items():
                partitions = []
                for partition_id, partition_metadata in topic_metadata.partitions.items():
                    partitions.append({
                        "id": partition_id,
                        "leader": partition_metadata.leader,
                        "replicas": partition_metadata.replicas,
                        "isr": partition_metadata.isr,
                    })
                
                topics.append({
                    "name": topic_name,
                    "partitions": len(partitions),
                    "partition_details": partitions,
                })
            
            return topics
        except Exception as e:
            logger.error(f"Error getting topics: {e}")
            return []
    
    def get_consumer_groups(self) -> List[Dict[str, Any]]:
        """Get consumer group information"""
        try:
            admin_client = self._get_admin_client()
            consumer = self._get_consumer()
            
            # Get consumer groups
            groups = admin_client.list_consumer_groups()
            
            consumer_groups = []
            for group_id, group_type in groups:
                try:
                    # Get group details
                    group_metadata = admin_client.describe_consumer_groups([group_id])
                    if group_id in group_metadata:
                        metadata = group_metadata[group_id]
                        consumer_groups.append({
                            "group_id": group_id,
                            "state": metadata.state,
                            "members": len(metadata.members),
                        })
                except Exception as e:
                    logger.warning(f"Error getting details for group {group_id}: {e}")
                    consumer_groups.append({
                        "group_id": group_id,
                        "state": "unknown",
                        "members": 0,
                    })
            
            return consumer_groups
        except Exception as e:
            logger.error(f"Error getting consumer groups: {e}")
            return []
    
    def get_consumer_lag(self, group_id: str, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get consumer lag for a group"""
        try:
            admin_client = self._get_admin_client()
            
            # Get consumer group offsets
            # This is a simplified version - in production, use kafka-python's offset fetcher
            lag_info = []
            
            # For now, return empty list - full implementation would require
            # fetching committed offsets and comparing with latest offsets
            return lag_info
        except Exception as e:
            logger.error(f"Error getting consumer lag: {e}")
            return []
    
    def get_topic_metrics(self, topic: str) -> Dict[str, Any]:
        """Get metrics for a specific topic"""
        try:
            consumer = self._get_consumer()
            
            # Get topic metadata
            cluster_metadata = consumer.list_topics()
            if topic not in cluster_metadata.topics:
                return {}
            
            topic_metadata = cluster_metadata.topics[topic]
            
            return {
                "name": topic,
                "partitions": len(topic_metadata.partitions),
                "partition_ids": list(topic_metadata.partitions.keys()),
            }
        except Exception as e:
            logger.error(f"Error getting topic metrics: {e}")
            return {}
    
    def get_kafka_metrics(self) -> Dict[str, Any]:
        """Get overall Kafka metrics"""
        try:
            topics = self.get_topics()
            consumer_groups = self.get_consumer_groups()
            
            return {
                "total_topics": len(topics),
                "total_consumer_groups": len(consumer_groups),
                "topics": topics,
                "consumer_groups": consumer_groups,
            }
        except Exception as e:
            logger.error(f"Error getting Kafka metrics: {e}")
            return {
                "total_topics": 0,
                "total_consumer_groups": 0,
                "topics": [],
                "consumer_groups": [],
            }
    
    def close(self):
        """Close connections"""
        if self._admin_client:
            try:
                self._admin_client.close()
            except Exception:
                pass
        if self._consumer:
            try:
                self._consumer.close()
            except Exception:
                pass

