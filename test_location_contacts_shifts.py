#!/usr/bin/env python
import os
import requests
import json
from dotenv import load_dotenv

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

print("=" * 60)
print("FETCHING CONTACTS FOR LOCATION 8 (SPECIAL EVENTS)")
print("=" * 60)

response = requests.get(f"{BASE_URL}/contacts", headers=headers, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    contacts = response.json()
    print(f"Found {len(contacts)} contacts:")
    for idx, contact in enumerate(contacts[:5]):  # Show first 5
        print(f"\n  Contact {idx+1}:")
        print(f"    ID: {contact.get('ID')}")
        print(f"    Code: {contact.get('Code')}")
        print(f"    Name: {contact.get('Name')}")
        print(f"    ContactType: {contact.get('ContactType')}")
else:
    print(f"Error: {response.text}")

print("\n" + "=" * 60)
print("FETCHING SHIFTS FOR LOCATION 8 (SPECIAL EVENTS)")
print("=" * 60)

response = requests.get(f"{BASE_URL}/shifts", headers=headers, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    shifts = response.json()
    print(f"Found {len(shifts)} shifts:")
    for idx, shift in enumerate(shifts):
        print(f"\n  Shift {idx+1}:")
        print(f"    ID: {shift.get('ID')}")
        print(f"    Code: {shift.get('Code')}")
        print(f"    Name: {shift.get('Name')}")
else:
    print(f"Error: {response.text}")
