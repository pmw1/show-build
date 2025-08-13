# main.py

from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from preproc_mqtt_pub import publish_message
from preproc_mqtt_listen import MQTTListener
from pydantic import BaseModel, Field
from typing import Optional
from utils.id import get_next_id
from utils.frontmatter_parser import parse_markdown_file
from auth.utils import get_current_user_or_key, get_current_user  # Add get_current_user
import logging
import hashlib
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
from models import ProcessingJob  # Keep only non-conflicting legacy models
from models_episode import BlueprintTemplate, BlueprintNode, EpisodeTemplate  
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
    health_status = {"status": "healthy", "database": "unknown"}
    
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
            
            health_status["database"] = "connected"
        else:
            health_status["database"] = "no_config"
            
    except asyncpg.InvalidAuthorizationSpecificationError:
        health_status["database"] = "auth_failed"
    except asyncpg.InvalidCatalogNameError:
        health_status["database"] = "db_not_found"
    except OSError:
        health_status["database"] = "connection_refused"
    except Exception as e:
        health_status["database"] = f"error: {str(e)[:50]}"
    
    # Set overall status based on database
    if health_status["database"] not in ["connected", "no_config"]:
        health_status["status"] = "degraded"
    
    return health_status

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
async def list_episodes():
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

        if os.path.exists(info_path):
            metadata = None  # Ensure metadata is reset for each episode
            try:
                metadata, _ = parse_markdown_file(info_path)
                
                # Defensive check: ensure metadata is a dictionary
                if metadata and isinstance(metadata, dict):
                    title = metadata.get("title", title)
                    airdate = metadata.get("airdate")
                    status = metadata.get("status", "unknown")
                elif metadata:
                    # Log if metadata is not a dictionary, to debug the 'tuple' error
                    logging.warning(f"Metadata for episode {item} is not a dictionary. Type: {type(metadata)}. Data: {metadata}")

            except Exception as e:
                # This will catch errors during parsing or attribute access
                logging.warning(f"Could not process info.md for episode {item}: {e}")
        
        episodes.append({
            "episode_number": item, 
            "title": title, 
            "airdate": airdate,
            "status": status
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
async def list_episodes():
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

        if os.path.exists(info_path):
            metadata = None  # Ensure metadata is reset for each episode
            try:
                metadata, _ = parse_markdown_file(info_path)
                
                # Defensive check: ensure metadata is a dictionary
                if metadata and isinstance(metadata, dict):
                    title = metadata.get("title", title)
                    airdate = metadata.get("airdate")
                    status = metadata.get("status", "unknown")
                elif metadata:
                    # Log if metadata is not a dictionary, to debug the 'tuple' error
                    logging.warning(f"Metadata for episode {item} is not a dictionary. Type: {type(metadata)}. Data: {metadata}")

            except Exception as e:
                # This will catch errors during parsing or attribute access
                logging.warning(f"Could not process info.md for episode {item}: {e}")
        
        episodes.append({
            "episode_number": item, 
            "title": title, 
            "airdate": airdate,
            "status": status
        })
            
    if not episodes:
        logging.warning(f"No valid episodes found in {base_path}")

    return {"episodes": episodes}

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

@app.put("/episodes/{episode_number}/info")
async def update_episode_info(episode_number: str, info_data: dict, current_user: dict = Depends(get_current_user_or_key)):
    """Update episode information in info.md file"""
    base_path = "/home/episodes"
    info_path = os.path.join(base_path, episode_number, "info.md")
    
    try:
        # Read existing content to preserve body
        existing_body = ""
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    existing_body = parts[2].strip()
        
        # Create new content with updated frontmatter
        frontmatter_yaml = yaml.dump(info_data, default_flow_style=False, allow_unicode=True)
        new_content = f"---\n{frontmatter_yaml}---\n{existing_body}"
        
        # Write back to file
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "message": f"Episode {episode_number} info updated successfully",
            "episode_number": episode_number,
            "info": info_data
        }
        
    except Exception as e:
        logging.error(f"Failed to update episode info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update episode info: {str(e)}"
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
        from models import ProcessingStatus
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
