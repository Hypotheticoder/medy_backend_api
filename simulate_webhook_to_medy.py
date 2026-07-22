import requests

payload = {
    "caby_order_id": "95f5e880-3921-430a-830e-536d1f35a627",
    "driver_id": "drv_123",
    "driver_name": "Rohan the Fast Rider",
    "driver_phone": "9876543210"
}

print("Firing webhook to Medy Backend...")
response = requests.post("http://127.0.0.1:8000/api/rest/orders/webhook/caby-driver-update", json=payload)
print(f"Medy Response: {response.status_code} {response.text}")

