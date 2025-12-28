import logging
from integrations.tripleseat.models import ValidationResult

logger = logging.getLogger(__name__)

def validate_event(event_id: str, correlation_id: str = None) -> ValidationResult:
    """Validate Triple Seat event for injection.
    
    NOTE: OAuth 2.0 API REMOVED - All API calls disabled.
    This function returns False to force webhook-payload-only mode.
    
    Callers MUST use skip_validation=True parameter to process events.
    All event data should come from webhook payloads.
    
    Args:
        event_id: TripleSeat event ID (unused)
        correlation_id: Request correlation ID for logging (unused)
    
    Returns:
        ValidationResult(is_valid=False) with message indicating API is disabled
    """
    if correlation_id:
        logger.warning(f"[req-{correlation_id}] Event validation via API DISABLED - use webhook payload only")
    else:
        logger.warning("Event validation via API DISABLED - use webhook payload only")
    
    return ValidationResult(False, "API_DISABLED_USE_WEBHOOK_PAYLOAD")