"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from shared.database.base import get_db
from app.models import LoginRequest, RegisterRequest, RefreshTokenRequest, TokenResponse, CurrentUserResponse
from app.services import AuthService, UserService
from app.dependencies import get_current_user
from app.utils import decode_token
from shared.common.errors import handle_exception

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    try:
        return AuthService.login(db, login_data)
    except Exception as e:
        raise handle_exception(e)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new user"""
    try:
        # Register user
        user = AuthService.register(db, register_data)
        
        # Auto-login after registration
        login_data = LoginRequest(
            email=register_data.email,
            password=register_data.password,  # In production, this should be handled differently
            organization_id=register_data.organization_id
        )
        return AuthService.login(db, login_data)
    except Exception as e:
        raise handle_exception(e)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    try:
        return AuthService.refresh_token(db, refresh_data.refresh_token)
    except Exception as e:
        raise handle_exception(e)


@router.post("/logout")
def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Logout user"""
    try:
        AuthService.logout(db, refresh_data.refresh_token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise handle_exception(e)


@router.get("/verify")
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify token endpoint for API gateway"""
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(
    user_id_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    try:
        user_id, organization_id = user_id_org
        return UserService.get_current_user(db, user_id, organization_id)
    except Exception as e:
        raise handle_exception(e)
