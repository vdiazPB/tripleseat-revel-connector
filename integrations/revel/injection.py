import logging
from .api_client import RevelAPIClient
from .mappings import get_revel_establishment, get_dining_option_id, get_payment_type_id, get_discount_id
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.tripleseat.models import InjectionResult, OrderDetails

logger = logging.getLogger(__name__)

def inject_order(event_id: str) -> InjectionResult:
    """Inject Triple Seat event into Revel POS."""
    external_order_id = f"tripleseat_event_{event_id}"

    # Get Triple Seat data
    ts_client = TripleSeatAPIClient()
    event_data = ts_client.get_event(event_id)
    if not event_data:
        return InjectionResult(False, error="Failed to fetch event data")

    event = event_data.get("event", {})
    site_id = event.get("site_id")

    # Get Revel establishment
    establishment = get_revel_establishment(site_id)
    if not establishment:
        return InjectionResult(False, error=f"No Revel establishment mapped for site {site_id}")

    revel_client = RevelAPIClient()

    # Check idempotency
    existing_order = revel_client.get_order(external_order_id, establishment)
    if existing_order:
        logger.info(f"Order {external_order_id} already exists")
        return InjectionResult(True)  # Exit safely

    # Get billing data
    documents = event_data.get("documents", [])
    billing_invoice = next((doc for doc in documents if doc.get("type") == "billing_invoice"), None)
    if not billing_invoice:
        return InjectionResult(False, error="No billing invoice found")

    invoice_total = billing_invoice.get("total", 0)
    subtotal = billing_invoice.get("subtotal", 0)

    # Get dining option
    dining_option_id = get_dining_option_id(establishment)
    if not dining_option_id:
        return InjectionResult(False, error="Triple Seat dining option not configured")

    # Build order data
    order_data = {
        "establishment": establishment,
        "external_order_id": external_order_id,
        "dining_option": dining_option_id,
        "order_status": "CLOSED",  # CLOSED / PAID
        "notes": f"Triple Seat Event #{event_id}",
        "items": [],  # Would need to map event items to Revel products
        "payments": []
    }

    # Add payment if invoice_total > 0
    if invoice_total > 0:
        payment_type_id = get_payment_type_id(establishment)
        if payment_type_id:
            order_data["payments"].append({
                "payment_type": payment_type_id,
                "amount": invoice_total
            })

    # Add discount if needed
    if invoice_total < subtotal:
        discount_id = get_discount_id(establishment)
        if discount_id:
            order_data["discounts"] = [{
                "discount": discount_id,
                "amount": subtotal - invoice_total
            }]

    # Create order
    created_order = revel_client.create_order(order_data)
    if not created_order:
        return InjectionResult(False, error="Failed to create order in Revel")

    # Build order details for email
    order_details = OrderDetails(
        revel_order_id=str(created_order.get("id")),
        subtotal=subtotal,
        discount=subtotal - invoice_total if invoice_total < subtotal else 0,
        final_total=invoice_total,
        payment_type="Triple Seat" if invoice_total > 0 else None
    )

    return InjectionResult(True, order_details=order_details)