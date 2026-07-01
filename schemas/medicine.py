from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class MedicineBase(BaseModel):
    medicine_name: str
    manufacturer: Optional[str] = None
    pack_form: str
    pack_size: str
    medicine_category: str
    medicine_photo: Optional[str] = None
    medicine_description: Optional[str] = None
    medicine_composition: Optional[str] = None
    precautions: Optional[Any] = None
    mrp: float
    discount_percent: float = 0.0
    final_selling_price: float
    prescription_required: bool = False

class MedicineCreate(MedicineBase):
    medicine_id: Optional[str] = None

class MedicineUpdate(BaseModel):
    medicine_name: Optional[str] = None
    manufacturer: Optional[str] = None
    pack_form: Optional[str] = None
    pack_size: Optional[str] = None
    medicine_category: Optional[str] = None
    medicine_photo: Optional[str] = None
    medicine_description: Optional[str] = None
    medicine_composition: Optional[str] = None
    precautions: Optional[Any] = None
    mrp: Optional[float] = None
    discount_percent: Optional[float] = None
    final_selling_price: Optional[float] = None
    prescription_required: Optional[bool] = None

class MedicineResponse(MedicineBase):
    medicine_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
