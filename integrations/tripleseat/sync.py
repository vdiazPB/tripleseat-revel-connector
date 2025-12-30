"""TripleSeat reconciliation sync module.

Handles querying recent events from TripleSeat and injecting them into Revel.
Provides safety net for missed webhooks and idempotent order creation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pytz
from integrations.tripleseat.api_client import TripleSeatAPIClient
from integrations.revel.injection import inject_order
from integrations.tripleseat.time_gate import check_time_gate

logger = logging.getLogger(__name__)

class TripleSeatSync:
    """Reconcile TripleSeat events with Revel POS."""
    
    def __init__(self, site_id: str, establishment: str, location_id: str):
        """Initialize sync with configuration.
        
        Args:
            site_id: TripleSeat site ID
            establishment: Revel establishment ID
            location_id: Revel location ID (for logging)
        """
        self.ts_client = TripleSeatAPIClient()
        self.site_id = site_id
        self.establishment = establishment
        self.location_id = location_id
    
    def sync_recent_events(
        self,
        hours_back: int = 48,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Query and sync recent TripleSeat events.
        
        Args:
            hours_back: Number of hours to look back (default 48)
            correlation_id: Request ID for logging
            
        Returns:
            Summary dict with counts: {
                'queried': N,
                'injected': N,
                'skipped': N,
                'failed': N,
                'events': [list of event details]
            }
        """
        req_id = f"[req-{correlation_id}]" if correlation_id else ""
        summary = {
            'queried': 0,
            'injected': 0,
            'skipped': 0,
            'failed': 0,
            'errors': [],
            'events': []
        }
        
        try:
            # Calculate date range (PST)
            pst = pytz.timezone('America/Los_Angeles')
            now_pst = datetime.now(pst)
            cutoff_time = now_pst - timedelta(hours=hours_back)
            cutoff_date = cutoff_time.strftime('%Y-%m-%d')
            
            logger.info(
                f"{req_id} Starting TripleSeat sync for site {self.site_id} "
                f"(events from {cutoff_date} onwards)"
            )
            
            # Query recent events (search for events updated in the past N hours)
            events = self._query_recent_events(cutoff_date, correlation_id)
            summary['queried'] = len(events)
            
            logger.info(f"{req_id} Found {len(events)} recent events to check")
            
            # Process each event
            for event in events:
                event_id = event.get('id')
                event_date = event.get('event_date')
                event_name = event.get('name', 'Unknown')
                
                try:
                    # Time gate check (don't inject past events)
                    time_gate_result = check_time_gate(event_id, correlation_id, event_data={'event': event})
                    if time_gate_result != "PROCEED":
                        logger.info(
                            f"{req_id} Event {event_id} ({event_name}) "
                            f"failed time gate - {time_gate_result}"
                        )
                        summary['skipped'] += 1
                        summary['events'].append({
                            'id': event_id,
                            'name': event_name,
                            'date': event_date,
                            'status': 'SKIPPED_TIME_GATE',
                            'reason': time_gate_result
                        })
                        continue
                    
                    # Inject order
                    logger.info(
                        f"{req_id} Processing event {event_id} ({event_name}) "
                        f"on {event_date}"
                    )
                    
                    result = inject_order(
                        event_id=str(event_id),
                        correlation_id=correlation_id,
                        dry_run=False,  # Production: always inject
                        enable_connector=True,
                        test_location_override=False
                    )
                    
                    if result.success:
                        summary['injected'] += 1
                        # Extract order ID from order_details
                        revel_order_id = None
                        if result.order_details:
                            revel_order_id = result.order_details.revel_order_id
                        summary['events'].append({
                            'id': event_id,
                            'name': event_name,
                            'date': event_date,
                            'status': 'INJECTED',
                            'revel_order_id': revel_order_id
                        })
                        logger.info(
                            f"{req_id} Event {event_id} successfully injected "
                            f"as Revel order {revel_order_id}"
                        )
                    else:
                        summary['skipped'] += 1
                        summary['events'].append({
                            'id': event_id,
                            'name': event_name,
                            'date': event_date,
                            'status': 'SKIPPED',
                            'reason': result.error or 'Unknown reason'
                        })
                        logger.info(
                            f"{req_id} Event {event_id} skipped: {result.error}"
                        )
                        
                except Exception as e:
                    summary['failed'] += 1
                    summary['errors'].append(str(e))
                    summary['events'].append({
                        'id': event_id,
                        'name': event_name,
                        'date': event_date,
                        'status': 'ERROR',
                        'error': str(e)
                    })
                    logger.error(
                        f"{req_id} Failed to process event {event_id}: {e}",
                        exc_info=True
                    )
            
            logger.info(
                f"{req_id} Sync complete: "
                f"queried={summary['queried']}, "
                f"injected={summary['injected']}, "
                f"skipped={summary['skipped']}, "
                f"failed={summary['failed']}"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"{req_id} Sync failed: {e}", exc_info=True)
            summary['errors'].append(f"Sync failed: {str(e)}")
            return summary
    
    def _query_recent_events(
        self,
        from_date: str,
        correlation_id: str = None
    ) -> List[Dict[str, Any]]:
        """Query TripleSeat for events from a given date.
        
        Args:
            from_date: Start date in format YYYY-MM-DD
            correlation_id: Request ID for logging
            
        Returns:
            List of event dictionaries
        """
        req_id = f"[req-{correlation_id}]" if correlation_id else ""
        
        try:
            # Use the TripleSeat API to query events
            # For now, we'll need to fetch events individually or via search
            # Since the API doesn't have a bulk search endpoint, we'll log this
            # and provide a method to be extended
            
            logger.info(
                f"{req_id} Querying TripleSeat events from {from_date} "
                f"(Note: TripleSeat API doesn't support bulk event search, "
                f"webhook trigger or manual event IDs required)"
            )
            
            # In a real implementation, you might:
            # 1. Store event IDs from webhooks in a queue
            # 2. Query specific known event IDs
            # 3. Use TripleSeat's search API if available
            
            return []
            
        except Exception as e:
            logger.error(f"{req_id} Failed to query events: {e}", exc_info=True)
            return []
    
    def sync_event(
        self,
        event_id: str,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Sync a single event by ID.
        
        Args:
            event_id: TripleSeat event ID
            correlation_id: Request ID for logging
            
        Returns:
            Result dict with status
        """
        req_id = f"[req-{correlation_id}]" if correlation_id else ""
        
        try:
            logger.info(f"{req_id} Syncing single event {event_id}")
            
            # Fetch event from TripleSeat
            event_data = self.ts_client.get_event(event_id)
            if not event_data:
                return {
                    'success': False,
                    'event_id': event_id,
                    'reason': 'Event not found in TripleSeat'
                }
            
            # Time gate check
            time_gate_result = check_time_gate(event_id, correlation_id, event_data={'event': event_data})
            if time_gate_result != "PROCEED":
                return {
                    'success': False,
                    'event_id': event_id,
                    'reason': f'Time gate failed: {time_gate_result}'
                }
            
            # Inject into Revel
            result = inject_order(
                event_id=str(event_id),
                correlation_id=correlation_id,
                dry_run=False,  # Production: always inject
                enable_connector=True,
                test_location_override=False
            )
            
            return {
                'success': result.success,
                'event_id': event_id,
                'revel_order_id': result.order_details.revel_order_id if result.order_details and result.success else None,
                'reason': result.error if not result.success else None
            }
            
        except Exception as e:
            logger.error(
                f"{req_id} Failed to sync event {event_id}: {e}",
                exc_info=True
            )
            return {
                'success': False,
                'event_id': event_id,
                'error': str(e)
            }
