#!/usr/bin/env python3
"""Test opening/activating orders in Revel."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('REVEL_API_KEY')
api_secret = os.getenv('REVEL_API_SECRET')
domain = os.getenv('REVEL_DOMAIN', 'pinkboxdoughnuts.revelup.com')

base_url = f"https://{domain}"
headers = {
    'API-AUTHENTICATION': f'{api_key}:{api_secret}',
    'Content-Type': 'application/json'
}

order_ids = ['10683655', '10683658']

print("=" * 70)
print("OPENING ORDERS IN REVEL")
print("=" * 70)

for order_id in order_ids:
    print(f"\n📋 Opening Order: {order_id}")
    
    url = f"{base_url}/resources/Order/{order_id}/"
    
    # Try with opened = True
    data = {'opened': True}
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 202]:
            print(f"   ✅ Successfully marked order as opened")
            
            # Verify
            check = requests.get(url, headers=headers)
            if check.status_code == 200:
                order = check.json()
                print(f"   Verified - opened flag is now: {order.get('opened')}")
        else:
            print(f"   ❌ Failed")
            print(f"   Response: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
