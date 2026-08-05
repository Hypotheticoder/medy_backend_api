from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from models.vendor_ledger import VendorLedger
from models.lab_booking import LabBooking

router = APIRouter(prefix="/api/rest/earnings", tags=["REST - Earnings Dashboard"])

@router.get("/{vendor_type}/{vendor_id}/summary")
def get_earnings_summary(vendor_type: str, vendor_id: str, db: Session = Depends(get_db)):
    """
    Returns a simple, clean summary of total earnings.
    vendor_type should be 'lab' or 'pharmacy'.
    """
    # Earnings from VendorLedger & Net Balance Calculation
    ledgers = db.query(VendorLedger).filter(
        VendorLedger.vendor_id == vendor_id,
        VendorLedger.vendor_type == vendor_type
    ).all()

    # Get bookings to check payment mode
    # Assuming for pharmacy we might need something similar later, but right now we only have LabBooking
    bookings = db.query(LabBooking).filter(LabBooking.lab_id == vendor_id).all()
    booking_modes = {b.booking_id: (b.payment_mode or "cod").lower() for b in bookings}

    total_earnings = 0.0
    amount_platform_owes_lab = 0.0
    amount_lab_owes_platform = 0.0

    for row in ledgers:
        total_earnings += row.vendor_earning
        payment_mode = booking_modes.get(row.order_id, "cod")
        
        if payment_mode == "online":
            amount_platform_owes_lab += row.vendor_earning
        else: # cod
            amount_lab_owes_platform += row.platform_commission

    net_balance = amount_platform_owes_lab - amount_lab_owes_platform

    return {
        "total_earnings": round(total_earnings, 2),
        "total_platform_owes_lab": round(amount_platform_owes_lab, 2),
        "total_lab_owes_platform": round(amount_lab_owes_platform, 2),
        "net_balance": round(net_balance, 2)
    }

@router.get("/{vendor_type}/{vendor_id}")
def get_recent_transactions(vendor_type: str, vendor_id: str, db: Session = Depends(get_db)):
    """
    Returns the raw list of transactions for the UI list view, hiding complex settlement data.
    """
    ledgers = db.query(VendorLedger).filter(
        VendorLedger.vendor_id == vendor_id,
        VendorLedger.vendor_type == vendor_type
    ).order_by(VendorLedger.created_at.desc()).limit(20).all()

    # We manually build the dict to hide internal tracking columns like platform_commission
    return [
        {
            "ledger_id": row.ledger_id,
            "order_id": row.order_id,
            "total_customer_paid": row.total_customer_paid,
            "vendor_earning": row.vendor_earning,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in ledgers
    ]
