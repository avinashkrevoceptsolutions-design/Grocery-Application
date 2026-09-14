
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.domain.Inventory.schemas import (
    AdjustmentType,
    InventoryAdjustmentRequest,
    InventoryAdjustmentResponse,
    InventoryAdjustmentSuccessResponse,
    InventoryAddSuccessResponse,
    InventoryCreateRequest,
    InventoryResponse,
    InventoryUpdateRequest,
    InventoryUpdateResponse,
    ItemStatus,
)
from app.repositarys.inventory_repository import inventory_repository
from app.services.inventory_rag_service import inventory_rag_service


class InventoryService:

    async def add_inventory(self,data: InventoryCreateRequest,admin_user: Dict[str, Any],) -> InventoryAddSuccessResponse:

        existing = await inventory_repository.get_by_name(data.name)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Inventory item with name '{data.name.strip()}' already exists",
            )

        item_status = (
            ItemStatus.OUT_OF_STOCK.value
            if data.quantity_available == 0
            else ItemStatus.IN_STOCK.value
        )

        item = {
            "name": data.name.strip(),
            "price": round(float(data.price), 2),
            "quantity_available": int(data.quantity_available),
            "image": data.image.strip(),
            "status": item_status,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        created_item = await inventory_repository.create_item(item)
        await inventory_rag_service.upsert_item(created_item)

        if data.quantity_available > 0:
            admin_id = (
                admin_user.get("email")
                or admin_user.get("username")
                or str(admin_user.get("id", "admin"))
            )

            await inventory_repository.create_adjustment(
                {
                    "inventory_id": created_item["id"],
                    "adjustment_type": AdjustmentType.ADD.value,
                    "quantity": data.quantity_available,
                    "reason": "Initial stock",
                    "previous_quantity": 0,
                    "new_quantity": data.quantity_available,
                    "created_by": admin_id,
                    "created_at": datetime.now(timezone.utc),
                }
            )

        return InventoryAddSuccessResponse(
            message="Item successfully added to inventory",
            data=InventoryResponse(**created_item)
        )

    async def edit_inventory(self, item_id: str, data: InventoryUpdateRequest, admin_user: Dict[str, Any]) -> None:

        existing = await inventory_repository.get_by_id(item_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Id not found",
            )

        update_data = {}

        if data.name is not None:
            name = data.name.strip()

            if name.lower() != existing["name"].lower():
                duplicate = await inventory_repository.get_by_name(name)

                if duplicate and duplicate["id"] != item_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Inventory item with name '{name}' already exists",
                    )

            update_data["name"] = name

        if data.price is not None:
            update_data["price"] = round(float(data.price), 2)

        if data.image is not None:
            update_data["image"] = data.image.strip()

        if not update_data:
            return

        updated_item = await inventory_repository.update_item(item_id, update_data)
        if updated_item:
            await inventory_rag_service.upsert_item(updated_item)

        return

    async def delete_inventory(self,item_id: str,admin_user: Dict[str, Any],) -> Dict[str, str]:

        existing = await inventory_repository.get_by_id(item_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Id not found",
            )

        deleted = await inventory_repository.delete_item(item_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete inventory item",
            )

        await inventory_rag_service.delete_item(item_id)

        return {
            "message": f"Inventory item '{existing.get('name')}' deleted successfully"
        }

    async def get_inventory_item(self, item_id: str) -> InventoryResponse:

        item = await inventory_repository.get_by_id(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Id not found",
            )

        return InventoryResponse(**item)

    async def list_inventory(self,skip: int = 0,limit: int = 50,search: Optional[str] = None,status_filter: Optional[str] = None,) -> List[InventoryResponse]:

        items = await inventory_repository.list_items(
            skip=skip,
            limit=limit,
            search=search,
            status=status_filter,
        )

        return [InventoryResponse(**item) for item in items]

    async def count_items_with_quantity_less_than(self, quantity: int) -> int:
        return await inventory_repository.count_quantity_less_than(quantity)

    async def list_low_stock_items( self,  quantity: int,  limit: int = 100, ) -> List[InventoryResponse]:
        items = await inventory_repository.list_items_with_quantity_less_than(
            quantity=quantity,
            limit=limit,
        )
        return [InventoryResponse(**item) for item in items]

    async def list_out_of_stock_items(self) -> List[InventoryResponse]:
        items = await inventory_repository.list_out_of_stock_items()
        return [InventoryResponse(**item) for item in items]

    async def get_highest_quantity_item(self) -> Optional[InventoryResponse]:
        item = await inventory_repository.get_item_with_highest_quantity()
        return InventoryResponse(**item) if item else None

    async def adjust_inventory(self, item_id: str, data: InventoryAdjustmentRequest, admin_user: Dict[str, Any],) -> InventoryAdjustmentSuccessResponse:

        item = await inventory_repository.get_by_id(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Id not found",
            )

        old_quantity = int(item.get("quantity_available", 0))

        if data.adjustment_type == AdjustmentType.ADD:
            new_quantity = old_quantity + data.quantity

        elif data.adjustment_type == AdjustmentType.REMOVE:
            if data.quantity > old_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot remove {data.quantity} units. Current quantity is {old_quantity}.",
                )

            new_quantity = old_quantity - data.quantity

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid adjustment type: {data.adjustment_type}",
            )

        item_status = ( ItemStatus.OUT_OF_STOCK.value if new_quantity == 0 else ItemStatus.IN_STOCK.value)

        updated_item = await inventory_repository.update_item(
            item_id,
            {
                "quantity_available": new_quantity,
                "status": item_status,
            },
        )

        if updated_item:
            await inventory_rag_service.upsert_item(updated_item)

        admin_id = (
            admin_user.get("email")
            or admin_user.get("username")
            or str(admin_user.get("id", "admin"))
        )

        adjustment = {
            "inventory_id": item_id,
            "adjustment_type": data.adjustment_type.value,
            "quantity": data.quantity,
            "reason": data.reason.strip(),
            "previous_quantity": old_quantity,
            "new_quantity": new_quantity,
            "created_by": admin_id,
            "created_at": datetime.now(timezone.utc),
        }

        created_adjustment = await inventory_repository.create_adjustment(
            adjustment
        )

        return InventoryAdjustmentSuccessResponse(
            message=f"Inventory quantity updated. New quantity: {new_quantity}.",
            adjustment=InventoryAdjustmentResponse(**created_adjustment),
            inventory=InventoryResponse(**updated_item),
        )

    async def get_adjustment_history( self, inventory_id: Optional[str] = None, skip: int = 0, limit: int = 50,) -> List[InventoryAdjustmentResponse]:

        if inventory_id:
            item = await inventory_repository.get_by_id(inventory_id)

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Id not found",
                )

        records = await inventory_repository.list_adjustments( inventory_id=inventory_id, skip=skip, limit=limit,)

        return [InventoryAdjustmentResponse(**record) for record in records]


inventory_service = InventoryService()
