"""
Kafka transaction wrapper for atomic DB+Kafka operations
"""
import functools
import logging
from typing import Callable, Any, Optional
from sqlalchemy.orm import Session
from contextlib import contextmanager
from shared.database.base import get_db_context

logger = logging.getLogger(__name__)


@contextmanager
def kafka_transaction(db: Session, event_publisher: Optional[Callable] = None, event_data: Optional[dict] = None):
    """
    Context manager for atomic database + Kafka operations
    
    Usage:
        with kafka_transaction(db, publish_module_event, {"module_id": "projects"}) as tx:
            # DB operations
            org = create_organization(...)
            db.commit()
            
            # Event will be published after successful commit
            tx.publish_event()
    
    Args:
        db: Database session
        event_publisher: Function to publish event (e.g., publish_module_event)
        event_data: Event data to publish
    """
    class TransactionContext:
        def __init__(self, db_session, publisher, data):
            self.db = db_session
            self.publisher = publisher
            self.event_data = data
            self._committed = False
        
        def publish_event(self):
            """Publish event after successful DB commit"""
            if self.publisher and self.event_data:
                try:
                    self.publisher(**self.event_data)
                except Exception as e:
                    logger.error(f"Failed to publish event after DB commit: {e}")
                    # Event publishing failure doesn't rollback DB (eventual consistency)
    
    ctx = TransactionContext(db, event_publisher, event_data)
    
    try:
        yield ctx
        # Commit DB transaction
        db.commit()
        ctx._committed = True
        
        # Publish event after successful commit
        if event_publisher and event_data:
            ctx.publish_event()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction failed, rolled back: {e}")
        raise


def kafka_transaction_decorator(event_publisher_func: Optional[str] = None):
    """
    Decorator for functions that need atomic DB+Kafka operations
    
    Usage:
        @kafka_transaction_decorator(event_publisher_func="publish_module_event")
        def assign_module(db: Session, org_id: UUID, module_id: str, user_id: UUID):
            # DB operations
            module = create_module(...)
            db.commit()
            
            # Event will be auto-published after commit
            return module
    
    Args:
        event_publisher_func: Name of the event publisher function (must be in module scope)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract db session from args/kwargs
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            if not db and 'db' in kwargs:
                db = kwargs['db']
            
            if not db:
                raise ValueError("Database session not found in function arguments")
            
            # Get event publisher if specified
            publisher = None
            if event_publisher_func:
                import sys
                module = sys.modules[func.__module__]
                publisher = getattr(module, event_publisher_func, None)
                if not publisher:
                    logger.warning(f"Event publisher function {event_publisher_func} not found in module")
            
            # Extract event data from function result or kwargs
            # This is a simple implementation - may need refinement based on use case
            event_data = {}
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # If function returns event data, use it
                if isinstance(result, dict) and 'event_data' in result:
                    event_data = result.pop('event_data')
                    publisher_func = result.pop('event_publisher', publisher)
                    if publisher_func:
                        publisher_func(**event_data)
                    return result
                
                # Otherwise, try to construct event data from result
                # This is use-case specific and may need customization
                
                return result
                
            except Exception as e:
                if db:
                    db.rollback()
                raise
        
        return wrapper
    return decorator

