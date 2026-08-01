from sqlalchemy.orm import Session
from sqlalchemy import func
from models.vendor_ledger import VendorLedger

PLATFORM_COMMISSION_RATE = 0.20 # 20% commission

def generate_earning_record(db: Session, vendor_id: str, vendor_type: str, order_id: str, total_amount: float):
    """
    Called automatically when an order is completed.
    Calculates the commission and records the vendor's net earning.
    """
    # Check if a ledger entry already exists to avoid duplicates
    existing = db.query(VendorLedger).filter(VendorLedger.order_id == order_id).first()
    if existing:
        return existing

    commission = total_amount * PLATFORM_COMMISSION_RATE
    vendor_earning = total_amount - commission

    ledger_entry = VendorLedger(
        vendor_id=vendor_id,
        vendor_type=vendor_type,
        order_id=order_id,
        total_customer_paid=total_amount,
        platform_commission=commission,
        vendor_earning=vendor_earning,
        settlement_status="pending_clearance"
    )

    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)
    return ledger_entry

def get_vendor_ledger(db: Session, vendor_id: str):
    """Fetch all transaction history for a specific vendor."""
    return db.query(VendorLedger).filter(VendorLedger.vendor_id == vendor_id).order_by(VendorLedger.created_at.desc()).all()

def get_vendor_earnings_summary(db: Session, vendor_id: str):
    """Aggregate total earnings, pending, and settled amounts."""
    ledger = db.query(VendorLedger).filter(VendorLedger.vendor_id == vendor_id).all()
    
    total_earnings = sum(entry.vendor_earning for entry in ledger)
    total_pending = sum(entry.vendor_earning for entry in ledger if entry.settlement_status in ["pending_clearance", "ready_for_payout"])
    total_settled = sum(entry.vendor_earning for entry in ledger if entry.settlement_status == "settled")
    
    return {
        "total_earnings": total_earnings,
        "total_pending": total_pending,
        "total_settled": total_settled
    }
