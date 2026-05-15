# Follow-ups: cue data-loss fixes + universal Ctrl+Z

This file enumerates the work that was deliberately **deferred** from the
PR titled *"Fix cue-modal data loss across all cue types + universal
Ctrl+Z"*. Everything below is intentionally out of scope of that PR but
should land in subsequent PRs.

The original implementation plan lives in
`/root/.claude/plans/system-reminder-you-re-running-in-humble-hellman.md`
(local to the agent session that produced the PR).

---

## 1. Rundown structure undo (Ctrl+Z for reorder / region ops)

**Status:** not implemented in the universal-undo PR.

Today the new `useUndoManager` captures any change that flows through
`rawMarkdownContent` (script edits, cue insert/edit/delete, scratch
content). Structural rundown operations that mutate `rundownItems`
directly — reorder, region create, region delete, move-region-to-
unassigned — bypass the manager and are NOT undoable.

**To implement:**

In `ContentEditor.vue`'s receivers for these `RundownPanel` emits
(`@delete-item`, `@reorder-items`, `@create-region`, `@delete-region`,
`@move-region-to-unassigned` — see `RundownPanel.vue:1015-1044`),
capture pre-state of `rundownItems` (shallow copy + region structure)
and push a command-pattern entry whose `undo` restores the array and
re-POSTs the order to `/api/episodes/{ep}/rundown`.

The reorder server endpoint already exists. For region create/delete the
server-side restore is straightforward.

**Defer permanently:** `delete-item` undo. Re-creating a deleted rundown
item requires a new backend endpoint + handling for media assets that
were unlinked. Document in the delete confirm dialog that the operation
is permanent.

---

## 2. MetadataPanel field-level undo

**Status:** not implemented.

Sidebar field edits (description, title, tags, etc.) are not captured by
the undo manager today. Native browser undo works inside each `<input>`
but does not survive focus loss, and changes are not reversible after
they persist.

**To implement:**

`MetadataPanel.vue` already emits `update-meta`. Wrap the receiving side
in `ContentEditor` through a single `applyMetaPatch(payload)` method
that:

1. Captures the pre-edit value of `rundownItems[i][field]`.
2. Applies the patch.
3. Pushes a manager entry: `{ label: 'edit metadata: ' + field, undo:
   () => restore prev, redo: () => re-apply patch }`.

No `MetadataPanel.vue` changes needed.

---

## 3. Modal ESC unification (CLAUDE.md standing todo #25)

**Status:** not done; 5 modals touched in this PR are candidates.

CLAUDE.md tracks an in-flight effort to convert all 27 modals to the
`registerModalEsc(...)` pattern from `useModalStack`. Foundation is
landed. Remaining 21 modals each need a one-line conversion of their
per-modal `addEventListener('keydown', handleEscapeKey, ...)` into one
`registerModalEsc(...)` call.

Modals this PR edited but did not unify ESC for:

- `disaffected-ui/src/components/modals/FsqModal.vue`
- `disaffected-ui/src/components/modals/GfxModal.vue`
- `disaffected-ui/src/components/modals/SotModal.vue`
- `disaffected-ui/src/components/modals/DirModal.vue` (touched indirectly via submit handler — modal file unchanged here)
- `disaffected-ui/src/components/modals/RifModal.vue` (likewise)

A follow-up that converts these five (plus the remaining 16) advances
the standing-todo without expanding the data-loss-fix PR's scope.

Plan: `docs/MODAL_ESC_UNIFICATION_PLAN.md`.

---

## 4. Insert-only cue types (VO, NAT, PKG, BUMP, STING, VOX, MUS, LIVE)

**Status:** intentional. None are reachable from a card's edit button
today (`EditorPanel.editCue` only routes IMG / SOT / FSQ / GFX / DIR /
RIF). This PR did not add edit support for them.

**If editability is requested later:** repeat the IMG-style pattern —
`editingFooCueData` state, `handleEditFooCue` opener with
`flushPendingChanges`, `editFoo` event from `EditorPanel.editCue`,
modal `editMode` + `initialData` props that load the original AssetID,
modal preserves AssetID through submit, `submitFoo` adds a
regex-replace edit branch with abort-on-miss.

Their submit handlers should still capture rawMarkdownContent
before/after for undo coverage on insert (currently implicit via the
`rawMarkdownContent` watcher).

---

## 5. Re-enable hard-abort tripwires in `useScriptCore`

**Status:** still on warning-only.

`useScriptCore.safeEmitScriptContent` had cue-count regression and
shrink-guard checks downgraded to warnings because of false positives
in pre-fix submit flows. Now that the submit handlers are coherent
(Priority 1 of this PR), revisit and consider promoting back to hard
aborts after a release of stability.

---

## 6. Remove `CueModal.vue` (unused)

**Status:** untouched; flagged for cleanup.

`disaffected-ui/src/components/content-editor/modals/CueModal.vue`
(~407 lines) appears to be a generic add-only modal that no live code
path uses — every cue type has its own dedicated modal. Audit references
and delete if confirmed orphaned.

---

## 7. Repository hygiene

**Status:** flagged; not in scope of any PR yet.

Files at the repo root that look like legacy / WIP detritus:

- `Dockerfile.enhanced`, `docker-compose.enhanced.yml`
- `minimal_*.py`, `enhanced_main_patch.py`
- `RundownPanel_new_template.vue`
- `backup_md_*`
- `tree_output.txt`
- `*.wav`, `decarlos_brown_newsweek_quote.json`

A separate cleanup pass would file these under `archive/` or remove
them outright.

---

## Verification checklist for the data-loss-fix PR

For each cue type that has an edit path (IMG, SOT, FSQ, GFX, DIR, RIF):

1. Start the dev server: `cd disaffected-ui && npm run serve`.
2. Open an episode and pick a rundown item containing at least one cue
   of that type.
3. Type a paragraph of new text, then **immediately** click the cue
   card's edit button (do not wait for the 1.5 s debounce). Modify a
   field. Submit.
4. Expect:
   - The original cue is **replaced in place** (count
     `<!-- Begin Cue -->` markers in Code Mode — should not change).
   - The typed paragraph survives (it is not lost to the regex replace).
   - The AssetID on the cue is **unchanged** from before the edit
     (visible in Code Mode).
5. DevTools network tab: no `assetid/generate-legacy` POST should fire
   on edit. (Fires only for inserts.)
6. Reload the page: edited content persists, the cue card still
   displays correctly, and any media that was already rendered (FSQ
   PNG, SOT video) still resolves by the unchanged AssetID.

For universal Ctrl+Z:

1. Type a paragraph; `Ctrl+Z` reverts it. `Ctrl+Shift+Z` returns it.
2. Insert an FSQ cue; `Ctrl+Z` removes it. `Ctrl+Shift+Z` brings it
   back.
3. Edit an existing SOT cue's slug; `Ctrl+Z` reverts the slug (the
   AssetID never changed in the first place after Priority 1).
4. Focus a sidebar `<input>` → type → `Ctrl+Z`: confirm the **browser's
   native** undo runs in the input (the global handler did NOT
   preempt).
5. In a script paragraph contenteditable, type → `Ctrl+Z`: the app's
   undo manager handles it; the paragraph reverts.
6. Switch episodes; verify the manager clears (`Ctrl+Z` is a no-op
   afterward).
7. Switch rundown items within the same episode; `Ctrl+Z` from the new
   item is a no-op (entry is item-scoped and bails when the user is on
   a different item). Switch back to the original item; `Ctrl+Z` works.

---

*Generated alongside the cue data-loss + universal-undo PR. Update this
file as items are picked up or descoped further.*
