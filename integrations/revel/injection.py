import logging
import os
from typing import List, Dict, Any, Optional
from integrations.revel.api_client import RevelAPIClient
from integrations.revel.mappings import get_revel_establishment, get_dining_option_id, get_payment_type_id, get_discount_id
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.models import InjectionResult, OrderDetails

logger = logging.getLogger(__name__)


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
            resolved_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': product.get('price', 0)
            })
            logger.info(f"[req-{correlation_id}] [ITEM RESOLVED] '{item_name}' → product_id={product_id}, qty={quantity}")
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
    
    external_order_id = f"tripleseat_event_{event_id}"

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

    # Get invoice totals (may be None if no billing invoice)
    invoice_total = billing_invoice.get("total", 0) if billing_invoice else 0
    subtotal = billing_invoice.get("subtotal", 0) if billing_invoice else 0
    
    # Calculate discount if invoice total is less than subtotal
    discount_amount = subtotal - invoice_total if invoice_total < subtotal else 0

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
    }

    logger.info(f"[req-{correlation_id}] [INJECTION] Creating order with {len(resolved_items)} items in establishment {establishment}")
    if discount_amount > 0:
        logger.info(f"[req-{correlation_id}] [INJECTION] Applying Triple Seat Discount: ${discount_amount}")
    if invoice_total > 0:
        logger.info(f"[req-{correlation_id}] [INJECTION] Applying Triple Seat Payment: ${invoice_total}")

    # Create order
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