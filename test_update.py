import asyncio
import os
import requests

# Assuming local backend
res = requests.get("http://localhost:8000/")
print("Backend status:", res.status_code)
