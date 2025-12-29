#!/usr/bin/env python3
"""Compare our created orders with real orders to identify missing fields."""

import os
import requests
import json
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

print("=" * 70)
print("COMPARING ORDER FIELDS")
print("=" * 70)

# Get our created order
our_order_id = '10683655'
url = f"{base_url}/resources/Order/{our_order_id}/"

print(f"\n📋 Our Order: {our_order_id}")
print("-" * 70)

response = requests.get(url, headers=headers)
our_order = response.json()

# Get a real order (from the past)
real_order_id = '280622'
url = f"{base_url}/resources/Order/{real_order_id}/"

print(f"\n📋 Real Order (for comparison): {real_order_id}")
print("-" * 70)

response = requests.get(url, headers=headers)
real_order = response.json()

# Compare key fields
key_fields = [
    'id', 'uuid', 'opened', 'closed', 'printed',
    'customer', 'table', 'bill_number', 'call_number',
    'created_date', 'updated_date', 'final_total', 'subtotal',
    'tax', 'payment_type', 'has_items', 'kitchen_status',
    'web_order', 'smart_order', 'is_invoice', 'is_readonly'
]

print("\n🔍 FIELD COMPARISON:\n")
print(f"{'Field':<25} {'Our Order':<30} {'Real Order':<30}")
print("-" * 85)

for field in key_fields:
    our_val = str(our_order.get(field, 'MISSING'))[:28]
    real_val = str(real_order.get(field, 'MISSING'))[:28]
    
    match = "✅" if our_val == real_val else "❌"
    print(f"{field:<25} {our_val:<30} {real_val:<30} {match}")

print("\n" + "=" * 70)
print("KEY DIFFERENCES:")
print("=" * 70)

differences = []
for field in key_fields:
    our_val = our_order.get(field)
    real_val = real_order.get(field)
    
    if our_val != real_val:
        differences.append((field, our_val, real_val))

for field, our_val, real_val in differences:
    print(f"\n🔴 {field}:")
    print(f"   Our order:  {our_val}")
    print(f"   Real order: {real_val}")

print("\n" + "=" * 70)
