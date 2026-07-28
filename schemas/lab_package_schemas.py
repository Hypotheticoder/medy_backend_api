from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class LabPackageBase(BaseModel):
    lab_id: str
    package_name: str
    test_details: List[Any]
    package_description: Optional[str] = None
    package_sample_collection_time: str
    package_report_delivery_time: str
    package_market_price: float
    discount_percentage: float
    package_final_price: float

class LabPackageCreate(LabPackageBase):
    pass

class LabPackageUpdate(BaseModel):
    package_name: Optional[str] = None
    test_details: Optional[List[Any]] = None
    package_description: Optional[str] = None
    package_sample_collection_time: Optional[str] = None
    package_report_delivery_time: Optional[str] = None
    package_market_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    package_final_price: Optional[float] = None

class LabPackageResponse(LabPackageBase):
    package_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
