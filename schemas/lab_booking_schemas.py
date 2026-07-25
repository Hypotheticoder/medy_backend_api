from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class BookedTestItem(BaseModel):
    """Schema for the individual tests inside the booked_tests array."""
    test_id: str
    test_name: str
    price: float

class LabBookingCreate(BaseModel):
    """Payload sent by the Flutter app when a customer clicks 'Confirm Booking'."""
    lab_id: str
    patient_name: str
    patient_phone: str
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = Field(None, description="Male, Female, Other")
    
    is_home_collection: bool = True
    collection_address: Optional[str] = None
    collection_lat: Optional[float] = None
    collection_lng: Optional[float] = None
    
    booked_tests: List[BookedTestItem] = Field(..., description="Array of tests they are buying")
    total_price: float
    payment_mode: str = Field("cod", description="cod or online")

class LabBookingStatusUpdate(BaseModel):
    """Payload for the Lab's tablet to update the booking state."""
    new_status: str = Field(..., description="e.g., sample_collected, processing, report_ready")

class LabBookingResponse(LabBookingCreate):
    booking_id: str
    customer_id: str
    payment_status: str
    booking_status: str
    report_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
