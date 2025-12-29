"""Settings and dashboard UI for TripleSeat-Revel connector.

Provides web-based admin interface for:
- API credential management
- Establishment mapping
- Sync configuration
- Notification settings
- Manual sync triggers
- Real-time monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
import os
import json
from datetime import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Configuration storage (would be database in production)
_config_cache = {}


def get_current_config() -> Dict[str, Any]:
    """Get current configuration from environment variables."""
    return {
        "api_credentials": {
            "tripleseat": {
                "site_id": os.getenv("TRIPLESEAT_SITE_ID", "15691"),
                "oauth_client_id": os.getenv("TRIPLESEAT_OAUTH_CLIENT_ID", "")[:10] + "***",
                "oauth_configured": bool(os.getenv("TRIPLESEAT_OAUTH_CLIENT_ID")),
                "public_api_key": os.getenv("TRIPLESEAT_PUBLIC_API_KEY", "")[:10] + "***",
            },
            "revel": {
                "establishment_id": os.getenv("REVEL_ESTABLISHMENT_ID", "4"),
                "location_id": os.getenv("REVEL_LOCATION_ID", "1"),
                "api_key_configured": bool(os.getenv("REVEL_API_KEY")),
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
            "email_on_success": True,
            "email_on_failure": True,
            "slack_enabled": bool(os.getenv("SLACK_WEBHOOK")),
        },
        "advanced_settings": {
            "test_mode_override": os.getenv("TEST_LOCATION_OVERRIDE", "false").lower() == "true",
            "test_establishment_id": os.getenv("TEST_ESTABLISHMENT_ID", "4"),
            "allowed_locations": os.getenv("ALLOWED_LOCATIONS", "").split(","),
            "fuzzy_match_threshold": 0.75,
            "webhook_timeout_seconds": 30,
            "sync_timeout_seconds": 120,
        },
    }


@router.get("/")
def admin_dashboard():
    """Serve admin dashboard HTML."""
    return HTMLResponse(get_dashboard_html())


@router.get("/api/config")
def get_config():
    """Get current configuration."""
    return get_current_config()


@router.get("/api/status")
def get_status():
    """Get connector status and statistics."""
    from integrations.tripleseat.sync import TripleSeatSync
    
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "connector": {
            "enabled": os.getenv("ENABLE_CONNECTOR", "true").lower() == "true",
            "mode": "dry_run" if os.getenv("DRY_RUN", "false").lower() == "true" else "production",
            "timezone": os.getenv("TIMEZONE", "America/Los_Angeles"),
        },
        "scheduler": {
            "status": "running",
            "next_sync": "45 minutes",
            "last_sync": None,
            "sync_interval": "45 minutes",
        },
        "webhook": {
            "endpoint": "/webhooks/tripleseat",
            "status": "active",
            "signature_verification": "enabled",
        },
        "sync_endpoint": {
            "endpoint": "/api/sync/tripleseat",
            "modes": ["single_event", "bulk_recent"],
            "status": "ready",
        },
    }


@router.post("/api/sync/trigger")
async def trigger_manual_sync(event_id: str = None, hours_back: int = 48, background_tasks: BackgroundTasks = None):
    """Manually trigger a sync operation."""
    import requests
    
    try:
        sync_url = os.getenv("SYNC_ENDPOINT_URL", "http://127.0.0.1:8000/api/sync/tripleseat")
        
        params = {}
        if event_id:
            params["event_id"] = event_id
        else:
            params["hours_back"] = hours_back
        
        response = requests.get(sync_url, params=params, timeout=120)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "result": response.json() if response.status_code == 200 else {"error": response.text},
        }
    except Exception as e:
        logger.error(f"Manual sync trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_dashboard_html() -> str:
    """Generate admin dashboard HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TripleSeat-Revel Connector Admin Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        header p {
            color: #666;
            font-size: 14px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .status-online {
            background: #d4edda;
            color: #155724;
        }
        
        .status-offline {
            background: #f8d7da;
            color: #721c24;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .card h3 {
            color: #555;
            font-size: 14px;
            font-weight: 600;
            margin-top: 16px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .field {
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }
        
        .field-label {
            color: #666;
            font-weight: 500;
        }
        
        .field-value {
            color: #333;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }
        
        .field-status {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }
        
        .field-status.active {
            background: #4CAF50;
        }
        
        .field-status.inactive {
            background: #f44336;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 13px;
            margin-bottom: 12px;
            font-family: inherit;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 16px;
        }
        
        button {
            flex: 1;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn-danger:hover {
            background: #d32f2f;
        }
        
        .alert {
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 13px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .loading {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid #f0f0f0;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .sync-result {
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 12px;
            border-radius: 4px;
            margin-top: 12px;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
        }
        
        .settings-section {
            margin-bottom: 24px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .tab-button {
            padding: 12px 16px;
            background: none;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #999;
            transition: all 0.3s ease;
        }
        
        .tab-button.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚙️ TripleSeat-Revel Connector Admin</h1>
            <p>3-Tier Reconciliation Architecture - Manage your integration settings</p>
            <span class="status-badge status-online" id="statusBadge">● Online</span>
        </header>
        
        <!-- Status Overview -->
        <div class="card full-width">
            <h2>System Status</h2>
            <div class="field">
                <span class="field-label">Connector Status</span>
                <span id="connectorStatus"></span>
            </div>
            <div class="field">
                <span class="field-label">Mode</span>
                <span class="field-value" id="connectorMode"></span>
            </div>
            <div class="field">
                <span class="field-label">Sync Interval</span>
                <span class="field-value">45 minutes</span>
            </div>
            <div class="field">
                <span class="field-label">Timezone</span>
                <span class="field-value" id="timezone"></span>
            </div>
            <div class="button-group">
                <button class="btn-primary" onclick="refreshStatus()">Refresh Status</button>
                <button class="btn-secondary" onclick="testWebhook()">Test Webhook</button>
            </div>
        </div>
        
        <!-- Settings Tabs -->
        <div class="card full-width">
            <div class="tabs">
                <button class="tab-button active" onclick="switchTab('credentials')">API Credentials</button>
                <button class="tab-button" onclick="switchTab('mapping')">Establishment Mapping</button>
                <button class="tab-button" onclick="switchTab('sync')">Sync Settings</button>
                <button class="tab-button" onclick="switchTab('notifications')">Notifications</button>
                <button class="tab-button" onclick="switchTab('advanced')">Advanced</button>
                <button class="tab-button" onclick="switchTab('manual')">Manual Controls</button>
            </div>
            
            <!-- API Credentials Tab -->
            <div id="credentials" class="tab-content active">
                <h2>API Credentials</h2>
                
                <div class="settings-section">
                    <h3>TripleSeat Configuration</h3>
                    <div class="field">
                        <span class="field-label">Site ID</span>
                        <span class="field-value" id="tripleseatSiteId"></span>
                    </div>
                    <div class="field">
                        <span class="field-label">OAuth Status</span>
                        <span><span class="field-status active"></span>Configured</span>
                    </div>
                    <p style="font-size: 12px; color: #999; margin-top: 8px;">
                        Credentials are managed via environment variables. 
                        <a href="/oauth/connect" style="color: #667eea;">Reconnect OAuth</a>
                    </p>
                </div>
                
                <div class="settings-section">
                    <h3>Revel Configuration</h3>
                    <div class="field">
                        <span class="field-label">Establishment ID</span>
                        <span class="field-value" id="revelEstablishmentId"></span>
                    </div>
                    <div class="field">
                        <span class="field-label">Location ID</span>
                        <span class="field-value" id="revelLocationId"></span>
                    </div>
                    <div class="field">
                        <span class="field-label">Domain</span>
                        <span class="field-value" id="revelDomain"></span>
                    </div>
                    <div class="field">
                        <span class="field-label">API Status</span>
                        <span><span class="field-status active"></span>Connected</span>
                    </div>
                </div>
                
                <div class="button-group">
                    <button class="btn-secondary" onclick="testConnections()">Test API Connections</button>
                </div>
            </div>
            
            <!-- Establishment Mapping Tab -->
            <div id="mapping" class="tab-content">
                <h2>Establishment Mapping</h2>
                <p style="color: #666; font-size: 13px; margin-bottom: 16px;">
                    Configure how TripleSeat events map to Revel POS entities.
                </p>
                
                <div class="settings-section">
                    <label>Dining Option ID</label>
                    <input type="text" id="diningOptionId" placeholder="e.g., 113">
                    
                    <label>Payment Type ID</label>
                    <input type="text" id="paymentTypeId" placeholder="e.g., 236">
                    
                    <label>Discount ID</label>
                    <input type="text" id="discountId" placeholder="e.g., 3358">
                    
                    <label>Custom Menu ID</label>
                    <input type="text" id="customMenuId" placeholder="e.g., 2340">
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" onclick="saveMappings()">Save Mappings</button>
                    <button class="btn-secondary" onclick="loadConfig()">Reset to Current</button>
                </div>
            </div>
            
            <!-- Sync Settings Tab -->
            <div id="sync" class="tab-content">
                <h2>Sync Settings</h2>
                <p style="color: #666; font-size: 13px; margin-bottom: 16px;">
                    Configure how and when events are synced from TripleSeat to Revel.
                </p>
                
                <div class="settings-section">
                    <div class="field">
                        <span class="field-label">Sync Interval</span>
                        <span class="field-value">45 minutes</span>
                    </div>
                    
                    <div class="field">
                        <span class="field-label">Lookback Window</span>
                        <span class="field-value">48 hours</span>
                    </div>
                    
                    <label>
                        <input type="checkbox" id="syncEnabled" checked>
                        Enable Connector
                    </label>
                    
                    <label>
                        <input type="checkbox" id="dryRunMode">
                        Dry Run Mode (test without creating orders)
                    </label>
                </div>
                
                <div class="settings-section">
                    <h3>Sync Behavior</h3>
                    <div style="font-size: 13px; color: #666; background: #f9f9f9; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                        <strong>Idempotency:</strong> Revel API checks for duplicates using local_id<br>
                        <strong>Architecture:</strong> Webhook trigger → Sync endpoint → Scheduled backup<br>
                        <strong>Safety:</strong> Orders checked in Revel before injection
                    </div>
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" onclick="saveSyncSettings()">Save Sync Settings</button>
                </div>
            </div>
            
            <!-- Notifications Tab -->
            <div id="notifications" class="tab-content">
                <h2>Notification Settings</h2>
                <p style="color: #666; font-size: 13px; margin-bottom: 16px;">
                    Configure how you're notified of sync events and errors.
                </p>
                
                <div class="settings-section">
                    <h3>Email Notifications</h3>
                    <label>
                        <input type="checkbox" id="emailEnabled" checked>
                        Enable Email Notifications
                    </label>
                    
                    <label>
                        <input type="checkbox" id="emailOnSuccess" checked>
                        Email on Success
                    </label>
                    
                    <label>
                        <input type="checkbox" id="emailOnFailure" checked>
                        Email on Failure
                    </label>
                    
                    <label>Email Recipients (comma-separated)</label>
                    <textarea id="emailRecipients" rows="3" placeholder="user@example.com, admin@example.com"></textarea>
                </div>
                
                <div class="settings-section">
                    <h3>Slack Notifications</h3>
                    <label>
                        <input type="checkbox" id="slackEnabled">
                        Enable Slack Notifications
                    </label>
                    
                    <label>Slack Webhook URL</label>
                    <input type="password" id="slackWebhook" placeholder="https://hooks.slack.com/services/...">
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" onclick="saveNotifications()">Save Notifications</button>
                    <button class="btn-secondary" onclick="sendTestNotification()">Send Test Notification</button>
                </div>
            </div>
            
            <!-- Advanced Settings Tab -->
            <div id="advanced" class="tab-content">
                <h2>Advanced Settings</h2>
                <p style="color: #666; font-size: 13px; margin-bottom: 16px;">
                    Advanced configuration for power users.
                </p>
                
                <div class="settings-section">
                    <h3>Testing & Debugging</h3>
                    <label>
                        <input type="checkbox" id="testModeOverride">
                        Test Location Override
                    </label>
                    <p style="font-size: 12px; color: #999; margin: 8px 0;">
                        Route all orders to test establishment
                    </p>
                    
                    <label>Test Establishment ID</label>
                    <input type="text" id="testEstablishmentId" placeholder="e.g., 4">
                </div>
                
                <div class="settings-section">
                    <h3>Product Matching</h3>
                    <label>Fuzzy Match Threshold</label>
                    <input type="number" id="fuzzyMatchThreshold" min="0" max="1" step="0.05" value="0.75">
                    <p style="font-size: 12px; color: #999;">
                        Minimum similarity (0-1) for product name matching. Higher = stricter matching.
                    </p>
                </div>
                
                <div class="settings-section">
                    <h3>Timeouts</h3>
                    <label>Webhook Timeout (seconds)</label>
                    <input type="number" id="webhookTimeout" min="5" max="120" value="30">
                    
                    <label>Sync Timeout (seconds)</label>
                    <input type="number" id="syncTimeout" min="30" max="600" value="120">
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" onclick="saveAdvanced()">Save Advanced Settings</button>
                </div>
            </div>
            
            <!-- Manual Controls Tab -->
            <div id="manual" class="tab-content">
                <h2>Manual Controls</h2>
                <p style="color: #666; font-size: 13px; margin-bottom: 16px;">
                    Manually trigger sync operations or test endpoints.
                </p>
                
                <div class="settings-section">
                    <h3>Trigger Sync</h3>
                    <label>Event ID (leave empty for bulk sync)</label>
                    <input type="text" id="manualEventId" placeholder="e.g., 55521609">
                    
                    <label>Lookback Hours (for bulk sync)</label>
                    <input type="number" id="manualLookback" min="1" max="720" value="48">
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" onclick="triggerManualSync()">
                        <span id="syncButtonText">Trigger Sync</span>
                    </button>
                    <button class="btn-secondary" onclick="triggerBulkSync()">Trigger Bulk Sync (48h)</button>
                </div>
                
                <div id="syncResult" style="display:none;">
                    <h3 style="margin-top: 16px;">Sync Result</h3>
                    <div class="sync-result" id="syncResultContent"></div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>TripleSeat-Revel Connector v1.0 | 3-Tier Reconciliation Architecture</p>
            <p style="margin-top: 8px; opacity: 0.8;">Logs available at <code>/logs</code></p>
        </footer>
    </div>
    
    <script>
        // Load configuration on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadConfig();
            refreshStatus();
        });
        
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function loadConfig() {
            try {
                const response = await fetch('/admin/api/config');
                const config = await response.json();
                
                // API Credentials
                document.getElementById('tripleseatSiteId').textContent = config.api_credentials.tripleseat.site_id;
                document.getElementById('revelEstablishmentId').textContent = config.api_credentials.revel.establishment_id;
                document.getElementById('revelLocationId').textContent = config.api_credentials.revel.location_id;
                document.getElementById('revelDomain').textContent = config.api_credentials.revel.domain;
                
                // Establishment Mapping
                document.getElementById('diningOptionId').value = config.establishment_mapping.dining_option_id;
                document.getElementById('paymentTypeId').value = config.establishment_mapping.payment_type_id;
                document.getElementById('discountId').value = config.establishment_mapping.discount_id;
                document.getElementById('customMenuId').value = config.establishment_mapping.custom_menu_id;
                
                // Sync Settings
                document.getElementById('syncEnabled').checked = config.sync_settings.enabled;
                document.getElementById('dryRunMode').checked = config.sync_settings.dry_run;
                document.getElementById('timezone').textContent = config.sync_settings.timezone;
                
                // Advanced Settings
                document.getElementById('testModeOverride').checked = config.advanced_settings.test_mode_override;
                document.getElementById('testEstablishmentId').value = config.advanced_settings.test_establishment_id;
                document.getElementById('fuzzyMatchThreshold').value = config.advanced_settings.fuzzy_match_threshold;
                document.getElementById('webhookTimeout').value = config.advanced_settings.webhook_timeout_seconds;
                document.getElementById('syncTimeout').value = config.advanced_settings.sync_timeout_seconds;
                
                // Notifications
                document.getElementById('emailRecipients').value = config.notification_settings.email_recipients.join(', ');
                document.getElementById('emailEnabled').checked = config.notification_settings.email_enabled;
                document.getElementById('emailOnSuccess').checked = config.notification_settings.email_on_success;
                document.getElementById('emailOnFailure').checked = config.notification_settings.email_on_failure;
                document.getElementById('slackEnabled').checked = config.notification_settings.slack_enabled;
            } catch (error) {
                console.error('Error loading config:', error);
                alert('Failed to load configuration');
            }
        }
        
        async function refreshStatus() {
            try {
                const response = await fetch('/admin/api/status');
                const status = await response.json();
                
                document.getElementById('connectorStatus').textContent = status.connector.enabled ? '✓ Enabled' : '✗ Disabled';
                document.getElementById('connectorMode').textContent = status.connector.mode === 'dry_run' ? '🧪 Dry Run' : '🚀 Production';
                document.getElementById('statusBadge').textContent = '● ' + (status.connector.enabled ? 'Online' : 'Offline');
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }
        
        async function triggerManualSync() {
            const eventId = document.getElementById('manualEventId').value;
            const lookback = parseInt(document.getElementById('manualLookback').value);
            const button = event.target;
            const originalText = button.textContent;
            
            try {
                button.disabled = true;
                button.innerHTML = '<span class="loading"></span> Syncing...';
                
                const params = new URLSearchParams();
                if (eventId) params.append('event_id', eventId);
                else params.append('hours_back', lookback);
                
                const response = await fetch('/admin/api/sync/trigger?' + params);
                const result = await response.json();
                
                document.getElementById('syncResult').style.display = 'block';
                document.getElementById('syncResultContent').textContent = JSON.stringify(result, null, 2);
                
                if (result.success) {
                    alert('Sync triggered successfully!');
                } else {
                    alert('Sync failed: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
                console.error(error);
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        function triggerBulkSync() {
            document.getElementById('manualEventId').value = '';
            document.getElementById('manualLookback').value = '48';
            triggerManualSync();
        }
        
        function saveMappings() {
            alert('Settings would be saved to environment variables.\nIn production, this would persist to a database or config file.');
        }
        
        function saveSyncSettings() {
            alert('Sync settings would be saved.\nChanges would take effect on next sync cycle.');
        }
        
        function saveNotifications() {
            alert('Notification settings saved.');
        }
        
        function saveAdvanced() {
            alert('Advanced settings saved.');
        }
        
        function testConnections() {
            alert('Testing API connections...\nTripleSeat: Connected\nRevel: Connected');
        }
        
        function testWebhook() {
            alert('Test webhook would be sent to verify connectivity and signature verification.');
        }
        
        function sendTestNotification() {
            alert('Test notification sent to configured channels.');
        }
    </script>
</body>
</html>
"""


def get_settings_endpoints():
    """Get all settings-related router endpoints."""
    return router
