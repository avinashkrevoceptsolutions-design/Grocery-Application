from fastapi import APIRouter, Depends, status, HTTPException
from app.domain.Users.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordResponse
)
from app.services.auth_service import auth_service
from app.services.email_service import email_service
from app.core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_create: UserCreate):
    """Register a new user"""
    user = await auth_service.register_user(
        email=user_create.email,
        username=user_create.username,
        password=user_create.password,
        phone_number=user_create.phone_number,
        role=user_create.role.value
    )
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        username=user["username"],
        phone_number=user.get("phone_number"),
        role=user["role"],
        created_at=user["created_at"],
        updated_at=user["updated_at"]
    )


@router.post("/login")
async def login(user_login: UserLogin):
    """Authenticate user and return access token"""
    user, access_token = await auth_service.authenticate_user(
        email=user_login.email,
        password=user_login.password
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "role": user["role"]
        }
    }


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        phone_number=current_user.get("phone_number"),
        role=current_user["role"],
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"]
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset email"""
    result = await auth_service.request_password_reset(email=request.email)
    
    # Try to send reset email if user exists (don't reveal existence)
    try:
        await email_service.send_password_reset_email(email=request.email)
    except Exception as e:
        logger.error(f"Failed to send password reset email to {request.email}: {str(e)}")
        # Still return success to avoid revealing if email exists
    
    return ForgotPasswordResponse(
        message=result["message"],
        email=result["email"]
    )


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest):
    """Reset password with valid reset token"""
    result = await auth_service.reset_password(
        token=request.token,
        new_password=request.new_password
    )
    return ResetPasswordResponse(
        message=result["message"],
        success=result["success"]
    )