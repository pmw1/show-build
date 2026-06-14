# Phase 0 Findings — Round-Trip Baseline (legacy CueParser)

**Worktree:** `/home/kevin/show-build-migration` · branch `feat/script-editor-tiptap`
**Date:** 2026-05-30
**Corpus:** 18 real `rundown_items.script_content` values pulled from the live DB
(cue-heavy, mixed-case cue types, bare-markdown, largest items, `dir`/`bump`/`Break` casing).
Harness: `baseline_roundtrip.mjs`, `value_fidelity.mjs`, `diff_one.mjs`.

## Purpose
Establish what the EXISTING `parseContent → formatForCard → reconstructContent`
pipeline already does to real content, so the ProseMirror round-trip can be held
to the right bar: **lose no more than the legacy round-trip — ideally nothing.**

## Headline results (production path: parse → formatForCard → reconstruct)
- **Cue count preserved: 18/18.** No cue block is lost on the production path.
  (NOTE: the *naive* path `parse → reconstruct` WITHOUT `formatForCard` drops
  ALL cues, because `reconstructContent` serializes from `data.rawData`, which only
  `formatForCard` populates. The editor always runs `formatForCard`, so production
  is safe — but this is a fragile coupling the ProseMirror model should remove by
  making the document the source of truth, not a `rawData` back-pointer.)
- **Byte-exact: 5/18.** The legacy round-trip is NOT byte-lossless even in normal use.
- **Most byte-diffs are cosmetic** and re-parse identically (see Mutation Classes).

## Mutation classes (cosmetic — no value lost)
1. **Bare text → `<p class="josh">…</p>` wrapping.** Raw markdown headings/paragraphs
   (`## Notes`, bare lines) get wrapped on reconstruct. Re-parses identically.
2. **Cue field label casing drift.** `[AssetID:]` → `[Asset Id:]`, `[MediaURL:]` →
   `[Media Url:]` via `toCamelCase` → `formatFieldForDisplay`. Value unchanged.
3. **Field reorder + empty-field pruning.** Fields reorder to priority order
   (`type, assetId, slug, duration, description` first); empty fields like
   `[Description: ]` are dropped. No information lost.

## ⚠️ REAL data-loss bugs found in the legacy parser (must NOT be carried forward)

### BUG 1 — CATASTROPHIC: bare markdown + one stray `<p>` tag wipes the script
**Item 13: 943 bytes → 20 bytes. Entire script destroyed.**
- Content is plain markdown (`## Notes`, `## Description`, `## Script`, body) with a
  single stray empty `<p class="josh"></p>` at the end.
- `parseTextSegments` detects ANY `<p>` tag via regex; finding the one empty tag, it
  takes the "has `<p>` tags" branch and processes ONLY the matched `<p>` elements —
  **silently discarding all surrounding bare-markdown text.**
- Result: 900+ chars collapse to a single empty paragraph.
- **This is almost certainly related to the 0272/0273 silent-shrink incidents.** The
  existing `safeEmitScriptContent` tripwires would catch the *save*, but the parser
  itself is the culprit.
- **ProseMirror implication:** the markdown→doc parser MUST handle mixed bare-markdown
  + HTML paragraphs without discarding the bare text. A real grammar (parse the whole
  string into blocks) instead of "regex for `<p>`, else treat-as-raw" eliminates this
  entire failure mode.

### BUG 2 — MINOR: `[MediaURL:]` dropped when an `<img>` is present
**Items 24, 29 (GFX/IMG cues).**
- When a GFX/IMG cue has both `[MediaURL: path]` and an embedded `<img src="path">`,
  the explicit `[MediaURL:]` line is dropped on reconstruct (the path survives via the
  `<img>` tag, so no *value* is truly lost, but the structured field is gone).
- **ProseMirror implication:** model `mediaUrl` and the image as distinct cue attrs and
  serialize both; don't let one absorb the other.

## False positives in the value-fidelity classifier (for the record)
`value_fidelity.mjs` flagged "lost slug" on items 24/21/29 — these are FALSE. The
classifier keyed cue fields per-document (Set of values per label) rather than per-cue;
multiple GFX cues share the label `slug` with different values, so set-diff mis-flagged
them. Manual check confirmed every slug survives. The classifier needs per-cue keying
(a Phase-1 todo for the serializer's loss-assertion).

## The bar for the ProseMirror round-trip
1. **Lose zero cues** (legacy already achieves this on the production path).
2. **Lose zero cue field VALUES** (legacy achieves this; BUG 2 is a structural-field nit).
3. **Lose zero paragraph TEXT** — legacy FAILS this (BUG 1); ProseMirror must FIX it.
4. Cosmetic normalization (label casing, field order, `<p>` wrapping) is acceptable and
   expected, provided it re-parses stably (idempotent: `f(f(x)) == f(x)`).

## ✅ PHASE 0 RESULT — GATE PASSED (2026-05-30)

Built a ProseMirror schema (`pm_schema.mjs`: `doc -> (paragraph | cue)+`, cue as an
open-ended atom with an ordered `fields` map + distinct `imgTag`) and a markdown↔doc
round-trip. Ran the 18-item real corpus through it (`pm_roundtrip.mjs`):

| Criterion | Legacy | ProseMirror |
|---|---|---|
| cue count preserved | 18/18 | **18/18** |
| cue field values kept | 18/18* | **18/18** |
| paragraph TEXT kept | **15/18 (BUG 1)** | **18/18 ✅** |
| idempotent | n/a | **18/18 ✅** |

The ProseMirror model **clears the bar on every real item** and **fixes BUG 1** (the
catastrophic bare-markdown wipe). Conclusion: **the migration is viable — proceed to
Phase 1.**

### A third bug found and fixed during the proof
**BUG 3 — non-idempotent field parse when a `[Field:]` is immediately followed by `<img>`.**
The cue field-terminator lookahead originally accepted only `\n[`, `\n<!--`, or end.
A field line directly before an `<img>` line (common in GFX/IMG cues) failed to match on
re-parse, silently dropping that field on the SECOND round-trip. Fixed by adding `\n<img`
as a valid terminator in `pm_schema.mjs`. **The legacy `cueParser.js` has the SAME regex
and likely the SAME latent bug** — worth back-porting the one-line fix to production
independent of the migration.

## Next (Phase 1)
- Build the ProseMirror schema (`paragraph` + open-ended `cue` atom) and a
  markdown↔doc parser/serializer that:
  - parses the WHOLE string into blocks (fixes BUG 1),
  - keeps `mediaUrl` + image as distinct attrs (fixes BUG 2),
  - is idempotent under round-trip,
  - carries a per-cue loss-assertion (successor to `safeEmitScriptContent`).
- Re-run this corpus through the new round-trip; require: 0 cue loss, 0 value loss,
  0 paragraph-text loss, and idempotency on the second pass.
