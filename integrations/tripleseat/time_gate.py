import logging
import json
import os
from datetime import datetime, time
from typing import Optional
from integrations.tripleseat.api_client import TripleSeatAPIClient

logger = logging.getLogger(__name__)

def check_time_gate(event_id: str, correlation_id: str = None) -> str:
    """Check if event is within injection time window."""
    client = TripleSeatAPIClient()
    event_data = client.get_event(event_id)

    if not event_data:
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

    # Parse event date
    try:
        event_date = datetime.fromisoformat(event_date_str).date()
    except ValueError:
        return "INVALID_DATE_FORMAT"

    # Get current time in site timezone
    # For simplicity, assume UTC for now - in production, use proper timezone handling
    now = datetime.now().date()

    if now < event_date:
        return "TOO_EARLY"
    elif now > event_date:
        return "EVENT_DAY_PASSED"
    else:
        # Check time window: 12:01 AM to 11:59 PM
        current_time = datetime.now().time()
        start_time = time(0, 1)  # 12:01 AM
        end_time = time(23, 59)  # 11:59 PM

        if start_time <= current_time <= end_time:
            return "PROCEED"
        else:
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