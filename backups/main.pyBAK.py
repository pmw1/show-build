from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.sot_processor import process_sot
import logging
import hashlib
import os

# Version: 1.0.2
# Date: May 21, 2025

os.makedirs('/home/logs', exist_ok=True)

logging.basicConfig(
    filename='/home/logs/asset-id.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

LAST_ID_FILE = '/home/logs/last.id'

if not os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE, 'w') as f:
        f.write('0')

def read_last_id():
    with open(LAST_ID_FILE, 'r') as f:
        return int(f.read().strip())

def write_last_id(new_id):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(new_id))

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
        logging.error(f"Failed to generate ID: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/process_sot")
async def process_sot(
    episode: str = Form(...),
    asset_id: str = Form(...),
    segment_file: str = Form(...),
    file: UploadFile = File(...),
    slug: str = Form(...),
    description: str = Form(default=""),
    trim_start: str = Form(default="00:00:00"),
    trim_end: str = Form(default="00:00:00")
):
    # Log the received fields for debugging
    print(f"Received: episode={episode}, asset_id={asset_id}, segment_file={segment_file}, slug={slug}, description={description}, trim_start={trim_start}, trim_end={trim_end}")

    # Compute MD5 hash of the file for identification
    file_content = await file.read()
    md5_hash = hashlib.md5(file_content).hexdigest()

    # Save the uploaded file to a temporary location
    temp_dir = "/mnt/shared_media/temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{slug}-{md5_hash}.mp4")
    with open(temp_path, "wb") as f:
        f.write(file_content)

    # Placeholder for processing (trim, generate thumbnail, etc.)
    # For now, save the file and move to final location
    final_dir = f"/mnt/sync/disaffected/episodes/{episode}/assets/video"
    os.makedirs(final_dir, exist_ok=True)
    final_path = os.path.join(final_dir, f"{slug}.mp4")
    os.rename(temp_path, final_path)

    # Return success response
    return {
        "status": "success",
        "message": "SOT processing triggered",
        "asset_id": asset_id,
        "md5": md5_hash
    }