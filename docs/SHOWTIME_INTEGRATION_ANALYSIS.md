# Showtime ↔ Show-Build Integration — Gap Analysis

**Status:** DRAFT — analysis only. No code changes. Awaiting user direction.
**Author:** prefect-claude-e2d781, 2026-05-20
**Scope:** Map the data contract showtime expects against what show-build serves today, and identify where post-recording data from showtime should land.

## 1. Endpoint inventory

### GET (read path) — present and partly aligned

| Side | Endpoint | Status |
|---|---|---|
| showtime calls | `GET /api/episodes/{n}/rundown` | — |
| show-build serves | `GET /api/episodes/{n}/rundown` (`rundown_router.py:137`) | ✅ exists |

Show-build returns `{items: [...]}` — a flat list mixing regular `rundown_item`s and content-library placements. Each item carries: `id`, `asset_id`, `type`, `slug`, `title`, `subtitle`, `duration`, `script`, `order`, `status`, `description`, plus per-item metadata.

Showtime's adapter (`/home/kevin/showtime/backend/modules/rundown_sources/show_build_http.py`) maps these into `RundownItem(id, sort_order, item_type, block_letter, title, slug, target_duration_seconds, script_content, status)`. Cues, takes, media-list are left empty.

### PUT (writeback path) — endpoint exists, payload is dropped

| Side | Endpoint | Status |
|---|---|---|
| showtime calls | `PUT /api/episodes/{n}/save-episode` with `{episode_metadata: {recording_manifest: {…}}}` | — |
| show-build serves | `PUT /api/episodes/{n}/save-episode` (`metadata_router.py:380`) | ⚠️ accepts, then silently drops |

The handler iterates `episode_data.items()` and does `setattr(episode, field, value)` only for fields that exist on the `Episode` model. There is no `episode_metadata` column, so the entire payload is discarded with HTTP 200. Showtime currently believes manifests are being persisted — they are not.

## 2. Three semantic gaps

### Gap A — Cues are not transmitted

Show-build stores cues as markdown directives inside `script_content`. The Vue editor parses them client-side via `disaffected-ui/src/utils/cueParser.js`. The HTTP API returns the raw markdown string only.

Showtime's `RundownItem.cues: list[Cue]` is therefore always empty after a fetch. The cue runner module (M9) will have nothing to schedule from a show-build–sourced episode.

**Options:**
- **A1** — Show-build pre-parses cues server-side and adds `cues: [...]` per item in the rundown response. Keeps parser authoritative in one place; lets the cue grammar evolve without porting code.
- **A2** — Showtime imports a Python port of `cueParser.js`. Avoids a show-build API change; doubles the parser maintenance surface.

Recommendation: **A1**. Cue grammar is show-build's domain.

### Gap B — Block grouping is implicit

Show-build's `type` field is free-form ("segment", "headline", "story", "sponsor", "ad", …). Showtime's `block_letter` is only populated when `type` is literally `"block-a"`…`"block-d"`, which show-build never emits in practice.

Block boundaries in the Vue editor are inferred from item ordering and a separate "advert" segment type that acts as a divider. This inference logic does not exist in showtime.

**Options:**
- **B1** — Add a `block_letter` column to `RundownItem` (nullable). Show-build editor populates it; API surfaces it. Showtime reads directly.
- **B2** — Showtime infers blocks from ordering + advert markers. Brittle; couples showtime to show-build's editor conventions.

Recommendation: **B1**. Explicit beats inferred.

### Gap C — Recording manifest has no home

`save-episode` accepting and dropping payloads is the immediate blocker. This is also where the user's question lives: "showtime will feed info back after a recording session — consider how and where that data gets stored and what it will be useful for."

A recording manifest is fundamentally different from the planning rundown:
- The rundown is **edited** (small mutations, single canonical state).
- A manifest is **observed** (append-only history of what actually happened during a take).
- Multiple manifests per episode are expected: rehearsals, retakes, the real session.

The manifest contains per-take: filenames, started_at_wallclock, duration, markers, pickup-splice sidecar refs, cue fire timestamps, disk band transitions, operator notes, drift_status, and the staged-counters trail.

## 3. Where the manifest should live — three shapes

| Shape | Storage | Query model | When it shines |
|---|---|---|---|
| **C1 — JSONB column** | `episodes.recording_manifests jsonb default '[]'` (array of session entries) | Read whole-episode; JSONB operators for filters | Fastest to ship; one migration; useful if downstream is "show me this episode's takes" |
| **C2 — Relational** | `recording_session` table (FK→episode) + `recording_take` child + `take_marker`/`take_cue_fire` grandchildren | Standard SQL; indexable; cross-episode analytics | Best long-term — "find all pickups", "average drift per operator", "which cues fire late" all become queries |
| **C3 — Hybrid** | `recording_session` row per session with `manifest jsonb` payload + indexed columns (`started_at`, `status`, `take_count`, `total_duration_seconds`) | SQL on session-level, JSONB for take details | Pragmatic — defers take-level normalization until you know what you'll query |

### Downstream uses worth considering before picking

- **Editorial decision-making.** Did the take complete? Were there pickups? Did markers indicate problems? This needs *take-level* visibility — argues against pure JSONB.
- **Post-production handoff.** Pickup sidecars need to surface to whoever splices. `recording_take` + a `pickups` view makes this trivial.
- **Show-build UI display.** A "Recording History" panel on the episode page that lists past sessions and their takes. JSONB is fine if read-only.
- **Cross-episode analytics.** "How often does cue X fire late?" "What's our average drift?" "Which segments routinely overrun?" These are SQL-shaped questions — argues for C2 or at least the indexed columns in C3.
- **vmix-promoter coordination.** Already a sibling service; promoter consumes manifest data for promo routing. Stable schema beats free-form JSON here.

Recommendation: **C3 (hybrid)**. Land a `recording_session` table now with the manifest as JSONB plus session-level indexed columns. Normalize take-level fields only when an actual query needs them. This is reversible (drop one table) but immediately unblocks showtime.

## 4. Non-destructive implementation path (proposal — not executed)

Each step is independently reversible. Nothing here has been done.

**Step 1 — Stop the silent drop.** Modify `save-episode` to validate `episode_metadata` and either:
  (a) reject with 400 + clear message until storage exists, OR
  (b) accept and route to `recording_session` table once Step 2 lands.
*Reversibility: revert one handler.*

> **2026-05-20 update:** **DONE.** `PUT /api/episodes/{n}/save-episode` now
> recognizes `episode_metadata.recording_manifest` and routes it to
> `services/recording_session_service.py:persist_recording_manifest`,
> which writes into recording_sessions/recording_takes/take_cue_fires.
> Existing setattr behavior for flat fields preserved (backward
> compatible). Smoke-tested in-container: 1 session + 2 takes (one
> with pickup metadata) + 1 cue-fire persisted from sample showtime
> manifest. Response now includes `recording_session_id` when manifest
> was processed. Reversible by reverting `metadata_router.py` and
> `services/recording_session_service.py`.

**Step 2 — Add `recording_session` table.** Alembic migration adding the table (no FK breaking changes). Showtime's `push_manifest` becomes a real write.
*Reversibility: alembic downgrade one revision.*

> **2026-05-20 update:** User chose **C2 fully relational**. Migration drafted at
> `app/alembic/versions/g016_recording_sessions.py`. Four tables:
> `recording_sessions`, `recording_takes`, `take_markers`, `take_cue_fires`.
> Originally chained to `g015`; rebased to chain from `g014_segment_llm_phase2`
> by user direction because `g015` is blocked by pre-existing duplicate
> (rundown_id, slug) pairs in production. Alembic now has two heads
> (g015 and g016) — they'll be reconciled when g015's data issue is resolved.
> **APPLIED 2026-05-20.** Current DB head: `g016_recording_sessions`.
> Reversible via `alembic downgrade g014_segment_llm_phase2`.

**Step 3 — Surface cues in GET response (Gap A).** Add server-side cue parsing in `get_episode_rundown` so each item gets a `cues: [...]` array alongside `script`. Backward compatible (additive field).
*Reversibility: revert the response builder; existing consumers ignore unknown fields.*

> **2026-05-20 update:** **DONE.** New module
> `app/services/cue_extractor.py` mirrors the cue-block parsing half of
> `disaffected-ui/src/utils/cueParser.js` (parseContent + parseCueBlock
> + toCamelCase + img extraction). `GET /api/episodes/{n}/rundown` now
> returns a `cues: [{order, type, slug, asset_id, duration,
> description, media_url, thumbnail_url, audio_url, image_src, quote,
> attribution, fields}]` array per item. Smoke-tested against episode
> 240 segment ASTMFMGRRWO0XMK4R: 28 structured cues extracted from
> real script content with correct types (SOT/GFX) and per-cue
> metadata. Backward compatible — existing consumers ignore the new
> field. Reversible: revert the response builder + delete the service
> file.

**Step 4 — Add `block_letter` column (Gap B).** Migration + editor wiring + API surface.
*Reversibility: alembic downgrade; column is nullable so no data loss.*

> **2026-05-20 update:** **DONE (column + API surface).** Migration
> `g017_rundown_item_block_letter` applied. `block_letter VARCHAR(2)`
> added nullable to `rundown_items`. SQLAlchemy model updated.
> `GET /rundown` surfaces it on each item. `POST /rundown/item`,
> `PUT /rundown/{item_filename}`, and `PUT /save-rundown` all accept
> `block_letter` on writes. Editor wiring (Vue UI to set the value) is
> NOT done — frontend work for a follow-up. Showtime can already
> consume the field once values exist. Reversibility: `alembic
> downgrade g016_recording_sessions`.

**Step 5 — Showtime adapter updates.** Read `cues` and `block_letter` from response; honor them in the local Episode model.
*Reversibility: revert in showtime repo; adapter just ignores the fields again.*

## 5. Open questions for the user

1. **Storage shape for the manifest** — C1 / C2 / C3?
2. **Multiple sessions per episode** — confirmed expected (rehearsals + real take), or single-session per episode?
3. **Show-build UI** — do you want a "Recording History" panel on the episode page (drives data shape needs)?
4. **Cue parsing on the server** — OK to add a Python parser that mirrors `cueParser.js`, or prefer a different boundary?
5. **Block letters** — add a column, or is there an existing convention in show-build I'm missing?

## 6. What this document is not

- Not a plan-of-record. Awaiting user direction.
- Not a contract change. Nothing is modified.
- Not exhaustive. M-by-M downstream consumers (vmix-promoter, companion-bridge, disk-monitor) may add further fields to the manifest; this analysis covers the spine.

## 6a. Contract alignment with showtime (per c2c043 msg #450)

c2c043 (showtime-side claude) sent direct field-shape preferences for
the cue extraction response. Updated 2026-05-20 to align:

**Cue field renames** — `extract_cues` now emits showtime's
`Cue` pydantic model fields (`sort_order`, `cue_type`, `title`,
`trigger`, `offset_seconds`, `status`) alongside show-build native
fields. Legacy aliases (`order`, `type`) kept for backward
compatibility through 2026-Q3. Showtime can now construct
`Cue(**c)` after picking the fields it needs.

**Title derivation** — mirrors `cueParser.js generateCardTitle`:
prefer `description` (human-readable); fall back to `f"{type}: {slug}"`;
final fallback `type` or `"Unknown Cue"`.

**Defensive logging on unknown PUT keys (msg #450 ask 2)** —
`PUT /save-episode` previously dropped unknown top-level keys
silently. Now collects them into `unknown_keys_dropped` in the
response and logs a WARNING with episode_number + key list. Clients
that send a misspelled or removed field will see what was ignored
instead of a misleading 200. `episode_metadata` is excluded from the
unknown list because it's routed separately (recording manifest).

**Lower-priority follow-up not yet addressed (msg #450 NEW gap):**
item types `coldopen` (one word) and `tease` are not normalized to
showtime's filename grammar. Three options on the table; showtime
client-maps for now (commit 35c5ab0). Park until grammar decision
lands.

## 7. E2E validation results (2026-05-20)

Live test of `ShowBuildHttpRundownSource.fetch_episode('240')` against
the running backend on `http://192.168.51.238:8888`:

- **HTTP path works** — `GET /api/episodes/240/rundown` returns 200,
  10 items with structured `cues:[]` arrays (new field) and
  `block_letter` (new field, empty string for unset).
- **Showtime-side contract mismatch surfaced.** Showtime's pydantic
  `Episode.episode_number` enforces `pattern=r'^\d{4}$'` (4-digit
  string), but show-build stores `'240'`, not `'0240'`. The adapter
  passes the raw show-build value through, so `Episode(...)`
  validation raises. Fix is on the showtime side — either zero-pad in
  `ShowBuildHttpRundownSource.fetch_episode` before constructing the
  `Episode`, or relax the pydantic pattern. Recommend zero-padding;
  the showtime filename grammar is 4-digit and consistency helps.

## 8a. Read API for recording sessions

Write path lands data via `PUT /save-episode`; the read counterpart was
added 2026-05-20 in `app/routers/recording_sessions_router.py`:

- `GET /api/episodes/{n}/recording-sessions` — list sessions for an
  episode, newest-first.
- `GET /api/recording-sessions/{id}` — full session detail with takes,
  markers, and cue-fires nested.
- `GET /api/recording-sessions/{id}/takes` — takes-only summary
  (cheaper when markers/cue-fires aren't needed).

Endpoints are unauthenticated, matching the existing `GET /rundown`
pattern. Smoke-tested against persisted test data; 200/404 paths both
correct. This unblocks a future "Recording History" panel on the
episode page.

## 8. Test coverage

- `app/tests/test_cue_extractor.py` — 10 tests covering empty inputs,
  camelCase conversion across all shapes (PascalCase, spaces,
  snake_case, kebab-case), single + multi-cue extraction, ordering,
  malformed cue (Begin without End must NOT swallow next cue),
  quote-stripping, embedded `<img>` extraction, type-required guard,
  multiline field values, and MediaURL camel/lowercase variants.
  All 10 pass.
- `app/services/recording_session_service.py` — smoke-tested in
  container against episode 236 with a representative manifest;
  verified session + 2 takes (pickup metadata preserved) + 1 cue-fire
  persisted. Formal pytest coverage deferred — needs DB fixture
  scaffolding the project doesn't have yet.
