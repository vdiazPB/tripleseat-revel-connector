#!/usr/bin/env python
import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

JERA_API_KEY = os.getenv('JERA_API_KEY')
JERA_API_USERNAME = os.getenv('JERA_API_USERNAME')
BASE_URL = "https://app.supplyit.com/api/v2"
LOCATION_CODE = "8"  # Special Events

headers = {
    'Authorization': JERA_API_KEY,
    'X-Api-User': JERA_API_USERNAME,
    'X-Supplyit-LocationCode': LOCATION_CODE,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

print("=" * 70)
print("CHECKING EXISTING ORDERS IN SPECIAL EVENTS (LOCATION CODE 8)")
print("=" * 70)

# Get recent orders
today = datetime.now().date().isoformat()
response = requests.get(f"{BASE_URL}/orders?date={today}", headers=headers, timeout=10)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    orders = response.json()
    if orders:
        print(f"\nFound {len(orders)} orders for today ({today}):")
        for idx, order in enumerate(orders[:3]):  # Show first 3
            print(f"\n--- Order {idx+1} ---")
            print(f"Order ID: {order.get('ID')}")
            print(f"Order Date: {order.get('OrderDate')}")
            print(f"Status: {order.get('OrderStatus')}")
            
            contact = order.get('Contact', {})
            print(f"\nContact Details:")
            print(f"  Contact ID: {contact.get('ID')}")
            print(f"  Contact Code: {contact.get('Code')}")
            print(f"  Contact Name: {contact.get('Name')}")
            
            contact_loc = contact.get('ContactLocation', {})
            print(f"  ContactLocation ID: {contact_loc.get('ID')}")
            print(f"  ContactLocation Code: {contact_loc.get('Code')}")
            print(f"  ContactLocation Name: {contact_loc.get('Name')}")
            
            shift = order.get('Shift', {})
            print(f"\nShift Details:")
            print(f"  Shift ID: {shift.get('ID')}")
            print(f"  Shift Code: {shift.get('Code')}")
            print(f"  Shift Name: {shift.get('Name')}")
            
            print(f"\nOrder Items: {len(order.get('OrderItems', []))} items")
    else:
        print("\nNo orders found for today. Checking last 7 days...")
        # Try last week
        for days_back in range(1, 8):
            date_to_check = (datetime.now() - timedelta(days=days_back)).date().isoformat()
            response = requests.get(f"{BASE_URL}/orders?date={date_to_check}", headers=headers, timeout=10)
            if response.status_code == 200:
                orders = response.json()
                if orders:
                    print(f"\nFound {len(orders)} orders on {date_to_check}:")
                    for idx, order in enumerate(orders[:2]):  # Show first 2
                        print(f"\n--- Order {idx+1} ---")
                        print(f"Order ID: {order.get('ID')}")
                        print(f"Order Date: {order.get('OrderDate')}")
                        
                        contact = order.get('Contact', {})
                        print(f"\nContact:")
                        print(f"  ID: {contact.get('ID')}")
                        print(f"  Code: {contact.get('Code')}")
                        print(f"  Name: {contact.get('Name')}")
                        
                        shift = order.get('Shift', {})
                        print(f"\nShift:")
                        print(f"  Code: {shift.get('Code')}")
                        print(f"  Name: {shift.get('Name')}")
                    break
else:
    print(f"Error: {response.text}")
