from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


class CustomerSignupRequest(BaseModel):
    first_name: str = Field(...,min_length=1, max_length=50, description="Customer First Name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Customer Last Name")
    email: EmailStr = Field(..., description="Unique Email Address")
    username: str = Field(..., min_length=3, max_length=30, description="Unique Username")
    phone_number: str = Field(..., min_length=7, max_length=20, description="Unique Phone Number")
    password: str = Field(..., min_length=6, max_length=128, description="Password")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered Email Address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    username: str
    phone_number: str
    role: UserRole
    created_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message", examples=["User registered successfully"])


class TokenResponse(BaseModel):
    message: str = Field(default="Login successfully", description="Status message", examples=["Login successfully"])
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    user_id: str
    username: str
    email: str
    role: UserRole
    exp: Optional[int] = None