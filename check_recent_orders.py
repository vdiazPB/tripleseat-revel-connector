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

# Get orders - try with a specific date
today = datetime.now().date()
event_date = datetime(2025, 12, 28).date()  # Event date

print("=" * 80)
print(f"FETCHING ORDERS FROM SPECIAL EVENTS LOCATION (Code 8)")
print(f"Date: {event_date}")
print("=" * 80)

# Try fetching orders for the event date
response = requests.get(f"{BASE_URL}/orders?date={event_date.isoformat()}", headers=headers, timeout=10)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    orders = response.json()
    print(f"Found {len(orders)} orders total\n")
    
    # Show details of the most recent orders
    if orders:
        # Sort by date (most recent first)
        orders_sorted = sorted(orders, key=lambda x: x.get('OrderDate', ''), reverse=True)
        
        print("RECENT ORDERS (up to 5):")
        print("=" * 80)
        
        for idx, order in enumerate(orders_sorted[:5]):
            print(f"\nOrder {idx+1}:")
            print(f"  ID: {order.get('ID')}")
            print(f"  Date: {order.get('OrderDate')}")
            print(f"  Status: {order.get('OrderStatus')}")
            print(f"  ViewType: {order.get('OrderViewType')}")
            
            contact = order.get('Contact', {})
            print(f"  Contact:")
            print(f"    ID: {contact.get('ID')}")
            print(f"    Name: {contact.get('Name')}")
            print(f"    Code: {contact.get('Code')}")
            print(f"    ContactType: {contact.get('ContactType')}")
            
            contact_location = contact.get('ContactLocation', {})
            if contact_location:
                print(f"    ContactLocation:")
                print(f"      ID: {contact_location.get('ID')}")
                print(f"      Code: {contact_location.get('Code')}")
                print(f"      Name: {contact_location.get('Name')}")
            
            shift = order.get('Shift', {})
            print(f"  Shift:")
            print(f"    ID: {shift.get('ID')}")
            print(f"    Code: {shift.get('Code')}")
            print(f"    Name: {shift.get('Name')}")
            
            items = order.get('OrderItems', [])
            print(f"  Items: {len(items)}")
            if items:
                print(f"    First item: {items[0].get('Product', {}).get('Name')} x{items[0].get('UnitsOrdered')}")
            
            print(f"  Notes: {order.get('OrderNotes', '(none)')[:60]}")
else:
    print(f"Error: {response.status_code}")
    print(f"Response: {response.text}")
