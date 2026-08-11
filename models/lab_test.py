from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_test_id():
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"

# ==========================================
# 1. GLOBAL TEST CATALOG (Admin Managed)
# ==========================================
class LabTest(Base):
    """The master list of all tests so spelling and categories are unified."""
    __tablename__ = "lab_tests"

    test_id = Column(String, primary_key=True, index=True, default=generate_test_id)
    
    # Core Details
    test_name = Column(String, nullable=False, index=True) # e.g., "Complete Blood Count (CBC)"
    category = Column(String, nullable=False, index=True)  # e.g., "Blood", "Hormones", "Diabetes"
    description = Column(Text, nullable=True)
    
    # NEW: UX Details for Premium Look
    is_profile = Column(Boolean, default=False) # True for "Thyroid Profile" (multi-test), False for single tests
    number_of_parameters = Column(Integer, default=1) # e.g., 27 parameters in a CBC
    
    # 🚨 NEW: PACKAGE SPECIFIC COLUMNS
    is_package = Column(Boolean, default=False) # True for "Full Body Checkup"
    included_tests = Column(JSON, nullable=True) # e.g., ["CBC", "Lipid Profile", "Liver Function"]
    target_gender = Column(String, default="Both") # "Male", "Female", "Both" (For marketing filters)
    target_age_group = Column(String, nullable=True) # e.g., "40-60 Years"
    
    sample_type = Column(String, nullable=True) # e.g., "Blood", "Urine", "Stool", "Swab"
    
    # 🪄 MAGIC: Hidden Search Tags for customers who don't know medical terms
    search_tags = Column(String, nullable=True) # e.g., "sugar, glucose, fever, body ache, heart"

    # Medical requirements
    fasting_required = Column(Boolean, default=False)
    fasting_hours = Column(String, nullable=True) # e.g., "10-12 hours"
    pre_test_info = Column(Text, nullable=True) # e.g., "Do not consume alcohol 24 hours before."
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())



