"""Admin module for TripleSeat-Revel connector.

Provides web-based admin interface, settings management, and monitoring.
"""

from .dashboard import router, get_settings_endpoints

__all__ = ["router", "get_settings_endpoints"]
