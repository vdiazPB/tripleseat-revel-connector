#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

order = requests.get(f'{base_url}/resources/Order/10685150/', headers=headers).json()

print('ORDER 10685150:')
print(f"Created By: {order.get('created_by')}")
print(f"Discount Amount: ${order.get('discount_amount'):.2f}")
print(f"Has OrderHistory: {bool(order.get('orderhistory'))}")
