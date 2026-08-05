from typing import List, Optional
import strawberry

@strawberry.type
class VendorLedgerType:
    """Represents a single completed transaction in the lab/pharmacy app."""
    ledger_id: str
    order_id: str
    total_customer_paid: float
    vendor_earning: float
    created_at: Optional[str] = None

@strawberry.type
class DashboardEarningsType:
    """The master data type that powers the top of the Vendor's screen."""
    total_lifetime_earnings: float
    total_orders_completed: int
    recent_transactions: List[VendorLedgerType]
