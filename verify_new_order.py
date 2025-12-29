#!/usr/bin/env python3
"""Verify the new order has correct amounts."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
REVEL_API_KEY = os.getenv('REVEL_API_KEY')
REVEL_API_SECRET = os.getenv('REVEL_API_SECRET')

base_url = 'https://pinkboxdoughnuts.revelup.com'
headers = {'API-AUTHENTICATION': f'{REVEL_API_KEY}:{REVEL_API_SECRET}'}

order_id = 10683848
resp = requests.get(f'{base_url}/resources/Order/{order_id}/', headers=headers)
order = resp.json()

print(f'\nOrder {order_id} Verification:')
print('=' * 70)
print('Subtotal:        ${:.2f}'.format(order.get('subtotal', 0)))
print('Discount Amount: -${:.2f}'.format(order.get('discount_amount', 0)))
print('Final Total:     ${:.2f}'.format(order.get('final_total', 0)))
print('Closed:          {}'.format(order.get('closed')))
print('Printed:         {}'.format(order.get('printed')))
print('=' * 70)

# Check expected values
expected_subtotal = 62.97
expected_discount = 10.00
expected_final = 52.97

subtotal_ok = abs(order.get('subtotal', 0) - expected_subtotal) < 0.01
discount_ok = abs(order.get('discount_amount', 0) - expected_discount) < 0.01
final_ok = abs(order.get('final_total', 0) - expected_final) < 0.01

if subtotal_ok and discount_ok and final_ok:
    print('\n✅ CORRECT - All values match!\n')
else:
    print('\n❌ MISMATCH')
    print('  Expected subtotal ${:.2f}, got ${:.2f}'.format(expected_subtotal, order.get('subtotal', 0)))
    print('  Expected discount ${:.2f}, got ${:.2f}'.format(expected_discount, order.get('discount_amount', 0)))
    print('  Expected final ${:.2f}, got ${:.2f}\n'.format(expected_final, order.get('final_total', 0)))
