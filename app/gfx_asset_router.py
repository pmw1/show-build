"""
GFX Asset Generation Router
Generates PNG/video graphics for Full Screen Text and other GFX cues.

Architecture:
- All GFX generation routes to Celery by default (non-blocking)
- Priority queues: assets_high, assets, assets_low
- Files stored in: {episode}/assets/graphics/

Endpoints:
- POST /generate: Default async with 30s wait (high priority)
- POST /generate-async: Fire-and-forget with task ID (configurable priority)
- GET /task/{task_id}: Poll task status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from auth.router import get_current_user_or_key
from services.asset_processing import generate_gfx_png
from database import get_db
from sqlalchemy.orm import Session
from celery_jobs_router import register_celery_job

router = APIRouter()


class GFXAssetRequest(BaseModel):
    episode_id: str
    gfx_type: str = "fullscreen-text"
    body: str
    slug: str
    asset_id: str
    title: Optional[str] = None
    alignment: str = "center"
    font_family: str = "sans-serif"
    font_size: int = 25
    render_mode: str = "png"
    priority: str = "normal"


class GFXAssetResponse(BaseModel):
    success: bool
    asset_path: str
    asset_url: str
    message: str


class GFXAssetTaskResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    message: str


@router.post("/generate", response_model=GFXAssetResponse)
async def generate_gfx_asset(
    request: GFXAssetRequest,
    current_user=Depends(get_current_user_or_key)
):
    """
    Generate GFX PNG asset - routes to Celery and waits for completion.

    Args:
        request: GFX asset generation request

    Process:
    1. Queue task to Celery worker with high priority
    2. Wait for task completion (up to 30s)
    3. Return asset path/URL
    """
    try:
        print(f"🎨 Generating GFX asset for episode {request.episode_id}")
        print(f"   GFX Type: {request.gfx_type}")
        print(f"   Body: {request.body[:50]}...")
        print(f"   Asset ID: {request.asset_id}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        print(f"   📤 Queuing to Celery worker (high priority)...")

        task = generate_gfx_png.apply_async(
            kwargs={
                'episode_id': episode_id,
                'gfx_type': request.gfx_type,
                'body': request.body,
                'slug': request.slug,
                'asset_id': request.asset_id,
                'title': request.title,
                'alignment': request.alignment,
                'font_family': request.font_family,
                'font_size': request.font_size,
                'render_mode': request.render_mode,
                'priority': 'high'
            },
            queue='assets_high'
        )

        print(f"   ⏳ Waiting for task {task.id} to complete...")

        # Wait for result with timeout
        try:
            result = task.get(timeout=30)

            if result.get('success'):
                print(f"   ✅ Asset generated successfully (Celery)")
                print(f"   📁 Path: {result.get('asset_path')}")
                print(f"   🔗 URL: {result.get('asset_url')}")

                return GFXAssetResponse(
                    success=True,
                    asset_path=result.get('asset_path', ''),
                    asset_url=result.get('asset_url', ''),
                    message=result.get('message', 'GFX asset generated successfully')
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"GFX generation failed: {result.get('message', 'Unknown error')}"
                )

        except TimeoutError:
            print(f"   ⏱️ Task {task.id} still running after 30s")
            raise HTTPException(
                status_code=202,
                detail=f"GFX generation queued but not yet complete. Task ID: {task.id}. Poll /api/gfx/task/{task.id} for status."
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error generating GFX asset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate GFX asset: {str(e)}"
        )


@router.post("/generate-async", response_model=GFXAssetTaskResponse)
async def generate_gfx_asset_async(
    request: GFXAssetRequest,
    current_user=Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Generate GFX PNG asset asynchronously using Celery.

    Returns task ID for monitoring progress via /api/gfx/task/{task_id} endpoint.
    """
    try:
        priority = request.priority.lower()
        if priority not in ('high', 'normal', 'low'):
            priority = 'normal'

        queue_map = {
            'high': 'assets_high',
            'normal': 'assets',
            'low': 'assets_low'
        }
        queue_name = queue_map[priority]

        print(f"🎨 Queuing GFX PNG generation for episode {request.episode_id}")
        print(f"   GFX Type: {request.gfx_type}")
        print(f"   Body: {request.body[:50]}...")
        print(f"   Asset ID: {request.asset_id}")
        print(f"   Priority: {priority} → Queue: {queue_name}")

        # Normalize episode ID
        episode_id = request.episode_id.zfill(4) if len(request.episode_id) < 4 else request.episode_id

        task = generate_gfx_png.apply_async(
            kwargs={
                'episode_id': episode_id,
                'gfx_type': request.gfx_type,
                'body': request.body,
                'slug': request.slug,
                'asset_id': request.asset_id,
                'title': request.title,
                'alignment': request.alignment,
                'font_family': request.font_family,
                'font_size': request.font_size,
                'render_mode': request.render_mode,
                'priority': priority
            },
            queue=queue_name
        )

        print(f"   ✅ Task queued: {task.id}")

        register_celery_job(db, task.id, "services.asset_processing.generate_gfx_png", "Generate GFX", "assets", episode_id, queue_name)

        return GFXAssetTaskResponse(
            success=True,
            task_id=task.id,
            status="QUEUED",
            message=f"GFX PNG generation task queued ({priority} priority): {task.id}"
        )

    except Exception as e:
        print(f"   ❌ Error queuing GFX generation task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue GFX generation task: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_gfx_task_status(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """
    Get status of a GFX PNG generation task.

    Returns task state and result if completed.
    """
    try:
        task_result = generate_gfx_png.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task_result.state,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None
        }

        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.info)
        elif task_result.state == 'PROGRESS':
            response["progress"] = task_result.info

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )
