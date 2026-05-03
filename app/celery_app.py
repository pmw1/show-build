"""
Celery configuration for server-heavy background processing.
Handles script compilation, quote extraction, and other intensive tasks.

Queue Architecture:
- assets_high: High-priority asset generation (user-initiated, single items)
- assets: Normal-priority asset generation (batch operations)
- assets_low: Low-priority asset generation (background regeneration)
- compilation: Script compilation tasks
- quotes: Quote extraction tasks
- media: FFmpeg/video processing tasks
"""
import sys
import os

# CRITICAL: Add /app to Python path BEFORE any imports
# This ensures wpm_audio_router and models_assetid can be imported by tasks
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

# Also add tools directory for direct renderer import
tools_path = '/app/../tools'
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

from celery import Celery

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://:showbuild2025@192.168.51.223:6379/0")

# Create Celery app
celery_app = Celery(
    "showbuild",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "services.script_compilation",
        "services.quote_extraction",
        "services.asset_processing",
        "services.ffmpeg_tasks",
        "services.tools_tasks",  # Production tools (validation, reports)
        "celery_cleanup",  # Orphaned job cleanup tasks
        "services.auto_description_service",  # Background tone + description generation
        "services.phase2_enrichment_service"  # Async Phase 2 Grok enrichment
    ]
)

# Custom task router for priority-based queue selection
def route_fsq_task(name, args, kwargs, options, task=None, **kw):
    """
    Route FSQ tasks to dedicated fsq queue on Kairo worker.

    This prevents the Windows media worker (which doesn't have FSQ dependencies)
    from picking up FSQ tasks via round-robin.
    """
    if name == 'services.asset_processing.generate_fsq_png':
        # Route to dedicated FSQ queue - only Kairo worker listens to this
        return {'queue': 'fsq'}
    return None


# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing with priority support
    task_routes=[
        route_fsq_task,  # Dynamic router for FSQ priority
        {
            "services.script_compilation.*": {"queue": "compilation"},
            "services.quote_extraction.*": {"queue": "quotes"},
            "services.asset_processing.*": {"queue": "assets"},  # Default for other asset tasks
            "services.ffmpeg_tasks.*": {"queue": "media"},
            "services.auto_description_service.*": {"queue": "llm_content"},
            "services.phase2_enrichment_service.*": {"queue": "llm_content"},
        }
    ],

    # Queue definitions with priorities
    # Workers should consume queues in priority order: assets_high, assets, assets_low
    task_queues={
        'assets_high': {
            'exchange': 'assets_high',
            'routing_key': 'assets.high',
        },
        'assets': {
            'exchange': 'assets',
            'routing_key': 'assets.normal',
        },
        'assets_low': {
            'exchange': 'assets_low',
            'routing_key': 'assets.low',
        },
        'compilation': {
            'exchange': 'compilation',
            'routing_key': 'compilation',
        },
        'quotes': {
            'exchange': 'quotes',
            'routing_key': 'quotes',
        },
        'media': {
            'exchange': 'media',
            'routing_key': 'media',
        },
        'fsq': {
            'exchange': 'fsq',
            'routing_key': 'fsq',
        },
        'llm_content': {
            'exchange': 'llm_content',
            'routing_key': 'llm_content',
        },
    },

    # Result backend settings
    result_expires=3600,  # 1 hour

    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Task time limits (prevent runaway tasks)
    task_soft_time_limit=540,  # 9 minutes soft limit (allows model loading + generation)
    task_time_limit=600,       # 10 minutes hard limit

    # Beat schedule — must live here so beat process loads it on startup
    beat_schedule={
        'cleanup-orphaned-jobs-every-5-min': {
            'task': 'cleanup_orphaned_jobs',
            'schedule': 300.0,
        },
        'cleanup-old-jobs-daily': {
            'task': 'cleanup_old_completed_jobs',
            'schedule': 86400.0,
            'args': (30,),
        },
        'llm-content-sweep-every-60s': {
            'task': 'services.auto_description_service.sweep_segments_for_auto_generation',
            'schedule': 60.0,
        },
        'episode-desc-sweep-every-120s': {
            'task': 'services.auto_description_service.sweep_episodes_for_auto_generation',
            'schedule': 120.0,
        },
    },
)

# Windows popup notifications (only on Windows)
import platform
if platform.system() == 'Windows':
    import ctypes
    import threading
    from celery.signals import task_prerun, task_postrun, task_failure

    def _show_popup(title, msg, timeout_ms=3000):
        """Show auto-closing popup (non-blocking)."""
        def _popup():
            ctypes.windll.user32.MessageBoxTimeoutW(0, msg, title, 0x40040, 0, timeout_ms)
        threading.Thread(target=_popup, daemon=True).start()

    @task_prerun.connect
    def notify_task_started(task_id, task, args, kwargs, **kw):
        """Show popup when task starts."""
        task_name = task.name.split('.')[-1]
        _show_popup("Task Started", task_name)

    @task_postrun.connect
    def notify_task_completed(task_id, task, args, kwargs, retval, state, **kw):
        """Show popup when task completes."""
        task_name = task.name.split('.')[-1]
        status = "Completed" if state == 'SUCCESS' else state
        _show_popup(f"Task {status}", task_name)

    @task_failure.connect
    def notify_task_failed(task_id, exception, args, kwargs, traceback, einfo, **kw):
        """Show popup when task fails."""
        _show_popup("Task FAILED", str(exception)[:100], timeout_ms=5000)