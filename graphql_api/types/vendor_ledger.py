from typing import List, Optional
import strawberry

@strawberry.type
class VendorLedgerType:
    """Represents a single completed transaction in the lab/pharmacy app."""
    ledger_id: str
    order_id: str
    total_customer_paid: float
    # platform_commission hidden from vendor
    vendor_earning: float
    # settlement_status removed!
    created_at: str

@strawberry.type
class DashboardEarningsType:
    """The master data type that powers the top of the Vendor's screen."""
    total_lifetime_earnings: float
    # pending_bank_payouts removed!
    total_orders_completed: int
    recent_transactions: List[VendorLedgerType]
