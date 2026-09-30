from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class DistributorBase(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    company_name: str
    owner_name: str
    address: str
    latitude: float
    longitude: float
    gstin_no: str
    pan_number: str
    wholesale_drug_license_20b: str
    wholesale_drug_license_21b: str
    bank_account_no: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

class DistributorCreate(DistributorBase):
    password: str

class DistributorResponse(DistributorBase):
    distributor_id: str
    is_verified: bool
    is_accepting_orders: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True} # Allows Pydantic to read SQLAlchemy models
