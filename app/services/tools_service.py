"""
Tools Service - Business logic for production tools.

Provides sync operations for:
- Extended health check
- Rundown diff comparison
"""

import os
import time
import socket
import logging
import httpx
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text, func

logger = logging.getLogger(__name__)


class ToolsService:
    """Service class for production tool operations."""

    @staticmethod
    async def run_health_check(db: Session) -> Dict[str, Any]:
        """
        Run extended health check with detailed diagnostics.

        Returns comprehensive status of:
        - Database (connectivity, table counts, recent activity)
        - Redis (connectivity, memory, queue lengths)
        - Celery (workers, active tasks)
        - Storage (paths, free space)
        - External APIs (Ollama, XTTS, etc.)
        """
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "healthy",
            "database": {},
            "redis": {},
            "celery": {},
            "storage": {},
            "apis": {}
        }

        issues = []

        # ========================================
        # Database Health
        # ========================================
        try:
            # Basic connectivity
            db.execute(text("SELECT 1"))
            result["database"]["connected"] = True

            # Table counts
            table_counts = {}
            tables_to_check = [
                "episodes", "rundown_items", "segments", "cues",
                "asset_id_registry", "users", "sot_processing_jobs"
            ]

            for table in tables_to_check:
                try:
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    table_counts[table] = count_result.scalar()
                except Exception:
                    table_counts[table] = "N/A"

            result["database"]["table_counts"] = table_counts

            # Recent activity (rundown items modified in last 24h)
            try:
                recent_count = db.execute(text("""
                    SELECT COUNT(*) FROM rundown_items
                    WHERE updated_at > NOW() - INTERVAL '24 hours'
                """)).scalar()
                result["database"]["recent_activity_24h"] = recent_count
            except Exception:
                result["database"]["recent_activity_24h"] = "N/A"

            result["database"]["status"] = "healthy"

        except Exception as e:
            result["database"]["connected"] = False
            result["database"]["status"] = "error"
            result["database"]["error"] = str(e)[:100]
            issues.append("Database connection failed")

        # ========================================
        # Redis Health
        # ========================================
        try:
            redis_url = os.getenv("REDIS_URL", "redis://:showbuild2025@192.168.51.223:6379/0")
            redis_password = os.getenv("REDIS_PASSWORD", "showbuild2025")

            # Parse Redis URL
            if "://" in redis_url:
                url_part = redis_url.split("://")[1]
                if "@" in url_part:
                    _, host_port = url_part.split("@", 1)
                else:
                    host_port = url_part
                redis_host = host_port.split(":")[0]
                port_and_db = host_port.split(":")[1] if ":" in host_port else "6379/0"
                redis_port = int(port_and_db.split("/")[0])
            else:
                redis_host = "192.168.51.223"
                redis_port = 6379

            start_time = time.time()
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                socket_connect_timeout=2,
                socket_timeout=2,
                db=0
            )

            # Ping test
            r.ping()
            latency_ms = int((time.time() - start_time) * 1000)

            result["redis"]["connected"] = True
            result["redis"]["latency_ms"] = latency_ms
            result["redis"]["host"] = redis_host

            # Memory info
            try:
                info = r.info("memory")
                result["redis"]["used_memory_human"] = info.get("used_memory_human", "N/A")
                result["redis"]["used_memory_peak_human"] = info.get("used_memory_peak_human", "N/A")
            except Exception:
                pass

            # Queue lengths
            queue_lengths = {}
            queues = ["celery", "assets", "assets_high", "assets_low", "media", "compilation", "quotes", "fsq"]
            for queue in queues:
                try:
                    length = r.llen(queue)
                    if length > 0:
                        queue_lengths[queue] = length
                except Exception:
                    pass

            result["redis"]["queue_lengths"] = queue_lengths
            result["redis"]["status"] = "healthy"

        except redis.ConnectionError:
            result["redis"]["connected"] = False
            result["redis"]["status"] = "error"
            result["redis"]["error"] = "Connection refused"
            issues.append("Redis connection failed")
        except Exception as e:
            result["redis"]["connected"] = False
            result["redis"]["status"] = "error"
            result["redis"]["error"] = str(e)[:100]
            issues.append("Redis error")

        # ========================================
        # Celery Health
        # ========================================
        try:
            from celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=2)
            active_workers = inspect.active()
            stats = inspect.stats()

            if active_workers:
                worker_info = {}
                for worker_name, tasks in active_workers.items():
                    worker_info[worker_name] = {
                        "active_tasks": len(tasks),
                        "status": "online"
                    }
                    if stats and worker_name in stats:
                        worker_stats = stats[worker_name]
                        worker_info[worker_name]["pool"] = worker_stats.get("pool", {}).get("max-concurrency", "N/A")

                result["celery"]["workers"] = worker_info
                result["celery"]["total_workers"] = len(worker_info)
                result["celery"]["status"] = "healthy"
            else:
                result["celery"]["workers"] = {}
                result["celery"]["total_workers"] = 0
                result["celery"]["status"] = "warning"
                result["celery"]["message"] = "No workers online"
                issues.append("No Celery workers online")

        except Exception as e:
            result["celery"]["status"] = "error"
            result["celery"]["error"] = str(e)[:100]
            issues.append("Celery check failed")

        # ========================================
        # Storage Health
        # ========================================
        storage_paths = {
            "episodes": "/home/episodes",
            "shared_media": "/shared_media",
            "preproc_working": "/shared_media/preproc/working"
        }

        for name, path in storage_paths.items():
            try:
                path_obj = Path(path)
                if path_obj.exists():
                    # Check if readable
                    can_read = os.access(path, os.R_OK)
                    can_write = os.access(path, os.W_OK)

                    # Get disk usage
                    statvfs = os.statvfs(path)
                    total = statvfs.f_frsize * statvfs.f_blocks
                    free = statvfs.f_frsize * statvfs.f_bfree
                    used_pct = ((total - free) / total) * 100 if total > 0 else 0

                    result["storage"][name] = {
                        "path": path,
                        "exists": True,
                        "readable": can_read,
                        "writable": can_write,
                        "free_gb": round(free / (1024**3), 2),
                        "used_percent": round(used_pct, 1),
                        "status": "healthy" if can_read and can_write and used_pct < 90 else "warning"
                    }

                    if used_pct >= 90:
                        issues.append(f"Storage {name} nearly full ({used_pct:.0f}%)")
                    if not can_write:
                        issues.append(f"Storage {name} not writable")
                else:
                    result["storage"][name] = {
                        "path": path,
                        "exists": False,
                        "status": "error"
                    }
                    issues.append(f"Storage path {name} not found")
            except Exception as e:
                result["storage"][name] = {
                    "path": path,
                    "status": "error",
                    "error": str(e)[:50]
                }

        # ========================================
        # External APIs Health
        # ========================================

        # Ollama
        try:
            ollama_result = db.execute(text("""
                SELECT config_value FROM api_configs
                WHERE service = 'ollama' AND config_key = 'host' AND is_enabled = true
            """))
            ollama_host = ollama_result.scalar()

            if ollama_host:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(f"{ollama_host}/api/tags")
                    if response.status_code == 200:
                        data = response.json()
                        models = [m["name"] for m in data.get("models", [])]
                        result["apis"]["ollama"] = {
                            "status": "connected",
                            "host": ollama_host,
                            "models_available": len(models),
                            "models": models[:5]  # First 5 models
                        }
                    else:
                        result["apis"]["ollama"] = {
                            "status": "error",
                            "host": ollama_host,
                            "error": f"HTTP {response.status_code}"
                        }
            else:
                result["apis"]["ollama"] = {"status": "not_configured"}
        except httpx.TimeoutException:
            result["apis"]["ollama"] = {"status": "timeout", "host": ollama_host}
        except httpx.ConnectError:
            result["apis"]["ollama"] = {"status": "connection_refused", "host": ollama_host if 'ollama_host' in locals() else "unknown"}
        except Exception as e:
            result["apis"]["ollama"] = {"status": "error", "error": str(e)[:50]}

        # XTTS/TTS
        try:
            xtts_result = db.execute(text("""
                SELECT config_value FROM api_configs
                WHERE service = 'xtts' AND config_key = 'host' AND is_enabled = true
            """))
            xtts_host = xtts_result.scalar()

            if xtts_host:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(f"{xtts_host}/health")
                    if response.status_code == 200:
                        result["apis"]["xtts"] = {
                            "status": "connected",
                            "host": xtts_host
                        }
                    else:
                        result["apis"]["xtts"] = {
                            "status": "error",
                            "host": xtts_host,
                            "error": f"HTTP {response.status_code}"
                        }
            else:
                result["apis"]["xtts"] = {"status": "not_configured"}
        except Exception as e:
            result["apis"]["xtts"] = {"status": "error", "error": str(e)[:50]}

        # ========================================
        # Overall Status
        # ========================================
        if any("error" in str(v).lower() for v in [
            result["database"].get("status"),
            result["redis"].get("status")
        ]):
            result["status"] = "degraded"
        elif issues:
            result["status"] = "warning"

        result["issues"] = issues

        return result

    @staticmethod
    def compare_rundown_versions(
        db: Session,
        episode: str,
        version_a: Optional[str] = None,
        version_b: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare two rundown versions.

        If versions not specified, compares current state with itself
        (useful for getting current rundown structure).
        """
        from models_v2 import RundownItem, Episode, Rundown

        # Get episode
        episode_record = db.query(Episode).filter(
            Episode.episode_number == int(episode.lstrip('0')) if episode.isdigit() else Episode.episode_number == episode
        ).first()

        if not episode_record:
            raise ValueError(f"Episode {episode} not found")

        # Get rundowns for this episode
        rundowns = db.query(Rundown).filter(
            Rundown.episode_id == episode_record.id
        ).all()

        rundown_ids = [r.id for r in rundowns]

        if not rundown_ids:
            raise ValueError(f"No rundowns found for episode {episode}")

        # Get current rundown items through rundown relationship
        current_items = db.query(RundownItem).filter(
            RundownItem.rundown_id.in_(rundown_ids)
        ).order_by(RundownItem.order_in_rundown).all()

        # Build current state
        current_state = []
        for item in current_items:
            current_state.append({
                "id": item.id,
                "asset_id": item.asset_id,
                "slug": item.slug,
                "title": item.title,
                "item_type": item.item_type,
                "order": item.order_in_rundown,
                "duration": item.duration,
                "status": item.status,
                "has_script": bool(item.script_content and len(item.script_content) > 50)
            })

        # For now, we only support current vs current (shows structure)
        # Future: Add snapshot storage for historical comparison
        if version_a and version_b and version_a != version_b:
            # Would need snapshot table to compare different versions
            logger.warning("Historical version comparison not yet implemented")

        # Return current structure as both versions (no diff)
        return {
            "episode": episode,
            "additions": [],
            "deletions": [],
            "modifications": [],
            "summary": {
                "total_items": len(current_state),
                "by_type": _count_by_type(current_state),
                "by_status": _count_by_status(current_state),
                "with_scripts": sum(1 for item in current_state if item["has_script"]),
                "total_duration": _sum_durations(current_state)
            },
            "current_state": current_state
        }


def _count_by_type(items: List[Dict]) -> Dict[str, int]:
    """Count items by type."""
    counts = {}
    for item in items:
        item_type = item.get("item_type", "unknown")
        counts[item_type] = counts.get(item_type, 0) + 1
    return counts


def _count_by_status(items: List[Dict]) -> Dict[str, int]:
    """Count items by status."""
    counts = {}
    for item in items:
        status = item.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _sum_durations(items: List[Dict]) -> str:
    """Sum all durations and return formatted time."""
    total_seconds = 0
    for item in items:
        duration = item.get("duration", "00:00:00")
        if duration and isinstance(duration, str):
            try:
                parts = duration.split(":")
                if len(parts) == 3:
                    h, m, s = parts
                    total_seconds += int(h) * 3600 + int(m) * 60 + int(float(s))
                elif len(parts) == 2:
                    m, s = parts
                    total_seconds += int(m) * 60 + int(float(s))
            except (ValueError, TypeError):
                pass

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
