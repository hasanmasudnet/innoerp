"""
Utility functions for authentication
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from uuid import UUID

# Password hashing - use bcrypt directly to avoid version conflicts
try:
    import bcrypt
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        try:
            # Encode password to bytes
            password_bytes = plain_password.encode('utf-8')
            # Truncate if longer than 72 bytes (bcrypt limit)
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            # Hash might be string or bytes - handle both
            if isinstance(hashed_password, str):
                hash_bytes = hashed_password.encode('utf-8')
            else:
                hash_bytes = hashed_password
            # Verify password
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            # Log error for debugging
            import logging
            logging.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(password: str) -> str:
        """Hash a password using bcrypt directly"""
        # Encode password to bytes
        password_bytes = password.encode('utf-8')
        # Truncate if longer than 72 bytes (bcrypt limit)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
except ImportError:
    # Fallback to passlib if bcrypt not available
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[UUID]:
    """Extract user ID from token"""
    payload = decode_token(token)
    if payload:
        return UUID(payload.get("sub"))
    return None

