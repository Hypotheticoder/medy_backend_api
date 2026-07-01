from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LabBase(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    owner_name: str
    lab_name: str
    lab_image: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    license_number: str
    is_verified: bool = False
    is_accepting_bookings: bool = True
    rating: float = 5.0
    gst_number: Optional[str] = None
    pan_number: str
    nabl_accreditation_number: str
    registration_certificate_url: str
    bank_passbook_url: str
    emergency_contact_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    terms_conditions_accepted: bool = False
    privacy_policy_accepted: bool = False
    status: str = "pending"

class LabCreate(LabBase):
    password: str

class LabUpdate(BaseModel):
    email: Optional[EmailStr] = None
    owner_name: Optional[str] = None
    lab_name: Optional[str] = None
    lab_image: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_accepting_bookings: Optional[bool] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    nabl_accreditation_number: Optional[str] = None
    registration_certificate_url: Optional[str] = None
    bank_passbook_url: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    terms_conditions_accepted: Optional[bool] = None
    privacy_policy_accepted: Optional[bool] = None
    status: Optional[str] = None

class LabResponse(LabBase):
    lab_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True
