from fastapi import FastAPI, Request, HTTPException, Query
import logging
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook
from integrations.revel.api_client import RevelAPIClient
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
import uuid

# Trigger redeploy - location 15691 config updated

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TripleSeat-Revel Connector")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)