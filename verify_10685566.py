import os, requests
from dotenv import load_dotenv
load_dotenv()

h = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
b = f"https://{os.getenv('REVEL_DOMAIN')}"

o = requests.get(f"{b}/resources/Order/10685566/", headers=h).json()
print(f"Order 10685566:")
print(f"  Closed: {o.get('closed')}")
print(f"  Call Name: {o.get('call_name')}")
