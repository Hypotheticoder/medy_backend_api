from db import SessionLocal
from models.order import Order

db = SessionLocal()
orders = db.query(Order).order_by(Order.created_at.desc()).limit(3).all()
for order in orders:
    order.order_status = "packing"
    order.caby_order_id = None
    # Ensure they have valid locations so they show up for the Kolkata driver
    order.delivery_lat = 22.4860
    order.delivery_lng = 88.3785
    print(f"Reset order {order.order_id} to packing")

db.commit()
