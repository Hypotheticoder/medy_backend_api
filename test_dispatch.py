from db import SessionLocal
from models.order import Order

db = SessionLocal()
order = db.query(Order).filter(Order.order_id == "ORD-24EB14A6").first()
if order:
    order.order_status = "packing"
    order.caby_order_id = None
    db.commit()
    print("Order reset to packing.")
