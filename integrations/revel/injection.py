import logging
import os
import re
import requests
from typing import List, Dict, Any, Optional
from html import unescape
from integrations.revel.api_client import RevelAPIClient
from integrations.revel.mappings import get_revel_establishment, get_dining_option_id, get_payment_type_id, get_discount_id
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.models import InjectionResult, OrderDetails

logger = logging.getLogger(__name__)


def parse_invoice_for_items(invoice_url: str, correlation_id: str = None) -> List[Dict[str, Any]]:
    """Fetch and parse TripleSeat invoice HTML to extract line items.
    
    Looks for table rows matching pattern: Qty Description Price Total
    Extracts product name before the " - " delimiter (description separator)
    
    Returns:
        List of dicts with 'name' and 'quantity' keys
    """
    req_id = f"[req-{correlation_id}]" if correlation_id else ""
    
    try:
        logger.info(f"{req_id} Fetching invoice from: {invoice_url}")
        response = requests.get(invoice_url, timeout=15)
        
        if response.status_code != 200:
            logger.warning(f"{req_id} Invoice fetch failed: HTTP {response.status_code}")
            return []
        
        # Extract table rows
        tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', response.text, re.DOTALL | re.IGNORECASE)
        
        # Function to extract clean text from HTML
        def extract_text(html_str):
            text = re.sub(r'<[^>]+>', '', html_str)
            text = unescape(text)
            text = ' '.join(text.split())
            return text.strip()
        
        items = []
        in_items_section = False
        
        for row in tr_matches:
            text = extract_text(row)
            
            # Check for header row "Qty. Qty Description Price Total"
            if 'qty' in text.lower() and 'description' in text.lower() and 'price' in text.lower():
                in_items_section = True
                logger.info(f"{req_id} Found invoice items section")
                continue
            
            # Stop when we hit the totals section
            if in_items_section and any(keyword in text.lower() for keyword in ['subtotal', 'food (', 'description percent']):
                break
            
            # Parse item rows: "8 ITEM NAME - DESCRIPTION $price $total"
            if in_items_section and text and '$' in text:
                # Split by $ to isolate the description
                parts = text.split('$')
                if len(parts) >= 3:  # Should have qty+name, price, total
                    try:
                        qty_and_name = parts[0].strip()
                        # Extract quantity from start
                        qty_match = re.match(r'^(\d+)\s+(.+)', qty_and_name)
                        if qty_match:
                            qty = int(qty_match.group(1))
                            full_name = qty_match.group(2).strip()
                            
                            # Extract product name before " - " separator
                            # If there's a " - ", use text before it; otherwise use full name
                            if ' - ' in full_name:
                                name = full_name.split(' - ')[0].strip()
                            else:
                                name = full_name
                            
                            if name and qty > 0:
                                items.append({'name': name, 'quantity': qty})
                                logger.info(f"{req_id} Parsed item: {name} x{qty} (full: {full_name})")
                    except Exception as e:
                        logger.warning(f"{req_id} Failed to parse item row: {text[:100]} - {e}")
        
        logger.info(f"{req_id} Extracted {len(items)} items from invoice")
        return items
        
    except Exception as e:
        logger.error(f"{req_id} Error parsing invoice: {e}")
        return []



def resolve_line_items(
    revel_client: RevelAPIClient,
    establishment: str,
    tripleseat_items: List[Dict[str, Any]],
    correlation_id: str
) -> List[Dict[str, Any]]:
    """
    Resolve TripleSeat line items to Revel product IDs by exact name match.
    Returns list of Revel order items for matched products only.
    """
    resolved_items = []
    
    for ts_item in tripleseat_items:
        item_name = ts_item.get('name', '').strip()
        quantity = ts_item.get('quantity', 1)
        
        if not item_name:
            logger.warning(f"[req-{correlation_id}] Skipping item with empty name")
            continue
        
        logger.info(f"[req-{correlation_id}] [ITEM RESOLUTION] Attempting: '{item_name}' x{quantity}")
        
        # Resolve product by exact name match
        product = revel_client.resolve_product_by_name(establishment, item_name)
        
        if product:
            product_id = product.get('id')
            # Use Triple Seat price if available, otherwise fall back to Revel product price
            ts_price = float(ts_item.get('price', 0))
            revel_price = product.get('price', product.get('cost', 0))
            final_price = ts_price if ts_price > 0 else revel_price
            
            resolved_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': final_price
            })
            logger.info(f"[req-{correlation_id}] [ITEM RESOLVED] '{item_name}' → product_id={product_id}, qty={quantity}, ts_price=${ts_price}, revel_price=${revel_price}, final_price=${final_price}")
        else:
            logger.warning(f"[req-{correlation_id}] [ITEM SKIPPED] '{item_name}' not found in Revel – skipping")
    
    return resolved_items


def inject_order(
    event_id: str,
    correlation_id: str = None,
    dry_run: bool = True,
    enable_connector: bool = True,
    test_location_override: bool = False,
    test_establishment_id: str = "4",
    webhook_payload: Dict[str, Any] = None
) -> InjectionResult:
    """Inject Triple Seat event into Revel POS.
    
    Args:
        webhook_payload: Optional webhook payload. If provided, uses this data directly
                        instead of fetching from TripleSeat API (more efficient).
    """
    
    external_order_id = f"Triple Seat {event_id}"

    # Always fetch full event details from API to get line items/invoice data
    # (webhook payload only has basic event info)
    logger.info(f"[req-{correlation_id}] Fetching full event data from TripleSeat API (for items/invoice)")
    ts_client = TripleSeatAPIClient()
    event_data = ts_client.get_event(event_id)
    if not event_data:
        logger.error(f"[req-{correlation_id}] Failed to fetch event data for event_id={event_id}")
        return InjectionResult(False, error="Failed to fetch event data")

    event = event_data.get("event", {})
    site_id = event.get("site_id")
    booking_id = event.get("booking_id")

    # Determine establishment (TEST MODE OVERRIDE)
    if test_location_override:
        establishment = test_establishment_id
        logger.warning(f"[req-{correlation_id}] Location override ACTIVE – using establishment {establishment} (ignoring site_id={site_id})")
    else:
        establishment = get_revel_establishment(site_id)
        if not establishment:
            return InjectionResult(False, error=f"No Revel establishment mapped for site {site_id}")

    revel_client = RevelAPIClient()

    # Check idempotency
    existing_order = revel_client.get_order(external_order_id, establishment)
    if existing_order:
        logger.info(f"[req-{correlation_id}] Order {external_order_id} already exists – skipping")
        return InjectionResult(True)  # Exit safely

    # Get billing data
    documents = event_data.get("documents", [])
    billing_invoice = next((doc for doc in documents if doc.get("type") == "billing_invoice"), None)
    
    # Extract line items from event data
    tripleseat_items = event_data.get("items", [])
    # Also check for menu_items in the event structure
    if not tripleseat_items:
        tripleseat_items = event.get("menu_items", [])
    if not tripleseat_items:
        tripleseat_items = event_data.get("menu_items", [])
    
    # If no items found, try fetching from booking (TripleSeat stores items in custom fields)
    if not tripleseat_items and booking_id:
        logger.info(f"[req-{correlation_id}] No items in event, checking booking {booking_id}")
        booking_url = f"{ts_client.base_url}/v1/bookings/{booking_id}"
        try:
            booking_response = ts_client.session.get(booking_url, timeout=10)
            if booking_response.status_code == 200:
                booking_data = booking_response.json()
                booking_obj = booking_data.get('booking', {})
                custom_fields = booking_obj.get('custom_fields', [])
                
                # Look for Boxing/Packing Slip custom field which contains the item name
                packing_slip = next((cf for cf in custom_fields if 'packing' in cf.get('custom_field_name', '').lower() or 'boxing' in cf.get('custom_field_name', '').lower()), None)
                
                if packing_slip and packing_slip.get('value'):
                    item_name = packing_slip.get('value').strip()
                    logger.info(f"[req-{correlation_id}] Found item in custom field: {item_name}")
                    tripleseat_items = [{'name': item_name, 'quantity': 1}]
        except Exception as e:
            logger.warning(f"[req-{correlation_id}] Failed to fetch booking details: {e}")
    
    # If still no items, try parsing invoice document
    if not tripleseat_items and documents:
        logger.info(f"[req-{correlation_id}] No items found, attempting to parse invoice document")
        # Find invoice document and its view URL
        for doc in documents:
            views = doc.get('views', [])
            invoice_view = next((v for v in views if 'invoice' in v.get('name', '').lower()), None)
            if invoice_view:
                invoice_url = invoice_view.get('url')
                if invoice_url:
                    tripleseat_items = parse_invoice_for_items(invoice_url, correlation_id)
                    if tripleseat_items:
                        logger.info(f"[req-{correlation_id}] Successfully extracted {len(tripleseat_items)} items from invoice")
                        break
    
    logger.info(f"[req-{correlation_id}] Found {len(tripleseat_items)} line items in TripleSeat event")

    # Resolve line items to Revel products
    resolved_items = resolve_line_items(revel_client, establishment, tripleseat_items, correlation_id)
    
    logger.info(f"[req-{correlation_id}] Resolved {len(resolved_items)}/{len(tripleseat_items)} items to Revel products")

    # ENABLE_CONNECTOR safety check
    if not enable_connector:
        logger.warning(f"[req-{correlation_id}] CONNECTOR DISABLED – blocking Revel write")
        return InjectionResult(True, error="CONNECTOR_DISABLED")

    # DRY RUN check - after resolution so we can see what would be injected
    if dry_run:
        logger.info(f"[req-{correlation_id}] [DRY_RUN] Would inject {len(resolved_items)} items to establishment {establishment}")
        for idx, item in enumerate(resolved_items):
            logger.info(f"[req-{correlation_id}] [DRY_RUN] Item {idx+1}: {item}")
        logger.info(f"[req-{correlation_id}] [DRY_RUN] Revel write PREVENTED – DRY_RUN=true")
        return InjectionResult(True)  # Return success without writing

    # If no items resolved, acknowledge safely
    if not resolved_items:
        logger.warning(f"[req-{correlation_id}] No items resolved – acknowledging event safely (no injection)")
        return InjectionResult(True, error="No items matched - event acknowledged without injection")

    # Calculate subtotal from resolved items (quantity × price for each item)
    subtotal = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in resolved_items)
    
    # Get invoice totals from billing invoice if available, otherwise use calculated subtotal
    invoice_total = billing_invoice.get("total", 0) if billing_invoice else 0
    invoice_subtotal = billing_invoice.get("subtotal", 0) if billing_invoice else 0
    
    # If invoice has no pricing, use our calculated subtotal
    if invoice_subtotal == 0 and subtotal > 0:
        invoice_subtotal = subtotal
        logger.info(f"[req-{correlation_id}] Using calculated subtotal ${subtotal} (billing invoice had 0)")
    
    if invoice_total == 0 and subtotal > 0:
        invoice_total = subtotal
        logger.info(f"[req-{correlation_id}] Using calculated total ${subtotal} (billing invoice had 0)")
    
    # Calculate discount if invoice total is less than subtotal
    discount_amount = subtotal - invoice_total if invoice_total < subtotal else 0
    
    # Get customer name and phone from event
    customer_name = event.get("name", "")  # Event guest name
    customer_phone = event.get("phone", "")  # Event phone number

    # Build order data with resolved items - use new format expected by create_order()
    # Uses Triple Seat configuration: Pinkbox menu, Triple Seat dining option,
    # Triple Seat custom payment, Triple Seat Discount
    order_data = {
        "establishment": establishment,
        "local_id": external_order_id,  # For idempotency/deduplication
        "notes": f"Triple Seat Event #{event_id}",
        "items": resolved_items,  # List of {product_id, quantity, price}
        "discount_amount": discount_amount,  # Triple Seat Discount
        "payment_amount": invoice_total,  # Triple Seat Payment
        "customer_name": customer_name,  # Guest name from Triple Seat
        "customer_phone": customer_phone,  # Phone from Triple Seat
    }

    logger.info(f"[req-{correlation_id}] [INJECTION] Creating order with {len(resolved_items)} items in establishment {establishment}")
    if discount_amount > 0:
        logger.info(f"[req-{correlation_id}] [INJECTION] Applying Triple Seat Discount: ${discount_amount}")
    if invoice_total > 0:
        logger.info(f"[req-{correlation_id}] [INJECTION] Applying Triple Seat Payment: ${invoice_total}")

    # Create order using direct API (handles all items and details)
    created_order = revel_client.create_order(order_data)
    if not created_order:
        logger.error(f"[req-{correlation_id}] [INJECTION FAILED] Failed to create order in Revel")
        return InjectionResult(False, error="Failed to create order in Revel")

    order_id = created_order.get('id')
    logger.info(f"[req-{correlation_id}] [INJECTION SUCCESS] Order created: {order_id}")
    
    # Open the order so it appears in Revel UI
    revel_client.open_order(str(order_id))

    # Build order details for email
    order_details = OrderDetails(
        revel_order_id=str(created_order.get("id", "unknown")),
        subtotal=subtotal,
        discount=subtotal - invoice_total if invoice_total < subtotal else 0,
        final_total=invoice_total,
        payment_type="Triple Seat" if invoice_total > 0 else None
    )

    return InjectionResult(True, order_details=order_details)