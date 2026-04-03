# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Production Environment

- **Host**: `prefect` (192.168.51.207) — all show-build services run here
- **Frontend**: https://192.168.51.207:8091
- **Backend API**: https://192.168.51.207:8888
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

**Check before starting any work:** [`ACTIVE_WORK_QUEUE.md`](ACTIVE_WORK_QUEUE.md)

Update task status as you complete work.

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

**Ollama**: `http://192.168.51.197:11434` (NOT .223). Config in `api_configs` table.

**XTTS**: Use settings from database (`api_configs` table), never hardcode.

**Announcements**: Create HTML file in `docs/announcements/` directory to display on dashboard.

## Claude-to-Claude Communication

ClaudeSpawn and CLAUDECOM protocols are deprecated. Use the inter-Claude relay instead (see relay commands at top of this file).
