"""Test Revel API: try order creation with ALL required fields."""
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import uuid
from datetime import datetime, timezone

from integrations.revel.api_client import RevelAPIClient

client = RevelAPIClient()
headers = client._get_headers()

print("="*60)
print("Creating order with ALL required fields")
print("="*60)

order_uuid = str(uuid.uuid4())
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

# Include ALL required fields
order_data = {
    'uuid': order_uuid,
    'establishment': '/enterprise/Establishment/4/',
    'created_by': '/enterprise/User/209/',
    'updated_by': '/enterprise/User/209/',
    'created_at': '/resources/PosStation/4/',
    'last_updated_at': '/resources/PosStation/4/',
    'created_date': now,
    'updated_date': now,
    'dining_option': 0,
    'pos_mode': 'Q',
    'notes': 'TripleSeat API Test',
    'web_order': True,
    # Required fields from error message:
    'final_total': 0,
    'tax': 0,
    'subtotal': 0,
    'remaining_due': 0,
    'surcharge': 0,
}

print("Order payload:")
print(json.dumps(order_data, indent=2))

url = f'{client.base_url}/resources/Order/'
response = requests.post(url, headers=headers, json=order_data)
print("\nCreate order response:")
print("Status:", response.status_code)
print("Response:", response.text[:2000])

if response.status_code in [200, 201]:
    order = response.json()
    order_id = order.get('id')
    order_uri = order.get('resource_uri')
    print(f"\n✅ Order created! ID: {order_id}, URI: {order_uri}")
    
    print("\n")
    print("="*60)
    print("Adding item to the order")
    print("="*60)
    
    item_uuid = str(uuid.uuid4())
    item_data = {
        'uuid': item_uuid,
        'order': order_uri,
        'product': '/resources/Product/505/',  # HOT COFFEE PREMIUM ROAST
        'quantity': 1,
        'price': 2.75,
        'created_by': '/enterprise/User/209/',
        'updated_by': '/enterprise/User/209/',
        'station': '/resources/PosStation/4/',
        'created_date': now,
        'updated_date': now,
        'tax_amount': 0,
        'modifier_amount': 0,
        'temp_sort': 0,
        'tax_rate': 0,
        'dining_option': 0,
    }
    
    print("Item payload:")
    print(json.dumps(item_data, indent=2))
    
    url_items = f'{client.base_url}/resources/OrderItem/'
    item_response = requests.post(url_items, headers=headers, json=item_data)
    print("\nAdd item response:")
    print("Status:", item_response.status_code)
    print("Response:", item_response.text[:1500])
else:
    print("\n❌ Failed to create order")
