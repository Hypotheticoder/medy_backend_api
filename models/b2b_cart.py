from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from db import Base
from utils.id_gen import generate_ulid

class B2BCart(Base):
    __tablename__ = "b2b_carts"

    cart_id = Column(String, primary_key=True, default=lambda: generate_ulid("BC"))
    
    # The Buyer (Retailer)
    shop_id = Column(String, ForeignKey("pharma_shop_users.shop_id"), unique=True, nullable=False, index=True)
    
    # The locked Seller (Distributor)
    active_distributor_id = Column(String, ForeignKey("distributor_users.distributor_id"), nullable=True)

    # Array of objects: [{inventory_id, medicine_id, batch_number, ptr, qty, gst_percentage}]
    items = Column(MutableList.as_mutable(JSON), nullable=False, default=list)
    
    total_estimated_price = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
