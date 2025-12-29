import logging
import json
import os
from datetime import datetime, time
from typing import Optional
import pytz
from integrations.tripleseat.api_client import TripleSeatAPIClient, TripleSeatFailureType

logger = logging.getLogger(__name__)

def check_time_gate(event_id: str, correlation_id: str = None, event_data: dict = None) -> str:
    """Check if event is within injection time window.
    
    AUTHENTICATION STRATEGY:
    - Uses provided event_data if available (from webhook, no API call needed)
    - Falls back to Public API Key fetch if event_data not provided
    
    Args:
        event_id: TripleSeat event ID
        correlation_id: Optional correlation ID for logging
        event_data: Optional event data dict (from webhook). If provided, skips API call.
    
    Returns:
        "PROCEED" if event is within injection window
        "TOO_EARLY" if event date is in the future
        "EVENT_DAY_PASSED" if event date is in the past (and outside window)
        "OUTSIDE_WINDOW" if today is event day but outside time window
        "UNKNOWN_TIMEZONE" if site timezone cannot be determined
        "INVALID_DATE_FORMAT" if event date cannot be parsed
        "MISSING_DATA" if event data is missing required fields
        "EVENT_DATA_UNAVAILABLE" if event cannot be fetched
        "AUTHORIZATION_DENIED" if authorization to event denied
    """
    # Use provided event_data if available, otherwise fetch from API
    if event_data:
        event = event_data.get("event", {})
        logger.info(f"[req-{correlation_id}] Using provided event_data (no API call)")
    else:
        client = TripleSeatAPIClient()
        response, failure_type = client.get_event_with_status(event_id)

        if not response:
            if failure_type == TripleSeatFailureType.AUTHORIZATION_DENIED:
                return "AUTHORIZATION_DENIED"
            return "EVENT_DATA_UNAVAILABLE"

        event = response.get("event", {})
    
    event_date_str = event.get("event_date")
    site_id = event.get("site_id")

    if not event_date_str or not site_id:
        return "MISSING_DATA"

    # Get timezone from config
    timezone = get_site_timezone(site_id)
    if not timezone:
        return "UNKNOWN_TIMEZONE"

    # Parse event date - TripleSeat returns MM/DD/YYYY format
    try:
        # Try ISO format first
        try:
            event_date = datetime.fromisoformat(event_date_str).date()
        except ValueError:
            # Fall back to MM/DD/YYYY format
            event_date = datetime.strptime(event_date_str, "%m/%d/%Y").date()
    except ValueError:
        logger.error(f"Cannot parse event date: {event_date_str}")
        return "INVALID_DATE_FORMAT"

    # Get current date in site timezone
    tz = pytz.timezone(timezone)
    now_pst = datetime.now(tz)
    now_date = now_pst.date()
    
    logger.info(f"Timezone: {timezone}, Current time in site TZ: {now_pst.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Simple date-based logic:
    # - Inject if event date is today (in site timezone)
    # - Hold (TOO_EARLY) if event date is in the future
    # - Block (EVENT_DAY_PASSED) if event date is in the past
    
    if now_date < event_date:
        logger.info(f"Event date {event_date} is in the future (today is {now_date}) - TOO_EARLY to inject")
        return "TOO_EARLY"
    elif now_date > event_date:
        logger.warning(f"Event date {event_date} is in the past (today is {now_date}) - cannot inject")
        return "EVENT_DAY_PASSED"
    else:
        # Event date matches today - PROCEED
        logger.info(f"Event date {event_date} matches today - PROCEED with injection")
        return "PROCEED"

def get_site_timezone(site_id: str) -> Optional[str]:
    """Get timezone for site from config."""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'locations.json')
    try:
        with open(config_path, 'r') as f:
            locations = json.load(f)
            site_config = locations.get(str(site_id))
            return site_config.get('timezone') if site_config else None
    except (FileNotFoundError, json.JSONDecodeError):
        return None