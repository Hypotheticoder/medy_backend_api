from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from db import Base
import uuid

def generate_ledger_id():
    return f"TXN-{uuid.uuid4().hex[:8].upper()}"

class VendorLedger(Base):
    """
    The Master Accounting Book. 
    Tracks exactly how much money came in, what your profit was, and what the lab gets paid.
    """
    __tablename__ = "vendor_ledgers"

    ledger_id = Column(String, primary_key=True, index=True, default=generate_ledger_id)
    
    # 1. WHO IS INVOLVED?
    vendor_id = Column(String, nullable=False, index=True) # Can be lab_id or shop_id
    vendor_type = Column(String, nullable=False) # "lab" or "pharmacy"
    
    # 2. WHAT WAS THE ORDER?
    order_id = Column(String, nullable=False, index=True) # The LabBooking ID or Medicine Order ID
    
    # 3. THE MONEY BREAKDOWN
    total_customer_paid = Column(Float, nullable=False) # e.g., ₹500
    platform_commission = Column(Float, nullable=False) # e.g., ₹100 (YOUR PROFIT)
    vendor_earning = Column(Float, nullable=False)      # e.g., ₹400 (WHAT THE LAB KEEPS)
    
    # 4. PAYOUT STATUS (Crucial for your accounting)
    # "pending_clearance" -> Money is in Razorpay, waiting to hit your bank
    # "ready_for_payout" -> Money is in your bank, you owe the Lab
    # "settled" -> You successfully transferred ₹400 to the Lab's bank account
    settlement_status = Column(String, default="pending_clearance", nullable=False, index=True)
    
    # Proof of transfer
    settlement_reference_id = Column(String, nullable=True) # UTR or IMPS reference number

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    settled_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "ledger_id": self.ledger_id,
            "order_id": self.order_id,
            "total_customer_paid": self.total_customer_paid,
            "platform_commission": self.platform_commission,
            "vendor_earning": self.vendor_earning,
            "settlement_status": self.settlement_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
