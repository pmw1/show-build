"""Failure report generator — writes self-contained markdown postmortems."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .rules import PLAYBOOK
from .store import Alert, JobState, Store


def _ts(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def _humansize(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def render_report(store: Store, job: JobState, verdict: str, rule_id: str) -> str:
    parts: list[str] = []
    parts.append(f"# SOT Failure Report — {job.temp_job_id}")
    parts.append(f"Verdict: {verdict}")
    parts.append(f"Rule: {rule_id}")
    parts.append(f"Generated: {datetime.now(tz=timezone.utc).isoformat(timespec='seconds')}")
    parts.append(f"Episode: {job.episode} | Slug: {job.slug} | Asset: {job.asset_id}")
    parts.append(f"Job type: {job.job_type or 'unknown'}")
    parts.append("")

    parts.append("## Summary")
    parts.append(_summary(store, job, rule_id))
    parts.append("")

    parts.append("## Timeline")
    parts.append("```")
    for ev in list(job.events):
        parts.append(_format_event(ev))
    parts.append("```")
    parts.append("")

    parts.append("## Job state at failure")
    parts.append("```json")
    parts.append(json.dumps(job.raw, indent=2, default=str))
    parts.append("```")
    parts.append("")

    parts.append("## Filesystem state")
    fs = store.fs_dirs.get(job.temp_job_id, {})
    if fs:
        parts.append(f"working_dir size: {_humansize(fs.get('size', 0))}")
        for path, meta in (fs.get("files", {}) or {}).items():
            parts.append(f"  {path}  {_humansize(meta['size'])}  mtime={_ts(meta['mtime'])}")
    else:
        parts.append("(no files observed for this job)")
    parts.append("")

    parts.append("## Workers that consume the relevant queue")
    queue_name = job.raw.get("queue", "media") if isinstance(job.raw, dict) else "media"
    for w in store.workers.values():
        if queue_name in (w.queues or []) or not w.queues:
            age = int(time.time() - w.last_heartbeat) if w.last_heartbeat else -1
            parts.append(f"  - {w.name}  state={w.state}  hb_age={age}s  active={w.active}  ✓{w.succeeded}  ✗{w.failed}")
    parts.append("")

    parts.append("## Suggested next steps")
    for step in PLAYBOOK.get(rule_id, ["(no playbook for this rule)"]):
        parts.append(f"- {step}")
    parts.append("")

    return "\n".join(parts)


def _summary(store: Store, job: JobState, rule_id: str) -> str:
    if rule_id == "task.lost":
        return (f"Celery task {job.celery_task_id[:8]} was sent but no worker "
                f"emitted task-received. Job stuck at phase={job.current_phase!r}.")
    if rule_id == "phase.stuck":
        elapsed = int(time.time() - job.last_phase_change) if job.last_phase_change else -1
        return f"Phase {job.current_phase!r} unchanged for {elapsed}s with status=processing."
    if rule_id == "job.ghost-failed":
        return "DB row marked failed but no worker emitted task-failed event."
    if rule_id == "job.mount-divergence":
        return ("Worker reports upload file missing, but FS observer sees the file. "
                "Likely NFS mount divergence between server and worker host.")
    return f"Job classified as failure by rule {rule_id}."


def _format_event(ev: dict) -> str:
    src = ev.get("source", "?")
    ts = _ts(ev.get("ts", 0)) if ev.get("ts") else "??:??:??.???"
    if src == "DB":
        row = ev.get("row", {})
        return f"{ts}  DB      status={row.get('status','?')} phase={row.get('current_phase','?')} err={row.get('error_message','-')[:80] if row.get('error_message') else '-'}"
    if src == "CELERY":
        t = ev.get("type", "?")
        host = ev.get("hostname", "")
        return f"{ts}  CELERY  {t:<16}  {ev.get('task_id','')[:8]}  {host}"
    if src == "FS":
        return f"{ts}  FS      {ev.get('action','?'):<8}  {ev.get('path','')}  ({_humansize(ev.get('size', 0))})"
    if src == "HTTP":
        return f"{ts}  HTTP    {ev.get('method','?')} {ev.get('path','?')} → {ev.get('status','?')}"
    if src == "WORKER":
        return f"{ts}  WORKER  {ev.get('text','')}"
    return f"{ts}  {src:<7} {ev}"


def write_report(store: Store, job: JobState, alert: Alert, dest_dir: str | None = None) -> str:
    dest_dir = dest_dir or os.environ.get("SOT_TRACE_DATA_DIR", "/var/log/sot-trace") + "/reports"
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromtimestamp(alert.ts, tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_rule = alert.rule_id.replace(".", "-")
    fname = f"{job.temp_job_id}__{stamp}__{safe_rule}.md"
    path = Path(dest_dir) / fname
    path.write_text(render_report(store, job, alert.severity.upper(), alert.rule_id))
    return str(path)
