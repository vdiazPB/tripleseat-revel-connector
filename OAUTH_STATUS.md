# TripleSeat-Revel Connector - API Authentication Status

**Last Updated:** December 28, 2025

## Current Authentication Method: OAuth 1.0 ✅

### Why OAuth 1.0?

- ✅ **Working:** All API endpoints return 200 with data
- ✅ **Simple:** Uses consumer key/secret (no token refresh needed)
- ✅ **Proven:** Has been tested and verified functional

### OAuth 2.0 Status

- **Status:** In codebase, not currently used
- **Issue:** Client credentials flow returns 401 "Token resource owner not found"
- **Cause:** TripleSeat OAuth 2.0 requires additional account-level configuration not yet available
- **Future:** Can be activated once TripleSeat admin resolves resource owner linking

## Webhook Processing Strategy

### Payload-First Design ✅

The webhook handler is designed to work **without additional API calls**:

1. **TripleSeat webhook** delivers full event/booking payload
2. **Handler extracts** all needed data from payload directly
3. **Revel injection** creates order using webhook data
4. **No OAuth calls needed** for typical event processing

### Files Using OAuth 1.0

- `integrations/tripleseat/oauth1.py` - OAuth 1.0 session creation
- `integrations/tripleseat/api_client.py` - Uses OAuth 1.0 session for API calls
- `integrations/revel/injection.py` - Prefers webhook payload (no API call needed)

### When OAuth 1.0 Is Used

- Webhook payload has incomplete data
- Manual API testing/validation needed
- Event status lookups required

## API Endpoints Verified ✅

```
GET /v1/events?limit=1     → 200 (event data)
GET /v1/locations          → 200 (location list)
GET /v1/leads?limit=1      → 200 (lead data)
```

## Environment Variables

```bash
TRIPLESEAT_API_BASE=https://api.tripleseat.com
CONSUMER_KEY=Whz3ADZ1VwNdSIssvh8jvCY2fmoPngT1b6Iuo5rX
CONSUMER_SECRET=VPZET8KoGih6FjsrU1KWYAI91Gz443cLMeNwvjKr
```

## OAuth 2.0 (Kept for Future Use)

```bash
TRIPLESEAT_OAUTH_CLIENT_ID=k2AjxXq3kP_VHXGN6TeVSnkq-HNn1QXiSr7UiH9tm34
TRIPLESEAT_OAUTH_CLIENT_SECRET=TLOKqkA5_0qFC9ki1kH-D9vUyXWNFWPe9ODHwq6X6Q8
TRIPLESEAT_OAUTH_TOKEN_URL=https://api.tripleseat.com/oauth2/token
```

## Webhook Flow

1. TripleSeat sends webhook to `/webhooks/tripleseat`
2. Signature verified using `TRIPLESEAT_WEBHOOK_SECRET`
3. Event data extracted from webhook payload
4. Revel order created without additional API calls
5. Success/failure email sent via SendGrid

## Next Steps

✅ OAuth 1.0 API is functional
✅ Webhook handler is ready
⏳ Deploy to Render and test end-to-end
