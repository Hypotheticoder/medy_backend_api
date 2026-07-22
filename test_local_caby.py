import requests
import os

CABY_BASE_URL = "http://192.168.0.222:8009/customer_orders"
headers = {
    "Authorization": "Bearer e0b3549686a40712c06a1eb60c13768076ce805d3aba2ac069a530ad4b61287a7"
}
caby_job_payload = {
    "order_type": "medicine",
    "vehicle_type": "parcel_bike",
    "pickup_address": "Test Shop", 
    "pickup_lat": 20.5937,
    "pickup_lng": 78.9629,
    "pickup_contact_name": "Shop Name",
    "pickup_contact_phone": "1234567890",
    "drop_address": "Test Drop",
    "drop_lat": 20.5938,
    "drop_lng": 78.9630,
    "drop_contact_name": "Customer Name",
    "drop_contact_phone": "0987654321",
    "distance_km": 1.0,
    "estimated_time_mins": 15,
    "payment_method": "cod",
    "item_count": 1,
    "weight_kg": 1.0,
}
try:
    response = requests.post(f"{CABY_BASE_URL}/create", json=caby_job_payload, headers=headers, timeout=10)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
