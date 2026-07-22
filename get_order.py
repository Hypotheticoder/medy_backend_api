from db import SessionLocal
from models.order import Order

db = SessionLocal()
order = db.query(Order).filter(Order.order_id == "ORD-24EB14A6").first()
print(f"Status: {order.order_status}, Caby ID: {order.caby_order_id}")
