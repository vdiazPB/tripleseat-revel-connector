#!/usr/bin/env python3
import os, requests
from dotenv import load_dotenv
load_dotenv()

headers = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
order = requests.get(f"https://{os.getenv('REVEL_DOMAIN')}/resources/Order/10685155/", headers=headers).json()
print(f"Created By: {order.get('created_by')}")
print(f"Discount: ${order.get('discount_amount'):.2f}")
print(f"Has OrderHistory: {bool(order.get('orderhistory'))}")
