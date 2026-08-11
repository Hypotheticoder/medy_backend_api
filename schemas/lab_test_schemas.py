from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# 1. GLOBAL CATALOG SCHEMAS (Admin Only)
# ==========================================
class LabTestCreate(BaseModel):
    """Payload sent by Admin to add a new test to the global dictionary."""
    test_name: str = Field(..., description="e.g., HbA1c or Comprehensive Full Body Checkup")
    category: str = Field(..., description="e.g., Diabetes or Packages")
    description: Optional[str] = None
    
    is_profile: bool = False
    number_of_parameters: int = 1
    
    # 🚨 NEW: Package Details
    is_package: bool = False
    included_tests: Optional[List[str]] = Field(None, description="List of tests inside this package")
    target_gender: str = "Both"
    target_age_group: Optional[str] = None
    
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
    mrp: float
    discount_percent: float = Field(0.0, description="0 to 100")
    
    turnaround_time_hours: int = Field(24, description="How fast do they give the report?")
    home_collection_available: bool = True
    walk_in_available: bool = True

class LabTestPricingResponse(LabTestPricingCreate):
    id: str
    lab_id: str
    final_price: float
    
    class Config:
        from_attributes = True

# ==========================================
# 3. LAB INVENTORY MANAGEMENT (NEW)
# ==========================================
class LabTestPricingUpdate(BaseModel):
    """Payload when a lab edits a test they already offer."""
    mrp: Optional[float] = None
    discount_percent: Optional[float] = None
    turnaround_time_hours: Optional[int] = None
    home_collection_available: Optional[bool] = None
    walk_in_available: Optional[bool] = None

class LabInventoryItemResponse(BaseModel):
    """Combined response showing the Global Test Name + The Lab's specific price"""
    id: str
    test_id: str
    test_name: str
    category: str
    mrp: float
    discount_percent: float
    final_price: float
    turnaround_time_hours: int
    home_collection_available: bool
    walk_in_available: bool
    
    class Config:
        from_attributes = True

class CustomLabPackageCreate(BaseModel):
    package_name: str = Field(..., description="e.g., Apollo Special Checkup")
    description: Optional[str] = Field(None, description="Description of the package")
    included_test_ids: List[str] = Field(..., description="IDs from the global catalog")
    price: float
    discount_percentage: float = 0.0
    turnaround_time_hours: int = 24

class CustomLabPackageUpdate(BaseModel):
    package_name: Optional[str] = None
    description: Optional[str] = None
    included_test_ids: Optional[List[str]] = None

