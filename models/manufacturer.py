from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
import uuid

def generate_manufacturer_id():
    return f"MFG{uuid.uuid4().hex[:8].upper()}"

class ManufacturerUser(Base):
    __tablename__ = "manufacturer_users"

    manufacturer_id = Column(String, primary_key=True, default=generate_manufacturer_id)
    company_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    gstin_no = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
