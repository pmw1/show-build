"""
Media path settings endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pathlib import Path
import os
import logging

from auth.utils import get_current_user_or_key
from ._shared import (
    load_settings, save_settings, derive_paths,
    MediaPathSettings,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])


@router.get("/media-paths")
async def get_media_paths(
    current_user: dict = Depends(get_current_user_or_key)
) -> MediaPathSettings:
    """Get media path settings"""
    settings = load_settings()
    paths = settings.get("media_paths", {})

    # Auto-derive paths
    if "show_root" in paths:
        paths = derive_paths(paths["show_root"], settings)

    return MediaPathSettings(**paths)


@router.put("/media-paths")
async def update_media_paths(
    paths: MediaPathSettings,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Update media path settings"""
    settings = load_settings()

    # Convert to dict and handle auto-derivation
    paths_dict = paths.dict()
    if paths.show_root:
        # Check which paths should be auto-derived
        for key in ["episodes_folder", "media_assets", "uploads", "process"]:
            if paths_dict.get(key) is None:
                # Auto-derive from show_root
                root = Path(paths.show_root)
                if key == "episodes_folder":
                    paths_dict[key] = str(root / "episodes")
                elif key == "media_assets":
                    paths_dict[key] = str(root / "mediaassets")
                else:
                    paths_dict[key] = str(root / key.replace("_", ""))

    settings["media_paths"] = paths_dict

    if save_settings(settings):
        # Validate paths exist or can be created
        validation_results = []
        for key, path in paths_dict.items():
            if path and key not in ["archive_enabled", "archive_type", "archive_endpoint",
                                     "archive_bucket", "archive_path", "archive_credentials"]:
                path_obj = Path(path)
                if not path_obj.exists():
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        validation_results.append(f"Created: {path}")
                    except Exception as e:
                        validation_results.append(f"Cannot create {path}: {str(e)}")
                else:
                    validation_results.append(f"Exists: {path}")

        return {
            "success": True,
            "message": "Media paths updated successfully",
            "paths": paths_dict,
            "validation": validation_results
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


@router.get("/validate-paths")
async def validate_paths(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Validate all configured paths"""
    settings = load_settings()
    paths = settings.get("media_paths", {})

    if "show_root" in paths:
        paths = derive_paths(paths["show_root"], settings)

    validation_results = {}
    for key, path in paths.items():
        if path and key not in ["archive_enabled", "archive_type", "archive_endpoint",
                                 "archive_bucket", "archive_path", "archive_credentials"]:
            path_obj = Path(path)
            validation_results[key] = {
                "path": path,
                "exists": path_obj.exists(),
                "is_directory": path_obj.is_dir() if path_obj.exists() else None,
                "writable": os.access(path, os.W_OK) if path_obj.exists() else None
            }

    return {
        "paths": validation_results,
        "all_valid": all(v["exists"] and v["is_directory"] and v["writable"]
                        for v in validation_results.values() if v["path"])
    }
