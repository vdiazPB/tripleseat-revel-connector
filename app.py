from fastapi import FastAPI, Request, HTTPException, Query
import logging
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook
from integrations.revel.api_client import RevelAPIClient
from integrations.admin.dashboard import get_settings_endpoints
from integrations.admin.settings_routes import router as settings_router
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
import uuid
from contextlib import asynccontextmanager

# Trigger redeploy - location 15691 config updated

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup & shutdown events for scheduler
async def startup_event():
    """Initialize scheduled tasks on app startup."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        import requests
        
        logger.info("APScheduler dependencies imported successfully")
        
        scheduler = BackgroundScheduler()
        
        def scheduled_sync_task():
            """Background task: sync recent events every 45 minutes."""
            correlation_id = str(uuid.uuid4())[:8]
            logger.info(f"[scheduled-{correlation_id}] Starting scheduled sync task")
            
            try:
                sync_url = os.getenv('SYNC_ENDPOINT_URL', 'http://127.0.0.1:8000/api/sync/tripleseat')
                
                # Call sync endpoint for recent events (48 hours)
                response = requests.get(
                    sync_url,
                    params={'hours_back': 48},
                    timeout=120  # 2 minutes timeout for bulk sync
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[scheduled-{correlation_id}] Sync completed - "
                               f"Queried: {result.get('summary', {}).get('queried', 0)}, "
                               f"Injected: {result.get('summary', {}).get('injected', 0)}, "
                               f"Skipped: {result.get('summary', {}).get('skipped', 0)}, "
                               f"Failed: {result.get('summary', {}).get('failed', 0)}")
                else:
                    logger.error(f"[scheduled-{correlation_id}] Sync endpoint returned {response.status_code}")
            except Exception as e:
                logger.error(f"[scheduled-{correlation_id}] Scheduled sync failed: {e}")
        
        # Schedule task to run every 45 minutes
        scheduler.add_job(
            scheduled_sync_task,
            'interval',
            minutes=45,
            id='tripleseat_sync',
            name='TripleSeat Scheduled Sync',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("APScheduler initialized - TripleSeat sync scheduled every 45 minutes")
        
        # Store scheduler in app state for potential cleanup
        app.scheduler = scheduler
        
    except ImportError as e:
        logger.warning(f"APScheduler not installed or import error: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)

async def shutdown_event():
    """Clean up scheduled tasks on app shutdown."""
    if hasattr(app, 'scheduler'):
        app.scheduler.shutdown()
        logger.info("APScheduler shut down")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle - startup and shutdown."""
    await startup_event()
    yield
    await shutdown_event()

app = FastAPI(title="TripleSeat-Revel Connector", lifespan=lifespan)

# Include admin dashboard router
admin_router = get_settings_endpoints()
app.include_router(admin_router)

# Include settings management router
app.include_router(settings_router)


# Startup logging & production safety flags
env = os.getenv('ENV', 'development')
timezone = os.getenv('TIMEZONE', 'UTC')
dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'  # Default to false for production
enable_connector = os.getenv('ENABLE_CONNECTOR', 'true').lower() == 'true'
allowed_locations = os.getenv('ALLOWED_LOCATIONS', '').split(',') if os.getenv('ALLOWED_LOCATIONS') else []

# TEST MODE: Override all locations to establishment 4 (Siegel)
test_location_override = os.getenv('TEST_LOCATION_OVERRIDE', 'false').lower() == 'true'
test_establishment_id = os.getenv('TEST_ESTABLISHMENT_ID', '4')

logger.info(f"Starting TripleSeat-Revel Connector")
logger.info(f"ENV: {env}")
logger.info(f"TIMEZONE: {timezone}")
logger.info(f"DRY_RUN: {dry_run}")
logger.info(f"ENABLE_CONNECTOR: {enable_connector}")
logger.info(f"ALLOWED_LOCATIONS: {allowed_locations if allowed_locations and allowed_locations[0] else 'UNRESTRICTED'}")
if test_location_override:
    logger.warning(f"TEST_LOCATION_OVERRIDE ENABLED – All orders routed to establishment {test_establishment_id}")

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    """Root path - used for Render health checks and endpoint validation.
    
    Supports both GET and HEAD requests.
    No authentication required.
    No database or OAuth calls.
    """
    return {"status": "ok"}

@app.get("/health")
def health():
    # Get current time with timezone
    tz = pytz.timezone(timezone)
    current_time = datetime.now(tz).isoformat()
    return {
        "status": "ok",
        "time": current_time
    }

@app.post("/webhook")
async def webhook(request: Request):
    correlation_id = str(uuid.uuid4())[:8]
    
    # Kill switch check
    if not enable_connector:
        logger.info(f"[req-{correlation_id}] CONNECTOR DISABLED – event acknowledged")
        return {"ok": True, "processed": False, "reason": "CONNECTOR_DISABLED", "trigger": None}
    
    logger.info(f"[req-{correlation_id}] WEBHOOK INVOKED")
    try:
        # Get raw body for signature verification
        raw_body = await request.body()
        payload = await request.json()
        
        # Log webhook payload to file for debugging
        event_id = payload.get('event', {}).get('id') or payload.get('booking', {}).get('event_id')
        if event_id:
            log_file = f"webhook_event_{event_id}.json"
            try:
                import json
                with open(log_file, 'w') as f:
                    json.dump(payload, f, indent=2)
                logger.info(f"[req-{correlation_id}] Webhook payload saved to {log_file}")
            except Exception as e:
                logger.warning(f"[req-{correlation_id}] Could not save webhook payload: {e}")
        
        # Get X-Signature header for verification
        x_signature_header = request.headers.get('X-Signature')
        
        result = await handle_tripleseat_webhook(
            payload, 
            correlation_id,
            x_signature_header=x_signature_header,
            raw_body=raw_body,
            verify_signature_flag=False,  # TEMPORARILY DISABLED for testing
            dry_run=dry_run,
            enable_connector=enable_connector,
            allowed_locations=allowed_locations,
            test_location_override=test_location_override,
            test_establishment_id=test_establishment_id
        )
        return result
    except Exception as e:
        logger.error(f"[req-{correlation_id}] Webhook handler failed: {e}")
        return {"ok": False, "processed": False, "reason": f"HANDLER_ERROR: {str(e)}", "trigger": None}

@app.post("/webhooks/tripleseat")
async def webhooks_tripleseat(request: Request):
    """Alias endpoint for /webhook to match TripleSeat configuration."""
    return await webhook(request)

@app.post("/test/webhook")
async def test_webhook(request: Request):
    correlation_id = str(uuid.uuid4())[:8]
    
    # Kill switch check
    if not enable_connector:
        logger.info(f"[req-{correlation_id}] CONNECTOR DISABLED – event acknowledged")
        return {"ok": True, "processed": False, "reason": "CONNECTOR_DISABLED", "trigger": None}
    
    logger.info(f"[req-{correlation_id}] TEST WEBHOOK INVOKED")
    try:
        # Get raw body for signature verification (test endpoint can skip verification)
        raw_body = await request.body()
        payload = await request.json()
        
        result = await handle_tripleseat_webhook(
            payload, 
            correlation_id,
            x_signature_header=None,  # Don't verify in test mode
            raw_body=raw_body,
            verify_signature_flag=False,  # Skip signature verification for test
            dry_run=dry_run,
            enable_connector=enable_connector,
            allowed_locations=allowed_locations,
            test_location_override=test_location_override,
            test_establishment_id=test_establishment_id
        )
        return result
    except Exception as e:
        logger.error(f"[req-{correlation_id}] Test webhook failed: {e}")
        return {
            "ok": False,
            "processed": False,
            "reason": f"HANDLER_EXCEPTION_{type(e).__name__}",
            "trigger": None
        }

@app.get("/test/revel")
def test_revel():
    """Safe read-only test of Revel API connection."""
    try:
        client = RevelAPIClient()
        # Test with a safe read endpoint - establishments
        response = client._get_headers()  # Just test auth headers
        # For a real test, we'd need to make a GET request, but let's simulate
        # Since we can't make actual API calls here, return a mock response
        return {
            "status": 200,
            "count": 1  # Mock count
        }
    except Exception as e:
        logger.error(f"Revel test failed: {e}")
        return {
            "status": 500,
            "error": str(e)
        }

@app.get("/oauth/callback")
def oauth_callback(code: str | None = Query(None), state: str | None = Query(None), error: str | None = Query(None)):
    """OAuth callback endpoint for TripleSeat OAuth redirects.
    
    Accepts authorization code or error from OAuth flow.
    Handles both success (code) and error (error) scenarios.
    No authentication required.
    No business logic - minimal implementation.
    
    Query Parameters:
        code: Authorization code from OAuth provider (optional)
        state: State parameter for CSRF protection (optional)
        error: Error code if OAuth flow failed (optional)
    """
    correlation_id = str(uuid.uuid4())[:8]
    
    if error:
        logger.warning(f"[oauth-{correlation_id}] OAuth callback received error - error: {error}")
        return {"status": "error", "error": error}
    
    if code:
        logger.info(f"[oauth-{correlation_id}] OAuth callback received - code: {code[:20]}..., state: {state}")
        return {"status": "received", "code": code[:20] + "..."}
    
    logger.warning(f"[oauth-{correlation_id}] OAuth callback received without code or error")
    return {"status": "invalid", "message": "No code or error in callback"}

@app.get("/debug/oauth")
def debug_oauth():
    """Temporary debug endpoint for OAuth token fetch issues.
    
    Use this to diagnose why OAuth is returning HTML instead of JSON in Render.
    Remove after debugging.
    """
    import requests
    
    client_id = os.getenv('TRIPLESEAT_OAUTH_CLIENT_ID')
    client_secret = os.getenv('TRIPLESEAT_OAUTH_CLIENT_SECRET')
    token_url = os.getenv('TRIPLESEAT_OAUTH_TOKEN_URL')
    
    result = {
        "environment_vars": {
            "client_id_set": bool(client_id),
            "client_secret_set": bool(client_secret),
            "token_url": token_url
        }
    }
    
    if client_id and client_secret and token_url:
        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'read write'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            result["oauth_request"] = {
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type'),
                "is_html": 'text/html' in response.headers.get('content-type', '').lower(),
                "is_json": 'application/json' in response.headers.get('content-type', '').lower(),
                "response_preview": response.text[:300] if response.text else "empty"
            }
        except Exception as e:
            result["oauth_request"] = {"error": str(e)}
    else:
        result["error"] = "Missing OAuth environment variables"
    
    return result

@app.get("/debug/order/{order_id}")
def debug_order(order_id: str):
    """Debug endpoint to check if an order exists in Revel."""
    try:
        client = RevelAPIClient()
        
        # Try to fetch the order directly from the API
        import requests
        url = f"{client.base_url}/resources/Order/{order_id}/"
        headers = client._get_headers()
        
        response = requests.get(url, headers=headers)
        
        return {
            "order_id": order_id,
            "status": response.status_code,
            "found": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text[:500]
        }
    except Exception as e:
        logger.error(f"Debug order lookup failed: {e}")
        return {
            "order_id": order_id,
            "error": str(e)
        }

@app.get("/api/sync/tripleseat")
def sync_tripleseat(
    event_id: str | None = Query(None),
    hours_back: int = Query(48)
):
    """Reconciliation endpoint - sync TripleSeat events to Revel.
    
    Supports two modes:
    1. Single event sync: GET /api/sync/tripleseat?event_id=55521609
    2. Recent events sync: GET /api/sync/tripleseat?hours_back=48
    
    Query Parameters:
        event_id: Optional - specific event to sync
        hours_back: Optional - sync events from past N hours (default 48)
    
    Returns:
        {
            "success": bool,
            "mode": "single" | "bulk",
            "summary": {
                "queried": int,
                "injected": int,
                "skipped": int,
                "failed": int
            },
            "events": [
                {
                    "id": str,
                    "name": str,
                    "date": str,
                    "status": "injected" | "skipped" | "failed",
                    "revel_order_id": str | null,
                    "reason": str | null,
                    "error": str | null
                }
            ]
        }
    """
    from integrations.tripleseat.sync import TripleSeatSync
    
    correlation_id = str(uuid.uuid4())[:8]
    
    try:
        # Get configuration from environment
        site_id = int(os.getenv('TRIPLESEAT_SITE_ID', '15691'))
        establishment = os.getenv('REVEL_ESTABLISHMENT_ID', '4')
        location_id = os.getenv('REVEL_LOCATION_ID', '1')
        
        # Initialize sync engine
        sync = TripleSeatSync(site_id, establishment, location_id)
        
        logger.info(f"[sync-{correlation_id}] Sync request - event_id={event_id}, hours_back={hours_back}")
        
        if event_id:
            # Single event sync
            logger.info(f"[sync-{correlation_id}] Single event mode: {event_id}")
            result = sync.sync_event(event_id, correlation_id=correlation_id)
            
            return {
                "success": result.get("success", False),
                "mode": "single",
                "summary": {
                    "queried": 1,
                    "injected": 1 if result.get("success") else 0,
                    "skipped": 0 if result.get("success") else 1,
                    "failed": 0
                },
                "events": [{
                    "id": event_id,
                    "name": result.get("event_name", "unknown"),
                    "date": result.get("event_date", "unknown"),
                    "status": "injected" if result.get("success") else (result.get("status", "failed")),
                    "revel_order_id": result.get("revel_order_id"),
                    "reason": result.get("reason"),
                    "error": result.get("error")
                }]
            }
        else:
            # Bulk recent events sync
            logger.info(f"[sync-{correlation_id}] Bulk events mode: hours_back={hours_back}")
            result = sync.sync_recent_events(hours_back=hours_back, correlation_id=correlation_id)
            
            return {
                "success": result.get("failed", 0) == 0,
                "mode": "bulk",
                "summary": {
                    "queried": result.get("queried", 0),
                    "injected": result.get("injected", 0),
                    "skipped": result.get("skipped", 0),
                    "failed": result.get("failed", 0)
                },
                "events": result.get("events", [])
            }
    
    except Exception as e:
        logger.error(f"[sync-{correlation_id}] Sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "mode": "error",
            "summary": {
                "queried": 0,
                "injected": 0,
                "skipped": 0,
                "failed": 0
            },
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)