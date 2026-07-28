from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_package_id():
    return f"PKG-{str(uuid.uuid4())[:8].upper()}"

class LabPackage(Base):
    __tablename__ = "lab_packages"

    package_id = Column(String, primary_key=True, index=True, default=generate_package_id)
    lab_id = Column(String, index=True, nullable=False)
    package_name = Column(String, nullable=False)
    test_details = Column(JSON, default=[]) # Storing list of test strings/objects
    package_description = Column(String, nullable=True)
    package_sample_collection_time = Column(String, nullable=False)
    package_report_delivery_time = Column(String, nullable=False)
    
    package_market_price = Column(Float, nullable=False, default=0.0)
    discount_percentage = Column(Float, nullable=False, default=0.0)
    package_final_price = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
