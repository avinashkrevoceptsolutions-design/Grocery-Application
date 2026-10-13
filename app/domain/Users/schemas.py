from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    phone_number: Optional[str] = None
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    password_hash: str
    phone_number: Optional[str] = None
    role: UserRole
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordResponse(BaseModel):
    message: str
    email: str


class ResetPasswordResponse(BaseModel):
    message: str
    success: bool