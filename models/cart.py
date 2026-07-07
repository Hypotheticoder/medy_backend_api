from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_cart_id():
    return f"CART-{uuid.uuid4().hex[:8].upper()}"

class Cart(Base):
    __tablename__ = "carts"

    cart_id = Column(String, primary_key=True, index=True, default=generate_cart_id)
    # 1-to-1 relationship: Each customer has exactly one active cart
    customer_id = Column(String, ForeignKey("customer_users.customer_id"), unique=True, nullable=False, index=True)
    
    # We use MutableList so SQLAlchemy automatically detects when we add/remove items to this array
    items = Column(MutableList.as_mutable(JSON), nullable=False, default=list)
    total_price = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
