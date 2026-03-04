"""
VO (Voice Over / B-Roll) processing router.

Handles video uploads and FFmpeg processing via Celery workers.
Similar to SOT but WITHOUT audio requirements - used for B-roll footage
that will be voiced over live during the show.

Cross-Platform Notes:
    - Files uploaded to shared storage accessible by all workers
    - Works with Linux workers (kairo, proxima) and Windows workers
    - Paths automatically normalized for worker platform
"""

import os
import shutil
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from celery_app import celery_app
from services.ffmpeg_tasks import process_vo_video
from auth.router import get_current_user_or_key
from database import get_db
from models_v2 import SOTProcessingJob  # Reuse SOT model with job_category field
from celery_jobs_router import register_celery_job
from models_assetid import AssetIDRegistry
from platform_utils import get_media_root

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vo", tags=["VO Processing"])


class VOUploadResponse(BaseModel):
    """Response model for VO upload."""
    task_id: str
    message: str
    status: str


class TaskStatusResponse(BaseModel):
    """Response model for task status check."""
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    result: Optional[dict] = None
    error: Optional[str] = None


class BackgroundUploadResponse(BaseModel):
    """Response model for background upload."""
    temp_job_id: str
    message: str
    status: str


@router.post("/upload/background", response_model=BackgroundUploadResponse)
async def upload_vo_background(
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
            temp_job_id = f"vo_{timestamp}_{unique_id}"

        # Create working directory on shared storage (cross-platform)
        working_dir = Path("/shared_media") / "preproc" / "working" / temp_job_id
        working_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file with standardized name
        upload_path = working_dir / f"{temp_job_id}_upload.mp4"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create database record (reuse SOTProcessingJob with job_category='vo')
        job = SOTProcessingJob(
            temp_job_id=temp_job_id,
            current_phase='upload',
            status='uploaded',
            working_directory=str(working_dir),
            job_category='vo'  # Distinguish from SOT
        )
        db.add(job)
        db.commit()

        return BackgroundUploadResponse(
            temp_job_id=temp_job_id,
            message=f"VO file uploaded successfully to working directory",
            status="uploaded"
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"🚨 VO UPLOAD ERROR: {str(e)}")
        logger.error(f"🚨 TRACEBACK:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Background upload failed: {str(e)}")


class VOProcessRequest(BaseModel):
    """Request model for VO processing."""
    temp_job_id: str
    episode: str
    slug: str
    asset_id: Optional[str] = None
    trim_start: str = "00:00:00"
    trim_end: str = "00:00:00"


@router.post("/process", response_model=VOUploadResponse)
async def process_vo_endpoint(
    request: VOProcessRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Trigger processing for an already-uploaded VO video.

    This endpoint is called when user submits the VO form after the
    video has been uploaded in the background.

    Args:
        request: Processing parameters including temp_job_id

    Returns:
        VOUploadResponse with celery task_id
    """
    try:
        logger.info(f"📥 VO process request: temp_job_id={request.temp_job_id}, episode={request.episode}, slug={request.slug}")

        # Verify job exists
        job = db.query(SOTProcessingJob).filter_by(temp_job_id=request.temp_job_id).first()
        if not job:
            logger.error(f"❌ Job not found: {request.temp_job_id}")
            raise HTTPException(status_code=404, detail=f"Job {request.temp_job_id} not found")

        if job.status != 'uploaded':
            logger.error(f"❌ Job {request.temp_job_id} has wrong status: {job.status}")
            raise HTTPException(
                status_code=400,
                detail=f"Job is in status '{job.status}', expected 'uploaded'"
            )

        # Verify upload file exists
        working_dir = Path("/shared_media/preproc/working") / request.temp_job_id
        upload_file = working_dir / f"{request.temp_job_id}_upload.mp4"

        if not working_dir.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Working directory not found: {working_dir}"
            )

        if not upload_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Upload file not found: {upload_file}"
            )

        file_size = upload_file.stat().st_size
        if file_size < 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Upload file too small ({file_size} bytes)"
            )

        logger.info(f"✅ Upload file verified: {upload_file} ({file_size:,} bytes)")

        # Create source AssetID
        source_asset_id = f"{request.asset_id}-src" if request.asset_id else None

        if source_asset_id:
            existing_source = db.query(AssetIDRegistry).filter_by(asset_id=source_asset_id).first()
            if not existing_source:
                source_asset = AssetIDRegistry(
                    asset_id=source_asset_id,
                    entity_type='vo_source',
                    request_reason='create',
                    request_context={
                        'episode': request.episode,
                        'slug': request.slug,
                        'original_asset_id': request.asset_id
                    },
                    asset_role='source',
                    purge_policy='keep',
                    meta_data={
                        'temp_job_id': request.temp_job_id,
                        'upload_date': datetime.now().isoformat()
                    }
                )
                db.add(source_asset)
                logger.info(f"✅ Created VO source asset: {source_asset_id}")

        # Update job
        job.episode = request.episode
        job.slug = request.slug
        job.asset_id = request.asset_id
        job.source_asset_id = source_asset_id
        job.final_asset_id = request.asset_id
        job.current_phase = 'phase0'
        job.status = 'processing'
        job.job_category = 'vo'

        # Submit to Celery - use NEW process_vo_video task
        task = process_vo_video.apply_async(
            args=[
                request.temp_job_id,
                request.episode,
                request.slug,
                request.trim_start,
                request.trim_end,
                request.asset_id
            ],
            queue='media',
            routing_key='media',
            exchange='media'
        )

        job.celery_task_id = task.id

        register_celery_job(db, task.id, "services.ffmpeg_tasks.process_vo_video", "Process VO Video", "media", request.episode, "media")

        db.commit()

        return VOUploadResponse(
            task_id=task.id,
            message=f"VO processing started for job {request.temp_job_id}",
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"🚨 VO PROCESSING ERROR: {str(e)}")
        logger.error(f"🚨 TRACEBACK:\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """Check status of VO processing task."""
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


@router.get("/job-status/{asset_id}")
async def get_job_status_by_asset_id(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current VO processing job status by AssetID.

    Returns the most recent job status for the given AssetID.
    Used for real-time status updates on cue cards.
    """
    logger.info(f"🔍 VO job status requested for AssetID: {asset_id}")

    try:
        # Find most recent VO job for this AssetID
        job = db.query(SOTProcessingJob).filter_by(
            asset_id=asset_id,
            job_category='vo'
        ).order_by(SOTProcessingJob.created_at.desc()).first()

        if not job:
            logger.warning(f"⚠️ No VO job found for AssetID: {asset_id}")
            return {
                "asset_id": asset_id,
                "status": "not_found",
                "message": "No VO processing job found for this AssetID"
            }

        logger.info(f"✅ Found VO job for AssetID {asset_id}: {job.temp_job_id}, status={job.status}")

        return {
            "asset_id": asset_id,
            "job_id": job.temp_job_id,
            "status": job.status,
            "current_phase": job.current_phase,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "celery_task_id": job.celery_task_id,
            "slug": job.slug,
            "episode": job.episode,
            "final_video_path": job.final_video_path,
            "final_thumbnail_path": job.final_thumbnail_path,
            "thumbnail_candidates": job.thumbnail_candidates,
            "source_asset_id": job.source_asset_id,
            "final_asset_id": job.final_asset_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/jobs/active")
async def get_active_vo_jobs(db: Session = Depends(get_db)):
    """Get all active VO processing jobs."""
    try:
        from datetime import timezone, timedelta

        active_jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.job_category == 'vo',
            SOTProcessingJob.status.in_(['queued', 'processing'])
        ).order_by(SOTProcessingJob.created_at.desc()).all()

        stall_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

        jobs_data = []
        for job in active_jobs:
            is_stalled = (
                job.status == 'processing' and
                job.updated_at and
                job.updated_at < stall_threshold
            )

            jobs_data.append({
                "job_id": job.temp_job_id,
                "asset_id": job.asset_id,
                "slug": job.slug,
                "episode": job.episode,
                "status": job.status,
                "current_phase": job.current_phase,
                "error_message": job.error_message,
                "is_stalled": is_stalled,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None
            })

        return {
            "active_count": len(jobs_data),
            "jobs": jobs_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active jobs: {str(e)}")


@router.get("/jobs/recent")
async def get_recent_vo_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent completed/failed VO jobs."""
    try:
        recent_jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.job_category == 'vo',
            SOTProcessingJob.status.in_(['completed', 'failed'])
        ).order_by(SOTProcessingJob.updated_at.desc()).limit(limit).all()

        jobs_data = []
        for job in recent_jobs:
            jobs_data.append({
                "job_id": job.temp_job_id,
                "asset_id": job.asset_id,
                "slug": job.slug,
                "episode": job.episode,
                "status": job.status,
                "current_phase": job.current_phase,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None
            })

        return {
            "count": len(jobs_data),
            "jobs": jobs_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent jobs: {str(e)}")
