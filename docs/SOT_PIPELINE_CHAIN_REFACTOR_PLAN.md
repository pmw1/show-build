# SOT Pipeline — Celery Chain Refactor + Phase Renumber (PLAN)

**Status:** draft for review · 2026-06-04 · prefect-show-build-claude-63ebeb
**Why:** `process_sot_video_multi_phase` calls `transcribe_sot_audio.apply_async(...).get(timeout=600)`
mid-job. Celery forbids a task waiting on a subtask (`Never call result.get() within a task!`),
so transcription now FAILS (seen on the "kevin single trim" test). Fix: restructure so nothing
blocks on a subtask, AND renumber the phases to clean sequential integers (no more `0.5`/`1.1`/`2.5`).

---

## Current pipeline (verified from code)

Two duplicate phase implementations exist:
- **`process_sot_video_multi_phase`** (lines ~1959-3055) — the `single_trim`/`full_process` path
- **`_process_single_clip`** (~1371-1553) — used by `montage` (and the DEPRECATED `individual_clips`)

Main path phases + the `_update_job_status` string they emit (what the frontend reads as `current_phase`):

| Order | code label | status string | does | transcription? | fails how |
|---|---|---|---|---|---|
| 1 | validation | `validation` | size/duration/res checks | no | raises ValueError |
| 2 | Phase 0 | `phase0` | ffprobe analysis | no | raises |
| 3 | **Phase 0.5** | `phase0.5` | audio extract + **Whisper transcribe** + outcue | **YES (.get blocker)** | non-fatal, stores error |
| 4 | Phase 1 | `phase1` | video normalize (H.264) | no | raises |
| 5 | **Phase 1.1** | `phase1.1` | audio channel fix (dual-mono) | no | non-fatal |
| 6 | Phase 2 | `phase2` | audio loudness (EBU R128) | no | raises |
| 7 | Phase 3 | `phase3` | trim (if needed) | no | raises |
| 8 | Phase 4 | `phase4` | 15 thumbnails + MP3 | no | mostly non-fatal |
| 9 | Phase 5 | `phase5` | move to final assets + DB final paths | no | raises |
| 10 | Phase 8 | `phase8` | post-analysis (re-probe final) | no | raises |

Frontend touchpoints that read `current_phase`: `SotCueContent.vue`, `useSOTProcessing.js`,
`PlaceholderCueCard.vue`. They display the string; `useSOTProcessing.js` prefers
`job.phase_message || job.current_phase`. **None hard-match specific phase strings for logic**
(they're shown, not branched on) — confirmed by the map. So renumbering is display-safe as long
as we also set a human `phase_message`.

---

## Design decision: chain vs "callback for transcription only"

The blocker is ONLY the transcription `.get()`. The other phases are plain ffmpeg subprocess calls
in-process — they are NOT subtasks and have no Celery-rule problem. So a full N-task chain is more
restructuring than the bug requires. **Recommended scope: minimal correct async** — make the whole
pipeline a Celery `chain` of THREE tasks split at the transcription boundary, NOT 10 tasks:

```
chain(
  sot_prepare,          # phases 1-3: validate + raw probe + TRIM + extract audio (from trimmed) -> ctx + wav
  transcribe_sot_audio, # phase 4: the EXISTING whisper-queue task, as a real chain link (no .get!)
  sot_finalize,         # phases 5-11: analyze-trimmed + normalize/audio/thumbs/move/verify
)
```
(Trim moved into `sot_prepare` BEFORE the audio extract, so the whisper link transcribes the
trimmed audio, and `sot_finalize`'s first step (phase 5 analyze) measures the trimmed clip.)

- `transcribe_sot_audio` becomes a genuine chain link: its return value (the transcript string) is
  passed as the first arg to `sot_finalize` by Celery — **no `.get()`, no blocking, rule satisfied.**
- The whisper task still runs on the dedicated `whisper` queue (load-balanced across .210/kairo).
- `sot_prepare` + `sot_finalize` run on the `media` queue.
- If transcription fails, the chain link returns a sentinel (`[Transcription failed: ...]`) instead
  of raising, so `sot_finalize` still runs (preserves today's non-fatal behavior).

This keeps the dedicated whisper pool, removes the `.get()` bug, and is FAR less risky than
splitting all 10 phases. `_process_single_clip` (montage) gets the same 3-way split.

**Trade-off vs full per-phase chain:** we don't get per-phase retry/visibility as separate tasks.
But the phases inside `sot_prepare`/`sot_finalize` already track progress via `_update_job_status`,
so the frontend still sees every phase advance. Full per-phase chaining can be a later step if you
want per-phase Celery retries; it is not needed to fix the bug or to renumber.

> NOTE: user asked for "full chain refactor." If you want literally one task per phase (10 links),
> say so and I'll expand `sot_finalize` into chained links. The 3-task split is my recommendation
> because it fixes the bug + renumbers with materially less risk on fragile code. **DECISION NEEDED.**

---

## CORRECTED PHASE ORDER (fixes the trim-ordering bug) + integer renumber

**Bug found 2026-06-04 (Kevin):** the current code TRIMS LATE (old `phase3`, after transcribe +
analyze). But transcription reads the raw `_upload.mp4`, and `phase0` analysis measures it too. So
when a user trims, the **transcription, the outcue (last-5-words), and the displayed duration are all
computed on content the user CUT AWAY** — wrong metadata written to the cue block. (Thumbnails were
fine — they ran post-trim — and `phase8` re-probes the final file, also fine.)

**Fix:** trim EARLY, then transcribe + analyze the TRIMMED result. Two analyze passes (per Kevin's
suggestion): a cheap *raw probe* up front just to validate the input is sane (dimensions/codec/has-
audio) before doing work, and the *real metadata analyze* AFTER trim that populates the cue block.

New order, renumbered as clean integers starting at 1 — applied consistently across BOTH functions,
the docstrings, every `_update_job_status` string, plus a `phase_message` (human label) written
alongside each. Frontend already prefers `phase_message` over the raw string.

| new # | status string | phase_message | runs on | from old |
|---|---|---|---|---|
| 1 | `phase1` | "Validating upload" | media (prepare) | validation |
| 2 | `phase2` | "Probing source" | media (prepare) | phase0 (raw probe, sanity only) |
| 3 | `phase3` | "Trimming" | media (prepare) | **phase3 trim — MOVED UP** |
| 4 | `phase4` | "Transcribing audio" | **whisper** | phase0.5 — now on the TRIMMED clip |
| 5 | `phase5` | "Analyzing trimmed clip" | media (finalize) | NEW 2nd analyze → real cue metadata (duration etc.) |
| 6 | `phase6` | "Normalizing video" | media (finalize) | phase1 |
| 7 | `phase7` | "Fixing audio channels" | media (finalize) | phase1.1 |
| 8 | `phase8` | "Normalizing loudness" | media (finalize) | phase2 |
| 9 | `phase9` | "Generating thumbnails + MP3" | media (finalize) | phase4 |
| 10 | `phase10` | "Moving to assets" | media (finalize) | phase5 |
| 11 | `phase11` | "Verifying output" | media (finalize) | phase8 (post-analysis) |
| — | `complete` | "Complete" | — | complete |

Notes:
- The **transcript + outcue (phase 4) and the cue-block duration/metadata (phase 5) are now computed
  on the trimmed clip** — correct.
- Phase 2 (raw probe) stays cheap: it only validates the input and detects `has_audio`; it does NOT
  write the user-facing duration (phase 5 does, post-trim).
- Chain seam is unchanged in spirit: `sot_prepare` now covers phases 1-3 (validate, probe, trim),
  `transcribe_sot_audio` is phase 4 (whisper link), `sot_finalize` covers phases 5-11.
- Working-dir intermediate filenames renumber to match (e.g. `_3_trimmed.mp4`, `_4_audio.wav`) —
  internal only, no external consumer.
- If NO trim is requested, phase 3 is a no-op pass-through (transcribe/analyze just run on the
  upload, which equals the trimmed result) — same correctness, no wasted work.

---

## Scope per workflow (which fix touches what)

Two distinct fixes, different blast radius:

| job_type | function | `.get()` bug? | trim-order bug? | action |
|---|---|---|---|---|
| `single_trim` / `full_process` | `process_sot_video_multi_phase` | YES | **YES** (trims late, after transcribe) | chain split + trim-early reorder + renumber |
| `montage` | `_process_montage` → `_process_single_clip` | YES | **NO** | chain/`.get()` fix only — trim already happens upstream (clips are extracted/trimmed BEFORE `_process_single_clip`, whose own "Phase 3 trim" is a deliberate no-op). Its phase 0.5 already transcribes trimmed content. |
| `individual_clips` | `_process_individual_clips` | n/a | n/a | DEPRECATED — raises DeprecationWarning, doesn't run. Leave as-is. |

So: the **`.get()`/chain fix applies to BOTH** `process_sot_video_multi_phase` AND `_process_single_clip`
(both call `transcribe_sot_audio.apply_async(...).get()` → both would hit the Celery error). The
**trim-early reorder is ONLY for the single_trim/full_process path** — montage is already correct and
must NOT be reordered (its trim is the upstream clip extraction).

## Progress reporting contract (preserved across the chain)

The worker reports phase progress to ShowBuild via two existing helpers, and EVERY chain link must
keep calling them so the cue block stays live:

1. `_update_job_status(temp_job_id, 'phaseN', 'processing'|'completed'|'failed')` — writes
   `current_phase` + `status` to the `sot_processing_jobs` DB row at the START of each phase. The
   frontend (`useSOTProcessing.js`) reads this and shows the current phase. Also write
   `phase_message` (human label) so the UI shows "Transcribing audio" not "phase4".
2. `_update_sot_cue_block(episode, slug, asset_id, {...})` — writes into the actual cue block in the
   rundown item's `script_content` (ProcessingStatus, Transcription, Outcue, Duration, MediaURL,
   ThumbnailURL, ...) at the phases that produce those fields.

Rules for the refactor:
- Each of the 3 chain tasks (`sot_prepare`, `transcribe_sot_audio`, `sot_finalize`) calls these
  helpers at each phase boundary it owns, keyed by the SAME `temp_job_id` + `episode/slug/asset_id`
  threaded through the chain context. No phase goes dark.
- **`transcribe_sot_audio` (phase 4) runs on a REMOTE worker (.210/kairo)** — it must reach
  `showbuild_dev` to call `_update_job_status`/`_update_sot_cue_block` (network DB; confirmed
  reachable). So it emits "phase4 processing" on start and writes Transcription+Outcue on success —
  the cue won't appear stalled during transcription.
- On chain-link failure, that link writes `status='failed'` + `error_message` so ShowBuild reflects
  the failure on the right phase.
- NOTE: reporting is POLL-based (frontend reads the DB row on a timer), so updates appear with a
  small lag, not instant push. Moving SOT status to SSE/push is the separate standing todo #24 —
  out of scope here.

## Execution steps (after you approve)

1. Add `phase_message` column handling (the model may already allow it; verify — if not, a tiny
   migration or reuse an existing field). Frontend already prefers `phase_message`.
2. Write `sot_prepare` + `sot_finalize` tasks (media queue); fold the existing phase code into them
   unchanged except the renumbered status strings + the transcript-passing seam.
3. Make `transcribe_sot_audio` chain-friendly (accept being a link; return transcript or sentinel).
4. Replace the body of `process_sot_video_multi_phase` with: build inputs, then
   `chain(sot_prepare.s(...), transcribe_sot_audio.s(), sot_finalize.s(...)).apply_async()`.
   (It becomes the orchestrator; returns the chain's AsyncResult id.)
5. Same 3-way split for `_process_single_clip` (montage path).
6. Renumber every `_update_job_status` string + docstrings.
7. Update the 3 frontend files to map the new strings to display text (cosmetic).
8. Lint, restart dev workers, run a real dev SOT, confirm: transcription succeeds via whisper
   worker (no `.get` error), all phases advance, final assets land, no regression.

## Risk / rollback
- Highest-risk change of the session; on the most fragile code. Done on DEV only first.
- Rollback = git revert the commit; dev workers restart on old code.
- The "kevin single trim" failure is the test case to confirm fixed.
