#!/usr/bin/env python3
"""Check the structure of OrderHistory record to understand what we need to create"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')
REVEL_DOMAIN = os.getenv('REVEL_DOMAIN')

base_url = f'https://{REVEL_DOMAIN}'
headers = {
    'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'
}

# Get the OrderHistory record from working order 10684118
order_history_uri = '/resources/OrderHistory/6765269/'
url = f'{base_url}{order_history_uri}'

resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}\n")

if resp.status_code == 200:
    oh = resp.json()
    print("OrderHistory Record Structure:")
    print(json.dumps(oh, indent=2))
