
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.database.connection import get_database


class UserRepository:

    def _collection(self):
        return get_database()["users"]

    def _format_doc(self, doc):
        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_by_id(self, user_id: str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            return None

        doc = await self._collection().find_one({"_id": user_id})
        return self._format_doc(doc)

    async def get_by_email(self, email: str):
        email = email.strip().lower()

        doc = await self._collection().find_one({
            "email": email
        })

        return self._format_doc(doc)

    async def get_by_username(self, username: str):
        username = username.strip().lower()

        doc = await self._collection().find_one({
            "username": username
        })

        return self._format_doc(doc)

    async def get_by_phone(self, phone_number: str):
        phone_number = phone_number.strip()

        doc = await self._collection().find_one({
            "phone_number": phone_number
        })

        return self._format_doc(doc)

    async def get_by_identifier(self, identifier: str):
        identifier = identifier.strip().lower()

        doc = await self._collection().find_one({
            "$or": [
                {"email": identifier},
                {"username": identifier}
            ]
        })

        return self._format_doc(doc)

    async def check_conflicts(self,email: str,username: str,phone_number: str,exclude_id: Optional[str] = None) -> List[str]:

        conflicts = []

        email = email.strip().lower()
        username = username.strip().lower()
        phone_number = phone_number.strip()

        query = {}

        if exclude_id:
            try:
                query = {"_id": {"$ne": ObjectId(exclude_id)}}
            except Exception:
                pass

        if await self._collection().find_one({
            "email": email,
            **query
        }):
            conflicts.append("Email already registered")

        if await self._collection().find_one({
            "username": username,
            **query
        }):
            conflicts.append("Username already taken")

        if await self._collection().find_one({
            "phone_number": phone_number,
            **query
        }):
            conflicts.append("Phone number already registered")

        return conflicts

    async def create_user(self, user_dict: Dict[str, Any]):
        now = datetime.now(timezone.utc)

        user_dict["created_at"] = now
        user_dict["updated_at"] = now

        result = await self._collection().insert_one(user_dict)

        user_dict["id"] = str(result.inserted_id)
        user_dict.pop("_id", None)

        return user_dict

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50
    ):
        cursor = (
            self._collection()
            .find()
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        users = []

        async for doc in cursor:
            users.append(self._format_doc(doc))

        return users


user_repository = UserRepository()