# Show-Build Codebase Navigation Index

Fast lookup for where functionality lives. Organized **top-down**:
Layer 0 (hot-spot shortcuts) → Layer 1 (feature → subsystem) → Layer 2
(subsystem → files + key entry points).

> **Production safety note** — Show-Build is both developed and used to
> produce live shows on the same codebase. Before editing in any
> `hot-spot` area, verify: (a) no in-progress edits on disk you don't
> recognize, (b) no conflicting session on the relay, (c) you understand
> the save-reload contract in `docs/SAVE_RELOAD_SPEC.md`.

---

## Layer 0 — Hot-Spot Shortcuts

| If you're touching… | Read first | Key file(s) |
|---|---|---|
| Script/Code mode typing, cursor loss | `docs/SAVE_RELOAD_SPEC.md`, `docs/EDITOR_PANEL_ARCHITECTURE.md` | `ContentEditor.vue`, `content-editor/EditorPanel.vue` |
| Cue cards / placeholder rendering | `docs/CUE_BLOCK_INSERTION_PROTOCOL.md` | `content-editor/cards/PlaceholderCueCard.vue`, `cards/cue-types/*` |
| Rundown reorder / DnD | `useRundownDragDrop.js` | `content-editor/RundownPanel.vue` |
| Metadata sidebar / LLM-purple fields | `CLAUDE.md` §MetadataPanel | `content-editor/MetadataPanel.vue`, `useEpisodeMetadata.js` |
| Asset pool / whiteboard-to-cue | — | `content-editor/AssetPoolPanel.vue`, `useCueTranslation.js` |
| LLM auto-description pipeline | `docs/LLM_AUTO_DESCRIPTION_IMPLEMENTATION_PLAN.md` | `app/services/auto_description_service.py`, `celery_app.py` |
| Save/reload bugs | `docs/SAVE_RELOAD_SPEC.md` | `ContentEditor.vue` rawMarkdownContent watcher, EditorPanel edit buffer |
| Auth / RBAC | `docs/RBAC_AUTHENTICATION_GUIDE.md` | `app/auth/`, `app/services/rbac_service.py`, `app/models_rbac.py` |
| Celery tasks | `celery_app.py` queue defs | `app/celery_app.py`, `services/*_tasks.py`, `services/auto_description_service.py` |
| LLM proxy / prompt overrides | `docs/PROMPT_OVERRIDE_SYSTEM.md` | `app/llm_proxy_router.py`, `app/prompts_router.py`, `useLLMPrompts.js` |
| Episode directory / media assets | `docs/EPISODE_DIRECTORY_STANDARD.md` | `app/routers/episodes/media_router.py`, `services/asset_processing.py` |
| Keyboard shortcuts | `docs/KEYBOARD_SHORTCUTS.md` + `disaffected-ui/src/data/keyboardShortcuts.js` | `useHotkeys.js` |
| Public/website-facing API (planned) | `docs/WEBSITE_PUBLIC_API_PLAN.md` | _not yet implemented; lives at `app/routers/public/` per plan_ |
| Distribution matrix (publication destinations) | `docs/PUBLICATION_DESTINATIONS_PLAN.md` | _stub; covers per-destination publishing state across YouTube, IG, X, TikTok, etc._ |

---

## Layer 1 — Feature → Subsystem Map

### A. Content Editor (the core)
```
ContentEditor.vue (parent, ~9200 lines)
 ├─ RundownPanel.vue         (left, item list + DnD)
 ├─ EditorPanel.vue          (center, ~12500 lines, script+code modes)
 │   ├─ cards/PlaceholderCueCard.vue (~4000 lines)
 │   │   └─ cards/cue-types/{Fsq,Sot,Gfx}CueContent.vue
 │   ├─ CueToolbar.vue
 │   └─ CuePlacementOverlay.vue
 ├─ MetadataPanel.vue        (right, sidebar fields)
 ├─ AssetPoolPanel.vue       (whiteboard media → cue extraction)
 └─ modals/*                 (CueModal, DeleteCueModal, ImgCueModal, …)
```
Composables backing it: `useContentEditor`, `useContentSanitizer`,
`useCollapseMode`, `useEditorPaste`, `useEpisodeMetadata`,
`useRundownDragDrop`, `useScriptCore`, `useCueTranslation`.

### B. Cues (cue system)
Types: `FSQ, GFX, SOT, VO, NAT, RIF, PKG, DIR, BUMP, STING, VOX, MUS, LIVE`.
- Parser (markdown ↔ segments): `src/utils/cueParser.js`
- Color map: `src/utils/themeColorMap.js`
- FSQ PNG gen: `services/script_compilation.py`, `services/quote_extraction.py`, frontend `fsqLayout.js`
- GFX-XPOST social: `app/routers/whiteboard/social_media_router.py`, `GfxModal.vue`
- SOT pipeline: `app/sot_router.py`, `services/sot_processor.py`, Celery `media` queue

### C. Rundown / Episode lifecycle
Backend router package `app/routers/episodes/`:
- `crud_router.py` — CRUD on episodes
- `metadata_router.py` — episode metadata
- `rundown_router.py` — rundown items
- `versioning_router.py` / `history_router.py` — version history
- `cues_router.py` / `media_router.py` / `thumbnails_router.py`
Services: `services/episode_scaffold.py`, `services/blueprint_renderer.py`,
`services/canonical_structure_parser.py`, `services/autosave_history.py`,
`services/host_script_generator.py`, `services/script_compilation.py`.

### D. Assets & Media
- AssetID: `services/asset_id.py`, `app/assetid_router.py`,
  `app/new_assetid_router.py`, `app/convert_assetid_router.py`
- Processing: `services/asset_processing.py`, `services/ffmpeg_tasks.py`
- File inventory / LLM classification: `services/file_inventory_*.py`,
  `app/file_inventory_router.py`
- Whiteboard (graphics + social): `app/routers/whiteboard/*`
- Media routers: `app/media_router.py`, `app/media_analysis_router.py`,
  `app/routers/upload_router.py`, `app/repo_router.py`

### E. LLM layer
- Providers: `src/composables/llm/providers.js`,
  `src/composables/llm/quoteSplitting.js`
- Proxy: `app/llm_proxy_router.py`
- State + prompts: `app/llm_state_router.py`, `app/prompts_router.py`,
  `useLLM.js`, `useLLMPrompts.js`, `useLLMState.js`
- Auto-description pipeline: `services/auto_description_service.py`
  (Celery chain: `classify_segment_tone` → `generate_segment_description`,
  swept by Beat every 60s on `llm_content` queue)
- Segment extraction: `services/segment_llm_extractor.py`,
  `app/segment_llm_router.py`

### F. Async / Celery
- Entry: `app/celery_app.py` (7 queues: `assets_high, assets, assets_low,
  compilation, quotes, media, fsq`; plus `llm_content` queue for
  auto-description; plus `descriptions` planned)
- Beat schedule lives alongside `celery_app.py` (Beat container:
  `show-build-celery-beat`)
- Cleanup: `app/celery_cleanup.py`
- Workers: `services/tools_tasks.py`, `services/ffmpeg_tasks.py`,
  `services/asset_processing.py`, `services/script_compilation.py`,
  `services/quote_extraction.py`, `services/sot_processor.py`,
  `services/auto_description_service.py`
- Jobs API: `app/celery_jobs_router.py`, `app/workers_router.py`

### G. Settings & Config
- Backend router pkg `app/routers/settings/`:
  `general_router.py`, `media_paths_router.py`, `interface_router.py`,
  `system_router.py`, `llm_identity_router.py`
- Frontend: `src/components/settings/*`, `SettingsView.vue`
- Runtime config utils: `app/config/`, `app/config_utils.py` (NO hardcoded
  IPs — always `get_service_url()`, `get_redis_url()`, `get_whisper_servers()`)
- API keys: `api_configs` DB table via `app/api_config_router.py`

### H. Auth & Users
- `app/auth/` (JWT), `app/services/rbac_service.py`, `app/models_rbac.py`
- Dual auth dep: `get_current_user_or_key`
- Frontend: `src/components/LoginModal.vue`, `useAuth.js`,
  `UserManagement.vue`

### I. Integrations
- Twitter/X: `app/twitter_oauth_router.py`, `app/models_twitter.py`, X-POST cue DB table
- Google Drive: `app/google_drive_router.py`, `services/google_drive_service.py`
- vMix: `app/vmix_router.py`
- Voice/XTTS: `app/xtts_router.py`, `app/voice_model_router.py`,
  `app/voice_sample_router.py`, `app/wpm_audio_router.py`, `useXtts.js`,
  `useTts.js`
- Asterisk / voice conf: `app/voice_conference_router.py`,
  `services/asterisk_service.py`
- Whisper: external at 192.168.51.210:8885 (per `api_configs`)

### J. Dashboard / Supporting UI
- `DashboardView.vue`, `NextShowPanel.vue`, `AnnouncementsPanel.vue`,
  `TodoPanel.vue` (unified `/api/todos`), `JobMonitor.vue`,
  `SystemHealthStatus.vue`, `StackManager.vue`, `NotificationCenter.vue`

### K. Database
- Models: `app/models/` pkg (`enums, organization, episode, content,
  production, settings, jobs`) + back-compat shims `app/models_v2.py`,
  `app/models_*.py`
- Migrations: `app/alembic/`
- Shared session: `app/database.py`
- Postgres on prefect (host 5433 → container 5432)

---

## Layer 2 — Entry-Point Reference

### main.py router wiring (`app/main.py`)
- Core: `health, upload, legacy, misc, comfyui`
- Auth: `auth, rbac`
- Settings: `api_config, settings, settings_colors, setup`
- Episodes: `episodes, episode_scaffold, rundown_templates,
  content_library, script_generation`
- Assets: `assets, assetid, new_assetid, convert_assetid, media,
  media_analysis, repo`
- Cues: `fsq_asset, gfx_asset, sot, vo`
- Voice/duration: `speakers, voice_sample, wpm_audio, voice_model, xtts,
  duration, duration_estimation`
- Org/show: `organization, show`
- Templates/docs: `templates, docs, mp3_profiles, blueprint_config`
- LLM: `llm_proxy, llm_state, prompts, segment_llm`
- Async: `tools, housekeeping, workers, celery_jobs`
- Other: `whiteboard, todos, announcements, voice_conference,
  segment_locks`
- Integrations: `google_drive, twitter_oauth, vmix`
- Data: `file_inventory, consolidation, customer, production_roles`

### Containers (prefect, 192.168.51.207)
- `show-build-server` — FastAPI backend (port 8888 → 80)
- `show-build-frontend` — Vue (port 8091 → 8080)
- `show-build-postgres` — Postgres (port 5433 → 5432)
- `show-build-celery-beat` — Beat scheduler
- `show-build-llm-content-worker` — `llm_content` queue worker,
  concurrency=1
- (External) `192.168.51.223:6379` Redis (farmhouse),
  `192.168.51.197:11434` Ollama (kairo)

### Non-obvious files
- `src/utils/cueParser.js` (~550 lines) — stateless; `parseContent()` and
  `reconstructContent()` are the only two public functions
- `src/utils/themeColorMap.js` — single source for segment/status/cue colors
- `app/config_utils.py` — service URL resolution (never hardcode IPs)
- `scripts/debug-frontend.sh` — first thing to run on a frontend bug

---

## How to Use This Index
1. Search by feature → find subsystem (Layer 1).
2. Drop to Layer 2 for exact file/entry point.
3. Hot-spots in Layer 0 flag reads that will save you a bad edit.

## Maintenance
This index reflects repo state as of **2026-04-18** on branch
`experiment/metadata-asset-pool`. Keep in sync with `docs/INDEX.md`
(which indexes *documentation*, not code). When adding a new router or
top-level feature, add a line to Layer 1 and/or Layer 2 here.
