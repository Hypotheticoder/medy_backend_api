from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_bid_id():
    return f"BID-{uuid.uuid4().hex[:8].upper()}"

class OrderBid(Base):
    __tablename__ = "order_bids"

    bid_id = Column(String, primary_key=True, index=True, default=generate_bid_id)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False, index=True)
    shop_id = Column(String, ForeignKey("pharma_shop_users.shop_id"), nullable=False, index=True)
    
    proposed_items = Column(MutableList.as_mutable(JSON), nullable=False, default=list)
    total_bid_price = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=True)
    
    # Statuses: "pending", "accepted_by_customer", "rejected"
    bid_status = Column(String, nullable=False, default="pending")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
