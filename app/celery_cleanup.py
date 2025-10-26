"""
Celery Background Tasks - Job Cleanup and Monitoring
Handles orphaned jobs, stuck tasks, and automatic retries
"""
from datetime import datetime, timedelta, timezone
from celery_app import celery_app
from database import SessionLocal
from models_v2 import SOTProcessingJob
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='cleanup_orphaned_jobs')
def cleanup_orphaned_jobs():
    """
    Find and cleanup orphaned SOT processing jobs

    A job is considered orphaned if:
    - Status is 'processing'
    - No updates for 10+ minutes (updated_at is stale)
    - Worker likely crashed or lost connection

    Actions taken:
    - Mark job as 'failed' with appropriate error message
    - Log the orphaned job for monitoring
    - Optionally: Auto-retry if retry_count < 3
    """
    db = SessionLocal()
    try:
        # Find jobs stuck in 'processing' with no recent updates
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)

        orphaned_jobs = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.status == 'processing',
            SOTProcessingJob.updated_at < cutoff_time
        ).all()

        if not orphaned_jobs:
            logger.debug("No orphaned jobs found")
            return {"orphaned_count": 0, "cleaned": 0}

        logger.warning(f"Found {len(orphaned_jobs)} orphaned jobs")

        cleaned_count = 0
        for job in orphaned_jobs:
            logger.warning(
                f"Orphaned job detected: {job.temp_job_id} "
                f"(slug: {job.slug}, phase: {job.current_phase}, "
                f"last update: {job.updated_at})"
            )

            # Mark as failed
            job.status = 'failed'
            job.error_message = (
                f'Job orphaned - no updates since {job.updated_at}. '
                f'Worker likely crashed or lost connection.'
            )

            cleaned_count += 1

            # TODO: Implement auto-retry logic if needed
            # if job.retry_count < 3:
            #     job.retry_count += 1
            #     job.status = 'queued'
            #     # Re-queue the task
            #     from services.ffmpeg_tasks import process_sot_video_multi_phase
            #     process_sot_video_multi_phase.apply_async(
            #         args=[job.temp_job_id, job.episode, job.slug, ...],
            #         countdown=30
            #     )

        db.commit()

        logger.info(f"Cleaned up {cleaned_count} orphaned jobs")
        return {
            "orphaned_count": len(orphaned_jobs),
            "cleaned": cleaned_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Error in cleanup_orphaned_jobs: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name='cleanup_old_completed_jobs')
def cleanup_old_completed_jobs(days_to_keep=30):
    """
    Clean up old completed/failed job records
    Keeps the database tidy by removing old processing records

    Args:
        days_to_keep: Number of days to keep completed jobs (default 30)
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        deleted = db.query(SOTProcessingJob).filter(
            SOTProcessingJob.status.in_(['completed', 'failed']),
            SOTProcessingJob.created_at < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Deleted {deleted} old job records (older than {days_to_keep} days)")
        return {
            "deleted_count": deleted,
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Error in cleanup_old_completed_jobs: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'cleanup-orphaned-jobs-every-5-min': {
        'task': 'cleanup_orphaned_jobs',
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-old-jobs-daily': {
        'task': 'cleanup_old_completed_jobs',
        'schedule': 86400.0,  # Every 24 hours
        'args': (30,)  # Keep last 30 days
    },
}

# Configure timezone
celery_app.conf.timezone = 'UTC'
celery_app.conf.enable_utc = True
