"""
TripleSeat OAuth 2.0 Client Credentials Flow Implementation

Provides secure token management for TripleSeat API authentication.
Handles token fetching, caching, and automatic refresh.
"""

import logging
import os
import time
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

class TripleSeatOAuthClient:
    """OAuth 2.0 Client Credentials Flow for TripleSeat API.
    
    Manages access tokens with automatic refresh before expiry.
    Thread-safe for stateless container environments like Render.
    """
    
    def __init__(self):
        self.client_id = os.getenv('TRIPLESEAT_OAUTH_CLIENT_ID', '').strip()
        self.client_secret = os.getenv('TRIPLESEAT_OAUTH_CLIENT_SECRET', '').strip()
        self.token_url = os.getenv('TRIPLESEAT_OAUTH_TOKEN_URL', '').strip()
        
        # In-memory token cache (module-level for stateless containers)
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.token_url]):
            logger.error("❌ OAuth 2.0 configuration incomplete: TRIPLESEAT_OAUTH_CLIENT_ID, TRIPLESEAT_OAUTH_CLIENT_SECRET, or TRIPLESEAT_OAUTH_TOKEN_URL missing")
            raise ValueError("OAuth 2.0 configuration incomplete")
        
        logger.info("✅ TripleSeatOAuthClient initialized")

    def get_access_token(self) -> str:
        """Get a valid access token, fetching or refreshing as needed.
        
        Returns:
            Valid Bearer token string
            
        Raises:
            RuntimeError: If token cannot be obtained
        """
        now = time.time()
        
        # Check if we have a valid token that won't expire in the next 60 seconds
        if self._access_token and self._token_expires_at and (self._token_expires_at - now) > 60:
            return self._access_token
        
        # Token is expired, missing, or expiring soon - fetch a new one
        try:
            token_data = self._fetch_new_token()
            self._access_token = token_data['access_token']
            expires_in = token_data['expires_in']
            self._token_expires_at = now + expires_in
            
            logger.info(f"✅ OAuth token refreshed, expires in {expires_in} seconds")
            return self._access_token
            
        except Exception as e:
            logger.error(f"❌ Failed to obtain OAuth token: {e}")
            raise RuntimeError(f"OAuth token fetch failed: {e}")

    def _fetch_new_token(self) -> Dict[str, Any]:
        """Fetch a new access token from TripleSeat OAuth endpoint.
        
        Returns:
            Token response data with access_token and expires_in
            
        Raises:
            ValueError: If response is invalid or missing required fields
            requests.RequestException: If HTTP request fails
        """
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'read write'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        logger.debug(f"Fetching OAuth token from {self.token_url}")
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30  # Longer timeout for OAuth
            )
            
            # Check for HTML response (auth failure)
            if 'text/html' in response.headers.get('content-type', '').lower():
                body_preview = response.text[:300] if response.text else "empty"
                logger.error(f"OAuth token endpoint returned HTML: HTTP {response.status_code}, Body: {body_preview}")
                raise ValueError(f"OAuth endpoint returned HTML login page (HTTP {response.status_code})")
            
            response.raise_for_status()
            
            try:
                token_data = response.json()
            except ValueError as e:
                logger.error(f"OAuth response not valid JSON: {e}, Body: {response.text[:300]}")
                raise ValueError(f"OAuth response not valid JSON: {e}")
            
            # Validate required fields
            if 'access_token' not in token_data:
                logger.error(f"OAuth response missing access_token: {token_data}")
                raise ValueError("OAuth response missing access_token")
            
            if 'expires_in' not in token_data:
                logger.error(f"OAuth response missing expires_in: {token_data}")
                raise ValueError("OAuth response missing expires_in")
            
            # Log success (without exposing token)
            logger.info("✅ OAuth token fetched successfully")
            return token_data
            
        except requests.RequestException as e:
            logger.error(f"OAuth HTTP request failed: {e}")
            raise

    def invalidate_token(self, token: str) -> bool:
        """Invalidate a TripleSeat OAuth access token.
        
        POST to /oauth/invalidate endpoint to revoke the token.
        Returns 410 Gone on success.
        
        Args:
            token: The access token to invalidate
            
        Returns:
            True if token was successfully invalidated, False otherwise
        """
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            invalidate_url = self.token_url.replace('/oauth2/token', '/oauth/invalidate')
            response = requests.post(invalidate_url, headers=headers, timeout=30)
            
            if response.status_code == 410:
                logger.info("✅ OAuth token invalidated successfully")
                # Clear cached token if it matches
                if self._access_token == token:
                    self._access_token = None
                    self._token_expires_at = None
                    logger.info("Cached token cleared")
                return True
            else:
                logger.warning(f"OAuth token invalidation failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"OAuth token invalidation error: {e}")
            return False

# Global OAuth client instance (singleton for the module)
_oauth_client: Optional[TripleSeatOAuthClient] = None

def get_access_token() -> str:
    """Get a valid TripleSeat OAuth access token.
    
    Uses cached token with automatic refresh.
    
    Returns:
        Valid Bearer token string
        
    Raises:
        RuntimeError: If OAuth client is not configured or token cannot be obtained
    """
    global _oauth_client
    
    if _oauth_client is None:
        try:
            _oauth_client = TripleSeatOAuthClient()
        except ValueError as e:
            raise RuntimeError(f"OAuth client initialization failed: {e}")
    
    return _oauth_client.get_access_token()

def clear_token_cache() -> None:
    """Clear the cached OAuth token to force a fresh fetch.
    
    Use this after permissions have been updated on the TripleSeat OAuth app.
    """
    global _oauth_client
    
    if _oauth_client:
        _oauth_client._access_token = None
        _oauth_client._token_expires_at = None
        logger.info("OAuth token cache cleared - next get_access_token() will fetch fresh token")