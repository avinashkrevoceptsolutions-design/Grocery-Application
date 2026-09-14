from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.domain.Users.schemas import UserRole
from app.domain.Inventory.schemas import (
    InventoryAdjustmentRequest,
    InventoryAdjustmentResponse,
    InventoryAdjustmentSuccessResponse,
    InventoryAddSuccessResponse,
    InventoryCreateRequest,
    InventoryMessageResponse,
    InventoryResponse,
    InventoryUpdateRequest,
    InventoryUpdateResponse
)
from app.core.dependencies import require_admin, require_inventory_access
from app.services.inventory_service import inventory_service

router = APIRouter(tags=["Inventory Management"])

@router.get(
    "/inventory",
    response_model=List[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Inventory Items"
)
async def list_inventory(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    search: Optional[str] = Query(None, description="Search term for item name"),
    status: Optional[str] = Query(None, description="Filter by status (IN_STOCK / OUT_OF_STOCK)"),
    current_user: Dict[str, Any] = Depends(require_inventory_access),
):
    return await inventory_service.list_inventory(
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status
    )


@router.get(
    "/inventory/{id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Inventory Item Details"
)
async def get_inventory_item(
    id: str,
    current_user: Dict[str, Any] = Depends(require_inventory_access),
):
    return await inventory_service.get_inventory_item(item_id=id)



@router.post(
    "/admin/inventory",
    response_model=InventoryAddSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Inventory Item (Admin Only)"
)
async def add_inventory(
    data: InventoryCreateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.add_inventory(data=data, admin_user=admin_user)


@router.get(
    "/admin/inventory",
    response_model=List[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Inventory Items for Admin (Admin Only)"
)
async def admin_list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.list_inventory(
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status
    )


@router.get(
    "/admin/inventory/adjustments",
    response_model=List[InventoryAdjustmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Inventory Adjustments History (Admin Only)"
)
async def get_all_adjustments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.get_adjustment_history(
        inventory_id=None,
        skip=skip,
        limit=limit
    )


@router.get(
    "/admin/inventory/{id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Inventory Item (Admin Only)"
)
async def admin_get_inventory(
    id: str,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.get_inventory_item(item_id=id)


@router.put(
    "/admin/inventory/{id}",
    response_model=InventoryMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit Inventory Item (Admin Only)"
)
async def edit_inventory(
    id: str,
    data: InventoryUpdateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    await inventory_service.edit_inventory(
        item_id=id,
        data=data,
        admin_user=admin_user
    )
    return {"message": "Item updated successfully"}


@router.delete(
    "/admin/inventory/{id}",
    response_model=InventoryMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Inventory Item (Admin Only)"
)
async def delete_inventory(
    id: str,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.delete_inventory(item_id=id, admin_user=admin_user)




@router.post(
    "/admin/inventory/{id}/adjust",
    response_model=InventoryAdjustmentSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Adjust Inventory Quantity (Admin Only)"
)
async def adjust_inventory(
    id: str,
    data: InventoryAdjustmentRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.adjust_inventory(
        item_id=id,
        data=data,
        admin_user=admin_user
    )


@router.get(
    "/admin/inventory/{id}/adjustments",
    response_model=List[InventoryAdjustmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Item Adjustment History (Admin Only)"
)
async def get_item_adjustments(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    return await inventory_service.get_adjustment_history(
        inventory_id=id,
        skip=skip,
        limit=limit
    )
