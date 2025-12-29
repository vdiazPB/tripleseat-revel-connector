#!/usr/bin/env python3
"""Check Payment structure and order totals."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

order_id = 10683890

# Get payments for this order
resp = requests.get(f'{base_url}/resources/Payment/?order=/resources/Order/{order_id}/', headers=headers)
payments = resp.json()

print(f'\nPayments for Order {order_id}:')
print('=' * 70)

if payments.get('results'):
    for payment in payments.get('results', []):
        print(f'\nPayment ID: {payment.get("id")}')
        print(f'  Amount: ${payment.get("amount", 0):.2f}')
        print(f'  Payment Type: {payment.get("payment_type")}')
        print(json.dumps(payment, indent=2, default=str))
else:
    print('No payments found')

print('\n' + '=' * 70)
