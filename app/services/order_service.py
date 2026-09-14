
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.domain.Inventory.schemas import AdjustmentType, ItemStatus
from app.domain.Order.schemas import OrderCreateResponse, OrderResponse, OrderStatus
from app.repositarys.cart_repository import cart_repository
from app.repositarys.inventory_repository import inventory_repository
from app.repositarys.order_repository import order_repository
from app.services.email_service import email_service
import logging


logger = logging.getLogger(__name__)


class OrderService:

    async def place_order(self, customer: Dict[str, Any]) -> OrderCreateResponse:
        customer_id = customer["id"]

        cart = await cart_repository.get_cart_by_customer_id(customer_id)

        if not cart or not cart.get("items"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your cart is empty.",
            )

        items = cart["items"]
        inventory_items = {}

        for item in items:
            inventory = await inventory_repository.get_by_id(
                item["inventory_id"]
            )

            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{item['name']}' is not available.",
                )

            available = inventory.get("quantity_available", 0)

            if item["quantity"] > available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for '{item['name']}'.",
                )

            inventory_items[item["inventory_id"]] = inventory

        customer_name = ( customer.get("email")or customer.get("username")or str(customer_id) )

        for item in items:
            inventory_id = item["inventory_id"]
            inventory = inventory_items[inventory_id]

            old_quantity = inventory.get("quantity_available", 0)
            new_quantity = old_quantity - item["quantity"]

            item_status = (
                ItemStatus.OUT_OF_STOCK.value
                if new_quantity == 0
                else ItemStatus.IN_STOCK.value
            )

            await inventory_repository.update_item(
                inventory_id,
                {
                    "quantity_available": new_quantity,
                    "status": item_status,
                },
            )

            await inventory_repository.create_adjustment(
                {
                    "inventory_id": inventory_id,
                    "adjustment_type": AdjustmentType.REMOVE.value,
                    "quantity": item["quantity"],
                    "reason": f"Order placed by {customer_name}",
                    "previous_quantity": old_quantity,
                    "new_quantity": new_quantity,
                    "created_by": customer_name,
                    "created_at": datetime.now(timezone.utc),
                }
            )

        order = {
            "customer_id": customer_id,
            "items": items,
            "total_amount": cart["cart_total"],
            "status": OrderStatus.COMPLETED.value,
            "created_at": datetime.now(timezone.utc),
        }

        created_order = await order_repository.create_order(order)

        await cart_repository.clear_cart(customer_id)

        try:
            await email_service.send_order_notifications(customer, created_order)
        except Exception:
            logger.exception("Failed to send order notification emails for %s", created_order.get("id"))

        return OrderCreateResponse(
            order=OrderResponse(**created_order)
        )

    async def get_previous_orders(self,customer_id: str,) -> List[OrderResponse]:

        orders = await order_repository.get_orders_by_customer_id(customer_id)

        return [OrderResponse(**order) for order in orders]


order_service = OrderService()