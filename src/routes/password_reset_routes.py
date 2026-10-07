from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.schemas.password_reset_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ValidateResetTokenRequest,
    PasswordResetResponse,
    ValidateTokenResponse
)
from src.services.password_reset_service import PasswordResetService
from src.utils.email_service import get_email_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["password-reset"]
)


@router.post(
    "/forgot-password",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset link to be sent to the user's email"
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    
    - **email**: User's email address
    
    Returns a success message regardless of whether the email exists (to prevent user enumeration).
    """
    try:
        email_service = get_email_service()
        password_reset_service = PasswordResetService(db, email_service)
        
        success, message, _ = await password_reset_service.generate_reset_token(request.email)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )
        
        return PasswordResetResponse(
            success=True,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in forgot_password endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset user password using a valid reset token"
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters with uppercase, lowercase, and numbers)
    - **confirm_password**: Confirmation of new password
    
    Returns success or error message.
    """
    try:
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match."
            )
        
        email_service = get_email_service()
        password_reset_service = PasswordResetService(db, email_service)
        
        success, message = await password_reset_service.reset_password(
            request.token,
            request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return PasswordResetResponse(
            success=True,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_password endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )


@router.post(
    "/validate-reset-token",
    response_model=ValidateTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate reset token",
    description="Validate if a password reset token is valid"
)
def validate_reset_token(
    request: ValidateResetTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a password reset token.
    
    - **token**: Password reset token to validate
    
    Returns validation status and user_id if valid.
    """
    try:
        email_service = get_email_service()
        password_reset_service = PasswordResetService(db, email_service)
        
        is_valid, message, user_id = password_reset_service.validate_reset_token(request.token)
        
        return ValidateTokenResponse(
            is_valid=is_valid,
            message=message,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error in validate_reset_token endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )
