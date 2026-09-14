
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.database.connection import get_database


class InventoryRepository:

    def _inventory_collection(self):
        return get_database()["inventory"]

    def _adjustments_collection(self):
        return get_database()["inventory_adjustments"]

    def _format_doc(self,doc: Optional[Dict[str, Any]],) -> Optional[Dict[str, Any]]:

        if not doc:
            return None

        doc = dict(doc)

        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]

        return doc

    async def get_by_id(self,item_id: str, ) -> Optional[Dict[str, Any]]:

        try:
            object_id = ObjectId(item_id)
        except Exception:
            return None

        doc = await self._inventory_collection().find_one({"_id": object_id})

        return self._format_doc(doc)

    async def get_by_name(self,name: str,) -> Optional[Dict[str, Any]]:

        query = {
            "name": {
                "$regex": f"^{name.strip()}$",
                "$options": "i",
            }
        }

        doc = await self._inventory_collection().find_one(query)

        return self._format_doc(doc)

    async def create_item(self,item_dict: Dict[str, Any],) -> Dict[str, Any]:

        now = datetime.now(timezone.utc)

        item_dict["created_at"] = item_dict.get("created_at", now)
        item_dict["updated_at"] = now

        result = await self._inventory_collection().insert_one(item_dict)

        item_dict["id"] = str(result.inserted_id)

        return item_dict

    async def update_item(self,item_id: str,update_dict: Dict[str, Any],) -> Optional[Dict[str, Any]]:

        try:
            object_id = ObjectId(item_id)
        except Exception:
            return None

        update_dict["updated_at"] = datetime.now(timezone.utc)

        updated = await self._inventory_collection().find_one_and_update(
            {"_id": object_id},
            {"$set": update_dict},
            return_document=True,
        )

        return self._format_doc(updated)

    async def delete_item(self, item_id: str) -> bool:

        try:
            object_id = ObjectId(item_id)
        except Exception:
            return False

        result = await self._inventory_collection().delete_one(
            {"_id": object_id}
        )

        return result.deleted_count > 0

    async def list_items(self,skip: int = 0,limit: int = 50,search: Optional[str] = None,status: Optional[str] = None,) -> List[Dict[str, Any]]:

        query: Dict[str, Any] = {}

        if search:
            query["name"] = {
                "$regex": search.strip(),
                "$options": "i",
            }

        if status:
            query["status"] = status.strip().upper()

        cursor = (self._inventory_collection().find(query).sort("created_at", -1).skip(skip).limit(limit))

        items = []

        async for doc in cursor:
            item = self._format_doc(doc)

            if item:
                items.append(item)

        return items

    async def list_all_items(self) -> List[Dict[str, Any]]:
        cursor = self._inventory_collection().find({}).sort("created_at", -1)
        items = []

        async for doc in cursor:
            item = self._format_doc(doc)
            if item:
                items.append(item)

        return items

    async def count_items(self,search: Optional[str] = None,status: Optional[str] = None,) -> int:

        query: Dict[str, Any] = {}

        if search:
            query["name"] = {
                "$regex": search.strip(),
                "$options": "i",
            }

        if status:
            query["status"] = status.strip().upper()

        return await self._inventory_collection().count_documents(query)

    async def count_quantity_less_than(self, quantity: int) -> int:
        return await self._inventory_collection().count_documents({
            "quantity_available": {"$lt": quantity}
        })

    async def list_items_with_quantity_less_than(
        self,
        quantity: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        cursor = (
            self._inventory_collection()
            .find({"quantity_available": {"$lt": quantity}})
            .sort("quantity_available", 1)
            .limit(limit)
        )
        items = []

        async for doc in cursor:
            item = self._format_doc(doc)
            if item:
                items.append(item)

        return items

    async def list_out_of_stock_items(self) -> List[Dict[str, Any]]:
        cursor = self._inventory_collection().find({
            "$or": [
                {"quantity_available": 0},
                {"status": "OUT_OF_STOCK"},
            ]
        }).sort("name", 1)
        items = []

        async for doc in cursor:
            item = self._format_doc(doc)
            if item:
                items.append(item)

        return items

    async def get_item_with_highest_quantity(self) -> Optional[Dict[str, Any]]:
        doc = await self._inventory_collection().find_one(
            {},
            sort=[("quantity_available", -1), ("name", 1)],
        )
        return self._format_doc(doc)

    async def create_adjustment(self,adj_dict: Dict[str, Any],) -> Dict[str, Any]:

        if "created_at" not in adj_dict:
            adj_dict["created_at"] = datetime.now(timezone.utc)

        result = await self._adjustments_collection().insert_one(adj_dict)

        adj_dict["id"] = str(result.inserted_id)

        return adj_dict

    async def list_adjustments(self,inventory_id: Optional[str] = None,skip: int = 0,limit: int = 50,) -> List[Dict[str, Any]]:

        query: Dict[str, Any] = {}

        if inventory_id:
            query["inventory_id"] = inventory_id

        cursor = (self._adjustments_collection().find(query).sort("created_at", -1).skip(skip).limit(limit))

        records = []

        async for doc in cursor:
            record = self._format_doc(doc)

            if record:
                records.append(record)

        return records


inventory_repository = InventoryRepository()