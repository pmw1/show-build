"""Health, ping, and version endpoints."""

import os
import logging
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/ping")
async def ping():
    """Lightweight liveness check for Docker healthcheck."""
    return {"status": "ok"}


@router.get("/health")
async def health():
    from sqlalchemy import text
    from database import SessionLocal

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "database": "unknown",
            "ollama": {
                "status": "unknown",
                "model": None,
                "url": None
            },
            "redis": {
                "status": "unknown",
                "connected": False,
                "latency": None,
                "error": None
            },
            "celery": {
                "status": "unknown",
                "workers": [],
                "error": None
            },
            "asterisk": {
                "status": "unknown",
                "connected": False,
                "host": None,
                "error": None
            },
            "google_drive": {
                "status": "unknown",
                "connected": False,
                "can_list": False,
                "can_write": False,
                "error": None
            },
            "xtts": {
                "status": "unknown",
                "host": None,
                "error": None
            },
            "vmix": {
                "status": "unknown",
                "connected": False,
                "host": None,
                "error": None
            },
            "whisper": {
                "status": "unknown",
                "connected": False,
                "host": None,
                "error": None
            }
        }
    }

    # Test database connectivity
    try:
        import json
        import asyncpg

        config_dir = Path("/app/config") if Path("/app").exists() else Path("app/config")
        db_config_file = config_dir / "database.json"

        if db_config_file.exists():
            with open(db_config_file, 'r') as f:
                db_config = json.load(f)

            conn = await asyncpg.connect(
                host=db_config.get("host", "postgres"),
                port=db_config.get("port", 5432),
                database=db_config.get("database", "showbuild"),
                user=db_config.get("username", "showbuild"),
                password=db_config.get("password", "showbuild")
            )

            await conn.fetchval("SELECT 1")
            await conn.close()

            health_status["services"]["database"] = "connected"
        else:
            health_status["services"]["database"] = "no_config"

    except Exception as e:
        error_type = type(e).__name__
        if "InvalidAuthorizationSpecification" in error_type:
            health_status["services"]["database"] = "auth_failed"
        elif "InvalidCatalogName" in error_type:
            health_status["services"]["database"] = "db_not_found"
        elif isinstance(e, OSError):
            health_status["services"]["database"] = "connection_refused"
        else:
            health_status["services"]["database"] = f"error: {str(e)[:50]}"

    # Check XTTS connectivity (from database config)
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT config_key, config_value
                FROM api_configs
                WHERE service = 'xtts' AND is_enabled = true
            """))
            rows = result.fetchall()

            if rows:
                xtts_config = {row[0]: row[1] for row in rows}

                if xtts_config.get('enabled') == 'true' and xtts_config.get('host'):
                    xtts_host = xtts_config['host']
                    try:
                        async with httpx.AsyncClient(timeout=2.0) as client:
                            response = await client.get(f"{xtts_host}/health")
                            if response.status_code == 200:
                                health_status["services"]["xtts"] = {
                                    "status": "connected",
                                    "host": xtts_host
                                }
                            else:
                                health_status["services"]["xtts"] = {
                                    "status": "error",
                                    "host": xtts_host,
                                    "error": f"HTTP {response.status_code}"
                                }
                    except httpx.ConnectError:
                        health_status["services"]["xtts"] = {
                            "status": "error",
                            "host": xtts_host,
                            "error": "Connection refused"
                        }
                    except httpx.TimeoutException:
                        health_status["services"]["xtts"] = {
                            "status": "warning",
                            "host": xtts_host,
                            "error": "Timeout"
                        }
                    except Exception as e:
                        health_status["services"]["xtts"] = {
                            "status": "error",
                            "host": xtts_host,
                            "error": str(e)[:50]
                        }
                else:
                    health_status["services"]["xtts"] = {
                        "status": "not_configured"
                    }
            else:
                health_status["services"]["xtts"] = {
                    "status": "not_configured"
                }
    except Exception as e:
        health_status["services"]["xtts"] = {
            "status": "error",
            "error": str(e)[:50]
        }

    # Test Ollama connectivity (load from database)
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT config_key, config_value, is_enabled
                FROM api_configs
                WHERE service = 'ollama' AND category = 'ai_services'
            """))
            rows = result.fetchall()

            if rows:
                ollama_config = {}
                is_enabled = False

                for row in rows:
                    key, value, enabled = row
                    if key == 'enabled':
                        is_enabled = enabled
                    else:
                        ollama_config[key] = value

                if is_enabled and ollama_config.get("host"):
                    ollama_host = ollama_config.get("host")
                    ollama_model = ollama_config.get("model")

                    health_status["services"]["ollama"]["url"] = ollama_host
                    health_status["services"]["ollama"]["model"] = ollama_model

                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{ollama_host}/api/tags")
                        if response.status_code == 200:
                            health_status["services"]["ollama"]["status"] = "connected"
                        else:
                            health_status["services"]["ollama"]["status"] = f"error: HTTP {response.status_code}"
                else:
                    health_status["services"].pop("ollama", None)
            else:
                health_status["services"].pop("ollama", None)

    except httpx.TimeoutException:
        health_status["services"]["ollama"]["status"] = "timeout"
    except httpx.ConnectError:
        health_status["services"]["ollama"]["status"] = "connection_refused"
    except Exception:
        health_status["services"].pop("ollama", None)

    # Test Redis connectivity
    try:
        import redis
        import time

        redis_url = os.getenv("REDIS_URL", "redis://192.168.51.223:6379/0")
        redis_password = os.getenv("REDIS_PASSWORD", "showbuild2025")

        if redis_url.startswith("redis://"):
            url_part = redis_url.replace("redis://", "")
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
            socket_connect_timeout=1,
            socket_timeout=1,
            db=0
        )

        r.ping()
        latency_ms = int((time.time() - start_time) * 1000)

        health_status["services"]["redis"]["status"] = "connected"
        health_status["services"]["redis"]["connected"] = True
        health_status["services"]["redis"]["latency"] = latency_ms

    except Exception as e:
        health_status["services"]["redis"]["status"] = "error"
        error_type = type(e).__name__
        if "ConnectionError" in error_type:
            health_status["services"]["redis"]["error"] = "Connection refused"
        elif "TimeoutError" in error_type:
            health_status["services"]["redis"]["error"] = "Timeout"
        else:
            health_status["services"]["redis"]["error"] = str(e)[:50]

    # Test Celery worker connectivity
    try:
        from celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=1)
        active_workers = inspect.active()

        if active_workers:
            worker_names = list(active_workers.keys())
            health_status["services"]["celery"]["status"] = "connected"
            health_status["services"]["celery"]["workers"] = worker_names
        else:
            health_status["services"]["celery"]["status"] = "no_workers"
            health_status["services"]["celery"]["workers"] = []

    except Exception as e:
        health_status["services"]["celery"]["status"] = "error"
        health_status["services"]["celery"]["error"] = str(e)[:50]

    # Test NFS/shared storage connectivity
    try:
        episodes_dir = Path("/home/episodes")

        if episodes_dir.exists():
            try:
                list(episodes_dir.iterdir())

                shared_media = Path("/shared_media")
                if shared_media.exists():
                    test_dir = shared_media / "temp" / "uploads"
                    test_dir.mkdir(parents=True, exist_ok=True)
                    test_file = test_dir / ".health_check"
                    test_file.touch()
                    test_file.unlink()

                    health_status["services"]["nfs"] = {
                        "status": "connected",
                        "mount_point": "/mnt/sync",
                        "readable": True,
                        "writable": True
                    }
                else:
                    health_status["services"]["nfs"] = {
                        "status": "warning",
                        "mount_point": "/mnt/sync",
                        "readable": True,
                        "writable": False,
                        "error": "Shared media directory not found"
                    }
            except PermissionError:
                health_status["services"]["nfs"] = {
                    "status": "warning",
                    "mount_point": "/mnt/sync",
                    "readable": True,
                    "writable": False,
                    "error": "Write permission denied"
                }
            except Exception as e:
                health_status["services"]["nfs"] = {
                    "status": "warning",
                    "mount_point": "/mnt/sync",
                    "readable": True,
                    "writable": False,
                    "error": f"Write test failed: {str(e)[:50]}"
                }
        else:
            health_status["services"]["nfs"] = {
                "status": "error",
                "mount_point": "/mnt/sync",
                "readable": False,
                "writable": False,
                "error": "Episodes directory not accessible"
            }

    except Exception as e:
        health_status["services"]["nfs"] = {
            "status": "error",
            "error": str(e)[:50]
        }

    # Test TTS connectivity (Fish Speech or XTTS)
    try:
        from api_config import api_config_manager

        fishspeech_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="fishspeech"
        )

        xtts_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="xtts"
        )

        fishspeech_enabled = fishspeech_config and fishspeech_config.get("enabled")
        xtts_enabled = xtts_config and xtts_config.get("enabled")

        if fishspeech_enabled and not xtts_enabled:
            fish_host = fishspeech_config.get("host")
            if not fish_host:
                health_status["services"]["tts"] = {
                    "status": "error",
                    "connected": False,
                    "service": "fishspeech",
                    "label": "Fish",
                    "error": "No host configured"
                }
            else:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{fish_host}/")
                        if response.status_code == 200:
                            health_status["services"]["tts"] = {
                                "status": "connected",
                                "connected": True,
                                "service": "fishspeech",
                                "label": "Fish",
                                "host": fish_host
                            }
                        else:
                            health_status["services"]["tts"] = {
                                "status": "error",
                                "connected": False,
                                "service": "fishspeech",
                                "label": "Fish",
                                "error": f"HTTP {response.status_code}"
                            }
                except httpx.TimeoutException:
                    health_status["services"]["tts"] = {
                        "status": "error",
                        "connected": False,
                        "service": "fishspeech",
                        "label": "Fish",
                        "error": "Timeout"
                    }
                except httpx.ConnectError:
                    health_status["services"]["tts"] = {
                        "status": "error",
                        "connected": False,
                        "service": "fishspeech",
                        "label": "Fish",
                        "error": "Connection refused"
                    }

            health_status["services"]["xtts"] = {
                "status": "deprecated",
                "connected": False,
                "error": "Replaced by Fish Speech"
            }
        elif not xtts_config:
            health_status["services"]["xtts"] = {
                "status": "error",
                "connected": False,
                "error": "Not configured"
            }
        elif not xtts_enabled:
            health_status["services"]["xtts"] = {
                "status": "error",
                "connected": False,
                "error": "Disabled in settings"
            }
        else:
            host = xtts_config.get("host")
            if not host:
                health_status["services"]["xtts"] = {
                    "status": "error",
                    "connected": False,
                    "error": "No host configured"
                }
            else:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{host}/health")
                    if response.status_code == 200:
                        data = response.json()
                        is_healthy = data.get("status") == "healthy"
                        model_loaded = data.get("model_loaded", False)

                        if is_healthy and model_loaded:
                            health_status["services"]["xtts"] = {
                                "status": "connected",
                                "connected": True,
                                "quota_remaining": None
                            }
                        else:
                            health_status["services"]["xtts"] = {
                                "status": "error",
                                "connected": False,
                                "error": "Unhealthy or model not loaded"
                            }
                    else:
                        health_status["services"]["xtts"] = {
                            "status": "error",
                            "connected": False,
                            "error": f"HTTP {response.status_code}"
                        }

    except httpx.TimeoutException:
        health_status["services"]["xtts"] = {
            "status": "error",
            "connected": False,
            "error": "Timeout"
        }
    except httpx.ConnectError:
        health_status["services"]["xtts"] = {
            "status": "error",
            "connected": False,
            "error": "Connection refused"
        }
    except Exception as e:
        health_status["services"]["xtts"] = {
            "status": "error",
            "connected": False,
            "error": f"Error: {str(e)[:30]}"
        }

    # Test Asterisk AMI connectivity
    try:
        import socket

        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT config_key, config_value, is_enabled
                FROM api_configs
                WHERE service = 'asterisk' AND category = 'communication' AND is_enabled = true
            """))
            rows = result.fetchall()

            if rows:
                asterisk_config = {}
                is_enabled = False

                for row in rows:
                    key, value, enabled = row
                    if key == 'enabled':
                        is_enabled = enabled
                    else:
                        asterisk_config[key] = value

                if is_enabled and asterisk_config.get("host"):
                    asterisk_host = asterisk_config.get("host")
                    asterisk_port = int(asterisk_config.get("amiPort", 5038))

                    health_status["services"]["asterisk"]["host"] = asterisk_host

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    try:
                        sock.connect((asterisk_host, asterisk_port))
                        health_status["services"]["asterisk"]["status"] = "connected"
                        health_status["services"]["asterisk"]["connected"] = True
                        sock.close()
                    except (socket.timeout, ConnectionRefusedError):
                        health_status["services"]["asterisk"]["status"] = "error"
                        health_status["services"]["asterisk"]["error"] = "Connection refused"
                else:
                    health_status["services"].pop("asterisk", None)
            else:
                health_status["services"].pop("asterisk", None)

    except Exception:
        health_status["services"].pop("asterisk", None)

    # Test Google Drive API connectivity
    try:
        from services.google_drive_service import get_drive_service_from_config
        from api_config import APIConfigManager

        health_status["services"]["google_drive"] = {
            "status": "unknown",
            "connected": False,
            "can_list": False,
            "can_write": False,
            "error": None
        }

        api_config_mgr = APIConfigManager()
        drive_service = get_drive_service_from_config(api_config_mgr)

        if drive_service:
            try:
                files = drive_service.list_files(page_size=1)
                health_status["services"]["google_drive"]["connected"] = True
                health_status["services"]["google_drive"]["can_list"] = True

                if drive_service.service:
                    health_status["services"]["google_drive"]["can_write"] = True
                    health_status["services"]["google_drive"]["status"] = "connected"
                else:
                    health_status["services"]["google_drive"]["status"] = "warning"
                    health_status["services"]["google_drive"]["error"] = "Service initialized but may have limited permissions"

            except Exception as list_error:
                health_status["services"]["google_drive"]["status"] = "warning"
                health_status["services"]["google_drive"]["connected"] = True
                health_status["services"]["google_drive"]["error"] = f"Connected but listing failed: {str(list_error)[:50]}"
        else:
            health_status["services"]["google_drive"]["status"] = "not_configured"
            health_status["services"]["google_drive"]["error"] = "No credentials configured"

    except Exception as e:
        health_status["services"]["google_drive"]["status"] = "error"
        health_status["services"]["google_drive"]["error"] = str(e)[:100]

    # --- vMix health check ---
    try:
        from api_config import APIConfigManager
        api_mgr = APIConfigManager()
        vmix_cfg = api_mgr.get_service_config("production", "control", "vmix") or {}
        vmix_host = vmix_cfg.get("host", "")
        vmix_port = vmix_cfg.get("port", "8088")
        vmix_enabled = vmix_cfg.get("enabled", False)

        if vmix_host and vmix_enabled:
            vmix_url = f"http://{vmix_host}:{vmix_port}/api"
            health_status["services"]["vmix"]["host"] = f"{vmix_host}:{vmix_port}"
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(vmix_url)
                    if response.status_code == 200:
                        health_status["services"]["vmix"]["status"] = "connected"
                        health_status["services"]["vmix"]["connected"] = True
                    else:
                        health_status["services"]["vmix"]["status"] = "warning"
                        health_status["services"]["vmix"]["error"] = f"HTTP {response.status_code}"
            except httpx.ConnectError:
                health_status["services"]["vmix"]["status"] = "error"
                health_status["services"]["vmix"]["error"] = "Connection refused"
            except httpx.TimeoutException:
                health_status["services"]["vmix"]["status"] = "error"
                health_status["services"]["vmix"]["error"] = "Timeout"
            except Exception as e:
                health_status["services"]["vmix"]["status"] = "error"
                health_status["services"]["vmix"]["error"] = str(e)[:50]
        elif vmix_host and not vmix_enabled:
            health_status["services"]["vmix"]["status"] = "disabled"
            health_status["services"]["vmix"]["host"] = f"{vmix_host}:{vmix_port}"
        else:
            health_status["services"]["vmix"]["status"] = "not_configured"
    except Exception as e:
        health_status["services"]["vmix"]["status"] = "error"
        health_status["services"]["vmix"]["error"] = str(e)[:50]

    # Test Whisper STT connectivity
    try:
        from api_config import APIConfigManager
        whisper_mgr = APIConfigManager()
        whisper_cfg = whisper_mgr.get_service_config("preproduction", "ai_services", "whisper") or {}
        whisper_host = whisper_cfg.get("host", "")
        whisper_enabled = whisper_cfg.get("enabled", False)

        if whisper_host and whisper_enabled:
            health_status["services"]["whisper"]["host"] = whisper_host
            endpoint = whisper_cfg.get("endpoint", "/v1/audio/transcriptions")
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    try:
                        resp = await client.get(f"{whisper_host}/health")
                        if resp.status_code < 500:
                            health_status["services"]["whisper"]["status"] = "connected"
                            health_status["services"]["whisper"]["connected"] = True
                        else:
                            health_status["services"]["whisper"]["status"] = "error"
                            health_status["services"]["whisper"]["error"] = f"HTTP {resp.status_code}"
                    except (httpx.ConnectError, httpx.TimeoutException):
                        resp = await client.get(f"{whisper_host}{endpoint}")
                        if resp.status_code < 500:
                            health_status["services"]["whisper"]["status"] = "connected"
                            health_status["services"]["whisper"]["connected"] = True
                        else:
                            health_status["services"]["whisper"]["status"] = "error"
                            health_status["services"]["whisper"]["error"] = f"HTTP {resp.status_code}"
            except httpx.ConnectError:
                health_status["services"]["whisper"]["status"] = "error"
                health_status["services"]["whisper"]["error"] = "Connection refused"
            except httpx.TimeoutException:
                health_status["services"]["whisper"]["status"] = "error"
                health_status["services"]["whisper"]["error"] = "Timeout"
            except Exception as e:
                health_status["services"]["whisper"]["status"] = "error"
                health_status["services"]["whisper"]["error"] = str(e)[:50]
        elif whisper_host and not whisper_enabled:
            health_status["services"]["whisper"]["status"] = "disabled"
            health_status["services"]["whisper"]["host"] = whisper_host
        else:
            health_status["services"]["whisper"]["status"] = "not_configured"
    except Exception as e:
        health_status["services"]["whisper"]["status"] = "error"
        health_status["services"]["whisper"]["error"] = str(e)[:50]

    # Set overall status based on CRITICAL services only (database)
    if health_status["services"]["database"] not in ["connected", "no_config"]:
        health_status["status"] = "degraded"

    return health_status


@router.get("/health/vmix")
async def get_vmix_health():
    """Dedicated vMix health check endpoint."""
    result = {"connected": False, "status": "not_configured"}
    try:
        from api_config import APIConfigManager
        api_mgr = APIConfigManager()
        vmix_cfg = api_mgr.get_service_config("production", "control", "vmix") or {}
        vmix_host = vmix_cfg.get("host", "")
        vmix_port = vmix_cfg.get("port", "8088")
        vmix_enabled = vmix_cfg.get("enabled", False)

        if vmix_host and vmix_enabled:
            vmix_url = f"http://{vmix_host}:{vmix_port}/api"
            result["host"] = f"{vmix_host}:{vmix_port}"
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(vmix_url)
                    if response.status_code == 200:
                        result["connected"] = True
                        result["status"] = "connected"
                    else:
                        result["error"] = f"HTTP {response.status_code}"
                        result["status"] = "warning"
            except httpx.ConnectError:
                result["error"] = "Connection refused"
                result["status"] = "error"
            except httpx.TimeoutException:
                result["error"] = "Timeout"
                result["status"] = "error"
            except Exception as e:
                result["error"] = str(e)[:100]
                result["status"] = "error"
        elif vmix_host and not vmix_enabled:
            result["status"] = "disabled"
            result["host"] = f"{vmix_host}:{vmix_port}"
            result["error"] = "vMix integration is disabled"
    except Exception as e:
        result["error"] = str(e)[:100]
        result["status"] = "error"
    return result


@router.get("/version")
async def get_version():
    """Get server version information for worker update polling."""
    version_info = {
        "version": "dev-v2.01.00",
        "git_commit": None,
        "git_branch": None,
        "git_date": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "key_files": {}
    }

    try:
        app_dir = Path("/app") if Path("/app").exists() else Path(".")

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=app_dir, timeout=5
        )
        if result.returncode == 0:
            version_info["git_commit"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=app_dir, timeout=5
        )
        if result.returncode == 0:
            version_info["git_branch"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, cwd=app_dir, timeout=5
        )
        if result.returncode == 0:
            version_info["git_date"] = result.stdout.strip()
    except Exception:
        pass

    key_files = [
        "services/ffmpeg_tasks.py",
        "platform_utils.py",
        "celery_app.py",
        "models_v2.py"
    ]

    for file_path in key_files:
        try:
            full_path = Path("/app") / file_path
            if not full_path.exists():
                full_path = Path("app") / file_path

            if full_path.exists():
                with open(full_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                version_info["key_files"][file_path] = file_hash
        except Exception:
            version_info["key_files"][file_path] = "error"

    return version_info
