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
