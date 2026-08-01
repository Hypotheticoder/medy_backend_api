from sqlalchemy.orm import Session
from datetime import datetime
from models.vendor_ledger import VendorLedger, generate_ledger_id
from schemas.vendor_ledger_schemas import VendorLedgerCreate

def create_ledger_entry(db: Session, ledger_data: VendorLedgerCreate) -> VendorLedger:
    """
    Called exactly when an order goes from 'pending' to 'paid'.
    Locks in the math so the admin and vendor know exactly who owes what.
    """
    db_ledger = VendorLedger(
        ledger_id=generate_ledger_id(),
        **ledger_data.model_dump()
    )
    
    db.add(db_ledger)
    db.commit()
    db.refresh(db_ledger)
    return db_ledger

def mark_payout_settled(db: Session, ledger_id: str, reference_id: str) -> VendorLedger:
    """
    Called by the Admin Panel when you actually send the money to the Lab's bank account.
    Moves the status from 'ready_for_payout' to 'settled'.
    """
    ledger = db.query(VendorLedger).filter(VendorLedger.ledger_id == ledger_id).first()
    
    if ledger and ledger.settlement_status != "settled":
        ledger.settlement_status = "settled"
        ledger.settlement_reference_id = reference_id
        ledger.settled_at = datetime.utcnow() # Stamps the exact time the money left your bank
        
        db.commit()
        db.refresh(ledger)
        
    return ledger

def get_pending_payouts(db: Session, vendor_type: str = None):
    """
    Used by your Admin Dashboard to see who you need to pay this week.
    """
    query = db.query(VendorLedger).filter(VendorLedger.settlement_status == "ready_for_payout")
    if vendor_type:
        query = query.filter(VendorLedger.vendor_type == vendor_type)
        
    return query.all()
