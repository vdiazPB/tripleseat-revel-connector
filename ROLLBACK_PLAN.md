# Rollback Plan

**Service:** TripleSeat-Revel Connector  
**Trigger:** Critical issues in production  
**Recovery Time:** < 5 minutes  

## Rollback Scenarios

### Scenario 1: Critical Runtime Errors

**Symptoms:**
- Service crashes repeatedly
- Unhandled exceptions in logs
- Multiple 500 errors in response
- Health check failing

**Rollback Decision Tree:**
```
Are errors in logs clear and addressable?
├─ Yes → Fix code, deploy new version (5-10 min)
└─ No → Activate kill switch immediately
         └─ Then investigate root cause
```

**Steps:**
1. Activate kill switch: `ENABLE_CONNECTOR=false`
2. Service continues returning 200 OK (no processing)
3. Investigate logs for root cause
4. Deploy fix or revert to previous commit
5. Test fix in staging environment
6. Re-enable connector: `ENABLE_CONNECTOR=true`
7. Monitor first 20 webhooks

### Scenario 2: Data Integrity Issues

**Symptoms:**
- Duplicate orders in Revel
- Orders with incorrect data
- Missing fields in created orders
- Inconsistent state across systems

**Immediate Action:**
1. Activate kill switch immediately: `ENABLE_CONNECTOR=false`
2. Page on-call engineer and Revel admin
3. Stop all processing

**Investigation:**
1. Review logs for last successful order
2. Identify what changed in code
3. Check Revel API responses in logs
4. Verify mapping logic

**Recovery:**
1. If data corruption: Manual cleanup in Revel required
2. Fix code issue
3. Deploy corrected version
4. Re-enable: `ENABLE_CONNECTOR=true`
5. Resume with manual monitoring

### Scenario 3: Third-Party API Failures

**Symptoms:**
- Revel API returning errors
- SendGrid API failures
- TripleSeat webhook delivery issues
- Consistent 400/500 responses from external APIs

**Immediate Action:**
1. Activate kill switch: `ENABLE_CONNECTOR=false`
2. Contact affected third-party support
3. Verify their status page

**Recovery:**
1. Wait for third-party service recovery
2. Verify recovery with health check from their dashboard
3. Deploy hotfix if code needs update
4. Re-enable connector: `ENABLE_CONNECTOR=true`
5. Monitor 20+ webhooks

### Scenario 4: Security Incident

**Symptoms:**
- Unauthorized access attempts
- Data leaks detected
- API key compromise
- Suspicious patterns in logs

**Immediate Action:**
1. Activate kill switch: `ENABLE_CONNECTOR=false`
2. Page security team
3. Rotate all credentials
4. Review audit logs

**Recovery:**
1. Update new credentials in Render environment
2. Deploy security fixes if needed
3. Clear idempotency cache (service restart)
4. Re-enable: `ENABLE_CONNECTOR=true`
5. Monitor with security team present

## Rollback Methods

### Method 1: Kill Switch (Safest)

**What it does:**
- Disables webhook processing
- Service stays online and healthy
- Returns 200 OK (acknowledged but not processed)
- No side effects

**How to use:**
```
Set ENABLE_CONNECTOR=false in Render environment
Wait < 30 seconds for redeploy
Verify in logs: "ENABLE_CONNECTOR: False"
```

**Recovery time:** < 5 minutes to re-enable

**Best for:** Immediate shutdown while investigating

### Method 2: Code Rollback

**What it does:**
- Reverts to previous working version
- Requires code commit/push
- Full service restart

**How to use:**
```bash
git log --oneline | head -10  # Find last good commit
git revert <commit-hash>      # Or git reset
git push origin master         # Trigger Render redeploy
```

**Recovery time:** 2-5 minutes (code build + deploy)

**Best for:** Code bugs that need instant fix

### Method 3: Restart Service

**What it does:**
- Restarts application
- Clears memory caches
- Reloads environment variables

**How to use:**
1. Render dashboard → Service → More options → Restart
2. Wait for service to restart (< 1 minute)
3. Verify in logs

**Recovery time:** 1-2 minutes

**Best for:** Clearing corrupted in-memory state

### Method 4: Environment Variable Revert

**What it does:**
- Changes configuration value
- No code deploy needed
- Instant effect

**How to use:**
```
Render dashboard → Settings → Environment
Change problematic variable back to known-good value
Service redeploys < 30 seconds
```

**Recovery time:** < 30 seconds

**Best for:** Configuration mistakes (DRY_RUN, ALLOWED_LOCATIONS, etc.)

## Decision Tree

```
ISSUE DETECTED (T=0)
├─ Unknown cause
│  └─ → ACTIVATE KILL SWITCH (ENABLE_CONNECTOR=false)
│     └─ T+1: Investigate while service is safe
│     └─ T+10: Identify root cause
│     └─ T+15: Apply fix (code deploy or config change)
│     └─ T+25: Re-enable and monitor
│
├─ Code bug identified
│  └─ → REVERT COMMIT (git revert)
│     └─ T+2: Code build starts
│     └─ T+5: Deploy complete
│     └─ T+10: Monitor for recovery
│
├─ Configuration issue
│  └─ → FIX ENVIRONMENT VARIABLE
│     └─ T+1: Change value in Render
│     └─ T+2: Redeploy
│     └─ T+5: Monitor for recovery
│
├─ Third-party API down
│  └─ → ACTIVATE KILL SWITCH (ENABLE_CONNECTOR=false)
│     └─ Wait for third-party recovery
│     └─ Re-enable when confirmed
│
└─ Memory/state corruption
   └─ → RESTART SERVICE
      └─ Clears in-memory cache
      └─ Reloads environment
```

## Pre-Rollback Checklist

Before executing any rollback:

- [ ] Document current issue (screenshots, error messages)
- [ ] Note time of issue detection
- [ ] Identify which system is affected (Revel, SendGrid, TripleSeat)
- [ ] Check third-party status pages
- [ ] Review recent code changes
- [ ] Get approval from engineering lead (if possible)
- [ ] Notify stakeholders (TripleSeat, operations team)

## Rollback Verification

After any rollback, verify:

1. **Service Health**
   - [ ] GET /health returns 200 OK
   - [ ] Startup logs show correct configuration
   - [ ] No errors in application logs

2. **Processing Works**
   - [ ] POST /test/webhook returns valid response
   - [ ] Response includes correlation ID
   - [ ] Logs show proper execution flow

3. **Safety Mechanisms**
   - [ ] DRY_RUN value correct
   - [ ] ENABLE_CONNECTOR value correct
   - [ ] Kill switch functional (if tested)

4. **No Data Issues**
   - [ ] Revel orders are correct
   - [ ] No duplicate orders
   - [ ] Email logs show expected behavior

## Post-Rollback Investigation

1. **Review logs** for timeline of events
2. **Identify root cause** (code bug, third-party issue, configuration)
3. **Create fix** if code change needed
4. **Test in staging** before re-deploying
5. **Document incident** in postmortem
6. **Update procedures** if needed

## Communication During Rollback

**To TripleSeat:**
- Event: "Webhook processing temporarily paused for investigation"
- ETA: "< 5 minutes to resume"
- Status: Provide updates every 2 minutes

**To Operations:**
- Alert: Service status change and reason
- Action: Avoid manual intervention (automated recovery in progress)
- Timeline: Estimated recovery time

**To Team:**
- Slack: "Incident response in progress - kill switch activated"
- Link: This document
- DRI: Assign incident commander

## Rollback Metrics

Track rollbacks for post-incident analysis:

| Date | Time | Trigger | Method | Duration | Status |
|------|------|---------|--------|----------|--------|
| 2025-12-27 | HH:MM | Example | Kill Switch | 2 min | ✓ Success |

## Disaster Recovery (Complete Outage)

If service cannot be recovered:

1. **Immediate (< 5 min):**
   - Activate kill switch
   - Notify all stakeholders
   - Page backup engineer

2. **Short-term (5-30 min):**
   - Investigate in parallel
   - Prepare rollback from scratch
   - Have TripleSeat pause webhook delivery

3. **Medium-term (30 min - 2 hours):**
   - Full code review and testing
   - Manual testing of all integrations
   - Staged re-enablement

4. **Escalation (> 2 hours):**
   - Incident commander escalates to VP
   - Customer communication from leadership
   - Root cause analysis begins

## Emergency Contacts

**On-Call Engineer:** [Name] - [Phone] - [Slack]  
**Engineering Lead:** [Name] - [Phone] - [Slack]  
**Operations Lead:** [Name] - [Phone] - [Slack]  
**TripleSeat Contact:** [Name] - [Email] - [Phone]  
**Revel Contact:** [Name] - [Email] - [Phone]  

---

**Last Updated:** December 27, 2025  
**Version:** 1.0

**Key Principle:** *In production, kill switch first, investigate later. Service availability and data integrity first, feature delivery second.*
