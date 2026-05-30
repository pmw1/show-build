# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Production Environment

- **Host**: `prefect` (192.168.51.238) — all show-build services run here
- **Frontend**: https://192.168.51.238:8091
- **Backend API**: https://192.168.51.238:8888
- **Containers**: `show-build-server`, `show-build-postgres`, `show-build-redis`
- **All URLs MUST use HTTPS** — no exceptions

## Mandatory Post-Change Actions

**After modifying Vue/JS files:**
```bash
cd disaffected-ui && npm run lint -- --fix
```

**After modifying backend Python files:**
```bash
docker compose restart server
```
Backend changes are NOT hot-reloaded. The container must restart.

## Inter-Claude Relay Coordination

Check relay on every user message:
```bash
curl -s 'http://192.168.51.223:8001/read?project=show-build&limit=5'
curl -s http://192.168.51.223:8001/announcements
```

Post updates when starting/completing work:
```bash
curl -X POST http://192.168.51.223:8001/write -H "Content-Type: application/json" \
  -d '{"content":"Your status","sender":"show-build-prefect","project":"show-build"}'
```

## Active Work Queue

**Check before starting any work:**
1. [`ACTIVE_WORK_QUEUE.md`](ACTIVE_WORK_QUEUE.md) — long-running initiatives
2. The unified todo list at `/api/todos` — short-lived tasks (see "Unified
   Task List" section below). Read it on session start; pay attention to
   `priority=high` and `priority=critical` items. The dashboard renders the
   same data at `/dashboard`.

Update task status as you complete work (PATCH `/api/todos/{id}`).

### Standing high-priority todos

These are large architectural changes that should be top-of-mind whenever
the related code is touched. If you're modifying these areas anyway,
**look at the linked plan first** and either advance the plan or note why
not in the todo description.

- **#24 — Replace polling with SSE for job status** ([plan](docs/SSE_JOB_STATUS_PLAN.md)).
  Per-cue-card + JobMonitor + SOT polling causes single-worker chokes
  (episode 0273 hit 5-13s loads on 2026-05-09; immediate fix was
  `WEB_CONCURRENCY=4`, durable fix is SSE). Phase 1 (SOT-job-status SSE)
  alone is the biggest UX win. Touch this if you're already working in
  `useJobMonitor.js`, `useSOTProcessing.js`, `PlaceholderCueCard.vue`, or
  any of the Celery task state-update paths.

- **#25 — Unify modal ESC behavior across all 27 modals**
  ([plan](docs/MODAL_ESC_UNIFICATION_PLAN.md)). Foundation already landed:
  `useModalStack` composable + global handler in `App.vue` + 5 previously-
  ESC-less modals patched. Phase 1 (~half day) converts the remaining 21
  modals from per-modal `addEventListener('keydown', ...)` to one-line
  `registerModalEsc(...)`. Touch this if you're already editing any modal
  in `components/modals/` or `components/content-editor/modals/`.

## Unified Task List (Dashboard Todo Panel)

All todos — from any user AND from Claude — live in one table (`user_todos`)
and one unified API under `/api/todos`. There is no longer a split between
"Claude tasks" and "user tasks"; the only distinction is the `created_by`
field on each row, which can be a username or `"claude"`.

**Canonical endpoints** (no auth required, permissive by design):
```
GET    /api/todos                 → all todos, sorted active→priority→newest
POST   /api/todos                 → create; body must include created_by
PATCH  /api/todos/{id}            → update any field (content/priority/status/etc.)
DELETE /api/todos/{id}            → delete
```

**POST body shape:**
```json
{
  "content":     "Task title",
  "description": "Optional details",
  "priority":    "low|normal|high|critical",
  "status":      "pending|in_progress|completed|on_hold",
  "created_by":  "kevin"   // or "claude", or any service name
}
```

**Claude's sync protocol** (what I use during sessions):
1. **Start of session** — read existing todos: `curl -sk http://localhost:8888/api/todos` (from inside the container) or `https://192.168.51.238:8888/api/todos` (from the host)
2. **Starting work** — POST with `created_by: "claude"` and `status: "in_progress"`
3. **Completing work** — PATCH the id to `status: "completed"`; the backend auto-fills `completed_at`
4. Keep the internal TaskCreate/TaskUpdate tools in sync with the dashboard — the dashboard is the single source of truth

**Legacy routes** (`/api/todos/claude` and `/api/todos/user`) are kept as
thin backward-compat wrappers but should NOT be used in new code. Use the
unified endpoints.

**Frontend** (`disaffected-ui/src/components/TodoPanel.vue`) renders the
unified list with: checkbox | task title (truncated, clickable for full
text) | priority chip | user chip (robot icon for Claude, account icon
for humans) | delete button. No tabs. A "Show completed" switch toggles
completed items in/out of view.

---

## Project Overview

Show-Build is a **database-first broadcast production platform** for the Disaffected media ecosystem. Web-based interface for managing episodes, rundowns, scripts, and media assets.

**Core principles:**
- PostgreSQL is the single source of truth for all content
- Filesystem is for media assets only (images, video, audio, graphics)
- Celery + Redis for async tasks (script generation, asset processing)
- MQTT has been removed — replaced by Celery

## Architecture

### Backend (FastAPI + Python)
- `app/main.py` — FastAPI app entry point (~238 lines): middleware, static mounts, router registration only
- `app/database.py` — PostgreSQL with SQLAlchemy ORM (shared by all services including auth)
- `app/auth/` — JWT auth with RBAC (`app/models_rbac.py`, `app/services/rbac_service.py`)
- `app/celery_app.py` — 7 task queues: assets_high, assets, assets_low, compilation, quotes, media, fsq
- `app/models/` — Domain-split SQLAlchemy models (enums, organization, episode, content, production, settings, jobs). `models_v2.py` is a backward-compat shim.
- `app/routers/` — Modularized router packages:
  - `routers/episodes/` — 8 sub-routers (crud, metadata, rundown, versioning, history, thumbnails, cues, media)
  - `routers/settings/` — 5 sub-routers (general, media_paths, interface, system, llm_identity)
  - `routers/whiteboard/` — 4 sub-routers (crud, media, social_media, node_links)
  - `routers/health_router.py`, `upload_router.py`, `legacy_router.py`, `misc_router.py`
- Legacy routers: `app/{feature}_router.py` — backward-compat shims re-exporting from `routers/` packages
- `app/services/` — All business logic services (including relocated rbac, housekeeping, asterisk, link_preview)

### Frontend (Vue 3 + Vuetify)
- `disaffected-ui/` — Vue 3 with Composition API, Vuetify 3
- `src/composables/` — shared state and behavior (Composition API)
  - `llm/` — LLM provider modules (`providers.js`, `quoteSplitting.js`)
  - `useContentSanitizer.js`, `useCollapseMode.js`, `useEditorPaste.js` — extracted from EditorPanel
  - `useEpisodeMetadata.js` — extracted from ContentEditor
  - `useRundownDragDrop.js` — extracted from RundownPanel
- `src/components/content-editor/cards/cue-types/` — per-type cue card components (FsqCueContent, SotCueContent, GfxCueContent)
- `src/utils/cueParser.js` — stateless markdown-to-segments parser
- `src/utils/themeColorMap.js` — centralized color system for segment types, statuses, cue types

### Key Documentation
- [`docs/EDITOR_PANEL_ARCHITECTURE.md`](docs/EDITOR_PANEL_ARCHITECTURE.md) — **READ BEFORE editing ContentEditor/EditorPanel**
- [`docs/SAVE_RELOAD_SPEC.md`](docs/SAVE_RELOAD_SPEC.md) — Save/reload system spec (authoritative)
- [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md) — Strategic decisions and rationale
- [`docs/EPISODE_DIRECTORY_STANDARD.md`](docs/EPISODE_DIRECTORY_STANDARD.md) — Media asset organization (authoritative)
- [`docs/RBAC_AUTHENTICATION_GUIDE.md`](docs/RBAC_AUTHENTICATION_GUIDE.md) — Complete RBAC reference
- [`docs/DASHBOARD_ANNOUNCEMENTS.md`](docs/DASHBOARD_ANNOUNCEMENTS.md) — Dashboard announcement creation
- [`docs/X_API_COMPLETE_REFERENCE.md`](docs/X_API_COMPLETE_REFERENCE.md) — X/Twitter API v2 reference
- [`docs/KEYBOARD_SHORTCUTS.md`](docs/KEYBOARD_SHORTCUTS.md) — Master keyboard shortcut reference. Runtime data lives in `disaffected-ui/src/data/keyboardShortcuts.js`; in-app help modal opens with `?` or `F1`. **When adding/changing a shortcut, update both the `.js` file and the `.md` file.**

## MetadataPanel LLM-Generated Field Highlighting

The right sidebar (`disaffected-ui/src/components/content-editor/MetadataPanel.vue`)
visually distinguishes LLM-written field values from human-written ones by
rendering LLM-filled inputs in purple italic (`#7e57c2`). This is wired up
**once**, in a single bottleneck — no per-field template annotations.

**How it lights up:**
1. The rundown item carries an array field `llm_generated_fields: string[]`
   listing field names the LLM filled in (e.g. `["description", "title"]`).
   This must be persisted on the rundown item by whatever generation code
   writes the field.
2. `MetadataPanel.vue` has one ref (`metadataRootRef`) on its root div and a
   single `watch` over `props.item` + `llm_generated_fields` that:
   - clears any stale `.llm-generated` classes under the root,
   - for each field in `llm_generated_fields`, queries all `.sidebar-field
     input, .sidebar-field textarea` descendants and finds the first whose
     current `.value` equals `item[field]`,
   - adds the `llm-generated` class to that input's `.sidebar-field` ancestor.
3. A delegated `input` listener on the same root strips the class the
   instant the user types into any LLM-marked field (instant feedback; no
   per-field handlers).
4. CSS: `:deep(.sidebar-field.llm-generated input, textarea, .v-field__input,
   .v-select__selection-text) { color: #7e57c2 !important; font-style: italic; }`

**Rules for future work:**
- **When writing an LLM generator that fills a MetadataPanel field**, update
  the rundown item's `llm_generated_fields` array (add the field name) as
  part of the same persistence operation. Do not try to style the field
  directly.
- **When a user edit persists**, the backend should remove the field name
  from `llm_generated_fields`. The frontend already strips the class
  instantly on keystroke, but removing it from the persisted array keeps the
  state correct across reloads.
- **Do NOT add per-field `:class="{ 'llm-generated': ... }"` bindings** in
  `MetadataPanel.vue`. The value-matching scanner handles every field in
  the panel automatically — adding new sidebar fields requires no wiring.
- **Do not key the scanner off placeholders or labels** — it matches by
  comparing the input's `.value` to `item[field]`. Field value collisions
  are handled via a `WeakSet` (first match wins per field).

## LLM Generation History Pattern (Universal)

Any field on a rundown item that an LLM can generate should follow a
**generation-history** pattern so the user can iteratively refine the output
across multiple rounds. The pattern has three parts:

### 1. History column (per field)
Each LLM-generated field gets a companion JSONB column named
`{field}_gen_history` (e.g. `description_gen_history`,
`title_gen_history`, `social_post_gen_history`). The column stores an
ordered array of conversation entries:
```json
[
  {"role": "llm", "text": "First attempt...", "ts": "2026-04-08T12:00:00Z"},
  {"role": "user", "text": "Make it shorter", "ts": "2026-04-08T12:01:00Z"},
  {"role": "llm", "text": "Revised attempt...", "ts": "2026-04-08T12:01:30Z"}
]
```
`role` is always `"llm"` or `"user"`. `ts` is UTC ISO-8601.

### 2. Service functions (per field)
In `app/services/auto_description_service.py` (or a future per-field
service), use these **field-specific** helper names:
- `append_{field}_history(db, asset_id, role, text)` — appends one entry.
- `get_{field}_history(db, asset_id)` — reads the array.
- `generate_{field}(asset_id)` — first-pass generation; appends an `llm`
  entry to history on success.
- `regenerate_{field}(asset_id, previous_value, feedback)` — reads full
  history, appends the `user` feedback entry, calls the LLM with the
  complete conversation, appends the new `llm` entry.

**Naming is field-specific, not generic.** `append_description_history` not
`append_history`; `regenerate_segment_description` not `regenerate_field`.
This keeps call sites self-documenting and avoids ambiguity when multiple
fields are LLM-generated on the same item.

### 3. Regenerate prompt structure
When regenerating, the LLM prompt contains (in this order):
1. The full standard generation prompt (segment content, tone, template).
2. `--- GENERATION HISTORY ---` block with every prior `[LLM generated]`
   and `[User feedback]` entry from the history array.
3. The current field value.
4. The user's latest feedback.
5. Instruction: "Write a NEW value that addresses ALL the user's feedback
   (both current and any prior rounds)."

This ensures each iteration converges toward the user's intent with full
context, not just the last attempt.

### 4. Frontend regenerate button
Each LLM-generated field with a history column should have a regenerate
button (purple refresh icon, bottom-right corner, appears on hover). The
button opens a modal showing the current value + a feedback textarea. On
submit, it calls `POST /api/episodes/regenerate-{field}` with
`{asset_id, previous_value, feedback}`.

### 5. When adding a new LLM-generated field
1. Create a `{field}_gen_history JSONB DEFAULT '[]'` migration.
2. Add the column to the SQLAlchemy model.
3. Write field-specific `generate_*` and `regenerate_*` functions.
4. Add the field name to `llm_generated_fields` on generation (drives
   purple highlighting automatically).
5. Add a regenerate button + modal in the sidebar (or wherever the field
   is displayed). Wire to a new API endpoint.
6. Return `{field}_gen_history` in the API response if the frontend needs
   to display iteration count or history.

## ContentEditor Save/Reload Architecture

**This is the most complex part of the codebase.** Read [`docs/SAVE_RELOAD_SPEC.md`](docs/SAVE_RELOAD_SPEC.md) before making changes.

### The Core Concept
Script Mode and Code Mode are two views of **one raw markdown string** (`rawMarkdownContent`). Code Mode edits it directly. Script Mode parses it into visual segments via `CueParser`, lets the user edit visually, then reconstructs the string.

### Save Ownership (Single Owner Per Path)
| Content Type | Owner | Debounce |
|---|---|---|
| Script Mode typing | EditorPanel (`updateTextSegment` + `persistCurrentItemToDatabase`) | 1.5s per-segment |
| Code Mode typing | ContentEditor `rawMarkdownContent` watcher | 2s |
| Cue insert/delete/reorder | ContentEditor `rawMarkdownContent` watcher | 2s |
| Scratch pad | ContentEditor `scratchContent` watcher | 2s |
| Manual save (Ctrl+S) | EditorPanel emits `save-all` | Immediate |
| Item switch | ContentEditor `selectRundownItem` | Immediate |

### Critical Design Rule
`saveCurrentItem()` skips reactive state mutations (`saving`, `hasUnsavedChanges`) when `isActivelyEditing=true`. This prevents Vue re-renders from stealing cursor focus in contenteditable elements. The API call still fires — only the bookkeeping is deferred.

### Key Files
- `ContentEditor.vue` (~9200 lines) — Parent, owns `rawMarkdownContent`, episode/rundown management. Modals lazy-loaded, metadata in `useEpisodeMetadata.js` composable.
- `EditorPanel.vue` (~12850 lines) — Child, visual editor, edit buffer, paragraph operations. Pure utility functions extracted to composables (`useContentSanitizer`, `useCollapseMode`, `useEditorPaste`).
- `PlaceholderCueCard.vue` (~3950 lines) — Cue card renderer with per-type child components in `cards/cue-types/` (FsqCueContent, SotCueContent, GfxCueContent).
- `src/utils/cueParser.js` (~550 lines) — Stateless parser: `parseContent()` and `reconstructContent()`

### Edit Buffer System
When typing in Script Mode, edits go into `segmentEditBuffer` (non-reactive, invisible to Vue) to prevent cursor loss. After 1.5s debounce, content is reconstructed and saved. `flushPendingChanges()` forces immediate application before transitions (item switch, mode switch, save all).

## Data Storage

**Database**: All content — episodes, rundowns, segments, cues, scripts, metadata
**Filesystem**: Media assets only — `/mnt/sync/disaffected/episodes/{episode}/assets/{video,images,audio,graphics}/`

Each rundown item has a `script_content` TEXT field containing markdown. YAML frontmatter is stripped on load, content body is what the editor works with.

## Development Commands

```bash
# Start all services
docker compose up --build

# View backend logs
docker logs show-build-server

# Connect to database
docker exec -it show-build-postgres psql -U showbuild -d showbuild

# Run migrations
cd app && python -m alembic upgrade head

# Frontend dev server
cd disaffected-ui && npm run serve

# Frontend lint (mandatory after changes)
cd disaffected-ui && npm run lint -- --fix

# Frontend tests
cd disaffected-ui && npm test
```

## Authentication

Dual auth: JWT tokens (user auth) and API keys (service-to-service). Use `get_current_user_or_key` dependency for endpoints accepting both.

RBAC: 5 built-in roles (Super Admin -> Viewer), 25+ permissions. See [`docs/RBAC_AUTHENTICATION_GUIDE.md`](docs/RBAC_AUTHENTICATION_GUIDE.md).

## Database Changes

1. Modify models in `app/models/` package (or legacy `app/models*.py` shims)
2. Create migration: `alembic revision --autogenerate -m "description"`
3. **Before any migration that deletes content**: ask user permission, explain consequences, create backup with `./scripts/backup_before_migration.sh`
4. Apply: `alembic upgrade head`

All content tables include `is_test_data` boolean. Test data uses episodes `900X`, titles `TEST: ...`.

## Troubleshooting

**Frontend issues — start here:** `./scripts/debug-frontend.sh`

This catches template ref naming conflicts (most common Vue issue), API connectivity, mounting problems.

**Template ref rule:** Always suffix template refs with `Ref` (`formRef`, `dialogRef`) to avoid conflicts with reactive variables of the same name. See [`docs/VUE_TEMPLATE_REF_CONFLICTS.md`](docs/VUE_TEMPLATE_REF_CONFLICTS.md).

**Logs:**
- Backend: `docker logs show-build-server`
- Database: `docker logs show-build-postgres`
- Frontend: Browser console + network tab
- Cache clearing: `scripts/clean-npm-servers.sh`

**Ollama**: Default is the **local container on prefect** — `http://ollama:11434` (from inside the docker network) or `http://192.168.51.238:11434` (from host/LAN). Default model is `qwen3:32b-q4_K_M`, kept resident via `OLLAMA_KEEP_ALIVE=-1` and an `ollama-preload` oneshot sidecar in `/home/kevin/ollama/docker-compose.yml`. Remote fallback (KairoBox shared instance): `http://192.168.51.197:11434`. Per-workflow overrides live in the `api_configs` table.

**XTTS**: Use settings from database (`api_configs` table), never hardcode.

**Announcements**: Create HTML file in `docs/announcements/` directory to display on dashboard.

## Claude-to-Claude Communication

ClaudeSpawn and CLAUDECOM protocols are deprecated. Use the inter-Claude relay instead (see relay commands at top of this file).
