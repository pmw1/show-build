"""Anomaly detection rules — phase-agnostic, transition-based.

Each rule is a function taking (Store, now) and returning a list[Alert].
None of them mention specific phase names. New phases require zero edits.
"""
from __future__ import annotations

import time
from .store import Alert, Store

# Default thresholds (seconds). Per-job-type overrides come from learned p95.
STUCK_FLOOR = 180          # phase unchanged this long → suspect
TASK_LOST_AFTER = 30       # task-sent w/o received this long → lost
WORKER_HEARTBEAT_DEAD = 60 # heartbeat stale this long → offline


def _has_event(job, kind: str, evt_type: str | None = None) -> bool:
    for ev in job.events:
        if ev.get("source") != kind:
            continue
        if evt_type is None or ev.get("type") == evt_type:
            return True
    return False


def _last_event_ts(job, kind: str, evt_type: str | None = None) -> float:
    for ev in reversed(job.events):
        if ev.get("source") != kind:
            continue
        if evt_type is None or ev.get("type") == evt_type:
            return float(ev.get("ts", 0))
    return 0.0


def rule_task_lost(store: Store, now: float) -> list[Alert]:
    out = []
    for j in store.jobs.values():
        if j.status not in ("processing", "queued"):
            continue
        sent_ts = _last_event_ts(j, "CELERY", "task-sent")
        recv_ts = _last_event_ts(j, "CELERY", "task-received")
        if sent_ts and not recv_ts and (now - sent_ts) > TASK_LOST_AFTER:
            out.append(Alert(
                ts=now, severity="critical", rule_id="task.lost",
                job_id=j.temp_job_id,
                message=f"task {j.celery_task_id[:8]} sent {int(now - sent_ts)}s ago, no worker received",
                payload={"queue": j.raw.get("queue", "media")},
            ))
    return out


def rule_phase_stuck(store: Store, now: float) -> list[Alert]:
    out = []
    for j in store.jobs.values():
        if j.status != "processing":
            continue
        if not j.last_phase_change:
            continue
        elapsed = now - j.last_phase_change
        if elapsed > STUCK_FLOOR:
            out.append(Alert(
                ts=now, severity="warn", rule_id="phase.stuck",
                job_id=j.temp_job_id,
                message=f"phase {j.current_phase!r} unchanged for {int(elapsed)}s",
            ))
    return out


def rule_ghost_failed(store: Store, now: float) -> list[Alert]:
    """status=failed but no celery task-failed event ever observed."""
    out = []
    for j in store.jobs.values():
        if j.status != "failed":
            continue
        if _has_event(j, "CELERY", "task-failed"):
            continue
        if _has_event(j, "CELERY", "task-sent"):
            out.append(Alert(
                ts=now, severity="error", rule_id="job.ghost-failed",
                job_id=j.temp_job_id,
                message="DB says failed but no worker emitted task-failed",
            ))
    return out


def rule_file_not_found_with_fs_present(store: Store, now: float) -> list[Alert]:
    out = []
    for j in store.jobs.values():
        if "Upload file not found" not in (j.error_message or ""):
            continue
        fs = store.fs_dirs.get(j.temp_job_id, {})
        if fs.get("files"):
            out.append(Alert(
                ts=now, severity="error", rule_id="job.mount-divergence",
                job_id=j.temp_job_id,
                message="Worker says file missing but FS observer sees it — NFS mount divergence?",
                payload={"fs_size": fs.get("size", 0)},
            ))
    return out


def rule_worker_dead(store: Store, now: float) -> list[Alert]:
    out = []
    for w in store.workers.values():
        if not w.last_heartbeat:
            continue
        if w.state == "offline":
            continue
        if (now - w.last_heartbeat) > WORKER_HEARTBEAT_DEAD:
            out.append(Alert(
                ts=now, severity="error", rule_id="worker.dead",
                job_id="", message=f"worker {w.name} no heartbeat for {int(now - w.last_heartbeat)}s",
            ))
    return out


ALL_RULES = [
    rule_task_lost,
    rule_phase_stuck,
    rule_ghost_failed,
    rule_file_not_found_with_fs_present,
    rule_worker_dead,
]


def run_rules(store: Store) -> list[Alert]:
    now = time.time()
    fresh = []
    for rule in ALL_RULES:
        try:
            fresh.extend(rule(store, now))
        except Exception as e:  # rules must not crash the observer
            fresh.append(Alert(
                ts=now, severity="warn", rule_id="rule.error",
                job_id="", message=f"rule {rule.__name__} crashed: {e!r}",
            ))
    return fresh


# Suggested next steps per rule (used in failure reports)
PLAYBOOK = {
    "task.lost": [
        "Check celery routes: `celery -A celery_app inspect active_queues`",
        "Verify both workers consuming `media` queue are alive and not deadlocked",
        "Inspect Redis broker queue length: `redis-cli -n 0 llen media`",
        "Reprocess the asset: POST /api/sot/reprocess/{asset_id}",
    ],
    "phase.stuck": [
        "Check the assigned worker's logs: `docker logs <worker>` filtered by job_id",
        "Verify external dependencies for that phase (whisper DNS, ffmpeg path, NFS mount)",
        "If retry-safe: revoke the task and reprocess",
    ],
    "job.ghost-failed": [
        "Look in server logs for non-worker writes to sot_processing_jobs",
        "Possible double-dispatch race; check celery_cleanup.py logic",
    ],
    "job.mount-divergence": [
        "ssh to the worker host and verify NFS mount: `mountpoint /mnt/sync`",
        "Pin SOT processing to one host by adding a host-specific queue route",
        "Add wait-for-file retry at top of process_sot_video_multi_phase",
    ],
    "worker.dead": [
        "`docker ps | grep <worker>` — is the container running?",
        "`docker logs <worker> --tail 100` — look for crash trace",
        "Restart: `docker compose restart <worker>`",
    ],
}
