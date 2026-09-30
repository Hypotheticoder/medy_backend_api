from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from db import Base
from utils.id_gen import generate_ulid

class B2BPurchaseOrder(Base):
    __tablename__ = "b2b_purchase_orders"

    po_id = Column(String, primary_key=True, index=True, default=lambda: generate_ulid("PO"))
    
    # Buyer & Seller
    shop_id = Column(String, ForeignKey("pharma_shop_users.shop_id"), nullable=False, index=True)
    distributor_id = Column(String, ForeignKey("distributor_users.distributor_id"), nullable=False, index=True)
    
    # Snapshot of the purchased items
    items = Column(MutableList.as_mutable(JSON), nullable=False, default=list)

    # Financials (GST strictly split for input tax credit)
    subtotal = Column(Float, nullable=False, default=0.0) # Total PTR * Qty
    cgst_amount = Column(Float, nullable=False, default=0.0)
    sgst_amount = Column(Float, nullable=False, default=0.0)
    total_invoice_amount = Column(Float, nullable=False, default=0.0)

    # Standard B2B Payment Cycles
    payment_terms = Column(String, nullable=False, default="prepaid") # "cod", "prepaid", "net_15", "net_30"
    payment_status = Column(String, nullable=False, default="pending") 
    
    # PO Lifecycle
    # placed -> accepted -> invoiced -> dispatched -> delivered -> cancelled
    po_status = Column(String, nullable=False, default="placed", index=True) 
    
    # The final generated GST invoice PDF for the retailer's accounting
    invoice_url = Column(String, nullable=True) 
    
    # Logistics (Handled by distributor's van/freight, not Caby)
    delivery_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
