import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.repositarys.user_repository import user_repository
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.user_repository = user_repository

    async def register_user(self, email: str, username: str, password: str, phone_number: Optional[str] = None, role: str = "customer"):
        """Register a new user"""
        # Check if user exists
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        existing_username = await self.user_repository.get_by_username(username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = await self.user_repository.create_user(
            email=email,
            username=username,
            password_hash=password_hash,
            phone_number=phone_number,
            role=role
        )

        logger.info(f"User registered: {email}")
        return user

    async def authenticate_user(self, email: str, password: str) -> Tuple[dict, str]:
        """Authenticate user and return user data with access token"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        access_token = create_access_token(data={"sub": str(user["_id"]), "email": user["email"], "role": user["role"]})
        logger.info(f"User authenticated: {email}")
        return user, access_token

    async def request_password_reset(self, email: str) -> dict:
        """Generate password reset token and send reset email"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            # Don't reveal if email exists for security
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return {
                "message": "If an account exists with this email, a password reset link has been sent.",
                "email": email
            }

        # Generate reset token (15 minute expiry)
        reset_token = self._create_reset_token(user_id=str(user["_id"]), email=user["email"])
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Update user with reset token and expiry
        await self.user_repository.update_reset_token(
            user_id=str(user["_id"]),
            reset_token=reset_token,
            expires_at=expires_at
        )

        logger.info(f"Password reset token generated for: {email}")
        return {
            "message": "If an account exists with this email, a password reset link has been sent.",
            "email": email
        }

    async def reset_password(self, token: str, new_password: str) -> dict:
        """Reset user password with valid reset token"""
        try:
            # Validate and decode reset token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            email = payload.get("email")
            token_type = payload.get("type")

            if token_type != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )

            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token"
                )

        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired password reset token used")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired. Please request a new one."
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid password reset token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or malformed token"
            )

        # Get user and verify token matches
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user["email"] != email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token email does not match user email"
            )

        # Verify token matches stored token and hasn't expired
        if user.get("password_reset_token") != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already used token"
            )

        if user.get("password_reset_expires") and user["password_reset_expires"] < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired"
            )

        # Hash new password
        password_hash = hash_password(new_password)

        # Update password and clear reset token
        updated_user = await self.user_repository.update_password(
            user_id=user_id,
            password_hash=password_hash
        )

        logger.info(f"Password reset successful for: {email}")
        return {
            "message": "Password has been reset successfully. You can now login with your new password.",
            "success": True
        }

    def _create_reset_token(self, user_id: str, email: str) -> str:
        """Create a password reset JWT token with 15 minute expiry"""
        expires = datetime.utcnow() + timedelta(minutes=15)
        payload = {
            "sub": user_id,
            "email": email,
            "type": "password_reset",
            "exp": expires,
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return token


auth_service = AuthService()