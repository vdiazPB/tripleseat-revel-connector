"""Test Revel API: explore order creation approaches."""
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import uuid

from integrations.revel.api_client import RevelAPIClient

client = RevelAPIClient()
headers = client._get_headers()

print("="*60)
print("APPROACH 1: Check OrderItem endpoint for adding items to order")
print("="*60)
# Maybe we need to create order first, then add items?
# Check if we can POST to OrderItem
url1 = f'{client.base_url}/resources/OrderItem/'
response1 = requests.options(url1, headers=headers)
print("OrderItem OPTIONS:", response1.status_code)
print("Allowed methods:", response1.headers.get('Allow', 'N/A'))

print("\n")
print("="*60)
print("APPROACH 2: Check if we can create empty order first")
print("="*60)
# Create minimal order
order_uuid = str(uuid.uuid4())
minimal_order = {
    'establishment': '/enterprise/Establishment/4/',
    'dining_option': 0,
    'pos_mode': 'Q',
}
url2 = f'{client.base_url}/resources/Order/'
response2 = requests.post(url2, headers=headers, json=minimal_order)
print("Create empty order:", response2.status_code)
print("Response:", response2.text[:500])

print("\n")
print("="*60)
print("APPROACH 3: Check OrderAllInOne with orderInfo structure")
print("="*60)
# Try with orderInfo wrapper
order_data = {
    'orderInfo': {
        'establishment': 4,
        'dining_option': 0,
        'notes': 'TripleSeat Test'
    },
    'items': [
        {
            'product': 505,
            'quantity': 1
        }
    ]
}
url3 = f'{client.base_url}/resources/OrderAllInOne/'
response3 = requests.post(url3, headers=headers, json=order_data)
print("OrderAllInOne with orderInfo:", response3.status_code)
print("Response:", response3.text[:500])

print("\n")
print("="*60)
print("APPROACH 4: Try different payload formats for Order")
print("="*60)
# Check if we need specific user/station references
url_users = f'{client.base_url}/enterprise/User/'
users_resp = requests.get(url_users, headers=headers, params={'limit': 5})
users = users_resp.json().get('objects', [])
print("Available users:")
for u in users[:3]:
    print(f"  ID {u.get('id')}: {u.get('email')}")

url_stations = f'{client.base_url}/resources/PosStation/'
stations_resp = requests.get(url_stations, headers=headers, params={'establishment': 4, 'limit': 5})
stations = stations_resp.json().get('objects', [])
print("\nPOS Stations for establishment 4:")
for s in stations[:3]:
    print(f"  ID {s.get('id')}: {s.get('name')}")

print("\n")
print("="*60)
print("APPROACH 5: Check external integrations endpoint")
print("="*60)
# List available special resources
endpoints = [
    '/specialresources/',
    '/webhooks/',
    '/enterprise/OrderSource/',
]
for ep in endpoints:
    url = f'{client.base_url}{ep}'
    resp = requests.get(url, headers=headers, params={'limit': 3})
    print(f"{ep}: {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f"  Keys: {list(data.keys())[:5]}")
        except:
            print(f"  Text: {resp.text[:100]}")
