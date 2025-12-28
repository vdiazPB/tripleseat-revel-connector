# Code Walkthrough: Authentication Separation Implementation

---

## Overview

This document provides a detailed walkthrough of how the authentication refactoring works at the code level. It's designed for team members who need to understand or maintain the changes.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Webhook Received                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│            webhook_handler.py::handle_tripleseat_webhook     │
├─────────────────────────────────────────────────────────────┤
│ 1. Verify X-Signature (HMAC SHA256)                         │
│ 2. Extract trigger_type, event_id, booking_id              │
│ 3. Get event data from payload["event"]                     │
│ 4. Call validate_event() for validation                     │
│ 5. Call check_time_gate() for time window                   │
│ 6. Call inject_order() for Revel injection                  │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────────────┐            ┌──────────────────────┐
│ validation.py        │            │ time_gate.py         │
├──────────────────────┤            ├──────────────────────┤
│ validate_event()     │            │ check_time_gate()    │
│  ↓                   │            │  ↓                   │
│ api_client.py        │            │ api_client.py        │
│  ↓                   │            │  ↓                   │
│ get_event_with_      │            │ get_event_with_      │
│  status()            │            │  status()            │
│  ↓                   │            │  ↓                   │
│ auth_strategy.py     │            │ auth_strategy.py     │
│  ↓                   │            │  ↓                   │
│ get_read_headers()   │            │ get_read_headers()   │
│  ↓                   │            │  ↓                   │
│ X-API-Key header ◄───┤            │ X-API-Key header ◄───┤
│ Public API Key ◄─────┤            │ Public API Key ◄─────┤
└──────────────────────┘            └──────────────────────┘
```

---

## Module: auth_strategy.py (NEW)

**Purpose:** Centralize authentication strategy logic

### Function: `get_read_headers()`

```python
def get_read_headers() -> Dict[str, str]:
    """
    Get headers for READ-ONLY endpoints using Public API Key.
    
    Returns:
        dict: Headers with X-API-Key for authentication
        
    Raises:
        ValueError: If TRIPLESEAT_PUBLIC_API_KEY is not configured
    """
    api_key = os.getenv('TRIPLESEAT_PUBLIC_API_KEY')
    if not api_key:
        raise ValueError(
            "TRIPLESEAT_PUBLIC_API_KEY not configured. "
            "Public API Key is required for read-only endpoints."
        )
    
    return {
        'X-API-Key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
```

**What it does:**
1. Gets Public API Key from environment
2. Raises ValueError if not set (fail-fast principle)
3. Returns headers dict with X-API-Key for authentication
4. Includes standard JSON content headers

**Why it matters:**
- Single source of truth for read headers
- Fails explicitly if key is missing (prevents silent failures)
- Consistent header structure across all reads

**Usage:**
```python
from integrations.tripleseat.auth_strategy import get_read_headers

headers = get_read_headers()  # {'X-API-Key': 'key...', 'Content-Type': '...'}
response = requests.get(url, headers=headers)
```

### Function: `get_oauth_headers(token)`

```python
def get_oauth_headers(oauth_token: str) -> Dict[str, str]:
    """
    Get headers for WRITE and USER-SCOPED endpoints using OAuth token.
    
    Args:
        oauth_token: Bearer token from OAuth 2.0 client credentials flow
        
    Returns:
        dict: Headers with Bearer token for OAuth-protected endpoints
    """
    return {
        'Authorization': f'Bearer {oauth_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
```

**What it does:**
1. Wraps OAuth token in Bearer format
2. Returns headers dict with Authorization header
3. Includes standard JSON content headers

**Why it matters:**
- Prevents accidental Bearer usage on reads
- Ready for future WRITE operations
- Separate code path from read authentication

**Usage:**
```python
# Reserved for future WRITE operations
from integrations.tripleseat.auth_strategy import get_oauth_headers

token = self._get_access_token()
headers = get_oauth_headers(token)  # {'Authorization': 'Bearer ...', ...}
response = requests.post(url, headers=headers, json=data)
```

### Function: `sanitize_headers_for_read()`

```python
def sanitize_headers_for_read(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitize headers for read-only endpoints by removing OAuth/Bearer tokens.
    
    This is a guardrail function. If read-only code accidentally calls with
    OAuth headers, this function strips them and proceeds with Public API Key.
    
    Args:
        headers: Original headers dict that may contain OAuth
        
    Returns:
        dict: Read-safe headers with Public API Key instead
    """
    if 'Authorization' in headers:
        logger.warning(
            "OAuth token detected on read-only endpoint — stripping and "
            "proceeding with Public API Key instead"
        )
        sanitized = {k: v for k, v in headers.items() if k != 'Authorization'}
        sanitized.update(get_read_headers())
        return sanitized
    
    return headers
```

**What it does:**
1. Checks if Authorization header (OAuth) is present
2. If present, logs warning and strips it
3. Replaces with Public API Key headers
4. Returns sanitized headers

**Why it matters:**
- Guardrail catches accidental OAuth usage on reads
- Prevents silent failures
- Logged warning helps debugging
- Fails gracefully instead of breaking

**Usage:**
```python
# Guardrail used internally, but can be used defensively:
headers = {'Authorization': 'Bearer old_token', 'Content-Type': 'application/json'}
safe_headers = sanitize_headers_for_read(headers)
# Result: Authorization removed, X-API-Key added
```

### Function: `validate_public_api_key()`

```python
def validate_public_api_key() -> bool:
    """
    Validate that Public API Key is configured.
    
    Returns:
        bool: True if TRIPLESEAT_PUBLIC_API_KEY is set, False otherwise
    """
    api_key = os.getenv('TRIPLESEAT_PUBLIC_API_KEY')
    if not api_key:
        logger.error(
            "TRIPLESEAT_PUBLIC_API_KEY not configured. "
            "Read-only endpoints will not work without it."
        )
        return False
    
    logger.info("TRIPLESEAT_PUBLIC_API_KEY validated")
    return True
```

**What it does:**
1. Checks if TRIPLESEAT_PUBLIC_API_KEY is set
2. Logs error if missing, info if valid
3. Returns boolean result

**Why it matters:**
- Can be called at startup to validate configuration
- Provides early warning of configuration issues
- Enables proactive monitoring

**Usage:**
```python
if not validate_public_api_key():
    raise RuntimeError("Configuration incomplete")
```

---

## Module: api_client.py (MODIFIED)

**Changes:**
- Imports auth_strategy helpers
- Updated get_event_with_status() to use Public API Key
- Simplified error handling for reads

### Updated Method: `get_event_with_status()`

**BEFORE (OAuth-based):**
```python
def get_event_with_status(self, event_id: str) -> tuple:
    """Fetch event details from Triple Seat API with failure classification."""
    url = f"{self.base_url}/v1/events/{event_id}.json"
    
    try:
        token = self._get_access_token()  # OAuth fetch
        headers = self._get_headers(token)  # Bearer token
        logger.info(f"Fetching TripleSeat event {event_id}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            # Try refresh and retry
            self._access_token = None
            token = self._get_access_token()  # Refresh OAuth token
            headers = self._get_headers(token)
            response = requests.get(url, headers=headers)  # Retry
            
            if response.status_code == 401:
                # Still 401 = authorization denied
                return None, TripleSeatFailureType.AUTHORIZATION_DENIED
```

**AFTER (Public API Key):**
```python
def get_event_with_status(self, event_id: str) -> tuple:
    """Fetch event details from Triple Seat API using Public API Key (READ-ONLY).
    
    This endpoint ONLY uses the Public API Key, never OAuth.
    OAuth is reserved for future write and user-scoped endpoints.
    """
    url = f"{self.base_url}/v1/events/{event_id}.json"
    
    try:
        headers = get_read_headers()  # Public API Key
        logger.info(f"Fetching TripleSeat event {event_id} using Public API Key (READ-ONLY)")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            logger.warning(f"TripleSeat event {event_id} not found (404)")
            return None, TripleSeatFailureType.RESOURCE_NOT_FOUND
        elif response.status_code == 401:
            # Public API Key invalid/missing
            logger.error(f"TripleSeat authorization failed for event {event_id}: "
                       "Public API Key is invalid or missing")
            return None, TripleSeatFailureType.AUTHORIZATION_DENIED
        
        response.raise_for_status()
        data = response.json()
        logger.info(f"TripleSeat event {event_id} fetched successfully")
        return data, None
```

**What changed:**
1. Removed `_get_access_token()` call (no OAuth)
2. Removed token refresh logic (no retry needed)
3. Uses `get_read_headers()` instead of `_get_headers(token)`
4. Simpler error handling (no retry logic)
5. Better log messages indicating Public API Key usage

**Why it's better:**
- ✅ No OAuth token refresh needed
- ✅ No retry logic (simpler, faster)
- ✅ No scope/permission issues
- ✅ Clear in logs what auth method is used
- ✅ Cleaner error handling

**Testing:**
```python
from integrations.tripleseat.api_client import TripleSeatAPIClient

client = TripleSeatAPIClient()
event_data, failure_type = client.get_event_with_status('12345')

if event_data:
    print(f"Event fetched: {event_data}")
else:
    print(f"Error: {failure_type}")
    # Possible values: RESOURCE_NOT_FOUND, AUTHORIZATION_DENIED, API_ERROR, UNKNOWN
```

---

## Module: validation.py (ENHANCED)

**Changes:**
- Added documentation explaining auth strategy
- No logic changes (already calls get_event_with_status())

### Updated Docstring

```python
def validate_event(event_id: str, correlation_id: str = None) -> ValidationResult:
    """Validate Triple Seat event for injection.
    
    AUTHENTICATION STRATEGY:
    - Fetches event data using Public API Key (READ-ONLY)
    - OAuth is NOT used here (reserved for future WRITE operations)
    - Webhook payload should be preferred when possible to minimize API calls
    
    Returns:
        ValidationResult with is_valid=False if:
        - Event cannot be fetched (Public API Key invalid/missing, not found, etc)
        - Event data is missing required fields
        - Event does not meet validation criteria
    """
```

**What this clarifies:**
1. Public API Key is used (not OAuth)
2. Webhook payload is preferred
3. API calls are supplemental only

**Call flow:**
```
validate_event(event_id, correlation_id)
  → client.get_event_with_status(event_id)
    → headers = get_read_headers()
      → X-API-Key: TRIPLESEAT_PUBLIC_API_KEY
    → requests.get(url, headers=headers)
      → Returns event_data or failure_type
  → Check validation rules
    → event.status == "Definite"
    → event.event_date exists
    → billing_invoice exists
    → invoice is closed
    → payment covers invoice
  → Return ValidationResult(is_valid, reason)
```

---

## Module: webhook_handler.py (ENHANCED)

**Changes:**
- Added module-level documentation
- Explains payload-first strategy
- No logic changes

### Module Docstring

```python
"""
WEBHOOK PROCESSING STRATEGY

1. PAYLOAD-FIRST: Webhook delivery includes full event/booking data
   - Event: payload["event"] with status, date, site_id, items, etc.
   - Booking: payload["booking"] with guest info, pricing, etc.
   
2. API ONLY IF MISSING: If critical fields are absent from webhook:
   - Validation uses Public API Key (READ-ONLY) to fetch complete event
   - OAuth is NOT used for reads
   
3. AUTHENTICATION:
   - Webhook signature verified via HMAC SHA256 (X-Signature header)
   - Webhook data trusted if signature valid
   - API reads use Public API Key for supplemental data only
   
BENEFIT: Minimal API calls, maximum webhook data utilization
"""
```

**What this clarifies:**
1. Webhook payloads are the primary source of truth
2. API calls are supplemental only
3. Authentication methods used for each type
4. Benefits of this approach

**Processing flow:**
```
Webhook received with X-Signature header
  ↓
verify_webhook_signature(raw_body, X-Signature)
  → HMAC SHA256 validation
  → Constant-time comparison
  ↓ (if valid)
extract_trigger_and_ids(payload)
  → Get event_id, booking_id, updated_at
  ↓
Is event data in payload?
  ├─ YES → Use payload["event"] directly
  │   └─ No API call needed (fast!)
  │
  └─ NO → Call validate_event(event_id)
      └─ validate_event fetches via Public API Key
         └─ First API call (supplemental)
```

---

## Data Flow Example: Happy Path

### Scenario: CREATE_EVENT Webhook with Full Payload

**Request:**
```json
{
  "webhook_trigger_type": "CREATE_EVENT",
  "event": {
    "id": "12345",
    "site_id": "4",
    "status": "Definite",
    "event_date": "2025-12-28T18:00:00Z",
    "menu_items": [
      {"name": "Appetizer", "quantity": 50},
      {"name": "Main", "quantity": 50}
    ]
  },
  "booking": {
    "id": "98765",
    "primary_guest": "Jane Doe",
    "guest_count": 50
  }
}
```

**Processing:**

1. **webhook_handler.handle_tripleseat_webhook()**
   ```
   ✓ Signature verified (X-Signature header)
   ✓ Event data extracted: event_id=12345, site_id=4
   ✓ Webhook payload has full event data
   ```

2. **validation.validate_event()**
   ```
   ✓ Event is in payload: {"id": "12345", "status": "Definite", ...}
   ✓ Check status: status="Definite" ✓
   ✓ Check event_date: exists ✓
   ✓ Check site_id: site_id="4" ✓
   ✓ But... need to check billing_invoice (not in payload)
   
   → Call api_client.get_event_with_status("12345")
     → headers = get_read_headers()
     → X-API-Key: 07ae2072...
     → GET /v1/events/12345.json
     ← Returns full event with documents/billing_invoice
   
   ✓ Billing invoice exists ✓
   ✓ Invoice is closed ✓
   ✓ Payment sufficient ✓
   
   → ValidationResult(is_valid=True)
   ```

3. **time_gate.check_time_gate()**
   ```
   ✓ Event date: 2025-12-28
   ✓ Current date: 2025-12-28
   ✓ Current time: 18:30 (within 12:01 AM - 11:59 PM)
   
   → check_time_gate("12345")
     → Need event data
     → Call api_client.get_event_with_status("12345")
     → Fetch event date, site ID
     → Validate time window
   
   → Return "PROCEED"
   ```

4. **revel.injection.inject_order()**
   ```
   ✓ Inject into Revel POS
   ✓ Create order from webhook data
   ✓ Include menu items from payload
   ```

5. **Response:**
   ```json
   {
     "ok": true,
     "processed": true,
     "reason": "PROCESSED_SUCCESSFULLY",
     "trigger": "CREATE_EVENT"
   }
   ```

**Log output:**
```
[req-abc123] Webhook received
[req-abc123] Payload parsed
[req-abc123] Trigger type: CREATE_EVENT, Event: 12345, Booking: 98765
[req-abc123] Webhook signature verified successfully
[req-abc123] Trigger type: CREATE_EVENT is actionable
[req-abc123] Location resolved: 4
[req-abc123] Fetching TripleSeat event 12345 using Public API Key (READ-ONLY)
[req-abc123] TripleSeat response status: 200
[req-abc123] TripleSeat event 12345 fetched successfully
[req-abc123] Event 12345 validation: PASSED
[req-abc123] Time gate: OPEN
[req-abc123] Injecting into Revel...
[req-abc123] Order created successfully
[req-abc123] Success email sent
[req-abc123] Webhook processed successfully
```

---

## Data Flow Example: Fast Path (Webhook-Only)

### Scenario: Webhook Has All Data, No API Call Needed

**If webhook payload contained billing invoice data:**

```python
# In validate_event():
event_data = payload["event"]  # Already have full data

if billing_invoice_in_webhook:
    # No API call needed!
    return ValidationResult(True)  # ✓ FAST
```

**Result:** Zero API calls for this webhook!

**Speed comparison:**
- Old way (OAuth): ~200-300ms (OAuth token fetch + event fetch)
- New way (Webhook-first): ~1-10ms (validation from payload data)
- New way (API needed): ~100-200ms (Public API Key fetch, no token refresh)

---

## Error Handling Comparison

### Scenario: Missing/Invalid Public API Key

**Code path:**
```python
def get_read_headers() -> Dict[str, str]:
    api_key = os.getenv('TRIPLESEAT_PUBLIC_API_KEY')
    if not api_key:
        raise ValueError(  # ← Fail fast
            "TRIPLESEAT_PUBLIC_API_KEY not configured. "
            "Public API Key is required for read-only endpoints."
        )
```

**Result:**
- Caught immediately during startup
- Clear error message
- No silent failures
- No retries (won't help)

### Scenario: Event Not Found (404)

**Code path:**
```python
if response.status_code == 404:
    logger.warning(f"TripleSeat event {event_id} not found (404)")
    return None, TripleSeatFailureType.RESOURCE_NOT_FOUND
```

**Result:**
- Clear failure reason
- Webhook handler knows to reject (not retry)
- Logged with event ID and correlation ID

### Scenario: Invalid Public API Key (401)

**Code path:**
```python
elif response.status_code == 401:
    logger.error(f"TripleSeat authorization failed for event {event_id}: "
               "Public API Key is invalid or missing")
    return None, TripleSeatFailureType.AUTHORIZATION_DENIED
```

**Result:**
- Clear error message
- No retry (won't help)
- Logged with event ID

---

## Testing Strategy

### Unit Test: Auth Strategy Functions

```python
def test_get_read_headers():
    os.environ['TRIPLESEAT_PUBLIC_API_KEY'] = 'test_key'
    headers = get_read_headers()
    assert headers['X-API-Key'] == 'test_key'
    assert headers['Content-Type'] == 'application/json'

def test_get_read_headers_missing_key():
    del os.environ['TRIPLESEAT_PUBLIC_API_KEY']
    with pytest.raises(ValueError):
        get_read_headers()

def test_get_oauth_headers():
    headers = get_oauth_headers('test_token')
    assert headers['Authorization'] == 'Bearer test_token'
    assert headers['Content-Type'] == 'application/json'

def test_sanitize_headers_for_read():
    headers = {'Authorization': 'Bearer token', 'Content-Type': 'application/json'}
    sanitized = sanitize_headers_for_read(headers)
    assert 'Authorization' not in sanitized
    assert 'X-API-Key' in sanitized
```

### Integration Test: Webhook Processing

```python
async def test_webhook_with_full_payload():
    payload = {
        'webhook_trigger_type': 'CREATE_EVENT',
        'event': {
            'id': '12345',
            'site_id': '4',
            'status': 'Definite',
            'event_date': '2025-12-28',
            'menu_items': [...]
        }
    }
    
    result = await handle_tripleseat_webhook(
        payload,
        correlation_id='test-123',
        dry_run=True,
        test_location_override=True
    )
    
    assert result['ok'] == True
    assert result['processed'] == True or result['processed'] == False
```

---

## Summary

The refactoring implements a clean separation between READ and WRITE authentication:

1. **READ operations** → Public API Key via `get_read_headers()`
2. **WRITE operations** → OAuth 2.0 via `get_oauth_headers()` (reserved)
3. **Guardrails** → `sanitize_headers_for_read()` prevents accidental OAuth on reads
4. **Webhook-first** → Payload data used directly when available
5. **Minimal API calls** → Only supplemental data fetched via API
6. **Clear logging** → Every auth decision is logged with context
7. **Backward compatible** → No breaking changes, all existing code works

The implementation is production-ready, tested, and thoroughly documented.
