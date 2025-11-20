"""
Log aggregation service for Elasticsearch
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from app.config import settings

logger = logging.getLogger(__name__)


class LogAggregator:
    """Aggregate and search logs from Elasticsearch"""
    
    def __init__(self):
        try:
            self.es = Elasticsearch([settings.elasticsearch_url])
            self.index_prefix = settings.elasticsearch_index_prefix
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            self.es = None
    
    def _get_index_name(self, date: Optional[datetime] = None) -> str:
        """Get index name for a date (logstash format)"""
        if date is None:
            date = datetime.utcnow()
        date_str = date.strftime("%Y.%m.%d")
        return f"{self.index_prefix}-{date_str}"
    
    def search_logs(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        query: Optional[str] = None,
        size: int = 100,
        from_: int = 0
    ) -> Dict[str, Any]:
        """Search logs with filters"""
        if not self.es:
            return {
                "total": 0,
                "logs": [],
                "error": "Elasticsearch not available"
            }
        
        try:
            # Build query
            must_clauses = []
            
            if service:
                must_clauses.append({"term": {"service.keyword": service}})
            
            if level:
                must_clauses.append({"term": {"level.keyword": level}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time.isoformat()
                if end_time:
                    time_range["lte"] = end_time.isoformat()
                must_clauses.append({"range": {"@timestamp": time_range}})
            
            if query:
                must_clauses.append({
                    "multi_match": {
                        "query": query,
                        "fields": ["message", "module", "function"],
                        "type": "best_fields"
                    }
                })
            
            es_query = {
                "bool": {
                    "must": must_clauses
                }
            } if must_clauses else {"match_all": {}}
            
            # Get indices for date range
            indices = []
            if start_time and end_time:
                current = start_time
                while current <= end_time:
                    indices.append(self._get_index_name(current))
                    current += timedelta(days=1)
            else:
                # Default to last 7 days
                for i in range(7):
                    date = datetime.utcnow() - timedelta(days=i)
                    indices.append(self._get_index_name(date))
            
            # Search
            response = self.es.search(
                index=",".join(indices),
                body={
                    "query": es_query,
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "size": size,
                    "from": from_,
                }
            )
            
            logs = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                logs.append({
                    "timestamp": source.get("@timestamp", source.get("timestamp")),
                    "level": source.get("level"),
                    "service": source.get("service"),
                    "message": source.get("message"),
                    "module": source.get("module"),
                    "function": source.get("function"),
                    "line": source.get("line"),
                    "request_id": source.get("request_id"),
                    "organization_id": source.get("organization_id"),
                    "user_id": source.get("user_id"),
                    "exception": source.get("exception"),
                })
            
            return {
                "total": response["hits"]["total"]["value"],
                "logs": logs,
            }
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return {
                "total": 0,
                "logs": [],
                "error": str(e)
            }
    
    def get_log_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get log statistics"""
        if not self.es:
            return {
                "error": "Elasticsearch not available"
            }
        
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=1)
            if not end_time:
                end_time = datetime.utcnow()
            
            # Get indices
            indices = []
            current = start_time
            while current <= end_time:
                indices.append(self._get_index_name(current))
                current += timedelta(days=1)
            
            # Aggregate by level
            response = self.es.search(
                index=",".join(indices),
                body={
                    "query": {
                        "range": {
                            "@timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat()
                            }
                        }
                    },
                    "size": 0,
                    "aggs": {
                        "by_level": {
                            "terms": {
                                "field": "level.keyword",
                                "size": 10
                            }
                        },
                        "by_service": {
                            "terms": {
                                "field": "service.keyword",
                                "size": 20
                            }
                        }
                    }
                }
            )
            
            by_level = {}
            for bucket in response["aggregations"]["by_level"]["buckets"]:
                by_level[bucket["key"]] = bucket["doc_count"]
            
            by_service = {}
            for bucket in response["aggregations"]["by_service"]["buckets"]:
                by_service[bucket["key"]] = bucket["doc_count"]
            
            return {
                "total": response["hits"]["total"]["value"],
                "by_level": by_level,
                "by_service": by_service,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                }
            }
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {
                "error": str(e)
            }
    
    def get_error_summary(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get error log summary"""
        if not self.es:
            return []
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            result = self.search_logs(
                level="ERROR",
                start_time=start_time,
                end_time=end_time,
                size=50
            )
            
            return result.get("logs", [])
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return []

