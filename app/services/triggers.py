"""Trigger dispatch tasks — the runtime side of the `triggers` table.

Two Celery tasks (NOT a custom Beat scheduler — show-build #708 elected the
single-tick approach so a table error can never take down Beat scheduling):

  tick_triggers       — registered in beat_schedule @ ~30s. Reads the triggers
                        table and dispatches whatever is due. Beat merely ENQUEUES
                        this task; all table I/O happens in a worker, not in Beat.
  scan_watch_trigger  — runs on assets_low. Scans one watch_folder trigger's path
                        for stable files and enqueues the bound task per new file.
                        Kept OFF the Beat process (show-build #708 MUST-FIX-2): a
                        blocking SMB/NFS scan ties up only this worker slot.

Firing reuses register_celery_job so triggered jobs appear in the existing job
monitor, and records last_task_id on the trigger row (joins celery_job_log).

See showtime docs/trigger-system-design.md (approved relay #708). Conventions
mirror existing show-build tasks (celery_app.send_task, SessionLocal,
register_celery_job).
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

from celery import shared_task

from celery_app import celery_app

log = logging.getLogger("services.triggers")

# Track which (trigger_id, filepath) pairs we've already dispatched, so a
# watch_folder re-scan doesn't re-fire a file every tick. In-process best-effort;
# a file's stability + this set is the dedupe. (For cross-restart durability a
# small processed-files table could be added later; not needed for v1.)
_WATCH_SEEN: set[tuple[int, str]] = set()


@contextmanager
def _db():
    """Fork-safe session, same pattern as ffmpeg_tasks.db_session()."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ----- enqueue + log (reuses show-build's job ledger) -----

def _fire(db, trigger, *, extra_kwargs: dict | None = None) -> str | None:
    """send_task the trigger's bound task, register it in celery_job_log, and
    stamp the trigger row. Returns the task_id (or None on failure)."""
    from celery_jobs_router import register_celery_job

    targs = trigger.task_args or {}
    args = list(targs.get("args", []) or [])
    kwargs = dict(targs.get("kwargs", {}) or {})
    if extra_kwargs:
        kwargs.update(extra_kwargs)
    try:
        async_res = celery_app.send_task(
            trigger.task_name, args=args, kwargs=kwargs, queue=trigger.queue
        )
    except Exception as e:  # noqa: BLE001
        log.error("trigger %s: send_task(%s) failed: %s",
                  trigger.name, trigger.task_name, e)
        return None

    try:
        register_celery_job(
            db, async_res.id, trigger.task_name,
            display_name=f"trigger:{trigger.name}",
            category=trigger.category or "general",
            queue=trigger.queue,
        )
    except Exception as e:  # noqa: BLE001
        # Ledger write is best-effort — never lose the dispatch over a log hiccup.
        log.warning("trigger %s: register_celery_job failed: %s", trigger.name, e)

    trigger.last_fired_at = _now()
    trigger.last_task_id = async_res.id
    trigger.fire_count = (trigger.fire_count or 0) + 1
    return async_res.id


# ----- due-checks per type -----

def _interval_due(trigger) -> bool:
    secs = float((trigger.config or {}).get("seconds", 0) or 0)
    if secs <= 0:
        return False
    if trigger.last_fired_at is None:
        return True
    last = trigger.last_fired_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (_now() - last) >= timedelta(seconds=secs)


def _cron_due(trigger) -> bool:
    """Evaluate a crontab schedule (UTC, since celery enable_utc=True)."""
    from celery.schedules import crontab
    c = trigger.config or {}
    try:
        cron = crontab(
            minute=c.get("minute", "*"),
            hour=c.get("hour", "*"),
            day_of_week=c.get("day_of_week", "*"),
            day_of_month=c.get("day_of_month", "*"),
            month_of_year=c.get("month_of_year", "*"),
        )
    except Exception as e:  # noqa: BLE001
        log.error("trigger %s: bad cron config: %s", trigger.name, e)
        return False
    # Fire if the crontab is due relative to last_fired (or now if never fired).
    last = trigger.last_fired_at or (_now() - timedelta(days=1))
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    due, _next = cron.is_due(last)
    return bool(due)


def _datetime_due(trigger) -> bool:
    """One-shot at config.run_at (UTC). Caller sets consumed=True after firing."""
    raw = (trigger.config or {}).get("run_at")
    if not raw:
        return False
    try:
        run_at = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        log.error("trigger %s: bad run_at %r", trigger.name, raw)
        return False
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=timezone.utc)
    return _now() >= run_at


# ----- the periodic tick (registered in beat_schedule) -----

@shared_task(name="services.triggers.tick_triggers")
def tick_triggers() -> dict:
    """Dispatch all due triggers. Registered to run every ~30s via beat_schedule.
    Runs in a worker (not Beat), so table I/O never blocks Beat scheduling."""
    fired, scanned, errors = 0, 0, 0
    with _db() as db:
        from models.triggers import Trigger
        rows = (
            db.query(Trigger)
            .filter(Trigger.enabled.is_(True), Trigger.consumed.is_(False))
            .all()
        )
        for t in rows:
            try:
                if t.type == "interval":
                    if _interval_due(t):
                        _fire(db, t); fired += 1
                elif t.type == "cron":
                    if _cron_due(t):
                        _fire(db, t); fired += 1
                elif t.type == "datetime":
                    if _datetime_due(t):
                        _fire(db, t)
                        t.consumed = True   # one-shot
                        fired += 1
                elif t.type in ("watch_folder", "state_change"):
                    # Do NOT scan inline (would block the tick on FS I/O).
                    # Enqueue the scan as its own task on assets_low.
                    celery_app.send_task(
                        "services.triggers.scan_watch_trigger",
                        args=[t.id], queue="assets_low",
                    )
                    scanned += 1
                elif t.type == "manual":
                    pass  # only fires via POST /api/triggers/{id}/fire
                else:
                    log.warning("trigger %s: unknown type %r", t.name, t.type)
            except Exception as e:  # noqa: BLE001
                errors += 1
                log.exception("trigger %s tick failed: %s", t.name, e)
        db.commit()
    return {"fired": fired, "scan_enqueued": scanned, "errors": errors}


# ----- watch-folder / state-change scan (on assets_low, never in Beat) -----

@shared_task(name="services.triggers.scan_watch_trigger", queue="assets_low")
def scan_watch_trigger(trigger_id: int) -> dict:
    """Scan one watch_folder trigger's path for files that have gone stable, and
    fire the bound task once per new file. state_change predicates evaluated here
    too. Runs on assets_low so a slow/blocking scan never stalls Beat or the tick."""
    import os
    import glob as _glob

    fired = 0
    with _db() as db:
        from models.triggers import Trigger
        t = db.query(Trigger).filter(Trigger.id == trigger_id).first()
        if not t or not t.enabled:
            return {"fired": 0, "detail": "missing-or-disabled"}

        if t.type == "state_change":
            # Predicate evaluation is project-specific; v1 leaves a hook. A named
            # predicate in config['check'] would be resolved by a registry the
            # owning tool provides. For now: log and no-op so the type is valid.
            log.info("trigger %s: state_change check=%r (no predicate registry yet)",
                     t.name, (t.config or {}).get("check"))
            return {"fired": 0, "detail": "state_change-noop"}

        cfg = t.config or {}
        path = cfg.get("path")
        if not path or not os.path.isdir(path):
            log.warning("trigger %s: watch path missing: %r", t.name, path)
            return {"fired": 0, "detail": "no-path"}
        pattern = cfg.get("glob", "*")
        recursive = bool(cfg.get("recursive", False))
        stable_s = float(cfg.get("stability_seconds", 15))

        search = os.path.join(path, "**", pattern) if recursive else os.path.join(path, pattern)
        now_ts = _now().timestamp()
        for fp in _glob.glob(search, recursive=recursive):
            if not os.path.isfile(fp):
                continue
            key = (t.id, fp)
            if key in _WATCH_SEEN:
                continue
            try:
                mtime = os.path.getmtime(fp)
            except OSError:
                continue
            if (now_ts - mtime) < stable_s:
                continue  # still being written
            # Stable + new -> fire the bound task with the file path as a kwarg.
            tid = _fire(db, t, extra_kwargs={"input": fp})
            if tid:
                _WATCH_SEEN.add(key)
                fired += 1
        db.commit()
    return {"fired": fired}
