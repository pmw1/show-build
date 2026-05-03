# LLM Auto-Description Implementation Plan

## Overview

Automated background generation of segment tone classifications and descriptions using local Ollama LLMs. The system runs a Celery Beat sweeper every 60 seconds that identifies eligible segments, classifies their editorial tone, and generates descriptions — all without user intervention. Users can opt segments/episodes in or out, regenerate with feedback, and receive notifications on completion.

---

## Current State (What's Already Built)

| Component | Status | Location |
|---|---|---|
| Tone classifier (`classify_segment_tone`) | Built, tested | `app/services/auto_description_service.py` |
| Description generator (`generate_segment_description`) | Built, tested | `app/services/auto_description_service.py` |
| Regenerate with feedback (`regenerate_segment_description`) | Built, tested | `app/services/auto_description_service.py` |
| LLM output cleaner (`clean_llm_description`) | Built | `app/services/auto_description_service.py` |
| Sweeper function (`sweep_segments_for_auto_generation`) | Written, not wired as Celery task | `app/services/auto_description_service.py` |
| DB columns: `tone`, `tone_rationale`, `tone_confidence` | Migrated (g006) | `rundown_items` table |
| DB columns: `llm_generated_fields`, `auto_generate_attempts` | Migrated (g006) | `rundown_items` table |
| DB column: `auto_generate_enabled` | Migrated (g006) | `episodes` table |
| DB column: `description_gen_history` | Migrated (g007) | `rundown_items` table |
| Sidebar tone field (badges + combobox) | Built | `MetadataPanel.vue` |
| Sidebar description auto-resize | Built | `MetadataPanel.vue` |
| Regenerate button + async modal | Built | `MetadataPanel.vue` |
| Purple LLM-generated field highlighting | Built | `MetadataPanel.vue` |
| Tone palette settings UI | Built | `GenerationSettings.vue` |
| Segment description prompt template UI | Built | `GenerationSettings.vue` |
| Generation history tracking | Built | `auto_description_service.py` |

---

## What Needs to Be Built

### Part 1: Database — New Column + Migration

**File**: `app/alembic/versions/g008_add_auto_description_enabled.py`

Add `auto_description_enabled BOOLEAN DEFAULT TRUE` to `rundown_items`. This is the **per-segment** opt-in/out flag that controls whether the sweeper can auto-generate a description for this specific segment.

The episode-level `auto_generate_enabled` already exists from migration g006.

### Part 2: SQLAlchemy Model Update

**File**: `app/models/episode.py`

Add to the `RundownItem` class (after `auto_generate_attempts`):
```python
auto_description_enabled = Column(Boolean, default=True, nullable=False, server_default="true")
```

### Part 3: Convert Functions to Celery Tasks

**File**: `app/services/auto_description_service.py`

1. Import `shared_task` from celery
2. Decorate the three main functions:
   ```python
   @shared_task(name="services.auto_description_service.classify_segment_tone")
   def classify_segment_tone(asset_id: str) -> dict:

   @shared_task(name="services.auto_description_service.generate_segment_description")
   def generate_segment_description(asset_id: str) -> dict:

   @shared_task(name="services.auto_description_service.sweep_segments_for_auto_generation")
   def sweep_segments_for_auto_generation():
   ```
3. Update the sweeper SQL query:
   - **Remove**: `AND NOT COALESCE(ri.llm_generated_fields, '[]'::jsonb) @> '"description"'`
   - **Add**: `AND COALESCE(ri.auto_description_enabled, TRUE) = TRUE`
4. Add Ollama health check at the top of the sweeper (quick GET to `/api/tags`; skip tick if it fails)

### Part 4: Add `llm_content` Queue + Beat Schedule

The queue is named **`llm_content`** (not `descriptions`) because this worker will expand to handle all LLM-generated content types: segment descriptions now, then episode descriptions, image descriptions, social media copy, etc. One queue, one worker, one-at-a-time concurrency.

**File**: `app/celery_app.py`

1. Add queue definition:
   ```python
   'llm_content': {
       'exchange': 'llm_content',
       'routing_key': 'llm_content',
   }
   ```
2. Add task route:
   ```python
   "services.auto_description_service.*": {"queue": "llm_content"}
   ```

**File**: `app/celery_cleanup.py`

3. Add to `beat_schedule` dict:
   ```python
   'llm-content-sweep-every-60s': {
       'task': 'services.auto_description_service.sweep_segments_for_auto_generation',
       'schedule': 60.0,
   }
   ```

### Part 5: Dedicated `llm-content-worker` on Prefect

A **new, separate worker** (not added to the existing assets worker) named `llm-content-worker@prefect`:

- Consumes ONLY the `llm_content` queue
- Runs with `--concurrency=1` (single-stream LLM calls — never overlaps)
- Named explicitly so `docker ps` / Celery inspect shows what it does

**Implementation** — new service in `docker-compose.yml`:
```yaml
llm-content-worker:
  build: .
  command: >
    celery -A celery_app worker
    -Q llm_content
    --hostname=llm-content-worker@prefect
    --concurrency=1
    --max-tasks-per-child=10
  volumes: [same as server]
  environment: [same as server]
  depends_on: [postgres]
```

**Future expansion**: When episode descriptions, image descriptions, social media copy tasks are added, they also route to `llm_content`. The sweeper can be extended with a priority system or separate sweep functions each on their own Beat schedule — all feeding the same single-concurrency queue.

### Part 6: API — Expose `auto_description_enabled`

**File**: `app/routers/episodes/rundown_router.py`

1. Add to GET rundown response dict:
   ```python
   "auto_description_enabled": getattr(item, 'auto_description_enabled', True)
   ```
2. Add to PATCH handler:
   ```python
   if 'auto_description_enabled' in item_data:
       item.auto_description_enabled = item_data['auto_description_enabled']
   ```
3. Add to bulk save handler similarly

### Part 7: Per-Segment "Auto" Toggle in Sidebar

**File**: `disaffected-ui/src/components/content-editor/MetadataPanel.vue`

Add a small toggle button next to the Regen button on the description wrapper:
- Pill-shaped button labeled "Auto" with on/off icon
- **Purple** when on (`auto_description_enabled = true`), **grey** when off
- Click emits `update-segment-field` with `{ field: 'auto_description_enabled', value: !current }`
- Positioned bottom-left of the description wrapper (Regen is bottom-right)
- Default state controlled by generation settings (default: ON)

### Part 8: Per-Episode "Auto-Describe" Toggle in ShowInfoHeader

**File**: `disaffected-ui/src/components/content-editor/ShowInfoHeader.vue`

Add a compact toggle in the episode header area:
- `v-switch` or compact toggle labeled "Auto-Describe"
- Reads/writes `auto_generate_enabled` on the episode
- Emits via existing episode field update mechanism
- When OFF, the sweeper skips the **entire episode** regardless of per-segment toggles

**File**: `app/routers/episodes/crud_router.py` (or metadata router)

Ensure the episode update endpoint accepts and persists `auto_generate_enabled`.

### Part 9: User Notifications on Completion/Failure

**Backend** — `app/services/auto_description_service.py`

After each `generate_segment_description` or `classify_segment_tone` completes (success or failure), write a notification record:
```python
{
    "type": "llm_content",
    "content_type": "segment_description",   # or "segment_tone"
    "asset_id": asset_id,
    "segment_title": ctx.get('title', ''),
    "episode_number": ctx.get('episode_number', ''),
    "status": "success" | "failed",
    "message": "Description generated" | "Error: Ollama timeout",
    "timestamp": utcnow
}
```

Storage: existing Celery jobs table or a new `llm_notifications` table.

**Frontend** — `disaffected-ui/src/composables/useJobMonitor.js`

Extend the existing polling to fetch new LLM notifications. On new notification:
- **Success**: `notifyUserStandard('Description generated for "Supreme Court..."', NOTIFICATION_COLORS.SUCCESS, 4000)`
- **Failure**: `notifyUserStandard('Description failed for "Vermont Ice": timeout', NOTIFICATION_COLORS.ERROR, 6000)`

The toast appears wherever the user is since `StandardNotification` is mounted in `App.vue`.

---

## Sweeper Decision Logic (every 60 seconds)

```
TICK
│
├─ Is Ollama reachable? (GET /api/tags)
│  └─ NO → skip, try next tick
│
├─ PICK ONE EPISODE:
│  │  WHERE production_status IN ('draft', 'production')
│  │    AND auto_generate_enabled = TRUE
│  │  ORDER BY air_date ASC NULLS LAST
│
├─ PICK ONE SEGMENT in that episode:
│  │  WHERE type IN ('segment', 'interview', 'coldopen')
│  │    AND description IS NULL OR description = ''
│  │    AND auto_description_enabled = TRUE
│  │    AND LENGTH(script_content) >= 100 chars
│  │    AND updated_at < NOW() - 2 minutes (cool-down)
│  │    AND auto_generate_attempts < 3 (retry budget)
│  │  ORDER BY order_in_rundown ASC
│  │  LIMIT 1
│  └─ NONE FOUND → idle, try next tick
│
├─ INCREMENT auto_generate_attempts
│
├─ NEEDS TONE? (tone IS NULL or empty)
│  ├─ YES → classify_segment_tone(asset_id)
│  │         writes tone, tone_rationale, tone_confidence
│  │         adds 'tone' to llm_generated_fields
│  └─ NO → skip to description
│
├─ generate_segment_description(asset_id)
│    reads tone + segment content + prompt template
│    writes description
│    adds 'description' to llm_generated_fields
│    appends to description_gen_history
│    resets auto_generate_attempts to 0
│    sends success notification
│
└─ ON FAILURE → log error, send failure notification
     attempts stay incremented (retries on next tick if < 3)
```

---

## Architecture: One Queue, Many Content Types

The `llm_content` queue is intentionally generic. Segment descriptions are the first route through it. Future content types plug in without new queues or workers:

| Content Type | Sweeper Function | Status |
|---|---|---|
| Segment tone | `classify_segment_tone` | Built, tested |
| Segment description | `generate_segment_description` | Built, tested |
| Episode description | `generate_episode_description` | Future |
| Image description | `generate_image_description` | Future |
| Social media copy | `generate_social_copy` | Future |

Each gets its own Beat schedule entry (or a unified sweeper that rotates through types). All route to `llm_content`. The `concurrency=1` worker serializes them naturally. Priority between types is handled by sweep order, not queue priority.

---

## Runtime Architecture

```
┌─────────────────────────────────────────────────────┐
│  FARMHOUSE (192.168.51.223)                         │
│                                                     │
│  ┌─────────────┐  ┌──────────────────────────────┐  │
│  │ Celery Beat  │  │ Redis (broker + result)      │  │
│  │ (scheduler)  │──│ redis://:showbuild2025@:6379 │  │
│  └──────┬───────┘  └──────────────────────────────┘  │
│         │ dispatches task every 60s                   │
│         │ to 'llm_content' queue                     │
└─────────┼───────────────────────────────────────────┘
          │
          ▼ (via Redis)
┌─────────────────────────────────────────────────────┐
│  PREFECT (192.168.51.207)                           │
│                                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐ │
│  │ llm-content-worker   │  │ show-build-postgres   │ │
│  │ concurrency=1        │──│ PostgreSQL             │ │
│  │ queue: llm_content   │  └──────────────────────┘ │
│  └──────────┬───────────┘                           │
│             │ HTTP call                              │
│             ▼                                        │
│  ┌──────────────────────┐                           │
│  │ Ollama               │                           │
│  │ 192.168.51.197:11434 │                           │
│  └──────────────────────┘                           │
└─────────────────────────────────────────────────────┘
```

---

## Verification Checklist

1. Run migration `g008`: `alembic upgrade head`
2. Restart server: `docker compose restart server`
3. Start llm-content-worker: `docker compose up -d llm-content-worker`
4. Verify Beat picks up new schedule (check Farmhouse Beat logs)
5. Check prefect logs: `[sweep] Running auto-description sweep` every 60s
6. Test: segment with >100 chars content + empty description → auto-fills within ~2 minutes
7. Test: toggle "Auto" off on a segment → sweeper skips it
8. Test: toggle episode "Auto-Describe" off → sweeper skips all segments
9. Test: notification toast appears on successful generation
10. Test: notification toast appears on failure (stop Ollama, wait for sweep)
11. `npm run lint -- --fix` passes
