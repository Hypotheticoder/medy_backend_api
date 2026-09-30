from sqlalchemy import Column, String, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from db import Base
from utils.id_gen import generate_ulid

class DistributorUser(Base):
    __tablename__ = "distributor_users"

    distributor_id = Column(String, primary_key=True, index=True, default=lambda: generate_ulid("DS"))
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    company_name = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    
    # Location for PostGIS radius search
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    # Strict B2B Indian Compliance
    gstin_no = Column(String, unique=True, nullable=False)
    pan_number = Column(String, nullable=False)
    wholesale_drug_license_20b = Column(String, nullable=False) # Document URL
    wholesale_drug_license_21b = Column(String, nullable=False) # Document URL
    
    # Banking for B2B settlements
    bank_account_no = Column(String, nullable=True)
    bank_ifsc_code = Column(String, nullable=True)
    
    is_verified = Column(Boolean, default=False, nullable=False)
    is_accepting_orders = Column(Boolean, default=True, nullable=False)
    status = Column(String, default="pending", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
