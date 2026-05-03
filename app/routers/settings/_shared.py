"""
Shared helpers, models, and constants for the settings router package.
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import json
from datetime import datetime
from auth.utils import get_current_user_or_key
import logging

logger = logging.getLogger(__name__)

# Settings storage file
SETTINGS_FILE = Path("/app/storage/settings.json") if Path("/app").exists() else Path("app/storage/settings.json")


class MediaPathSettings(BaseModel):
    """Media storage path configuration"""
    show_root: str = Field(..., description="Root folder for all show content")
    episodes_folder: Optional[str] = Field(None, description="Episodes folder (auto-derived or custom)")
    media_assets: Optional[str] = Field(None, description="Media assets folder (graphics, promos, ads, music)")
    uploads: Optional[str] = Field(None, description="Uploads folder (locked down)")
    process: Optional[str] = Field(None, description="Process folder (media conversions, automations)")

    # Archive is separate as it may be a remote service
    archive_enabled: bool = Field(False, description="Whether archive storage is enabled")
    archive_type: str = Field("s3", description="Archive storage type (s3, azure, gcs, smb)")
    archive_endpoint: Optional[str] = Field(None, description="Archive service endpoint")
    archive_bucket: Optional[str] = Field(None, description="Archive bucket/container name")
    archive_path: Optional[str] = Field(None, description="Archive path prefix")
    archive_credentials: Optional[Dict[str, str]] = Field(None, description="Archive service credentials")

class InterfaceSettings(BaseModel):
    """Interface preferences"""
    dark_mode: bool = Field(True, description="Enable dark mode")
    compact_view: bool = Field(False, description="Use compact view")
    show_tooltips: bool = Field(True, description="Show helpful tooltips")
    auto_save: bool = Field(True, description="Auto-save changes")
    auto_save_interval: int = Field(30, description="Auto-save interval in seconds")
    sidebar_position: str = Field("left", description="Sidebar position (left/right)")
    default_view: str = Field("grid", description="Default episode view (grid/list)")
    cue_card_alignment: str = Field("left", description="Cue card alignment in script mode (left/center/right)")
    legacy_cue_convert_enabled: bool = Field(True, description="Enable the Legacy Cue Convert module — adds a 'Convert to Cue' button on Auto-Scrub-flagged paragraphs containing legacy {SOT/foo} or (SOT/foo) tokens")

class RundownSettings(BaseModel):
    """Rundown configuration"""
    default_segment_duration: str = Field("00:05:00", description="Default segment duration")
    enable_timecode: bool = Field(True, description="Show timecodes")
    timecode_format: str = Field("HH:MM:SS", description="Timecode display format")
    show_cumulative_time: bool = Field(True, description="Show cumulative runtime")
    enable_drag_drop: bool = Field(True, description="Enable drag and drop reordering")
    auto_calculate_duration: bool = Field(True, description="Auto-calculate total duration")
    warn_on_delete: bool = Field(True, description="Warn before deleting items")
    show_item_numbers: bool = Field(True, description="Display item numbers")
    auto_number_rundown_items: bool = Field(True, description="Auto-number rundown items")
    enumerate_rundown_markdown_files: bool = Field(True, description="Enumerate Rundown Item markdown files with order number")

class SystemSettings(BaseModel):
    """System configuration"""
    enable_websockets: bool = Field(True, description="Enable WebSocket connections")
    max_upload_size_mb: int = Field(100, description="Maximum upload size in MB")
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [".mp4", ".mov", ".mp3", ".wav", ".jpg", ".png", ".pdf"],
        description="Allowed file types for uploads"
    )
    enable_transcoding: bool = Field(True, description="Enable automatic media transcoding")
    backup_enabled: bool = Field(True, description="Enable automatic backups")
    backup_interval_hours: int = Field(24, description="Backup interval in hours")
    log_level: str = Field("INFO", description="Logging level")

class GenerationSettings(BaseModel):
    """Generation/FSQ Quote Generator configuration"""
    preview_background_video: str = Field("/assets/preview-background.mp4", description="Path to preview background video")
    background_video_path: str = Field("/assets/preview-background.mp4", description="Background video path for FSQ")
    default_fsq_style: str = Field("left", description="Default FSQ alignment style")
    default_text_alignment: str = Field("left", description="Default text alignment")
    default_font_family: str = Field("sans-serif", description="Default font family")
    default_font_size: str = Field("19px", description="Default font size")
    include_attribution_default: bool = Field(True, description="Include attribution by default")

    # Screen capacity settings
    fsq_max_lines: int = Field(5, description="Maximum lines per FSQ quote slide")
    fsq_chars_per_line: int = Field(50, description="Average characters per line at default font size")

    # Split behavior settings
    fsq_min_second_screen: int = Field(80, description="Minimum characters for second screen to prevent orphan text")
    fsq_split_strategy: str = Field("smart", description="Split strategy: smart, always_balance, strict_limit, ai_only")

    # Advanced tuning settings
    fsq_balance_threshold_percent: int = Field(30, description="Percentage over limit to trigger balanced split instead of standard")
    fsq_prefer_sentence_boundaries: bool = Field(True, description="Prefer splitting at sentence boundaries (periods, etc)")
    fsq_allow_mid_sentence_split: bool = Field(False, description="Allow splitting at commas/clauses if needed")
    fsq_overflow_handling: str = Field("multi_segment", description="Overflow handling: multi_segment, compress, truncate")

class AutosaveHistorySettings(BaseModel):
    """Autosave file history configuration"""
    enabled: bool = Field(True, description="Enable filesystem autosave snapshots")
    segment_interval_seconds: int = Field(30, description="Seconds between segment snapshots")
    episode_interval_seconds: int = Field(300, description="Seconds between episode snapshots")
    segment_retention_count: int = Field(20, description="Max segment snapshots to keep per item")
    episode_retention_count: int = Field(12, description="Max episode snapshots to keep")

class SettingsUpdate(BaseModel):
    """Complete settings update model"""
    media_paths: Optional[MediaPathSettings] = None
    interface: Optional[InterfaceSettings] = None
    rundown: Optional[RundownSettings] = None
    system: Optional[SystemSettings] = None
    generation: Optional[GenerationSettings] = None
    autosave_history: Optional[AutosaveHistorySettings] = None


def load_settings() -> Dict[str, Any]:
    """Load settings from DATABASE"""
    from database import SessionLocal
    from sqlalchemy import text

    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT category, key, value FROM settings"))
            rows = result.fetchall()

        # Build nested settings structure
        settings = {}
        for category, key, value in rows:
            if category not in settings:
                settings[category] = {}

            # Parse JSON value
            try:
                settings[category][key] = json.loads(value)
            except:
                settings[category][key] = value

        # Add defaults for missing categories
        if "media_paths" not in settings:
            settings["media_paths"] = {
                "show_root": os.getenv("MEDIA_ROOT", "/mnt/sync/disaffected"),
                "episodes_folder": None,
                "media_assets": None,
                "uploads": None,
                "process": None,
                "archive_enabled": False,
                "archive_type": "s3"
            }

        return settings
    except Exception as e:
        logger.error(f"Failed to load settings from database: {e}")
        # Return defaults on error
        return {
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
            "system": SystemSettings().dict(),
            "autosave_history": AutosaveHistorySettings().dict()
        }


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case for database storage"""
    import re
    # Insert underscore before uppercase letters and convert to lowercase
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    return snake


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to DATABASE"""
    from database import SessionLocal
    from sqlalchemy import text

    try:
        with SessionLocal() as db:
            for category, category_data in settings.items():
                if not isinstance(category_data, dict):
                    continue

                for key, value in category_data.items():
                    # Convert camelCase keys to snake_case for database consistency
                    db_key = camel_to_snake(key)

                    # ALWAYS convert value to JSON string for database storage
                    # This ensures proper encoding of all types (strings, numbers, booleans, etc.)
                    value_str = json.dumps(value)

                    # Upsert to database
                    db.execute(text("""
                        INSERT INTO settings (category, key, value, updated_at)
                        VALUES (:category, :key, :value, NOW())
                        ON CONFLICT (key)
                        DO UPDATE SET
                            value = :value,
                            category = :category,
                            updated_at = NOW()
                    """), {"category": category, "key": db_key, "value": value_str})

            db.commit()

        logger.info("Settings saved successfully to database")
        return True
    except Exception as e:
        logger.error(f"Failed to save settings to database: {e}")
        return False


def derive_paths(show_root: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Auto-derive paths from show root if not manually set"""
    paths = settings.get("media_paths", {})
    root = Path(show_root)

    # Auto-derive paths if not manually overridden
    if not paths.get("episodes_folder"):
        paths["episodes_folder"] = str(root / "episodes")
    if not paths.get("media_assets"):
        paths["media_assets"] = str(root / "mediaassets")
    if not paths.get("uploads"):
        paths["uploads"] = str(root / "uploads")
    if not paths.get("process"):
        paths["process"] = str(root / "process")

    return paths


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"
