from typing import List
from pydantic import BaseModel, ConfigDict, Field

class CartItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    inventory_id: str
    name: str
    price: float
    quantity: int
    image: str
    total_price: float

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: str
    items: List[CartItemSchema] = []
    cart_total: float = 0.0

class CartItemAddRequest(BaseModel):
    inventory_id: str = Field(..., description="ID of the inventory item to add")
    quantity: int = Field(..., gt=0, description="Quantity to add")




class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="New quantity for the item")
