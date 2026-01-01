from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from integrations.admin.settings_manager import get_all_settings, set_setting
import logging

logger = logging.getLogger(__name__)

class SettingValue(BaseModel):
    value: bool


router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/")
async def get_settings():
    """Get all application settings."""
    try:
        settings = get_all_settings()
        return {
            "success": True,
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{key}")
async def get_setting(key: str):
    """Get a specific setting by key (e.g., 'jera.testing_mode')."""
    try:
        from integrations.admin.settings_manager import get_setting
        value = get_setting(key)
        logger.debug(f"GET setting: {key} = {value} (type: {type(value).__name__})")
        return {
            "success": True,
            "key": key,
            "value": value
        }
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{key}")
async def update_setting(key: str, setting: SettingValue):
    """Update a setting by key (e.g., POST /api/settings/jera.testing_mode with body: {"value": true})."""
    try:
        value = setting.value
        success = set_setting(key, value)
        
        if success:
            from integrations.admin.settings_manager import get_setting
            new_value = get_setting(key)
            logger.info(f"✅ Setting updated: {key} = {new_value}")
            return {
                "success": True,
                "key": key,
                "value": new_value,
                "message": f"Setting '{key}' updated to {new_value}"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to save setting {key}")
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle/{key}")
async def toggle_setting(key: str):
    """Toggle a boolean setting (flip true to false, false to true)."""
    try:
        from integrations.admin.settings_manager import get_setting
        
        current = get_setting(key, False)
        logger.info(f"🔵 Toggle endpoint: key={key}, current_value={current}, type={type(current)}")
        
        # Ensure we're working with a boolean
        if not isinstance(current, bool):
            logger.warning(f"🟡 Current value is not boolean, converting: {current} (type: {type(current)})")
            current = bool(current)
        
        new_value = not current
        logger.info(f"🔵 Toggle endpoint: new_value={new_value}, will_save={key}={new_value}")
        
        success = set_setting(key, new_value)
        
        if success:
            # Verify the value was actually saved
            verified_value = get_setting(key, False)
            logger.info(f"✅ Setting toggled: {key} - current: {current} -> new: {new_value}, verified: {verified_value}")
            
            # Double-check verification
            if verified_value != new_value:
                logger.error(f"🔴 Verification failed: expected {new_value}, got {verified_value}")
                return {
                    "success": False,
                    "key": key,
                    "value": verified_value,
                    "error": "Verification failed - value was not saved correctly",
                    "expected": new_value,
                    "actual": verified_value
                }
            
            return {
                "success": True,
                "key": key,
                "value": new_value,
                "verified_value": verified_value,
                "message": f"Setting '{key}' toggled to {new_value}"
            }
        else:
            logger.error(f"🔴 Failed to save setting {key}")
            raise HTTPException(status_code=500, detail=f"Failed to toggle setting {key}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔴 Failed to toggle setting {key}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
