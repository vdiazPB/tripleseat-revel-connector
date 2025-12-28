# Kill Switch Operations Guide

**Service:** TripleSeat-Revel Connector  
**Function:** Global on/off control for webhook processing  
**Response:** Graceful (200 OK acknowledged, no processing)  

## What is the Kill Switch?

The **ENABLE_CONNECTOR** environment variable is a global kill switch that instantly disables webhook processing without crashing the service.

**When enabled (true):**
- All webhooks are processed normally
- Orders injected to Revel (if DRY_RUN=false)
- Emails sent on success/failure

**When disabled (false):**
- All webhooks return 200 OK
- No processing occurs
- No side effects (no orders, no emails)
- Service stays running and healthy

## When to Use the Kill Switch

### Immediate Shutdown Scenarios

**Activate kill switch immediately if:**

1. **Revel API Issues**
   - Revel API returning 500 errors
   - Revel API connection failures
   - Revel responding with unexpected errors

2. **Data Integrity Issues**
   - Orders being created with wrong data
   - Multiple orders from single event
   - Inconsistent state detected

3. **Integration Failures**
   - SendGrid API failures
   - TripleSeat API disconnection
   - Unexpected error patterns in logs

4. **Unknown/Unhandled Errors**
   - Errors not matching known patterns
   - Repeated exception crashes
   - Any critical system error

5. **Security Incident**
   - Unauthorized access detected
   - Data breach indicators
   - Suspicious activity patterns

## How to Activate Kill Switch

### Method 1: Render Dashboard (Recommended)

1. Log in to Render.com dashboard
2. Select the TripleSeat-Revel Connector service
3. Click "Settings" tab
4. Find "Environment" section
5. Locate variable: `ENABLE_CONNECTOR`
6. Change value from `true` to `false`
7. Click "Save" button
8. Service will redeploy (< 30 seconds)
9. Verify in logs: "ENABLE_CONNECTOR: False"

### Method 2: Render CLI (If Dashboard Unavailable)

```bash
# Set kill switch OFF
render env update --service-id <service-id> ENABLE_CONNECTOR=false

# Verify change
render env get --service-id <service-id> | grep ENABLE_CONNECTOR
```

### Method 3: Emergency (Phone/Out-of-band)

If Render is unavailable:
1. Page on-call engineer
2. Have them execute Method 1 or 2
3. Provide this document as reference

## Verification After Kill Switch

After setting `ENABLE_CONNECTOR=false`, verify:

1. **Check Logs**
   ```
   Log message should show: "ENABLE_CONNECTOR: False"
   All new webhooks should log: "CONNECTOR DISABLED – event acknowledged"
   ```

2. **Test Webhook**
   ```bash
   curl -X POST https://<url>/test/webhook \
     -H "Content-Type: application/json" \
     -d '{"event": {"id": "test-kill", "site_id": "1"}}'
   ```
   
   **Expected response:**
   ```json
   {
     "ok": true,
     "acknowledged": true,
     "reason": "CONNECTOR_DISABLED"
   }
   ```

3. **Verify No Side Effects**
   - No new orders in Revel POS
   - No emails sent
   - Health endpoint still responds
   - Service still running

## Logs While Kill Switch Active

You'll see logs like:
```
INFO:app:[req-abc12345] CONNECTOR DISABLED – event acknowledged
```

This is **correct and expected behavior**.

## Re-enabling the Service

### After Issue Resolution

1. **Investigate Root Cause**
   - Review logs during incident
   - Identify what went wrong
   - Document findings

2. **Fix the Issue**
   - Deploy code fix if needed
   - Update configuration if needed
   - Verify fix in test environment

3. **Gradual Re-enablement**
   - Set ENABLE_CONNECTOR=true
   - Monitor logs for first webhook
   - Confirm success
   - Monitor next 10-20 webhooks
   - If all good, resume normal operations

### Re-enablement Steps

1. Log in to Render dashboard
2. Select service
3. Go to Settings > Environment
4. Set `ENABLE_CONNECTOR=true`
5. Click Save
6. Wait for service to redeploy
7. Verify logs show "ENABLE_CONNECTOR: True"

## DRY_RUN vs ENABLE_CONNECTOR

| Feature | ENABLE_CONNECTOR=false | DRY_RUN=true |
|---------|----------------------|--------------|
| **Purpose** | Emergency kill switch | Development/testing |
| **Response** | 200 OK (acknowledged) | Full processing |
| **Processing** | None | Full validation, time gate, injection (blocked) |
| **Logs** | "CONNECTOR DISABLED" | "DRY RUN ENABLED" |
| **Recovery** | Manual flip required | Can be used during development |
| **Use Case** | Production incident | Pre-production testing |

**Example:**
- Use `DRY_RUN=true` for 24-48 hour verification period before go-live
- Use `ENABLE_CONNECTOR=false` if production incident requires immediate shutdown

## Monitoring & Alerting

### Set Up Alerts

**Alert if ENABLE_CONNECTOR changes:**
```
Event: Environment variable modification
Service: TripleSeat-Revel Connector
Action: Page on-call engineer immediately
```

**Alert if kill switch is active > 1 hour:**
```
Condition: ENABLE_CONNECTOR=false for > 1 hour
Action: Escalate to engineering lead
```

### Manual Verification

Check kill switch status in logs:
```bash
# View recent startup logs
curl https://<url>/health  # Should return 200 OK

# Search logs for ENABLE_CONNECTOR
# Should show current value in startup output
```

## Runbook Summary

**Incident Detected** → Activate kill switch (< 2 min)  
↓  
**Service Disabled** → No new webhooks processed (< 30 sec)  
↓  
**Investigation** → Review logs, identify issue  
↓  
**Fix Applied** → Code deploy or config change  
↓  
**Gradual Re-enablement** → Watch first webhooks  
↓  
**Normal Operations** → Resume processing  

## FAQ

**Q: Will activating kill switch crash the service?**  
A: No. Service stays running, returns 200 OK, just doesn't process webhooks.

**Q: How long does kill switch take to activate?**  
A: < 30 seconds (Render redeploys environment variable change).

**Q: Can users see the difference when kill switch is active?**  
A: No. They receive 200 OK response. TripleSeat events are acknowledged but not processed.

**Q: Is data lost when kill switch is active?**  
A: No. Events are not created in Revel. When re-enabled, new events will be processed normally. Old events are not replayed (depends on TripleSeat retry policy).

**Q: What if I accidentally activate the kill switch?**  
A: Set ENABLE_CONNECTOR=true immediately. Service resumes in < 30 seconds. No data is lost.

**Q: Can I activate kill switch remotely?**  
A: Yes, via Render dashboard or CLI from anywhere.

**Q: Who should have access to activate kill switch?**  
A: On-call engineer, engineering lead, and operations team.

## Contact Information

**On-Call Engineer:** [Contact info]  
**Engineering Lead:** [Contact info]  
**Operations Lead:** [Contact info]  

---

**Last Updated:** December 27, 2025  
**Version:** 1.0
