#!/usr/bin/env python
"""Debug time gate check"""

import logging
from datetime import datetime
from integrations.tripleseat.time_gate import check_time_gate

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

event_id = '55383184'
print(f'\n=== Time Gate Debug ===')
print(f'Event ID: {event_id}')
print(f'Current Time: {datetime.now()}')
print(f'Current Time Only: {datetime.now().time()}')

result = check_time_gate(event_id, 'debug-001')

print(f'\nTime Gate Result: {result}')
print(f'Expected: PROCEED')
print(f'Match: {result == "PROCEED"}')
