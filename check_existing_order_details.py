#!/usr/bin/env python
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JERA_API_KEY = os.getenv('JERA_API_KEY')
JERA_API_USERNAME = os.getenv('JERA_API_USERNAME')
BASE_URL = "https://app.supplyit.com/api/v2"
LOCATION_CODE = "8"

headers = {
    'Authorization': JERA_API_KEY,
    'X-Api-User': JERA_API_USERNAME,
    'X-Supplyit-LocationCode': LOCATION_CODE,
    'Accept': 'application/json'
}

# Check the order we just created with contact code 10
order_id = 6991166

print("=" * 80)
print(f"CHECKING EXISTING ORDER {order_id} FROM SPECIAL EVENTS")
print("=" * 80)

response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=headers, timeout=10)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    order = response.json()
    print(json.dumps(order, indent=2))
else:
    print(f"Error: {response.text}")
