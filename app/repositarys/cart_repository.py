
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.database.connection import get_database


class CartRepository:

    def _cart_collection(self):
        return get_database()["carts"]

    def _format_doc(self,doc: Optional[Dict[str, Any]],) -> Optional[Dict[str, Any]]:

        if not doc:
            return None

        doc = dict(doc)

        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]

        return doc

    async def get_cart_by_customer_id(self,customer_id: str,) -> Optional[Dict[str, Any]]:

        doc = await self._cart_collection().find_one(
            {"customer_id": customer_id}
        )

        return self._format_doc(doc)

    async def update_cart(self,customer_id: str,cart_data: Dict[str, Any],) -> Dict[str, Any]:

        now = datetime.now(timezone.utc)
   
        cart_data["updated_at"] = now

        updated = await self._cart_collection().find_one_and_update(
            {"customer_id": customer_id},
            {
                "$set": cart_data,
                "$setOnInsert": {
                    "created_at": now
                },
            },
            upsert=True,
            return_document=True,
        )

        return self._format_doc(updated)

    async def clear_cart(self, customer_id: str) -> bool:

        result = await self._cart_collection().delete_one(
            {"customer_id": customer_id}
        )

        return result.deleted_count > 0


cart_repository = CartRepository()