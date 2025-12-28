import logging
import json
import os
from datetime import datetime, time
from typing import Optional
from integrations.tripleseat.api_client import TripleSeatAPIClient, TripleSeatFailureType

logger = logging.getLogger(__name__)

def check_time_gate(event_id: str, correlation_id: str = None) -> str:
    """Check if event is within injection time window.
    
    AUTHENTICATION STRATEGY:
    - Fetches event data using Public API Key (READ-ONLY)
    - OAuth is NOT used here (reserved for future WRITE operations)
    
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
    client = TripleSeatAPIClient()
    event_data, failure_type = client.get_event_with_status(event_id)

    if not event_data:
        if failure_type == TripleSeatFailureType.AUTHORIZATION_DENIED:
            return "AUTHORIZATION_DENIED"
        return "EVENT_DATA_UNAVAILABLE"

    event = event_data.get("event", {})
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

    # Get current time in site timezone
    # For simplicity, assume UTC for now - in production, use proper timezone handling
    now = datetime.now().date()

    if now < event_date:
        return "TOO_EARLY"
    elif now > event_date:
        return "EVENT_DAY_PASSED"
    else:
        # Check time window: 12:01 AM to 11:59:59 PM
        # Gate is OPEN during this window, CLOSED outside (midnight to 12:00:59 AM)
        current_time = datetime.now().time()
        start_time = time(0, 1, 0)   # 12:01:00 AM
        end_time = time(23, 59, 59)  # 11:59:59 PM

        if start_time <= current_time <= end_time:
            logger.info(f"Time gate OPEN: {current_time} is within {start_time} to {end_time}")
            return "PROCEED"
        else:
            logger.warning(f"Time gate CLOSED: {current_time} is outside {start_time} to {end_time}")
            return "OUTSIDE_TIME_WINDOW"

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