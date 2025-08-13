"""
Settings management router for Show-Build application
Handles configuration of media paths, system settings, and preferences
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import json
from auth.utils import get_current_user_or_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

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

class SettingsUpdate(BaseModel):
    """Complete settings update model"""
    media_paths: Optional[MediaPathSettings] = None
    interface: Optional[InterfaceSettings] = None
    rundown: Optional[RundownSettings] = None
    system: Optional[SystemSettings] = None

def load_settings() -> Dict[str, Any]:
    """Load settings from file or return defaults"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    # Return default settings
    return {
        "media_paths": {
            "show_root": os.getenv("MEDIA_ROOT", "/mnt/sync/disaffected"),
            "episodes_folder": None,  # Will auto-derive
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

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file"""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
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
    settings = load_settings()
    settings["rundown"] = rundown.dict()
    
    if save_settings(settings):
        return {
            "success": True,
            "message": "Rundown settings updated successfully",
            "settings": rundown.dict()
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")

@router.put("/system")
async def update_system_settings(
    system: SystemSettings,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Update system settings"""
    settings = load_settings()
    settings["system"] = system.dict()
    
    if save_settings(settings):
        # Apply system settings changes
        if system.log_level:
            logging.getLogger().setLevel(getattr(logging, system.log_level))
        
        return {
            "success": True,
            "message": "System settings updated successfully",
            "settings": system.dict()
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")

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

@router.get("/system-info")
async def get_system_info(
    current_user: Optional[dict] = None  # Make auth optional for now
) -> Dict[str, Any]:
    """Get system information including database size, media usage, cache, and backups"""
    import subprocess
    import shutil
    from datetime import datetime
    
    system_info = {
        "database_size": None,
        "media_storage_used": None,
        "cache_size": None,
        "last_backup": None,
        "disk_usage": {},
        "episode_count": 0
    }
    
    try:
        # Get database size (PostgreSQL)
        try:
            # Connect to database and get size
            import psycopg2
            from urllib.parse import urlparse
            
            db_url = os.getenv("DATABASE_URL", "postgresql://showbuild:showbuild@show-build-postgres/showbuild")
            parsed = urlparse(db_url)
            
            conn = psycopg2.connect(
                host=parsed.hostname or "show-build-postgres",
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/') or "showbuild",
                user=parsed.username or "showbuild",
                password=parsed.password or "showbuild"
            )
            
            cur = conn.cursor()
            cur.execute("""
                SELECT pg_database_size(current_database()) as size,
                       pg_size_pretty(pg_database_size(current_database())) as pretty_size
            """)
            result = cur.fetchone()
            if result:
                system_info["database_size"] = {
                    "bytes": result[0],
                    "formatted": result[1]
                }
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not get database size: {e}")
            system_info["database_size"] = {
                "bytes": 0,
                "formatted": "Unknown"
            }
        
        # Get media storage usage
        settings = load_settings()
        media_root = settings.get("media_paths", {}).get("show_root", "/mnt/sync/disaffected")
        
        if Path(media_root).exists():
            # Get total size of media directory
            total_size = 0
            episode_count = 0
            
            episodes_path = Path(media_root) / "episodes"
            if episodes_path.exists():
                for item in episodes_path.iterdir():
                    if item.is_dir() and item.name.isdigit():
                        episode_count += 1
                        # Get size of episode directory
                        for root, dirs, files in os.walk(item):
                            for file in files:
                                file_path = Path(root) / file
                                if file_path.exists():
                                    total_size += file_path.stat().st_size
            
            # Add other media directories
            for subdir in ["mediaassets", "uploads", "process"]:
                path = Path(media_root) / subdir
                if path.exists():
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = Path(root) / file
                            if file_path.exists():
                                total_size += file_path.stat().st_size
            
            system_info["media_storage_used"] = {
                "bytes": total_size,
                "formatted": format_bytes(total_size)
            }
            system_info["episode_count"] = episode_count
            
            # Get disk usage for media root
            if shutil.disk_usage:
                usage = shutil.disk_usage(media_root)
                system_info["disk_usage"] = {
                    "total": {
                        "bytes": usage.total,
                        "formatted": format_bytes(usage.total)
                    },
                    "used": {
                        "bytes": usage.used,
                        "formatted": format_bytes(usage.used)
                    },
                    "free": {
                        "bytes": usage.free,
                        "formatted": format_bytes(usage.free)
                    },
                    "percent": round((usage.used / usage.total) * 100, 1)
                }
        
        # Get cache size (Redis and temp files)
        cache_size = 0
        
        # Check Redis memory usage
        try:
            import redis
            r = redis.Redis(host='showbuild-redis', port=6379, decode_responses=True)
            info = r.info('memory')
            cache_size += int(info.get('used_memory', 0))
        except Exception as e:
            logger.debug(f"Could not get Redis memory usage: {e}")
        
        # Check temp/cache directories
        cache_dirs = [
            Path("/tmp"),
            Path("/app/cache") if Path("/app/cache").exists() else None,
            Path("/home/.cache") if Path("/home/.cache").exists() else None
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir and cache_dir.exists():
                for root, dirs, files in os.walk(cache_dir):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.exists():
                            try:
                                cache_size += file_path.stat().st_size
                            except:
                                pass
        
        system_info["cache_size"] = {
            "bytes": cache_size,
            "formatted": format_bytes(cache_size)
        }
        
        # Get last backup information
        backup_dir = Path("/mnt/sync/disaffected/backups")
        if not backup_dir.exists():
            backup_dir = Path("/app/backups")
        
        if backup_dir.exists():
            # Find most recent backup file
            backup_files = list(backup_dir.glob("*.tar.gz")) + list(backup_dir.glob("*.sql")) + list(backup_dir.glob("*.zip"))
            if backup_files:
                most_recent = max(backup_files, key=lambda f: f.stat().st_mtime)
                system_info["last_backup"] = {
                    "filename": most_recent.name,
                    "timestamp": datetime.fromtimestamp(most_recent.stat().st_mtime).isoformat(),
                    "size": {
                        "bytes": most_recent.stat().st_size,
                        "formatted": format_bytes(most_recent.stat().st_size)
                    },
                    "age_hours": round((datetime.now().timestamp() - most_recent.stat().st_mtime) / 3600, 1)
                }
        
        # Get Python process memory usage
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            system_info["process_memory"] = {
                "rss": {
                    "bytes": mem_info.rss,
                    "formatted": format_bytes(mem_info.rss)
                },
                "vms": {
                    "bytes": mem_info.vms,
                    "formatted": format_bytes(mem_info.vms)
                }
            }
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
    
    return system_info

def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

@router.post("/backup")
async def create_backup(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Create a backup of the database and configuration"""
    from datetime import datetime
    import subprocess
    import tarfile
    
    try:
        # Create backup directory if it doesn't exist
        backup_dir = Path("/mnt/sync/disaffected/backups")
        if not backup_dir.exists():
            backup_dir = Path("/app/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup database
        db_backup_file = backup_dir / f"database_backup_{timestamp}.sql"
        db_url = os.getenv("DATABASE_URL", "postgresql://showbuild:showbuild@show-build-postgres/showbuild")
        
        # Parse database URL
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        # Use pg_dump to backup database
        dump_cmd = [
            "pg_dump",
            "-h", parsed.hostname or "show-build-postgres",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "showbuild",
            "-d", parsed.path.lstrip('/') or "showbuild",
            "-f", str(db_backup_file)
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = parsed.password or "showbuild"
        
        try:
            subprocess.run(dump_cmd, check=True, env=env, capture_output=True)
            logger.info(f"Database backed up to {db_backup_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Database backup failed: {e.stderr}")
            # Continue with config backup even if DB backup fails
        
        # Backup configuration files
        config_backup_file = backup_dir / f"config_backup_{timestamp}.tar.gz"
        
        with tarfile.open(config_backup_file, "w:gz") as tar:
            # Add settings file
            if SETTINGS_FILE.exists():
                tar.add(SETTINGS_FILE, arcname="settings.json")
            
            # Add user storage files
            storage_dir = Path("/app/storage") if Path("/app").exists() else Path("app/storage")
            if storage_dir.exists():
                for file in storage_dir.glob("*.json"):
                    tar.add(file, arcname=f"storage/{file.name}")
            
            # Add environment file if it exists
            env_file = Path("/app/.env") if Path("/app").exists() else Path(".env")
            if env_file.exists():
                tar.add(env_file, arcname=".env")
        
        logger.info(f"Configuration backed up to {config_backup_file}")
        
        # Get backup sizes
        backup_info = {
            "success": True,
            "timestamp": timestamp,
            "files": []
        }
        
        if db_backup_file.exists():
            backup_info["files"].append({
                "type": "database",
                "filename": db_backup_file.name,
                "size": format_bytes(db_backup_file.stat().st_size)
            })
        
        if config_backup_file.exists():
            backup_info["files"].append({
                "type": "configuration",
                "filename": config_backup_file.name,
                "size": format_bytes(config_backup_file.stat().st_size)
            })
        
        return backup_info
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.delete("/cache")
async def clear_cache(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Clear application cache"""
    import shutil
    
    cleared = {
        "redis": False,
        "temp_files": 0,
        "freed_space": 0
    }
    
    try:
        # Clear Redis cache
        try:
            import redis
            r = redis.Redis(host='showbuild-redis', port=6379)
            r.flushdb()
            cleared["redis"] = True
            logger.info("Redis cache cleared")
        except Exception as e:
            logger.warning(f"Could not clear Redis cache: {e}")
        
        # Clear temp directories
        cache_dirs = [
            Path("/tmp/show-build"),
            Path("/app/cache") if Path("/app/cache").exists() else None,
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir and cache_dir.exists():
                try:
                    # Calculate size before deletion
                    size_before = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    cleared["freed_space"] += size_before
                    
                    # Remove directory contents
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    cleared["temp_files"] += 1
                except Exception as e:
                    logger.warning(f"Could not clear {cache_dir}: {e}")
        
        cleared["freed_space_formatted"] = format_bytes(cleared["freed_space"])
        
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "details": cleared
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")