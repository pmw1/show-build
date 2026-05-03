"""In-memory store for jobs, workers, events, and alerts.

All sources push dicts onto a single asyncio.Queue. The store fans them
into per-job event lists, per-worker state, and a global alert ring.
Nothing here writes back to any external system.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobState:
    temp_job_id: str
    asset_id: str = ""
    slug: str = ""
    episode: str = ""
    job_type: str = ""
    status: str = "unknown"
    current_phase: str = ""
    error_message: str = ""
    celery_task_id: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    last_phase_change: float = 0.0
    worker: str = ""           # populated from celery task-received
    events: deque = field(default_factory=lambda: deque(maxlen=500))
    raw: dict = field(default_factory=dict)

    def add_event(self, ev: dict) -> None:
        self.events.append(ev)


@dataclass
class WorkerState:
    name: str                            # e.g. "assets_worker@prefect"
    hostname: str = ""
    container: str = ""
    queues: list[str] = field(default_factory=list)
    state: str = "unknown"               # online/active/degraded/offline
    last_heartbeat: float = 0.0
    first_seen: float = 0.0
    active: int = 0                      # currently running tasks
    succeeded: int = 0
    failed: int = 0
    lost: int = 0
    load_history: deque = field(default_factory=lambda: deque(maxlen=60))
    cpu: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass
class Alert:
    ts: float
    severity: str       # info/warn/error/critical
    rule_id: str
    job_id: str
    message: str
    payload: dict = field(default_factory=dict)


class Store:
    def __init__(self, mem_alerts: int = 500) -> None:
        self.queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=10_000)
        self.jobs: dict[str, JobState] = {}
        self.workers: dict[str, WorkerState] = {}
        self.alerts: deque[Alert] = deque(maxlen=mem_alerts)
        self.fs_dirs: dict[str, dict] = {}      # job_id -> {size, mtime, files}
        self.queue_depths: dict[str, int] = defaultdict(int)
        self.start_ts = time.time()
        self.paused = False
        # for change broadcasts
        self.version = 0

    # ---------- ingestion ----------
    async def consume_forever(self) -> None:
        while True:
            ev = await self.queue.get()
            if self.paused:
                continue
            try:
                self._dispatch(ev)
                self.version += 1
            except Exception as e:  # observer must never crash on bad input
                self.alerts.append(Alert(
                    ts=time.time(), severity="warn", rule_id="ingest.error",
                    job_id="", message=f"ingest error: {e!r}",
                    payload={"event": ev},
                ))

    def _dispatch(self, ev: dict) -> None:
        kind = ev.get("source")
        if kind == "DB":
            self._apply_db(ev)
        elif kind == "CELERY":
            self._apply_celery(ev)
        elif kind == "FS":
            self._apply_fs(ev)
        elif kind == "HTTP":
            self._apply_http(ev)
        elif kind == "WORKER":
            self._apply_worker_log(ev)
        # always append to job timeline if we can correlate
        jid = ev.get("job_id")
        if jid and jid in self.jobs:
            self.jobs[jid].add_event(ev)

    def _job(self, jid: str) -> JobState:
        if jid not in self.jobs:
            self.jobs[jid] = JobState(temp_job_id=jid, created_at=time.time())
        return self.jobs[jid]

    def _apply_db(self, ev: dict) -> None:
        row = ev.get("row", {})
        jid = row.get("temp_job_id") or ev.get("job_id")
        if not jid:
            return
        j = self._job(jid)
        new_phase = row.get("current_phase", j.current_phase)
        # Use the row's own updated_at as the phase-change timestamp so that
        # historical stuck jobs register correctly during backfill.
        ev_ts = float(ev.get("ts") or time.time())
        first_seen = not j.current_phase
        if new_phase != j.current_phase:
            j.last_phase_change = ev_ts if first_seen else time.time()
        for k in ("asset_id", "slug", "episode", "job_type", "status",
                  "current_phase", "error_message", "celery_task_id"):
            if k in row and row[k] is not None:
                setattr(j, k, row[k])
        j.updated_at = ev_ts
        j.raw = row

    def _apply_celery(self, ev: dict) -> None:
        evt_type = ev.get("type", "")
        worker = ev.get("hostname") or ev.get("worker") or ""
        if worker:
            w = self.workers.setdefault(worker, WorkerState(name=worker))
            if not w.first_seen:
                w.first_seen = time.time()
            if evt_type == "worker-heartbeat":
                w.last_heartbeat = time.time()
                w.state = "online"
                w.active = ev.get("active", w.active)
                w.cpu = ev.get("loadavg", [0])[0] if ev.get("loadavg") else w.cpu
                w.load_history.append(w.cpu)
                if ev.get("active", 0) > 0:
                    w.state = "active"
            elif evt_type == "worker-online":
                w.state = "online"
                w.first_seen = time.time()
            elif evt_type == "worker-offline":
                w.state = "offline"
            elif evt_type == "task-received":
                w.active += 1
                # correlate task to job
                jid = ev.get("job_id")
                if jid:
                    self._job(jid).worker = worker
            elif evt_type == "task-succeeded":
                w.succeeded += 1
                w.active = max(0, w.active - 1)
            elif evt_type == "task-failed":
                w.failed += 1
                w.active = max(0, w.active - 1)

    def _apply_fs(self, ev: dict) -> None:
        jid = ev.get("job_id")
        if not jid:
            return
        d = self.fs_dirs.setdefault(jid, {"files": {}})
        path = ev.get("path", "")
        action = ev.get("action", "")
        if action == "modified" or action == "created":
            d["files"][path] = {"size": ev.get("size", 0), "mtime": ev.get("mtime", time.time())}
        elif action == "deleted":
            d["files"].pop(path, None)
        d["size"] = sum(f["size"] for f in d["files"].values())
        d["mtime"] = max((f["mtime"] for f in d["files"].values()), default=0)

    def _apply_http(self, ev: dict) -> None:
        # Just appended to timeline by caller
        pass

    def _apply_worker_log(self, ev: dict) -> None:
        # Just appended to timeline by caller
        pass

    # ---------- queries ----------
    def jobs_sorted(self, limit: int = 50, only_active: bool = False) -> list[JobState]:
        rows = list(self.jobs.values())
        if only_active:
            rows = [r for r in rows if r.status in ("processing", "queued", "unknown")]

        def keyf(j: JobState) -> tuple:
            active = j.status in ("processing", "queued", "unknown")
            failed = j.status == "failed"
            # active first, then failed, then everything else; recent first
            return (0 if active else (1 if failed else 2), -j.updated_at)

        rows.sort(key=keyf)
        return rows[:limit]

    def add_alert(self, alert: Alert) -> None:
        self.alerts.append(alert)
