"""
Color settings management router using database storage
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
from database import get_db
from models import Settings
from auth.utils import get_current_user_or_key
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])

class ColorSettings(BaseModel):
    """Color configuration model"""
    colors: Dict[str, str]
    category: str = "colors"
    profile: str = "default"

class ThemeSettings(BaseModel):
    """Theme configuration model"""
    theme: str = "dark"  # "light", "dark", "auto"
    category: str = "theme"
    profile: str = "default"

class AccessibilitySettings(BaseModel):
    """Accessibility configuration model"""
    high_contrast: bool = False
    reduced_motion: bool = False
    keyboard_shortcuts: bool = True
    category: str = "accessibility"
    profile: str = "default"

class ProfileSettings(BaseModel):
    """Complete profile configuration model"""
    colors: Optional[Dict[str, str]] = None
    theme: Optional[str] = None
    accessibility: Optional[Dict[str, Any]] = None
    profile: str = "default"

@router.get("/colors")
async def get_color_settings(
    profile: str = "default",
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None  # Make auth optional for now
) -> Dict[str, Any]:
    """Get color settings from database for specified global profile"""
    try:
        # Get global color profile (user_id = None)
        settings = db.query(Settings).filter(
            Settings.key == f"theme_colors_{profile}",
            Settings.category == "colors", 
            Settings.user_id.is_(None)
        ).first()
        
        if settings:
            return {
                "success": True,
                "profile": profile,
                "colors": settings.value
            }
        else:
            # Return default colors if profile not found
            default_colors = {
                'segment': 'info',
                'ad': 'primary', 
                'promo': 'success',
                'cta': 'accent',
                'trans': 'secondary',
                'unknown': 'grey',
                'Selection-interface': 'warning',
                'Hover-interface': 'blue-lighten-4',
                'Highlight-interface': 'yellow-lighten-3',
                'Dropline-interface': 'green-lighten-4',
                'DragLight-interface': 'cyan-lighten-4',
                'Draft-script': 'grey-darken-2',
                'Approved-script': 'green-accent',
                'Production-script': 'blue-accent',
                'Completed-script': 'yellow-accent'
            }
            return {
                "success": True,
                "profile": profile,
                "colors": default_colors
            }
    except Exception as e:
        logger.error(f"Failed to get color settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/colors") 
async def save_color_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None  # Make auth optional for now
) -> Dict[str, Any]:
    """Save color settings to database for specified global profile"""
    try:
        # Parse request body
        body = await request.json()
        colors = body.get("colors", {})
        profile = body.get("profile", "default")
        
        profile_key = f"theme_colors_{profile}"
        
        # Check if global color profile exists
        settings = db.query(Settings).filter(
            Settings.key == profile_key,
            Settings.category == "colors",
            Settings.user_id.is_(None)
        ).first()
        
        if settings:
            # Update existing settings
            settings.value = colors
            settings.description = f"Theme color configuration for '{profile}' profile"
        else:
            # Create new settings
            settings = Settings(
                key=profile_key,
                value=colors,
                category="colors",
                user_id=None,  # Global settings
                description=f"Theme color configuration for '{profile}' profile"
            )
            db.add(settings)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Color settings saved successfully for profile '{profile}'",
            "profile": profile,
            "colors": colors
        }
    except Exception as e:
        logger.error(f"Failed to save color settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/theme")
async def get_theme_settings(
    profile: str = "default",
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Get theme settings from database for specified global profile"""
    try:
        settings = db.query(Settings).filter(
            Settings.key == f"theme_settings_{profile}",
            Settings.category == "theme",
            Settings.user_id.is_(None)
        ).first()
        
        if settings:
            return {
                "success": True,
                "profile": profile,
                "theme": settings.value.get("theme", "dark")
            }
        else:
            return {
                "success": True,
                "profile": profile,
                "theme": "dark"
            }
    except Exception as e:
        logger.error(f"Failed to get theme settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/theme")
async def save_theme_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Save theme settings to database for specified global profile"""
    try:
        body = await request.json()
        theme = body.get("theme", "dark")
        profile = body.get("profile", "default")
        
        profile_key = f"theme_settings_{profile}"
        
        settings = db.query(Settings).filter(
            Settings.key == profile_key,
            Settings.category == "theme",
            Settings.user_id.is_(None)
        ).first()
        
        theme_data = {"theme": theme}
        
        if settings:
            settings.value = theme_data
            settings.description = f"Theme settings for '{profile}' profile"
        else:
            settings = Settings(
                key=profile_key,
                value=theme_data,
                category="theme",
                user_id=None,
                description=f"Theme settings for '{profile}' profile"
            )
            db.add(settings)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Theme settings saved successfully for profile '{profile}'",
            "profile": profile,
            "theme": theme
        }
    except Exception as e:
        logger.error(f"Failed to save theme settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accessibility")
async def get_accessibility_settings(
    profile: str = "default",
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Get accessibility settings from database for specified global profile"""
    try:
        settings = db.query(Settings).filter(
            Settings.key == f"accessibility_settings_{profile}",
            Settings.category == "accessibility",
            Settings.user_id.is_(None)
        ).first()
        
        default_accessibility = {
            "high_contrast": False,
            "reduced_motion": False,
            "keyboard_shortcuts": True
        }
        
        if settings:
            return {
                "success": True,
                "profile": profile,
                "accessibility": settings.value
            }
        else:
            return {
                "success": True,
                "profile": profile,
                "accessibility": default_accessibility
            }
    except Exception as e:
        logger.error(f"Failed to get accessibility settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accessibility")
async def save_accessibility_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Save accessibility settings to database for specified global profile"""
    try:
        body = await request.json()
        accessibility = body.get("accessibility", {})
        profile = body.get("profile", "default")
        
        profile_key = f"accessibility_settings_{profile}"
        
        settings = db.query(Settings).filter(
            Settings.key == profile_key,
            Settings.category == "accessibility",
            Settings.user_id.is_(None)
        ).first()
        
        if settings:
            settings.value = accessibility
            settings.description = f"Accessibility settings for '{profile}' profile"
        else:
            settings = Settings(
                key=profile_key,
                value=accessibility,
                category="accessibility",
                user_id=None,
                description=f"Accessibility settings for '{profile}' profile"
            )
            db.add(settings)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Accessibility settings saved successfully for profile '{profile}'",
            "profile": profile,
            "accessibility": accessibility
        }
    except Exception as e:
        logger.error(f"Failed to save accessibility settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles")
async def list_all_profiles(
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """List all available global profiles with their settings"""
    try:
        # Get all global settings (user_id = None)
        settings = db.query(Settings).filter(
            Settings.key.like("%_settings_%"),
            Settings.user_id.is_(None)
        ).all()
        
        # Group settings by profile name
        profiles_dict = {}
        
        for setting in settings:
            # Extract profile name from key (theme_colors_profilename -> profilename)
            if "_colors_" in setting.key:
                profile_name = setting.key.replace("theme_colors_", "")
                category = "colors"
            elif "_settings_" in setting.key:
                if setting.category == "theme":
                    profile_name = setting.key.replace("theme_settings_", "")
                elif setting.category == "accessibility":
                    profile_name = setting.key.replace("accessibility_settings_", "")
                else:
                    continue
                category = setting.category
            else:
                continue
            
            if profile_name not in profiles_dict:
                profiles_dict[profile_name] = {
                    "name": profile_name,
                    "settings": {},
                    "created_at": setting.created_at.isoformat() if hasattr(setting, 'created_at') and setting.created_at else None
                }
            
            profiles_dict[profile_name]["settings"][category] = {
                "value": setting.value,
                "description": setting.description
            }
        
        # Always ensure default profile exists
        if "default" not in profiles_dict:
            profiles_dict["default"] = {
                "name": "default",
                "settings": {
                    "colors": {"value": {}, "description": "Default color scheme"},
                    "theme": {"value": {"theme": "dark"}, "description": "Default theme settings"},
                    "accessibility": {"value": {"high_contrast": False, "reduced_motion": False, "keyboard_shortcuts": True}, "description": "Default accessibility settings"}
                },
                "created_at": None
            }
        
        profiles = list(profiles_dict.values())
        
        return {
            "success": True,
            "profiles": profiles
        }
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colors/profiles")
async def list_color_profiles(
    db: Session = Depends(get_db),
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """List all available global color profiles (backward compatibility)"""
    try:
        all_profiles_response = await list_all_profiles(db, current_user)
        profiles = []
        
        for profile in all_profiles_response["profiles"]:
            color_settings = profile.get("settings", {}).get("colors", {})
            profiles.append({
                "name": profile["name"],
                "description": color_settings.get("description", f"Color scheme for {profile['name']}"),
                "created_at": profile["created_at"],
                "color_count": len(color_settings.get("value", {}))
            })
        
        return {
            "success": True,
            "profiles": profiles
        }
    except Exception as e:
        logger.error(f"Failed to list color profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colors/user/{user_id}")
async def get_user_color_settings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get user-specific color settings"""
    try:
        # Check authorization
        if current_user.get("id") != user_id and current_user.get("access_level") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to view these settings")
        
        # Get user-specific color settings
        settings = db.query(Settings).filter(
            Settings.key == "theme_colors",
            Settings.category == "colors",
            Settings.user_id == user_id
        ).first()
        
        if settings:
            return {
                "success": True,
                "colors": settings.value
            }
        else:
            # Return global settings or defaults
            return await get_color_settings(db, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user color settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/colors/user/{user_id}")
async def save_user_color_settings(
    user_id: int,
    color_settings: ColorSettings,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Save user-specific color settings"""
    try:
        # Check authorization
        if current_user.get("id") != user_id and current_user.get("access_level") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to modify these settings")
        
        # Check if user-specific color settings exist
        settings = db.query(Settings).filter(
            Settings.key == "theme_colors",
            Settings.category == "colors",
            Settings.user_id == user_id
        ).first()
        
        if settings:
            # Update existing settings
            settings.value = color_settings.colors
        else:
            # Create new settings
            settings = Settings(
                key="theme_colors",
                value=color_settings.colors,
                category="colors",
                user_id=user_id,
                description=f"Theme color configuration for user {user_id}"
            )
            db.add(settings)
        
        db.commit()
        
        return {
            "success": True,
            "message": "User color settings saved successfully",
            "colors": color_settings.colors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save user color settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/colors/user/{user_id}")
async def delete_user_color_settings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Delete user-specific color settings (revert to global)"""
    try:
        # Check authorization
        if current_user.get("id") != user_id and current_user.get("access_level") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete these settings")
        
        # Find and delete user-specific color settings
        settings = db.query(Settings).filter(
            Settings.key == "theme_colors",
            Settings.category == "colors",
            Settings.user_id == user_id
        ).first()
        
        if settings:
            db.delete(settings)
            db.commit()
            return {
                "success": True,
                "message": "User color settings deleted, reverting to global settings"
            }
        else:
            return {
                "success": True,
                "message": "No user-specific settings found"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user color settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))