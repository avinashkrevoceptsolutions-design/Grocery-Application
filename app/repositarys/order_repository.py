
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.database.connection import get_database


class OrderRepository:

    def _order_collection(self):
        return get_database()["orders"]

    def _format_doc(
        self,
        doc: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:

        if not doc:
            return None

        doc = dict(doc)

        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]

        return doc

    async def create_order(self,order_dict: Dict[str, Any],) -> Dict[str, Any]:

        if "created_at" not in order_dict:
            order_dict["created_at"] = datetime.now(timezone.utc)

        result = await self._order_collection().insert_one(order_dict)

        order_dict["id"] = str(result.inserted_id)

        return order_dict

    async def get_orders_by_customer_id(self,customer_id: str,) -> List[Dict[str, Any]]:

        cursor = (self._order_collection().find({"customer_id": customer_id}).sort("created_at", -1))

        orders = []

        async for order in cursor:
            formatted_order = self._format_doc(order)

            if formatted_order:
                orders.append(formatted_order)

        return orders


order_repository = OrderRepository()