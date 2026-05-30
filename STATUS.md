# Script Editor Migration — Status & Resume Guide

**Last updated:** 2026-05-30
**Branch:** `feat/script-editor-tiptap` (worktree at `/home/kevin/show-build-migration`)
**Base/live:** `main` (live `showbuild.app`, untouched, old editor)
**Plan:** `docs/SCRIPT_EDITOR_MIGRATION_PLAN.md`

---

## TL;DR — where we are

Migrating Script Mode from the legacy contenteditable editor to a TipTap/ProseMirror
editor. **Phases 0–4 done + Phase 5 started.** The new editor renders, is wired into
the real `ContentEditor` behind a flag (default ON for the dev site), and we're now
fixing real-world editing behaviors. Last work: making the slash (`/`) cue menu launch
the real cue modals and ensuring cue insertion (incl. SOT processing) reaches the new
editor.

**Live (`showbuild.app`) is completely unaffected** — all work is on the migration
branch / dev environment.

---

## Phases complete (committed on the branch)

- **Phase 0** — round-trip gate PASSED (18 real episode scripts, 0 loss).
- **Phase 1** — production markdown↔ProseMirror parser/serializer + loss assertion + 19 unit tests (`src/utils/prosemirror/`).
- **Phase 2** — TipTap cue NodeView (reuses existing cue cards) + paragraph extension.
- **Phase 3** — revision mark, paragraph commands, keyboard shortcuts, extension bundle.
- **Phase 4** — `ScriptEditor.vue` wired INTO `EditorPanel` behind `useProseMirrorEditor` flag (swaps only the contenteditable surface; toolbar/modes/cue chrome stay). Cue cards render (Vuetify context via `<EditorContent>`).
- **Phase 5 (part 1)** — parity gate: new editor proven a strict superset of legacy.

## Editor-experience work done since Phase 5

- **Slash command** (`/`) opens a cue menu at the caret → launches the SAME modal the ADD CUE buttons launch (via `insertCueFromMenu`). NOT a bare-node insert. Files: `prosemirror/SlashCommand.js`, `CueSlashMenu.vue`, `extensions.js`, `ScriptEditor.vue`, `EditorPanel.vue`.
- **Cue insertion reaches the new editor:** `insertCueAtSnapshotPosition` (EditorPanel) now, when `useProseMirrorEditor` is on, appends the cue block straight to `rawScriptContent` (the new editor watches `scriptContent` and reloads). One source-level guard covers FSQ/SOT/VOX/MUS/LIVE/IMG + the multi-SOT loop. SOT `triggerSOTProcessing` unchanged (Celery kickoff intact).
- **Admin-only Development → Wireframes** nav + `/dev/wireframes` page + interactive region wireframe (`public/wireframes/content-editor-wireframe.html`; double-click a region to copy a focus prompt).

## Bug fixes landed on `main` (live) along the way

- `a72bbe3` — **cueParser data-loss fixes** (catastrophic bare-markdown-wipe BUG 1 + field-drop BUG 3). Real production fix.
- `abf92fc` — **fast `/health/critical` + `/health/secondary`** split (dashboard flash on live too).
- `ef49ca4` — `docker-compose.dev.yml` (opt-in dev backend).

---

## ⚠️ OPEN ITEMS / what to test next

1. **Verify SOT end-to-end** (was mid-test at pause): `/` → SOT → "Insert and Begin Processing" → cue appears in editor AND Celery processing kicks off. Console shows `📍 ProseMirror active — appended cue to rawScriptContent` when the new path fires.
2. **Test the other cue types** through `/` (FSQ, GFX, IMG, VO, NAT, PKG, NOTE, BUMP, STING, RIF) — confirm modal opens + cue inserts.
3. **Cue insertion position** — cues currently land at the END of the script (legacy behavior). May want at-caret insertion as a follow-up.
4. **todo #30** — `llm_notifications` model/table schema mismatch (500 on `/api/llm/notifications`); currently a graceful empty-list band-aid in `app/llm_state_router.py`. Real fix: one shared model matching the real `asset_id`-shaped table.
5. **Phase 5 remainder** — full chrome parity, then flip default on main, then delete the ~55 legacy contenteditable band-aids (LAST).

---

## Dev environment (how to bring it back up)

The dev stack is **separate from live** and was shut down at pause. To resume:

1. **Dev backend** (points at `showbuild_dev` DB copy, 6 workers):
   `cd /srv/show-build && docker compose -f docker-compose.dev.yml up -d`
2. **Dev frontend** (MUST set the env var, or the reload loop returns):
   `cd /home/kevin/show-build-migration/disaffected-ui && DEV_API_TARGET=http://localhost:8889 node_modules/.bin/vue-cli-service serve --port 8092`
   (Verify env landed: `cat /proc/<pid>/environ | tr '\0' '\n' | grep DEV_API_TARGET`)
3. **Refresh dev DB from live** (optional): `scripts/mirror_live_to_dev_db.sh`
4. **Access:** `https://dev.showbuild.app` (Cloudflare cache is bypassed for it now) OR `https://192.168.51.238:8092` (LAN, no Cloudflare). Log in as `kevin` (admin) → new editor is default-on.

**Reload-loop gotchas (all fixed, don't reintroduce):** HMR disabled for the tunnel dev server (`DEV_API_TARGET` gate in `vue.config.js`); Cloudflare cache-bypass rule on `dev.showbuild.app` (token at `/srv/show-build/.cloudflare-token`, gitignored). See memory `project_dev_cloudflare_cache`.

---

## Key files

- `src/utils/prosemirror/{schema,markdown}.js` — the markdown↔doc engine (source of truth for save format).
- `src/components/content-editor/ScriptEditor.vue` — the TipTap editor component.
- `src/components/content-editor/prosemirror/` — extensions (CueNode, CueNodeView, ScriptParagraph, RevisionMark, SlashCommand, CueSlashMenu, extensions.js).
- `src/components/content-editor/EditorPanel.vue` — hosts the swap (`useProseMirrorEditor` flag); `insertCueAtSnapshotPosition` has the cue-insert guard.
- `src/composables/useFeatureFlags.js` — `useProseMirrorEditor` default (currently `true` for dev).
