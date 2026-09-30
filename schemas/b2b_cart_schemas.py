from pydantic import BaseModel
from typing import List, Optional

class B2BCartItem(BaseModel):
    inventory_id: str
    medicine_id: str
    batch_number: str
    qty_boxes: int
    ptr: float
    gst_percentage: float

class AddToB2BCart(BaseModel):
    distributor_id: str
    item: B2BCartItem

class B2BCartResponse(BaseModel):
    cart_id: str
    shop_id: str
    active_distributor_id: Optional[str]
    items: List[B2BCartItem]
    total_estimated_price: float

    class Config:
        from_attributes = True
