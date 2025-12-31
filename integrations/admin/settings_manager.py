import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to settings file (in config directory)
SETTINGS_FILE = Path(__file__).parent.parent / 'config' / 'settings.json'

class SettingsManager:
    """Manage application settings from persistent JSON file."""
    
    @staticmethod
    def load() -> dict:
        """Load settings from file."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                logger.info(f"✅ Settings loaded from {SETTINGS_FILE}")
                return settings
            else:
                logger.warning(f"Settings file not found at {SETTINGS_FILE}, using defaults")
                return SettingsManager._get_defaults()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return SettingsManager._get_defaults()
    
    @staticmethod
    def save(settings: dict) -> bool:
        """Save settings to file."""
        try:
            # Ensure config directory exists
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp
            settings['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            # Write file
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"✅ Settings saved to {SETTINGS_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    @staticmethod
    def get(key: str, default=None):
        """Get a specific setting value."""
        settings = SettingsManager.load()
        parts = key.split('.')
        value = settings
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
        
        # Handle nested 'enabled' key
        if isinstance(value, dict) and 'enabled' in value:
            return value['enabled']
        
        return value if value is not None else default
    
    @staticmethod
    def set(key: str, value) -> bool:
        """Set a specific setting value."""
        settings = SettingsManager.load()
        parts = key.split('.')
        
        # Navigate to the parent key
        current = settings
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        final_key = parts[-1]
        if isinstance(current.get(final_key), dict) and 'enabled' in current[final_key]:
            current[final_key]['enabled'] = value
        else:
            current[final_key] = value
        
        return SettingsManager.save(settings)
    
    @staticmethod
    def _get_defaults() -> dict:
        """Return default settings."""
        return {
            "jera": {
                "testing_mode": False,
                "description": "JERA/Supply It injection mode"
            },
            "dry_run": {
                "enabled": False,
                "description": "Global dry-run mode"
            },
            "enable_connector": {
                "enabled": True,
                "description": "Enable/disable all Supply It injections"
            },
            "last_updated": datetime.utcnow().isoformat() + 'Z'
        }


# Global instance
_settings_cache = None

def get_setting(key: str, default=None):
    """Convenience function to get a setting."""
    return SettingsManager.get(key, default)

def set_setting(key: str, value) -> bool:
    """Convenience function to set a setting."""
    return SettingsManager.set(key, value)

def get_all_settings() -> dict:
    """Get all settings."""
    return SettingsManager.load()
