import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from integrations.supplyit.api_client import SupplyItAPIClient
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.revel.injection import parse_invoice_for_items
from integrations.tripleseat.models import InjectionResult

logger = logging.getLogger(__name__)

# Product name mappings: TripleSeat -> JERA/Supply It
# Handles cases where product names don't match exactly
PRODUCT_NAME_MAPPINGS = {
    'OG': 'O G',  # TripleSeat "OG" is "O G" with space in JERA
}


def inject_order_to_supplyit(
    event_id: str,
    correlation_id: str = None,
    dry_run: bool = True,
    enable_connector: bool = True,
    webhook_payload: Dict[str, Any] = None
) -> InjectionResult:
    """Inject Triple Seat event into Supply It for Special Events location.
    
    Creates an order for Special Events catering/supplies.
    
    Args:
        event_id: TripleSeat event ID
        correlation_id: Request correlation ID for logging
        dry_run: If True, don't actually create the order
        enable_connector: If False, skip creation
        webhook_payload: Optional webhook payload with event details
    
    Returns:
        InjectionResult with success status
    """
    req_id = f"[req-{correlation_id}]" if correlation_id else "[supplyit]"
    
    # Safety checks
    if not enable_connector:
        logger.warning(f"{req_id} CONNECTOR DISABLED – blocking Supply It write")
        return InjectionResult(True, error="CONNECTOR_DISABLED")
    
    # Fetch event details from TripleSeat
    logger.info(f"{req_id} Fetching event {event_id} from TripleSeat API")
    ts_client = TripleSeatAPIClient()
    event_data = ts_client.get_event(event_id)
    
    if not event_data:
        logger.error(f"{req_id} Failed to fetch event data for event_id={event_id}")
        return InjectionResult(False, error="Failed to fetch event data")
    
    event = event_data if isinstance(event_data, dict) else event_data.get('event', {})
    
    # Extract event details
    event_name = event.get('name', f'Event {event_id}')
    event_date = event.get('event_date', datetime.now().isoformat())
    guest_name = event.get('guest_name') or event.get('client_name') or event.get('host_name') or ''
    event_total = event.get('grand_total') or event.get('total') or 0
    
    logger.info(f"{req_id} Event details: name='{event_name}', date='{event_date}', guest='{guest_name}', total=${event_total}")
    
    # Get Supply It client and locate the correct location
    # Location mapping: site_id 15691 (Special Events) -> Supply It location code "8" (C: Special Events)
    supplyit_client = SupplyItAPIClient()
    
    # Get location by code "8" (C: Special Events)
    special_events_location = supplyit_client.get_location_by_code("8")
    
    if not special_events_location:
        logger.error(f"{req_id} Could not find Supply It location code '8' (C: Special Events)")
        return InjectionResult(False, error="Special Events location not found")
    
    location_id = special_events_location.get('ID')
    logger.info(f"{req_id} Using Supply It location: {special_events_location.get('Name')} (ID: {location_id})")
    
    # Extract items from Triple Seat event - check multiple sources
    tripleseat_items = event.get('items', []) or event.get('menu_items', []) or event_data.get('items', [])
    
    # If no items found, try fetching from booking custom fields
    booking_id = event.get('booking_id')
    if not tripleseat_items and booking_id:
        logger.info(f"{req_id} No items in event, checking booking {booking_id}")
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
                    logger.info(f"{req_id} Found item in custom field: {item_name}")
                    tripleseat_items = [{'name': item_name, 'quantity': 1}]
        except Exception as e:
            logger.warning(f"{req_id} Failed to fetch booking details: {e}")
    
    # If still no items, try parsing invoice document
    documents = event_data.get('documents', [])
    if not tripleseat_items and documents:
        logger.info(f"{req_id} No items found, attempting to parse invoice document")
        # Find invoice document and its view URL
        for doc in documents:
            views = doc.get('views', [])
            invoice_view = next((v for v in views if 'invoice' in v.get('name', '').lower()), None)
            if invoice_view:
                invoice_url = invoice_view.get('url')
                if invoice_url:
                    logger.info(f"{req_id} Found invoice URL, parsing for items")
                    tripleseat_items, guest_name_from_invoice = parse_invoice_for_items(invoice_url, correlation_id)
                    if tripleseat_items:
                        logger.info(f"{req_id} Successfully extracted {len(tripleseat_items)} items from invoice")
                        if guest_name_from_invoice and not guest_name:
                            guest_name = guest_name_from_invoice
                            logger.info(f"{req_id} Also extracted guest name: '{guest_name}'")
                    break
    
    if not tripleseat_items:
        logger.warning(f"{req_id} No items found after checking all sources")
        return InjectionResult(True, error="No items to transfer")
    
    logger.info(f"{req_id} Found {len(tripleseat_items)} items in Triple Seat event")
    
    # Resolve items to Supply It products
    order_items = []
    for item in tripleseat_items:
        item_name = item.get('name') if isinstance(item, dict) else str(item)
        item_qty = item.get('quantity', 1) if isinstance(item, dict) else 1
        
        # Apply product name mapping if available
        jera_product_name = PRODUCT_NAME_MAPPINGS.get(item_name, item_name)
        if jera_product_name != item_name:
            logger.info(f"{req_id} [PRODUCT MAPPING] '{item_name}' -> '{jera_product_name}'")
        
        # Try to find product in Supply It (using mapped name)
        product = supplyit_client.get_product_by_name(location_id, jera_product_name)
        
        if product:
            product_id = product.get('ID')
            unit_price = product.get('UnitPrice', 0)
            
            order_item = {
                "Product": {
                    "ID": product_id,
                    "Name": item_name
                },
                "UnitsOrdered": item_qty,
                "UnitPrice": unit_price
            }
            order_items.append(order_item)
            logger.info(f"{req_id} [ITEM MATCHED] '{item_name}' → product_id={product_id}, qty={item_qty}")
        else:
            logger.warning(f"{req_id} [ITEM NOT FOUND] '{item_name}' not found in Supply It products")
    
    if not order_items:
        logger.warning(f"{req_id} No items matched to Supply It products")
        return InjectionResult(True, error="No items matched to Supply It products")
    
    logger.info(f"{req_id} Resolved {len(order_items)}/{len(tripleseat_items)} items to Supply It products")
    
    # DRY RUN check
    if dry_run:
        logger.info(f"{req_id} [DRY_RUN] Would create order for {len(order_items)} items in Special Events location")
        for idx, item in enumerate(order_items):
            logger.info(f"{req_id} [DRY_RUN] Item {idx+1}: {item['Product']['Name']} x{item['UnitsOrdered']}")
        logger.info(f"{req_id} [DRY_RUN] Supply It write PREVENTED – DRY_RUN=true")
        return InjectionResult(True)
    
    # Build Supply It order
    # Note: OrderItems must use StartingOrder instead of UnitsOrdered (per API spec)
    # Contact and Shift must be included with Code field (per API spec)
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
            "ID": location_id  # C: Special Events (Code 8)
        },
        "Contact": {
            "Code": "10"  # Customer contact for Special Events
        },
        "Shift": {
            "Code": "Production 01"  # Production shift
        },
        "OrderDate": event_date,
        "OrderItems": order_items_formatted,
        "OrderNotes": f"Triple Seat Event #{event_id}: {event_name}",
        "OrderStatus": "Open",
        "OrderViewType": "SalesOrder"  # SalesOrder with customer contact
    }
    
    logger.info(f"{req_id} [INJECTION] Creating Supply It order with {len(order_items)} items")
    
    # Create order in Supply It
    created_order = supplyit_client.create_order(order_data, correlation_id)
    
    if not created_order:
        logger.error(f"{req_id} [INJECTION FAILED] Failed to create order in Supply It")
        return InjectionResult(False, error="Failed to create order in Supply It")
    
    order_id = created_order.get('ID')
    logger.info(f"{req_id} [INJECTION SUCCESS] Supply It order created: {order_id}")
    
    return InjectionResult(True, order_details=None)
