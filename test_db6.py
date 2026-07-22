from db import SessionLocal
from models.order import Order

db = SessionLocal()
orders = db.query(Order).order_by(Order.created_at.desc()).limit(3).all()
for order in orders:
    print(f"Order: {order.order_id}, status: {order.order_status}, caby: {order.caby_order_id}")
