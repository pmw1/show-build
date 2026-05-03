"""Filesystem source — read-only inotify watcher on the working dir.

Emits {source: 'FS', action: 'created'/'modified'/'deleted', path, size, mtime}
correlated to job_id by stripping the directory name.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from pathlib import Path

log = logging.getLogger("sot-trace.fs")

JOB_DIR_RE = re.compile(r"sot_\d{8}_\d{6}_[0-9a-f]+|vo_\d{8}_\d{6}_[0-9a-f]+")


def _job_id_from_path(p: str) -> str | None:
    m = JOB_DIR_RE.search(p)
    return m.group(0) if m else None


async def run(queue: asyncio.Queue, root: str | None = None) -> None:
    root = root or os.environ.get("SOT_TRACE_FS_ROOT", "/shared_media/preproc/working")
    rp = Path(root)
    if not rp.exists():
        log.warning("FS root not found: %s — disabling FS source", root)
        return

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        log.warning("watchdog not installed — falling back to mtime polling")
        await _poll_loop(queue, rp)
        return

    loop = asyncio.get_running_loop()

    class Handler(FileSystemEventHandler):
        def _emit(self, event_path: str, action: str) -> None:
            jid = _job_id_from_path(event_path)
            if not jid:
                return
            try:
                st = Path(event_path).stat()
                size, mtime = st.st_size, st.st_mtime
            except FileNotFoundError:
                size, mtime = 0, time.time()
            ev = {
                "source": "FS",
                "action": action,
                "ts": time.time(),
                "job_id": jid,
                "path": event_path,
                "size": size,
                "mtime": mtime,
            }
            asyncio.run_coroutine_threadsafe(queue.put(ev), loop)

        def on_created(self, event):
            if not event.is_directory:
                self._emit(event.src_path, "created")

        def on_modified(self, event):
            if not event.is_directory:
                self._emit(event.src_path, "modified")

        def on_deleted(self, event):
            if not event.is_directory:
                self._emit(event.src_path, "deleted")

    obs = Observer()
    obs.schedule(Handler(), str(rp), recursive=True)
    obs.start()
    try:
        while True:
            await asyncio.sleep(60)
    finally:
        obs.stop()
        obs.join(timeout=3)


async def _poll_loop(queue: asyncio.Queue, root: Path) -> None:
    seen: dict[str, tuple[int, float]] = {}
    while True:
        try:
            for sub in root.iterdir():
                if not sub.is_dir():
                    continue
                jid = _job_id_from_path(sub.name)
                if not jid:
                    continue
                for f in sub.iterdir():
                    if not f.is_file():
                        continue
                    st = f.stat()
                    key = str(f)
                    prev = seen.get(key)
                    if prev != (st.st_size, st.st_mtime):
                        action = "modified" if prev else "created"
                        seen[key] = (st.st_size, st.st_mtime)
                        await queue.put({
                            "source": "FS", "action": action,
                            "ts": time.time(), "job_id": jid,
                            "path": key, "size": st.st_size, "mtime": st.st_mtime,
                        })
        except Exception as e:
            log.warning("fs poll error: %r", e)
        await asyncio.sleep(2.0)
