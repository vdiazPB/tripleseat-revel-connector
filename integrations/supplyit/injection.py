import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from integrations.supplyit.api_client import SupplyItAPIClient
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.models import InjectionResult

logger = logging.getLogger(__name__)


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
    
    # Extract items from Triple Seat event
    tripleseat_items = event.get('items', []) or event.get('menu_items', []) or event_data.get('items', [])
    
    if not tripleseat_items:
        logger.warning(f"{req_id} No items found in Triple Seat event")
        # Continue anyway - create order with zero items or skip
        return InjectionResult(True, error="No items to transfer")
    
    logger.info(f"{req_id} Found {len(tripleseat_items)} items in Triple Seat event")
    
    # Resolve items to Supply It products
    order_items = []
    for item in tripleseat_items:
        item_name = item.get('name') if isinstance(item, dict) else str(item)
        item_qty = item.get('quantity', 1) if isinstance(item, dict) else 1
        
        # Try to find product in Supply It
        product = supplyit_client.get_product_by_name(location_id, item_name)
        
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
    order_data = {
        "Location": {
            "ID": location_id,
            "Name": special_events_location.get('Name')
        },
        "Contact": {
            "Name": guest_name
        } if guest_name else None,
        "OrderDate": event_date,
        "OrderItems": order_items,
        "OrderNotes": f"Triple Seat Event #{event_id}: {event_name}",
        "OrderStatus": "Open"
    }
    
    # Remove null Contact if not provided
    if not guest_name:
        del order_data["Contact"]
    
    logger.info(f"{req_id} [INJECTION] Creating Supply It order with {len(order_items)} items")
    
    # Create order in Supply It
    created_order = supplyit_client.create_order(order_data, correlation_id)
    
    if not created_order:
        logger.error(f"{req_id} [INJECTION FAILED] Failed to create order in Supply It")
        return InjectionResult(False, error="Failed to create order in Supply It")
    
    order_id = created_order.get('ID')
    logger.info(f"{req_id} [INJECTION SUCCESS] Supply It order created: {order_id}")
    
    return InjectionResult(True, order_details=None)
