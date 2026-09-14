from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.domain.Users.schemas import (
    CustomerSignupRequest,
    LoginRequest,
    MessageResponse,
    TokenResponse,
    UserResponse,
    UserRole
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password
)
from app.core.config import settings
from app.repositarys.user_repository import user_repository


class AuthService:
    async def signup_customer(self, data: CustomerSignupRequest) -> MessageResponse:
        """
        Registers a new CUSTOMER user.
        Validates uniqueness of email, username, and phone_number.
        Hashes password securely with bcrypt.
        Returns a success message without user data.
        """
      
        conflicts = await user_repository.check_conflicts(
            email=data.email,
            username=data.username,
            phone_number=data.phone_number
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="; ".join(conflicts)
            )

       
        hashed_pwd = hash_password(data.password)

       
        user_doc: Dict[str, Any] = {
            "first_name": data.first_name.strip(),
            "last_name": data.last_name.strip(),
            "email": data.email.strip().lower(),
            "username": data.username.strip().lower(),
            "phone_number": data.phone_number.strip(),
            "password_hash": hashed_pwd,
            "role": UserRole.CUSTOMER.value,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        try:
            await user_repository.create_user(user_doc)
        except DuplicateKeyError as e:
            errmsg = str(e)
            if "email" in errmsg:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
            elif "username" in errmsg:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
            elif "phone" in errmsg:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already registered")
            else:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with these details already exists")

        return MessageResponse(message="User registered successfully")

    async def authenticate_user(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticates an ADMIN or CUSTOMER using email + password.
        Returns a JWT token and success message without exposing user data.
        """
        user = await user_repository.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(data.password, user.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_payload = {
            "sub": user["id"],
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }

        token = create_access_token(data=token_payload)

        return TokenResponse(
            message="Login successfully",
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )


auth_service = AuthService()
