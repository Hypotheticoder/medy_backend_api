import requests
import os
from db import SessionLocal
from models.order import Order
from models.pharma_shop import PharmaShopUser

db = SessionLocal()
order = db.query(Order).order_by(Order.created_at.desc()).first()
shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == order.shop_id).first()

CABY_BASE_URL = "http://192.168.0.222:8009/customer_orders"
headers = {
    "Authorization": "Bearer e0b3549686a40712c06a1eb60c13768076ce805d3aba2ac069a530ad4b61287a7"
}

caby_job_payload = {
    "order_type": "medicine",
    "vehicle_type": "parcel_bike", 
    "pickup_address": shop.address, 
    "pickup_lat": shop.latitude, 
    "pickup_lng": shop.longitude, 
    "pickup_contact_name": shop.shop_name, 
    "pickup_contact_phone": shop.phone_number,
    "drop_address": order.delivery_address,
    "drop_lat": order.delivery_lat,
    "drop_lng": order.delivery_lng,
    "drop_contact_name": order.customer_name or "Customer",
    "drop_contact_phone": order.customer_phone or "0000000000",
    "distance_km": 1.0, 
    "estimated_time_mins": 15,
    "payment_method": order.payment_mode or "cod",
    "item_count": len(order.items) if order.items else 1,
    "weight_kg": 1.0,
}

print(f"Payload: {caby_job_payload}")

try:
    response = requests.post(f"{CABY_BASE_URL}/create", json=caby_job_payload, headers=headers, timeout=10)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
