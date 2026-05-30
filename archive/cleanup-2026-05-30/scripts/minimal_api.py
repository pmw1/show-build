"""
Minimal FastAPI app for script compilation coordination.
Only essential endpoints to prevent conflicts and queue jobs.
"""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from minimal_models import Episode, ProcessingJob
from minimal_celery import compile_script_task
from database import get_db
import uuid

app = FastAPI(title="Show-Build Minimal Coordinator")

@app.post("/episodes/{episode_number}/compile")
async def start_compilation(episode_number: str, db: Session = Depends(get_db)):
    """Start script compilation job for episode."""
    
    # Check if already processing
    episode = db.query(Episode).filter(Episode.episode_number == episode_number).first()
    if not episode:
        episode = Episode(episode_number=episode_number)
        db.add(episode)
        db.commit()
    
    if episode.is_processing:
        raise HTTPException(status_code=409, detail="Episode is already being processed")
    
    # Mark as processing
    episode.is_processing = True
    db.commit()
    
    # Create job
    job = ProcessingJob(
        episode_number=episode_number,
        job_type="script_compilation"
    )
    db.add(job)
    db.commit()
    
    # Start Celery task
    task = compile_script_task.delay(episode_number, job.id)
    
    return {"job_id": job.id, "task_id": str(task.id), "status": "started"}

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Check job status."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "episode_number": job.episode_number,
        "status": job.status,
        "created_at": job.created_at,
        "error_message": job.error_message,
        "result": job.result
    }

@app.get("/episodes/{episode_number}/status")
async def get_episode_status(episode_number: str, db: Session = Depends(get_db)):
    """Check if episode is currently being processed."""
    episode = db.query(Episode).filter(Episode.episode_number == episode_number).first()
    
    return {
        "episode_number": episode_number,
        "is_processing": episode.is_processing if episode else False,
        "last_compiled": episode.last_compiled if episode else None
    }