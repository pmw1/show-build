"""
SOT (Sound on Tape) processing router.

Handles video uploads and FFmpeg processing via Celery workers.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult

from celery_app import celery_app
from services.ffmpeg_tasks import process_sot_video
from auth.router import get_current_user_or_key

router = APIRouter(prefix="/api/sot", tags=["SOT Processing"])


class SOTUploadResponse(BaseModel):
    """Response model for SOT upload."""
    task_id: str
    message: str
    status: str


class TaskStatusResponse(BaseModel):
    """Response model for task status check."""
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/upload", response_model=SOTUploadResponse)
async def upload_sot_video(
    file: UploadFile = File(...),
    episode: str = Form(...),
    slug: str = Form(...),
    trim_start: str = Form("00:00:00"),
    trim_end: str = Form("00:00:00"),
    current_user=Depends(get_current_user_or_key)
):
    """
    Upload SOT video file and queue for processing.

    The file is saved temporarily and then processed by a Celery worker
    (running on kairo or proxima) which handles FFmpeg operations.

    Args:
        file: Video file upload
        episode: Episode number (e.g., "0245")
        slug: Item slug for naming output files
        trim_start: Optional start time for trimming (HH:MM:SS)
        trim_end: Optional end time for trimming (HH:MM:SS)

    Returns:
        SOTUploadResponse with task_id for status polling
    """
    try:
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")

        # Create temp directory for uploads
        temp_dir = Path("/tmp/sot_uploads")
        temp_dir.mkdir(exist_ok=True)

        # Save uploaded file to temp location
        temp_file_path = temp_dir / f"{episode}_{slug}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Submit task to Celery (will run on kairo/proxima)
        task = process_sot_video.apply_async(
            args=[str(temp_file_path), episode, slug, trim_start, trim_end],
            queue='media'
        )

        return SOTUploadResponse(
            task_id=task.id,
            message=f"SOT video queued for processing on media worker",
            status="queued"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """
    Check status of SOT processing task.

    Poll this endpoint to monitor progress of video processing.

    Args:
        task_id: Task ID returned from upload endpoint

    Returns:
        TaskStatusResponse with current status and results if complete
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
        )

        if task_result.successful():
            response.result = task_result.result
        elif task_result.failed():
            response.error = str(task_result.info)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """
    Cancel a running SOT processing task.

    Args:
        task_id: Task ID to cancel

    Returns:
        Confirmation message
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {"message": f"Task {task_id} cancelled", "status": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel failed: {str(e)}")
