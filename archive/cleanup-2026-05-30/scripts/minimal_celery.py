"""
Minimal Celery worker for script compilation.
Wraps existing compile-script-dev.py tool with database coordination.
"""
from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from minimal_models import Episode, ProcessingJob
from datetime import datetime
import subprocess
import os

# Celery app
celery_app = Celery(
    'minimal_showbuild',
    broker='redis://redis:6379',
    backend='redis://redis:6379'
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://showbuild:showbuild_dev@postgres:5432/showbuild_minimal")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task
def compile_script_task(episode_number: str, job_id: int):
    """Compile episode script using existing tool."""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        episode = db.query(Episode).filter(Episode.episode_number == episode_number).first()
        
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Run existing compilation script
        result = subprocess.run([
            "python", "/tools/compile-script-dev.py", episode_number
        ], capture_output=True, text=True, cwd="/tools")
        
        if result.returncode == 0:
            # Success
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.result = {"output": result.stdout}
            
            episode.is_processing = False
            episode.last_compiled = datetime.utcnow()
            
        else:
            # Failure
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error_message = result.stderr
            episode.is_processing = False
            
        db.commit()
        return {"status": job.status, "episode": episode_number}
        
    except Exception as e:
        # Handle errors
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        episode.is_processing = False
        db.commit()
        raise
        
    finally:
        db.close()