#!/usr/bin/env python
"""Auto-close DEFINITE events for today - Can be run standalone or imported."""

import os
import json
import logging
from datetime import datetime
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get credentials from environment or .env
CONSUMER_KEY = os.getenv('CONSUMER_KEY', '')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET', '')
BASE_URL = os.getenv('TRIPLESEAT_API_BASE', 'https://api.tripleseat.com')

if not CONSUMER_KEY or not CONSUMER_SECRET:
    logger.error("CONSUMER_KEY or CONSUMER_SECRET not set in environment")

def get_events_for_today():
    """Get all DEFINITE events scheduled for today.
    
    Returns:
        List of event dictionaries
    """
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    today = datetime.now().strftime('%m/%d/%Y')
    
    logger.info(f"Searching for DEFINITE events on {today}...")
    
    params = {
        'status': 'definite',
        'event_start_date': today,
        'event_end_date': today,
    }
    
    try:
        resp = oauth.get(f'{BASE_URL}/v1/events/search.json', params=params, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"API error: {resp.status_code} - {resp.text}")
            return []
        
        data = resp.json()
        events = data.get('results', [])
        
        logger.info(f"Found {len(events)} DEFINITE events for today")
        return events
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return []

def close_event(event_id):
    """Close a single event by changing status to CLOSED.
    
    Args:
        event_id: TripleSeat event ID
        
    Returns:
        True if successful, False otherwise
    """
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    
    logger.info(f"  Closing event {event_id}...")
    
    try:
        payload = {'event': {'status': 'CLOSED'}}
        resp = oauth.put(
            f'{BASE_URL}/v1/events/{event_id}.json',
            json=payload,
            timeout=10
        )
        
        if resp.status_code in (200, 201):
            data = resp.json()
            event = data.get('event', {})
            logger.info(f"  ✓ Event {event_id} ({event.get('name')}) closed successfully!")
            return True
        else:
            logger.error(f"  ✗ Failed to close event {event_id}: {resp.status_code} - {resp.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error closing event {event_id}: {e}")
        return False

def run_auto_close():
    """Run auto-close process for all DEFINITE events today.
    
    Returns:
        Dictionary with results
    """
    logger.info("=" * 80)
    logger.info("EVENT STATUS CHECKER - Auto-Close DEFINITE Events")
    logger.info("=" * 80)
    logger.info("")
    
    # Get today's DEFINITE events
    events = get_events_for_today()
    
    if not events:
        logger.info("No DEFINITE events found for today.")
        return {'success': True, 'closed': 0, 'failed': 0, 'total': 0}
    
    # Process each event
    closed_count = 0
    failed_count = 0
    
    for event in events:
        event_id = event.get('id')
        event_name = event.get('name')
        event_status = event.get('status', 'UNKNOWN')
        
        logger.info(f"\nProcessing: {event_name} (ID: {event_id}, Status: {event_status})")
        
        # Only close if status is DEFINITE
        if event_status == 'DEFINITE':
            if close_event(event_id):
                closed_count += 1
            else:
                failed_count += 1
        else:
            logger.info(f"  Skipping: event status is {event_status}, not DEFINITE")
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total events processed: {len(events)}")
    logger.info(f"Successfully closed: {closed_count}")
    logger.info(f"Failed to close: {failed_count}")
    logger.info("")
    
    return {
        'success': failed_count == 0,
        'closed': closed_count,
        'failed': failed_count,
        'total': len(events)
    }

def main():
    """Main function for standalone execution."""
    result = run_auto_close()
    exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()

