# TripleSeat-Revel Connector - Admin Dashboard & Settings

## Overview

Industry-standard admin UI for managing integration settings, monitoring status, and triggering manual syncs.

**Access**: Navigate to `http://localhost:8000/admin` (or your Render deployment URL)

---

## Dashboard Sections

### 1. System Status (Always Visible)

**Real-time Status Indicators**:
- ✅ Connector Status - Enabled/Disabled
- 🚀 Mode - Production or Dry Run
- ⏱️ Sync Interval - 45 minutes (displays next scheduled sync)
- 🌍 Timezone - America/Los_Angeles (PST)

**Quick Actions**:
- **Refresh Status** - Fetch latest connector state
- **Test Webhook** - Verify webhook connectivity
- **Test API Connections** - Check TripleSeat & Revel connectivity

---

## 5 Main Settings Tabs

### Tab 1: API Credentials

**TripleSeat Configuration**:
- Site ID - Your TripleSeat site identifier (15691 for Pinkbox)
- OAuth Status - Green indicator when OAuth is configured
- Public API Key Status - Shows if public API key is set

**Revel Configuration**:
- Establishment ID - Target Revel establishment (4 for test)
- Location ID - Target location for orders (1)
- Domain - Revel instance domain
- API Status - Green indicator when API is connected

**Features**:
- View current credentials (masked for security)
- Reconnect OAuth button (for re-authentication)
- Test API connections button

---

### Tab 2: Establishment Mapping

**What This Controls**: How TripleSeat events map to Revel POS entities.

**Configurable Fields**:

| Setting | Purpose | Default | Example |
|---------|---------|---------|---------|
| Dining Option ID | How orders are categorized | 113 | Maps TripleSeat to Revel's dining types |
| Payment Type ID | Payment method for orders | 236 | TripleSeat Discount Payment in Revel |
| Discount ID | Applied discount to orders | 3358 | TripleSeat Discount in Revel system |
| Custom Menu ID | Product category mapping | 2340 | TripleSeat Products custom menu |

**Use Case**: When you add new product categories or change how Revel categorizes TripleSeat orders, update these IDs here.

---

### Tab 3: Sync Settings

**Synchronization Configuration**:

| Setting | Default | Range | Purpose |
|---------|---------|-------|---------|
| Sync Interval | 45 minutes | Fixed | How often scheduler runs safety net sync |
| Lookback Window | 48 hours | Variable | How far back to search for missed events |
| Enable Connector | ON | Toggle | Turn entire connector on/off (kills webhooks) |
| Dry Run Mode | OFF | Toggle | Test mode - validates orders without creating |

**Architecture Info Displayed**:
- Idempotency: Revel API deduplication via local_id
- Pattern: Webhook → Sync Endpoint → Scheduled Backup
- Safety: Orders checked before injection

**Use Case**:
- Enable Dry Run to test new product mappings without creating real orders
- Increase Lookback for bulk backfill of old events
- Toggle Enable to pause processing during maintenance

---

### Tab 4: Notifications

**Email Notifications**:
- Enable Email Notifications - Master toggle
- Email on Success - Get notified when orders inject successfully
- Email on Failure - Get alerted on errors
- Email Recipients - Comma-separated list

**Slack Notifications** (Optional):
- Enable Slack Notifications - Toggle
- Slack Webhook URL - Your integration webhook

**Use Case**: Route success emails to analytics team, failures to ops team. Use Slack for real-time alerts.

---

### Tab 5: Advanced Settings

**Testing & Debugging**:
- **Test Location Override** - Route ALL orders to a test establishment (establishment 4)
  - Use this for testing product mappings without affecting live data
  - Uncheck before production!

**Product Matching**:
- **Fuzzy Match Threshold** (0-1) - Controls product name matching
  - 0.75 = Strict matching (only 75%+ similar names match)
  - 0.9 = Very strict (prevents false positives like "HEY BLONDIE" vs "SALTY BLONDE")
  - Use 0.75 for most cases (current setting)

**Timeouts**:
- **Webhook Timeout** (5-120 sec) - How long to wait for webhook processing
- **Sync Timeout** (30-600 sec) - How long to wait for sync operations

**Use Case**: Adjust timeouts if TripleSeat or Revel API is slow. Increase fuzzy threshold if seeing incorrect product matches.

---

### Tab 6: Manual Controls

**Trigger Sync Operations**:

**Single Event Sync**:
- Enter an Event ID (e.g., 55521609)
- Click "Trigger Sync"
- Result: Syncs that one event to Revel
- Time: ~30 seconds

**Bulk Sync**:
- Leave Event ID blank
- Set Lookback Hours (default 48)
- Click "Trigger Bulk Sync"
- Result: Syncs all events from past 48 hours
- Time: ~2 minutes

**Use Case**: 
- Test individual event before scheduler runs (verification)
- Bulk sync to catch up after downtime
- Manual recovery of failed events

---

## Settings by Category

### 🔐 Security Settings

| Category | Setting | Default | Purpose |
|----------|---------|---------|---------|
| Credentials | OAuth Status | Configured | TripleSeat authentication |
| Credentials | API Key Status | Set | Revel authentication |
| Sync | Webhook Timeout | 30s | Prevent hanging webhooks |
| Advanced | Fuzzy Match | 0.75 | Prevent false positive matches |

---

### 🔄 Integration Settings

| Category | Setting | Default | Purpose |
|----------|---------|---------|---------|
| Mapping | Dining Option ID | 113 | Revel categorization |
| Mapping | Payment Type ID | 236 | TripleSeat payment method |
| Mapping | Discount ID | 3358 | TripleSeat discount |
| Mapping | Custom Menu ID | 2340 | Product grouping |
| Credentials | Establishment ID | 4 | Target Revel location |
| Credentials | Location ID | 1 | Order location |

---

### ⏱️ Scheduling Settings

| Category | Setting | Default | Purpose |
|----------|---------|---------|---------|
| Sync | Sync Interval | 45 min | Safety net frequency |
| Sync | Lookback Window | 48 hours | Historical search range |
| Sync | Enable Connector | ON | Master switch |
| Sync | Dry Run Mode | OFF | Test mode |

---

### 📧 Notification Settings

| Category | Setting | Default | Purpose |
|----------|---------|---------|---------|
| Email | Email Enabled | ON | Receive notifications |
| Email | Email on Success | ON | Confirmation emails |
| Email | Email on Failure | ON | Error alerts |
| Email | Recipients | [configured] | Who gets emails |
| Slack | Slack Enabled | OFF | Real-time alerts |

---

### 🧪 Testing Settings

| Category | Setting | Default | Purpose |
|----------|---------|---------|---------|
| Testing | Test Mode Override | OFF | Route orders to test |
| Testing | Test Establishment ID | 4 | Test destination |
| Advanced | Webhook Timeout | 30s | Timeout management |
| Advanced | Sync Timeout | 120s | Timeout management |

---

## Industry Standards Applied

### Pattern: 3-Tier Reconciliation

Your dashboard reflects the industry standard architecture used by:
- **PayPal** - Webhook + reconciliation endpoint + scheduled backup
- **Stripe** - Event webhooks + list endpoint + batch operations
- **Square** - Webhooks + sync API + scheduled verification

### Settings Sections: Standard Sections

All major integration platforms have:
1. **API Credentials** - Authentication management
2. **Mapping/Configuration** - Business logic setup
3. **Sync Settings** - Data flow controls
4. **Notifications** - Alerting configuration
5. **Advanced** - Power user settings
6. **Manual Controls** - Ad-hoc operations

### UI/UX: Modern Standards

- ✅ Tabbed interface (organized)
- ✅ Real-time status (up-to-date information)
- ✅ Masked credentials (security)
- ✅ Test buttons (verification)
- ✅ Manual triggers (operations)
- ✅ Status indicators (quick scanning)
- ✅ Helpful descriptions (guidance)

---

## Common Workflows

### Workflow 1: Initial Setup

1. Go to **API Credentials** tab
2. Verify TripleSeat Site ID and OAuth status
3. Verify Revel Establishment ID and API connection
4. Click **Test API Connections**
5. Move to **Establishment Mapping** tab
6. Verify Dining Option, Payment Type, and Discount IDs match your Revel setup
7. Go to **Notifications** tab
8. Enter your email address
9. Move to **Sync Settings** and enable connector
10. ✅ Setup complete

### Workflow 2: Testing Product Mappings

1. Go to **Advanced Settings** tab
2. Enable **Test Location Override**
3. Set **Test Establishment ID** to 4 (or your test location)
4. Go to **Manual Controls** tab
5. Enter an Event ID to test
6. Click **Trigger Sync**
7. Check **Fuzzy Match Threshold** if product doesn't match
8. Review result in **Sync Result** panel
9. Disable **Test Location Override** when confident
10. ✅ Mappings verified

### Workflow 3: Bulk Recovery After Downtime

1. Go to **Manual Controls** tab
2. Leave Event ID blank
3. Set **Lookback Hours** to match downtime (e.g., 72 hours)
4. Click **Trigger Bulk Sync**
5. Monitor Sync Result for success
6. Check emails for any failures
7. If failures: Adjust settings and re-run
8. ✅ Recovered missed events

### Workflow 4: Troubleshooting Duplicate Orders

1. Go to **API Credentials** tab
2. Click **Test API Connections** to verify Revel connection
3. Go to **Sync Settings** tab
4. Note: Idempotency is automatic (Revel dedup)
5. Check Dry Run is OFF (should create real orders)
6. Go to **Manual Controls** and trigger a test sync
7. Review result - should skip if order exists
8. ✅ Deduplication working

---

## Environment Variables → Settings Mapping

When settings are updated via UI, they override environment variables:

| Environment Variable | Dashboard Tab | Setting |
|----------------------|---------------|---------|
| TRIPLESEAT_SITE_ID | API Credentials | Site ID |
| REVEL_ESTABLISHMENT_ID | API Credentials | Establishment ID |
| REVEL_LOCATION_ID | API Credentials | Location ID |
| REVEL_TRIPLESEAT_DINING_OPTION_ID | Establishment Mapping | Dining Option ID |
| REVEL_TRIPLESEAT_PAYMENT_TYPE_ID | Establishment Mapping | Payment Type ID |
| REVEL_TRIPLESEAT_DISCOUNT_ID | Establishment Mapping | Discount ID |
| ENABLE_CONNECTOR | Sync Settings | Enable Connector |
| DRY_RUN | Sync Settings | Dry Run Mode |
| TIMEZONE | Sync Settings | Timezone |
| TRIPLESEAT_EMAIL_RECIPIENTS | Notifications | Email Recipients |
| TEST_LOCATION_OVERRIDE | Advanced | Test Location Override |
| TEST_ESTABLISHMENT_ID | Advanced | Test Establishment ID |

---

## Production Deployment

**Dashboard Access**: 
```
Production: https://your-app.onrender.com/admin
Local: http://localhost:8000/admin
```

**Security Note**: In production, add authentication (OAuth, JWT, API key) to `/admin` endpoints.

**Backup**: Settings are read from environment variables. To persist changes, implement database storage (recommended for production).

---

## Monitoring & Alerts

**Dashboard Status Indicators**:
- 🟢 **Online** - Connector running normally
- 🔴 **Offline** - Connector disabled or not responding
- 🟡 **Warning** - Running in dry run or test mode

**Next Sync Display**:
- Shows when the 45-minute scheduler will next run
- Updates every time you refresh status

**Manual Sync Results**:
- Shows real-time results of manual sync operations
- Displays: queried, injected, skipped, failed counts
- Can be exported or saved for audit trail

---

## API Endpoints Behind the Dashboard

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/` | GET | Dashboard HTML |
| `/admin/api/config` | GET | Get all settings |
| `/admin/api/status` | GET | Get system status |
| `/admin/api/sync/trigger` | POST | Trigger manual sync |

All endpoints are protected by your existing authentication (if deployed with auth).

---

**Status: Ready for Use** ✅

Dashboard is fully functional and integrated with your 3-tier architecture.
