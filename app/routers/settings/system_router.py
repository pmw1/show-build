"""
System settings, system info, backup, and cache endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pathlib import Path
import os
import logging

from auth.utils import get_current_user_or_key
from ._shared import (
    load_settings, save_settings, format_bytes,
    SystemSettings, AutosaveHistorySettings, SETTINGS_FILE,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])


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


@router.put("/autosave-history")
async def update_autosave_history_settings(
    autosave: AutosaveHistorySettings,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Update autosave history settings"""
    settings = load_settings()
    settings["autosave_history"] = autosave.dict()

    if save_settings(settings):
        return {
            "success": True,
            "message": "Autosave history settings updated successfully",
            "settings": autosave.dict()
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


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
                from datetime import datetime as dt
                system_info["last_backup"] = {
                    "filename": most_recent.name,
                    "timestamp": dt.fromtimestamp(most_recent.stat().st_mtime).isoformat(),
                    "size": {
                        "bytes": most_recent.stat().st_size,
                        "formatted": format_bytes(most_recent.stat().st_size)
                    },
                    "age_hours": round((dt.now().timestamp() - most_recent.stat().st_mtime) / 3600, 1)
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
        raise HTTPException(status_code=500, detail=str(e))
