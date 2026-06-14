# TipTap Merge → Live: Reconciliation Resume Guide

**Saved:** 2026-06-13. Session "Showbuild Merge".
**Goal:** Get `feat/script-editor-tiptap` (new ProseMirror script editor) safely onto
`main` / live showbuild.app, WITHOUT losing live-only SOT/media hotfixes.

---

## ⚠️ NOTHING IS LIVE YET. Live is untouched.

- **Live** = `/srv/show-build`, branch `main`, HEAD `0666277`. **Unchanged.** Not touched.
- **All work** is on branch **`reconcile/tiptap-sot-merge`** in the **dev folder**
  `/home/kevin/show-build-migration`. This is dev only.
- Live DB and live server: **NOT modified, NOT restarted.**

---

## Why this got complicated (the core finding)

A plain merge of feat→main looked clean, BUT the live folder `/srv/show-build` had
~1,500 lines of **uncommitted, live-only hotfixes** (SOT/ffmpeg/media/celery). A merge
would have silently erased them. So:

1. Live DB fully backed up → `/mnt/sync/disaffected/backups/pre-tiptap-merge-20260613/showbuild_full.dump` (68MB, verified).
2. Live uncommitted work snapshotted → branch **`live-wip-snapshot-20260613`** (commit `a1a8ca7`). Nothing lost.
3. Reconciling those hotfixes onto the feat branch, file by file, on `reconcile/tiptap-sot-merge`.

---

## Reconciliation progress (7 diverged files)

| File | Status | What was done |
|---|---|---|
| `mediaUpload.js` | ✅ DONE (`f60a895`) | Took live (adds `uploadVideoChunked` for >100MB). feat never touched it. |
| `useWaveform.js` | ✅ DONE (`f60a895`) | Took live (`hasNoAudio` + EncodingError guard). feat never touched it. |
| `celery_app.py` | ✅ DONE (`f60a895`) | Appended live's `worker_process_init` engine.dispose() (fork-safe DB pool). |
| `asset_processing.py` | ✅ DONE (`f60a895`) | Union: feat's `generate_fsq_png` regen + live's `_wrap_text`/`generate_gfx_png` blank-line fixes. |
| `llm_state_router.py` | ✅ DONE (no-op) | feat DELETED the broken endpoint — supersedes live's band-aid. Nothing to port. |
| `SotModal.vue` | ✅ DONE (`146119c`) | 3-way merge (git merge-file, 0 conflicts): feat UI restructure + live chunked-upload. Lint clean. |
| `ffmpeg_tasks.py` | ✅ DONE (`3c6540d`) | Ported both live hotfixes onto feat's 3-task chain: frame-accurate trim (sot_prepare Phase 3, both branches) + silent-audio injection (sot_finalize Phase 6, then has_audio=True). py_compile clean. |

**✅ ALL 7 FILES RECONCILED as of `3c6540d`.** Remaining work is build + test + deploy (below).

---

## ⛔ REMAINING WORK: `ffmpeg_tasks.py` (the SOT video engine)

**This is the only file left, and it's the on-air-critical one.**

feat REWROTE the monolithic `process_sot_video_multi_phase` into a 3-task Celery chain:
- `sot_prepare` (Phases 1-3: validate, probe, **trim EARLY**, extract audio)
- `transcribe_sot_audio` (Phase 4)
- `sot_finalize` (Phases 5-11: analyze, **normalize video Phase 6**, channels, loudness, mp3, move-to-assets)

The rewrite **LOST two live hotfixes** that must be re-implemented into the new structure:

1. **Frame-accurate trim** — feat's `sot_prepare` Phase 3 trim uses `-c copy`
   (keyframe-bounded, overruns OUT by ~1 GOP). Live re-encoded with
   `video_encoder_args` (nvenc h264 / libx264 fallback — see `process_vo_montage`
   for the exact pattern) + AAC. Apply to BOTH trim branches (with-end, from-start).

2. **Silent-audio injection** — feat's `sot_finalize` Phase 6 normalization uses
   `-an` / skips audio when source has no audio track. Live injected
   `-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000`, mapped
   `0:v:0`+anullsrc audio, AAC 192k/48k/stereo, `-shortest`, then set
   `has_audio = True` so downstream audio phases (channels, loudness, mp3) run.

**See the exact live code to port:**
```
cd /home/kevin/show-build-migration
git diff $(git merge-base main feat/script-editor-tiptap) live-wip-snapshot-20260613 -- app/services/ffmpeg_tasks.py
```
Three versions saved (may be gone after reboot — regenerate from git if so):
- merge-base: `/tmp/ff.base.py` | feat: `/tmp/ff.feat.py` | live: `/tmp/ff.live.py`

The auto 3-way merge left **2 conflicts** (around feat lines ~2568 and ~2758) — do NOT
just accept it; re-implement the two behaviors by hand into feat's structure.

After editing: `python3 -m py_compile app/services/ffmpeg_tasks.py`

---

## AFTER ffmpeg_tasks.py is reconciled — remaining steps to go live

1. **Build frontend** in dev folder: `cd disaffected-ui && npm run lint -- --fix && npm run build`
2. **Test SOT end-to-end on DEV** (dev.showbuild.app / :8889) — upload, trim, audioless
   case, multi-clip. This is mandatory; SOT engine regressions break on-air.
3. **Merge** `reconcile/tiptap-sot-merge` → `feat/script-editor-tiptap` → then into `main`
   (or merge reconcile straight to main once proven).
4. **Live deploy:**
   - `cd /srv/show-build && git merge <reconciled branch>` (main is clean at 0666277).
   - Live DB migration: live `showbuild` is at `g019`; needs `g020_normalize_color_keys`
     + `g021_add_slug_gen_history` (both additive/idempotent, already verified safe).
     Run `alembic upgrade head`.
   - **Restart live backend** (NOT hot-reloaded): `docker compose restart server`.
   - **Restart BOTH prefect AND kairo media workers** (ffmpeg_tasks change — kairo has
     historically diverged; file edit alone won't take). 
   - Rebuild/redeploy frontend on live.

---

## Safety / rollback levers already in place

- **Editor kill-switch** (commit `2380999`): if the new editor misbehaves live, in the
  affected browser run `localStorage.setItem('ff:useProseMirrorEditor','false')` + reload
  → falls back to the legacy contenteditable editor. No redeploy needed.
- **DB backup:** `/mnt/sync/disaffected/backups/pre-tiptap-merge-20260613/showbuild_full.dump`
- **Live WIP snapshot branch:** `live-wip-snapshot-20260613` (`a1a8ca7`) — the original
  live hotfixes, in case any reconciliation needs re-checking.
- **Secrets:** `app/storage/api_keys.json` + `users.json` now gitignored. NOTE: pre-existing
  `*.backup_20250810_*` files with real secrets are ALREADY committed on live `main` —
  recommend rotating that admin password + API key separately (out of scope here).

## Branch map
- `main` — live, untouched, `0666277`
- `feat/script-editor-tiptap` — migration branch, `2380999` (kill-switch + WIP committed)
- `reconcile/tiptap-sot-merge` — **WORK HERE**, `146119c`, 6 of 7 files reconciled
- `live-wip-snapshot-20260613` — rescued live hotfixes, `a1a8ca7`
