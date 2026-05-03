"""Polling-based postgres source — read-only.

Polls sot_processing_jobs every second for rows whose updated_at is newer
than the last seen high-water mark. Emits a {source: 'DB'} event per row.
No triggers, no schema changes.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time

import psycopg

log = logging.getLogger("sot-trace.pg")

POLL_SECONDS = 1.0


async def run(queue: asyncio.Queue, dsn: str | None = None) -> None:
    dsn = dsn or os.environ.get(
        "SOT_TRACE_DSN",
        "host=show-build-postgres port=5432 dbname=showbuild user=showbuild password=showbuild",
    )
    high_water = None
    backoff = 1.0
    while True:
        try:
            async with await psycopg.AsyncConnection.connect(dsn) as conn:
                backoff = 1.0
                # First connect: leave high_water as-is; the inner loop's else-branch
            # will fetch rows from the last 6h on the first iteration.
                while True:
                    async with conn.cursor() as cur:
                        if high_water:
                            await cur.execute(
                                """
                                SELECT temp_job_id, asset_id, slug, episode, job_type,
                                       status, current_phase, error_message, celery_task_id,
                                       created_at, updated_at
                                FROM sot_processing_jobs
                                WHERE updated_at > %s
                                ORDER BY updated_at
                                """,
                                (high_water,),
                            )
                        else:
                            await cur.execute(
                                """
                                SELECT temp_job_id, asset_id, slug, episode, job_type,
                                       status, current_phase, error_message, celery_task_id,
                                       created_at, updated_at
                                FROM sot_processing_jobs
                                WHERE created_at > NOW() - INTERVAL '6 hours'
                                ORDER BY updated_at
                                """
                            )
                        rows = await cur.fetchall()
                        cols = [d.name for d in cur.description]

                    for row in rows:
                        d = dict(zip(cols, row))
                        ts = d["updated_at"].timestamp() if d.get("updated_at") else time.time()
                        if not high_water or d["updated_at"] > high_water:
                            high_water = d["updated_at"]
                        await queue.put({
                            "source": "DB",
                            "type": "row",
                            "ts": ts,
                            "job_id": d["temp_job_id"],
                            "row": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in d.items()},
                        })
                    await asyncio.sleep(POLL_SECONDS)
        except Exception as e:
            log.warning("postgres source error: %r — reconnecting in %.1fs", e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
