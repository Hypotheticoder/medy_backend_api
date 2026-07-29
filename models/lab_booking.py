from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_booking_id():
    return f"LAB-BKG-{uuid.uuid4().hex[:8].upper()}"

class LabBooking(Base):
    """Stores the actual appointment when a customer books a test at a patholab."""
    __tablename__ = "lab_bookings"

    booking_id = Column(String, primary_key=True, index=True, default=generate_booking_id)
    customer_id = Column(String, ForeignKey("customer_users.customer_id"), nullable=False, index=True)
    lab_id = Column(String, ForeignKey("lab_users.lab_id"), nullable=False, index=True)

    # Patient Details (might be booking for their parents/kids)
    patient_name = Column(String, nullable=False)
    patient_phone = Column(String, nullable=False)
    patient_age = Column(String, nullable=True)
    patient_gender = Column(String, nullable=True)

    # Home Collection Details
    is_home_collection = Column(Boolean, default=True, nullable=False)
    collection_address = Column(Text, nullable=True)
    collection_lat = Column(Float, nullable=True)
    collection_lng = Column(Float, nullable=True)
    
    # JSON array of the matched tests they actually booked
    # Format: [{"test_id": "T1", "test_name": "CBC", "price": 400}]
    booked_tests = Column(MutableList.as_mutable(JSON), nullable=False, default=list)

    # Financials
    total_price = Column(Float, nullable=False)
    payment_mode = Column(String, nullable=False, default="cod") # "cod" or "online"
    payment_status = Column(String, nullable=False, default="pending") 
    transaction_id = Column(String, nullable=True) # Razorpay ID if online

    # Lifecycle: pending -> confirmed -> sample_collected -> processing -> report_ready -> cancelled
    booking_status = Column(String, nullable=False, default="pending", index=True)

    # The final PDF report link that the Lab will upload later
    report_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        # Format booked tests to include 'item_name' for frontend compatibility if needed
        # Or let frontend handle it. We'll send raw data and format patient details correctly.
        return {
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "lab_id": self.lab_id,
            "booking_type": "home_collection" if self.is_home_collection else "lab_visit",
            "patient_details": [{
                "full_name": self.patient_name,
                "name": self.patient_name,
                "phone_number": self.patient_phone,
                "age": self.patient_age,
                "gender": self.patient_gender
            }],
            "sample_collection_address": {
                "address_1": self.collection_address or ""
            },
            "booked_tests": self.booked_tests,
            "sub_total_amount": self.total_price,
            "total_price": self.total_price,
            "platform_fee": 0.0,
            "tax_amount": 0.0,
            "total_amount_to_be_paid": self.total_price,
            "payment_mode": self.payment_mode,
            "booking_status": self.booking_status,
            "report_url": self.report_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
