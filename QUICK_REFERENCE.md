# Quick Reference: 3-Tier Architecture

## What Was Built

Industry-standard webhook → sync endpoint → scheduled task pattern.

```
Webhook Trigger (5 sec) → Sync Endpoint (30 sec) → Scheduled Task (every 45 min)
```

## Endpoints

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|----------------|
| `/webhooks/tripleseat` | POST | Webhook entry point | ~5 sec (async) |
| `/api/sync/tripleseat?event_id=X` | GET | Single event sync | ~30 sec |
| `/api/sync/tripleseat?hours_back=48` | GET | Bulk recent sync | ~2 min |

## Files Changed

```
app.py
  - Added APScheduler initialization
  - Added /api/sync/tripleseat endpoint
  - Added scheduled task (every 45 minutes)

integrations/tripleseat/webhook_handler.py
  - STEP 5c: Changed from direct inject_order() to sync endpoint call
  - Webhook now purely a trigger

requirements.txt
  - Added: apscheduler

integrations/tripleseat/sync.py (already created)
  - No changes needed, endpoint uses this
```

## How It Works

### Webhook Arrives
```
POST /webhooks/tripleseat
{
  "webhook_trigger_type": "UPDATE_EVENT",
  "event": {
    "id": "55521609",
    "site_id": "15691",
    ...
  }
}
```

### Webhook Handler Processing
1. Verify signature (HMAC)
2. Validate trigger type
3. Check idempotency cache
4. **NEW**: Call sync endpoint: `GET /api/sync/tripleseat?event_id=55521609`
5. Return 200 to TripleSeat
6. Send email with result

### Sync Endpoint Processing
1. Create TripleSeatSync instance
2. Call `sync_event(event_id)` or `sync_recent_events(hours_back)`
3. For each event:
   - Fetch from TripleSeat API
   - Check Revel for duplicate (local_id lookup)
   - Inject if new
   - Collect results
4. Return summary: `{success, mode, summary, events}`

### Scheduled Task (Every 45 Min)
1. Background job starts
2. Calls: `GET /api/sync/tripleseat?hours_back=48`
3. Catches any missed webhooks
4. Logs summary to console/files

## Testing

### Test Single Event
```bash
curl "http://localhost:8000/api/sync/tripleseat?event_id=55521609"
```

### Test Bulk Recent
```bash
curl "http://localhost:8000/api/sync/tripleseat?hours_back=48"
```

### Test Full Flow
```bash
python test_architecture.py
```

## Deployment Checklist

- [ ] Run `pip install -r requirements.txt` (installs apscheduler)
- [ ] Test locally: `python test_architecture.py`
- [ ] Verify sync endpoint: `curl http://localhost:8000/api/sync/tripleseat?event_id=55521609`
- [ ] Commit changes
- [ ] Deploy to Render
- [ ] Check logs for "APScheduler initialized"
- [ ] Wait 45 minutes for first scheduled sync
- [ ] Check logs: "Starting scheduled sync task"

## Rollback

If issues:
1. Revert webhook_handler.py (remove sync endpoint call)
2. Uncomment `inject_order()` call
3. Deploy again

## Monitoring

Watch logs for:
- `[scheduled-X] Starting scheduled sync task` (every 45 min)
- `[sync-X] Sync completed - Queried: X, Injected: Y, Skipped: Z, Failed: W`
- `ERROR` or `FAIL` entries

## Key Benefits

✅ **No Duplicates** - Revel API checks `local_id` (source of truth)
✅ **Catches Missed Webhooks** - Scheduled task runs every 45 minutes
✅ **Manual Sync** - Call endpoint anytime to sync specific event or bulk
✅ **Audit Trail** - All syncs logged with correlation IDs
✅ **Industry Standard** - Matches PayPal/Stripe/Square patterns
✅ **Reliable** - Double-safeguard against missed events

## Architecture Pattern

```
BEFORE (Unreliable):
  Webhook → Direct Inject (single point of failure, no safety net)

AFTER (Reliable):
  Webhook → Sync Endpoint ← Scheduled Task (dual triggers, audit trail)
```

## Environment Variables

No new variables required. Existing variables still apply:
- `TRIPLESEAT_SITE_ID` (used by sync module)
- `REVEL_ESTABLISHMENT_ID` (used by sync module)
- `REVEL_LOCATION_ID` (used by sync module)
- All OAuth/API credentials (unchanged)

Optional:
- `SYNC_ENDPOINT_URL` (default: http://127.0.0.1:8000/api/sync/tripleseat)

## Response Examples

### Success Response
```json
{
  "success": true,
  "mode": "single",
  "summary": {
    "queried": 1,
    "injected": 1,
    "skipped": 0,
    "failed": 0
  },
  "events": [
    {
      "id": "55521609",
      "name": "Event Name",
      "status": "injected",
      "revel_order_id": "uuid-here"
    }
  ]
}
```

### Duplicate (Skip) Response
```json
{
  "success": true,
  "mode": "single",
  "summary": {
    "queried": 1,
    "injected": 0,
    "skipped": 1,
    "failed": 0
  },
  "events": [
    {
      "id": "55521609",
      "name": "Event Name",
      "status": "skipped",
      "reason": "DUPLICATE - Order Triple Seat_55521609 already exists"
    }
  ]
}
```

## Next Steps

1. **Deploy**: Commit and push to Render
2. **Verify**: Check logs for scheduler initialization
3. **Test**: Call sync endpoint manually
4. **Monitor**: Watch for scheduled sync logs every 45 minutes
5. **Celebrate**: You now have industry-standard reconciliation! 🎉
