#!/usr/bin/env python3
"""Check the state of the newest orders"""
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

for order_id in [10684998, 10684977, 10684118]:
    print(f"\n{'='*60}")
    print(f"ORDER {order_id}")
    print('='*60)
    
    url = f'{base_url}/resources/Order/{order_id}/'
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        order = resp.json()
        print(f"  Opened:       {order.get('opened')}")
        print(f"  Closed:       {order.get('closed')}")
        print(f"  Printed:      {order.get('printed')}")
        print(f"  Web Order:    {order.get('web_order')}")
        print(f"  Status:       {order.get('status')}")
        print(f"  Subtotal:     {order.get('subtotal')}")
        print(f"  Discount:     {order.get('discount_amount')}")
        print(f"  Final Total:  {order.get('final_total')}")
        print(f"  Dining Option: {order.get('dining_option')}")
        print(f"  Created By:   {order.get('created_by')}")
