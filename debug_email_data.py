#!/usr/bin/env python3
import logging
logging.basicConfig(level=logging.WARNING)

from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.revel.mappings import get_revel_establishment
from datetime import datetime

ts_client = TripleSeatAPIClient()
event_data = ts_client.get_event('55558872')
event = event_data.get('event', {})

site_id = event.get('site_id')
event_date = event.get('event_date')

print(f'Site ID: {site_id}')
print(f'Event Date (raw): {event_date}')

# Test establishment mapping
establishment = get_revel_establishment(site_id)
print(f'Establishment from mapping: {establishment}')

# Test date parsing
if event_date:
    date_str = str(event_date).strip()
    try:
        if '/' in date_str:
            formatted = datetime.strptime(date_str, '%m/%d/%Y').strftime('%B %d, %Y')
        else:
            formatted = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
        print(f'Formatted date: {formatted}')
    except Exception as e:
        print(f'Date parse error: {e}')
