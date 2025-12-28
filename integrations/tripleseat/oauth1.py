"""OAuth 1.0 (3-legged) implementation for TripleSeat API.

Uses consumer key and secret to sign requests.
"""

import logging
import os
from requests_oauthlib import OAuth1Session

logger = logging.getLogger(__name__)

def get_oauth1_session():
    """Create an OAuth 1.0 session with TripleSeat credentials."""
    
    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET')
    
    if not consumer_key or not consumer_secret:
        logger.error("OAuth 1.0 credentials missing: CONSUMER_KEY or CONSUMER_SECRET not set")
        raise ValueError("OAuth 1.0 credentials incomplete")
    
    # Create OAuth1 session - uses 2-legged OAuth (no token/token_secret needed)
    session = OAuth1Session(
        client_key=consumer_key,
        client_secret=consumer_secret,
        # For 2-legged OAuth (server-to-server), resource owner credentials are empty
        resource_owner_key='',
        resource_owner_secret=''
    )
    
    logger.info("✅ OAuth 1.0 session created with consumer key")
    return session
