"""Miscellaneous endpoints: branding, LLM, logging, compilation, websocket."""

import os
import random
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from auth.utils import get_current_user_or_key
from websocket import websocket_endpoint
from services.script_compilation import compile_episode_script
from celery_app import celery_app
from celery_jobs_router import register_celery_job
from models_v2 import Episode

logger = logging.getLogger(__name__)

router = APIRouter(tags=["misc"])


# ── LLM Notifications ──

@router.get("/api/llm-notifications/unseen")
async def get_unseen_llm_notifications(db: Session = Depends(get_db)):
    """Return unseen LLM content generation notifications and mark them as seen."""
    from sqlalchemy import text
    try:
        rows = db.execute(text("""
            SELECT id, type, content_type, asset_id, segment_title, episode_number,
                   status, message, created_at
            FROM llm_notifications
            WHERE seen = FALSE
            ORDER BY created_at DESC
            LIMIT 20
        """)).fetchall()
        if not rows:
            return {"notifications": []}
        ids = [r.id for r in rows]
        db.execute(text("UPDATE llm_notifications SET seen = TRUE WHERE id = ANY(:ids)"), {"ids": ids})
        db.commit()
        return {"notifications": [dict(r._mapping) for r in rows]}
    except Exception as e:
        return {"notifications": [], "error": str(e)}


@router.get("/api/branding/random")
async def random_branding_image():
    """Serve a random branding image from docs/branding/"""
    branding_dir = Path("/app/docs/branding")
    if not branding_dir.exists():
        branding_dir = Path("docs/branding")

    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    images = [f for f in branding_dir.iterdir() if f.suffix.lower() in image_extensions]

    if not images:
        raise HTTPException(status_code=404, detail="No branding images found")

    random_image = random.choice(images)
    return FileResponse(random_image)


@router.get("/api/llm/ollama/models")
async def get_ollama_models(current_user: dict = Depends(get_current_user_or_key)):
    """Get list of available Ollama models"""
    try:
        from api_config import api_config_manager

        ollama_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="ollama"
        )

        if not ollama_config or not ollama_config.get("host"):
            return {"models": []}

        ollama_host = ollama_config.get("host")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "models": [{"name": m["name"], "size": m.get("size")} for m in models]
                }

        return {"models": []}
    except Exception as e:
        logger.error(f"Failed to fetch Ollama models: {e}")
        return {"models": []}


@router.post("/api/logs/client-event")
async def log_client_event(event_data: dict):
    """Log client-side events for monitoring and analytics"""
    event_logger = logging.getLogger("client_events")

    event_type = event_data.get("event", "unknown")
    duration = event_data.get("duration_ms", 0)
    reason = event_data.get("reason", "")
    timestamp = event_data.get("timestamp", "")

    log_message = f"Client Event: {event_type} | Duration: {duration}ms | Reason: {reason} | Time: {timestamp}"

    if duration > 5000:
        event_logger.error(log_message)
    elif duration > 2000:
        event_logger.warning(log_message)
    else:
        event_logger.info(log_message)

    return {"success": True, "message": "Event logged"}


@router.websocket("/ws/{client_id}")
async def websocket_connection(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time job status updates."""
    await websocket_endpoint(websocket, client_id)


@router.post("/episodes/{episode_id}/compile-script")
async def compile_script_async(
    episode_id: str,
    output_format: str = "html",
    include_cues: bool = True,
    validate_only: bool = False,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Start script compilation as background job with real-time updates."""
    try:
        from core.paths import paths
        if not paths.episode_exists(episode_id):
            raise HTTPException(status_code=404, detail="Episode not found")

        job = compile_episode_script.delay(
            episode_id=episode_id,
            output_format=output_format,
            include_cues=include_cues,
            validate_only=validate_only
        )

        register_celery_job(db, job.id, "services.script_tasks.compile_episode_script", "Compile Script", "tools", episode_id, "compilation")

        return {
            "job_id": job.id,
            "status": "started",
            "message": f"Script compilation started for episode {episode_id}",
            "websocket_url": "/ws/{client_id}",
            "check_status_url": f"/jobs/{job.id}/status"
        }

    except Exception as e:
        logging.error(f"Failed to start script compilation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Get current status of a background processing job."""
    from models_v2 import CeleryJobLog
    job = db.query(CeleryJobLog).filter(CeleryJobLog.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    celery_result = celery_app.AsyncResult(job_id)

    return {
        "job_id": job_id,
        "status": job.status,
        "celery_status": celery_result.status,
        "progress": getattr(job, 'progress', None),
        "job_type": job.task_name,
        "result": getattr(job, 'result', None),
        "error_message": getattr(job, 'error_message', None),
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }
