# Cue Delete + Media Disposition — Implementation Plan

**Date:** 2026-06-01
**Status:** Awaiting approval

## Goal

Every cue block's delete button (`mdi-delete`) actually removes the cue from
the script. For cues that link to media files, a second confirmation modal
offers what to do with those files.

## Findings (constraints that shape the design)

1. **Cue removal already works** — `performCueDeletion()` (`EditorPanel.vue:5792`)
   is robust and guarded against the known data-loss bugs. We wrap it (to add
   undo) but do **not** change its script-mutation core.
2. The media-delete half was a **stubbed TODO** (`EditorPanel.vue:5925`,
   `console.log` only) and was wired only for `IMG` cues.
3. **AssetID is NOT safe to glob on.** Two different cues in ep 0276 share
   `PROD-SOT-79A4B334B1CB` but point at different MediaURLs. Deletion MUST be
   driven by the specific cue's URL fields, never by AssetID-in-filename.
4. A cue's authoritative file pointers: `MediaURL` (all media types) + for SOT
   `audioUrl`, `thumbnailUrl`, `thumbnailOptions[]`. Paths are relative
   (`../assets/video/x.mp4`), resolved against `/home/episodes/{ep}/`.
5. There is a live **`asset_pool_files`** table + `AssetPoolFile` model
   (`models_whiteboard.py:108`) — the natural store for "released to pool"
   media (a future browse-the-pool picker will query it).
6. The whiteboard code writes the pool to `/mnt/sync/asset-pool`, which is **NOT
   mounted** in `show-build-server` (ephemeral). We will use a new mounted
   location instead.

## Decisions (from the user)

- All cue types are deletable. Only media-linked cues prompt about the media.
- "Delete & media" removes **all** linked files (video + audio + thumbnails +
  generated graphics), driven by the cue's own URL fields.
- Third option: **release media to a pool** instead of deleting it.
  - File is **moved** out of `episodes/{ep}/assets/...` into the pool (gone
    from the episode, not copied).
  - Pool is **episode-foldered for provenance** but logically unbound from any
    cue: `{pool_root}/{ep}/assets/...`. Future: whiteboard media may also live
    under `{pool_root}/{ep}/whiteboard/...`.
  - A future tool will browse this pool and let users re-add media (like the
    whiteboard media browser). So the `AssetPoolFile` DB row is the contract.
- On media-delete failure: a **Warning modal** — "cue deleted but media failed:
  {files}{reasons}{paths}" with three options: (1) acknowledge/do nothing,
  (2) acknowledge/try again, (3) cancel deletion → **restore the cue**.

## Pool storage

- **Host:** `/data/sync/disaffected/pool`  →  **Container:** `/home/pool`
  (new bind mount added to `docker-compose.yml` for `show-build-server`,
  both the web service and the celery worker service).
- Layout: `/home/pool/{episode}/assets/{video,audio,images,graphics}/{file}`
- TODO note (code comment + this doc): whiteboard media may relocate to
  `/home/pool/{episode}/whiteboard/` in the future.

## Backend (additive — no existing endpoints changed)

New file: `app/routers/episodes/cue_assets_router.py`, registered in
`app/routers/episodes/__init__.py`. Two endpoints (both under `/episodes`):

### `POST /{episode_number}/cue-assets/delete`
Body: `{ "media_urls": ["../assets/video/x.mp4", ...] }`
- Resolve each URL against `/home/episodes/{ep}/`.
- Hard safety assert: resolved path stays within `/home/episodes/{ep}/assets/`
  or `/home/episodes/{ep}/thumbnails/`. Reject traversal (403).
- `unlink(missing_ok=True)`.
- Returns `{ deleted: [...], skipped: [...], errors: [{path, reason}] }`
  (200 even on partial failure; the frontend decides what to show).

### `POST /{episode_number}/cue-assets/move-to-pool`
Body: `{ "media_urls": [...], "slug": "...", "cue_type": "...", "asset_id": "..." }`
- For each file:
  - Resolve + safety-assert as above.
  - Mint a pool AssetID via `AssetIDService.request_asset_id(db,
    entity_type="pool", reason="cue_release", context={...})`.
  - Move the file to `/home/pool/{ep}/assets/{subdir}/{file}` (subdir derived
    from the source subdir: video/audio/images/graphics).
  - Insert `AssetPoolFile(asset_id, file_path, original_filename, mime_type,
    file_size, source="cue_release", source_context={episode, origin_cue_assetid,
    slug, cue_type, original_path})`.
  - Tag with `AssetTag` (cue_type, slug) for future browse/filter.
  - `db.commit()`.
- Returns `{ moved: [{asset_id, new_path, original_path}], errors: [{path, reason}] }`.

Restart `show-build-server` after backend changes (not hot-reloaded).

## Frontend

### Generalize the modal
`DeleteImgCueModal.vue` → `DeleteCueWithMediaModal.vue` (keep old file as a thin
re-export or delete after callsites updated). Content:
- Title "Delete Cue" + cue type/slug.
- Lists linked file(s) by path.
- Buttons:
  1. **Delete Cue** — `color="error" variant="outlined"` — emits `delete-only`.
  2. **Delete Cue & Associated Media** — `color="error" variant="elevated"` —
     emits `delete-with-media`.
  3. **Delete Cue, Release Media to Pool** — `variant="tonal"` — emits
     `delete-release-to-pool`.
  4. Cancel.

### New Warning modal
`MediaDeleteFailedModal.vue`: shows `[{file, reason, path}]` and three buttons:
- "Acknowledge" → `acknowledge`
- "Acknowledge, try again" → `retry`
- "Cancel deletion, restore cue" → `restore`

### EditorPanel.vue wiring
- **`deleteCue(index)`**: collect `linkedMedia` from the segment
  (`mediaUrl`, `audioUrl`, `thumbnailUrl`, `...thumbnailOptions`, deduped,
  non-empty). If non-empty → open `DeleteCueWithMediaModal`; else → existing
  plain confirm. (Every cue stays deletable.)
- **Capture undo state**: `performCueDeletion` returns / stashes
  `{ removedBlockText, removeStart }` so a cue can be re-inserted on "restore".
  Implement `restoreDeletedCue()` that splices the captured block back into
  `rawScriptContent` at `removeStart` and re-emits update/save.
- **Disposition handlers**:
  - `delete-only` → `performCueDeletion(index, false)` (no API call).
  - `delete-with-media` → `performCueDeletion` first (capture undo), then
    `POST .../cue-assets/delete`. On `errors.length` → open
    `MediaDeleteFailedModal`.
  - `delete-release-to-pool` → `performCueDeletion` first, then
    `POST .../cue-assets/move-to-pool`. On error → `MediaDeleteFailedModal`
    (same retry/restore semantics).
- **Failed-modal handlers**: `acknowledge` = close; `retry` = re-POST the same
  endpoint; `restore` = `restoreDeletedCue()` + close.
- Snackbar on success. Episode number comes from existing props/state.

### Lint
`cd disaffected-ui && npm run lint -- --fix`.

## Explicitly NOT doing
- No AssetID globbing (unsafe — shared AssetIDs).
- No change to `performCueDeletion`'s proven script-mutation logic.
- No use of the unmounted `/mnt/sync/asset-pool`.
- The pool **browser/picker** UI is out of scope (future tool); we only write
  the `AssetPoolFile` rows it will consume.
