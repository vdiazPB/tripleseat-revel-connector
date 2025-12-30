import os, requests
from dotenv import load_dotenv
load_dotenv()

headers = {'API-AUTHENTICATION': f"{os.getenv('REVEL_API_KEY')}:{os.getenv('REVEL_API_SECRET')}"}
base = f"https://{os.getenv('REVEL_DOMAIN')}"

o1 = requests.get(f"{base}/resources/Order/10684118/", headers=headers).json()
o2 = requests.get(f"{base}/resources/Order/10685204/", headers=headers).json()

print("Working Order (10684118):")
print(f"  created_by: {o1.get('created_by')}")
print(f"  opened: {o1.get('opened')}")
print(f"  closed: {o1.get('closed')}")
print(f"  printed: {o1.get('printed')}")

print("\nTest Order (10685204):")
print(f"  created_by: {o2.get('created_by')}")
print(f"  opened: {o2.get('opened')}")
print(f"  closed: {o2.get('closed')}")
print(f"  printed: {o2.get('printed')}")
