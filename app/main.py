# Version: 1.01.00
# Date: June 6, 2025
#### This file now should be living in /mnt/process/show-build/app


from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from preproc_mqtt_pub import publish_message
from preproc_mqtt_listen import MQTTListener
from pydantic import BaseModel
import logging
import hashlib
import os
import threading
import re
from pathlib import Path
import frontmatter
from typing import List
import traceback


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


# Constants
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
LAST_ID_FILE = "/home/logs/last.id"

os.makedirs("/home/logs", exist_ok=True)

if not os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE, "w") as f:
        f.write("0")

logging.basicConfig(
    filename="/home/logs/asset-id.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Helper Functions
def read_last_id():
    with open(LAST_ID_FILE, "r") as f:
        return int(f.read().strip())


def write_last_id(new_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(new_id))


# Pydantic Models
class PublishRequest(BaseModel):
    topic: str
    message: str


class SegmentReorderItem(BaseModel):
    filename: str


####################### Routes


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Server with MQTT integration"}


@app.post("/publish/")
async def publish_endpoint(payload: PublishRequest):
    try:
        print(f"Publishing message to topic {payload.topic}: {payload.message}")
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
    logging.info(f"Received /next-id request: type={type}, slug={slug}")
    if not slug.strip():
        logging.error("Invalid slug: empty or whitespace")
        raise HTTPException(status_code=422, detail="Slug cannot be empty")
    try:
        last_id = read_last_id()
        new_id = last_id + 1
        write_last_id(new_id)
        logging.info(f"Generated new ID: {new_id} for type {type}, slug {slug}")
        return {"id": f"{new_id:05d}"}
    except Exception as e:
        logging.error(f"Failed to generate ID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/preproc_sot")
async def upload(
    file: UploadFile = File(..., alias="file"),
    type: str = Form(..., alias="type"),
    asset_id: str = Form(..., alias="assetID"),
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

    if not file.filename or not file.filename.lower().endswith(
        (".mp4", ".mov", ".mkv")
    ):
        raise HTTPException(status_code=422, detail="File must be mp4, mov, or mkv")

    md5_hash = hashlib.md5(file_content).hexdigest()

    work_dir = f"/shared_media/preproc/working/{asset_id}"
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
    # Construct the path to the episode's rundown directory
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")

    # Check if the directory exists
    if not os.path.isdir(episode_path):
        raise HTTPException(
            status_code=404, detail=f"Episode {episode_number} not found."
        )

    segment_list = []

    # Iterate over all .md files in the rundown directory
    for file_name in sorted(os.listdir(episode_path)):
        if file_name.endswith(".md"):
            file_path = os.path.join(episode_path, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Default values
            slug = None
            item_type = None
            duration = None
            title = file_name  # Fallback title

            # Attempt to extract metadata from cue block
            cue_block_match = re.search(
                r"<<!-- Begin Cue -->>[\s\S]*?<<!-- End Cue -->>", content
            )
            if cue_block_match:
                block = cue_block_match.group(0)

                slug_match = re.search(r"\[Slug:(.*?)\]", block)
                if slug_match:
                    slug = slug_match.group(1).strip()

                type_match = re.search(r"\[Type:(.*?)\]", block)
                if type_match:
                    item_type = type_match.group(1).strip()

                duration_match = re.search(r"\[Duration:(.*?)\]", block)
                if duration_match:
                    duration = duration_match.group(1).strip()

                title_match = re.search(r"\[Title:(.*?)\]", block)
                if title_match:
                    title = title_match.group(1).strip()

            segment_list.append(
                {
                    "filename": file_name,
                    "slug": slug,
                    "item_type": item_type,
                    "duration": duration,
                    "title": title,
                }
            )

    return JSONResponse(content=segment_list)


@app.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(
    episode_number: str, segments: List[SegmentReorderItem] = Body(...)
):
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")

    if not os.path.isdir(episode_path):
        raise HTTPException(
            status_code=404, detail=f"Episode {episode_number} not found."
        )

    order_value = 10
    for segment in segments:
        file_path = os.path.join(episode_path, segment.filename)
        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=404, detail=f"Segment file {segment.filename} not found."
            )

        try:
            post = frontmatter.load(file_path)
            post["order"] = order_value
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
            order_value += 10

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail=f"Failed to update {segment.filename}: {str(e)}"
            )

    return {"status": "success", "message": "Rundown order updated."}
