from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from app.domain.Users.schemas import (
    CustomerSignupRequest,
    LoginRequest,
    MessageResponse,
    TokenResponse,
    UserResponse
)
from app.core.dependencies import get_current_user
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Customer Signup"
)
@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Customer Register",
    include_in_schema=False
)
async def signup(signup_data: CustomerSignupRequest):
    return await auth_service.signup_customer(signup_data)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login (Admin & Customer)"
)
async def login(login_data: LoginRequest):
    return await auth_service.authenticate_user(login_data)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current User Profile"
)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(**current_user)
