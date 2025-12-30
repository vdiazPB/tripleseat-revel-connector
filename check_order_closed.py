#!/usr/bin/env python3
import requests
import hmac
import hashlib
import json
from integrations.revel.api_client import RevelAPIClient

# Initialize client
client = RevelAPIClient()

# Query the last order we created
order_id = '10685939'
url = f"{client.base_url}/resources/Order/{order_id}/"

# Get the order details
response = requests.get(url, headers=client._get_headers())

if response.status_code == 200:
    order = response.json()
    print("Order Details for ID 10685939:")
    print(json.dumps({
        'id': order.get('id'),
        'closed': order.get('closed'),
        'open': order.get('open'),
        'printed': order.get('printed'),
        'voided': order.get('voided'),
        'paid': order.get('paid'),
        'final_total': order.get('final_total'),
        'discount_amount': order.get('discount_amount'),
    }, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])
