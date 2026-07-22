from db import SessionLocal
from models.order import Order
from models.pharma_shop import PharmaShopUser

db = SessionLocal()
order = db.query(Order).filter(Order.order_id.like("%F8DA962C%")).first()
if order:
    print(f"Order: {order.order_id}, lat: {order.delivery_lat}, lng: {order.delivery_lng}, address: {order.delivery_address}, shop: {order.shop_id}")
    if order.shop_id:
        shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == order.shop_id).first()
        if shop:
            print(f"Shop: {shop.shop_id}, lat: {shop.latitude}, lng: {shop.longitude}")
        else:
            print("Shop not found in db")
else:
    print("Order not found")
