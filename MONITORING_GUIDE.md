# Monitoring & Observability Guide

**Service:** TripleSeat-Revel Connector  
**Deployment:** Render (Real-time logs)  
**Metrics:** Correlation IDs, error classification, response times  

## Overview

All webhook processing is fully observable through:
- Real-time logs with correlation IDs
- Structured error codes
- Clear state transitions
- Response time metrics

**No external monitoring required** (but integration recommended).

## Log Monitoring

### Real-Time Log Access

```bash
# Via Render CLI (recommended)
render logs --service-id <service-id> --follow

# Via Render Dashboard
# Settings > Logs tab > View logs in browser
```

### Expected Log Patterns

#### Successful Processing (DRY_RUN=true)

```
INFO:app:[req-abc12345] WEBHOOK INVOKED
INFO:integrations.tripleseat.webhook_handler:[req-abc12345] Webhook received
INFO:integrations.tripleseat.webhook_handler:[req-abc12345] Payload parsed
INFO:integrations.tripleseat.webhook_handler:[req-abc12345] Location resolved: 1
INFO:integrations.tripleseat.validation:[req-abc12345] Validation: Event is Definite
INFO:integrations.tripleseat.webhook_handler:[req-abc12345] Time gate: OPEN
INFO:integrations.revel.injection:[req-abc12345] DRY RUN ENABLED – skipping Revel write
INFO:emailer.sendgrid_emailer:[req-abc12345] Success email sent for event 12345
INFO:integrations.tripleseat.webhook_handler:[req-abc12345] Webhook completed
```

**All logs for single request have same correlation ID: `[req-abc12345]`**

#### Kill Switch Active

```
INFO:app:[req-def67890] CONNECTOR DISABLED – event acknowledged
```

No other logs follow. Response returns immediately.

#### Duplicate Event Detection

```
INFO:integrations.tripleseat.webhook_handler:[req-ghi11111] Webhook received
INFO:integrations.tripleseat.webhook_handler:[req-ghi11111] Payload parsed
INFO:integrations.tripleseat.webhook_handler:[req-ghi11111] Location resolved: 1
INFO:integrations.tripleseat.webhook_handler:[req-ghi11111] Duplicate event detected (idempotency): 1:12345:2025-12-27T18:00:00Z
```

Response: `ok: true, acknowledged: true, reason: "DUPLICATE_EVENT"`

#### Location Not Allowed

```
INFO:integrations.tripleseat.webhook_handler:[req-jkl22222] Webhook received
INFO:integrations.tripleseat.webhook_handler:[req-jkl22222] Payload parsed
INFO:integrations.tripleseat.webhook_handler:[req-jkl22222] Location resolved: 7
WARNING:integrations.tripleseat.webhook_handler:[req-jkl22222] Site 7 NOT in ALLOWED_LOCATIONS: ['1', '2', '5']
```

Response: `ok: true, acknowledged: true, reason: "LOCATION_NOT_ALLOWED"`

#### Time Gate Closed

```
INFO:integrations.tripleseat.webhook_handler:[req-mno33333] Webhook received
INFO:integrations.tripleseat.webhook_handler:[req-mno33333] Payload parsed
INFO:integrations.tripleseat.webhook_handler:[req-mno33333] Location resolved: 1
INFO:integrations.tripleseat.time_gate:[req-mno33333] Time gate: CLOSED (TOO_EARLY)
```

Response: `ok: true, dry_run: true, site_id: 1, time_gate: "CLOSED"`

#### Validation Error

```
INFO:integrations.tripleseat.webhook_handler:[req-pqr44444] Webhook received
INFO:integrations.tripleseat.webhook_handler:[req-pqr44444] Payload parsed
INFO:integrations.tripleseat.webhook_handler:[req-pqr44444] Location resolved: 1
INFO:integrations.tripleseat.validation:[req-pqr44444] Validation: Event status not Definite
INFO:integrations.tripleseat.webhook_handler:[req-pqr44444] Event 98765 failed validation: Event status not Definite
```

Response: `ok: false, dry_run: true, site_id: 1, time_gate: "UNKNOWN"`

#### Missing site_id (HTTP 400)

```
INFO:app:[req-stu55555] WEBHOOK INVOKED
INFO:integrations.tripleseat.webhook_handler:[req-stu55555] Webhook received
INFO:integrations.tripleseat.webhook_handler:[req-stu55555] Payload parsed
ERROR:integrations.tripleseat.webhook_handler:[req-stu55555] Missing or invalid site_id
```

Response: HTTP 400, `{"detail": "Missing or invalid site_id"}`

#### Internal Error

```
INFO:integrations.tripleseat.webhook_handler:[req-vwx66666] Webhook received
ERROR:integrations.tripleseat.webhook_handler:[req-vwx66666] Pipeline failed for event 12345: ConnectionError: Failed to connect to TripleSeat API
ERROR:integrations.tripleseat.webhook_handler:[req-vwx66666] Failed to send failure email
```

Response: `ok: false, error: "ConnectionError: ...", correlation_id: vwx66666`

## Error Classification

### HTTP Status Codes

| Status | Scenario | Example Log |
|--------|----------|-------------|
| **200** | All webhooks accepted | Normal processing or kill switch |
| **400** | Bad request (missing site_id) | "Missing or invalid site_id" |
| **500** | Internal error | "Pipeline failed:", "Failed to send email" |

### Response Structure

```json
{
  "ok": true|false,
  "dry_run": true|false,
  "site_id": "1",
  "time_gate": "OPEN|CLOSED|UNKNOWN",
  "correlation_id": "abc12345",
  "acknowledged": true|false,
  "reason": "DUPLICATE_EVENT|LOCATION_NOT_ALLOWED|CONNECTOR_DISABLED"
}
```

### Log Levels

| Level | Severity | Example |
|-------|----------|---------|
| **INFO** | Normal operation | "Webhook received", "Time gate: OPEN" |
| **WARNING** | Expected but attention needed | "Site X NOT in ALLOWED_LOCATIONS" |
| **ERROR** | Problem occurred | "failed validation", "Pipeline failed" |

## Monitoring Checklist (Daily)

### Morning Check
- [ ] Service is running (GET /health → 200)
- [ ] Startup logs show correct configuration (DRY_RUN, ENABLE_CONNECTOR, ALLOWED_LOCATIONS)
- [ ] No error spikes in last 24 hours
- [ ] Correlation IDs present on all logs

### During Business Hours
- [ ] Monitor incoming webhook count
- [ ] Check for any ERROR level logs
- [ ] Verify response times < 5 seconds
- [ ] Confirm emails sent for successful events (if DRY_RUN=false)

### End of Day
- [ ] Review error logs from entire day
- [ ] Check Revel for expected order counts
- [ ] Verify no duplicate orders created
- [ ] Note any patterns for investigation

## Alerting & Notifications

### Automatic Alerts (Recommended Setup)

**Alert if:**

1. **Service Health Down**
   - Condition: GET /health returns non-200
   - Action: Page on-call engineer immediately
   - Escalation: After 5 minutes, escalate to lead

2. **Error Rate High**
   - Condition: > 5 ERROR logs in 5 minute window
   - Action: Notify ops team
   - Investigation: Check Revel/TripleSeat status

3. **Response Time Slow**
   - Condition: Webhook response time > 10 seconds
   - Action: Monitor for memory/CPU issues
   - Escalation: Check external API response times

4. **Kill Switch Active**
   - Condition: ENABLE_CONNECTOR=false
   - Action: Page on-call engineer
   - Escalation: If > 1 hour, notify lead

### Manual Notifications

Check these regularly:
```bash
# Count errors in last hour
render logs | grep "ERROR" | tail -100

# Find slowest webhooks
render logs | grep "\[req-" | grep -E "[0-9]+ms"

# Check for kill switch
render logs | grep "CONNECTOR DISABLED" | wc -l

# Search for specific event
render logs | grep "event_id=12345"
```

## Performance Metrics

### Expected Performance

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| Response time | < 1 second | > 10 seconds |
| 200 OK responses | > 95% | < 90% |
| Error logs | < 5% | > 10% |
| Processing rate | Depends on volume | N/A |

### Measuring Response Time

Check logs for patterns:

**Expected (fast):**
```
[req-abc] WEBHOOK INVOKED
[req-abc] Webhook completed
(Total time: < 1 second)
```

**Slow (investigate):**
```
[req-def] WEBHOOK INVOKED
... (delays here)
[req-def] Webhook completed
(Total time: > 10 seconds)
```

**Likely causes of slow responses:**
1. External API (TripleSeat, Revel) is slow
2. Service resource constrained (CPU, memory)
3. Network latency to third-party services

## Key Metrics Dashboard

### Recommended Dashboard (in your monitoring tool)

```
┌─────────────────────────────────────────┐
│ TripleSeat-Revel Connector Status       │
├─────────────────────────────────────────┤
│ Uptime: 99.9%                          │
│ Webhooks Processed (24h): 1,247        │
│ Success Rate: 97.3%                    │
│ Error Rate: 2.7%                       │
│ Avg Response Time: 0.8s                │
│ P95 Response Time: 3.2s                │
│ Recent Errors: 5 in last hour          │
│ Kill Switch Status: OFF (enabled)      │
│ DRY_RUN Status: False (live writes)    │
└─────────────────────────────────────────┘
```

## Debugging with Correlation IDs

**Every webhook has a unique correlation ID for tracing.**

### Find all logs for a single webhook

```bash
# If you have the correlation ID
render logs --service-id <id> | grep "req-abc12345"

# This returns:
# - Webhook received
# - Payload parsed
# - All pipeline steps
# - Completion or error
```

### Find webhooks with errors

```bash
# All error logs (correlation IDs included)
render logs | grep "ERROR"

# Extract correlation ID from error
# Example: [req-xyz99999] Pipeline failed...
# Then search for all [req-xyz99999] logs
```

### Correlate with TripleSeat event

```bash
# If you have TripleSeat event ID
render logs | grep "event_12345"

# This shows all logs for that specific event
```

## Long-Term Monitoring (Weekly)

### Weekly Review

1. **Count webhooks by outcome:**
   - Successful (ok: true)
   - Blocked by time gate
   - Blocked by ALLOWED_LOCATIONS
   - Validation failed
   - Internal errors

2. **Error analysis:**
   - Most common errors
   - Error trends (increasing/decreasing)
   - External API issues

3. **Performance trends:**
   - Average response time
   - Peak response time
   - Correlation with webhook volume

4. **Integration health:**
   - Revel API: Error rate, speed
   - SendGrid: Email delivery rate
   - TripleSeat: Webhook delivery count

### Monthly Review

1. **Capacity planning:**
   - Webhook volume trends
   - Peak concurrent requests
   - Resource usage patterns

2. **Reliability:**
   - Uptime percentage
   - Critical incident count
   - Mean time to recovery

3. **Cost analysis:**
   - API call volumes
   - Email count
   - Render compute usage

## Testing Observability

### Test Correlation ID Propagation

```bash
# Send test webhook
curl -X POST https://<url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": {"id": "test-123", "site_id": "1"}}'

# Search logs for correlation ID from response
render logs | grep "req-"

# Verify all logs use same ID
```

### Test Error Logging

```bash
# Test missing site_id (should log error)
curl -X POST https://<url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": {"id": "test-456"}}'

# Check logs for ERROR level and proper details
render logs | grep "ERROR"
```

### Test Kill Switch

```bash
# Set ENABLE_CONNECTOR=false via Render dashboard

# Send webhook
curl -X POST https://<url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": {"id": "test-789", "site_id": "1"}}'

# Check logs
# Should show: "CONNECTOR DISABLED – event acknowledged"
# No other processing logs

# Re-enable: Set ENABLE_CONNECTOR=true
```

## Incident Response

### When Alert Fires

1. **Check service health**
   ```bash
   curl https://<url>/health
   ```

2. **Review recent logs**
   ```bash
   render logs --follow | head -50
   ```

3. **Identify pattern**
   - Single error or repeated?
   - Specific event IDs affected?
   - External API or internal?

4. **Take action**
   - Kill switch if severe: `ENABLE_CONNECTOR=false`
   - Check environment variables
   - Review external API status pages
   - Contact on-call engineer

### Common Alerts & Responses

| Alert | Likely Cause | First Action |
|-------|-------------|--------------|
| Health check fails | Service crashed | Restart service |
| High error rate | External API down | Check status page |
| Slow responses | Resource constraints | Check CPU/memory |
| Kill switch active | Manual activation | Investigate why |
| Duplicate orders | Idempotency failed | Check timestamps |

---

**Last Updated:** December 27, 2025  
**Version:** 1.0

**Remember:** Every log entry includes a correlation ID. Use it to trace end-to-end execution for any webhook request.
