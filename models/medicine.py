from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_medicine_id():
    return f"MED-{uuid.uuid4().hex[:8].upper()}"

class Medicine(Base):
    __tablename__ = "medicines"

    medicine_id = Column(String, primary_key=True, index=True, default=generate_medicine_id)
    medicine_name = Column(String, nullable=False, index=True)
    manufacturer = Column(String, nullable=True, index=True) # e.g., "Sun Pharma", "Cipla"
    
    # pack_form: "Tablet", "Capsule", "Syrup", "Injection", "Cream", "Drop"
    pack_form = Column(String, nullable=False, index=True) 
    # pack_size: "1 Strip of 15 Tablets", "100ml Bottle", "10g Tube"
    pack_size = Column(String, nullable=False) 
    
    medicine_category = Column(String, nullable=False, index=True) # e.g., "Pain Relief", "Antibiotics"
    medicine_photo = Column(String, nullable=True)
    medicine_description = Column(Text, nullable=True)
    medicine_composition = Column(String, nullable=True) # e.g., "Paracetamol 650mg"
    precautions = Column(JSON, nullable=True)
    
    mrp = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0, nullable=True)
    final_selling_price = Column(Float, nullable=False) # Auto-calculated during CSV import
    
    prescription_required = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        return {
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine_name,
            "manufacturer": self.manufacturer,
            "pack_form": self.pack_form,
            "pack_size": self.pack_size,
            "medicine_category": self.medicine_category,
            "medicine_composition": self.medicine_composition,
            "mrp": self.mrp,
            "discount_percent": self.discount_percent,
            "final_selling_price": self.final_selling_price,
            "prescription_required": self.prescription_required
        }
