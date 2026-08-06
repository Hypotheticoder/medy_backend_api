from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, extract
from datetime import datetime, timedelta

from db import get_db
from models.order import Order
from models.vendor_ledger import VendorLedger

router = APIRouter(prefix="/api/rest/dashboard", tags=["REST - Pharmacy Dashboard Analytics"])


@router.get("/pharmacy/{shop_id}")
def get_pharmacy_dashboard(shop_id: str, db: Session = Depends(get_db)):
    """
    Returns all dashboard analytics for a pharmacy shop in a single call.
    Queries the orders table and vendor_ledgers table.
    """
    # --- All orders for this shop ---
    orders = db.query(Order).filter(Order.shop_id == shop_id).all()

    total_orders = len(orders)

    # --- KPIs ---
    orders_delivered = sum(1 for o in orders if o.order_status == "delivered")
    orders_cancelled = sum(1 for o in orders if o.order_status in ("cancelled", "rejected"))
    pending_orders = sum(1 for o in orders if o.order_status in ("bidding", "packing", "checkout_pending", "finding_driver", "driver_assigned"))
    active_orders = sum(1 for o in orders if o.order_status in ("packing", "out_for_delivery", "finding_driver", "driver_assigned"))

    total_revenue = sum(o.total_bill_amount for o in orders if o.order_status not in ("cancelled", "rejected", "bidding"))
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # Earnings from VendorLedger
    ledgers = db.query(VendorLedger).filter(
        VendorLedger.vendor_id == shop_id,
        VendorLedger.vendor_type == "pharmacy"
    ).all()

    total_earnings = sum(row.vendor_earning for row in ledgers)
    platform_owes_shop = 0.0
    shop_owes_platform = 0.0

    order_payment_modes = {o.order_id: (o.payment_mode or "cod").lower() for o in orders}

    for row in ledgers:
        payment_mode = order_payment_modes.get(row.order_id, "cod")
        if payment_mode == "online":
            platform_owes_shop += row.vendor_earning
        else:
            shop_owes_platform += row.platform_commission

    net_balance = platform_owes_shop - shop_owes_platform

    kpis = {
        "total_orders": total_orders,
        "total_earnings": round(total_earnings, 2),
        "total_revenue": round(total_revenue, 2),
        "orders_delivered": orders_delivered,
        "orders_cancelled": orders_cancelled,
        "pending_orders": pending_orders,
        "active_orders": active_orders,
        "avg_order_value": avg_order_value,
        "platform_owes_shop": round(platform_owes_shop, 2),
        "shop_owes_platform": round(shop_owes_platform, 2),
        "net_balance": round(net_balance, 2),
    }

    # --- Orders by Status ---
    status_keys = ["bidding", "checkout_pending", "packing", "finding_driver",
                   "driver_assigned", "out_for_delivery", "delivered", "cancelled", "rejected"]
    orders_by_status = {s: 0 for s in status_keys}
    for o in orders:
        status = o.order_status or "bidding"
        if status in orders_by_status:
            orders_by_status[status] += 1
        else:
            orders_by_status[status] = 1

    # --- Payment Mode Split ---
    payment_mode_split = {"cod": 0, "online": 0}
    for o in orders:
        mode = (o.payment_mode or "cod").lower()
        if mode in payment_mode_split:
            payment_mode_split[mode] += 1
        else:
            payment_mode_split[mode] = 1

    # --- Order Type Split ---
    order_type_split = {"cart": 0, "prescription": 0}
    for o in orders:
        otype = (o.order_type or "cart").lower()
        if otype in order_type_split:
            order_type_split[otype] += 1
        else:
            order_type_split[otype] = 1

    # --- Earnings Trend (last 7 days) ---
    today = datetime.utcnow().date()
    seven_days_ago = today - timedelta(days=6)

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

    # --- Hourly Order Distribution (all time, 0-23) ---
    hourly_dist = {h: 0 for h in range(24)}
    for o in orders:
        if o.created_at:
            hourly_dist[o.created_at.hour] += 1

    hourly_order_distribution = [{"hour": h, "count": c} for h, c in sorted(hourly_dist.items())]

    # --- Recent Orders (last 5) ---
    recent = sorted(orders, key=lambda o: o.created_at or datetime.min, reverse=True)[:5]
    recent_orders = [
        {
            "order_id": o.order_id,
            "receiver_name": o.receiver_name,
            "total_bill_amount": o.total_bill_amount,
            "order_status": o.order_status,
            "order_type": o.order_type,
            "payment_mode": o.payment_mode,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in recent
    ]

    return {
        "kpis": kpis,
        "orders_by_status": orders_by_status,
        "payment_mode_split": payment_mode_split,
        "order_type_split": order_type_split,
        "earnings_trend": earnings_trend,
        "hourly_order_distribution": hourly_order_distribution,
        "recent_orders": recent_orders,
    }
