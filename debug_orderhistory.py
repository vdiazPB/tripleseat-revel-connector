#!/usr/bin/env python3
import os, requests
from dotenv import load_dotenv
load_dotenv()

headers = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
base_url = f"https://{os.getenv('REVEL_DOMAIN')}"

order = requests.get(f"{base_url}/resources/Order/10685155/", headers=headers).json()

print(f"Order 10685155:")
print(f"  Has OrderHistory: {order.get('has_history')}")
print(f"  OrderHistory Records: {order.get('orderhistory')}")
print(f"  Closed: {order.get('closed')}")
print(f"  Opened: {order.get('opened')}")
print()

if order.get('orderhistory'):
    for oh_uri in order.get('orderhistory', []):
        print(f"Fetching OrderHistory: {oh_uri}")
        oh = requests.get(f"{base_url}{oh_uri}", headers=headers).json()
        print(f"  ID: {oh.get('id')}")
        print(f"  Opened: {oh.get('opened')}")
        print(f"  Closed: {oh.get('closed')}")
        print(f"  Order: {oh.get('order')}")
else:
    print("No OrderHistory records found!")
