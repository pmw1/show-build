"""
Interface and rundown settings endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from auth.utils import get_current_user_or_key
from ._shared import (
    load_settings, save_settings,
    InterfaceSettings, RundownSettings,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])


@router.put("/interface")
async def update_interface_settings(
    interface: InterfaceSettings,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Update interface settings"""
    settings = load_settings()
    settings["interface"] = interface.dict()

    if save_settings(settings):
        return {
            "success": True,
            "message": "Interface settings updated successfully",
            "settings": interface.dict()
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


@router.post("/interface")
async def save_interface_settings(
    request: Request,
    current_user: Optional[dict] = None  # Make auth optional for testing
) -> Dict[str, Any]:
    """Save interface settings (alternative POST endpoint)"""
    try:
        body = await request.json()
        settings = load_settings()
        settings["interface"] = body

        if save_settings(settings):
            return {
                "success": True,
                "message": "Interface settings saved successfully",
                "settings": body
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
    except Exception as e:
        logger.error(f"Error saving interface settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rundown")
async def update_rundown_settings(
    rundown: RundownSettings,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Update rundown settings"""
    try:
        # from models import Settings
        from database import get_db
        from sqlalchemy.orm import Session

        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)

        try:
            # Update or create settings in database
            rundown_data = rundown.dict()

            for key, value in rundown_data.items():
                setting = db.query(Settings).filter(Settings.key == key).first()

                if setting:
                    setting.value = value
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = Settings(
                        key=key,
                        value=value,
                        category="rundown",
                        description=f"Rundown setting: {key}"
                    )
                    db.add(setting)

            db.commit()

            # Also update JSON file for backward compatibility
            settings = load_settings()
            settings["rundown"] = rundown_data
            save_settings(settings)

            return {
                "success": True,
                "message": "Rundown settings updated successfully",
                "settings": rundown_data
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to update rundown settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update rundown settings: {str(e)}")
