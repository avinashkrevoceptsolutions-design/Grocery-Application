from typing import Any, Dict
from fastapi import APIRouter, Depends, status, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
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


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User by ID"
)
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserResponse:
    """
    Retrieve a user by their MongoDB ObjectId.
    
    Args:
        user_id: MongoDB ObjectId as a string (24 hex characters)
        current_user: Current authenticated user (required for authorization)
    
    Returns:
        UserResponse: User data if found
    
    Raises:
        HTTPException: 400 if user_id is not a valid MongoDB ObjectId
        HTTPException: 404 if user is not found
    """
    try:
        # Validate that user_id is a valid MongoDB ObjectId
        object_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format: {user_id}"
        )
    
    # Retrieve user from database
    user = await auth_service.get_user_by_id(object_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"404 Not Found - User not found - user_id={user_id}"
        )
    
    return UserResponse(**user)
