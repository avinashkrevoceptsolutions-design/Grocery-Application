from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ItemStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class AdjustmentType(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"


class InventoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Product Name")
    price: float = Field(..., gt=0, description="Product Unit Price")
    quantity_available: int = Field(default=0, ge=0, description="Initial quantity avaialble")
    image: str = Field(..., min_length=1, description="Image URL")


class InventoryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=120, description="Product Name")
    price: Optional[float] = Field(None, gt=0, description="Product Unit Price")
    image: Optional[str] = Field(None, min_length=1, description="Image URL")

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_fields(cls, values):
        if isinstance(values, dict):
            if "quantity_available" in values or "quantity" in values:
                raise ValueError("Direct modification of quantity_available is not allowed. Please use the adjustment API.")
        return values


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price: float
    quantity_available: int
    image: str
    status: ItemStatus
    created_at: Optional[datetime] = None


class InventoryUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price: float
    quantity_available: int
    image: str
    status: ItemStatus
    updated_at: Optional[datetime] = None


class InventoryAdjustmentRequest(BaseModel):
    adjustment_type: AdjustmentType = Field(..., description="Adjustment type: ADD or REMOVE")
    quantity: int = Field(..., gt=0, description="Quantity to adjust (positive integer > 0)")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for inventory adjustment")


class InventoryAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    inventory_id: str
    adjustment_type: AdjustmentType
    quantity: int
    reason: str
    previous_quantity: int
    new_quantity: int
    created_by: str
    created_at: datetime


class InventoryAdjustmentSuccessResponse(BaseModel):
    message: str = "Inventory adjusted successfully"
    adjustment: InventoryAdjustmentResponse
    inventory: InventoryResponse


class InventoryAddSuccessResponse(BaseModel):
    message: str = "Item successfully added to inventory"
    data: InventoryResponse


class InventoryMessageResponse(BaseModel):
    message: str
