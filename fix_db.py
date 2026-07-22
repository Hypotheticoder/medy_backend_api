from db import SessionLocal
from models.order import Order
from models.pharma_shop import PharmaShopUser

db = SessionLocal()

# Reset the order so we can dispatch it again
order = db.query(Order).filter(Order.order_id.like("%F8DA962C%")).first()
if order:
    order.order_status = "packing"
    order.caby_order_id = None
    # Fix customer location to Kolkata
    order.delivery_lat = 22.4860
    order.delivery_lng = 88.3785
    order.delivery_address = "Customer Address in Kolkata"
    print(f"Order reset: {order.order_id}")
    
    # Fix shop location to Kolkata so the driver can see it
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == order.shop_id).first()
    if shop:
        shop.latitude = 22.4855
        shop.longitude = 88.3775
        print(f"Shop location updated to Kolkata: {shop.shop_id}")

    db.commit()
else:
    print("Order not found")
