from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from db import get_db
from models.vendor_ledger import VendorLedger
from models.lab_booking import LabBooking
from models.order import Order

router = APIRouter(prefix="/api/rest/earnings", tags=["REST - Earnings Dashboard"])

def get_date_filter(period: str):
    now = datetime.utcnow()
    if period == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        return now - timedelta(days=7)
    elif period == 'month':
        return now - timedelta(days=30)
    return None

@router.get("/{vendor_type}/{vendor_id}/summary")
def get_earnings_summary(
    vendor_type: str, 
    vendor_id: str, 
    period: Optional[str] = Query("all"),
    db: Session = Depends(get_db)
):
    """
    Returns a simple, clean summary of total earnings.
    vendor_type should be 'lab' or 'pharmacy'.
    """
    query = db.query(VendorLedger).filter(
        VendorLedger.vendor_id == vendor_id,
        VendorLedger.vendor_type == vendor_type
    )

    date_filter = get_date_filter(period)
    if date_filter:
        query = query.filter(VendorLedger.created_at >= date_filter)

    ledgers = query.all()

    booking_modes = {}
    if vendor_type == "lab":
        bookings = db.query(LabBooking).filter(LabBooking.lab_id == vendor_id).all()
        booking_modes = {b.booking_id: (b.payment_mode or "cod").lower() for b in bookings}
    elif vendor_type == "pharmacy":
        orders = db.query(Order).filter(Order.shop_id == vendor_id).all()
        booking_modes = {o.order_id: (o.payment_mode or "cod").lower() for o in orders}

    total_earnings = 0.0
    amount_platform_owes_vendor = 0.0
    amount_vendor_owes_platform = 0.0

    for row in ledgers:
        total_earnings += row.vendor_earning
        payment_mode = booking_modes.get(row.order_id, "cod")
        
        if payment_mode == "online":
            amount_platform_owes_vendor += row.vendor_earning
        else: # cod
            amount_vendor_owes_platform += row.platform_commission

    net_balance = amount_platform_owes_vendor - amount_vendor_owes_platform

    return {
        "total_earnings": round(total_earnings, 2),
        "total_platform_owes_vendor": round(amount_platform_owes_vendor, 2),
        "total_vendor_owes_platform": round(amount_vendor_owes_platform, 2),
        "net_balance": round(net_balance, 2)
    }

@router.get("/{vendor_type}/{vendor_id}")
def get_recent_transactions(
    vendor_type: str, 
    vendor_id: str, 
    period: Optional[str] = Query("all"),
    db: Session = Depends(get_db)
):
    """
    Returns the raw list of transactions for the UI list view, hiding complex settlement data.
    """
    query = db.query(VendorLedger).filter(
        VendorLedger.vendor_id == vendor_id,
        VendorLedger.vendor_type == vendor_type
    )

    date_filter = get_date_filter(period)
    if date_filter:
        query = query.filter(VendorLedger.created_at >= date_filter)

    ledgers = query.order_by(VendorLedger.created_at.desc()).limit(50).all()

    booking_modes = {}
    if vendor_type == "lab":
        bookings = db.query(LabBooking).filter(LabBooking.lab_id == vendor_id).all()
        booking_modes = {b.booking_id: (b.payment_mode or "cod").lower() for b in bookings}
    elif vendor_type == "pharmacy":
        orders = db.query(Order).filter(Order.shop_id == vendor_id).all()
        booking_modes = {o.order_id: (o.payment_mode or "cod").lower() for o in orders}

    return [
        {
            "ledger_id": row.ledger_id,
            "order_id": row.order_id,
            "total_customer_paid": row.total_customer_paid,
            "vendor_earning": row.vendor_earning,
            "payment_mode": booking_modes.get(row.order_id, "cod"),
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in ledgers
    ]
