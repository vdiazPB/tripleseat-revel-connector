#!/usr/bin/env python3
"""Test invoice parsing to extract items"""

from dotenv import load_dotenv
from integrations.revel.injection import parse_invoice_for_items

load_dotenv()

# Invoice URL from the event
INVOICE_URL = "https://portal.tripleseat.com/doc/84b0295d467c5c1f859639005dba3d4d92289138/296467"

print(f"\nFetching and parsing invoice from: {INVOICE_URL}\n")

try:
    # Parse items directly from URL
    items, guest_name = parse_invoice_for_items(INVOICE_URL)
    
    print(f"Extracted {len(items)} items:")
    for item in items:
        print(f"  - {item['name']} x {item['quantity']}")
    
    print(f"\nExtracted Guest Name: {guest_name}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
