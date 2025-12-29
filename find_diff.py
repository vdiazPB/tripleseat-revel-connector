#!/usr/bin/env python3
"""Deep comparison - save to files"""
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

# Working order vs new order
for order_id in ['10684118', '10685039']:
    url = f'{base_url}/resources/Order/{order_id}/'
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        order = resp.json()
        with open(f'order_{order_id}.json', 'w') as f:
            json.dump(order, f, indent=2)
        print(f"✅ Saved order_{order_id}.json")

# Now find differences
import json

with open('order_10684118.json') as f:
    working = json.load(f)
    
with open('order_10685039.json') as f:
    new = json.load(f)

print("\n" + "="*70)
print("DIFFERENCES BETWEEN WORKING (10684118) vs NEW (10685039)")
print("="*70)

all_keys = set(working.keys()) | set(new.keys())

for key in sorted(all_keys):
    w_val = working.get(key)
    n_val = new.get(key)
    
    if w_val != n_val:
        print(f"\n❌ {key}:")
        print(f"   WORKING:  {w_val}")
        print(f"   NEW:      {n_val}")
