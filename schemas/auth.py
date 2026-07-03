from pydantic import BaseModel, Field
from typing import Optional

class CustomerFirebaseLogin(BaseModel):
    """Payload sent by Flutter after successful Firebase OTP verification"""
    firebase_uid: str
    phone: str
    name: Optional[str] = None

class VendorLoginRequest(BaseModel):
    """Payload used by both Shops and Labs to log in"""
    phone: str
    password: str

class AdminCreateShopRequest(BaseModel):
    """Payload used by the Admin Panel to onboard a new Pharmacy"""
    phone: str
    owner_name: str
    shop_name: str
    address: str
    latitude: float
    longitude: float
    license_number: str
    shop_password: str # The raw password you assign them
    
    # Optional/Extra fields
    shop_alternative_phone_no: Optional[str] = None
    whatsapp_number: Optional[str] = None
    gstin_no: Optional[str] = None
    drug_license_upload: str
    pan_card_upload: str
    registration_certificate_upload: str
    bank_account_no: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None

class AdminCreateLabRequest(BaseModel):
    """Payload used by the Admin Panel to onboard a new Lab"""
    phone: str
    owner_name: str
    lab_name: str
    address: str
    latitude: float
    longitude: float
    license_number: str
    password: str # The raw password you assign them
    
    # Optional/Extra fields
    gst_number: Optional[str] = None
    pan_number: str
    nabl_accreditation_number: str
    registration_certificate_url: str
    bank_passbook_url: str
    emergency_contact_number: Optional[str] = None
    whatsapp_number: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str # "customer", "shop", or "lab"

class CheckPhoneRequest(BaseModel):
    """Payload to check if a phone number exists before sending OTP"""
    phone: str
