from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class OrderStatus(str, Enum):
    COMPLETED = "COMPLETED"

class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    inventory_id: str
    name: str
    price: float
    quantity: int
    total_price: float

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    customer_id: str
    items: List[OrderItemSchema]
    total_amount: float
    status: OrderStatus
    created_at: datetime

class OrderCreateResponse(BaseModel):
    message: str = "Order placed successfully"
    order: OrderResponse
