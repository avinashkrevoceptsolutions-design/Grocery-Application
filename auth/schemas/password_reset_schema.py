from pydantic import BaseModel, EmailStr, Field, validator
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
    """Schema for password reset request."""
    token: str = Field(..., min_length=20, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    class Config:
        schema_extra = {
            "example": {
                "token": "secure_token_here",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            }
        }


class ValidateResetTokenRequest(BaseModel):
    """Schema for token validation request."""
    token: str = Field(..., min_length=20, description="Password reset token")

    class Config:
        schema_extra = {
            "example": {
                "token": "secure_token_here"
            }
        }


class ValidateResetTokenResponse(BaseModel):
    """Schema for token validation response."""
    valid: bool = Field(..., description="Whether token is valid")
    message: str = Field(..., description="Validation message")
    email: Optional[str] = Field(None, description="Associated email if valid")

    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "message": "Token is valid",
                "email": "user@example.com"
            }
        }


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    success: bool = Field(..., description="Whether reset was successful")
    message: str = Field(..., description="Response message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Password has been reset successfully"
            }
        }
