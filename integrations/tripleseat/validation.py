import logging
from integrations.tripleseat.models import ValidationResult
from integrations.tripleseat.api_client import TripleSeatAPIClient

logger = logging.getLogger(__name__)

def validate_event(event_id: str, correlation_id: str = None) -> ValidationResult:
    """Validate Triple Seat event for injection."""
    client = TripleSeatAPIClient()
    event_data = client.get_event(event_id)

    if not event_data:
        return ValidationResult(False, "Failed to fetch event data")

    event = event_data.get("event", {})

    # Check status
    if event.get("status") != "Definite":
        return ValidationResult(False, "Event status not Definite")

    # Check event_date
    if not event.get("event_date"):
        return ValidationResult(False, "Missing event_date")

    # Check site_id
    if not event.get("site_id"):
        return ValidationResult(False, "Missing site_id")

    # Check billing invoice
    documents = event_data.get("documents", [])
    billing_invoice = None
    for doc in documents:
        if doc.get("type") == "billing_invoice":
            billing_invoice = doc
            break

    if not billing_invoice:
        return ValidationResult(False, "No billing invoice found")

    # Check invoice is closed/final
    if not billing_invoice.get("is_closed", False):
        return ValidationResult(False, "Invoice not closed")

    invoice_total = billing_invoice.get("total", 0)
    if invoice_total < 0:
        return ValidationResult(False, "Invalid invoice total")

    # Check payments
    payments = event_data.get("payments", [])
    paid_total = sum(payment.get("amount", 0) for payment in payments)

    if invoice_total == 0:
        # PASS for free events
        pass
    elif paid_total < invoice_total:
        return ValidationResult(False, "Payment insufficient")

    return ValidationResult(True)