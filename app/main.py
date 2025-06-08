# main.py

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from preproc_mqtt_pub import publish_message
from preproc_mqtt_listen import MQTTListener
from pydantic import BaseModel
from utils.id import get_next_id
from utils.validator import validate_front_matter
import logging
import hashlib
import os
import threading
import re
import yaml

app = FastAPI()

listener = MQTTListener()

@app.on_event("startup")
def startup_event():
    threading.Thread(target=listener.start, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

class PublishRequest(BaseModel):
    topic: str
    message: str

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

