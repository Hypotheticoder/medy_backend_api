from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InventoryBase(BaseModel):
    medicine_id: str
    batch_number: str
    expiry_date: datetime
    ptr: float = Field(..., description="Price to Retailer excluding GST")
    mrp: float
    gst_percentage: float = 12.0
    available_stock_boxes: int = Field(..., ge=0)
    moq: int = Field(default=1, ge=1)

class InventoryCreate(InventoryBase):
    pass

class InventoryResponse(InventoryBase):
    inventory_id: str
    distributor_id: str
    is_active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
