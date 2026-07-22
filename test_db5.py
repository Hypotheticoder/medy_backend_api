from db import SessionLocal
from models.order import Order

db = SessionLocal()
order = db.query(Order).filter(Order.order_id.like("%F8DA962C%")).first()
if order:
    print(f"Order: {order.order_id}, status: {order.order_status}, caby_tracking_id: {order.caby_order_id}")
else:
    print("Order not found")
