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

# Check the order we just created
order_id = 6991166

response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=headers, timeout=10)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    order = response.json()
    print(f"Order ID: {order.get('ID')}")
    print(f"OrderViewType: {order.get('OrderViewType')}")
    print(f"OrderDate: {order.get('OrderDate')}")
    print(f"OrderStatus: {order.get('OrderStatus')}")
    print(f"Contact Code: {order.get('Contact', {}).get('Code')}")
    print(f"Contact Name: {order.get('Contact', {}).get('Name')}")
    print(f"Items: {len(order.get('OrderItems', []))}")
else:
    print(f"Error: {response.text}")
