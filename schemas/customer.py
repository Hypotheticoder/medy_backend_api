from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None
    status: str = "active"

class CustomerCreate(CustomerBase):
    firebase_uid: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None
    status: Optional[str] = None

class CustomerResponse(CustomerBase):
    customer_id: str
    firebase_uid: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
