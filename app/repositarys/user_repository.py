from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.database.connection import db
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection: AsyncIOMotorCollection = db["users"]

    async def create_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        phone_number: Optional[str] = None,
        role: str = "customer"
    ) -> dict:
        """Create a new user"""
        user = {
            "email": email,
            "username": username,
            "password_hash": password_hash,
            "phone_number": phone_number,
            "role": role,
            "password_reset_token": None,
            "password_reset_expires": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(user)
        user["_id"] = result.inserted_id
        return user

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        from bson import ObjectId
        try:
            return await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {str(e)}")
            return None

    async def get_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        return await self.collection.find_one({"email": email})

    async def get_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        return await self.collection.find_one({"username": username})

    async def get_by_phone_number(self, phone_number: str) -> Optional[dict]:
        """Get user by phone number"""
        return await self.collection.find_one({"phone_number": phone_number})

    async def update_reset_token(
        self,
        user_id: str,
        reset_token: str,
        expires_at: datetime
    ) -> dict:
        """Update user's password reset token and expiry"""
        from bson import ObjectId
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_reset_token": reset_token,
                        "password_reset_expires": expires_at,
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Error updating reset token for user {user_id}: {str(e)}")
            raise

    async def update_password(
        self,
        user_id: str,
        password_hash: str
    ) -> dict:
        """Update user password and clear reset token"""
        from bson import ObjectId
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "password_reset_token": None,
                        "password_reset_expires": None,
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )
            logger.info(f"Password updated for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {str(e)}")
            raise

    async def list_all(self) -> List[dict]:
        """List all users"""
        return await self.collection.find().to_list(length=None)

    async def delete_by_id(self, user_id: str) -> bool:
        """Delete user by ID"""
        from bson import ObjectId
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False


user_repository = UserRepository(db)