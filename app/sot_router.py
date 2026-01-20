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
import logging
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
from models_assetid import AssetIDRegistry, AssetRelationship
from platform_utils import get_media_root  # Cross-platform path handling

logger = logging.getLogger(__name__)
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
    devel_mode: bool = False  # If True, keep all intermediate files and return paths in payload


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
        # DEBUG: Log incoming request
        logger.info(f"📥 Multi-phase request received: temp_job_id={request.temp_job_id}, episode={request.episode}, slug={request.slug}, asset_id={request.asset_id}")

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

        logger.info(f"✅ Job found with correct status: {job.status}")

        # CRITICAL FIX: Verify upload file exists before submitting to Celery
        # Prevents race condition where file hasn't fully synced to NFS
        # Use /shared_media which is the Docker container mount point (not /mnt/sync/shared_media)
        from pathlib import Path
        working_dir = Path("/shared_media/preproc/working") / request.temp_job_id
        upload_file = working_dir / f"{request.temp_job_id}_upload.mp4"

        logger.info(f"🔍 Checking paths: working_dir={working_dir}, exists={working_dir.exists()}")

        if not working_dir.exists():
            logger.error(f"❌ Working directory not found: {working_dir}")
            raise HTTPException(
                status_code=400,
                detail=f"Working directory not found: {working_dir}. Background upload may have failed."
            )

        if not upload_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Upload file not found: {upload_file}. Background upload may still be in progress or failed."
            )

        file_size = upload_file.stat().st_size
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Upload file is empty (0 bytes). Please re-upload the video."
            )

        # Minimum file size sanity check (1KB)
        if file_size < 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Upload file too small ({file_size} bytes). File may be corrupted."
            )

        logger.info(f"✅ Upload file verified: {upload_file} ({file_size:,} bytes)")

        # Pre-processing FFprobe validation
        # Validates file before submitting to Celery to catch issues early
        try:
            import subprocess
            from platform_utils import get_ffprobe_binary

            ffprobe = get_ffprobe_binary()

            # Get video metadata via FFprobe
            probe_cmd = [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height",
                "-of", "json",
                str(upload_file)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)

            if probe_result.returncode == 0:
                import json
                probe_data = json.loads(probe_result.stdout)

                # Extract format info
                fmt = probe_data.get('format', {})
                duration = float(fmt.get('duration', 0))
                probe_size = int(fmt.get('size', 0))

                # Extract stream info
                streams = probe_data.get('streams', [])
                has_video = any(s.get('codec_type') == 'video' for s in streams)
                video_codec = next((s.get('codec_name') for s in streams if s.get('codec_type') == 'video'), None)

                # Validation checks
                MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
                MAX_DURATION = 60 * 60  # 60 minutes
                MIN_DURATION = 1  # 1 second

                if probe_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large: {probe_size / (1024**3):.2f}GB exceeds 10GB limit"
                    )

                if duration < MIN_DURATION:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Video too short: {duration:.1f}s (minimum 1 second)"
                    )

                if duration > MAX_DURATION:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Video too long: {duration / 60:.1f} minutes (maximum 60 minutes)"
                    )

                if not has_video:
                    raise HTTPException(
                        status_code=400,
                        detail="No video stream found in file. Please upload a valid video file."
                    )

                # Log warnings for unusual codecs
                unusual_codecs = ['mjpeg', 'rawvideo', 'gif', 'webp']
                if video_codec and video_codec.lower() in unusual_codecs:
                    logger.warning(f"⚠️ Unusual video codec detected: {video_codec}. Processing may be slower.")

                logger.info(f"✅ FFprobe validation passed: {duration:.1f}s, codec={video_codec}")

            else:
                # FFprobe failed - log warning but continue (might still be processable)
                stderr = probe_result.stderr[:200] if probe_result.stderr else 'Unknown error'
                logger.warning(f"⚠️ FFprobe validation failed: {stderr}. Continuing anyway.")

        except HTTPException:
            raise
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ FFprobe validation timed out. Continuing anyway.")
        except Exception as e:
            logger.warning(f"⚠️ FFprobe validation error: {e}. Continuing anyway.")

        # Create source AssetID for parent/child architecture
        # Source AssetID stores the original uploaded video
        source_asset_id = f"{request.asset_id}-src" if request.asset_id else None

        if source_asset_id:
            # Check if source asset already exists
            existing_source = db.query(AssetIDRegistry).filter_by(asset_id=source_asset_id).first()

            if not existing_source:
                # Create source asset registry entry
                source_asset = AssetIDRegistry(
                    asset_id=source_asset_id,
                    entity_type='sot_source',
                    request_reason='create',
                    request_context={
                        'episode': request.episode,
                        'slug': request.slug,
                        'original_asset_id': request.asset_id
                    },
                    asset_role='source',
                    purge_policy='keep',  # Default to keeping sources
                    meta_data={
                        'temp_job_id': request.temp_job_id,
                        'upload_date': datetime.now().isoformat(),
                        'trim_start': request.trim_start,
                        'trim_end': request.trim_end,
                        'job_type': request.job_type
                    }
                )
                db.add(source_asset)
                logger.info(f"✅ Created source asset: {source_asset_id}")

        # Update job with episode, slug, and asset_id
        job.episode = request.episode
        job.slug = request.slug
        job.asset_id = request.asset_id
        job.source_asset_id = source_asset_id
        job.final_asset_id = request.asset_id  # This will be the final trimmed asset
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
                request.asset_id,
                request.devel_mode  # Pass devel_mode flag
            ],
            queue='media',
            routing_key='media',
            exchange='media'
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
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"🚨 PROCESSING ERROR: {str(e)}")
        logger.error(f"🚨 TRACEBACK:\n{error_trace}")
        db.rollback()
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
        List of active job records with human-readable phase messages
    """
    # Phase display messages for toast notifications
    PHASE_MESSAGES = {
        'upload': 'Video uploaded',
        'phase0': 'Analyzing video properties',
        'phase0.5': 'Transcribing audio with Whisper',
        'phase1': 'Normalizing video codec',
        'phase1.1': 'Analyzing audio channels',
        'phase2': 'Normalizing audio levels',
        'phase3': 'Trimming video',
        'phase4': 'Generating thumbnails & extracting audio',
        'phase5': 'Creating derivatives',
        'phase6': 'Copying to final destination',
        'phase7': 'Finalizing',
        'phase8': 'Verifying output quality'
    }

    try:
        jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.episode == episode,
            SOTProcessingJob.status.in_(['uploaded', 'processing', 'partial_complete'])
        ).all()

        return {
            "episode": episode,
            "jobs": [
                {
                    "temp_job_id": job.temp_job_id,
                    "asset_id": job.asset_id,
                    "slug": job.slug,
                    "current_phase": job.current_phase,
                    "phase_message": PHASE_MESSAGES.get(job.current_phase, job.current_phase),
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

        # CRITICAL FIX: Verify upload file still exists before retry
        # Use /shared_media which is the Docker container mount point
        from pathlib import Path
        working_dir = Path("/shared_media/preproc/working") / temp_job_id
        upload_file = working_dir / f"{temp_job_id}_upload.mp4"

        if not upload_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Upload file no longer exists: {upload_file}. Cannot retry - please re-upload."
            )

        logger.info(f"✅ Retry file verified: {upload_file}")

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


@router.get("/jobs/active")
async def get_active_jobs(db: Session = Depends(get_db)):
    """
    Get all active SOT processing jobs.

    Returns all jobs that are currently queued or processing.
    Used for job monitoring dashboard.

    Returns:
        List of active jobs with status, phase, progress, and errors
    """
    try:
        from datetime import datetime, timezone, timedelta

        # Get all queued or processing jobs
        active_jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.status.in_(['queued', 'processing'])
        ).order_by(SOTProcessingJob.created_at.desc()).all()

        # Detect stalled jobs (no update in 5+ minutes while processing)
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
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "celery_task_id": job.celery_task_id
            })

        return {
            "active_count": len(jobs_data),
            "jobs": jobs_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active jobs: {str(e)}")


@router.get("/jobs/recent")
async def get_recent_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get recent completed/failed jobs.

    Args:
        limit: Maximum number of jobs to return (default 20)

    Returns:
        List of recent jobs
    """
    try:
        recent_jobs = db.query(SOTProcessingJob).filter(
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
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "celery_task_id": job.celery_task_id
            })

        return {
            "count": len(jobs_data),
            "jobs": jobs_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent jobs: {str(e)}")


@router.get("/job-status/{asset_id}")
async def get_job_status_by_asset_id(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current SOT processing job status by AssetID.

    Returns the most recent job status for the given AssetID.
    Used for real-time status updates on cue cards.

    Args:
        asset_id: AssetID of the SOT cue

    Returns:
        Job status information including status, phase, progress, and errors
    """
    logger.info(f"🔍 Job status requested for AssetID: {asset_id}")

    try:
        # Find most recent job for this AssetID
        job = db.query(SOTProcessingJob).filter_by(
            asset_id=asset_id
        ).order_by(SOTProcessingJob.created_at.desc()).first()

        if not job:
            logger.warning(f"⚠️ No job found for AssetID: {asset_id}")
            return {
                "asset_id": asset_id,
                "status": "not_found",
                "message": "No processing job found for this AssetID"
            }

        logger.info(f"✅ Found job for AssetID {asset_id}: {job.temp_job_id}, status={job.status}, phase={job.current_phase}")

        # Return job status with transcription and asset paths
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
            "transcription": job.transcription,
            "final_video_path": job.final_video_path,
            "final_thumbnail_path": job.final_thumbnail_path,
            "thumbnail_candidates": job.thumbnail_candidates,
            "source_asset_id": job.source_asset_id,
            "final_asset_id": job.final_asset_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/reprocess/{asset_id}")
async def reprocess_sot_by_asset_id(
    asset_id: str,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Completely reprocess a SOT - wipe media, delete DB entries, and resubmit.

    This endpoint:
    1. Wipes all media files created by the job (video, audio, thumbnails)
    2. Deletes all SOTProcessingJob database entries for this AssetID
    3. Re-examines the cue data from rundown_items
    4. Checks if uploaded video file still exists
    5. Resubmits the Celery job with fresh metadata

    Args:
        asset_id: AssetID of the SOT to reprocess

    Returns:
        dict: Cleanup summary and new task_id
    """
    try:
        import glob
        from models_v2 import RundownItem

        cleanup_summary = {
            "asset_id": asset_id,
            "cancelled_tasks": 0,
            "deleted_jobs": 0,
            "deleted_media_files": 0,
            "media_files_deleted": [],
            "working_dirs_removed": []
        }

        # Find all jobs for this AssetID
        jobs = db.query(SOTProcessingJob).filter_by(asset_id=asset_id).all()

        if not jobs:
            raise HTTPException(
                status_code=404,
                detail=f"No processing jobs found for asset_id: {asset_id}"
            )

        # Get info from the first job for resubmission
        first_job = jobs[0]
        episode = first_job.episode
        slug = first_job.slug
        uploaded_video_path = None

        # Check if uploaded video still exists in working directory
        if first_job.working_directory:
            working_dir = Path(first_job.working_directory)
            if working_dir.exists():
                # Look for the uploaded video file
                upload_file = working_dir / f"{first_job.temp_job_id}_upload.mp4"
                if upload_file.exists():
                    uploaded_video_path = str(upload_file)

        # Cancel Celery tasks and collect job data
        for job in jobs:
            if job.celery_task_id:
                try:
                    celery_app.control.revoke(job.celery_task_id, terminate=True)
                    cleanup_summary["cancelled_tasks"] += 1
                except Exception as e:
                    print(f"Failed to cancel task {job.celery_task_id}: {e}")

        # Delete all generated media files in episode assets directory
        media_root = get_media_root()
        sots_dir = media_root / "episodes" / episode / "assets" / "sots"

        if sots_dir.exists():
            # Find all files matching the slug pattern
            patterns = [
                f"{slug}.*",  # Main files (video, audio)
                f"{slug}-thumb*.jpg",  # Thumbnails
                f"{slug}-*.mp4",  # Clip derivatives if any
                f"{slug}-*.mp3"   # Audio derivatives if any
            ]

            for pattern in patterns:
                matching_files = list(sots_dir.glob(pattern))
                for file_path in matching_files:
                    try:
                        file_path.unlink()
                        cleanup_summary["media_files_deleted"].append(str(file_path))
                        cleanup_summary["deleted_media_files"] += 1
                        print(f"Deleted media file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")

        # Clean up working directories (but keep uploaded video if exists)
        for job in jobs:
            if job.working_directory and Path(job.working_directory).exists():
                working_dir = Path(job.working_directory)
                # Don't delete the upload file, only intermediate files
                for item in working_dir.iterdir():
                    if item.name != f"{job.temp_job_id}_upload.mp4":
                        try:
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                        except Exception as e:
                            print(f"Failed to remove {item}: {e}")

        # Delete all SOTProcessingJob records
        for job in jobs:
            db.delete(job)
            cleanup_summary["deleted_jobs"] += 1

        db.commit()

        # Re-examine cue data from rundown_items
        # SOTs can be embedded in segments, so check both direct asset_id match
        # and script_content containing the SOT AssetID
        rundown_item = db.query(RundownItem).filter_by(asset_id=asset_id).first()

        # If not found as direct asset_id, search script_content for SOT cues
        if not rundown_item:
            rundown_item = db.query(RundownItem).filter(
                RundownItem.script_content.like(f'%[AssetID: {asset_id}]%')
            ).first()

        if not rundown_item:
            return {
                "message": "Cleanup complete but no rundown item found",
                "asset_id": asset_id,
                "status": "cleaned_no_cue",
                "cleanup_summary": cleanup_summary,
                "next_steps": "No associated rundown item found. Manual re-upload required."
            }

        # Check if we have the uploaded video to reprocess
        if not uploaded_video_path:
            return {
                "message": "Cleanup complete but uploaded video not found",
                "asset_id": asset_id,
                "status": "cleaned_no_video",
                "cleanup_summary": cleanup_summary,
                "next_steps": "Original video file not found. Please re-upload video using SOT modal."
            }

        # Create new processing job with NEW working directory
        new_temp_job_id = f"sot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # CRITICAL: Create a NEW working directory for the new temp_job_id
        # The worker expects: /shared_media/preproc/working/{temp_job_id}/{temp_job_id}_upload.mp4
        new_working_dir = Path("/shared_media") / "preproc" / "working" / new_temp_job_id
        new_working_dir.mkdir(parents=True, exist_ok=True)

        new_job = SOTProcessingJob(
            temp_job_id=new_temp_job_id,
            episode=episode,
            slug=slug,
            asset_id=asset_id,
            status='processing',
            current_phase='phase0',
            working_directory=str(new_working_dir)
        )
        db.add(new_job)

        # Copy the uploaded video to the NEW working directory with correct filename
        new_upload_path = new_working_dir / f"{new_temp_job_id}_upload.mp4"
        if not new_upload_path.exists():
            shutil.copy2(uploaded_video_path, new_upload_path)
            logger.info(f"Copied upload file to new working directory: {new_upload_path}")

        # CRITICAL FIX: Verify copy succeeded before submitting to Celery
        if not new_upload_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Failed to copy upload file to {new_upload_path}"
            )

        file_size = new_upload_path.stat().st_size
        if file_size < 1024:
            raise HTTPException(
                status_code=500,
                detail=f"Copy appears corrupted: {file_size} bytes"
            )

        logger.info(f"✅ Reprocess file verified: {new_upload_path} ({file_size:,} bytes)")

        # Extract metadata from rundown item (trim times, job type, clips if stored)
        import json
        import re
        trim_start = "00:00:00"
        trim_end = "00:00:00"
        job_type = "full_process"
        clips = None

        # Try to get processing metadata from cue block in script_content
        if rundown_item.script_content:
            # First, find the specific cue block for this AssetID
            cue_pattern = re.compile(
                r'<!-- Begin Cue -->.*?\[AssetID: ' + re.escape(asset_id) + r'\].*?<!-- End Cue -->',
                re.DOTALL
            )
            cue_match = cue_pattern.search(rundown_item.script_content)

            if cue_match:
                cue_block = cue_match.group(0)

                # Extract TrimStart
                trim_start_match = re.search(r'\[TrimStart:\s*([^\]]+)\]', cue_block)
                if trim_start_match:
                    trim_start = trim_start_match.group(1).strip()

                # Extract TrimEnd
                trim_end_match = re.search(r'\[TrimEnd:\s*([^\]]+)\]', cue_block)
                if trim_end_match:
                    trim_end = trim_end_match.group(1).strip()

                # Extract ClippingMethod and map to job_type
                clipping_match = re.search(r'\[ClippingMethod:\s*([^\]]+)\]', cue_block)
                if clipping_match:
                    clipping_method = clipping_match.group(1).strip()
                    if clipping_method == 'individual-clips':
                        job_type = 'individual_clips'
                    elif clipping_method == 'montage':
                        job_type = 'montage'
                    elif clipping_method == 'single-trim':
                        job_type = 'single_trim'
                    logger.info(f"📋 Extracted clipping method: {clipping_method} -> job_type: {job_type}")

                # Extract Clips array
                clips_match = re.search(r'\[Clips:\s*"(.+?)"\]', cue_block, re.DOTALL)
                if clips_match:
                    try:
                        # The clips are JSON-escaped inside the cue block
                        clips_json = clips_match.group(1).replace('\\"', '"')
                        clips = json.loads(clips_json)
                        logger.info(f"📋 Extracted {len(clips)} clips from cue block")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Could not parse clips JSON: {e}")
            else:
                logger.warning(f"Could not find cue block for AssetID {asset_id}")

        # Resubmit to Celery
        task = process_sot_video_multi_phase.apply_async(
            args=[
                new_temp_job_id,
                episode,
                slug,
                trim_start,
                trim_end,
                job_type,
                clips,
                asset_id,
                False  # devel_mode
            ],
            queue='media',
            routing_key='media',
            exchange='media'
        )

        new_job.celery_task_id = task.id
        db.commit()

        return {
            "message": "SOT reprocessing started successfully",
            "asset_id": asset_id,
            "status": "reprocessing",
            "new_task_id": task.id,
            "new_temp_job_id": new_temp_job_id,
            "cleanup_summary": cleanup_summary,
            "episode": episode,
            "slug": slug
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"🚨 REPROCESS ERROR: {str(e)}")
        print(f"🚨 TRACEBACK:\n{error_trace}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reprocess failed: {str(e)}")
