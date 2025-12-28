# Render Deployment & Verification Guide

## Pre-Deployment Verification (Local)

### 1. Run Test Suite
```bash
cd tripleseat-revel-connector
python test_verification.py
```

Expected output should show:
- ✓ All log messages with correlation IDs
- ✓ Response structure with ok, dry_run, site_id, time_gate
- ✓ Defensive validation errors caught
- ✓ All fields present in responses

### 2. Verify Imports
```bash
python -c "from app import app; print('App ready')"
```

Expected output:
```
INFO:app:Starting TripleSeat-Revel Connector
INFO:app:ENV: production
INFO:app:TIMEZONE: America/Los_Angeles
INFO:app:DRY_RUN: False
App ready
```

### 3. Check Endpoints
```bash
python -c "from app import app; print([r.path for r in app.routes if hasattr(r, 'path')])"
```

Expected output includes:
- /health
- /webhook
- /test/webhook
- /test/revel

## Render Deployment Steps

### 1. Environment Variables
Set in Render dashboard under **Settings > Environment**:

```
ENV=production
TIMEZONE=America/Los_Angeles
DRY_RUN=true
TRIPLESEAT_API_KEY=<your-api-key>
TRIPLESEAT_SIGNING_SECRET=<your-signing-secret>
REVEL_API_KEY=<your-api-key>
SENDGRID_API_KEY=<your-api-key>
TRIPLESEAT_EMAIL_SENDER=noreply@company.com
TRIPLESEAT_EMAIL_RECIPIENTS=ops@company.com,admin@company.com
```

**CRITICAL:** Set `DRY_RUN=true` initially for testing!

### 2. Deploy Service
```bash
git push render main
```

Monitor logs in Render dashboard during deployment.

### 3. Verify Startup
Check Render logs for:
```
INFO:app:Starting TripleSeat-Revel Connector
INFO:app:ENV: production
INFO:app:TIMEZONE: America/Los_Angeles
INFO:app:DRY_RUN: True
INFO:     Application startup complete.
```

## Post-Deployment Verification

### Test 1: Health Check
```bash
curl https://<render-service-url>/health
```

Expected response:
```json
{
  "status": "ok",
  "time": "2025-12-27T18:30:00-08:00"
}
```

### Test 2: Webhook Test Endpoint
```bash
curl -X POST https://<render-service-url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "id": "test-12345",
      "site_id": "1",
      "status": "Definite",
      "event_date": "2025-12-27T20:00:00Z"
    }
  }'
```

Expected response:
```json
{
  "ok": false,
  "dry_run": true,
  "site_id": "1",
  "time_gate": "UNKNOWN"
}
```

### Test 3: Verify Logs Show Correlation IDs
In Render dashboard logs, search for your request ID. You should see:

```
[req-abc12345] Webhook received
[req-abc12345] Payload parsed
[req-abc12345] Location resolved: 1
[req-abc12345] Event test-12345 failed validation: Failed to fetch event data
```

Every line should have the same correlation ID prefix.

### Test 4: Verify DRY_RUN Blocks Writes
Logs should show:
```
[req-{id}] DRY RUN ENABLED – skipping Revel write
```

**IMPORTANT:** No actual orders should be created in Revel POS when DRY_RUN=true.

### Test 5: Test Missing site_id Validation
```bash
curl -X POST https://<render-service-url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": {"id": "test-99999"}}'
```

Expected response:
```json
{"detail": "Missing or invalid site_id"}
```

Expected log:
```
[req-{id}] Webhook received
[req-{id}] Payload parsed
ERROR:integrations.tripleseat.webhook_handler:[req-{id}] Missing or invalid site_id
```

## Verification Monitoring (24-48 hours)

### Checklist
- [ ] Health endpoint responds consistently
- [ ] Test webhook requests return proper responses
- [ ] All logs show correlation ID prefixes
- [ ] No Revel API errors in logs
- [ ] No crashes or exceptions
- [ ] Response times reasonable (< 5 seconds for test endpoint)
- [ ] DRY_RUN logs appear for all webhook calls
- [ ] No emails sent (SendGrid should show no delivery when DRY_RUN=true)

### Common Issues & Solutions

**Issue:** No correlation ID in logs
- **Solution:** Check app.py line 43-44 - UUID generation and passing

**Issue:** Response missing fields
- **Solution:** Verify webhook_handler.py returns all response fields

**Issue:** DRY_RUN not blocking writes
- **Solution:** Check injection.py line 11-14 - DRY_RUN check

**Issue:** Time gate shows UNKNOWN
- **Solution:** This is expected when TripleSeat API isn't accessible (test mode)

**Issue:** Startup logs missing DRY_RUN status
- **Solution:** Check app.py line 25 - startup logging

## Transition to Production

Once verification complete and DRY_RUN behaves correctly:

### 1. Prepare
- [ ] Backup current Render environment
- [ ] Review all test results
- [ ] Notify stakeholders of transition

### 2. Enable Production Mode
In Render dashboard, update environment variable:
```
DRY_RUN=false
```

### 3. Monitor Intensively
- [ ] Watch logs continuously
- [ ] Check Revel POS for order creation
- [ ] Verify SendGrid delivery
- [ ] Monitor error rates

### 4. First Order Test
Have TripleSeat create a test event and verify:
1. Webhook received (logs show [req-{id}] Webhook received)
2. Event validated (logs show location resolved)
3. Time gate checked (logs show OPEN/CLOSED)
4. Order injected to Revel (logs show order ID)
5. Email sent (SendGrid delivery log)
6. Response returns ok: true

### 5. Rollback Plan
If issues occur, immediately set:
```
DRY_RUN=true
```

This will:
- Stop all Revel writes immediately
- Continue processing webhooks
- Allow investigation without causing data issues

## Logs Location

Access Render logs via:
1. Dashboard > Service > Logs
2. Or via CLI: `render logs --service-id <id> --follow`

## Key Log Signatures to Monitor

### Success Flow
```
[req-abc123] Webhook received
[req-abc123] Payload parsed
[req-abc123] Location resolved: 1
[req-abc123] Time gate: OPEN
[req-abc123] DRY RUN ENABLED – skipping Revel write
[req-abc123] Webhook completed
```

### Validation Failure
```
[req-abc123] Webhook received
[req-abc123] Payload parsed
[req-abc123] Location resolved: 1
[req-abc123] Event 12345 failed validation: <reason>
```

### Time Gate Closed
```
[req-abc123] Webhook received
[req-abc123] Payload parsed
[req-abc123] Location resolved: 1
[req-abc123] Time gate: CLOSED (TOO_EARLY)
```

## Support & Debugging

### Enable Debug Logging
If needed, update app.py line 16:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Common Grep Patterns
```bash
# Find all failures
render logs | grep "ERROR\|FAILED"

# Find specific correlation ID
render logs | grep "req-abc12345"

# Find DRY_RUN blocks
render logs | grep "DRY RUN ENABLED"

# Find validation errors
render logs | grep "failed validation"
```

## Summary

The TripleSeat-Revel Connector is fully verified and ready for:
1. ✅ Local testing (test_verification.py)
2. ✅ Render deployment (DRY_RUN=true)
3. ✅ Production monitoring (correlation IDs enable tracing)
4. ✅ Safe rollback (DRY_RUN=true stops writes immediately)

**Deployment Status: READY**
