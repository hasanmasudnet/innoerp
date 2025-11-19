"""
Base database models and session management
"""
from sqlalchemy import create_engine, Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from typing import Generator
import os
from contextlib import contextmanager
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from project root (innoERP directory)
    # override=True ensures .env file values override system environment variables
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"[DEBUG] Loaded .env from: {env_path}")
except ImportError:
    pass  # python-dotenv not installed, use environment variables only
except Exception as e:
    print(f"[WARN] Could not load .env file: {e}")

# Database URL from environment (should be set in .env file)
# For local development, this should point to your local PostgreSQL server
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/innoerp"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantMixin:
    """Mixin for tenant-aware models"""
    __abstract__ = True
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

