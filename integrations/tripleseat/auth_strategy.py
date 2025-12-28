"""
Authentication Strategy for TripleSeat Integration

⚠️ OAUTH 2.0 REMOVED - This module is DEPRECATED

This module previously handled OAuth 2.0 authentication for TripleSeat API calls.
As of the latest refactoring, all TripleSeat OAuth 2.0 API calls have been disabled.

WEBHOOK-ONLY MODE:
- All event data comes from webhook payloads
- No API calls to TripleSeat (they're stubbed)
- Validation is bypassed (skip_validation=True)
- Time gate checks are bypassed (skip_time_gate=True)

WHY:
- OAuth 2.0 token fetch was unreliable in async contexts
- Webhook payloads contain all needed data
- Simpler, faster, more reliable approach
- Reduces external dependencies

LEGACY NOTE:
This file is kept for reference but is no longer actively used.
All auth has been removed from the codebase.
"""

import logging

logger = logging.getLogger(__name__)

def get_read_headers():
    """DEPRECATED - OAuth 2.0 removed"""
    logger.warning("DEPRECATED: get_read_headers() - OAuth 2.0 API is disabled")
    return {'Content-Type': 'application/json', 'Accept': 'application/json'}

def get_oauth_headers(oauth_token: str):
    """DEPRECATED - OAuth 2.0 removed"""
    logger.warning("DEPRECATED: get_oauth_headers() - OAuth 2.0 API is disabled")
    return {'Content-Type': 'application/json', 'Accept': 'application/json'}

def sanitize_headers_for_read(headers):
    """DEPRECATED - OAuth 2.0 removed"""
    return headers

def validate_public_api_key():
    """DEPRECATED - OAuth 2.0 removed"""
    logger.warning("DEPRECATED: validate_public_api_key() - OAuth 2.0 API is disabled")
    return True
