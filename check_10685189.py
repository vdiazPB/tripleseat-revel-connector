#!/usr/bin/env python3
import os, requests
from dotenv import load_dotenv
load_dotenv()

headers = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
base_url = f"https://{os.getenv('REVEL_DOMAIN')}"

order = requests.get(f"{base_url}/resources/Order/10685189/", headers=headers).json()

print(f"Order 10685189:")
print(f"  Created By: {order.get('created_by')}")
print(f"  Opened (field): {order.get('opened')}")
print(f"  Has OrderHistory: {order.get('has_history')}")
print(f"  OrderHistory: {order.get('orderhistory')}")
