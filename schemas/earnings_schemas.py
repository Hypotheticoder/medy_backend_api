from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VendorLedgerResponse(BaseModel):
    ledger_id: str
    order_id: str
    total_customer_paid: float
    platform_commission: float
    vendor_earning: float
    settlement_status: str
    settlement_reference_id: Optional[str] = None
    created_at: datetime
    settled_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VendorEarningsSummary(BaseModel):
    total_earnings: float
    total_pending: float
    total_settled: float
