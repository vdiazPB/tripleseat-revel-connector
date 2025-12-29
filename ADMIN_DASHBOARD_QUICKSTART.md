# Admin Dashboard - Quick Start Guide

## Accessing the Dashboard

### After Deployment

```
Local: http://localhost:8000/admin
Production: https://your-app.onrender.com/admin
```

Just navigate to the URL - no login required (add OAuth in production).

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  ⚙️ TripleSeat-Revel Connector Admin                │
│  3-Tier Reconciliation Architecture                 │
│  Status: ● Online                                   │
└─────────────────────────────────────────────────────┘

┌─ System Status ─────────────────────────────────────┐
│  Connector Status: ✓ Enabled                        │
│  Mode: 🚀 Production                                │
│  Sync Interval: 45 minutes                          │
│  Timezone: America/Los_Angeles                      │
│                                                     │
│  [Refresh Status] [Test Webhook]                    │
└─────────────────────────────────────────────────────┘

┌─ Settings ──────────────────────────────────────────┐
│  [API Credentials] [Mapping] [Sync] [Notifications] │
│  [Advanced] [Manual Controls]                       │
│                                                     │
│  ┌─ Selected Tab Content ──────────────────────┐   │
│  │                                             │   │
│  │ (Tab content displays here)                 │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Tab 1: API Credentials

### What You'll See

```
🔐 API Credentials
───────────────────────────────────────

TripleSeat Configuration
  Site ID: 15691
  OAuth Status: [●] Configured
  [Reconnect OAuth]

Revel Configuration
  Establishment ID: 4
  Location ID: 1
  Domain: pinkboxdoughnuts.revelup.com
  API Status: [●] Connected

[Test API Connections]
```

### When You'd Use It
- Initial setup (verify credentials are configured)
- Troubleshooting (test if APIs are reachable)
- Switching to different environment (but don't edit here - change .env)

---

## Tab 2: Establishment Mapping

### What You'll See

```
🗺️ Establishment Mapping
─────────────────────────────

Dining Option ID:        [113         ]
Payment Type ID:         [236         ]
Discount ID:             [3358        ]
Custom Menu ID:          [2340        ]

Configure how TripleSeat events map to Revel POS entities.

[Save Mappings] [Reset to Current]
```

### When You'd Use It
- Adding new dining option to Revel
- Changing payment method for TripleSeat orders
- Creating new discount codes
- Reorganizing product categories

### Example Change
If you create a new dining option in Revel with ID 200:
1. Update "Dining Option ID" to 200
2. Click "Save Mappings"
3. New orders will use this ID

---

## Tab 3: Sync Settings

### What You'll See

```
⏱️ Sync Settings
────────────────────────────────

Sync Interval:        45 minutes
Lookback Window:      48 hours

☑ Enable Connector
☑ Dry Run Mode (test without creating orders)

Sync Behavior Info:
─────────────────────
Idempotency: Revel API checks for duplicates using local_id
Architecture: Webhook trigger → Sync endpoint → Scheduled backup
Safety: Orders checked in Revel before injection

[Save Sync Settings]
```

### When You'd Use It

**Enable Connector**:
- Toggle OFF to pause all webhook processing
- Use when doing maintenance on Revel
- Webhooks queue, not dropped (resume when ready)

**Dry Run Mode**:
- Toggle ON to test without creating real orders
- Useful for testing new product mappings
- Orders validated but not injected into Revel
- Toggle OFF before production use

**Lookback Window**:
- Increase from 48 to 72 hours after downtime
- Scheduler will catch events from 3 days back
- Useful for bulk recovery

---

## Tab 4: Notifications

### What You'll See

```
📧 Notifications
────────────────────────────

Email Notifications
  ☑ Enable Email Notifications
  ☑ Email on Success
  ☑ Email on Failure
  
  Email Recipients:
  [vdiaz@weareamazing.com, admin@example.com]

Slack Notifications
  ☐ Enable Slack Notifications
  [https://hooks.slack.com/services/...]

[Save Notifications] [Send Test Notification]
```

### When You'd Use It

**Success Emails** (turn on):
- Confirms orders are injecting successfully
- Good for daily verification

**Failure Emails** (always on):
- Alerts you to injection failures
- Critical for troubleshooting

**Multiple Recipients**:
- Success → analytics team
- Failure → ops team

**Slack** (optional):
- Real-time alerts in Slack channel
- Faster than email for urgent issues

### Example Setup
```
Success emails: dataanalytics@company.com
Failure emails: devops@company.com, me@company.com
Slack: #tripleseat-alerts channel
```

---

## Tab 5: Advanced Settings

### What You'll See

```
🧪 Advanced Settings
─────────────────────

Testing & Debugging
  ☐ Test Location Override
    Route all orders to test establishment
  
  Test Establishment ID: [4]

Product Matching
  Fuzzy Match Threshold: [0.75]
  Minimum similarity (0-1) for product name matching.
  Higher = stricter matching.

Timeouts
  Webhook Timeout (seconds): [30]
  Sync Timeout (seconds): [120]

[Save Advanced Settings]
```

### When You'd Use It

**Test Location Override**:
1. Turn ON
2. Set test establishment (usually 4)
3. All orders go to establishment 4 instead of live
4. Test product mappings, prices, etc.
5. Turn OFF before production

**Fuzzy Match Threshold**:
- 0.75 = Strict (current, recommended)
- 0.90 = Very strict (prevents false positives)
- 0.50 = Loose (catches variations)
- Change if: "HEY BLONDIE" not matching "BLONDIE DONUT"

**Timeouts**:
- Webhook (default 30s) - increase if TripleSeat API is slow
- Sync (default 120s) - increase for bulk operations

---

## Tab 6: Manual Controls

### What You'll See

```
🎛️ Manual Controls
──────────────────

Trigger Sync
  Event ID (leave blank for bulk):
  [55521609        ]
  
  Lookback Hours (for bulk sync):
  [48]

[Trigger Sync] [Trigger Bulk Sync (48h)]

Sync Result
────────────────────────────────────────
{
  "success": true,
  "mode": "single",
  "summary": {
    "queried": 1,
    "injected": 1,
    "skipped": 0,
    "failed": 0
  },
  "events": [...]
}
```

### When You'd Use It

**Single Event Sync**:
- Event ID 55521609 has a problem
- Enter 55521609
- Click "Trigger Sync"
- See results in ~30 seconds

**Bulk Sync**:
- Server was down for 2 hours
- No lookback needed (default 48)
- Click "Trigger Bulk Sync"
- Catches all events in past 48 hours
- Takes ~2 minutes

**Bulk Recovery**:
- Server down for 3 days
- Change Lookback to 72 hours
- Click "Trigger Sync"
- Recovers all events since downtime

---

## Real-World Usage Scenarios

### Scenario 1: First Time Setup

1. **Navigate to** http://localhost:8000/admin
2. **Go to** API Credentials tab
3. **Verify**:
   - TripleSeat Site ID shows 15691
   - OAuth Status is "Configured" ✓
   - Revel Establishment ID shows 4
   - API Status is "Connected" ✓
4. **Click** "Test API Connections" → Should pass
5. **Go to** Establishment Mapping tab
6. **Verify** IDs match your Revel setup
7. **Go to** Notifications tab
8. **Enter** your email address
9. **Go to** Manual Controls tab
10. **Enter** Event ID 55521609 (test event)
11. **Click** "Trigger Sync"
12. **Wait** 30 seconds, check result
13. **✅ Setup complete!**

### Scenario 2: Testing New Product

1. **Go to** Advanced Settings tab
2. **Enable** "Test Location Override"
3. **Go to** Manual Controls
4. **Enter** Event ID with new product
5. **Click** "Trigger Sync"
6. **Check** result - if product didn't match:
   - **Go to** Advanced Settings
   - **Lower** Fuzzy Match Threshold to 0.50
   - **Retry** sync
7. **Once working**:
   - **Disable** "Test Location Override"
   - **Restore** Fuzzy threshold to 0.75
8. **✅ Product tested**

### Scenario 3: Server Downtime Recovery

1. **Server was down** from 2am to 5am
2. **Go to** Manual Controls tab
3. **Leave** Event ID blank (for bulk)
4. **Set** Lookback Hours to 24 (covers downtime + buffer)
5. **Click** "Trigger Bulk Sync"
6. **Wait** 2 minutes
7. **Check** result - shows queried, injected, skipped, failed
8. **Review** your email for details
9. **✅ Events recovered**

### Scenario 4: Troubleshooting Duplicate Orders

1. **Go to** System Status section
2. **Click** "Test API Connections"
3. **Should all be green** ✓
4. **If red**, fix connectivity first
5. **Go to** Sync Settings tab
6. **Verify** Enable Connector is ON
7. **Go to** Manual Controls
8. **Trigger** a sync
9. **Check** result - should skip if duplicate exists
10. **✅ Dedup working as expected**

---

## Tips & Tricks

### Tip 1: Test Before Production
- Always enable Test Location Override before testing mappings
- This prevents test data from hitting live Revel location

### Tip 2: Monitor Success Emails
- Email on success = early warning if something changes
- If you stop getting success emails, something may be wrong

### Tip 3: Use Slack for Emergencies
- Set up Slack for critical failures only
- Keeps you alert without email fatigue

### Tip 4: Manual Sync for Verification
- After major changes, manually sync an event
- Verify result looks right
- Then let scheduler take over

### Tip 5: Check Lookback After Outages
- After downtime, increase lookback hours
- Catch events from the entire downtime period
- Then reset to 48 hours

---

## When to Ask for Help

❌ **Something looks wrong if**:
- API Status shows ✗ Disconnected
- Manual sync shows "failed": true
- Email recipients are empty but notifications enabled
- Fuzzy match threshold too high (products not matching)

✅ **These are normal**:
- Events showing "status": "skipped" (duplicates)
- Zero failures when triggering sync
- Dry run mode showing orders but not in Revel
- Multiple test syncs in a row

---

## Quick Keyboard Shortcuts

| Action | Steps |
|--------|-------|
| Go Home | Type `http://localhost:8000/admin` |
| Test API | Go to Credentials tab → Test button |
| Test Event | Go to Manual Controls → Enter event ID → Trigger |
| Check Status | Go to System Status → Refresh Status button |

---

## Mobile Access

Dashboard is **fully responsive**:
- ✅ Works on iPhone/Android
- ✅ Works on iPad/tablets
- ✅ Works on desktop
- ✅ Single-column layout on mobile
- ✅ Touch-friendly buttons

Access from anywhere: `https://your-app.onrender.com/admin`

---

**Status: Ready to Use** ✅

Dashboard is live and ready for immediate use. 
Navigate to `/admin` to get started!
