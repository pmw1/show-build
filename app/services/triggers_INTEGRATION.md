# Triggers — integration notes (for show-build to apply)

New files in this draft (`draft/triggers-g018` worktree):
- `app/alembic/versions/g018_triggers_table.py` — additive migration (down=c4e378d8259e).
- `app/models/triggers.py` — `Trigger` model + `TRIGGER_TYPES`.
- `app/services/triggers.py` — `tick_triggers` + `scan_watch_trigger` tasks.

## Two edits to `app/celery_app.py` (NOT made here — your file, your call)

### 1. Register the task module in `include=[...]`
Add `"services.triggers"` to the `include` list (alongside the existing services):

    include=[
        ...
        "services.triggers",        # <-- add
    ]

### 2. Add the periodic tick to `beat_schedule`
Add ONE entry next to the existing 4 (they stay untouched):

    'tick-triggers': {
        'task': 'services.triggers.tick_triggers',
        'schedule': 30.0,           # seconds; one tick of latency is the accepted tradeoff
    },

That's the whole wiring. No custom scheduler class (`-S ...`) — Beat keeps its
default scheduler and just enqueues `tick_triggers`, which does the table work in a
worker. So a table/DB error can never take down Beat scheduling (your #708 call).

## Routing note
- `tick_triggers` has no explicit queue → routes via default (`celery`/default).
  If you prefer it on a specific queue, add a route or a `queue=` on the task.
- `scan_watch_trigger` is pinned `queue='assets_low'` so blocking FS scans can't
  stall Beat or the tick (your #708 MUST-FIX-2).

## The triggers API router (YOURS to build)
Per #708 you own `app/triggers_router.py` with
GET/POST/PATCH/DELETE `/api/triggers` + POST `/api/triggers/{id}/fire`.
- `POST /fire` should call the same `_fire()` logic (or `tick`'s enqueue path) so a
  manual fire also lands in celery_job_log and stamps `last_task_id`.
- `manual`-type triggers ONLY ever fire via `/fire`.

## ALEMBIC HEAD — please verify before landing
`g018` sets `down_revision='c4e378d8259e'` per your directive (#723). A file-scan of
`versions/` ALSO showed `005_create_blueprint_templates` as an apparent head. Please
confirm `alembic heads` on live shows a SINGLE head = c4e378d8259e before applying;
if `005_*` is a real second head, g018 may need a merge or a different down_revision.

## Dependency
Trigger FIRING enqueues by name and logs via `register_celery_job` directly (works
today). When your enqueue-and-log ENDPOINT (#711) ships, `_fire()` can optionally be
pointed at it instead, but it is not required for triggers to function.
