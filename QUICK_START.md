# Quick-Start: Production Deployment

**For:** Operators and deployment engineers  
**Duration:** < 15 minutes to understand, < 5 minutes to deploy  

## TL;DR

1. Set environment variables in Render
2. Deploy to Render
3. Verify startup logs
4. Monitor webhooks (DRY_RUN=true prevents writes)
5. After 24-48 hours: Set DRY_RUN=false to enable writes

## Environment Variables (Required)

Copy these to Render **Settings > Environment**:

```env
ENV=production
TIMEZONE=America/Los_Angeles
DRY_RUN=true
ENABLE_CONNECTOR=true
TRIPLESEAT_API_KEY=<your-key>
REVEL_API_KEY=<your-key>
SENDGRID_API_KEY=<your-key>
TRIPLESEAT_EMAIL_SENDER=noreply@company.com
TRIPLESEAT_EMAIL_RECIPIENTS=ops@company.com
```

## Deployment Steps

### Step 1: Update Render Environment
1. Log in to Render.com
2. Select TripleSeat-Revel Connector service
3. Click **Settings**
4. Click **Environment**
5. Add/update the variables above
6. Click **Save**

### Step 2: Deploy
```bash
git push origin master
# Render auto-deploys on push
```

### Step 3: Verify Startup
Check Render logs for:
```
INFO:app:Starting TripleSeat-Revel Connector
INFO:app:ENV: production
INFO:app:TIMEZONE: America/Los_Angeles
INFO:app:DRY_RUN: True
INFO:app:ENABLE_CONNECTOR: True
```

### Step 4: Test Health
```bash
curl https://<your-render-url>/health

# Expected response:
# {"status": "ok", "time": "2025-12-27T..."}
```

### Step 5: Monitor Webhooks
- Watch Render logs in real-time
- Every webhook should log with [req-UUID] prefix
- DRY_RUN=true prevents Revel writes (EXPECTED)
- Look for "DRY RUN ENABLED – skipping Revel write" in logs

## Safety Features (All Enabled by Default)

| Feature | Variable | Current Value | What It Does |
|---------|----------|---------------|--------------|
| **Safe Writes** | DRY_RUN | true | Prevents Revel writes during verification |
| **Kill Switch** | ENABLE_CONNECTOR | true | Set to false to stop all processing immediately |
| **Location Scope** | ALLOWED_LOCATIONS | (empty) | Leave empty for now, configure later if needed |

## Verification Checklist (24-48 hours)

- [ ] Service running (health endpoint responds)
- [ ] Webhooks being received (check logs for [req-UUID])
- [ ] All logs include correlation ID
- [ ] No unexpected errors
- [ ] Response times < 5 seconds
- [ ] Startup logs show correct configuration
- [ ] Kill switch working (test by setting ENABLE_CONNECTOR=false)

## Enable Real Writes (After Verification)

Once verification complete:

1. Render dashboard > Settings > Environment
2. Change: `DRY_RUN=false`
3. Click Save (service redeploys < 30 seconds)
4. Verify logs show: `INFO:app:DRY_RUN: False`
5. Monitor first 20+ orders in Revel

## Emergency: Instant Shutdown

```bash
# Set in Render environment:
ENABLE_CONNECTOR=false

# Service will:
# - Return 200 OK to all webhooks
# - Not process anything
# - Stay healthy and responsive

# To resume:
ENABLE_CONNECTOR=true
```

## Common Issues

### Health check fails
```bash
curl https://<url>/health
# If 404 or timeout: Check Render logs for startup errors
```

### DRY_RUN value not changing
```
1. Verify change saved in Render dashboard
2. Wait 30+ seconds for redeploy
3. Check logs to confirm value changed
4. Restart service if needed
```

### Webhooks not appearing in logs
```
1. Verify ENABLE_CONNECTOR=true
2. Check TripleSeat is sending webhooks to correct URL
3. Verify webhook authentication if configured
4. Test with POST /test/webhook endpoint
```

## Documentation Files

Read these for detailed information:

1. **GO_LIVE_CHECKLIST.md** - Complete pre-deployment checklist
2. **KILL_SWITCH.md** - How to use emergency shutdown
3. **ROLLBACK_PLAN.md** - How to recover from incidents
4. **ENVIRONMENT_REFERENCE.md** - All environment variables explained
5. **MONITORING_GUIDE.md** - How to monitor and debug

## Quick Test

```bash
# Test webhook endpoint
curl -X POST https://<your-url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "id": "test-123",
      "site_id": "1",
      "status": "Definite"
    }
  }'

# Expected response:
# {
#   "ok": false,
#   "dry_run": true,
#   "site_id": "1",
#   "time_gate": "UNKNOWN"
# }

# Check logs for:
# [req-XXX] Webhook received
# [req-XXX] Payload parsed
# [req-XXX] Location resolved: 1
```

## Support

- **Issue?** Check logs for [req-UUID] prefix matching your request
- **Can't decode error?** See MONITORING_GUIDE.md for log reference
- **Need to stop everything?** Set ENABLE_CONNECTOR=false (instant)
- **Want to troubleshoot?** See ROLLBACK_PLAN.md

---

**Key Point:** DRY_RUN=true (current) means all logs are recorded and validated, but no orders written to Revel. This is SAFE for extended testing.

Change to DRY_RUN=false only after 24-48 hour verification period and team approval.
