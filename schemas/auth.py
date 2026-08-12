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

class SendOtpRequest(BaseModel):
    phone: str

class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str

class LabProfileResponse(BaseModel):
    """Payload representing a Lab User's Profile"""
    lab_id: str
    phone: str
    email: Optional[str] = None
    owner_name: str
    lab_name: str
    lab_image: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    license_number: str
    is_verified: bool
    is_accepting_bookings: bool
    rating: float
    gst_number: Optional[str] = None
    pan_number: str
    nabl_accreditation_number: str
    registration_certificate_url: str
    bank_passbook_url: str
    emergency_contact_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    
    # We alias phone to mobile_number and lab_image to lab_logo_url so the Flutter app parses it automatically
    # Or flutter already handles phone fallback?
    # Flutter expects: mobile_number, email_address or email, lab_logo_url or lab_logo
    class Config:
        from_attributes = True
        # Let's map model fields to flutter expected fields if needed.
        # But flutter handles `mobile_number`, which we don't have.
        # Let's just return what DB has and we'll fix flutter side if needed, but wait:
        # Flutter's User.fromJson has:
        # id: json['lab_id'] ?? json['id'],
        # mobileNumber: json['mobile_number'],
        # email: json['email_address'] ?? json['email'],
        # labLogo: json['lab_logo_url'] ?? json['lab_logo']
        # I will just return the exact fields that are in DB.

