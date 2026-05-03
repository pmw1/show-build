# sot-trace

Read-only TUI observer for the SOT processing pipeline. Watches Postgres,
Celery events, and the working filesystem; surfaces stuck/lost/failed jobs;
writes self-contained markdown postmortems.

## Two modes

- **Daemon** (always-on container) — silently records events, runs anomaly
  rules, writes failure reports to `data/reports/*.md`, persists alert
  history to `data/alerts.db`.
- **TUI** (on-demand) — full-screen ncurses-style dashboard. Worker strip
  with mouse-clickable cards, jobs table, live timeline, alerts.

## Run

```bash
# Daemon (already in docker-compose)
docker compose up -d sot-trace
docker logs -f show-build-sot-trace

# Open the TUI inside the running container
docker exec -it show-build-sot-trace sot-trace tui

# One-shot report from the host
docker exec show-build-sot-trace sot-trace report sot_20260424_231423_ae05197a
```

## Keys

| Key   | Action                          |
|-------|---------------------------------|
| ↑ ↓   | Select a job                    |
| Click | Open worker detail (on a card)  |
| F     | Toggle failed-only filter       |
| p     | Pause/resume ingestion          |
| c     | Clear in-memory alerts          |
| r     | Manual report for selected job  |
| q     | Quit                            |

## Anomaly rules (v1)

| Rule                       | Severity  | Triggers report? |
|----------------------------|-----------|------------------|
| `task.lost`                | critical  | yes              |
| `phase.stuck`              | warn      | no               |
| `job.ghost-failed`         | error     | yes              |
| `job.mount-divergence`     | error     | yes              |
| `worker.dead`              | error     | yes              |

## Read-only safety

- Postgres: `SELECT` only. Polled every 1s, no schema changes.
- Redis: celery event consumer; never publishes.
- Filesystem: working dir mounted `:ro`.
- No docker exec, no `--privileged`, no app code modification.

## Layout (where things live)

```
tools/sot-trace/
├── pyproject.toml
├── Dockerfile
├── README.md
└── sot_trace/
    ├── __main__.py        # CLI: tui | daemon | report
    ├── store.py           # in-memory event store
    ├── ui.py              # textual app, worker strip, modal detail
    ├── colors.py          # color/symbol scheme
    ├── rules.py           # anomaly detection (phase-agnostic)
    ├── reports.py         # markdown postmortem generator
    └── sources/
        ├── pg.py          # postgres poller
        ├── celery_evt.py  # celery event consumer
        └── fs.py          # inotify watcher on working dir
```

## Future phases — agnostic by design

The tool never references specific phase names. Add `phase2.5_caption_burn`
to the worker code and `sot-trace` picks it up automatically: phase
denominators are computed from observed completions per `job_type`, and
all anomaly rules reason about transitions/timeouts rather than named phases.
