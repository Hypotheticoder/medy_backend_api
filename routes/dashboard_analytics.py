from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta

from db import get_db
from models.lab_booking import LabBooking
from models.vendor_ledger import VendorLedger

router = APIRouter(prefix="/api/rest/dashboard", tags=["REST - Dashboard Analytics"])


@router.get("/lab/{lab_id}")
def get_lab_dashboard(lab_id: str, db: Session = Depends(get_db)):
    """
    Returns all dashboard analytics for a lab in a single call.
    """
    # --- All bookings for this lab ---
    bookings = db.query(LabBooking).filter(LabBooking.lab_id == lab_id).all()

    total_bookings = len(bookings)
    total_tests_done = 0
    for b in bookings:
        if isinstance(b.booked_tests, list):
            total_tests_done += len(b.booked_tests)

    # --- KPIs ---
    total_revenue = sum(b.total_price for b in bookings if b.booking_status not in ('cancelled',))
    avg_order_value = round(total_revenue / total_bookings, 2) if total_bookings > 0 else 0.0

    # Earnings from VendorLedger & Net Balance Calculation
    ledgers = db.query(VendorLedger).filter(
        VendorLedger.vendor_id == lab_id,
        VendorLedger.vendor_type == "lab"
    ).all()
    
    total_earnings = 0.0
    amount_platform_owes_lab = 0.0
    amount_lab_owes_platform = 0.0

    # Create a quick lookup for payment mode
    booking_modes = {b.booking_id: (b.payment_mode or "cod").lower() for b in bookings}

    for row in ledgers:
        total_earnings += row.vendor_earning
        payment_mode = booking_modes.get(row.order_id, "cod")
        
        if payment_mode == "online":
            amount_platform_owes_lab += row.vendor_earning
        else: # cod
            amount_lab_owes_platform += row.platform_commission

    net_balance = amount_platform_owes_lab - amount_lab_owes_platform

    kpis = {
        "total_bookings": total_bookings,
        "total_earnings": round(total_earnings, 2),
        "total_tests_done": total_tests_done,
        "avg_order_value": avg_order_value,
        "amount_platform_owes_lab": round(amount_platform_owes_lab, 2),
        "amount_lab_owes_platform": round(amount_lab_owes_platform, 2),
        "net_balance": round(net_balance, 2),
    }

    # --- Bookings by Status ---
    status_keys = ["pending", "accepted", "sample_collected", "processing", "report_ready", "completed", "cancelled"]
    bookings_by_status = {s: 0 for s in status_keys}
    for b in bookings:
        status = b.booking_status or "pending"
        if status in bookings_by_status:
            bookings_by_status[status] += 1
        else:
            bookings_by_status[status] = 1

    # --- Payment Mode Split ---
    payment_mode_split = {"cod": 0, "online": 0}
    for b in bookings:
        mode = (b.payment_mode or "cod").lower()
        if mode in payment_mode_split:
            payment_mode_split[mode] += 1
        else:
            payment_mode_split[mode] = 1

    # --- Earnings Trend (last 7 days) ---
    today = datetime.utcnow().date()
    seven_days_ago = today - timedelta(days=6)

    # Initialize all 7 days to 0
    trend_map = {}
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        trend_map[d.isoformat()] = 0.0

    for ledger in ledgers:
        if ledger.created_at:
            day_key = ledger.created_at.date().isoformat()
            if day_key in trend_map:
                trend_map[day_key] += ledger.vendor_earning

    earnings_trend = [{"date": k, "amount": round(v, 2)} for k, v in sorted(trend_map.items())]

    # --- Recent Bookings (last 5) ---
    recent = sorted(bookings, key=lambda b: b.created_at or datetime.min, reverse=True)[:5]
    recent_bookings = [
        {
            "booking_id": b.booking_id,
            "patient_name": b.patient_name,
            "total_price": b.total_price,
            "booking_status": b.booking_status,
            "payment_mode": b.payment_mode,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in recent
    ]

    return {
        "kpis": kpis,
        "bookings_by_status": bookings_by_status,
        "payment_mode_split": payment_mode_split,
        "earnings_trend": earnings_trend,
        "recent_bookings": recent_bookings,
    }
