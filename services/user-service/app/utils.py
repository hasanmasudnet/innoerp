"""
Utility functions for user service
"""
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm = "HS256"
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return {}

