# main.py

from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from preproc_mqtt_pub import publish_message
from preproc_mqtt_listen import MQTTListener
from pydantic import BaseModel, Field
from typing import Optional
from utils.id import get_next_id
from utils.frontmatter_parser import parse_markdown_file
from auth.utils import get_current_user_or_key, get_current_user  # Add get_current_user
import logging
import httpx
import hashlib

# Initialize logger
logger = logging.getLogger(__name__)
import os
import sys
import threading  # Add this import
import re
import yaml  # Add yaml import for debug endpoint
import random  # Add random import for asset ID generation
from pathlib import Path
from glob import glob
import markdown
import traceback
from enhanced_reorder import reorder_rundown_with_rename

# Database and background processing imports
from database import engine, Base, get_db
from sqlalchemy.orm import Session
# from models import ProcessingJob  # REMOVED - models.py deleted
from models_episode import BlueprintTemplate, BlueprintNode, Blueprint  
from models_assetid import AssetIDRegistry, AssetIDRelationship, AssetIDPendingMessage
from models_v2 import Organization, Show, Season, Episode, Break, Rundown, RundownItem, Segment, Script, Element, Cue, AssetLink, AssetMessage
from services.script_compilation import compile_episode_script
from websocket import websocket_endpoint, manager
from celery_app import celery_app

# Absolute path to the app directory
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

print(f"Python path: {sys.path}")
print(f"App directory: {APP_DIR}")
print(f"Directory contents: {os.listdir(APP_DIR)}")
print(f"Auth directory contents: {os.listdir(APP_DIR / 'auth')}")

# Now try importing the auth module
try:
    from auth.router import router as auth_router
    from api_config_router import router as api_config_router
    from assets_router import router as assets_router
    from templates_router import router as templates_router
    from docs_router import router as docs_router
    from assetid_router import router as assetid_router
    from organization_router import router as organization_router
    from show_router import router as show_router
    from media_router import router as media_router
    from settings_router import router as settings_router
    from settings_colors_router import router as settings_colors_router
    from episodes_router import router as episodes_router
    from episode_scaffold_router import router as episode_scaffold_router
    from setup_router import router as setup_router
    from rbac_router import router as rbac_router
    from duration_analysis_router import router as duration_router
    from new_assetid_router import router as new_assetid_router
    from convert_assetid_router import router as convert_assetid_router
    from duration_estimation_router import router as duration_estimation_router
    from fsq_asset_router import router as fsq_asset_router
    from speakers_router import router as speakers_router
    from voice_sample_router import router as voice_sample_router
    from wpm_audio_router import router as wpm_audio_router
    from voice_model_router import router as voice_model_router
    from xtts_router import router as xtts_router
    from housekeeping_router import router as housekeeping_router
    from sot_router import router as sot_router
    from llm_proxy_router import router as llm_proxy_router
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current directory: {os.getcwd()}")
    raise

app = FastAPI()

listener = MQTTListener()

@app.on_event("startup")
def startup_event():
    """Initialize database and start background services."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Start MQTT listener
    threading.Thread(target=listener.start, daemon=True).start()
    
    logging.info("Show-Build server started with database and background processing")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for episode assets (images, etc.)
app.mount("/episodes", StaticFiles(directory="/home/episodes"), name="episodes")

# Include the auth router with /api prefix
app.include_router(auth_router, prefix="/api")

# Include the API configuration router
app.include_router(api_config_router)

# Include the assets router
app.include_router(assets_router, prefix="/api", tags=["assets"])

# Include the templates router
app.include_router(templates_router, prefix="/api", tags=["templates"])

# Include the documentation router
app.include_router(docs_router)

# Include the enhanced AssetID router
app.include_router(assetid_router)

# Include the organization router
app.include_router(organization_router, prefix="/api")

# Include the show router
app.include_router(show_router, prefix="/api")

# Include the media router
app.include_router(media_router, prefix="/api")

# Include the settings router 
app.include_router(settings_router, prefix="/api")
# Include the database-based color settings router
app.include_router(settings_colors_router)

# Include the episodes router
app.include_router(episodes_router, prefix="/api")

# Include the episode scaffolding router
app.include_router(episode_scaffold_router, prefix="/api")

# Include the setup router
app.include_router(setup_router, prefix="/api")

# Include the RBAC router
app.include_router(rbac_router, prefix="/api")

# Include the duration analysis router
app.include_router(duration_router)
# Include the unified new AssetID router
app.include_router(new_assetid_router)

# Include the AssetID conversion router
app.include_router(convert_assetid_router, prefix="/api")

# Include the duration estimation router
app.include_router(duration_estimation_router, prefix="/api")

# Include the FSQ asset generation router
app.include_router(fsq_asset_router, prefix="/api/fsq", tags=["fsq"])

# Include the Speakers router
app.include_router(speakers_router)

# Include the Voice Sample router
app.include_router(voice_sample_router)

# Include the WPM Audio Analysis router
app.include_router(wpm_audio_router)

# Include the Voice Model Training router
app.include_router(voice_model_router)

# Include the XTTS status router
app.include_router(xtts_router)

# Include housekeeping router
app.include_router(housekeeping_router, prefix="/api")

# Include SOT processing router
app.include_router(sot_router)

# Include LLM proxy router (for mixed content avoidance)
app.include_router(llm_proxy_router)

# Include the media analysis router
from media_analysis_router import router as media_analysis_router
app.include_router(media_analysis_router)

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

class PublishRequest(BaseModel):
    topic: str
    message: str

class ReorderRequest(BaseModel):
    segments: list[dict]

class NewRundownItem(BaseModel):
    title: str = Field(..., description="Title of the rundown item")
    type: str = Field(..., description="Type of rundown item (segment, promo, advert, etc.)")
    slug: str = Field(..., description="Short slug for the item")
    duration: Optional[str] = Field("00:00:30", description="Estimated duration")
    description: Optional[str] = Field("", description="Description of the item")
    priority: Optional[str] = Field("", description="Priority level")
    guests: Optional[str] = Field("", description="Guests for this item")
    tags: Optional[str] = Field("", description="Tags for this item")

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
      <head>
        <title>Show Builder API</title>
        <style>
          body { font-family: sans-serif; margin: 2em; }
          code { background: #f0f0f0; padding: 2px 4px; border-radius: 4px; }
          h2 { margin-top: 1.5em; }
        </style>
      </head>
      <body>
        <h1>🎬 Show Builder API</h1>
        <p>This server powers the Disaffected Rundown Builder. Here are the available endpoints:</p>

        <h2>GET <code>/health</code></h2>
        <p>Returns basic server status.</p>

        <h2>GET <code>/rundown/{episode_number}</code></h2>
        <p>Fetch rundown items with validated front matter metadata.</p>

        <h2>POST <code>/rundown/{episode_number}/reorder</code></h2>
        <p>Reorder segments by updating <code>order:</code> in YAML frontmatter.</p>

        <h2>POST <code>/publish/</code></h2>
        <p>Send a raw MQTT message.</p>

        <h2>GET <code>/listen/?topic=xyz</code></h2>
        <p>Subscribe to an MQTT topic and stream responses.</p>

        <h2>POST <code>/next-id</code></h2>
        <p>Generates the next unique ID. Requires form fields <code>slug</code> and <code>type</code>.</p>

        <h2>POST <code>/proc_vid</code></h2>
        <p>Upload a video file for processing. Accepts multipart form fields: <code>file</code>, <code>type</code>, <code>id</code>, <code>episode</code>, <code>slug</code>, and optional <code>trim_start</code>/<code>trim_end</code>.</p>
      </body>
    </html>
    """

@app.post("/publish/")
async def publish_endpoint(payload: PublishRequest):
    try:
        result = publish_message(payload.topic, payload.message)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to publish message")
        return {
            "topic": payload.topic,
            "message": payload.message,
            "status": "published",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/listen/")
async def listen_endpoint(topic: str):
    try:
        listener.subscribe_to_topic(topic)
        return {"topic": topic, "status": "listening"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    from datetime import datetime
    import httpx

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
            "xtts": {
                "status": "unknown",
                "connected": False,
                "quota_remaining": None,
                "error": None
            }
        }
    }

    # Test database connectivity
    try:
        from pathlib import Path
        import json
        import asyncpg

        # Load database config if it exists
        config_dir = Path("/app/config") if Path("/app").exists() else Path("app/config")
        db_config_file = config_dir / "database.json"

        if db_config_file.exists():
            with open(db_config_file, 'r') as f:
                db_config = json.load(f)

            # Test connection
            conn = await asyncpg.connect(
                host=db_config.get("host", "postgres"),
                port=db_config.get("port", 5432),
                database=db_config.get("database", "showbuild"),
                user=db_config.get("username", "showbuild"),
                password=db_config.get("password", "showbuild")
            )

            # Simple connectivity test
            await conn.fetchval("SELECT 1")
            await conn.close()

            health_status["services"]["database"] = "connected"
        else:
            health_status["services"]["database"] = "no_config"

    except asyncpg.InvalidAuthorizationSpecificationError:
        health_status["services"]["database"] = "auth_failed"
    except asyncpg.InvalidCatalogNameError:
        health_status["services"]["database"] = "db_not_found"
    except OSError:
        health_status["services"]["database"] = "connection_refused"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)[:50]}"

    # Test Ollama connectivity (load from database)
    try:
        from sqlalchemy import text
        from database import SessionLocal

        with SessionLocal() as db:
            # Query Ollama config from database
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

                    # Ping Ollama API (1s timeout for health check speed)
                    async with httpx.AsyncClient(timeout=1.0) as client:
                        response = await client.get(f"{ollama_host}/api/tags")
                        if response.status_code == 200:
                            health_status["services"]["ollama"]["status"] = "connected"
                        else:
                            health_status["services"]["ollama"]["status"] = f"error: HTTP {response.status_code}"
                else:
                    # Ollama not enabled - remove from status
                    health_status["services"].pop("ollama", None)
            else:
                # No Ollama config in database - remove from status
                health_status["services"].pop("ollama", None)

    except httpx.TimeoutException:
        health_status["services"]["ollama"]["status"] = "timeout"
    except httpx.ConnectError:
        health_status["services"]["ollama"]["status"] = "connection_refused"
    except Exception as e:
        # Config error - remove from status
        health_status["services"].pop("ollama", None)

    # Test Redis connectivity
    try:
        import redis
        import time

        # Get Redis URL from environment
        redis_url = os.getenv("REDIS_URL", "redis://192.168.51.223:6379/0")
        redis_password = os.getenv("REDIS_PASSWORD", "showbuild2025")

        # Parse Redis URL (handle password in URL like redis://:password@host:port/db)
        if redis_url.startswith("redis://"):
            # Remove redis:// prefix
            url_part = redis_url.replace("redis://", "")

            # Check for password in URL (format: :password@host:port/db)
            if "@" in url_part:
                _, host_port = url_part.split("@", 1)
            else:
                host_port = url_part

            # Split host:port/db
            redis_host = host_port.split(":")[0]
            port_and_db = host_port.split(":")[1] if ":" in host_port else "6379/0"
            redis_port = int(port_and_db.split("/")[0])
        else:
            redis_host = "192.168.51.223"
            redis_port = 6379

        # Connect to Redis with reduced timeout for faster health checks
        start_time = time.time()
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            socket_connect_timeout=1,
            socket_timeout=1,
            db=0
        )

        # Ping Redis
        r.ping()
        latency_ms = int((time.time() - start_time) * 1000)

        health_status["services"]["redis"]["status"] = "connected"
        health_status["services"]["redis"]["connected"] = True
        health_status["services"]["redis"]["latency"] = latency_ms

    except redis.ConnectionError as e:
        health_status["services"]["redis"]["status"] = "error"
        health_status["services"]["redis"]["error"] = "Connection refused"
    except redis.TimeoutError:
        health_status["services"]["redis"]["status"] = "error"
        health_status["services"]["redis"]["error"] = "Timeout"
    except Exception as e:
        health_status["services"]["redis"]["status"] = "error"
        health_status["services"]["redis"]["error"] = str(e)[:50]

    # Test Celery worker connectivity
    try:
        from celery_app import celery_app

        # Get active workers (reduced timeout for faster health checks)
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
    # Note: Container has /home/episodes mounted from /mnt/sync/disaffected/episodes
    # We check accessibility of the mounted directories, not the NFS mount itself
    try:
        from pathlib import Path

        # Check if episodes directory is accessible (via NFS or local mount)
        episodes_dir = Path("/home/episodes")

        if episodes_dir.exists():
            try:
                # Test read
                list(episodes_dir.iterdir())

                # Test write in shared_media location
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

    # Test XTTS connectivity
    try:
        from pathlib import Path
        import json
        from api_config import api_config_manager

        # Load XTTS configuration
        xtts_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="xtts"
        )

        if not xtts_config:
            # XTTS not configured - show as error
            health_status["services"]["xtts"] = {
                "status": "error",
                "connected": False,
                "error": "Not configured"
            }
        elif not xtts_config.get("enabled"):
            # XTTS disabled in config - show as error
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
                # Test XTTS connectivity using /health endpoint (1s timeout)
                async with httpx.AsyncClient(timeout=1.0) as client:
                    response = await client.get(f"{host}/health")
                    if response.status_code == 200:
                        data = response.json()
                        # Check if service is healthy and model is loaded
                        is_healthy = data.get("status") == "healthy"
                        model_loaded = data.get("model_loaded", False)

                        if is_healthy and model_loaded:
                            health_status["services"]["xtts"] = {
                                "status": "connected",
                                "connected": True,
                                "quota_remaining": None  # XTTS doesn't have quota
                            }
                        else:
                            health_status["services"]["xtts"] = {
                                "status": "error",
                                "connected": False,
                                "error": f"Unhealthy or model not loaded"
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
        # Show error status instead of hiding XTTS
        health_status["services"]["xtts"] = {
            "status": "error",
            "connected": False,
            "error": f"Error: {str(e)[:30]}"
        }

    # Set overall status based on CRITICAL services only (database)
    # Ollama is non-critical - it has its own status indicator
    if health_status["services"]["database"] not in ["connected", "no_config"]:
        health_status["status"] = "degraded"

    return health_status

@app.get("/api/llm/ollama/models")
async def get_ollama_models(current_user: dict = Depends(get_current_user_or_key)):
    """Get list of available Ollama models"""
    try:
        from api_config import api_config_manager

        # Load Ollama config
        ollama_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="ollama"
        )

        if not ollama_config or not ollama_config.get("host"):
            return {"models": []}

        ollama_host = ollama_config.get("host")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "models": [{"name": m["name"], "size": m.get("size")} for m in models]
                }

        return {"models": []}
    except Exception as e:
        logger.error(f"Failed to fetch Ollama models: {e}")
        return {"models": []}

@app.get("/show-info")
async def get_show_info():
    """
    Returns basic information about the show.
    For now, it's hardcoded, but could be read from a config file.
    """
    return {
        "show_title": "Disaffected",
        "show_description": "A show about current events and technology.",
        "episodes_base_path": "/home/episodes"
    }

@app.get("/episodes")
async def list_episodes(db: Session = Depends(get_db)):
    """
    Lists all available episodes by scanning the /home/episodes directory.
    An episode is considered a directory with a 'rundown' subdirectory.
    """
    base_path = "/home/episodes"
    if not os.path.isdir(base_path):
        logging.error(f"Episodes base path not found: {base_path}")
        raise HTTPException(status_code=500, detail="Episodes directory not configured.")

    episodes = []
    for item in sorted(os.listdir(base_path), reverse=True):
        episode_path = os.path.join(base_path, item)
        if not os.path.isdir(episode_path):
            continue

        # We no longer require a 'rundown' subdirectory to list an episode
        info_path = os.path.join(episode_path, "info.md")
        
        # Default values
        title = f"Episode {item}"
        airdate = None
        status = "unknown"
        asset_id = None

        if os.path.exists(info_path):
            metadata = None  # Ensure metadata is reset for each episode
            try:
                metadata, _ = parse_markdown_file(info_path)
                
                # Defensive check: ensure metadata is a dictionary
                if metadata and isinstance(metadata, dict):
                    title = metadata.get("title", title)
                    airdate = metadata.get("airdate")
                    status = metadata.get("status", "unknown")
                    asset_id = metadata.get("AssetID")
                elif metadata:
                    # Log if metadata is not a dictionary, to debug the 'tuple' error
                    logging.warning(f"Metadata for episode {item} is not a dictionary. Type: {type(metadata)}. Data: {metadata}")

            except Exception as e:
                # This will catch errors during parsing or attribute access
                logging.warning(f"Could not process info.md for episode {item}: {e}")
        
        # If no AssetID in filesystem, check database
        if not asset_id:
            try:
                from models_v2 import Episode
                # Convert string episode number to int for database query
                try:
                    episode_num_int = int(item.lstrip('0')) if item.isdigit() else None
                    if episode_num_int:
                        episode_record = db.query(Episode).filter(Episode.episode_number == episode_num_int).first()
                    else:
                        episode_record = None
                except ValueError:
                    episode_record = None
                if episode_record and episode_record.asset_id:
                    asset_id = episode_record.asset_id
            except Exception as e:
                logging.warning(f"Could not query database for episode {item} AssetID: {e}")

        episodes.append({
            "episode_number": item,
            "title": title,
            "airdate": airdate,
            "status": status,
            "asset_id": asset_id
        })
            
    if not episodes:
        logging.warning(f"No valid episodes found in {base_path}")

    return {"episodes": episodes}

@app.post("/next-id")
async def next_id_legacy_redirect(slug: str = Form(...), type: str = Form(...)):
    """
    DEPRECATED: Use /assetid/generate-legacy instead.
    This endpoint redirects to the new AssetID service for backwards compatibility.
    """
    from fastapi.responses import RedirectResponse
    
    # Log deprecation warning
    logging.warning(f"DEPRECATED: /next-id endpoint used. Migrate to /assetid/generate-legacy")
    
    # For now, keep the old functionality but encourage migration
    try:
        from utils.id import get_next_id
        next_id_value = get_next_id(slug, type)
        return {
            "id": next_id_value,
            "deprecated": True,
            "message": "This endpoint is deprecated. Use /assetid/generate-legacy instead.",
            "migration_url": "/assetid/generate-legacy"
        }
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logging.error(f"Failed to generate ID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/generate_asset_id/rundown")
async def generate_rundown_asset_id(
    type: str = Form(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Generate AssetID for rundown items - Obsidian plugin compatibility endpoint.
    """
    try:
        from services.asset_id import AssetIDService
        
        # Generate AssetID with full tracking
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="rundown",
            reason="create",
            requested_by=current_user.get("username", current_user.get("client_name", "obsidian_plugin")),
            context={
                "source": "obsidian_plugin",
                "legacy_type": type
            }
        )
        
        return {"asset_id": asset_id}
        
    except Exception as e:
        logging.error(f"Failed to generate rundown AssetID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate AssetID: {str(e)}")

@app.post("/generate_asset_id/cue")
async def generate_cue_asset_id(
    type: str = Form(...),  # SOT, GFX, FSQ
    media_url: str = Form(None),
    cue_type: str = Form(None),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Generate AssetID for cue blocks - Obsidian plugin compatibility endpoint.
    """
    try:
        from services.asset_id import AssetIDService
        
        # Build context with cue-specific information
        context = {
            "source": "obsidian_plugin",
            "cue_type": type,
            "legacy_type": type
        }
        
        if media_url:
            context["media_url"] = media_url
        if cue_type:
            context["specific_cue_type"] = cue_type
        
        # Generate AssetID with full tracking
        asset_id = AssetIDService.request_asset_id(
            db=db,
            entity_type="cue",
            reason="create",
            requested_by=current_user.get("username", current_user.get("client_name", "obsidian_plugin")),
            context=context
        )
        
        return {"asset_id": asset_id}
        
    except Exception as e:
        logging.error(f"Failed to generate cue AssetID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate AssetID: {str(e)}")

@app.post("/proc_vid")
async def upload(
    file: UploadFile = File(..., alias="file"),
    type: str = Form(..., alias="type"),
    id: str = Form(..., alias="id"),
    episode: str = Form(..., alias="episode"),
    slug: str = Form(..., alias="slug"),
    trim_start: str = Form(default=None),
    trim_end: str = Form(default=None),
):
    if not file:
        raise HTTPException(status_code=400, detail="File is required")

    file_content = await file.read()

    if not file_content:
        raise HTTPException(status_code=422, detail="File content is empty")

    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv")):
        raise HTTPException(status_code=422, detail="File must be mp4, mov, or mkv")

    md5_hash = hashlib.md5(file_content).hexdigest()
    work_dir = f"/shared_media/preproc/working/{id}"
    os.makedirs(work_dir, exist_ok=True)
    filepath = os.path.join(work_dir, file.filename)

    try:
        with open(filepath, "wb") as f:
            f.write(file_content)

        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, detail=f"File size exceeds {MAX_FILE_SIZE_MB} MB."
            )

        logging.info(f"File successfully saved: {filepath}, MD5: {md5_hash}")
        return {"status": "file uploaded", "filepath": filepath, "md5": md5_hash}

    except Exception as e:
        logging.error(f"Failed to save file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

@app.post("/upload_image")
async def upload_image(
    file: UploadFile = File(..., alias="file"),
    id: str = Form(..., alias="id"),
    episode: str = Form(..., alias="episode"),
    slug: str = Form(..., alias="slug"),
):
    """
    Upload an image file for processing.

    Args:
        file (UploadFile): The image file to upload.
        id (str): Unique identifier for the asset.
        episode (str): Episode identifier.
        slug (str): Slug for naming convention.

    Returns:
        dict: Status, file path, and asset ID.
    """
    if not file:
        raise HTTPException(status_code=400, detail="File is required")

    file_content = await file.read()

    if not file_content:
        raise HTTPException(status_code=422, detail="File content is empty")

    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        raise HTTPException(status_code=422, detail="File must be an image (png, jpg, jpeg, gif)")

    md5_hash = hashlib.md5(file_content).hexdigest()
    work_dir = f"/shared_media/images/{id}"
    os.makedirs(work_dir, exist_ok=True)
    filepath = os.path.join(work_dir, file.filename)

    try:
        with open(filepath, "wb") as f:
            f.write(file_content)

        logging.info(f"Image successfully saved: {filepath}, MD5: {md5_hash}")
        return {"status": "image uploaded", "filepath": filepath, "md5": md5_hash}

    except Exception as e:
        logging.error(f"Failed to save image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/upload/image")
async def upload_img_cue_image(
    file: UploadFile = File(...),
    filename: str = Form(...),
    episode: str = Form(...)
):
    """
    Upload an image file for IMG cue blocks to episode assets/images directory.

    Args:
        file (UploadFile): The image file to upload.
        filename (str): The normalized filename (slug-based with extension).
        episode (str): The episode number for the target directory.

    Returns:
        dict: Status and file information.
    """
    if not file:
        raise HTTPException(status_code=400, detail="File is required")

    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not episode:
        raise HTTPException(status_code=400, detail="Episode number is required")

    file_content = await file.read()

    if not file_content:
        raise HTTPException(status_code=422, detail="File content is empty")

    # Validate image file type
    allowed_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=422,
            detail="File must be an image (png, jpg, jpeg, gif, webp)"
        )

    # Ensure episode is properly formatted (4 digits)
    padded_episode = episode.zfill(4)

    # Create the assets/images directory for the episode
    images_dir = f"/home/episodes/{padded_episode}/assets/images"
    os.makedirs(images_dir, exist_ok=True)

    # Create the full file path
    filepath = os.path.join(images_dir, filename)
    
    try:
        # Write the file
        with open(filepath, "wb") as f:
            f.write(file_content)
        
        # Calculate MD5 for verification
        md5_hash = hashlib.md5(file_content).hexdigest()
        
        logging.info(f"IMG cue image saved: {filepath}, MD5: {md5_hash}")
        
        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "filename": filename,
            "filepath": filepath,
            "md5": md5_hash,
            "size": len(file_content)
        }
        
    except Exception as e:
        logging.error(f"Failed to save IMG cue image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")


@app.get("/rundown/{episode_number}/debug")
async def debug_rundown(episode_number: str):
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")
    
    debug_info = {
        "episode_number": episode_number,
        "episode_path": episode_path,
        "path_exists": os.path.isdir(episode_path),
        "files": [],
        "errors": []
    }
    
    if not os.path.isdir(episode_path):
        debug_info["errors"].append(f"Directory does not exist: {episode_path}")
        return debug_info
    
    # List all files
    all_files = os.listdir(episode_path)
    md_files = [f for f in all_files if f.endswith('.md')]
    
    debug_info["all_files"] = all_files
    debug_info["md_files"] = md_files
    
    # Try to process each .md file
    for file_name in md_files:
        file_path = os.path.join(episode_path, file_name)
        file_info = {
            "filename": file_name,
            "status": "unknown",
            "error": None,
            "has_frontmatter": False,
            "frontmatter_preview": None
        }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            file_info["file_size"] = len(content)
            file_info["starts_with_yaml"] = content.startswith("---")
            
            if content.startswith("---"):
                file_info["has_frontmatter"] = True
                fm_end = content.find("\n---", 4)
                if fm_end == -1:
                    file_info["error"] = "Front matter block not properly closed"
                    file_info["status"] = "error"
                else:
                    yaml_block = content[4:fm_end]
                    file_info["frontmatter_preview"] = yaml_block[:200] + "..." if len(yaml_block) > 200 else yaml_block
                    
                    try:
                        front_matter = yaml.safe_load(yaml_block)
                        file_info["parsed_yaml"] = True
                        
                        try:
                            validated_metadata = validate_front_matter(front_matter, filename=file_name)
                            file_info["status"] = "valid"
                            file_info["metadata_keys"] = list(validated_metadata.keys()) if validated_metadata else []
                        except Exception as ve:
                            file_info["status"] = "validation_error"
                            file_info["error"] = str(ve)
                            
                    except Exception as ye:
                        file_info["status"] = "yaml_error"
                        file_info["error"] = f"YAML parsing error: {str(ye)}"
            else:
                file_info["error"] = "No YAML front matter found"
                file_info["status"] = "no_frontmatter"
                
        except Exception as e:
            file_info["status"] = "file_error"
            file_info["error"] = f"File reading error: {str(e)}"
        
        debug_info["files"].append(file_info)
    
    return debug_info

@app.get("/episodes/{episode_number}/rundown")
async def get_episode_rundown(episode_number: str):
    """Provides rundown items in a format expected by the frontend.
    Flattens the metadata into the main item object.
    """
    base_path = os.getenv("EPISODE_ROOT", "/home/episodes")
    print(f"[DEBUG] get_episode_rundown: base_path={base_path}, episode_number={episode_number}")
    episode_path = os.path.join(base_path, episode_number, "rundown")

    if not os.path.isdir(episode_path):
        error_msg = f"Episode path not found: {episode_path}"
        print(f"[ERROR] {error_msg}")
        # Raise for full traceback
        raise Exception(error_msg)

    rundown_items = []
    for file_name in sorted(os.listdir(episode_path)):
        if file_name.endswith(".md"):
            file_path = os.path.join(episode_path, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if content.startswith("---"):
                    fm_end = content.find("\n---", 4)
                    if fm_end == -1:
                        continue # Skip malformed files
                    yaml_block = content[4:fm_end]
                    front_matter = yaml.safe_load(yaml_block)
                    script_content = content[fm_end + 4:].strip()
                else:
                    continue # Skip files without frontmatter

                # Flatten the structure directly from front_matter
                item = {
                    "id": front_matter.get('id', file_name.replace('.md', '')),
                    "type": front_matter.get('type', 'segment'),
                    "slug": front_matter.get('slug', file_name.replace('.md', '').lower()),
                    "duration": front_matter.get('duration', '00:00:00'),
                    "script": script_content,
                    **front_matter # Include all other metadata fields
                }
                rundown_items.append(item)

            except Exception as e:
                logging.warning(f"Skipping invalid file {file_name} in rundown: {e}")
                pass
    
    return {"items": rundown_items}


@app.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(episode_number: str, payload: ReorderRequest):
    """Reorder rundown items and rename files to match their new order."""
    return await reorder_rundown_with_rename(episode_number, payload.dict())

@app.post("/rundown/{episode_number}/item")
async def create_rundown_item(episode_number: str, item: NewRundownItem):
    """Create a new rundown item for the specified episode"""
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")

    if not os.path.isdir(episode_path):
        raise HTTPException(
            status_code=404, detail=f"Episode {episode_number} not found."
        )

    # Generate a unique asset ID
    asset_id = f"{random.randint(10000, 99999)}"
    
    # Create a safe filename from the title
    safe_title = "".join(c for c in item.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '-') # Normalize spaces
    
    # Get the next order number
    existing_files = [f for f in os.listdir(episode_path) if f.endswith('.md')]
    max_order = 0
    for filename in existing_files:
        try:
            # Extract order from filename (assumes format like "20 Title.md")
            parts = filename.split(' ', 1)
            if parts[0].isdigit():
                max_order = max(max_order, int(parts[0]))
        except:
            pass
    
    next_order = max_order + 10
    
    # Create filename
    filename = f"{next_order:02d} {safe_title}.md"
    file_path = os.path.join(episode_path, filename)
    
    # Ensure filename is unique
    counter = 1
    while os.path.exists(file_path):
        filename = f"{next_order:02d} {safe_title} ({counter}).md"
        file_path = os.path.join(episode_path, filename)
        counter += 1
    
    # Create the file content
    content = f"""---
id: '{asset_id}'
slug: {item.slug}
type: {item.type}
order: {next_order}
duration: {item.duration}
status: draft
title: {item.title}
subtitle: null
description: {item.description or 'null'}
airdate: null
priority: '{item.priority}'
guests: {item.guests or 'null'}
resources: ''
tags: {item.tags or 'null'}
server_message: ''
---

## Notes

## Description

{item.description or 'Add description here...'}

## Script

Add script content here...
"""

    try:
        # Write the new file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "asset_id": asset_id,
            "order": next_order,
            "message": f"Created new rundown item: {filename}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create rundown item: {str(e)}"
        )

@app.get("/show-info")
@app.get("/api/show-info")
async def get_show_info():
    """
    Returns basic information about the show.
    For now, it's hardcoded, but could be read from a config file.
    """
    return {
        "show_title": "Disaffected",
        "show_description": "A show about current events and technology.",
        "episodes_base_path": "/home/episodes"
    }

@app.post("/api/logs/client-event")
async def log_client_event(event_data: dict):
    """
    Log client-side events for monitoring and analytics (mandatory)
    """
    logger = logging.getLogger("client_events")

    # Extract event details
    event_type = event_data.get("event", "unknown")
    duration = event_data.get("duration_ms", 0)
    reason = event_data.get("reason", "")
    timestamp = event_data.get("timestamp", "")

    # Log the event
    log_message = f"Client Event: {event_type} | Duration: {duration}ms | Reason: {reason} | Time: {timestamp}"

    if duration > 5000:
        logger.error(log_message)
    elif duration > 2000:
        logger.warning(log_message)
    else:
        logger.info(log_message)

    return {"success": True, "message": "Event logged"}

@app.get("/protected-endpoint")
async def protected_route(current_user: dict = Depends(get_current_user_or_key)):
    return {
        "message": "Access granted to protected endpoint",
        "user": current_user
    }

@app.post("/secured-route")
async def secured_route(
    payload: dict,
    current_user: dict = Depends(get_current_user_or_key)  # Use the combined auth
):
    return {
        "message": "Secured operation successful",
        "user": current_user,
        "data": payload
    }

@app.get("/episodes/{episode_number}/info")
async def get_episode_info(episode_number: str, current_user: dict = Depends(get_current_user_or_key)):
    """Get episode information from info.md file"""
    base_path = "/home/episodes"
    info_path = os.path.join(base_path, episode_number, "info.md")
    
    if not os.path.exists(info_path):
        raise HTTPException(
            status_code=404,
            detail=f"Episode info file not found: {info_path}"
        )
    
    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 2:
                frontmatter_text = parts[1].strip()
                body = parts[2].strip() if len(parts) > 2 else ""
                
                # Parse YAML frontmatter
                frontmatter = yaml.safe_load(frontmatter_text) or {}
                
                return {
                    "episode_number": episode_number,
                    "info": frontmatter,
                    "body": body
                }
        
        # If no frontmatter, return empty info
        return {
            "episode_number": episode_number,
            "info": {},
            "body": content
        }
        
    except Exception as e:
        logging.error(f"Failed to read episode info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read episode info: {str(e)}"
        )


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_connection(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time job status updates."""
    await websocket_endpoint(websocket, client_id)

# Enhanced script compilation endpoint with background processing
@app.post("/episodes/{episode_id}/compile-script")
async def compile_script_async(
    episode_id: str,
    output_format: str = "html",
    include_cues: bool = True,
    validate_only: bool = False,
    current_user: dict = Depends(get_current_user_or_key),
    db = Depends(get_db)
):
    """
    Start script compilation as background job with real-time updates.
    Server handles all heavy processing, client receives WebSocket updates.
    """
    try:
        # Check if episode exists in filesystem
        from core.paths import paths
        if not paths.episode_exists(episode_id):
            raise HTTPException(status_code=404, detail="Episode not found")
        
        # Start background compilation job
        job = compile_episode_script.delay(
            episode_id=episode_id,
            output_format=output_format,
            include_cues=include_cues,
            validate_only=validate_only
        )
        
        # Create database record for job tracking
        # from models import ProcessingStatus  # REMOVED - models.py deleted
        db_job = ProcessingJob(
            job_type="script_compilation",
            job_id=job.id,
            status=ProcessingStatus.PENDING,
            parameters={
                "episode_id": episode_id,
                "output_format": output_format,
                "include_cues": include_cues,
                "validate_only": validate_only
            }
        )
        
        # Find or create episode record
        episode = db.query(Episode).filter(Episode.episode_number == episode_id).first()
        if episode:
            db_job.episode_id = episode.id
        
        db.add(db_job)
        db.commit()
        
        return {
            "job_id": job.id,
            "status": "started",
            "message": f"Script compilation started for episode {episode_id}",
            "websocket_url": f"/ws/{{client_id}}",
            "check_status_url": f"/jobs/{job.id}/status"
        }
        
    except Exception as e:
        logging.error(f"Failed to start script compilation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Job status endpoint
@app.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db = Depends(get_db)
):
    """Get current status of a background processing job."""
    job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get Celery task result
    celery_result = celery_app.AsyncResult(job_id)
    
    return {
        "job_id": job_id,
        "status": job.status,
        "celery_status": celery_result.status,
        "progress": job.progress,
        "job_type": job.job_type,
        "parameters": job.parameters,
        "result": job.result,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }
