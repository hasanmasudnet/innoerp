"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from shared.database.base import get_db
from app.models import LoginRequest, RegisterRequest, RefreshTokenRequest, TokenResponse, CurrentUserResponse
from app.services import AuthService, UserService
from app.dependencies import get_current_user
from app.utils import decode_token
from shared.common.errors import handle_exception
from shared.common.logging import get_logger, log_entry_exit

app_name = "auth-service"
logger = get_logger(__name__, app_name=app_name)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
@log_entry_exit(app_name=app_name)
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    try:
        logger.info(
            f"Login attempt for email: {login_data.email}",
            "login",
            "POST",
            login_data.email,
            app_name,
            extra={"organization_id": str(login_data.organization_id) if login_data.organization_id else None}
        )
        result = AuthService.login(db, login_data)
        logger.info(
            "Login successful",
            "login",
            "POST",
            login_data.email,
            app_name
        )
        return result
    except Exception as e:
        logger.error(
            f"Login failed: {str(e)}",
            "login",
            "POST",
            login_data.email,
            app_name,
            extra={"error": str(e)}
        )
        raise handle_exception(e)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@log_entry_exit(app_name=app_name)
def register(
    request: Request,
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new user"""
    try:
        logger.info(
            f"Registration attempt for email: {register_data.email}",
            "register",
            "POST",
            register_data.email,
            app_name,
            extra={"organization_id": str(register_data.organization_id) if register_data.organization_id else None}
        )
        # Register user
        user = AuthService.register(db, register_data)
        
        # Auto-login after registration
        login_data = LoginRequest(
            email=register_data.email,
            password=register_data.password,  # In production, this should be handled differently
            organization_id=register_data.organization_id
        )
        result = AuthService.login(db, login_data)
        logger.info(
            "Registration successful",
            "register",
            "POST",
            register_data.email,
            app_name
        )
        return result
    except Exception as e:
        logger.error(
            f"Registration failed: {str(e)}",
            "register",
            "POST",
            register_data.email,
            app_name,
            extra={"error": str(e)}
        )
        raise handle_exception(e)


@router.post("/refresh", response_model=TokenResponse)
@log_entry_exit(app_name=app_name)
def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    try:
        logger.info(
            "Token refresh requested",
            "refresh_token",
            "POST",
            "",
            app_name
        )
        return AuthService.refresh_token(db, refresh_data.refresh_token)
    except Exception as e:
        logger.error(
            f"Token refresh failed: {str(e)}",
            "refresh_token",
            "POST",
            "",
            app_name,
            extra={"error": str(e)}
        )
        raise handle_exception(e)


@router.post("/logout")
@log_entry_exit(app_name=app_name)
def logout(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Logout user"""
    try:
        logger.info(
            "Logout requested",
            "logout",
            "POST",
            "",
            app_name
        )
        AuthService.logout(db, refresh_data.refresh_token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(
            f"Logout failed: {str(e)}",
            "logout",
            "POST",
            "",
            app_name,
            extra={"error": str(e)}
        )
        raise handle_exception(e)


@router.get("/verify")
@log_entry_exit(app_name=app_name)
def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify token endpoint for API gateway"""
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            logger.warning(
                "Token verification failed: invalid token type",
                "verify_token",
                "GET",
                "",
                app_name
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Token verification error: {str(e)}",
            "verify_token",
            "GET",
            "",
            app_name,
            extra={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/me", response_model=CurrentUserResponse)
@log_entry_exit(app_name=app_name)
def get_current_user_info(
    request: Request,
    user_id_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    try:
        user_id, organization_id = user_id_org
        logger.info(
            f"Getting current user info for user_id: {user_id}",
            "get_current_user",
            "GET",
            str(user_id),
            app_name,
            extra={"organization_id": str(organization_id) if organization_id else None}
        )
        return UserService.get_current_user(db, user_id, organization_id)
    except Exception as e:
        logger.error(
            f"Failed to get current user: {str(e)}",
            "get_current_user",
            "GET",
            "",
            app_name,
            extra={"error": str(e)}
        )
        raise handle_exception(e)
