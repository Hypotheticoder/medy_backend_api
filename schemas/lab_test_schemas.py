from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================================
# 1. GLOBAL CATALOG SCHEMAS (Admin Only)
# ==========================================
class LabTestCreate(BaseModel):
    """Payload sent by Admin to add a new test to the global dictionary."""
    test_name: str = Field(..., description="e.g., HbA1c")
    category: str = Field(..., description="e.g., Diabetes")
    description: Optional[str] = None
    
    is_profile: bool = False
    number_of_parameters: int = 1
    sample_type: Optional[str] = Field(None, description="Blood, Urine, Swab")
    search_tags: Optional[str] = Field(None, description="Hidden keywords: sugar, sweet")
    
    fasting_required: bool = False
    fasting_hours: Optional[str] = None
    pre_test_info: Optional[str] = None

class LabTestResponse(LabTestCreate):
    test_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# 2. LAB PRICING SCHEMAS (Patholab Back-Office)
# ==========================================
class LabTestPricingCreate(BaseModel):
    """Payload sent by a PathLab to add a test to their specific inventory."""
    test_id: str = Field(..., description="The ID from the Global Catalog")
    lab_base_rate: float
    customer_selling_price: float
    mrp: float
    
    turnaround_time_hours: int = Field(24, description="How fast do they give the report?")
    home_collection_available: bool = True
    walk_in_available: bool = True

class LabTestPricingResponse(LabTestPricingCreate):
    id: str
    lab_id: str
    
    class Config:
        from_attributes = True
