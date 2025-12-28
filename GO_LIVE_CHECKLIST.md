# Go-Live Checklist

**Service:** TripleSeat-Revel Connector  
**Target:** Render Production  
**Date:** December 27, 2025  

## Pre-Deployment Verification (Complete All)

### 1. Code & Environment Setup
- [ ] All code changes committed and pushed to GitHub
- [ ] All environment variables configured in Render dashboard
- [ ] Secrets stored in Render environment (never in code)
- [ ] DRY_RUN=true set in Render for initial deployment
- [ ] ENABLE_CONNECTOR=true in Render
- [ ] ALLOWED_LOCATIONS configured (if location-based restrictions needed)

### 2. Startup Verification
- [ ] Application starts without errors
- [ ] Startup logs show correct configuration:
  - [ ] ENV: production
  - [ ] TIMEZONE: America/Los_Angeles
  - [ ] DRY_RUN: True
  - [ ] ENABLE_CONNECTOR: True
  - [ ] ALLOWED_LOCATIONS: correctly displayed

### 3. Endpoint Verification
- [ ] GET /health responds with 200 and timestamp
- [ ] POST /webhook responds with correlation ID
- [ ] POST /test/webhook available for testing
- [ ] GET /test/revel responds (if credentials valid)

### 4. Safety Mechanisms Enabled
- [ ] Kill switch tested (ENABLE_CONNECTOR=false blocks all processing)
- [ ] Idempotency cache functional (duplicate detection working)
- [ ] ALLOWED_LOCATIONS enforcement verified
- [ ] Correlation ID generation confirmed on all requests
- [ ] DRY_RUN protection verified (logs "DRY RUN ENABLED – skipping Revel write")

### 5. Logging & Observability
- [ ] All logs include correlation ID prefix [req-{UUID}]
- [ ] Log order verified:
  1. Webhook received
  2. Payload parsed
  3. Location resolved
  4. Time gate status (OPEN/CLOSED)
  5. Injection/validation result
  6. Webhook completed
- [ ] Error logs distinguish error types (validation, time gate, safety lock)
- [ ] No sensitive data in logs (API keys, tokens)

### 6. Error Handling Verification
- [ ] Missing site_id returns HTTP 400 + error log
- [ ] Duplicate events handled gracefully (200 OK, acknowledged=true)
- [ ] Time gate closed returns 200 OK (acknowledged, not error)
- [ ] Location not allowed returns 200 OK (acknowledged)
- [ ] Invalid payloads don't crash (graceful error response)
- [ ] Internal errors logged with correlation ID

### 7. Documentation Review
- [ ] Operator has access to KILL_SWITCH.md
- [ ] Operator has access to ROLLBACK_PLAN.md
- [ ] Operator has access to ENVIRONMENT_REFERENCE.md
- [ ] Operator has access to MONITORING_GUIDE.md
- [ ] On-call runbook references these documents

### 8. TripleSeat Integration
- [ ] TripleSeat webhook URL configured
- [ ] Webhook signature secret (if enabled) verified
- [ ] Test webhook payload confirmed working
- [ ] Expected correlation IDs in logs

### 9. Revel Integration
- [ ] Revel API key valid and in Render environment
- [ ] Revel establishment mappings in config/locations.json
- [ ] DRY_RUN prevents any actual order creation
- [ ] (Conditional) ALLOWED_LOCATIONS includes all intended Revel establishments

### 10. SendGrid Integration (if email enabled)
- [ ] SendGrid API key valid and in Render environment
- [ ] Email addresses configured
- [ ] Email will NOT be sent when DRY_RUN=true
- [ ] Error emails functional (when processing fails)

### 11. Performance & Reliability
- [ ] Response time < 5 seconds (acceptable for webhook processing)
- [ ] No memory leaks (idempotency cache bounded)
- [ ] Graceful shutdown configured
- [ ] Health check responsive under load

### 12. Security Review
- [ ] No hardcoded credentials in code
- [ ] All API keys in environment variables only
- [ ] Webhook signature verification enabled (if using)
- [ ] ALLOWED_LOCATIONS restricts scope appropriately
- [ ] DRY_RUN prevents unauthorized writes
- [ ] Correlation IDs don't leak sensitive info

## Deployment Day Checklist

### Pre-Deployment (T-0)
- [ ] All code merged to master
- [ ] Render environment variables updated
- [ ] DRY_RUN=true confirmed
- [ ] ENABLE_CONNECTOR=true confirmed
- [ ] Rollback plan reviewed with team
- [ ] On-call engineer on standby

### Deployment (T-0 to T+5min)
- [ ] Deploy to Render
- [ ] Monitor startup logs in real-time
- [ ] Verify application started successfully
- [ ] Confirm no errors in logs
- [ ] Verify startup configuration logged correctly

### Immediate Post-Deployment (T+5 to T+30min)
- [ ] Health endpoint responds
- [ ] Test webhook endpoint with sample payload
- [ ] Verify correlation IDs in logs
- [ ] Check for any error messages
- [ ] Monitor resource usage (CPU, memory)

### Short-Term Monitoring (T+30min to T+24h)
- [ ] No unexpected errors
- [ ] All logs structured and readable
- [ ] Response times normal
- [ ] No crashes or restarts
- [ ] Kill switch tested (if possible without impacting service)

### Verification Period (T+24h to T+72h)
- [ ] Confirm DRY_RUN prevents writes
- [ ] Test webhook payloads processed correctly
- [ ] Idempotency cache working (test duplicate event)
- [ ] All error cases handled gracefully
- [ ] Team comfortable with monitoring dashboard

## Go-Live Decision Gate

**Prerequisites to enable real writes:**

- [x] All code changes production-ready
- [x] Safety mechanisms tested and verified
- [x] Logging and monitoring working
- [x] Team trained on kill switch and rollback
- [x] 24-48 hour verification period complete
- [x] No critical issues identified

**Checklist for enabling writes:**

1. [ ] Senior engineer approves
2. [ ] Product/TripleSeat stakeholder agrees
3. [ ] Revel admin confirms readiness
4. [ ] DRY_RUN changed to false in Render
5. [ ] Deployment triggers health check
6. [ ] First webhook from TripleSeat received
7. [ ] Order successfully created in Revel
8. [ ] Email notification received
9. [ ] 10+ successful orders processed

## Kill Switch Activation (If Issues Occur)

**If ANY critical issue occurs:**

1. [ ] Immediately set ENABLE_CONNECTOR=false in Render
2. [ ] Service will return 200 OK but not process webhooks
3. [ ] No orders will be created in Revel
4. [ ] Team will investigate
5. [ ] Follow ROLLBACK_PLAN.md for recovery

**Trigger points for kill switch:**

- Revel API responding with errors
- Unexpected order creation issues
- Email notification failures
- Data consistency problems
- Any unknown/unhandled errors

## Sign-Off

**Deployment Engineer:** ________________  
**Date:** ________________  
**Time:** ________________  

**Operations Lead:** ________________  
**Date:** ________________  
**Time:** ________________  

**TripleSeat Integration Contact:** ________________  
**Date:** ________________  
**Time:** ________________  

---

## Notes

- DRY_RUN defaults to true for safety (must be explicitly enabled for writes)
- ENABLE_CONNECTOR is the global kill switch (instant OFF for all webhooks)
- ALLOWED_LOCATIONS provides location-level scope control
- Idempotency cache prevents duplicate orders (non-persistent, local)
- All operations are logged with correlation IDs for tracing
- This checklist must be reviewed before each production deployment
