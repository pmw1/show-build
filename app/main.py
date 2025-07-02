# main.py

from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from preproc_mqtt_pub import publish_message
from preproc_mqtt_listen import MQTTListener
from pydantic import BaseModel, Field
from typing import Optional
from utils.id import get_next_id
from utils.validator import validate_front_matter
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
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current directory: {os.getcwd()}")
    raise

app = FastAPI()

listener = MQTTListener()

@app.on_event("startup")
def startup_event():
    threading.Thread(target=listener.start, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the auth router
app.include_router(auth_router)

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
    return {"status": "healthy"}

@app.post("/next-id")
async def next_id(slug: str = Form(...), type: str = Form(...)):
    try:
        next_id_value = get_next_id(slug, type)
        return {"id": next_id_value}
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

@app.get("/rundown/{episode_number}")
async def get_rundown(episode_number: str):
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")

    if not os.path.isdir(episode_path):
        raise HTTPException(
            status_code=404, detail=f"Episode {episode_number} not found."
        )

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
                        raise ValueError("Front matter block not properly closed")
                    yaml_block = content[4:fm_end]
                    front_matter = yaml.safe_load(yaml_block)
                else:
                    raise ValueError("No YAML front matter found")

                validated_metadata = validate_front_matter(front_matter, filename=file_name)
                rundown_items.append({"filename": file_name, "metadata": validated_metadata})

            except Exception as e:
                #logging.warning(f"Invalid metadata in {file_name}: {e}")
                pass  ##skipping the warning messages about unvalidated fields for now  uncomment above to re-enable
    return JSONResponse(content=jsonable_encoder(rundown_items))

@app.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(episode_number: str, payload: ReorderRequest):
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")

    if not os.path.isdir(episode_path):
        raise HTTPException(
            status_code=404, detail=f"Episode {episode_number} not found."
        )

    try:
        for index, segment in enumerate(payload.segments):
            filename = segment.get("filename")
            if not filename or not filename.endswith(".md"):
                raise HTTPException(
                    status_code=422, detail=f"Invalid or missing filename in segment {index}"
                )

            file_path = os.path.join(episode_path, filename)
            if not os.path.isfile(file_path):
                raise HTTPException(
                    status_code=404, detail=f"File {filename} not found."
                )

            # Read existing file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                raise HTTPException(
                    status_code=422, detail=f"No YAML frontmatter in {filename}"
                )

            fm_end = content.find("\n---", 4)
            if fm_end == -1:
                raise HTTPException(
                    status_code=422, detail=f"Invalid YAML frontmatter in {filename}"
                )

            yaml_block = content[4:fm_end]
            body = content[fm_end + 4:]
            front_matter = yaml.safe_load(yaml_block) or {}

            # Update order
            front_matter["order"] = (index + 1) * 10

            # Write back to file
            new_yaml = yaml.safe_dump(front_matter, sort_keys=False)
            new_content = f"---\n{new_yaml}---\n{body}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        return {"status": "success", "message": f"Rundown for episode {episode_number} reordered"}

    except Exception as e:
        logging.error(f"Failed to reorder rundown: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reorder rundown: {str(e)}")

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
    safe_title = safe_title.replace(' ', ' ')  # Normalize spaces
    
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

@app.get("/episodes")
async def list_episodes():
    """List all available episode numbers by scanning /home/episodes directory"""
    base_path = "/home/episodes"
    try:
        # Get directories that have a rundown subdirectory
        episodes = [
            d for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d)) and
               os.path.isdir(os.path.join(base_path, d, "rundown")) and
               re.match(r'^\d{4}$', d)  # Must be 4 digits
        ]
        return sorted(episodes)  # Return sorted list of valid episode numbers
    except Exception as e:
        logging.error(f"Failed to list episodes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list episodes: {str(e)}"
        )

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
