"""Trigger model — backs the `triggers` table (migration g018_triggers_table).

A trigger is a configurable, table-driven schedule/condition that fires a Celery
task by name. Read by the tick_triggers task (services/triggers.py) every ~30s.
See showtime docs/trigger-system-design.md. Conventions mirror models/jobs.py.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from database import Base


# Valid trigger types (kept here as the single source of truth; validated by the
# API/router and by tick_triggers).
TRIGGER_TYPES = (
    "interval",       # config: {"seconds": int}
    "cron",           # config: {"minute","hour","day_of_week","day_of_month","month_of_year"} (UTC)
    "datetime",       # config: {"run_at": ISO-8601 UTC} — one-shot, sets consumed=True
    "watch_folder",   # config: {"path","glob","recursive","stability_seconds","emit_existing_on_start"}
    "state_change",   # config: {"check": <named predicate>, "params": {...}}
    "manual",         # config: {} — never auto-fires; only via POST /fire
)


class Trigger(Base):
    """One configurable trigger binding. Fires `task_name` on `queue` when due."""
    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)
    config = Column(JSON, nullable=False)
    task_name = Column(String(255), nullable=False)
    task_args = Column(JSON, nullable=True)        # {"args": [...], "kwargs": {...}}
    queue = Column(String(50), nullable=True)
    enabled = Column(Boolean, nullable=False, server_default="1", index=True)
    category = Column(String(50), nullable=False, server_default="general")
    owner_tool = Column(String(50), nullable=True)
    last_fired_at = Column(DateTime(timezone=True), nullable=True)
    last_task_id = Column(String(255), nullable=True)   # joins celery_job_log.task_id
    fire_count = Column(Integer, nullable=False, server_default="0")
    consumed = Column(Boolean, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
