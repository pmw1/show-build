"""
Production Tools API Router

Provides API endpoints for production validation and diagnostic tools.
All tools are accessible via both programmatic API and UI interfaces.

Tools:
- Health Check (sync): Extended system diagnostics
- Rundown Diff (sync): Compare two rundown versions
- Asset Metadata Validator (async): Scan cue blocks for missing fields
- Duration Reconciliation (async): Compare DB vs actual media durations
- Production Report (async): Generate episode summary HTML
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from celery_app import celery_app
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["Production Tools"])


# ============================================================================
# Pydantic Models
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Extended health check response."""
    timestamp: str
    status: str
    database: Dict[str, Any]
    redis: Dict[str, Any]
    celery: Dict[str, Any]
    storage: Dict[str, Any]
    apis: Dict[str, Any]


class TaskResponse(BaseModel):
    """Response for async task initiation."""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response for task status check."""
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RundownDiffRequest(BaseModel):
    """Request for rundown diff comparison."""
    episode: str
    version_a: Optional[str] = None  # Timestamp or 'current'
    version_b: Optional[str] = None  # Timestamp or 'current'


class RundownDiffResponse(BaseModel):
    """Response for rundown diff."""
    episode: str
    additions: List[Dict[str, Any]]
    deletions: List[Dict[str, Any]]
    modifications: List[Dict[str, Any]]
    summary: Dict[str, Any]


class ValidateMetadataRequest(BaseModel):
    """Request for metadata validation."""
    episode: Optional[str] = None  # None = validate all episodes


class ReconcileDurationsRequest(BaseModel):
    """Request for duration reconciliation."""
    episode: str


class ProductionReportRequest(BaseModel):
    """Request for production report generation."""
    episode: str
    include_assets: bool = True
    include_scripts: bool = True
    include_timeline: bool = True


class GenerateMp3Request(BaseModel):
    """Request for MP3 generation from episode master video."""
    episode: str
    profile_id: Optional[int] = None
    bitrate: str = "192k"


# ============================================================================
# Sync Endpoints (Immediate Response)
# ============================================================================

@router.get("/health-check", response_model=HealthCheckResponse)
async def extended_health_check(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Extended system health check with detailed diagnostics.

    Checks:
    - Database connectivity and table counts
    - Redis connectivity and memory usage
    - Celery worker status and queue lengths
    - Storage paths accessibility
    - External API connectivity (Ollama, XTTS, etc.)
    """
    from services.tools_service import ToolsService

    try:
        result = await ToolsService.run_health_check(db)
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/rundown-diff", response_model=RundownDiffResponse)
async def compare_rundown_versions(
    request: RundownDiffRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Compare two rundown versions and return differences.

    If version_a/version_b not specified, compares current DB state
    with last saved snapshot (if available).
    """
    from services.tools_service import ToolsService

    try:
        result = ToolsService.compare_rundown_versions(
            db=db,
            episode=request.episode,
            version_a=request.version_a,
            version_b=request.version_b
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Rundown diff failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rundown diff failed: {str(e)}")


# ============================================================================
# Async Endpoints (Celery Tasks)
# ============================================================================

@router.post("/validate-metadata", response_model=TaskResponse)
async def validate_asset_metadata(
    request: ValidateMetadataRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Start async validation of cue block metadata.

    Scans all cue blocks for:
    - Missing required fields (AssetID, Duration, etc.)
    - Invalid field values
    - Orphaned asset references
    """
    from services.tools_tasks import validate_metadata_task

    try:
        task = validate_metadata_task.apply_async(
            args=[request.episode],
            queue='assets'
        )

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Metadata validation started for {'all episodes' if not request.episode else f'episode {request.episode}'}"
        )
    except Exception as e:
        logger.error(f"Failed to start metadata validation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@router.get("/validate-metadata/{task_id}", response_model=TaskStatusResponse)
async def get_validation_status(
    task_id: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get status of metadata validation task."""
    return _get_task_status(task_id)


@router.post("/reconcile-durations", response_model=TaskResponse)
async def reconcile_durations(
    request: ReconcileDurationsRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Start async duration reconciliation.

    Compares:
    - Database duration values vs actual media file durations (via ffprobe)
    - Identifies mismatches and suggests corrections
    """
    from services.tools_tasks import reconcile_durations_task

    try:
        task = reconcile_durations_task.apply_async(
            args=[request.episode],
            queue='media'  # Uses ffprobe, route to media queue
        )

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Duration reconciliation started for episode {request.episode}"
        )
    except Exception as e:
        logger.error(f"Failed to start duration reconciliation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@router.get("/reconcile-durations/{task_id}", response_model=TaskStatusResponse)
async def get_reconciliation_status(
    task_id: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get status of duration reconciliation task."""
    return _get_task_status(task_id)


@router.post("/production-report", response_model=TaskResponse)
async def generate_production_report(
    request: ProductionReportRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Start async generation of production report.

    Generates comprehensive HTML report including:
    - Episode summary and metadata
    - Rundown item status overview
    - Asset inventory with thumbnails
    - Timeline visualization
    - Script completion status
    """
    from services.tools_tasks import generate_production_report_task

    try:
        task = generate_production_report_task.apply_async(
            args=[
                request.episode,
                request.include_assets,
                request.include_scripts,
                request.include_timeline
            ],
            queue='assets'
        )

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Production report generation started for episode {request.episode}"
        )
    except Exception as e:
        logger.error(f"Failed to start production report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@router.get("/production-report/{task_id}", response_model=TaskStatusResponse)
async def get_report_status(
    task_id: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get status of production report task."""
    return _get_task_status(task_id)


# ============================================================================
# Helper Functions
# ============================================================================

# ============================================================================
# Generate MP3 Endpoints
# ============================================================================

@router.get("/generate-mp3/eligible")
async def get_eligible_mp3_episodes(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    List episodes eligible for MP3 generation.

    An episode is eligible if it has a master video file (.mov, .mp4, or .avi)
    in its exports directory and does not already have an MP3.
    """
    import os
    from platform_utils import get_media_root

    media_root = get_media_root()
    episodes_dir = os.path.join(media_root, "episodes")

    # Get all episodes from database
    episodes = db.execute(
        text("SELECT episode_number, title, status FROM episodes WHERE episode_number IS NOT NULL ORDER BY episode_number DESC")
    ).fetchall()

    eligible = []
    for ep in episodes:
        ep_num = str(ep.episode_number).zfill(4)
        exports_dir = os.path.join(episodes_dir, ep_num, "exports")

        source_file = None
        for ext in [".mov", ".mp4", ".avi"]:
            candidate = os.path.join(exports_dir, f"{ep_num}{ext}")
            if os.path.isfile(candidate):
                source_file = f"{ep_num}{ext}"
                break

        if source_file:
            mp3_path = os.path.join(exports_dir, f"{ep_num}.mp3")
            mp3_exists = os.path.isfile(mp3_path)
            mp3_size_mb = None
            if mp3_exists:
                mp3_size_mb = round(os.path.getsize(mp3_path) / (1024 * 1024), 1)

            eligible.append({
                "episode": ep_num,
                "title": ep.title,
                "status": ep.status,
                "source_file": source_file,
                "mp3_exists": mp3_exists,
                "mp3_size_mb": mp3_size_mb,
            })

    return {"eligible": eligible}


@router.get("/generate-mp3/check/{episode}")
async def check_mp3_status(
    episode: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Check if source video exists and MP3 status for an episode."""
    import os
    from platform_utils import get_media_root

    media_root = get_media_root()
    exports_dir = os.path.join(media_root, "episodes", episode, "exports")

    source_file = None
    for ext in [".mov", ".mp4", ".avi"]:
        candidate = os.path.join(exports_dir, f"{episode}{ext}")
        if os.path.isfile(candidate):
            source_file = f"{episode}{ext}"
            break

    mp3_path = os.path.join(exports_dir, f"{episode}.mp3")
    mp3_exists = os.path.isfile(mp3_path)
    mp3_size_mb = None
    if mp3_exists:
        mp3_size_mb = round(os.path.getsize(mp3_path) / (1024 * 1024), 1)

    return {
        "episode": episode,
        "source_exists": source_file is not None,
        "source_file": source_file,
        "mp3_exists": mp3_exists,
        "mp3_size_mb": mp3_size_mb,
    }


@router.post("/generate-mp3", response_model=TaskResponse)
async def generate_mp3(
    request: GenerateMp3Request,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Start async MP3 generation from episode master video."""
    import os
    from platform_utils import get_media_root

    # Validate source exists before dispatching
    media_root = get_media_root()
    exports_dir = os.path.join(media_root, "episodes", request.episode, "exports")

    source_exists = False
    for ext in [".mov", ".mp4", ".avi"]:
        if os.path.isfile(os.path.join(exports_dir, f"{request.episode}{ext}")):
            source_exists = True
            break

    if not source_exists:
        raise HTTPException(
            status_code=404,
            detail=f"No source video found for episode {request.episode}"
        )

    from services.ffmpeg_tasks import generate_episode_mp3

    try:
        task = generate_episode_mp3.apply_async(
            args=[request.episode, request.profile_id, request.bitrate],
            queue='media'
        )

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"MP3 generation started for episode {request.episode}"
        )
    except Exception as e:
        logger.error(f"Failed to start MP3 generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@router.get("/generate-mp3/status/{task_id}", response_model=TaskStatusResponse)
async def get_mp3_status(
    task_id: str,
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get status of MP3 generation task."""
    return _get_task_status(task_id)


# ============================================================================
# Helper Functions
# ============================================================================

def _get_task_status(task_id: str) -> TaskStatusResponse:
    """Get status of a Celery task."""
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
        )

        # Handle different task states
        if task_result.status == 'PENDING':
            response.status = 'pending'
        elif task_result.status == 'STARTED':
            response.status = 'running'
            if task_result.info and isinstance(task_result.info, dict):
                response.progress = task_result.info.get('progress', 0)
        elif task_result.status == 'SUCCESS':
            response.status = 'completed'
            response.result = task_result.result
        elif task_result.status == 'FAILURE':
            response.status = 'failed'
            response.error = str(task_result.info)
        elif task_result.status == 'PROGRESS':
            response.status = 'running'
            if task_result.info and isinstance(task_result.info, dict):
                response.progress = task_result.info.get('progress', 0)

        return response

    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
