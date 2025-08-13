"""
Celery configuration for server-heavy background processing.
Handles script compilation, quote extraction, and other intensive tasks.
"""
from celery import Celery
import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "showbuild",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "services.script_compilation",
        "services.quote_extraction", 
        "services.asset_processing"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "services.script_compilation.*": {"queue": "compilation"},
        "services.quote_extraction.*": {"queue": "quotes"},
        "services.asset_processing.*": {"queue": "assets"},
    },
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)