# Script Editor Drag-and-Drop — Rebuild Plan (ProseMirror)

**Status:** draft for review · 2026-06-04 · prefect-show-build-claude-63ebeb
**Goal:** Restore drag-to-reorder for paragraphs AND cue cards in the ProseMirror
ScriptEditor. The legacy contenteditable editor used a `<draggable>` list with a
grab handle + drop zones; that's gone now (PM editor is the only editor) and only
PM's raw built-in node drag remains — clunky, no handle, conflicts with text editing.

## Current state (verified)
- Doc schema is a FLAT sequence: `doc -> (paragraph | cue)+`, never nested. Ideal for reorder.
- `cue` node: `atom: true, draggable: true`. `paragraph`: standard `group: 'block'`, `content: 'inline*'`.
- `buildScriptExtensions` = Document, Text, ScriptParagraph, CueNode, RevisionMark, SlashCommand, UndoRedo. **No drag extension.**
- No `@tiptap/extension-drag-handle` installed.
- ScriptEditor serializes the doc → markdown on every change (`docToMarkdown`) and emits
  `update:scriptContent`, with the `assertNoLoss` guard. **Any reorder that mutates the doc
  flows through this automatically — no separate persistence path needed.** This is the big
  win: a drag that produces a correct PM transaction serializes + saves for free.

## UX (chosen + refined by Kevin)
- Grab handle ("drag tag") on the **left-hand side of each row** (paragraph or cue).
- Pull the row **up/down one line at a time**, and **everything around the landing spot DISPLACES
  live** to make room as you drag — i.e. the surrounding rows shift in real time to show where the
  dragged row will land. NOT a static "drop zone" target; the layout reflows continuously.
- Release → the row settles into that position; the displaced rows close the gap above it.
- Text selection/editing is untouched (you only drag via the left handle), cue atoms move as a unit.

### Reuse the EXISTING drag styling tokens (do NOT invent new colors)
These already exist in the legacy editor and are user-configurable via the theme color system —
the new editor must reuse them so the look matches:
- **`--dropline-color`** CSS var — the drag **line / drop indicator** color. Set at runtime from
  `getColorValue('dropline')` → `resolveVuetifyColor(...)` (fallback `rgb(33,150,243)` blue, or
  `green-lighten-4` in one path). This is "the drag line, color".
- **`--draglight-color`** CSS var — the dragged-row / displacement **highlight** background
  (fallback `rgba(33,150,243,0.15)`).
- **drop-shadow color** = `selectionShadowColor` = the selection color at 20% opacity
  (`rgba(r,g,b,0.2)`), used as `box-shadow: 0 0 0 2px <selectionShadowColor>` (and the dropline
  glow variant `0 0 12px <droplineColor>`). This is "the drop shadow color".
- **handle styling**: `.drag-handle-column` — 30px wide left gutter, `opacity 0.3` default →
  `1` on hover, hover bg `rgba(33,150,243,0.08)`, icon `rgb(33,150,243)` on hover, `cursor: grab`
  / `grabbing` on active. Mirror this for the new handle.

So: the drag line uses `--dropline-color`, the live-displacement highlight uses `--draglight-color`,
and the dragged row's drop-shadow uses `selectionShadowColor`. All three are already wired to the
configurable theme — the new plugin must read the same CSS vars / computed colors, not hardcode.

## Approach: ProseMirror drag-handle plugin
Two implementation options — pick in review:

### Option A — `@tiptap/extension-drag-handle-vue-3` (official, add dep)
- TipTap ships an official drag-handle extension (Vue 3 variant renders a handle component).
- Add to `buildScriptExtensions`. It computes the block under the cursor, renders a handle in the
  gutter, and performs the move via a PM transaction on drop. Least custom code; maintained upstream.
- Cost: one new dependency (+ its peer `@tiptap/extension-node-range` if required); verify versions
  match our pinned `@tiptap/*` (check `package.json`).

### Option B — small custom ProseMirror plugin (no new dep)
- A `Plugin` with `decorations` that adds a draggable handle widget at the start of each top-level
  block, plus `handleDOMEvents` (dragstart/dragover/drop) that:
  - on dragstart: record the dragged block's position (its top-level index / `$pos.before(1)`),
  - on dragover: compute the target gap, draw a drop-indicator decoration,
  - on drop: build ONE transaction that deletes the block's node range and re-inserts it at the
    target gap (PM `tr.delete` + `tr.insert`, mapped carefully so positions stay valid).
- More code (~150 lines) but zero new deps and full control. This mirrors what the official ext
  does internally.

**Recommendation (revised for Kevin's UX):** lean to **Option B (custom plugin)**. The
"pull up one line at a time with everything around the landing spot displacing live" behavior
is a *continuous reflow* with our own dropline + draglight + drop-shadow tokens — the official
extension gives a single drop indicator and its own styling, which fights that spec. The custom
plugin lets us: render the left-gutter handle, on dragover compute the nearest top-level gap and
push the surrounding rows apart live (a decoration/`--draglight-color` highlight + the
`--dropline-color` line at the gap), apply the dragged row's `selectionShadowColor` drop-shadow,
and commit one move transaction on drop. Still confirm at build time, but plan around B.

## Behavior / edge cases to handle
- **Cues are atoms** — must move as one opaque unit (already `draggable`), never split.
- **Paragraph text drag must NOT trigger block drag** — only the handle initiates a move; selecting
  text inside a paragraph stays normal.
- **Drop targets are the GAPS between top-level blocks** (and at very top / very bottom), never
  *inside* a paragraph or cue.
- **Serialize-back is automatic**: after the move transaction, `onUpdate` fires →
  `scheduleSave/flushPendingChanges` → `docToMarkdown` → `assertNoLoss` → emit. A reorder is just a
  node-position change, so `assertNoLoss` (cueDelta 0, no dropped fields) should pass — VERIFY in test.
- **Undo**: the move is a single transaction, so the existing UndoRedo extension covers Ctrl+Z.
- **RevisionMark / needsAttention / speaker attrs**: moving a paragraph node carries its attrs with
  it (we move the whole node, not its text) — so flags/speaker survive the move.

## Steps (after approval)
1. Version-check TipTap; decide Option A vs B.
2. Add the drag-handle (extension or custom plugin) to `buildScriptExtensions`.
3. Style the gutter handle + drop indicator to match the editor (handle on hover, subtle).
4. Verify on dev: reorder a paragraph, reorder a cue, paragraph↔cue swaps; confirm
   serialize-back is lossless (assertNoLoss ok), save persists the new order, reload shows it,
   Ctrl+Z undoes the move, and text editing/selection is unaffected.

## Risk / rollback
- Additive: a new extension in the list. Removing it from `buildScriptExtensions` reverts cleanly.
- The serialize/save path is untouched — drag only mutates the doc, which already round-trips.
- Dev-only first.
