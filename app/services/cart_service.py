
from fastapi import HTTPException, status

from app.domain.Cart.schemas import (CartItemAddRequest,CartItemUpdateRequest,CartResponse,)
from app.repositarys.cart_repository import cart_repository
from app.repositarys.inventory_repository import inventory_repository


class CartService:

    async def get_cart(self, customer_id: str) -> CartResponse:
        cart = await cart_repository.get_cart_by_customer_id(customer_id)

        if not cart:
            return CartResponse(
                customer_id=customer_id,
                items=[],
                cart_total=0,
            )

        return CartResponse(**cart)

    async def add_item_to_cart(self,customer_id: str,data: CartItemAddRequest,) -> CartResponse:

        inventory = await inventory_repository.get_by_id(data.inventory_id)

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory item not found.",
            )

        available = inventory.get("quantity_available", 0)

        if data.quantity > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available} items are available.",
            )

        cart = await cart_repository.get_cart_by_customer_id(customer_id)

        items = cart.get("items", []) if cart else []

        existing_item = next(
            (item for item in items if item["inventory_id"] == data.inventory_id),
            None,
        )

        if existing_item:
            quantity = existing_item["quantity"] + data.quantity

            if quantity > available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available} items are available.",
                )

            existing_item["quantity"] = quantity
            existing_item["total_price"] = round(quantity * existing_item["price"], 2)

        else:
            price = inventory["price"]

            items.append(
                {
                    "inventory_id": data.inventory_id,
                    "name": inventory["name"],
                    "price": price,
                    "quantity": data.quantity,
                    "image": inventory.get("image"),
                    "total_price": round(price * data.quantity, 2),
                }
            )

        cart_total = round(
            sum(item["total_price"] for item in items), 2
        )

        cart_data = {
            "customer_id": customer_id,
            "items": items,
            "cart_total": cart_total,
        }

        updated_cart = await cart_repository.update_cart(
            customer_id,
            cart_data,
        )

        return CartResponse(**updated_cart)

    async def update_item_quantity(self,customer_id: str,inventory_id: str,data: CartItemUpdateRequest,) -> CartResponse:

        cart = await cart_repository.get_cart_by_customer_id(customer_id)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found.",
            )

        items = cart.get("items", [])

        existing_item = next(
            (item for item in items if item["inventory_id"] == inventory_id),
            None,
        )

        if not existing_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Item not found in cart.",)

        inventory = await inventory_repository.get_by_id(inventory_id)

        if inventory:
            available = inventory.get("quantity_available", 0)

            if data.quantity > available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not enough stock.",
                )

            existing_item["name"] = inventory["name"]
            existing_item["price"] = inventory["price"]
            existing_item["image"] = inventory.get("image")

        existing_item["quantity"] = data.quantity
        existing_item["total_price"] = round(
            existing_item["quantity"] * existing_item["price"],
            2,
        )

        cart_total = round(
            sum(item["total_price"] for item in items), 2
        )

        cart_data = {
            "customer_id": customer_id,
            "items": items,
            "cart_total": cart_total,
        }

        updated_cart = await cart_repository.update_cart(
            customer_id,
            cart_data,
        )

        return CartResponse(**updated_cart)

    async def remove_item( self,   customer_id: str,   inventory_id: str,  ) -> CartResponse:

        cart = await cart_repository.get_cart_by_customer_id(customer_id)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found.",
            )

        items = cart.get("items", [])

        new_items = [
            item for item in items
            if item["inventory_id"] != inventory_id
        ]

        if len(new_items) == len(items):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart.",
            )

        cart_total = round(
            sum(item["total_price"] for item in new_items), 2
        )

        cart_data = {
            "customer_id": customer_id,
            "items": new_items,
            "cart_total": cart_total,
        }

        updated_cart = await cart_repository.update_cart(
            customer_id,
            cart_data,
        )

        return CartResponse(**updated_cart)

    async def clear_cart(self, customer_id: str) -> None:
        await cart_repository.clear_cart(customer_id)


cart_service = CartService()