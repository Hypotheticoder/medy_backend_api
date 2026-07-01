from sqlalchemy import Column, String, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_shop_id():
    return f"SHOP-{uuid.uuid4().hex[:8].upper()}"

class PharmaShopUser(Base):
    __tablename__ = "pharma_shop_users"

    shop_id = Column(String, primary_key=True, index=True, default=generate_shop_id)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    owner_name = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    shop_image = Column(String, nullable=True)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    license_number = Column(String, unique=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_accepting_orders = Column(Boolean, default=True, nullable=False)
    rating = Column(Float, default=5.0, nullable=False)
    
    # Extra columns for registration
    shop_password = Column(String, nullable=False)
    shop_alternative_phone_no = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    gstin_no = Column(String, nullable=True)
    drug_license_upload = Column(String, nullable=False)
    pan_card_upload = Column(String, nullable=False)
    registration_certificate_upload = Column(String, nullable=False)
    bank_account_no = Column(String, nullable=True)
    bank_ifsc_code = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        return {
            "shop_id": self.shop_id,
            "owner_name": self.owner_name,
            "shop_name": self.shop_name,
            "phone": self.phone,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_verified": self.is_verified,
            "is_accepting_orders": self.is_accepting_orders,
            "rating": self.rating,
            "shop_alternative_phone_no": self.shop_alternative_phone_no,
            "whatsapp_number": self.whatsapp_number,
            "gstin_no": self.gstin_no,
            "drug_license_upload": self.drug_license_upload,
            "pan_card_upload": self.pan_card_upload,
            "registration_certificate_upload": self.registration_certificate_upload,
            "bank_account_no": self.bank_account_no,
            "bank_ifsc_code": self.bank_ifsc_code,
            "bank_name": self.bank_name,
            "bank_account_name": self.bank_account_name,
            "status": self.status
        }
