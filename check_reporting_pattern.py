import os, requests
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

# Get multiple recent orders to see reporting_id pattern
orders = requests.get(f"{b}/resources/Order/", headers=h, params={
    'limit': 10, 
    'ordering': '-id',
    'establishment__id': '4'  # Our establishment
}).json()

print("Recent orders and their reporting_id:")
for order in orders.get('results', []):
    print(f"  Order {order.get('id')}: reporting_id={order.get('reporting_id')}, closed={order.get('closed')}")
