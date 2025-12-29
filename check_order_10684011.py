#!/usr/bin/env python3
"""Check full details of order 10684011."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

resp = requests.get(f'{base_url}/resources/Order/10684061/', headers=headers)
order = resp.json()

print('\nOrder 10684061 - Key Fields:')
print('=' * 70)
print('subtotal: {}'.format(order.get('subtotal')))
print('discount_amount: {}'.format(order.get('discount_amount')))
print('final_total: {}'.format(order.get('final_total')))
print('is_discounted: {}'.format(order.get('is_discounted')))
print('remaining_due: {}'.format(order.get('remaining_due')))
print('discount field: {}'.format(order.get('discount')))
print()
print('Applied Discounts:')
for d in order.get('applied_discounts', []):
    print('  ID: {}'.format(d.get('id')))
    print('  Name: {}'.format(d.get('name')))
    print('  Amount: {}'.format(d.get('discount_amount')))
print('=' * 70)
