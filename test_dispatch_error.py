import os
from db import SessionLocal
from models.order import Order
from models.pharma_shop import PharmaShopUser
import requests

db = SessionLocal()
order_id = "ORD-24EB14A6"
order = db.query(Order).filter(Order.order_id == order_id).first()
shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == order.shop_id).first()

caby_job_payload = {
    "order_type": "medicine",
    "vehicle_type": "parcel_bike", 
    "pickup_address": shop.address, 
    "pickup_lat": shop.latitude, 
    "pickup_lng": shop.longitude, 
    "pickup_contact_name": shop.shop_name, 
    "pickup_contact_phone": shop.phone,    
    "drop_address": order.delivery_address,
    "drop_lat": order.delivery_lat,
    "drop_lng": order.delivery_lng,
    "drop_contact_name": order.receiver_name,
    "drop_contact_phone": order.receiver_phone,
    "distance_km": order.distance_km,
    "estimated_time_mins": 15,
    "payment_method": order.payment_mode,
    "item_count": len(order.items) if order.items else 1,
    "weight_kg": 1.0,
}

headers = {
    "Authorization": "Bearer e0b3549686a40712c06a1eb60c13768076ce805d3aba2ac069a530ad4b61287a7"
}

caby_url = os.getenv("CABY_BASE_URL", "http://192.168.0.222:8009/customer_orders")
print(f"URL: {caby_url}")
try:
    response = requests.post(f"{caby_url}/create", json=caby_job_payload, headers=headers, timeout=3)
    response.raise_for_status()
    print("Success:", response.json())
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'response') and e.response is not None:
        print("Response text:", e.response.text)
