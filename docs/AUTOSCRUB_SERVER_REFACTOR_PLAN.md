# Move Autoscrub Server-Side (and Disable the Client Scrub in the Interim)

## Status

- **Interim step (do first):** disable the client-side Autoscrub entirely.
  Blocked only on the editor-lane coordination hold — `EditorPanel.vue` is
  currently claimed by sibling session 746024 (todos #37/#34/#35). Apply once
  that lane clears.
- **Full refactor (do after):** reimplement Autoscrub as a server-side
  normalization function. Larger, multi-file, touches the SSE plan (#24) and
  `SAVE_RELOAD_SPEC.md`; deserves its own focused pass.

## Problem

"Autoscrub" (formerly "Autoformat") is a **client-side** content normalizer.
Every N seconds (admin-set `autoscrubInterval`, default 30s) the open editor
scrubs its own content, then asks `ContentEditor` to scrub every other rundown
item. It is all pure regex over `script_content`:

- strip `<span>`/`<div>` tags and Google-Docs paste cruft
- convert `font-weight`/`font-style` spans to `<b>`/`<i>`
- clean `&nbsp;` and collapse runs of whitespace
- strip leading dashes from non-list paragraphs
- flag invalid cue codes / unwelcome HTML with
  `data-needs-attention="true"` + `data-flag-note="…"` (and un-flag when fixed)

### Why the current (client) design hurts

1. **Split-brain duplication.** The rules exist twice, separately
   implemented: `EditorPanel.autoscrubContent()` (the open item) and
   `ContentEditor.autoscrubAllItems()` (every other item). Two copies drift.
   This is the same neighborhood as the cueParser data-loss incidents and the
   autosave-freeze bug — client-side string surgery on live content.
2. **Timing hazards.** Because it mutates the buffer the user is editing, it
   needs a wall of guards: don't-run-while-typing, don't-run-with-a-modal-open,
   skip-active-cursor-highlighting, a 10s recent-activity check. All of that
   exists only to avoid clobbering the active editor.
3. **Single-user only.** It scrubs the items loaded in one browser. Items
   edited by other users (or never opened) are never normalized.
4. **Settings live in `localStorage`** (`showbuild_interface_settings`:
   `autoscrubEnabled`, `autoscrubStripSpans`, `autoscrubRemoveLeadingDashes`,
   `autoscrubCleanWhitespace`, `autoscrubInterval`), set by admin in the
   Settings UI. A server worker cannot read them there.

## Interim: disable the client-side scrub

Goal: stop all client scrubbing now, recoverably, without ripping out code (so
the regex rules survive as reference for the server port).

**Single chokepoint.** `runAutoscrub()` in `EditorPanel.vue` is the sole entry
point — the interval timer and the 5s debounce both call it, and it is what
emits `autoscrub-all-items` to `ContentEditor`. An early `return` at its top
disables: the interval scrub, the debounced scrub, the open-item scrub
(`autoscrubContent`), the orphaned-cursor-marker cleanup, AND the
`autoscrub-all-items` emit (so `ContentEditor.autoscrubAllItems` never fires).
**One function, one file — `ContentEditor.vue` needs no change.**

Implementation: gate with a clearly-named constant, e.g.
`const AUTOSCRUB_DISABLED = true;` checked at the top of `runAutoscrub()`, with
a comment pointing here. Leave `autoscrubContent()`,
`autoscrubAllItems()`, the timers, and the settings wiring intact (dormant).

Caveat to preserve: `smartCleanupOrphanedCursorMarkers()` (stripping stray `█`
cursor chars) also runs inside `runAutoscrub()`. If that cleanup is still
wanted while Autoscrub is off, call it from a separate small timer instead of
gating it behind the same flag. Otherwise it stops too — confirm with Kevin
which behavior is intended.

**Coordination:** the disable edits `EditorPanel.vue`, which overlaps sibling
746024's todo #37 ("remove Caller/Director/Prompter view stubs — EditorPanel").
Apply only after that lane clears; rebase against their changes first.

## Full refactor: Autoscrub on the server

### Design

One **shared normalization function** in Python (e.g.
`app/services/script_scrub_service.py`) that takes a `script_content` string +
the resolved settings and returns the scrubbed string (+ any
needs-attention flags). Two callers:

1. **Celery beat job** (every `autoscrubInterval`s) — normalizes every rundown
   item in active episodes **except items currently being edited**. You already
   run Celery + Redis; add a `scrub` periodic task.
2. **Save endpoint** — scrubs the single item being saved as it lands, so the
   focused item is normalized on save without a 30s wait.

### The open-editor problem (the hard part)

Do **not** let the server rewrite `script_content` for the item a user is
actively editing — that reintroduces the clobbering/cursor-jump problem from
the opposite direction. Two-part answer:

- The beat job skips items with a recent edit (a `last_edited_at` / soft-lock
  signal), or all items currently open in a session.
- Keep a **minimal** client scrub for the focused item, run only on
  blur/save (the safe slice), OR rely on the save-endpoint scrub. This means
  the client code shrinks but is not fully deleted.

### Settings

Move the admin-configured toggles out of `localStorage` into a server-readable
home (the existing settings / `api_configs` tables) so the worker reads them.
Keep the Settings UI writing to the same place.

### Behavior change to be deliberate about

The `data-needs-attention` flagging is **semantic**, not cosmetic: it drives UI
markers and is checked by `findUnresolvedRevisions()` before script generation.
Moving it server-side changes *when* flags appear (every beat tick vs. live in
the browser). Probably an improvement, but call it out — don't let it surprise
anyone gating script generation on those flags.

### Multi-user payoff

A server scrub is the first real consumer of `refreshAllItemContentInPlace()`
(added in `ContentEditor.vue`): server scrubs → emit a "rundown changed"
Server-Sent Event (see [`docs/SSE_JOB_STATUS_PLAN.md`](SSE_JOB_STATUS_PLAN.md),
standing todo #24) → connected clients live-refresh other users' normalized
content in place, no page reload, selection preserved. The three pieces
(server scrub + SSE channel + the refresh handler) compose cleanly.

## Files

Interim:
- `disaffected-ui/src/components/content-editor/EditorPanel.vue` —
  `runAutoscrub()` guard (single edit).

Full refactor:
- `app/services/script_scrub_service.py` (new) — shared normalizer.
- `app/celery_app.py` — register periodic `scrub` task.
- the rundown-item save endpoint — call the normalizer on save.
- settings tables + Settings UI — relocate `autoscrub*` config.
- `disaffected-ui/src/components/content-editor/EditorPanel.vue` /
  `ContentEditor.vue` — remove `autoscrubAllItems` + shrink the client scrub to
  focused-item-on-save (or remove entirely if the save-endpoint scrub covers
  it).
- SSE channel (per the SSE plan) → `refreshAllItemContentInPlace()`.

## Verification

Interim: with the flag on, no content is rewritten on the 30s/5s timers; no
cursor jumps; manual edits + normal autosave still work; the
`autoscrub-all-items` path is silent.

Full: a pasted Google-Docs blob in an idle item gets its spans/divs stripped
within one beat tick server-side; the item being typed is never rewritten
mid-edit; invalid-cue flags still appear and still block script generation; a
second user viewing the rundown sees normalized content refresh in place once
the SSE channel exists.
