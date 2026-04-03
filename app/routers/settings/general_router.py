"""
General settings endpoints: get all, update all, save general, reset.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
import os
import logging

from auth.utils import get_current_user_or_key
from ._shared import (
    load_settings, save_settings, derive_paths,
    MediaPathSettings, InterfaceSettings, RundownSettings,
    SystemSettings, GenerationSettings, SettingsUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])


@router.get("/")
async def get_settings(
    current_user: Optional[dict] = None  # Make auth optional for testing
) -> Dict[str, Any]:
    """Get all current settings"""
    settings = load_settings()

    # Auto-derive paths if needed
    if "media_paths" in settings and "show_root" in settings["media_paths"]:
        settings["media_paths"] = derive_paths(
            settings["media_paths"]["show_root"],
            settings
        )

    return settings


@router.post("/")
async def save_general_settings(
    request: Request,
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Save general settings (POST endpoint for generation and other settings)"""
    try:
        body = await request.json()
        settings = load_settings()

        # Handle generation settings
        if "generation" in body:
            settings["generation"] = body["generation"]

        # Handle other top-level settings
        for key in ["interface", "rundown", "system", "media_paths"]:
            if key in body:
                settings[key] = body[key]

        if save_settings(settings):
            return {
                "success": True,
                "message": "Settings saved successfully",
                "settings": settings
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/")
async def update_all_settings(
    settings_update: SettingsUpdate,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Update all settings at once"""
    settings = load_settings()

    # Update each section if provided
    if settings_update.media_paths:
        paths_dict = settings_update.media_paths.dict()
        if settings_update.media_paths.show_root:
            paths_dict = derive_paths(settings_update.media_paths.show_root, {"media_paths": paths_dict})
        settings["media_paths"] = paths_dict

    if settings_update.interface:
        settings["interface"] = settings_update.interface.dict()

    if settings_update.rundown:
        settings["rundown"] = settings_update.rundown.dict()

    if settings_update.system:
        settings["system"] = settings_update.system.dict()
        # Apply system settings
        if settings_update.system.log_level:
            logging.getLogger().setLevel(getattr(logging, settings_update.system.log_level))

    if settings_update.generation:
        settings["generation"] = settings_update.generation.dict()

    if save_settings(settings):
        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": settings
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


@router.post("/reset")
async def reset_settings(
    section: Optional[str] = None,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Reset settings to defaults"""
    if section:
        settings = load_settings()
        if section == "media_paths":
            settings["media_paths"] = {
                "show_root": os.getenv("MEDIA_ROOT", "/mnt/sync/disaffected"),
                "episodes_folder": None,
                "media_assets": None,
                "uploads": None,
                "process": None,
                "archive_enabled": False,
                "archive_type": "s3"
            }
        elif section == "interface":
            settings["interface"] = InterfaceSettings().dict()
        elif section == "rundown":
            settings["rundown"] = RundownSettings().dict()
        elif section == "system":
            settings["system"] = SystemSettings().dict()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown section: {section}")
    else:
        # Reset all settings
        settings = {
            "media_paths": {
                "show_root": os.getenv("MEDIA_ROOT", "/mnt/sync/disaffected"),
                "episodes_folder": None,
                "media_assets": None,
                "uploads": None,
                "process": None,
                "archive_enabled": False,
                "archive_type": "s3"
            },
            "interface": InterfaceSettings().dict(),
            "rundown": RundownSettings().dict(),
            "system": SystemSettings().dict()
        }

    if save_settings(settings):
        return {
            "success": True,
            "message": f"Settings {'for ' + section if section else ''} reset to defaults",
            "settings": settings if not section else settings.get(section)
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reset settings")
