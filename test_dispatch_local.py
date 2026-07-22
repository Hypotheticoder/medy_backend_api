from db import SessionLocal
from models.order import Order

db = SessionLocal()
order = db.query(Order).filter(Order.order_id == "ORD-E102475A").first()
order.order_status = "packing"
order.caby_order_id = None
db.commit()
print("Reset ORD-E102475A to packing.")
