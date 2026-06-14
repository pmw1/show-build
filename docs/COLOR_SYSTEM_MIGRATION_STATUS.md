# Color System Migration — Status & Follow-ups

_Last updated: 2026-06-04 (dev branch `feat/script-editor-tiptap`)_

## What this was

Unified the UI color settings system and migrated hardcoded colors to reference it.
Prompted by: a clunky color picker + quietly-broken plumbing (a PascalCase/suffix vs
lowercase key schism that polluted the stored profile, and diverging backend/frontend
defaults).

## Done

### Phase A — plumbing unified (no visible change)
- **`src/utils/colorRegistry.js`** (NEW) is the single source of truth: every color slot
  (canonical lowercase key, label, category, default, legacy aliases, preview type) +
  the base/variant helpers (`BASE_COLORS`, `getVariantsForBase`, `splitColor`,
  `composeColor`, `normalizeColorKeys`, `legacyKeyMap`).
- **`src/utils/themeColorMap.js`** — `defaultColors` now derived from the registry;
  `getColorValue` + load paths fold legacy keys to canonical. Public API unchanged.
- **`app/settings_colors_router.py`** — no longer hardcodes defaults (returns `{}` when no
  row; frontend merges registry defaults); normalizes legacy keys on read.
- **`app/alembic/versions/g020_normalize_color_keys.py`** — de-polluted the
  `theme_colors_default` row (45 clean canonical keys; legacy duplicates dropped; values
  preserved). Applied on `showbuild_dev` only.

### Phase B — picker rebuilt
- **`src/components/ColorSelector.vue`** fully rebuilt registry-driven: collapsible
  categories, per-type popover swatch picker (base grid → variant strip), live preview
  per `entry.preview`, search, per-type + global reset, inline save state. Writes ONLY
  canonical keys (can't re-pollute). Preserves `compact`/`hideSaveButton` props +
  `colors-changed`/`colors-saved` emits.

### Phase C — semantic hardcoded colors migrated
- `CurrentShowPanel.vue`, `NextShowPanel.vue` — status bars → configurable
  `draft`/`approved`/`production`/`running`/`completed`.
- `ImageCueCard.vue` — AI-state borders → `ai-analyzing` / `ai-rejected`.
- `PlaceholderCueCard.vue` — cue completion borders/headers → `complete` /
  `needs-attention` / `urgent-attention` (added `complete` + `urgent-attention` to the
  registry).
- `ShowInfoHeader.vue` — thumbnail conversion-status CSS `@keyframes` borders converted to
  CSS custom properties (`--thumb-attention`, `--thumb-attention-pulse`, `--thumb-success`)
  set from the registry in `onMounted` → now themeable (`needs-attention`, `production`).

## Deferred — legacy-key swaps in shared files (low priority, NOT urgent)

These still resolve correctly via `legacyKeyMap` (the compatibility fold), so there is no
functional bug. Canonicalize when the other dev sessions are out of these files (avoid
merge collisions). One-line swaps:

- `RundownPanel.vue:1678` — `getColorValue('Selection-interface')` → `'selection'`
  (also: this file has CSS-keyframe status colors — the `#9C27B0↔#BA68C8` throb ~3810 and
  `.toolbar-btn-*` status colors ~3965 — convert to the `--thumb-*`/registry pattern in
  the same pass).
- `ContentEditor.vue:1605` — `'draglight-interface'` → `'draglight'`
- `ContentEditor.vue:2983` — `'hover-interface'` → `'hover'`
- `ContentEditor.vue:8819` & `SotModal.vue:1126` — `'locatorflash-interface'` → `'locatorflash'`

Once no consumer references a legacy key, the `legacyKeyMap`/`normalizeColorKeys` fold can
eventually be removed (keep one release as insurance).

## Intentionally left alone

- **AI "purple" (`#7e57c2`) LLM-generated indicators.** Already user-configurable through a
  SEPARATE system: `src/composables/useContentIndicators.js` reads a "Content Origin
  Indicators" setting and publishes `--llm-indicator-text/-border` CSS vars (the hardcoded
  `#7e57c2` are only fallbacks). The registry has an `ai-generated` slot, but folding the
  two systems together would create two competing config UIs for the same color and touches
  the delicate MetadataPanel LLM-highlight wiring. Decision (Kevin, 2026-06-04): leave as-is.
  Revisit only if having two config spots becomes confusing.

## Bucket #2 — broader migration (prepared, NOT executed)

Per user: do semantic colors first, prepare #2 for after testing. These spots hardcode
colors that *could* be configurable but are lower-value / more involved. Would each need a
new registry type:

- **Notifications / flash messages** — `useStandardNotification.js`, `useScreenFlash.js`,
  many `flashUrgent(..., '#F44336')` and `notifyUserStandard(..., '#...')` call sites across
  modals + ContentEditor/EditorPanel. New types e.g. `notify-error`/`notify-info`/`notify-warning`.
- **Audio visualization** — `AudioWaveform.vue`, `VUMeter.vue`, `LEDMeter.vue`, and the
  waveform props in `SotModal.vue`/`VoModal.vue`. New types e.g. `waveform-wave`,
  `waveform-playhead`.
- **Story priority tag palette** — `MetadataPanel.vue:~1058` (main-feature/top-story/
  breaking/urgent/etc.). New `priority-*` types.
- **Per-modal accent / focus borders** — `GfxModal`, `FsqModal`, `RifModal`, `VoModal`,
  `ScriptCompareModal`, `TimezoneClock`, `MessagesPanel` (mostly `primary`/cue-type borders).

## Verification done

- `npm run lint` clean; production build exits 0.
- Phase A: API serves 45 canonical keys, no legacy; DB row cleaned (valid json object,
  values preserved); legacy-key fold proven for the 5 deferred consumers.
- Phase B: visually confirmed by Kevin (picker, popover, live preview, save/reload).
- All work on `showbuild_dev`; LIVE `showbuild` untouched.
