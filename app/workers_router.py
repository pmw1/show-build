"""
Worker Monitoring API Router

Provides real-time information about active Celery workers across platforms.
Displays which workers are online, their platform, current tasks, and statistics.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel
from celery_app import celery_app
from auth.router import get_current_user_or_key

router = APIRouter(prefix="/api/workers", tags=["Worker Monitoring"])


class WorkerInfo(BaseModel):
    """Information about a single Celery worker"""
    name: str
    hostname: str
    platform: str  # "Linux" or "Windows"
    status: str  # "online", "offline", "busy"
    active_tasks: int
    queue: str
    capabilities: List[str]  # ["ffmpeg", "nvenc", "vaapi", etc.]
    stats: Optional[Dict] = None


class WorkerStatusResponse(BaseModel):
    """Response model for worker status endpoint"""
    total_workers: int
    online_workers: int
    workers: List[WorkerInfo]
    queue_depth: int


@router.get("/status", response_model=WorkerStatusResponse)
async def get_worker_status(current_user=Depends(get_current_user_or_key)):
    """
    Get current status of all Celery workers.

    Returns information about each worker including:
    - Platform (Linux/Windows)
    - Active task count
    - Worker capabilities (GPU encoding, etc.)
    - Queue depth

    Useful for monitoring cross-platform worker distribution.
    """
    try:
        inspector = celery_app.control.inspect()

        # Get active workers
        active_workers = inspector.active()
        registered = inspector.registered()
        stats = inspector.stats()

        if not active_workers:
            return WorkerStatusResponse(
                total_workers=0,
                online_workers=0,
                workers=[],
                queue_depth=0
            )

        workers_list = []

        for worker_name in active_workers.keys():
            # Parse worker info from name
            # Format: "windows-PCNAME@hostname" or "kairo@hostname"
            platform = "Windows" if "windows" in worker_name.lower() else "Linux"

            # Get active tasks for this worker
            active_task_count = len(active_workers.get(worker_name, []))

            # Determine status
            if active_task_count > 0:
                status = "busy"
            else:
                status = "online"

            # Get worker stats
            worker_stats = stats.get(worker_name, {}) if stats else {}

            # Determine capabilities
            capabilities = ["ffmpeg"]
            if platform == "Windows":
                capabilities.append("nvenc")  # Assume NVENC on Windows
                capabilities.append("windows-native")
            else:
                capabilities.append("vaapi")  # Assume VAAPI on Linux
                capabilities.append("whisper")  # Whisper typically on Linux

            workers_list.append(WorkerInfo(
                name=worker_name,
                hostname=worker_name.split('@')[-1] if '@' in worker_name else worker_name,
                platform=platform,
                status=status,
                active_tasks=active_task_count,
                queue="media",  # All workers use media queue
                capabilities=capabilities,
                stats=worker_stats
            ))

        # Get queue depth (approximate from active tasks)
        total_active = sum(w.active_tasks for w in workers_list)

        return WorkerStatusResponse(
            total_workers=len(workers_list),
            online_workers=len([w for w in workers_list if w.status != "offline"]),
            workers=workers_list,
            queue_depth=total_active
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")


@router.get("/active-tasks")
async def get_active_tasks(current_user=Depends(get_current_user_or_key)):
    """
    Get all currently executing tasks across all workers.

    Returns detailed information about what each worker is currently processing.
    """
    try:
        inspector = celery_app.control.inspect()
        active = inspector.active()

        if not active:
            return {"active_tasks": [], "total": 0}

        all_tasks = []

        for worker_name, tasks in active.items():
            platform = "Windows" if "windows" in worker_name.lower() else "Linux"

            for task in tasks:
                all_tasks.append({
                    "worker": worker_name,
                    "platform": platform,
                    "task_id": task.get("id"),
                    "task_name": task.get("name"),
                    "args": task.get("args", []),
                    "time_start": task.get("time_start")
                })

        return {
            "active_tasks": all_tasks,
            "total": len(all_tasks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active tasks: {str(e)}")


@router.get("/stats")
async def get_worker_stats(current_user=Depends(get_current_user_or_key)):
    """
    Get detailed statistics for all workers.

    Includes completed task counts, execution times, and resource usage.
    """
    try:
        inspector = celery_app.control.inspect()
        stats = inspector.stats()

        if not stats:
            return {"workers": {}, "total_workers": 0}

        workers_stats = {}

        for worker_name, worker_info in stats.items():
            platform = "Windows" if "windows" in worker_name.lower() else "Linux"

            workers_stats[worker_name] = {
                "platform": platform,
                "pool": worker_info.get("pool", {}).get("implementation"),
                "max_concurrency": worker_info.get("pool", {}).get("max-concurrency"),
                "total_tasks": worker_info.get("total", {}),
                "rusage": worker_info.get("rusage")
            }

        return {
            "workers": workers_stats,
            "total_workers": len(workers_stats)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker stats: {str(e)}")


@router.post("/ping")
async def ping_workers(current_user=Depends(get_current_user_or_key)):
    """
    Ping all workers to check if they're responsive.

    Returns a list of workers that responded to the ping.
    """
    try:
        inspector = celery_app.control.inspect()
        ping_result = inspector.ping()

        if not ping_result:
            return {"responsive_workers": [], "total": 0}

        responsive = []
        for worker_name, pong in ping_result.items():
            platform = "Windows" if "windows" in worker_name.lower() else "Linux"
            responsive.append({
                "worker": worker_name,
                "platform": platform,
                "response": pong
            })

        return {
            "responsive_workers": responsive,
            "total": len(responsive)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ping workers: {str(e)}")


@router.get("/platform-summary")
async def get_platform_summary(current_user=Depends(get_current_user_or_key)):
    """
    Get summary statistics grouped by platform.

    Shows how many Linux vs Windows workers are active and their task counts.
    """
    try:
        inspector = celery_app.control.inspect()
        active = inspector.active()

        if not active:
            return {
                "Linux": {"workers": 0, "active_tasks": 0},
                "Windows": {"workers": 0, "active_tasks": 0}
            }

        platform_stats = {
            "Linux": {"workers": 0, "active_tasks": 0},
            "Windows": {"workers": 0, "active_tasks": 0}
        }

        for worker_name, tasks in active.items():
            platform = "Windows" if "windows" in worker_name.lower() else "Linux"
            platform_stats[platform]["workers"] += 1
            platform_stats[platform]["active_tasks"] += len(tasks)

        return platform_stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get platform summary: {str(e)}")
