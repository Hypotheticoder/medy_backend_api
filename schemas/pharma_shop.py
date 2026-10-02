from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class PharmaShopBase(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    owner_name: str
    shop_name: str
    shop_image: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    license_number: str
    is_verified: bool = False
    whatsapp_number: Optional[str] = None
    shop_alternative_phone_no: Optional[str] = None
    gstin_no: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    is_accepting_orders: bool = True
    rating: float = 5.0
    shop_alternative_phone_no: Optional[str] = None
    whatsapp_number: Optional[str] = None
    gstin_no: Optional[str] = None
    drug_license_upload: str
    pan_card_upload: str
    registration_certificate_upload: str
    bank_account_no: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    status: str = "pending"

class PharmaShopCreate(PharmaShopBase):
    shop_password: str

class PharmaShopUpdate(BaseModel):
    email: Optional[EmailStr] = None
    owner_name: Optional[str] = None
    shop_name: Optional[str] = None
    shop_image: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_accepting_orders: Optional[bool] = None
    shop_alternative_phone_no: Optional[str] = None
    whatsapp_number: Optional[str] = None
    gstin_no: Optional[str] = None
    drug_license_upload: Optional[str] = None
    pan_card_upload: Optional[str] = None
    registration_certificate_upload: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    status: Optional[str] = None

class PharmaShopResponse(PharmaShopBase):
    shop_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
