"""
Celery Jobs API Router

Provides unified job monitoring for all celery tasks dispatched from show-build.
Tracks tasks in celery_job_log table and syncs status from Celery backend.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from celery_app import celery_app
from celery.result import AsyncResult
from models_v2 import CeleryJobLog

logger = logging.getLogger(__name__)

router = APIRouter()


def register_celery_job(
    db: Session,
    task_id: str,
    task_name: str,
    display_name: str = None,
    category: str = "general",
    episode: str = None,
    queue: str = None
):
    """Register a dispatched celery task in the job log.

    Call this after every .apply_async() or .delay() call.
    """
    job = CeleryJobLog(
        task_id=task_id,
        task_name=task_name,
        display_name=display_name or task_name.split(".")[-1].replace("_", " ").title(),
        category=category,
        episode=episode,
        status="pending",
        queue=queue
    )
    db.add(job)
    db.commit()
    return job


def _sync_job_status(job: CeleryJobLog) -> dict:
    """Sync a job's status from Celery backend and return dict."""
    try:
        result = AsyncResult(job.task_id, app=celery_app)

        celery_status = result.status
        status_map = {
            'PENDING': 'pending',
            'STARTED': 'running',
            'PROGRESS': 'running',
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'REVOKED': 'failed',
            'RETRY': 'running',
        }
        new_status = status_map.get(celery_status, job.status)

        progress = None
        stage = None
        result_summary = job.result_summary

        if celery_status in ('STARTED', 'PROGRESS') and isinstance(result.info, dict):
            progress = result.info.get('progress')
            stage = result.info.get('stage')
        elif celery_status == 'SUCCESS':
            progress = 100
            if isinstance(result.result, dict):
                result_summary = result.result.get('message', str(result.result)[:200])
            elif result.result:
                result_summary = str(result.result)[:200]
        elif celery_status == 'FAILURE':
            result_summary = str(result.info)[:500] if result.info else 'Task failed'

        return {
            "id": job.id,
            "task_id": job.task_id,
            "task_name": job.task_name,
            "display_name": job.display_name,
            "category": job.category,
            "episode": job.episode,
            "status": new_status,
            "progress": progress,
            "stage": stage,
            "result_summary": result_summary,
            "worker": job.worker,
            "queue": job.queue,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }
    except Exception as e:
        logger.warning(f"Failed to sync status for task {job.task_id}: {e}")
        return {
            "id": job.id,
            "task_id": job.task_id,
            "task_name": job.task_name,
            "display_name": job.display_name,
            "category": job.category,
            "episode": job.episode,
            "status": job.status,
            "progress": job.progress,
            "result_summary": job.result_summary,
            "worker": job.worker,
            "queue": job.queue,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }


@router.get("/active")
async def get_active_celery_jobs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key)
):
    """Get all active (pending/running) celery jobs with live status from Celery backend."""
    try:
        jobs = db.query(CeleryJobLog).filter(
            CeleryJobLog.status.in_(['pending', 'running'])
        ).order_by(CeleryJobLog.created_at.desc()).all()

        jobs_data = []
        for job in jobs:
            job_data = _sync_job_status(job)

            # Update DB if status changed
            if job_data["status"] != job.status:
                job.status = job_data["status"]
                if job_data["progress"] is not None:
                    job.progress = job_data["progress"]
                if job_data["result_summary"] and job_data["result_summary"] != job.result_summary:
                    job.result_summary = job_data["result_summary"]

            jobs_data.append(job_data)

        db.commit()

        return {
            "active_count": len(jobs_data),
            "jobs": jobs_data
        }

    except Exception as e:
        logger.error(f"Failed to fetch active celery jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_celery_jobs(
    limit: int = Query(default=30, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key)
):
    """Get recent completed/failed celery jobs."""
    try:
        jobs = db.query(CeleryJobLog).filter(
            CeleryJobLog.status.in_(['completed', 'failed'])
        ).order_by(CeleryJobLog.updated_at.desc()).limit(limit).all()

        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "id": job.id,
                "task_id": job.task_id,
                "task_name": job.task_name,
                "display_name": job.display_name,
                "category": job.category,
                "episode": job.episode,
                "status": job.status,
                "progress": job.progress,
                "result_summary": job.result_summary,
                "worker": job.worker,
                "queue": job.queue,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            })

        return {
            "count": len(jobs_data),
            "jobs": jobs_data
        }

    except Exception as e:
        logger.error(f"Failed to fetch recent celery jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_celery_jobs(
    limit: int = Query(default=50, le=200),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key)
):
    """Get all celery jobs (active + recent) with optional category filter."""
    try:
        query = db.query(CeleryJobLog)
        if category:
            query = query.filter(CeleryJobLog.category == category)

        jobs = query.order_by(CeleryJobLog.created_at.desc()).limit(limit).all()

        jobs_data = []
        for job in jobs:
            if job.status in ('pending', 'running'):
                job_data = _sync_job_status(job)
                if job_data["status"] != job.status:
                    job.status = job_data["status"]
                    if job_data["progress"] is not None:
                        job.progress = job_data["progress"]
                    if job_data["result_summary"]:
                        job.result_summary = job_data["result_summary"]
                jobs_data.append(job_data)
            else:
                jobs_data.append({
                    "id": job.id,
                    "task_id": job.task_id,
                    "task_name": job.task_name,
                    "display_name": job.display_name,
                    "category": job.category,
                    "episode": job.episode,
                    "status": job.status,
                    "progress": job.progress,
                    "result_summary": job.result_summary,
                    "worker": job.worker,
                    "queue": job.queue,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                })

        db.commit()

        active = [j for j in jobs_data if j["status"] in ("pending", "running")]
        completed = [j for j in jobs_data if j["status"] not in ("pending", "running")]

        return {
            "total": len(jobs_data),
            "active_count": len(active),
            "completed_count": len(completed),
            "jobs": jobs_data
        }

    except Exception as e:
        logger.error(f"Failed to fetch celery jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_celery_jobs(
    status: Optional[str] = Query(default=None, description="Clear only jobs with this status (completed, failed). Omit to clear all non-active."),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_or_key)
):
    """Clear completed/failed jobs from the log."""
    try:
        if status:
            if status not in ('completed', 'failed'):
                raise HTTPException(status_code=400, detail="Can only clear 'completed' or 'failed' jobs")
            count = db.query(CeleryJobLog).filter(
                CeleryJobLog.status == status
            ).delete()
        else:
            # Clear all non-active jobs
            count = db.query(CeleryJobLog).filter(
                CeleryJobLog.status.in_(['completed', 'failed'])
            ).delete()

        db.commit()

        return {"cleared": count, "message": f"Cleared {count} job(s)"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear celery jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
