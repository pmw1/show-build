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
        "celery_cleanup"  # Orphaned job cleanup tasks
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
    task_soft_time_limit=120,  # 2 minutes soft limit (raises exception)
    task_time_limit=180,       # 3 minutes hard limit (kills task)
)