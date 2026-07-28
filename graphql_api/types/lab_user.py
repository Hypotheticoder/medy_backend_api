import strawberry
from typing import Optional

@strawberry.type
class LabUserType:
    """GraphQL representation of a Lab User Profile (excluding passwords)."""
    lab_id: str
    phone: str
    owner_name: str
    lab_name: str
    address: str
    latitude: float
    longitude: float
    license_number: str
    is_verified: bool
    is_accepting_bookings: bool
    rating: float
    
    email: Optional[str] = None
    lab_image: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    nabl_accreditation_number: Optional[str] = None
    registration_certificate_url: Optional[str] = None
    bank_passbook_url: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
