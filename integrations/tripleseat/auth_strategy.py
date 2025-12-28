"""
OAuth 1.0 Authentication Strategy for TripleSeat Integration

This module handles OAuth 1.0 (3-legged) authentication for TripleSeat API calls.
Replaces deprecated OAuth 2.0 with cleaner, more reliable OAuth 1.0.

OAuth 1.0 FEATURES:
- Signature-based authentication (HMAC-SHA1)
- Consumer Key + Consumer Secret (app credentials)
- Access Token + Access Token Secret (user authorization)
- Built-in nonce and timestamp for security
- No token refresh needed
"""

import logging
import os

logger = logging.getLogger(__name__)

def get_read_headers():
    """Return default headers for TripleSeat API requests."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def get_oauth1_credentials():
    """Get OAuth 1.0 credentials from environment.
    
    Returns:
        Dict with consumer_key, consumer_secret, access_token, access_token_secret
    """
    return {
        'consumer_key': os.getenv('CONSUMER_KEY', '').strip(),
        'consumer_secret': os.getenv('CONSUMER_SECRET', '').strip(),
        'access_token': os.getenv('TRIPLESEAT_OAUTH_TOKEN', '').strip(),
        'access_token_secret': os.getenv('TRIPLESEAT_OAUTH_TOKEN_SECRET', '').strip()
    }

def validate_oauth1_credentials():
    """Validate OAuth 1.0 credentials are configured.
    
    Returns:
        bool: True if all required credentials are present
    """
    creds = get_oauth1_credentials()
    
    required = ['consumer_key', 'consumer_secret']
    optional = ['access_token', 'access_token_secret']
    
    # Consumer Key + Secret are REQUIRED
    if not all(creds.get(k) for k in required):
        logger.error(f"❌ OAuth 1.0: Missing required credentials: {required}")
        return False
    
    # Access Token + Secret are OPTIONAL (for public endpoints)
    if not all(creds.get(k) for k in optional):
        logger.warning(f"⚠️ OAuth 1.0: Access tokens not configured - limited to public endpoints")
    
    logger.info("✅ OAuth 1.0 credentials validated")
    return True

def get_oauth_headers(oauth_token: str = None):
    """Legacy function - use OAuth1Session instead.
    
    This function is kept for backward compatibility.
    OAuth 1.0 signatures are automatically handled by requests-oauthlib.
    """
    logger.debug("[get_oauth_headers] Using OAuth 1.0 signature-based auth")
    return get_read_headers()

def sanitize_headers_for_read(headers):
    """Remove auth headers for public API endpoints."""
    sanitized = {k: v for k, v in headers.items() 
                 if k.lower() not in ['authorization', 'x-api-key']}
    return sanitized
