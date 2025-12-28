import logging
from integrations.tripleseat.models import ValidationResult
from integrations.tripleseat.api_client import TripleSeatAPIClient

logger = logging.getLogger(__name__)

def validate_event(event_id: str, correlation_id: str = None, skip_validation: bool = False) -> ValidationResult:
    """Validate TripleSeat event using OAuth 2.0 API.
    
    Args:
        event_id: TripleSeat event ID
        correlation_id: Request correlation ID for logging
        skip_validation: Skip API validation (use for webhook-only mode)
    
    Returns:
        ValidationResult with validation status
    """
    req_id = f"[req-{correlation_id}]" if correlation_id else "[validation]"
    
    # Allow webhook-only mode
    if skip_validation:
        logger.info(f"{req_id} Validation skipped - using webhook payload only")
        return ValidationResult(True, "WEBHOOK_PAYLOAD_MODE")
    
    # Use OAuth 2.0 API for validation
    client = TripleSeatAPIClient()
    
    try:
        event, status = client.get_event_with_status(event_id)
        
        if event is None:
            logger.warning(f"{req_id} Event {event_id} validation failed: {status}")
            return ValidationResult(False, status)
        
        # Check event status
        event_status = event.get('status', '').upper()
        if event_status not in ['DEFINITE', 'CONFIRMED']:
            logger.warning(f"{req_id} Event {event_id} has status '{event_status}' - not definite/confirmed")
            return ValidationResult(False, f"INVALID_STATUS:{event_status}")
        
        logger.info(f"{req_id} Event {event_id} validation successful via OAuth 2.0 API")
        return ValidationResult(True, "VALID")
    
    except Exception as e:
        logger.error(f"{req_id} Event validation error: {e}")
        return ValidationResult(False, "VALIDATION_ERROR")