from typing import Any, Dict
from fastapi import APIRouter, Depends, status

from app.domain.Cart.schemas import CartItemAddRequest, CartItemUpdateRequest, CartResponse
from app.domain.Users.schemas import MessageResponse
from app.services.cart_service import cart_service
from app.core.dependencies import require_customer

router = APIRouter(prefix="/cart", tags=["Cart Management"])

@router.get(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="View Cart"
)
async def get_cart(
    customer: Dict[str, Any] = Depends(require_customer)
):
    return await cart_service.get_cart(customer_id=customer["id"])

@router.post(
    "/items",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Add Item to Cart"
)
async def add_item_to_cart(
    data: CartItemAddRequest,
    customer: Dict[str, Any] = Depends(require_customer)
):
    await cart_service.add_item_to_cart(customer_id=customer["id"], data=data)
    return {"message": "Item added to cart successfully"}

@router.put(
    "/items/{inventory_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Cart Item Quantity"
)
async def update_item_quantity(
    inventory_id: str,
    data: CartItemUpdateRequest,
    customer: Dict[str, Any] = Depends(require_customer)
):
    await cart_service.update_item_quantity(
        customer_id=customer["id"],
        inventory_id=inventory_id,
        data=data
    )
    return {"message": "Cart item updated successfully"}

@router.delete(
    "/items/{inventory_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove Item from Cart"
)
async def remove_item_from_cart(
    inventory_id: str,
    customer: Dict[str, Any] = Depends(require_customer)
):
    await cart_service.remove_item(customer_id=customer["id"], inventory_id=inventory_id)
    return {"message": "Item deleted from cart successfully"}
