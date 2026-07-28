from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from db import Base
import uuid

# ==========================================
# 2. LAB SPECIFIC INVENTORY & PRICING
# ==========================================
class LabTestPricing(Base):
    """
    The 'Bridge' Table. 
    If a row exists here, it means this specific Lab offers this specific Test.
    """
    __tablename__ = "lab_test_pricing"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    
    # Foreign Keys connecting the Lab to the Global Test
    lab_id = Column(String, ForeignKey("lab_users.lab_id"), nullable=False, index=True)
    test_id = Column(String, ForeignKey("lab_tests.test_id"), nullable=False, index=True)
    
    # NEW Pricing Fields to match Flutter App
    price = Column(Float, nullable=False, server_default="0.0") # Used to be mrp
    discount_percentage = Column(Float, nullable=False, server_default="0.0")
    final_price = Column(Float, nullable=False, server_default="0.0") # Used to be customer_selling_price
    
    # Internal Base Rate (what the lab actually gets)
    lab_base_rate = Column(Float, nullable=True)
    
    # NEW: Logistics & Turnaround Time (Crucial for conversion rate)
    turnaround_time_hours = Column(Integer, default=24) # e.g., 24 (Flutter shows: "Reports in 24 hrs")
    home_collection_available = Column(Boolean, default=True)
    walk_in_available = Column(Boolean, default=True) # Customer visits the clinic
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
