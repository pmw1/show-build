# Legacy Cue Convert

Self-contained module that converts legacy `{SOT/foo}` and `(SOT/foo)`
style tokens — the kind that show up when scripts are pasted from
Google Docs or other external sources — into real cue blocks with
proper AssetIDs, default durations, and (when possible) auto-linked
media files from the episode's `preshow/` folder.

## Why this exists

The editor's **Auto Scrub** feature (in `EditorPanel.vue`'s
`applyAutoFormatting`) detects legacy tokens and flags the paragraph
with `data-needs-attention="true"` + `data-flag-note="Invalid cue
code"` + a leading `***` prefix. Until now, fixing those flags meant
hand-typing the proper cue block. This module adds a **"Convert to
Cue"** button on the flag-note panel that does the cleanup in one
click while preserving any prose around the token.

## Public API

Import from `@/modules/legacyCueConvert`:

| Export | Purpose |
|---|---|
| `LEGACY_CUE_REGEX` | The pattern that matches legacy tokens. Imported by Auto Scrub in `EditorPanel.vue`. Single source of truth — don't define it again anywhere else. |
| `LEGACY_CUE_REGEX_GLOBAL` | Same pattern with the `g` flag for `matchAll()` over multi-token paragraphs. |
| `LEGACY_CUE_FLAG_LABEL` | The exact string Auto Scrub writes to `data-flag-note` when a paragraph contains a legacy token. The button checks this to decide whether to render. |
| `ALIAS_MAP` | Token-type → canonical cue type. `VOT→SOT` (typo), `DIR→NOTE`, `FS QUOTE→FSQ`, others identity. `CUE` intentionally absent (unconvertible). |
| `DEFAULT_DURATION_BY_TYPE` | Per-type `[Duration]` defaults. Currently hand-mirrored from each modal — see *current vs future state* below. |
| `MEDIA_BEARING_TYPES` | Set of canonical types that trigger a `find-media` lookup in `preshow/`. |
| `normalizeTokenType(raw)` | Helper: uppercase + strip whitespace. |
| `sanitizeSlug(raw)` | Mirror of `ImgCueModal.sanitizeSlug`. |
| `convertLegacyToken({ paragraphSegment, episode, segmentId })` | Async; returns `{ replacementSegments, audit }` for splicing into `scriptSegments`. |
| `ConvertButton` | Vue 3 component to drop into the flag-note action row. Emits `converted` with the splice payload. |
| `useLegacyCueConvertEnabled()` | Composable: `{ enabled, setEnabled }` backed by localStorage. Default `true`. |

## Wiring

### EditorPanel.vue
```vue
<script setup>
import {
  LEGACY_CUE_REGEX,
  LEGACY_CUE_FLAG_LABEL,
  ConvertButton,
  useLegacyCueConvertEnabled,
} from '@/modules/legacyCueConvert'

const { enabled: legacyCueConvertEnabled } = useLegacyCueConvertEnabled()

function onLegacyCueConverted({ replacementSegments, segmentIndex }) {
  const next = [...scriptSegments.value]
  next.splice(segmentIndex, 1, ...replacementSegments)
  scriptSegments.value = next  // routes through safeEmitScriptContent guards
}
</script>

<template>
  <!-- inside the flag-note panel action row -->
  <ConvertButton
    v-if="legacyCueConvertEnabled && segment.flagNote === LEGACY_CUE_FLAG_LABEL"
    :paragraph-segment="segment"
    :segment-index="index"
    :episode="currentEpisode"
    :segment-id="currentItem?.id ?? null"
    @converted="onLegacyCueConverted"
  />
</template>
```

Auto Scrub's regex definition (in `applyAutoFormatting`) uses
`LEGACY_CUE_REGEX` directly — no inline `invalidCuePattern` literal.
The disable toggle does **not** affect Auto Scrub's flagging — paragraphs
with legacy tokens still get the red flag whether the module is on or
off. Only the convert button appears/disappears with the toggle.

### InterfaceSettings.vue
A subsection in the Content Editor tab binds a `v-switch` to
`interfaceSettings.legacyCueConvertEnabled` and mirrors that to the
same localStorage key (`show-build:legacyCueConvertEnabled`) the
composable reads. The model picker for the find-media tiebreaker LLM
lives in **Settings → LLM Routing**, not duplicated here.

## Current state vs future state

### Today (2026-05)
The per-type cue-block format is **hand-mirrored** from each modal's
`buildCueBlock()` function. There are 16 of those in the codebase
(`SotModal.vue`, `ImgCueModal.vue`, `FsqModal.vue`, `GfxModal.vue`,
`NatModal.vue`, `VoModal.vue`, `PkgModal.vue`, `DirModal.vue`,
`RifModal.vue`, plus `BumpModal/StingModal/MusModal/LiveModal/VoxModal`
which are library-backed). Each one currently builds its cue block via
inline string concatenation with no shared schema.

The conversion module mirrors those formats in:
- `patterns.js` → `DEFAULT_DURATION_BY_TYPE`
- `conversion.js` → `buildCueBlock(...)`

**Parity tests** in `__tests__/parity.test.js` compare
`convertLegacyToken({TYPE/foo})` output against each modal's
`buildCueBlock` for the same inputs. If any modal's format drifts,
the parity test fails and forces a coordinated update of the module.

### Future (after the cue-type-schema TODO)
A shared schema definition (likely `disaffected-ui/src/utils/cueTypeSchema.js`)
will own per-type fields, defaults, and ordering. All 16 modals get
refactored to consume it. This module then:
- Imports `cueTypeSchema` directly.
- Deletes `DEFAULT_DURATION_BY_TYPE` and the per-type branches in
  `buildCueBlock()`.
- Retires the parity tests (replaced by direct schema use).

The follow-up work item is recorded in 4 places so it doesn't get
lost:
1. Dashboard todo panel (`/api/todos`, `created_by='claude'`).
2. `ACTIVE_WORK_QUEUE.md` in the repo root.
3. Inline `// TODO(cueTypeSchema):` comments in `conversion.js`.
4. ICR post (`project=show-build`, full migration plan).

## Out of scope (for this module)

These belong to other work items:

- **NAT/PKG manual modal flow is broken** — `NatModal.vue` and
  `PkgModal.vue` POST to `192.168.51.210:8888/preproc_nat` and
  `/preproc_pkg`, which are dead URLs on the decommissioned whisperbox
  host. The conversion module produces a NAT/PKG cue with
  `[MediaURL: episodes/{ep}/preshow/{filename}]` linking directly to
  the preshow file (no copy, no Celery processing). When the manual
  modal flow is fixed, the conversion module should be updated to
  reuse the same backend entry point. See `ACTIVE_WORK_QUEUE.md`.

- **GFX and FSQ are generators**, not uploaders. Conversion produces
  a media-less cue; the user finishes via the modal's generation flow.

- **Library-backed types** (BUMP/STING/MUS/LIVE/VOX) — the manual
  modals pick from a content library, not upload. The conversion
  module's behavior: if `find-media` finds a matching audio file in
  preshow/, the cue lands with `[MediaURL]` linking to that file;
  otherwise the cue lands media-less and the user picks from the
  library via the modal afterward.

## Testing

```bash
# Frontend unit tests (Vitest or whatever's configured for this project)
cd disaffected-ui
npm test src/modules/legacyCueConvert
```

Test files live in `__tests__/`:
- `patterns.test.js` — regex matches, alias map correctness
- `conversion.test.js` — multi-token paragraphs, *** stripping, audit
- `parity.test.js` — output matches each modal's buildCueBlock

Backend tests:
```bash
docker exec show-build-server pytest -q app/tests/test_legacy_cue_convert_router.py
```
