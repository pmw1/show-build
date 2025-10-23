"""
SOT (Sound on Tape) processing router.

Handles video uploads and FFmpeg processing via Celery workers.

Cross-Platform Notes:
    - Files uploaded to shared storage accessible by all workers
    - Works with Linux workers (kairo, proxima) and Windows workers
    - Paths automatically normalized for worker platform
"""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from celery_app import celery_app
from services.ffmpeg_tasks import process_sot_video, process_sot_video_multi_phase
from auth.router import get_current_user_or_key
from database import get_db
from models_v2 import SOTProcessingJob
from platform_utils import get_media_root  # Cross-platform path handling

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

    The file is saved to shared storage accessible by all workers
    (Linux and Windows) and then processed by whichever Celery worker
    is available.

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

        # Use shared storage for cross-platform worker access
        # This path is accessible by both Linux (/mnt/sync/disaffected) and Windows (Z:\) workers
        media_root = get_media_root()
        upload_dir = media_root / "incoming" / "nat"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{episode}_{slug}_{timestamp}_{unique_id}_{file.filename}"

        upload_path = upload_dir / safe_filename

        # Save uploaded file to shared storage
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Submit task to Celery queue
        # Path will be automatically normalized by worker's platform_utils
        task = process_sot_video.apply_async(
            args=[str(upload_path), episode, slug, trim_start, trim_end],
            queue='media'
        )

        return SOTUploadResponse(
            task_id=task.id,
            message=f"SOT video uploaded to shared storage and queued for processing",
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


class BackgroundUploadResponse(BaseModel):
    """Response model for background upload."""
    temp_job_id: str
    message: str
    status: str


@router.post("/upload/background", response_model=BackgroundUploadResponse)
async def upload_sot_background(
    file: UploadFile = File(...),
    temp_job_id: Optional[str] = Form(None),
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Background upload endpoint - saves file without processing.

    This endpoint is called immediately when user selects a video file,
    before they fill out the form. The file is saved to a working directory
    on shared storage (accessible by all workers) and a temp_job_id is
    returned for later processing.

    Args:
        file: Video file upload
        temp_job_id: Optional job ID (generated if not provided)

    Returns:
        BackgroundUploadResponse with temp_job_id
    """
    try:
        # Generate temp_job_id if not provided
        if not temp_job_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            temp_job_id = f"sot_{timestamp}_{unique_id}"

        # Create working directory on shared storage (cross-platform)
        # Docker container: /shared_media/preproc/working/{job_id}/
        # Windows worker: Z:\shared_media\preproc\working\{job_id}\
        # Using /shared_media which is mounted in container from /mnt/sync/shared_media
        working_dir = Path("/shared_media") / "preproc" / "working" / temp_job_id
        working_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file with standardized name
        upload_path = working_dir / f"{temp_job_id}_upload.mp4"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create database record
        job = SOTProcessingJob(
            temp_job_id=temp_job_id,
            current_phase='upload',
            status='uploaded',
            working_directory=str(working_dir)
        )
        db.add(job)
        db.commit()

        return BackgroundUploadResponse(
            temp_job_id=temp_job_id,
            message=f"File uploaded successfully to working directory",
            status="uploaded"
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"🚨 UPLOAD ERROR: {str(e)}")
        print(f"🚨 TRACEBACK:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Background upload failed: {str(e)}")


class MultiPhaseProcessRequest(BaseModel):
    """Request model for multi-phase processing."""
    temp_job_id: str
    episode: str
    slug: str
    asset_id: Optional[str] = None  # AssetID for linking to cue block
    trim_start: str = "00:00:00"
    trim_end: str = "00:00:00"
    job_type: str = "full_process"  # single_trim, individual_clips, montage, full_process
    clips: Optional[list] = None  # Array of clip objects for individual_clips/montage modes


@router.post("/process/multi-phase", response_model=SOTUploadResponse)
async def process_sot_multi_phase_endpoint(
    request: MultiPhaseProcessRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Trigger multi-phase processing for an already-uploaded video.

    This endpoint is called when user submits the SOT form after the
    video has been uploaded in the background.

    Args:
        request: Processing parameters including temp_job_id

    Returns:
        SOTUploadResponse with celery task_id
    """
    try:
        # Verify job exists
        job = db.query(SOTProcessingJob).filter_by(temp_job_id=request.temp_job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {request.temp_job_id} not found")

        if job.status != 'uploaded':
            raise HTTPException(
                status_code=400,
                detail=f"Job is in status '{job.status}', expected 'uploaded'"
            )

        # Update job with episode, slug, and asset_id
        job.episode = request.episode
        job.slug = request.slug
        job.asset_id = request.asset_id
        job.current_phase = 'phase1'
        job.status = 'processing'

        # Submit to Celery with job_type, clips, and asset_id
        task = process_sot_video_multi_phase.apply_async(
            args=[
                request.temp_job_id,
                request.episode,
                request.slug,
                request.trim_start,
                request.trim_end,
                request.job_type,
                request.clips,
                request.asset_id
            ],
            queue='media'
        )

        job.celery_task_id = task.id
        db.commit()

        return SOTUploadResponse(
            task_id=task.id,
            message=f"Multi-phase processing started for job {request.temp_job_id}",
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/active-jobs/{episode}")
async def get_active_jobs(
    episode: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get all active (processing/uploaded) SOT jobs for an episode.

    Used by frontend to poll for processing updates.

    Args:
        episode: Episode number

    Returns:
        List of active job records
    """
    try:
        jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.episode == episode,
            SOTProcessingJob.status.in_(['uploaded', 'processing'])
        ).all()

        return {
            "episode": episode,
            "jobs": [
                {
                    "temp_job_id": job.temp_job_id,
                    "asset_id": job.asset_id,
                    "slug": job.slug,
                    "current_phase": job.current_phase,
                    "status": job.status,
                    "job_type": job.job_type,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active jobs: {str(e)}")


@router.post("/retry/{temp_job_id}")
async def retry_failed_job(
    temp_job_id: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Retry a failed SOT processing job from the last successful phase.

    Args:
        temp_job_id: Job ID to retry

    Returns:
        SOTUploadResponse with new task_id
    """
    try:
        # Get job from database
        job = db.query(SOTProcessingJob).filter_by(temp_job_id=temp_job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {temp_job_id} not found")

        if job.status not in ['failed', 'error']:
            raise HTTPException(
                status_code=400,
                detail=f"Job status is '{job.status}', can only retry failed jobs"
            )

        # Increment retry count
        job.retry_count += 1
        if job.retry_count > 3:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum retry limit (3) reached for job {temp_job_id}"
            )

        # Reset status and error message
        job.status = 'processing'
        job.error_message = None

        # Resubmit to Celery
        task = process_sot_video_multi_phase.apply_async(
            args=[
                temp_job_id,
                job.episode,
                job.slug,
                "00:00:00",  # Use defaults for trim (stored in job if needed)
                "00:00:00"
            ],
            queue='media'
        )

        job.celery_task_id = task.id
        db.commit()

        return SOTUploadResponse(
            task_id=task.id,
            message=f"Job {temp_job_id} retry started (attempt {job.retry_count})",
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")
