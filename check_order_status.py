"""
Diagnostic: Check order status in Revel
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('REVEL_API_KEY')
api_secret = os.getenv('REVEL_API_SECRET')
domain = os.getenv('REVEL_DOMAIN')  # Already has .revelup.com
base_url = f"https://{domain}"

# Order ID from the test
order_id = "10678332"

headers = {
    'Authorization': f'ApiKey {api_key}:{api_secret}',
    'Content-Type': 'application/json'
}

# Check order status
url = f"{base_url}/resources/Order/{order_id}/"
response = requests.get(url, headers=headers)

print(f"URL: {url}")
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")
