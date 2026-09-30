from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean, Integer
from sqlalchemy.sql import func
from db import Base
from utils.id_gen import generate_ulid

class DistributorInventory(Base):
    __tablename__ = "distributor_inventory"

    inventory_id = Column(String, primary_key=True, default=lambda: generate_ulid("IN"))
    
    distributor_id = Column(String, ForeignKey("distributor_users.distributor_id"), nullable=False, index=True)
    medicine_id = Column(String, ForeignKey("medicines.medicine_id"), nullable=False, index=True)
    
    # Crucial for B2B pharma
    batch_number = Column(String, nullable=False, index=True)
    expiry_date = Column(DateTime, nullable=False, index=True)
    
    # B2B Pricing Structure
    ptr = Column(Float, nullable=False) # Price to Retailer (excl. GST)
    mrp = Column(Float, nullable=False) # Reference MRP for the retailer's margin
    gst_percentage = Column(Float, default=12.0) # Standard pharma GST slab
    
    # Stock & Logistics
    available_stock_boxes = Column(Integer, nullable=False, default=0)
    moq = Column(Integer, default=1) # Minimum Order Quantity (e.g., must buy 10 boxes minimum)
    
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
