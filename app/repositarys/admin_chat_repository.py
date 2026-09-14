from datetime import datetime, timezone
from typing import Any, Dict, List

from app.database.connection import get_database


class AdminChatRepository:

    def _messages_collection(self):
        return get_database()["admin_chat_messages"]

    async def list_messages(  self, admin_id: str, conversation_id: str,  limit: int = 20, ) -> List[Dict[str, Any]]:
        cursor = (
            self._messages_collection()
            .find({
                "admin_id": admin_id,
                "conversation_id": conversation_id,
            })
            .sort("created_at", -1)
            .limit(limit)
        )
        messages = []

        async for message in cursor:
            messages.append(message)

        messages.reverse()
        return messages

    async def get_latest_conversation_id(self, admin_id: str) -> str | None:
        message = await self._messages_collection().find_one(
            {"admin_id": admin_id},
            sort=[("created_at", -1)],
        )
        return message.get("conversation_id") if message else None

    async def add_message(  self,  admin_id: str,  conversation_id: str,  role: str,   content: str, ) -> None:
        await self._messages_collection().insert_one({
            "admin_id": admin_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        })


admin_chat_repository = AdminChatRepository()