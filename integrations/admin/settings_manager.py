import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Determine settings file path
def _get_settings_file_path():
    """Get the settings file path, with fallback options for different environments."""
    # First check if explicitly set via environment
    if os.getenv('SETTINGS_FILE'):
        return Path(os.getenv('SETTINGS_FILE'))
    
    # Try project config directory first (local development)
    project_config = Path(__file__).parent.parent.parent / 'config' / 'settings.json'
    if project_config.parent.exists() and os.access(project_config.parent, os.W_OK):
        return project_config
    
    # Fallback to /tmp for Render or other restricted environments
    if os.getenv('RENDER') or os.getenv('ENV') == 'production':
        tmp_config = Path('/tmp') / 'settings.json'
        logger.info(f"Using fallback settings path for production: {tmp_config}")
        return tmp_config
    
    # Final fallback to project config
    return project_config

SETTINGS_FILE = _get_settings_file_path()

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
                logger.info(f"Settings file path: {SETTINGS_FILE} (parent exists: {SETTINGS_FILE.parent.exists()})")
                return SettingsManager._get_defaults()
        except Exception as e:
            logger.error(f"Failed to load settings from {SETTINGS_FILE}: {e}")
            return SettingsManager._get_defaults()
    
    @staticmethod
    def save(settings: dict) -> bool:
        """Save settings to file."""
        try:
            # Ensure config directory exists
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp
            settings['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            logger.info(f"🔵 Saving settings to {SETTINGS_FILE}")
            logger.info(f"🔵 Settings before save: {json.dumps(settings, indent=2)}")
            
            # Write file
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Verify file was written
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r') as f:
                    verified = json.load(f)
                logger.info(f"✅ Settings file saved and verified at {SETTINGS_FILE}")
                logger.info(f"✅ Verified content: {json.dumps(verified, indent=2)}")
                return True
            else:
                logger.error(f"🔴 Settings file not found after save at {SETTINGS_FILE}!")
                return False
        except IOError as e:
            logger.error(f"🔴 IO Error saving settings to {SETTINGS_FILE}: {e}", exc_info=True)
            logger.error(f"🔴 Directory writable: {os.access(SETTINGS_FILE.parent, os.W_OK) if SETTINGS_FILE.parent.exists() else 'parent does not exist'}")
            return False
        except Exception as e:
            logger.error(f"🔴 Failed to save settings: {e}", exc_info=True)
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
        
        return value if value is not None else default
    
    @staticmethod
    def set(key: str, value) -> bool:
        """Set a specific setting value."""
        logger.info(f"🔵 SettingsManager.set() called: key={key}, value={value}, type={type(value)}")
        
        settings = SettingsManager.load()
        logger.info(f"🔵 Loaded settings: {json.dumps(settings, indent=2)}")
        
        parts = key.split('.')
        
        # Navigate to the parent key
        current = settings
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value at the final key
        final_key = parts[-1]
        logger.info(f"🔵 Setting {key}: {parts[:-1]} -> {final_key} = {value}")
        current[final_key] = value
        
        logger.info(f"🔵 Settings after modification: {json.dumps(settings, indent=2)}")
        
        result = SettingsManager.save(settings)
        logger.info(f"🔵 SettingsManager.set() result: {result}")
        return result
    
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
