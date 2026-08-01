from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================================
# 1. CREATE SCHEMA (Internal Use Only)
# ==========================================
class VendorLedgerCreate(BaseModel):
    """
    Used internally by your FastAPI backend when an order successfully completes.
    Never accept this directly from the frontend!
    """
    vendor_id: str
    vendor_type: str = Field(..., description="'lab' or 'pharmacy'")
    order_id: str
    
    total_customer_paid: float
    platform_commission: float
    vendor_earning: float

# ==========================================
# 2. UPDATE SCHEMA (Admin Payouts)
# ==========================================
class VendorLedgerPayoutUpdate(BaseModel):
    """
    Used by your Admin Panel when you manually transfer money to a lab/pharmacy.
    """
    settlement_reference_id: str = Field(..., description="The UPI UTR or NEFT reference number")

# ==========================================
# 3. RESPONSE SCHEMA
# ==========================================
class VendorLedgerResponse(VendorLedgerCreate):
    ledger_id: str
    settlement_status: str
    settlement_reference_id: Optional[str] = None
    created_at: datetime
    settled_at: Optional[datetime] = None

    class Config:
        from_attributes = True
