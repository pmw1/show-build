# Universal ESC-Closes-Modal Behavior

## Problem

Show-build has 27 modal components. ESC behavior is inconsistent:

- **21 modals** each implement their own
  `document.addEventListener('keydown', handleEscapeKey)` with mount/unmount
  bookkeeping. This is duplicated boilerplate. Each implementation is slightly
  different (some `event.preventDefault()`, some don't, some check
  `props.show`, some check internal `dialog` ref).
- **5 modals** had no ESC handler at all (now fixed — see "What's already
  done" below).
- **`ContentEditor.vue`** has a central ESC-closes-all-modals handler that
  closes ~20 modals in one shot. But it only fires when ContentEditor is
  the focused component, so modals opened from Settings, Dashboard, Profile,
  etc. were never covered by it.
- Per-modal handlers and the ContentEditor handler can race; some modals
  call `event.stopImmediatePropagation()`, others don't.

This means a user pressing ESC may or may not close the topmost modal
depending on what view they're in. Not a data-loss bug, but a UX
inconsistency that becomes a bigger pain as the app grows.

## What's already done (2026-05-09)

A foundation has landed:

1. **New composable** `disaffected-ui/src/composables/useModalStack.js`
   provides:
   - `installModalStackHandler()` / `uninstallModalStackHandler()` — installs
     a single document-level ESC listener (capture phase) that closes the
     topmost registered modal.
   - `useModalStack()` — `register(closeFn, label)` / `unregister(id)` /
     `unregisterTop()` / `depth()` for explicit registration.
   - `registerModalEsc(showGetter, closeFn, label)` — one-line helper for
     modals using the standard `:model-value="show"` + `@update:show` pattern.
     Handles register-on-open, unregister-on-close, and unmount cleanup.

2. **Installed app-wide** in `App.vue` (alongside the existing global
   keydown handler).

3. **Patched the 5 modals that previously had no ESC behavior at all:**
   - `components/content-editor/modals/CueModal.vue`
   - `components/content-editor/modals/DeleteImgCueModal.vue`
   - `components/content-editor/modals/EpisodeDetailsModal.vue`
   - `components/content-editor/modals/SpeakerSelectorModal.vue`
   - `components/modals/NewSOTModal.vue`
   - (`components/EpisodeScaffoldModal.vue` was thought to be missing
     but already had its own; left alone.)

After this baseline, ESC closes some modal in every part of the app.

## What still needs doing

### Phase 1 — convert the 21 modals that have their own ESC handler

Each of these modals should:

1. Import `registerModalEsc` from `@/composables/useModalStack`.
2. Add the one-line `registerModalEsc(...)` call near the top of `<script setup>`.
3. **Remove** the per-modal `handleEscapeKey` function, the
   `document.addEventListener('keydown', ...)` in `onMounted`, and the
   matching `removeEventListener` in `onBeforeUnmount`.

Files to convert:
- `components/modals/StingModal.vue`
- `components/modals/ScriptCompareModal.vue`
- `components/modals/MusModal.vue`
- `components/modals/AssetBrowserModal.vue`
- `components/modals/ContentLibraryPickerModal.vue`
- `components/modals/VoxModal.vue`
- `components/modals/GfxModal.vue`
- `components/modals/NatModal.vue`
- `components/modals/RifModal.vue`
- `components/modals/LoginModal.vue`
- `components/modals/NewItemModal.vue`
- `components/modals/RequireEpisodeModal.vue`
- `components/modals/DirModal.vue`
- `components/modals/FsqModal.vue`
- `components/modals/TemplateManagerModal.vue`
- `components/modals/BumpModal.vue`
- `components/modals/SotModal.vue`
- `components/modals/PkgModal.vue`
- `components/modals/LiveModal.vue`
- `components/modals/VoModal.vue`
- `components/content-editor/modals/DeleteCueModal.vue`
- `components/content-editor/modals/ImgCueModal.vue`

A few of these have additional cleanup logic in their ESC handler (reset
form state, abort in-flight uploads, etc.). For those, the close callback
passed to `registerModalEsc` should perform the same cleanup before
emitting `update:show`. Don't blindly delete custom logic.

**Estimated effort: half a day.** Mostly mechanical, but each file needs
a quick read to check for non-trivial cleanup logic.

### Phase 2 — remove ContentEditor's per-modal ESC handler

Once Phase 1 lands, the central ESC handler in
`ContentEditor.vue:4567-4617` (the `if (event.key === 'Escape')` branch
inside `handleKeydown`) becomes redundant. It can be deleted entirely —
the global modal stack handler will close the topmost modal regardless of
who owns it.

The `joinMode.active` ESC branch (`this.rejectJoin()`) should remain —
that's not a modal, it's a UI mode. Same for any non-modal ESC behaviors
elsewhere.

**Estimated effort: an hour.** Test that ESC still closes editor modals
correctly after the deletion.

### Phase 3 — consider auditing non-modal overlays

Several Vuetify components other than `<v-dialog>` produce overlays that
should also respond to ESC: `<v-menu>`, `<v-bottom-sheet>`, `<v-overlay>`.
Vuetify's stock behavior already handles those, but some may be configured
with `:persistent`. Audit and align.

**Estimated effort: an hour.**

## Migration template

Before:
```vue
<script setup>
const props = defineProps({ show: Boolean })
const emit = defineEmits(['update:show'])

function handleEscapeKey(event) {
  if (event.key === 'Escape' && props.show) {
    event.preventDefault()
    event.stopPropagation()
    emit('update:show', false)
  }
}

onMounted(() => document.addEventListener('keydown', handleEscapeKey))
onBeforeUnmount(() => document.removeEventListener('keydown', handleEscapeKey))
</script>
```

After:
```vue
<script setup>
import { registerModalEsc } from '@/composables/useModalStack'

const props = defineProps({ show: Boolean })
const emit = defineEmits(['update:show'])

registerModalEsc(() => props.show, () => emit('update:show', false), 'MyModal')
</script>
```

## How the global handler works (for reviewers)

- One `document.addEventListener('keydown', _onKeydown, true)` in capture
  phase. Capture chosen so we win the race against legacy per-modal handlers
  that listen in bubble phase — important during the Phase 1 migration.
- Stack is plain LIFO. Topmost (last registered) gets ESC.
- Each registered entry has a `close` callback supplied by the modal. The
  global handler doesn't know how a specific modal closes; the modal does.
  So Phase 1 conversion is just "swap N lines of imperative listener code
  for one declarative `registerModalEsc(...)` line."
- `event.preventDefault() + stopPropagation() + stopImmediatePropagation()`
  prevent any other handler (per-modal, ContentEditor's central handler,
  Vuetify's own ESC behavior) from also firing on the same ESC.

## Edge cases noted during the design

- **Persistent dialogs.** Many modals use `:persistent` to prevent
  scrim-click and Vuetify's built-in ESC. The global stack closes them
  anyway because we call the modal-supplied close callback directly.
- **Nested modals.** If modal A opens modal B, B is on top of A in the
  stack; ESC closes B first, then A on the next press. Correct LIFO.
- **Modals that shouldn't close on ESC** (none currently, but in the
  future). Just don't call `registerModalEsc` for those.

## References

- Foundation files:
  - `disaffected-ui/src/composables/useModalStack.js` (new)
  - `disaffected-ui/src/App.vue` (install/uninstall hook added)
- Modals already converted:
  - `components/content-editor/modals/CueModal.vue`
  - `components/content-editor/modals/DeleteImgCueModal.vue`
  - `components/content-editor/modals/EpisodeDetailsModal.vue`
  - `components/content-editor/modals/SpeakerSelectorModal.vue`
  - `components/modals/NewSOTModal.vue`
- Central ESC handler to remove eventually: `ContentEditor.vue:4567-4617`

---

*Authored: 2026-05-09 by `prefect-show-build-claude-c6e0ef`. Triggered by
the request "make ESC close the focused modal site-wide."*
