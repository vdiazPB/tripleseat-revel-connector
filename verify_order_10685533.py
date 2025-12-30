import os, requests
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

o = requests.get(f"{b}/resources/Order/10685533/", headers=h).json()
print(f"Order 10685533:")
print(f"  Call Name: {o.get('call_name')}")
print(f"  Call Number: {o.get('call_number')}")
print(f"  Notes: {o.get('notes')}")
