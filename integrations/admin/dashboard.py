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
SETTINGS_FILE = Path(__file__).parent.parent.parent / "config" / "settings.json"


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
    """Generate professional admin dashboard HTML with location override."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - TripleSeat Revel Connector</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #1e40af;
            --secondary: #0f766e;
            --accent: #059669;
            --danger: #dc2626;
            --warning: #f59e0b;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --border: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, #1a2942 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 24px;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            padding: 0;
        }

        .header-content h1 {
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            color: var(--text-primary);
        }

        .platform-flow {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }

        .platform-badge {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            min-width: 100px;
        }

        .platform-badge svg {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            padding: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .platform-logo {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.1);
        }

        .platform-logo svg {
            width: 100%;
            height: 100%;
            padding: 0;
            border-radius: 50%;
        }

        .platform-logo.tripleseat-logo {
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        }

        .platform-logo.revel-logo {
            background: linear-gradient(135deg, #1e3a5f 0%, #0f2844 100%);
        }

        .platform-logo.supplying-logo {
            background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        }

        .platform-name {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
            text-align: center;
        }

        .flow-connector {
            font-size: 1.5rem;
            color: var(--accent);
            opacity: 0.7;
            margin-bottom: 24px;
        }

        .logo-icon {
            font-size: 2rem;
            display: inline-block;
        }

        .platform-connector {
            background: linear-gradient(135deg, var(--accent) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }

        .connector-arrow {
            color: var(--accent);
            opacity: 0.6;
            font-size: 1.25rem;
        }

        .header-content p {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        .header-status {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
        }

        .status-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--accent);
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (max-width: 1024px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: var(--secondary);
            box-shadow: 0 4px 20px rgba(15, 118, 110, 0.1);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }

        .card-icon {
            font-size: 1.5rem;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(5, 150, 105, 0.1);
            border-radius: 8px;
        }

        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .card-description {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        .setting-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            margin-bottom: 12px;
            border: 1px solid transparent;
            transition: all 0.3s ease;
        }

        .setting-row:hover {
            border-color: var(--border);
            background: rgba(255, 255, 255, 0.05);
        }

        .setting-row:last-child {
            margin-bottom: 0;
        }

        .setting-label {
            flex: 1;
        }

        .setting-name {
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .setting-help {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 52px;
            height: 28px;
            background: var(--border);
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            padding: 0;
            margin: 0;
            flex-shrink: 0;
            z-index: 1;
        }

        .toggle-switch:hover {
            opacity: 0.8;
        }

        .toggle-switch:active {
            transform: scale(0.98);
        }

        .toggle-switch.active {
            background: var(--accent);
        }

        .toggle-switch::after {
            content: '';
            position: absolute;
            width: 24px;
            height: 24px;
            background: white;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: all 0.3s ease;
            pointer-events: none;
        }

        .toggle-switch.active::after {
            left: 26px;
        }

        .input-group {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-top: 12px;
        }

        input[type="number"] {
            flex: 1;
            padding: 10px 12px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        input[type="number"]:focus {
            outline: none;
            border-color: var(--secondary);
            box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1);
        }

        button {
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }

        button:hover {
            background: #1e3a8a;
            box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
        }

        button:active {
            transform: scale(0.98);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-lg {
            padding: 12px 24px;
            font-size: 1rem;
            width: 100%;
            justify-content: center;
        }

        .message {
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 16px;
            display: none;
            font-size: 0.95rem;
            border: 1px solid;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.success {
            background: rgba(5, 150, 105, 0.1);
            border-color: var(--accent);
            color: var(--accent);
        }

        .message.error {
            background: rgba(220, 38, 38, 0.1);
            border-color: var(--danger);
            color: var(--danger);
        }

        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        footer {
            text-align: center;
            padding-top: 32px;
            margin-top: 32px;
            border-top: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 20px;
        }

        @media (max-width: 768px) {
            .stats {
                grid-template-columns: 1fr;
            }
            
            .grid {
                grid-template-columns: 1fr;
            }
        }

        .stat-box {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }

        .stat-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <div class="platform-flow">
                    <div class="platform-badge tripleseat">
                        <div class="platform-logo tripleseat-logo">
                            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <!-- TripleSeat cyan sound wave -->
                                <rect x="10" y="25" width="6" height="50" rx="3" fill="white"/>
                                <rect x="22" y="15" width="6" height="70" rx="3" fill="white"/>
                                <rect x="34" y="20" width="6" height="60" rx="3" fill="white"/>
                                <rect x="46" y="15" width="6" height="70" rx="3" fill="white"/>
                                <rect x="58" y="25" width="6" height="50" rx="3" fill="white"/>
                                <rect x="70" y="20" width="6" height="60" rx="3" fill="white"/>
                                <rect x="82" y="30" width="6" height="40" rx="3" fill="white"/>
                            </svg>
                        </div>
                        <span class="platform-name">TripleSeat</span>
                    </div>
                    
                    <div class="flow-connector">→</div>
                    
                    <div class="platform-badge revel">
                        <div class="platform-logo revel-logo">
                            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <!-- Revel mixer bars -->
                                <rect x="15" y="30" width="8" height="40" rx="4" fill="white"/>
                                <rect x="30" y="20" width="8" height="50" rx="4" fill="white"/>
                                <rect x="45" y="25" width="8" height="45" rx="4" fill="white"/>
                                <rect x="60" y="20" width="8" height="50" rx="4" fill="white"/>
                                <rect x="75" y="30" width="8" height="40" rx="4" fill="white"/>
                            </svg>
                        </div>
                        <span class="platform-name">Revel POS</span>
                    </div>
                    
                    <div class="flow-connector">→</div>
                    
                    <div class="platform-badge supplying">
                        <div class="platform-logo supplying-logo">
                            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <!-- SupplyIt S logo -->
                                <path d="M 70 25 Q 80 25 80 35 Q 80 42 65 45 Q 85 48 85 55 Q 85 70 70 70 Q 55 70 55 60 L 65 60 Q 65 65 70 65 Q 75 65 75 60 Q 75 55 65 52 Q 45 48 45 40 Q 45 28 60 28 Q 70 28 72 35 L 62 35 Q 61 32 60 32 Q 55 32 55 37 Q 55 42 70 45" fill="white"/>
                            </svg>
                        </div>
                        <span class="platform-name">SupplyIt</span>
                    </div>
                </div>
                <p>Seamless event order integration across platforms</p>
            </div>
            <div class="header-status">
                <span class="status-dot"></span>
                <span>Operational</span>
            </div>
        </header>

        <div id="message" class="message"></div>

        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">⚙️</div>
                    <div>
                        <div class="card-title">Operation Modes</div>
                        <div class="card-description">Control system behavior and testing modes</div>
                    </div>
                </div>

                <div class="setting-row">
                    <div class="setting-label">
                        <div class="setting-name">JERA Testing Mode</div>
                        <div class="setting-help">Simulate orders without SupplyIt API calls</div>
                    </div>
                    <button type="button" class="toggle-switch" id="jeraToggle"></button>
                </div>

                <div class="setting-row">
                    <div class="setting-label">
                        <div class="setting-name">Global Dry-Run</div>
                        <div class="setting-help">Test all operations without creating orders</div>
                    </div>
                    <button type="button" class="toggle-switch" id="dryRunToggle"></button>
                </div>

                <div class="setting-row">
                    <div class="setting-label">
                        <div class="setting-name">Enable Connector</div>
                        <div class="setting-help">Enable or disable all injections globally</div>
                    </div>
                    <button type="button" class="toggle-switch" id="connectorToggle"></button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-icon">📍</div>
                    <div>
                        <div class="card-title">Location Override</div>
                        <div class="card-description">Test with specific establishments</div>
                    </div>
                </div>

                <div class="setting-row">
                    <div class="setting-label">
                        <div class="setting-name">Enable Override</div>
                        <div class="setting-help">Force all orders to specific establishment</div>
                    </div>
                    <button type="button" class="toggle-switch" id="locationOverrideToggle"></button>
                </div>

                <div class="setting-row">
                    <div class="setting-label">
                        <div class="setting-name">Establishment ID</div>
                        <div class="setting-help">Target establishment when override enabled</div>
                    </div>
                </div>

                <div class="input-group">
                    <input type="number" id="establishmentIdInput" min="1" placeholder="Enter establishment ID">
                    <button onclick="updateEstablishmentId()">Update</button>
                </div>
            </div>
        </div>

        <div class="card full-width">
            <div class="card-header">
                <div class="card-icon">🔧</div>
                <div>
                    <div class="card-title">System Tools</div>
                    <div class="card-description">Manual operations and maintenance</div>
                </div>
            </div>

            <button class="btn-lg" onclick="triggerSync()" id="syncBtn">
                <span>🔄</span> Trigger Manual Sync
            </button>

            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value" id="modeStatus">-</div>
                    <div class="stat-label">Mode</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="connectorStatus">-</div>
                    <div class="stat-label">Connector</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="lastSyncStatus">-</div>
                    <div class="stat-label">Last Update</div>
                </div>
            </div>
        </div>

        <footer>
            <p>Last sync: <span id="lastUpdate">Loading...</span></p>
            <p style="margin-top: 8px; opacity: 0.6;">v1.0 • Supply It Integration Service</p>
        </footer>
    </div>

    <script>
        async function loadSettings() {
            try {
                console.log('Loading settings from /api/settings/');
                const response = await fetch('/api/settings/');
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Settings response:', data);
                
                const settings = data.settings || data;
                console.log('Extracted settings:', settings);

                const jeraMode = settings.jera?.testing_mode || false;
                const dryRun = settings.dry_run?.enabled || false;
                const connectorEnabled = settings.enable_connector?.enabled || true;
                const locationOverride = settings.location_override?.enabled || false;
                const establishmentId = settings.location_override?.establishment_id || 4;

                console.log('Toggle states:', { jeraMode, dryRun, connectorEnabled, locationOverride });

                // Update toggle buttons
                const jeraBtn = document.getElementById('jeraToggle');
                const dryBtn = document.getElementById('dryRunToggle');
                const connBtn = document.getElementById('connectorToggle');
                const locBtn = document.getElementById('locationOverrideToggle');
                
                if (!jeraBtn || !dryBtn || !connBtn || !locBtn) {
                    console.error('Some toggle buttons not found in DOM!');
                    return;
                }

                jeraBtn.classList.toggle('active', jeraMode);
                dryBtn.classList.toggle('active', dryRun);
                connBtn.classList.toggle('active', connectorEnabled);
                locBtn.classList.toggle('active', locationOverride);
                
                console.log('Toggle buttons updated');
                
                const establishmentInput = document.getElementById('establishmentIdInput');
                if (establishmentInput) {
                    establishmentInput.value = establishmentId;
                }

                // Update status indicators
                const modeText = jeraMode ? 'Testing' : (dryRun ? 'Dry-Run' : 'Production');
                document.getElementById('modeStatus').textContent = modeText;
                document.getElementById('connectorStatus').textContent = connectorEnabled ? 'Active' : 'Inactive';
                document.getElementById('lastSyncStatus').textContent = new Date().toLocaleTimeString();
                document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
            } catch (error) {
                console.error('Error loading settings:', error);
                showMessage('Error loading settings', 'error');
            }
        }

        async function toggleSetting(key) {
            console.log('Toggle clicked for:', key);
            try {
                const url = `/api/settings/toggle/${key}`;
                console.log('Fetching:', url);
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                console.log('Response status:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('Toggle response:', result);
                
                if (result.success) {
                    showMessage(result.message || 'Setting updated successfully', 'success');
                    // Reload settings after a brief delay to ensure update
                    setTimeout(() => loadSettings(), 500);
                } else {
                    showMessage(result.detail || 'Failed to update setting', 'error');
                }
            } catch (error) {
                console.error('Error toggling setting:', error);
                showMessage(`Error: ${error.message}`, 'error');
            }
        }

        async function updateEstablishmentId() {
            try {
                const id = parseInt(document.getElementById('establishmentIdInput').value);
                if (!id || id < 1) {
                    showMessage('Please enter a valid establishment ID', 'error');
                    return;
                }
                const response = await fetch('/api/settings/location_override.establishment_id', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ value: id })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('Update establishment response:', result);
                
                if (result.success) {
                    showMessage(result.message || 'Establishment ID updated', 'success');
                    await loadSettings();
                } else {
                    showMessage(result.detail || 'Failed to update establishment ID', 'error');
                }
            } catch (error) {
                console.error('Error updating establishment ID:', error);
                showMessage(`Error: ${error.message}`, 'error');
            }
        }

        async function triggerSync() {
            const button = document.getElementById('syncBtn');
            button.disabled = true;
            const originalText = button.innerHTML;
            button.innerHTML = '<span class="loading"></span> Syncing...';

            try {
                const response = await fetch('/admin/api/sync/trigger', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('Sync response:', result);
                showMessage(result.message || 'Sync completed', 'success');
                await loadSettings();
            } catch (error) {
                console.error('Error triggering sync:', error);
                showMessage(`Error: ${error.message}`, 'error');
            } finally {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        }

        function showMessage(text, type) {
            const msgEl = document.getElementById('message');
            msgEl.textContent = text;
            msgEl.className = `message ${type}`;
            msgEl.style.display = 'block';
            setTimeout(() => {
                msgEl.style.display = 'none';
            }, 4000);
        }

        // Setup toggle button event listeners
        document.addEventListener('DOMContentLoaded', function() {
            try {
                console.log('🟢 DOMContentLoaded fired');
                console.log('DOM elements:', {
                    jeraToggle: !!document.getElementById('jeraToggle'),
                    dryRunToggle: !!document.getElementById('dryRunToggle'),
                    connectorToggle: !!document.getElementById('connectorToggle'),
                    locationOverrideToggle: !!document.getElementById('locationOverrideToggle')
                });
                
                // Load settings first
                console.log('🔵 Calling loadSettings()');
                loadSettings();
                
                // Add click listeners to all toggle buttons
                const toggleButtons = document.querySelectorAll('.toggle-switch');
                console.log('🔵 Found', toggleButtons.length, 'toggle buttons');
                
                // JERA Toggle
                const jeraToggle = document.getElementById('jeraToggle');
                if (jeraToggle) {
                    console.log('✅ Attaching listener to JERA toggle');
                    jeraToggle.addEventListener('click', async function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('🟡 JERA toggle clicked - calling toggleSetting()');
                        await toggleSetting('jera.testing_mode');
                        return false;
                    });
                } else {
                    console.error('❌ JERA toggle button not found!');
                }
                
                // Dry-Run Toggle
                const dryRunToggle = document.getElementById('dryRunToggle');
                if (dryRunToggle) {
                    console.log('✅ Attaching listener to Dry-Run toggle');
                    dryRunToggle.addEventListener('click', async function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('🟡 Dry-Run toggle clicked - calling toggleSetting()');
                        await toggleSetting('dry_run.enabled');
                        return false;
                    });
                } else {
                    console.error('❌ Dry-Run toggle button not found!');
                }
                
                // Connector Toggle
                const connectorToggle = document.getElementById('connectorToggle');
                if (connectorToggle) {
                    console.log('✅ Attaching listener to Connector toggle');
                    connectorToggle.addEventListener('click', async function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('🟡 Connector toggle clicked - calling toggleSetting()');
                        await toggleSetting('enable_connector.enabled');
                        return false;
                    });
                } else {
                    console.error('❌ Connector toggle button not found!');
                }
                
                // Location Override Toggle
                const locationToggle = document.getElementById('locationOverrideToggle');
                if (locationToggle) {
                    console.log('✅ Attaching listener to Location Override toggle');
                    locationToggle.addEventListener('click', async function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('🟡 Location Override toggle clicked - calling toggleSetting()');
                        await toggleSetting('location_override.enabled');
                        return false;
                    });
                } else {
                    console.error('❌ Location Override toggle button not found!');
                }
                
                // Refresh settings every 5 seconds
                console.log('✅ Starting 5-second refresh interval');
                setInterval(loadSettings, 5000);
                
                console.log('🟢 All event listeners attached successfully!');
            } catch (error) {
                console.error('❌ ERROR during DOMContentLoaded setup:', error);
                console.error('Stack trace:', error.stack);
            }
        });
    </script>
</body>
</html>"""
    
    return html


def get_settings_endpoints():
    """Get all settings-related router endpoints."""
    return router
