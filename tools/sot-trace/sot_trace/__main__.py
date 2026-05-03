"""sot-trace entry point.

Subcommands:
  sot-trace tui       — full-screen TUI (default)
  sot-trace daemon    — record-only mode for the always-on container
  sot-trace report    — render a one-shot markdown report for a job_id
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sqlite3
import sys
import time
from pathlib import Path

import click

from .reports import write_report
from .rules import run_rules
from .sources import celery_evt as celery_src
from .sources import fs as fs_src
from .sources import pg as pg_src
from .store import Alert, Store

log = logging.getLogger("sot-trace")


# ──────────────── shared bootstrap ────────────────

async def _start_sources(store: Store, dsn: str | None, broker: str | None, fs_root: str | None) -> list[asyncio.Task]:
    return [
        asyncio.create_task(pg_src.run(store.queue, dsn=dsn), name="src.pg"),
        asyncio.create_task(celery_src.run(store.queue, broker_url=broker), name="src.celery"),
        asyncio.create_task(fs_src.run(store.queue, root=fs_root), name="src.fs"),
        asyncio.create_task(store.consume_forever(), name="store.consume"),
    ]


def _alert_seen_key(a: Alert) -> str:
    return f"{a.rule_id}:{a.job_id}"


async def _rules_loop(store: Store, on_alert) -> None:
    seen: set[str] = set()
    while True:
        try:
            for a in run_rules(store):
                k = _alert_seen_key(a)
                if k in seen:
                    continue
                seen.add(k)
                store.add_alert(a)
                try:
                    await on_alert(a)
                except Exception as e:
                    log.warning("on_alert failed: %r", e)
        except Exception as e:
            log.warning("rules loop error: %r", e)
        await asyncio.sleep(1.0)


def _data_dir() -> Path:
    p = Path(os.environ.get("SOT_TRACE_DATA_DIR", "/var/log/sot-trace"))
    p.mkdir(parents=True, exist_ok=True)
    (p / "reports").mkdir(parents=True, exist_ok=True)
    return p


def _open_alert_db(disk_alerts: int) -> sqlite3.Connection:
    db = sqlite3.connect(str(_data_dir() / "alerts.db"))
    db.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL, severity TEXT, rule_id TEXT,
            job_id TEXT, message TEXT, payload TEXT
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_job ON alerts(job_id)")
    db.commit()
    # trim
    db.execute(
        "DELETE FROM alerts WHERE id IN (SELECT id FROM alerts ORDER BY id DESC LIMIT -1 OFFSET ?)",
        (disk_alerts,),
    )
    db.commit()
    return db


# ──────────────── CLI ────────────────

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """sot-trace — read-only SOT pipeline observer."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(tui)


@cli.command()
@click.option("--dsn", default=None, help="Postgres DSN (env: SOT_TRACE_DSN)")
@click.option("--broker", default=None, help="Celery broker URL (env: SOT_TRACE_BROKER)")
@click.option("--fs-root", default=None, help="Working dir to watch (env: SOT_TRACE_FS_ROOT)")
@click.option("--mem-alerts", default=500, show_default=True, help="In-memory alert ring size")
@click.option("--disk-alerts", default=2000, show_default=True, help="On-disk alert retention")
def tui(dsn, broker, fs_root, mem_alerts, disk_alerts) -> None:
    """Launch the full-screen TUI."""
    from .ui import SotTraceApp

    store = Store(mem_alerts=mem_alerts)
    db = _open_alert_db(disk_alerts)

    async def on_alert(a: Alert) -> None:
        db.execute(
            "INSERT INTO alerts (ts, severity, rule_id, job_id, message, payload) VALUES (?,?,?,?,?,?)",
            (a.ts, a.severity, a.rule_id, a.job_id, a.message, str(a.payload)),
        )
        db.commit()
        if a.severity in ("error", "critical") and a.job_id and a.job_id in store.jobs:
            try:
                path = write_report(store, store.jobs[a.job_id], a)
                log.info("report written: %s", path)
            except Exception as e:
                log.warning("report write failed: %r", e)

    app = SotTraceApp(store)

    async def _runner() -> None:
        await _start_sources(store, dsn, broker, fs_root)
        asyncio.create_task(_rules_loop(store, on_alert), name="rules")
        await app.run_async()

    asyncio.run(_runner())


@cli.command()
@click.option("--dsn", default=None)
@click.option("--broker", default=None)
@click.option("--fs-root", default=None)
@click.option("--mem-alerts", default=500)
@click.option("--disk-alerts", default=2000)
def daemon(dsn, broker, fs_root, mem_alerts, disk_alerts) -> None:
    """Headless recorder. Runs forever, generates reports on failures."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    store = Store(mem_alerts=mem_alerts)
    db = _open_alert_db(disk_alerts)

    async def on_alert(a: Alert) -> None:
        db.execute(
            "INSERT INTO alerts (ts, severity, rule_id, job_id, message, payload) VALUES (?,?,?,?,?,?)",
            (a.ts, a.severity, a.rule_id, a.job_id, a.message, str(a.payload)),
        )
        db.commit()
        log.info("ALERT %s [%s] %s — %s", a.severity, a.rule_id, a.job_id, a.message)
        if a.severity in ("error", "critical") and a.job_id and a.job_id in store.jobs:
            try:
                path = write_report(store, store.jobs[a.job_id], a)
                log.info("report written: %s", path)
            except Exception as e:
                log.warning("report write failed: %r", e)

    async def _runner() -> None:
        tasks = await _start_sources(store, dsn, broker, fs_root)
        tasks.append(asyncio.create_task(_rules_loop(store, on_alert), name="rules"))
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: stop.done() or stop.set_result(None))
        await stop
        for t in tasks:
            t.cancel()

    asyncio.run(_runner())


@cli.command()
@click.argument("job_id")
@click.option("--dsn", default=None)
@click.option("--fs-root", default=None)
def report(job_id: str, dsn: str | None, fs_root: str | None) -> None:
    """Generate a one-shot report for an existing job_id (queries DB + FS on demand)."""
    import psycopg

    real_dsn = dsn or os.environ.get(
        "SOT_TRACE_DSN",
        "host=show-build-postgres port=5432 dbname=showbuild user=showbuild password=showbuild",
    )
    with psycopg.connect(real_dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM sot_processing_jobs WHERE temp_job_id = %s", (job_id,))
        row = cur.fetchone()
        if not row:
            click.echo(f"No job {job_id}", err=True)
            sys.exit(1)
        cols = [d.name for d in cur.description]
        d = dict(zip(cols, row))
    store = Store()
    store._apply_db({"source": "DB", "ts": time.time(), "job_id": job_id,
                     "row": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in d.items()}})

    # Synchronously scan the working dir for this job and feed FS events into the store
    fs_root = fs_root or os.environ.get("SOT_TRACE_FS_ROOT", "/shared_media/preproc/working")
    job_dir = Path(fs_root) / job_id
    if job_dir.exists():
        for f in job_dir.rglob("*"):
            if not f.is_file():
                continue
            try:
                st = f.stat()
            except OSError:
                continue
            store._apply_fs({
                "source": "FS", "action": "created",
                "ts": st.st_mtime, "job_id": job_id,
                "path": str(f), "size": st.st_size, "mtime": st.st_mtime,
            })

    a = Alert(ts=time.time(), severity="info", rule_id="manual",
              job_id=job_id, message="on-demand report")
    path = write_report(store, store.jobs[job_id], a)
    click.echo(path)


if __name__ == "__main__":
    cli()
