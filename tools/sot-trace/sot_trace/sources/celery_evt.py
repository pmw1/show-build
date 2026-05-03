"""Celery events source — pure consumer.

Subscribes to the celery event stream broadcast by workers. Emits
{source: 'CELERY', type: 'task-sent'/'task-received'/...} events.
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import time

log = logging.getLogger("sot-trace.celery")


def _run_receiver(loop: asyncio.AbstractEventLoop, queue: asyncio.Queue, broker_url: str, job_lookup: dict[str, str]) -> None:
    """Run celery's blocking receiver in a thread, push events into asyncio queue."""
    from celery import Celery  # imported here to keep import-time light

    app = Celery(broker=broker_url)

    def push(ev: dict) -> None:
        # Translate celery event → store event
        evt_type = ev.get("type", "")
        task_id = ev.get("uuid") or ev.get("task_id") or ""
        ev_out = {
            "source": "CELERY",
            "type": evt_type,
            "ts": ev.get("timestamp") or time.time(),
            "task_id": task_id,
            "hostname": ev.get("hostname", ""),
            "raw": ev,
        }
        # Best-effort job correlation: task args may carry temp_job_id
        # We also keep a task_id→job_id map populated by the DB source so any
        # later events can be correlated even without args.
        args = ev.get("args", "")
        if isinstance(args, str) and "sot_2" in args:
            # crude but effective; DB source still authoritative
            for tok in args.replace("'", " ").replace('"', " ").split():
                if tok.startswith("sot_"):
                    ev_out["job_id"] = tok
                    job_lookup[task_id] = tok
                    break
        if "job_id" not in ev_out and task_id in job_lookup:
            ev_out["job_id"] = job_lookup[task_id]

        # numeric extras for store
        if evt_type == "worker-heartbeat":
            ev_out["active"] = ev.get("active", 0)
            ev_out["loadavg"] = ev.get("loadavg", [0, 0, 0])

        asyncio.run_coroutine_threadsafe(queue.put(ev_out), loop)

    while True:
        try:
            with app.connection() as conn:
                recv = app.events.Receiver(conn, handlers={"*": lambda ev: push(ev)})
                recv.capture(limit=None, timeout=None, wakeup=True)
        except Exception as e:
            log.warning("celery receiver error: %r — retrying in 5s", e)
            time.sleep(5)


async def run(queue: asyncio.Queue, broker_url: str | None = None) -> None:
    broker_url = broker_url or os.environ.get("SOT_TRACE_BROKER", "redis://192.168.51.223:6379/0")
    job_lookup: dict[str, str] = {}
    loop = asyncio.get_running_loop()
    t = threading.Thread(target=_run_receiver, args=(loop, queue, broker_url, job_lookup), daemon=True)
    t.start()
    while True:
        await asyncio.sleep(60)
