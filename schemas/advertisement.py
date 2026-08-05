from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AdvertisementBase(BaseModel):
    title: str
    target_url: Optional[str] = None
    is_active: bool = True

class AdvertisementCreate(AdvertisementBase):
    pass

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    target_url: Optional[str] = None
    is_active: Optional[bool] = None

class AdvertisementResponse(AdvertisementBase):
    id: str
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True
