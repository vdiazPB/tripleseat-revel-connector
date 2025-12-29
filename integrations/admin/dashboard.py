"""Settings and dashboard UI with persistent JSON storage."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
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
async def update_config(request_data: Dict[str, Any]):
    """Update configuration and save to JSON."""
    try:
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
        logger.error(f"Error updating config: {e}")
        return {"success": False, "error": str(e)}


@router.get("/api/status")
def get_status():
    """Get connector status and statistics."""
    config = load_settings()
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "connector": {
            "enabled": config["sync_settings"]["enabled"],
            "mode": "dry_run" if config["sync_settings"]["dry_run"] else "production",
            "timezone": config["sync_settings"]["timezone"],
        },
        "settings_file": str(SETTINGS_FILE),
        "settings_file_exists": SETTINGS_FILE.exists(),
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
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px;
                 box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        header h1 { color: #333; font-size: 28px; margin-bottom: 10px; }
        .status-badge { display: inline-block; padding: 8px 16px; border-radius: 20px;
                       font-size: 12px; font-weight: 600; margin-top: 10px;
                       background: #d4edda; color: #155724; }
        .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px;
               box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .card h2 { color: #333; font-size: 18px; margin-bottom: 16px;
                  padding-bottom: 12px; border-bottom: 2px solid #f0f0f0; }
        .field { margin-bottom: 12px; display: flex; justify-content: space-between;
                align-items: center; font-size: 13px; }
        .field-label { font-weight: 600; color: #555; min-width: 200px; }
        .field-value { color: #666; }
        .button-group { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
        button { padding: 10px 20px; border: none; border-radius: 6px; font-size: 13px;
                font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-secondary { background: #e0e0e0; color: #333; }
        .btn-secondary:hover { background: #d0d0d0; }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #218838; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input, select { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
               margin-bottom: 12px; font-size: 13px; }
        .result { background: #f5f5f5; padding: 12px; border-radius: 6px; margin-top: 12px;
                 font-family: monospace; font-size: 11px; max-height: 300px; overflow-y: auto; }
        footer { text-align: center; color: white; margin-top: 40px; font-size: 12px; }
        .success-msg { background: #d4edda; color: #155724; padding: 12px; border-radius: 6px; margin-top: 12px; }
        .error-msg { background: #f8d7da; color: #721c24; padding: 12px; border-radius: 6px; margin-top: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚙️ TripleSeat-Revel Connector Admin</h1>
            <p>3-Tier Reconciliation Architecture - Settings Persist to JSON</p>
            <div class="status-badge">● Online</div>
        </header>

        <div class="card">
            <h2>System Status</h2>
            <div class="field">
                <span class="field-label">Connector Status:</span>
                <span class="field-value" id="connStatus">Loading...</span>
            </div>
            <div class="field">
                <span class="field-label">Mode:</span>
                <span class="field-value" id="connMode">Loading...</span>
            </div>
            <div class="field">
                <span class="field-label">Timezone:</span>
                <span class="field-value" id="connTimezone">Loading...</span>
            </div>
            <div class="field">
                <span class="field-label">Settings File:</span>
                <span class="field-value" id="settingsFile">settings.json</span>
            </div>
            <button class="btn-primary" onclick="refreshStatus()">Refresh Status</button>
        </div>

        <div class="card">
            <h2>Establishment Mapping (Editable - Saved to JSON)</h2>
            <label>Dining Option ID:</label>
            <input type="text" id="diningOptionId" value=\"""" + config['establishment_mapping']['dining_option_id'] + """\">
            
            <label>Payment Type ID:</label>
            <input type="text" id="paymentTypeId" value=\"""" + config['establishment_mapping']['payment_type_id'] + """\">
            
            <label>Discount ID:</label>
            <input type="text" id="discountId" value=\"""" + config['establishment_mapping']['discount_id'] + """\">
            
            <label>Custom Menu ID:</label>
            <input type="text" id="customMenuId" value=\"""" + config['establishment_mapping']['custom_menu_id'] + """\">
            
            <button class="btn-success" onclick="saveEstablishmentMapping()">💾 Save Mapping Settings</button>
            <div id="mappingMsg"></div>
        </div>

        <div class="card">
            <h2>Sync Settings (Editable - Saved to JSON)</h2>
            <label>
                <input type="checkbox" id="syncEnabled" """ + ("checked" if config['sync_settings']['enabled'] else "") + """>
                Enable Connector
            </label>
            
            <label>
                <input type="checkbox" id="dryRunMode" """ + ("checked" if config['sync_settings']['dry_run'] else "") + """>
                Dry Run Mode (test without creating orders)
            </label>
            
            <label>Timezone:</label>
            <input type="text" id="timezone" value=\"""" + config['sync_settings']['timezone'] + """\">
            
            <label>Lookback Hours:</label>
            <input type="number" id="lookbackHours" min="1" max="720" value=\"""" + str(config['sync_settings']['lookback_hours']) + """\">
            
            <button class="btn-success" onclick="saveSyncSettings()">💾 Save Sync Settings</button>
            <div id="syncMsg"></div>
        </div>

        <div class="card">
            <h2>Manual Sync Trigger</h2>
            <label>Event ID (leave blank for bulk sync):</label>
            <input type="text" id="eventId" placeholder="e.g., 55521609">
            
            <label>Lookback Hours (for bulk sync):</label>
            <input type="number" id="manualLookback" min="1" max="720" value="48">
            
            <button class="btn-primary" onclick="triggerSync()">▶️ Trigger Sync</button>
            <button class="btn-primary" onclick="triggerBulkSync()">⚡ Trigger Bulk Sync (48h)</button>
            
            <div id="resultDiv" style="display: none;">
                <h3 style="margin-top: 16px;">Sync Result:</h3>
                <div class="result" id="syncResult"></div>
            </div>
        </div>

        <div class="card">
            <h2>API Credentials (Read-Only)</h2>
            <div class="field">
                <span class="field-label">TripleSeat Site ID:</span>
                <span class="field-value">""" + config['api_credentials']['tripleseat']['site_id'] + """</span>
            </div>
            <div class="field">
                <span class="field-label">Revel Establishment:</span>
                <span class="field-value">""" + config['api_credentials']['revel']['establishment_id'] + """</span>
            </div>
            <div class="field">
                <span class="field-label">Revel Domain:</span>
                <span class="field-value">""" + config['api_credentials']['revel']['domain'] + """</span>
            </div>
            <p style="font-size: 12px; color: #999; margin-top: 12px;">
                💡 API credentials are set via environment variables for security.
            </p>
        </div>

        <footer>
            <p>TripleSeat-Revel Connector v1.0 | Settings saved to settings.json</p>
        </footer>
    </div>

    <script>
        window.addEventListener("load", function() {
            refreshStatus();
        });
        
        function refreshStatus() {
            fetch("/admin/api/status")
                .then(r => {
                    if (!r.ok) throw new Error("HTTP " + r.status);
                    return r.json();
                })
                .then(data => {
                    var status = data.connector.enabled ? "✓ Enabled" : "✗ Disabled";
                    var mode = data.connector.mode === "dry_run" ? "🧪 Dry Run" : "🚀 Production";
                    document.getElementById("connStatus").textContent = status;
                    document.getElementById("connMode").textContent = mode;
                    document.getElementById("connTimezone").textContent = data.connector.timezone;
                    document.getElementById("settingsFile").textContent = data.settings_file_exists ? "✓ settings.json (persisted)" : "📄 settings.json (not found, using defaults)";
                })
                .catch(e => {
                    console.error("Status error:", e);
                    document.getElementById("connStatus").textContent = "Error: " + e.message;
                });
        }
        
        function saveEstablishmentMapping() {
            var btn = event.target;
            btn.disabled = true;
            btn.textContent = "💾 Saving...";
            
            var config = {
                establishment_mapping: {
                    dining_option_id: document.getElementById("diningOptionId").value,
                    payment_type_id: document.getElementById("paymentTypeId").value,
                    discount_id: document.getElementById("discountId").value,
                    custom_menu_id: document.getElementById("customMenuId").value
                }
            };
            
            fetch("/admin/api/config", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(config)
            })
            .then(r => r.json())
            .then(data => {
                var msg = document.getElementById("mappingMsg");
                if (data.success) {
                    msg.innerHTML = "<div class=\"success-msg\">✓ Establishment mapping saved to settings.json</div>";
                } else {
                    msg.innerHTML = "<div class=\"error-msg\">✗ Error: " + data.error + "</div>";
                }
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = "💾 Save Mapping Settings";
            });
        }
        
        function saveSyncSettings() {
            var btn = event.target;
            btn.disabled = true;
            btn.textContent = "💾 Saving...";
            
            var config = {
                sync_settings: {
                    sync_interval_minutes: 45,
                    lookback_hours: parseInt(document.getElementById("lookbackHours").value),
                    timezone: document.getElementById("timezone").value,
                    enabled: document.getElementById("syncEnabled").checked,
                    dry_run: document.getElementById("dryRunMode").checked
                }
            };
            
            fetch("/admin/api/config", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(config)
            })
            .then(r => r.json())
            .then(data => {
                var msg = document.getElementById("syncMsg");
                if (data.success) {
                    msg.innerHTML = "<div class=\"success-msg\">✓ Sync settings saved to settings.json</div>";
                } else {
                    msg.innerHTML = "<div class=\"error-msg\">✗ Error: " + data.error + "</div>";
                }
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = "💾 Save Sync Settings";
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
            btn.textContent = "⏳ Syncing...";
            
            fetch(url, { method: "POST" })
                .then(r => r.json())
                .then(data => {
                    document.getElementById("resultDiv").style.display = "block";
                    document.getElementById("syncResult").textContent = JSON.stringify(data, null, 2);
                    alert("Sync triggered!");
                })
                .catch(e => alert("Error: " + e))
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = "▶️ Trigger Sync";
                });
        }
        
        function triggerBulkSync() {
            document.getElementById("eventId").value = "";
            document.getElementById("manualLookback").value = "48";
            triggerSync();
        }
    </script>
</body>
</html>
"""
    return html


def get_settings_endpoints():
    """Get all settings-related router endpoints."""
    return router
