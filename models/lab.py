from sqlalchemy import Column, String, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_lab_id():
    return f"LAB-{uuid.uuid4().hex[:8].upper()}"

class LabUser(Base):
    __tablename__ = "lab_users"

    lab_id = Column(String, primary_key=True, index=True, default=generate_lab_id)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    owner_name = Column(String, nullable=False)
    lab_name = Column(String, nullable=False)
    lab_image = Column(String, nullable=True)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    license_number = Column(String, unique=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_accepting_bookings = Column(Boolean, default=True, nullable=False)
    rating = Column(Float, default=5.0, nullable=False)
    platform_commission_rate = Column(Float, default=0.20, nullable=False)
    
    # Extra columns for registration
    password = Column(String, nullable=False)
    gst_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=False)
    nabl_accreditation_number = Column(String, nullable=False)
    registration_certificate_url = Column(String, nullable=False)
    bank_passbook_url = Column(String, nullable=False)
    emergency_contact_number = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    terms_conditions_accepted = Column(Boolean, default=False, nullable=False)
    privacy_policy_accepted = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="pending", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "lab_id": self.lab_id,
            "owner_name": self.owner_name,
            "lab_name": self.lab_name,
            "phone": self.phone,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_verified": self.is_verified,
            "is_accepting_bookings": self.is_accepting_bookings,
            "rating": self.rating,
            "gst_number": self.gst_number,
            "pan_number": self.pan_number,
            "nabl_accreditation_number": self.nabl_accreditation_number,
            "registration_certificate_url": self.registration_certificate_url,
            "bank_passbook_url": self.bank_passbook_url,
            "emergency_contact_number": self.emergency_contact_number,
            "whatsapp_number": self.whatsapp_number,
            "terms_conditions_accepted": self.terms_conditions_accepted,
            "privacy_policy_accepted": self.privacy_policy_accepted,
            "status": self.status,
            "last_login_at": self.last_login_at.isoformat() if hasattr(self, 'last_login_at') and self.last_login_at else None
        }
