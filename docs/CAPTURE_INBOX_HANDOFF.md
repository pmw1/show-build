# Capture Inbox → Whiteboard Integration (handoff spec)

**Audience:** the whiteboard-canvas session (owner of `ScratchpadView.vue`).
**Status:** backend + Chrome extension live as of 2026-07-22; this UI
integration is the missing last mile. Until it lands, captures accumulate as
`pending` and their media is already visible in the AssetPoolPanel — nothing
is lost.

## Background (why an inbox exists)

The capture extension (`capture-extension/`) and, later, a phone PWA send
content into an episode from outside the app. They can never append a
whiteboard card directly: `POST /api/whiteboard/{ep}/save` deletes and
reinserts every item, so any external insert would be clobbered by the next
save from an open board. Instead, external clients POST to a **capture
inbox** (`whiteboard_captures` table, `app/routers/whiteboard/
captures_router.py`, migration g026). The whiteboard UI drains pending
captures into real Vue Flow cards and acks them **after** a successful board
save.

## API (all under `/api/whiteboard/{episode}` — auth like every whiteboard call)

| Call | Purpose |
|---|---|
| `GET /captures?status=pending` | `{captures:[...], count}` oldest-first. The poll target. |
| `POST /captures/{id}/ack` | Mark placed. Idempotent. 409 while still `processing`. |
| `POST /captures/{id}/dismiss` | User discarded the spawned card before saving. Idempotent. Never deletes pool media. |

Capture rows carry `WhiteboardItem`-shaped content fields plus:
`capture_kind` (selection/link/image/video/page/screenshot), `item_type`
(text/link/image/video/audio), `media_url` (computed `/pool/{media_path}`),
`extra_assets` (secondary assets of multi-media posts), `intended_cue_type`
(sot/vo/nat or null), `processing_job_id` (SOT/VO `temp_job_id` in
`sot_processing_jobs` when typed processing was dispatched), `source`
(`{agent, version, page_url, page_title}`), `created_by`, `error`.

## Integration spec

1. **Poll** while ScratchpadView is mounted for episode E:
   `GET /api/whiteboard/{E}/captures?status=pending` every **20 s**, plus
   immediately on mount and on `window` focus. (Registered pollers are
   zone-scoped elsewhere in the app — same idea: one place, one cadence.
   Converts to SSE with todo #24 whenever that lands.)

2. **Spawn** each pending capture whose id is not in a local in-memory
   `Set` (`spawnedCaptureIds`) as a normal card at the standard spawn point
   (cascade-offset multiples like the spawn menu does). Field mapping is a
   direct copy: `item_type, title, text_content, url, notes, caption,
   preview_*` → same names; media cards get `media_asset_id`,
   `media_url = /pool/{media_path}`, `mime_type`, `file_size`,
   `thumbnail_url`, `media_metadata`; social cards get `social_metadata`.
   Embed provenance so it survives into the saved item row (g023 JSONB):

   ```js
   media_metadata: { ...capture.media_metadata,
     capture: { capture_id, intended_cue_type, processing_job_id,
                source, created_at, created_by } }
   ```

   The `Set` is deliberately **not persisted**: if the tab dies before a
   save, the spawned cards vanish but the captures are still `pending`
   server-side and respawn on next load — self-healing, no loss.

3. **Ack only after persistence.** Track `spawnedUnacked: Map<captureId,
   cardRef>`. On the next **successful** full-board save: ack every capture
   whose card still exists on the board; dismiss those the user deleted
   before the save. Never ack at spawn time. Acks/dismisses are idempotent;
   a failed ack just means another client may spawn a duplicate card —
   consistent with the board's last-write-wins model.

4. **Multi-client:** two open boards both spawn a pending capture; whoever
   saves+acks first wins and the other's duplicate is just a normal card the
   user can delete. Claim/lease semantics are a possible later upgrade, not
   v1.

5. **Optional UX garnish** (not required): a small inbox badge/tray showing
   `count` of pending captures before spawning, and a distinct spawn flash
   for capture-born cards. `status=processing` rows (social download in
   flight, up to ~2 min) can show as a ghost/spinner chip if you want —
   they become `pending` when enrichment finishes, and rows stuck
   `processing` >10 min should be treated as stalled (the extension popup
   already displays them that way).

## Verified behaviors you can rely on

- Text/link captures are `pending` immediately; social captures go
  `processing` → `pending` in seconds (X) to ~2 min (yt-dlp).
- Every media capture already has pool files + `asset_pool_files` rows +
  `episode:{ep}` tags at `pending` time — AssetPoolPanel shows them without
  any whiteboard involvement.
- Enrichment failures degrade to a `pending` **link** card with `error` set
  (never lost, never blocks the queue).
- SOT/VO-typed video captures also ran the full processing pipeline
  (transcode + Whisper transcript on the `sot_processing_jobs` row keyed by
  `processing_job_id`) — the spawned card's `media_metadata.capture` carries
  everything needed to wire "insert as cue" later.
