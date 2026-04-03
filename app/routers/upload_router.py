"""File upload endpoints for video and image processing."""

import os
import logging
import hashlib

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["uploads"])

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/proc_vid")
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


@router.post("/upload_image")
async def upload_image(
    file: UploadFile = File(..., alias="file"),
    id: str = Form(..., alias="id"),
    episode: str = Form(..., alias="episode"),
    slug: str = Form(..., alias="slug"),
):
    """Upload an image file for processing."""
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


@router.post("/api/upload/image")
async def upload_img_cue_image(
    file: UploadFile = File(...),
    filename: str = Form(...),
    episode: str = Form(...)
):
    """Upload an image file for IMG cue blocks to episode assets/images directory."""
    if not file:
        raise HTTPException(status_code=400, detail="File is required")

    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not episode:
        raise HTTPException(status_code=400, detail="Episode number is required")

    file_content = await file.read()

    if not file_content:
        raise HTTPException(status_code=422, detail="File content is empty")

    allowed_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=422,
            detail="File must be an image (png, jpg, jpeg, gif, webp)"
        )

    padded_episode = episode.zfill(4)
    images_dir = f"/home/episodes/{padded_episode}/assets/images"
    os.makedirs(images_dir, exist_ok=True)
    filepath = os.path.join(images_dir, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(file_content)

        md5_hash = hashlib.md5(file_content).hexdigest()

        logging.info(f"IMG cue image saved: {filepath}, MD5: {md5_hash}")

        web_url = f"/episodes/{padded_episode}/assets/images/{filename}"

        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "filename": filename,
            "filepath": web_url,
            "md5": md5_hash,
            "size": len(file_content)
        }

    except Exception as e:
        logging.error(f"Failed to save IMG cue image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
