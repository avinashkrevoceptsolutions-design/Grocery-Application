from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status

from app.domain.Order.schemas import OrderCreateResponse, OrderResponse
from app.services.order_service import order_service
from app.core.dependencies import require_customer

router = APIRouter(prefix="/orders", tags=["Order Management"])

@router.post(
    "",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place Order"
)
async def place_order(
    customer: Dict[str, Any] = Depends(require_customer)
):
    return await order_service.place_order(customer=customer)

@router.get(
    "",
    response_model=List[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="View Previous Orders"
)
async def get_previous_orders(
    customer: Dict[str, Any] = Depends(require_customer)
):
    return await order_service.get_previous_orders(customer_id=customer["id"])
