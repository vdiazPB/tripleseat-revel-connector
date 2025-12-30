#!/usr/bin/env python3
"""
Test script to inject event 55521609 into JERA with full order details and items.
"""
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.supplyit.api_client import SupplyItAPIClient
from integrations.revel.injection import parse_invoice_for_items


def test_jera_injection():
    """Test injecting event 55521609 into JERA with items."""
    
    print("=" * 70)
    print("TEST: JERA/SUPPLY IT ORDER INJECTION")
    print("=" * 70)
    print()
    
    event_id = 55521609
    
    # Step 1: Fetch event from TripleSeat
    print("STEP 1: Fetching event from TripleSeat API")
    print("-" * 70)
    ts_client = TripleSeatAPIClient()
    event_data = ts_client.get_event(event_id)
    
    if not event_data:
        logger.error(f"Failed to fetch event {event_id}")
        return False
    
    event = event_data if isinstance(event_data, dict) else event_data.get('event', {})
    
    print(f"[OK] Event fetched: {event.get('name')}")
    print(f"   Date: {event.get('event_date')}")
    print(f"   Status: {event.get('status')}")
    print(f"   Total: ${event.get('grand_total', event.get('total', 0))}")
    print()
    
    # Step 2: Get items from event or invoice
    print("STEP 2: Extracting items from event")
    print("-" * 70)
    
    items = event.get('items', [])
    if not items:
        items = event_data.get('items', [])
    if not items:
        items = event.get('menu_items', [])
    
    # If no items, try parsing invoice
    if not items:
        print("No items in event data, checking for invoice document...")
        documents = event_data.get('documents', [])
        for doc in documents:
            views = doc.get('views', [])
            invoice_view = next((v for v in views if 'invoice' in v.get('name', '').lower()), None)
            if invoice_view:
                invoice_url = invoice_view.get('url')
                if invoice_url:
                    print(f"Found invoice, parsing: {invoice_url}")
                    items, invoice_guest_name = parse_invoice_for_items(invoice_url, "test")
                    if invoice_guest_name:
                        print(f"Extracted guest name from invoice: {invoice_guest_name}")
                    break
    
    print(f"Found {len(items)} items:")
    for item in items:
        if isinstance(item, dict):
            item_name = item.get('name', 'Unknown')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            print(f"  - {item_name} (Qty: {qty}, Price: ${price})")
        else:
            print(f"  - {item}")
    print()
    
    # Step 3: Connect to JERA/Supply It
    print("STEP 3: Connecting to JERA/Supply It")
    print("-" * 70)
    
    supplyit_client = SupplyItAPIClient()
    location = supplyit_client.get_location_by_code("8")
    
    if not location:
        logger.error("Could not find location code 8")
        return False
    
    location_id = location.get('ID')
    location_name = location.get('Name')
    
    print(f"[OK] Connected to location: {location_name} (ID: {location_id}, Code: 8)")
    print()
    
    # Step 4: Try to map items to JERA products
    print("STEP 4: Mapping items to JERA products")
    print("-" * 70)
    
    order_items = []
    for item in items:
        if isinstance(item, dict):
            item_name = item.get('name', 'Unknown')
            qty = float(item.get('quantity', 1))
            price = float(item.get('price', 0))
            
            # Try to find product in JERA
            product = supplyit_client.get_product_by_name(location_id, item_name)
            
            if product:
                product_id = product.get('ID')
                product_code = product.get('Code')
                print(f"[OK] Found: '{item_name}' -> Product ID {product_id} (Code: {product_code})")
                
                order_item = {
                    "Product": {
                        "ID": product_id,
                        "Code": product_code,
                        "Name": item_name
                    },
                    "UnitsOrdered": qty,
                    "UnitPrice": price if price > 0 else 1.00
                }
                order_items.append(order_item)
            else:
                print(f"[NOT FOUND] {item_name} - skipping")
    
    print()
    
    if not order_items:
        print("[ERROR] No items could be mapped to JERA products")
        print("    This is likely because TripleSeat item names don't match JERA product names")
        print()
        print("SUGGESTION: Check JERA product catalog and update item name mappings")
        return False
    
    # Step 5: Build and display order
    print("STEP 5: Order structure")
    print("-" * 70)
    
    # Format order items according to Supply It API spec
    order_items_formatted = [
        {
            "Product": {"ID": item['Product']['ID']},
            "StartingOrder": item['UnitsOrdered'],
            "UnitPrice": item.get('UnitPrice', 0)
        }
        for item in order_items
    ]
    
    order_data = {
        "Location": {
            "ID": location_id  # C: Special Events
        },
        "Contact": {
            "Code": "#c11"  # Supplier (#c11) that handles the order
        },
        "Shift": {
            "Code": "Production 01"  # Default production shift
        },
        "OrderDate": event.get('event_date_iso8601', datetime.now().date().isoformat()),
        "OrderItems": order_items_formatted,
        "OrderNotes": f"TripleSeat Event {event_id} - {event.get('name')}",
        "OrderStatus": "Open",
        "OrderViewType": "SalesOrder"  # Sales order through supplier to location
    }
    
    print(json.dumps(order_data, indent=2))
    print()
    
    # Step 6: Create order in JERA
    print("STEP 6: Creating order in JERA")
    print("-" * 70)
    
    try:
        result = supplyit_client.create_order(order_data, event_id)
        
        if result:
            print(f"[OK] Order created successfully!")
            print(f"   Order ID: {result.get('ID')}")
            print(f"   Status: {result.get('OrderStatus')}")
            print()
            return True
        else:
            print("[ERROR] Order creation failed")
            return False
            
    except Exception as e:
        logger.exception(f"Error creating order: {e}")
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    success = test_jera_injection()
    
    print()
    print("=" * 70)
    if success:
        print("[OK] TEST PASSED - Order successfully injected to JERA")
    else:
        print("[ERROR] TEST FAILED - See details above")
    print("=" * 70)
