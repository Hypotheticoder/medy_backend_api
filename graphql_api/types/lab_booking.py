from datetime import datetime
from typing import Optional
import strawberry
from strawberry.scalars import JSON

@strawberry.type
class LabBookingType:
    """GraphQL representation of a customer's Lab Booking History."""
    booking_id: str
    customer_id: str
    lab_id: str
    
    # Updated patient details
    patient_name: str
    patient_phone: str
    patient_age: Optional[str]
    patient_gender: Optional[str]
    
    # Updated collection details
    is_home_collection: bool
    collection_address: Optional[str]
    collection_lat: Optional[float]
    collection_lng: Optional[float]
    
    booked_tests: JSON # Returns the exact array of tests they bought
    total_price: float
    payment_mode: str
    payment_status: str
    transaction_id: Optional[str]
    booking_status: str
    report_url: Optional[str]
    created_at: datetime
