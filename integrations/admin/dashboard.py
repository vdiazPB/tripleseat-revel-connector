"""Settings and dashboard UI with persistent JSON storage."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
import os
import json
from datetime import datetime
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent.parent / "settings.json"


def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file, fallback to environment variables."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings.json: {e}, using defaults")
    
    return get_default_settings()


def get_default_settings() -> Dict[str, Any]:
    """Get settings from environment variables."""
    return {
        "api_credentials": {
            "tripleseat": {
                "site_id": os.getenv("TRIPLESEAT_SITE_ID", "15691"),
                "oauth_configured": bool(os.getenv("TRIPLESEAT_OAUTH_CLIENT_ID")),
            },
            "revel": {
                "establishment_id": os.getenv("REVEL_ESTABLISHMENT_ID", "4"),
                "location_id": os.getenv("REVEL_LOCATION_ID", "1"),
                "domain": os.getenv("REVEL_DOMAIN", "pinkboxdoughnuts.revelup.com"),
            },
        },
        "establishment_mapping": {
            "dining_option_id": os.getenv("REVEL_TRIPLESEAT_DINING_OPTION_ID", "113"),
            "payment_type_id": os.getenv("REVEL_TRIPLESEAT_PAYMENT_TYPE_ID", "236"),
            "discount_id": os.getenv("REVEL_TRIPLESEAT_DISCOUNT_ID", "3358"),
            "custom_menu_id": os.getenv("REVEL_TRIPLESEAT_CUSTOM_MENU_ID", "2340"),
        },
        "sync_settings": {
            "sync_interval_minutes": 45,
            "lookback_hours": 48,
            "timezone": os.getenv("TIMEZONE", "America/Los_Angeles"),
            "enabled": os.getenv("ENABLE_CONNECTOR", "true").lower() == "true",
            "dry_run": os.getenv("DRY_RUN", "false").lower() == "true",
        },
        "notification_settings": {
            "email_enabled": True,
            "email_recipients": os.getenv("TRIPLESEAT_EMAIL_RECIPIENTS", "").split(","),
        },
        "advanced_settings": {
            "test_mode_override": os.getenv("TEST_LOCATION_OVERRIDE", "false").lower() == "true",
            "test_establishment_id": os.getenv("TEST_ESTABLISHMENT_ID", "4"),
        },
    }


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to JSON file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info("Settings saved to settings.json")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {e}")


def get_current_config() -> Dict[str, Any]:
    """Get current configuration from JSON or environment."""
    return load_settings()


@router.get("/")
def admin_dashboard():
    """Serve admin dashboard HTML."""
    return HTMLResponse(get_dashboard_html())


@router.get("/api/config")
def get_config():
    """Get current configuration."""
    return get_current_config()


@router.post("/api/config")
async def update_config(request: Request):
    """Update configuration and save to JSON."""
    try:
        # Parse JSON body
        request_data = await request.json()
        
        # Merge with existing settings
        current = load_settings()
        
        # Update with new values
        if "establishment_mapping" in request_data:
            current["establishment_mapping"].update(request_data["establishment_mapping"])
        if "sync_settings" in request_data:
            current["sync_settings"].update(request_data["sync_settings"])
        
        save_settings(current)
        logger.info("Settings updated and saved to JSON")
        return {"success": True, "message": "Settings saved to settings.json"}
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.get("/api/test")
def test_endpoint():
    """Test endpoint to verify API is responding."""
    return {"status": "ok", "message": "API is responding"}


@router.get("/api/status")
def get_status():
    """Get connector status and statistics."""
    return {
        "status": "online",
        "connector": {
            "enabled": True,
            "mode": "production",
            "timezone": "America/Los_Angeles",
        },
    }


@router.post("/api/sync/trigger")
async def trigger_sync(event_id: str = None, hours_back: int = 48):
    """Trigger a manual sync."""
    try:
        import requests
        sync_url = os.getenv('SYNC_ENDPOINT_URL', 'http://127.0.0.1:8000/api/sync/tripleseat')
        
        params = {}
        if event_id:
            params['event_id'] = event_id
        else:
            params['hours_back'] = hours_back
        
        response = requests.get(sync_url, params=params, timeout=120)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_dashboard_html() -> str:
    """Generate admin dashboard HTML with editable settings."""
    config = load_settings()
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TripleSeat-Revel Connector Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace;
            background: #0f1419;
            color: #e0e6ed;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header { 
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            border-left: 4px solid #00d4ff;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
        }
        header h1 { 
            color: #00d4ff;
            font-size: 32px;
            margin-bottom: 8px;
            letter-spacing: 2px;
        }
        header p {
            color: #a0aec0;
            font-size: 13px;
        }
        .status-badge { 
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            margin-top: 12px;
            background: #0d3f3f;
            color: #48d1cc;
            border: 1px solid #48d1cc;
            letter-spacing: 1px;
        }
        .status-badge.online::before { content: "● "; color: #00ff00; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; }
        .card { 
            background: #1a202c;
            border: 1px solid #2d3748;
            border-left: 3px solid #00d4ff;
            padding: 24px;
            margin-bottom: 20px;
            border-radius: 6px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }
        .card h2 { 
            color: #00d4ff;
            font-size: 16px;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid #2d3748;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .field { 
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            padding: 8px;
            background: rgba(0, 212, 255, 0.05);
            border-radius: 4px;
        }
        .field-label { 
            font-weight: 700;
            color: #48d1cc;
            min-width: 200px;
        }
        .field-value { 
            color: #cbd5e0;
            font-family: 'Courier New', monospace;
        }
        .toggle-group {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding: 12px;
            background: rgba(0, 212, 255, 0.05);
            border-radius: 4px;
        }
        .toggle-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
            accent-color: #00d4ff;
        }
        .toggle-group label {
            margin: 0;
            cursor: pointer;
            color: #cbd5e0;
            flex: 1;
        }
        .button-group { 
            display: flex;
            gap: 10px;
            margin-top: 16px;
            flex-wrap: wrap;
        }
        button { 
            padding: 10px 16px;
            border: 1px solid #2d3748;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn-primary { 
            background: #00d4ff;
            color: #0f1419;
            border-color: #00d4ff;
        }
        .btn-primary:hover { 
            background: #00ffff;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }
        .btn-success { 
            background: #48d1cc;
            color: #0f1419;
            border-color: #48d1cc;
        }
        .btn-success:hover { 
            background: #7fffd4;
            box-shadow: 0 0 20px rgba(72, 209, 204, 0.5);
        }
        .btn-warning {
            background: #ffa500;
            color: #0f1419;
            border-color: #ffa500;
        }
        .btn-warning:hover {
            background: #ffb347;
            box-shadow: 0 0 20px rgba(255, 165, 0, 0.5);
        }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        label { 
            display: block;
            margin-bottom: 8px;
            font-weight: 700;
            color: #48d1cc;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        input[type="text"], 
        input[type="number"],
        select { 
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #2d3748;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 12px;
            background: #0a0e17;
            color: #00d4ff;
            font-family: 'Courier New', monospace;
        }
        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }
        .result { 
            background: #0a0e17;
            padding: 12px;
            border-radius: 4px;
            margin-top: 12px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-height: 400px;
            overflow-y: auto;
            color: #00d4ff;
            border: 1px solid #2d3748;
        }
        footer { 
            text-align: center;
            color: #718096;
            margin-top: 40px;
            font-size: 11px;
        }
        .success-msg { 
            background: rgba(72, 209, 204, 0.1);
            color: #48d1cc;
            padding: 12px;
            border-radius: 4px;
            margin-top: 12px;
            border: 1px solid #48d1cc;
        }
        .error-msg { 
            background: rgba(255, 69, 0, 0.1);
            color: #ff4500;
            padding: 12px;
            border-radius: 4px;
            margin-top: 12px;
            border: 1px solid #ff4500;
        }
        .loading { animation: pulse 1.5s infinite; }
        @keyframes pulse { 
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>█ CONNECTOR ADMIN █</h1>
            <p>TripleSeat-Revel Integration Control Panel</p>
            <div class="status-badge online">ONLINE</div>
        </header>

        <div class="grid">
            <div class="card">
                <h2>⚡ System Status</h2>
                <div class="field">
                    <span class="field-label">Status:</span>
                    <span class="field-value" id="connStatus">[ LOADING ]</span>
                </div>
                <div class="field">
                    <span class="field-label">Mode:</span>
                    <span class="field-value" id="connMode">[ LOADING ]</span>
                </div>
                <div class="field">
                    <span class="field-label">Timezone:</span>
                    <span class="field-value" id="connTimezone">[ LOADING ]</span>
                </div>
                <div class="field">
                    <span class="field-label">Config:</span>
                    <span class="field-value" id="settingsFile">[ CHECK ]</span>
                </div>
                <button class="btn-primary" onclick="refreshStatus()">↻ REFRESH</button>
            </div>

            <div class="card">
                <h2>⚙ Operation Mode</h2>
                <div class="toggle-group">
                    <input type="checkbox" id="jeraTestingMode">
                    <label for="jeraTestingMode">JERA Testing Mode (Dry-Run)</label>
                </div>
                <div class="toggle-group">
                    <input type="checkbox" id="dryRunMode">
                    <label for="dryRunMode">Global Dry-Run</label>
                </div>
                <div class="toggle-group">
                    <input type="checkbox" id="enableConnector">
                    <label for="enableConnector">Enable Connector</label>
                </div>
                <button class="btn-success" onclick="saveOperationMode()">💾 SAVE</button>
                <div id="opModeMsg"></div>
            </div>
        </div>

        <div class="card">
            <h2>🔧 Manual Sync Control</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <label>Event ID:</label>
                    <input type="text" id="eventId" placeholder="Leave blank for bulk sync">
                    <label>Lookback Hours:</label>
                    <input type="number" id="manualLookback" min="1" max="720" value="48">
                    <button class="btn-primary" onclick="triggerSync()">▶ TRIGGER SYNC</button>
                </div>
                <div id="resultDiv" style="display: none;">
                    <h3 style="color: #00d4ff; margin-bottom: 12px;">[ RESULT ]</h3>
                    <div class="result" id="syncResult"></div>
                </div>
            </div>
        </div>

        <footer>
            <p>TripleSeat-Revel Connector | Settings Persisted to config/settings.json</p>
        </footer>
    </div>

    <script>
        window.addEventListener("load", function() {
            refreshStatus();
            loadOperationMode();
        });
        
        function refreshStatus() {
            fetch("/admin/api/test")
                .then(r => r.json())
                .then(data => fetch("/admin/api/status"))
                .then(r => r.json())
                .then(data => {
                    var status = data.connector.enabled ? "✓ ENABLED" : "✗ DISABLED";
                    var mode = data.connector.mode === "dry_run" ? "🧪 DRY-RUN" : "🚀 PRODUCTION";
                    document.getElementById("connStatus").textContent = status;
                    document.getElementById("connMode").textContent = mode;
                    document.getElementById("connTimezone").textContent = data.connector.timezone;
                    document.getElementById("settingsFile").textContent = "✓ config/settings.json";
                })
                .catch(e => {
                    document.getElementById("connStatus").textContent = "✗ ERROR";
                });
        }
        
        function loadOperationMode() {
            fetch("/api/settings/")
                .then(r => r.json())
                .then(data => {
                    var settings = data.settings;
                    document.getElementById("jeraTestingMode").checked = settings.jera.testing_mode;
                    document.getElementById("dryRunMode").checked = settings.dry_run.enabled;
                    document.getElementById("enableConnector").checked = settings.enable_connector.enabled;
                })
                .catch(e => console.error("Failed to load settings:", e));
        }
        
        function saveOperationMode() {
            var btn = event.target;
            btn.disabled = true;
            btn.textContent = "💾 SAVING...";
            
            var updates = [
                fetch("/api/settings/jera.testing_mode", { 
                    method: "POST", 
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(document.getElementById("jeraTestingMode").checked)
                }),
                fetch("/api/settings/dry_run.enabled", { 
                    method: "POST", 
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(document.getElementById("dryRunMode").checked)
                }),
                fetch("/api/settings/enable_connector.enabled", { 
                    method: "POST", 
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(document.getElementById("enableConnector").checked)
                })
            ];
            
            Promise.all(updates)
                .then(() => {
                    var msg = document.getElementById("opModeMsg");
                    msg.innerHTML = "<div class='success-msg'>✓ Settings saved to config/settings.json</div>";
                })
                .catch(e => {
                    var msg = document.getElementById("opModeMsg");
                    msg.innerHTML = "<div class='error-msg'>✗ Error: " + e + "</div>";
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = "💾 SAVE";
                });
        }
        
        function triggerSync() {
            var eventId = document.getElementById("eventId").value;
            var lookback = document.getElementById("manualLookback").value;
            var url = "/admin/api/sync/trigger?";
            
            if (eventId) {
                url += "event_id=" + encodeURIComponent(eventId);
            } else {
                url += "hours_back=" + lookback;
            }
            
            var btn = event.target;
            btn.disabled = true;
            btn.textContent = "⏳ SYNCING...";
            
            fetch(url, { method: "POST" })
                .then(r => r.json())
                .then(data => {
                    document.getElementById("resultDiv").style.display = "block";
                    document.getElementById("syncResult").textContent = JSON.stringify(data, null, 2);
                })
                .catch(e => {
                    document.getElementById("resultDiv").style.display = "block";
                    document.getElementById("syncResult").textContent = "ERROR: " + e;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = "▶ TRIGGER SYNC";
                });
        }
    </script>
</body>
</html>"""
    
    return html


def get_settings_endpoints():
    """Get all settings-related router endpoints."""
    return router
