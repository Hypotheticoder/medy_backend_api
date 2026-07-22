import requests

payload = {
    "external_order_id": "95f5e880-3921-430a-830e-536d1f35a627",
    "driver_id": "drv_123",
    "driver_name": "Rohan the Fast Rider",
    "driver_phone": "9876543210"
}

headers = {
    "x-hub-secret": "90fd3c734a022b06fa5370d4c08720aa2e98d9b50c2f19b68cbdbee30ccf9d75"
}

print("Firing webhook to Caby Backend...")
response = requests.post("http://127.0.0.1:8009/webhooks/driver-assigned", json=payload, headers=headers)
print(f"Caby Response: {response.status_code} {response.text}")

