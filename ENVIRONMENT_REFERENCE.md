# Environment Reference

**Service:** TripleSeat-Revel Connector  
**Deployment:** Render (Python 3.13)  
**Last Updated:** December 27, 2025  

## Environment Variables

All environment variables must be set in Render dashboard under **Settings > Environment**.

### Required Variables (Must Set)

| Variable | Type | Default | Purpose | Example |
|----------|------|---------|---------|---------|
| `ENV` | string | development | Deployment environment | `production` |
| `TIMEZONE` | string | UTC | Timezone for events and logging | `America/Los_Angeles` |
| `TRIPLESEAT_API_KEY` | secret | NONE | TripleSeat API authentication | `ts_live_xxx` |
| `REVEL_API_KEY` | secret | NONE | Revel POS API authentication | `revel_xxx` |
| `SENDGRID_API_KEY` | secret | NONE | SendGrid email API key | `SG.xxx` |

### Safety & Control Variables

| Variable | Type | Default | Purpose | Example |
|----------|------|---------|---------|---------|
| `DRY_RUN` | boolean | `true` | Enable/disable Revel write operations | `true` \| `false` |
| `ENABLE_CONNECTOR` | boolean | `true` | Global kill switch for all webhook processing | `true` \| `false` |
| `ALLOWED_LOCATIONS` | csv | EMPTY | Comma-separated site IDs to process (empty = all) | `1,2,5` |

### Email Variables (Optional)

| Variable | Type | Default | Purpose | Example |
|----------|------|---------|---------|---------|
| `TRIPLESEAT_EMAIL_SENDER` | email | NONE | Sender address for notifications | `noreply@company.com` |
| `TRIPLESEAT_EMAIL_RECIPIENTS` | csv | NONE | Recipients for success/failure emails | `ops@company.com,admin@company.com` |

### Optional Variables

| Variable | Type | Default | Purpose | Example |
|----------|------|---------|---------|---------|
| `TRIPLESEAT_SIGNING_SECRET` | secret | NONE | Webhook signature verification (if enabled) | `secret_xxx` |
| `LOG_LEVEL` | string | INFO | Python logging level | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |

## Pre-Production Configuration

**For 24-48 hour verification period:**

```
ENV=production
TIMEZONE=America/Los_Angeles
DRY_RUN=true
ENABLE_CONNECTOR=true
ALLOWED_LOCATIONS=                    # Empty = no restrictions
TRIPLESEAT_API_KEY=<production-key>
REVEL_API_KEY=<production-key>
SENDGRID_API_KEY=<production-key>
TRIPLESEAT_EMAIL_SENDER=noreply@company.com
TRIPLESEAT_EMAIL_RECIPIENTS=ops@company.com
```

**Expected behavior:**
- All webhooks processed fully
- Validation runs
- Time gate checked
- Revel writes SKIPPED (DRY_RUN=true)
- Emails NOT SENT (because no real orders)
- Logs show "DRY RUN ENABLED – skipping Revel write"

## Production Configuration

**After verification passes and approval obtained:**

Change only this variable:
```
DRY_RUN=false
```

**All others stay the same.**

**Expected behavior:**
- Orders written to Revel POS
- Emails sent on success/failure
- Logs show actual order IDs from Revel

## Safety Configuration (Gradual Rollout)

**If deploying to multiple locations:**

Set `ALLOWED_LOCATIONS` to restrict processing:

```
ALLOWED_LOCATIONS=1,2,5
```

**Behavior:**
- Only events from site IDs 1, 2, 5 are processed
- Events from other sites return 200 OK (acknowledged but not processed)
- Logs show: "Site X NOT in ALLOWED_LOCATIONS"

**Gradual expansion:**
1. Day 1: `ALLOWED_LOCATIONS=1` (single location)
2. Monitor 50+ webhooks, confirm all working
3. Day 2: `ALLOWED_LOCATIONS=1,2,5` (add more)
4. Monitor again
5. Day 3: `ALLOWED_LOCATIONS=` (empty = all locations, full rollout)

## Kill Switch Configuration

**To instantly disable all processing:**

```
ENABLE_CONNECTOR=false
```

**Behavior:**
- All webhooks return 200 OK immediately
- No processing occurs
- No side effects (no Revel writes, no emails)
- Logs show: "CONNECTOR DISABLED – event acknowledged"

**Recovery:**
```
ENABLE_CONNECTOR=true
```

**Action:** Takes < 30 seconds to take effect

## Startup Verification

After each deployment, verify logs show:

```
INFO:app:Starting TripleSeat-Revel Connector
INFO:app:ENV: production
INFO:app:TIMEZONE: America/Los_Angeles
INFO:app:DRY_RUN: True
INFO:app:ENABLE_CONNECTOR: True
INFO:app:ALLOWED_LOCATIONS: UNRESTRICTED
```

**OR:**

```
INFO:app:DRY_RUN: False                      # Real writes enabled
INFO:app:ENABLE_CONNECTOR: True
INFO:app:ALLOWED_LOCATIONS: ['1', '2', '5'] # Restricted locations
```

## Changing Variables

### Step-by-Step

1. Log in to Render.com
2. Select **TripleSeat-Revel Connector** service
3. Click **Settings** tab
4. Click **Environment** section
5. Find variable to change
6. Click **Edit** or **Update**
7. Change value
8. Click **Save**
9. Service redeploys automatically (< 30 seconds)
10. Verify new value in startup logs

### Via Render CLI

```bash
# Set single variable
render env update --service-id <id> DRY_RUN=false

# Verify change
render env get --service-id <id> | grep DRY_RUN

# View all variables
render env get --service-id <id>
```

### During Incident

```bash
# Activate kill switch
render env update --service-id <id> ENABLE_CONNECTOR=false

# Verify
render logs --service-id <id> --follow
# Should show: "ENABLE_CONNECTOR: False"
```

## Configuration Validation

### Pre-Deployment Checklist

Before setting variables, verify:

```bash
# Check all required variables are set
ENV=?                           # Must be "production"
TIMEZONE=?                      # Must be valid timezone
TRIPLESEAT_API_KEY=?            # Must start with ts_
REVEL_API_KEY=?                 # Must be set
SENDGRID_API_KEY=?              # Must start with SG.
DRY_RUN=true                    # Safe default
ENABLE_CONNECTOR=true           # Normal operation
ALLOWED_LOCATIONS=<empty>       # Unrestricted initially
```

### After Deployment Verification

```bash
# Test health endpoint
curl https://<url>/health
# Should return 200 with timestamp

# Check startup logs
# Should show correct ENV values

# Test webhook with missing site_id
curl -X POST https://<url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": {"id": "123"}}'
# Should return 400 (validation error)

# Test webhook with valid site_id
curl -X POST https://<url>/test/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": {"id": "123", "site_id": "1"}}'
# Should return 200 (acknowledged)
```

## Timezone Reference

Common timezones:

| Timezone | Region |
|----------|--------|
| `America/Los_Angeles` | Pacific Time (PT) |
| `America/Denver` | Mountain Time (MT) |
| `America/Chicago` | Central Time (CT) |
| `America/New_York` | Eastern Time (ET) |
| `UTC` | Coordinated Universal Time |
| `Europe/London` | London |
| `Australia/Sydney` | Sydney |

**Verify correct timezone:**
- Affects time gate calculations
- Affects event_date comparisons
- Affects log timestamps

## API Key Format Reference

### TripleSeat
- Format: `ts_live_xxx` or `ts_test_xxx`
- Length: ~30-50 characters
- Contains: Alphanumeric + underscores

### Revel
- Format: Varies (usually UUIDs or hex)
- Length: Usually 32-36 characters
- Specific format in Revel docs

### SendGrid
- Format: `SG.xxxx_xxxx_xxxx`
- Always starts with `SG.`
- Contains underscores, no spaces

## Secrets Management

**NEVER:**
- Put API keys in code
- Commit secrets to git
- Share keys in Slack/email
- Log full API keys
- Expose keys in URLs

**DO:**
- Use Render environment variables
- Rotate keys quarterly
- Use service account keys (if available)
- Log only last 4 characters (if needed): `key ending in xxx`
- Follow principle of least privilege

## Common Issues & Solutions

### "DRY_RUN: False" not applied

**Cause:** Environment variable not saved or service not redeployed  
**Solution:** Check Render dashboard shows variable change, wait 30 seconds, verify in logs

### "Missing or invalid site_id" errors

**Cause:** Event payload missing site_id field  
**Solution:** Verify TripleSeat is sending site_id, check webhook payload format

### "NOT in ALLOWED_LOCATIONS" logs

**Cause:** ALLOWED_LOCATIONS restricts site  
**Solution:** Add site ID to ALLOWED_LOCATIONS or empty it to allow all

### Orders not appearing in Revel

**Likely causes:**
1. DRY_RUN=true (blocking writes) - EXPECTED in pre-production
2. Revel API key invalid - Check key in logs
3. Time gate closed - Check timezone and event_date
4. ALLOWED_LOCATIONS doesn't include site - Add to list

## Monitoring Variables

**Check these values regularly:**

```bash
# Via dashboard logs
# Should see on startup:
ENV: production
DRY_RUN: true/false
ENABLE_CONNECTOR: true/false
ALLOWED_LOCATIONS: correct value

# Via health endpoint
curl https://<url>/health
# Response includes current timezone
```

## Updating Secrets Safely

1. Generate new API key in third-party platform
2. Test new key in staging (if possible)
3. Update in Render environment
4. Wait 30 seconds for redeploy
5. Verify in logs (no errors)
6. Revoke old key in third-party platform
7. Document rotation in change log

---

**Last Updated:** December 27, 2025  
**Version:** 1.0
