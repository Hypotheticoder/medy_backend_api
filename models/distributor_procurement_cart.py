from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
import uuid

def generate_dpc_id():
    return f"DPC{uuid.uuid4().hex[:8].upper()}"

class DistributorProcurementCart(Base):
    __tablename__ = "distributor_procurement_carts"

    cart_id = Column(String, primary_key=True, default=generate_dpc_id)
    distributor_id = Column(String, ForeignKey("distributor_users.distributor_id"), unique=True, nullable=False)
    
    manufacturer_id = Column(String, ForeignKey("manufacturer_users.manufacturer_id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DistributorProcurementCartItem(Base):
    __tablename__ = "distributor_procurement_cart_items"

    item_id = Column(String, primary_key=True, default=lambda: f"DPCI{uuid.uuid4().hex[:8].upper()}")
    cart_id = Column(String, ForeignKey("distributor_procurement_carts.cart_id"), nullable=False)
    
    medicine_id = Column(String, ForeignKey("medicines.medicine_id"), nullable=False)
    
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=False)
    
    added_at = Column(DateTime, default=datetime.utcnow)
