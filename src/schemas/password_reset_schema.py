from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr = Field(..., description="User email address")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    token: str = Field(..., min_length=32, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123"
            }
        }


class ValidateResetTokenRequest(BaseModel):
    """Schema for validating reset token."""
    token: str = Field(..., min_length=32, description="Password reset token")

    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr"
            }
        }


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    success: bool
    message: str

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Password has been reset successfully."
            }
        }


class ValidateTokenResponse(BaseModel):
    """Schema for token validation response."""
    is_valid: bool
    message: str
    user_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "message": "Token is valid.",
                "user_id": "user-id-123"
            }
        }
