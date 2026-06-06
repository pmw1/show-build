# ProseMirror / TipTap — Animating Block Displacement (research + our findings)

Compiled while building the script-editor drag-and-drop displacement
(`BlockDragHandle.js`). Sources are ProseMirror discuss-forum threads (several
are maintainer **Marijn Haverbeke** statements) and the `prosemirror-view`
source. Keep this next to the code so future drag/animation work doesn't
re-learn it the hard way.

---

## TL;DR — the rules that actually bit us

1. **PM patches decoration `class`/`style` changes IN PLACE.** It does *not*
   destroy/recreate the block element on a pure decoration change. So a CSS
   `transition` on a decorated block **does fire** — the framework was never the
   problem.
2. **Our "pop" was a CSS override, not PM.** Every shifted block also carried
   `.pm-dim`, and `.pm-dim { transition: opacity }` **replaced** (CSS `transition`
   is a shorthand, last-wins, not additive) `.pm-drag-block { transition:
   transform }`. So shifted+dimmed blocks transitioned *opacity only* and the
   transform jumped → pop. The up-vs-down **asymmetry** came from up-shifted vs
   down-shifted blocks momentarily carrying different class combinations, so a
   different `transition` rule won depending on direction.
3. **The fix (canonical, per Marijn):** declare ONE combined `transition` on the
   base class and let feature classes set only VALUES:
   ```css
   .pm-drag-block { transition: transform 200ms EASE, opacity 200ms EASE; }
   .pm-shift-up   { transform: translateY(-32px); }   /* value only */
   .pm-shift-down { transform: translateY( 32px); }   /* value only */
   .pm-dim        { opacity: 0.65; }                  /* value only, NO transition */
   ```
   A feature class must **never re-declare the `transition` shorthand**.
4. **Never write inline `style`/`transform` onto editable block DOM.** PM's
   MutationObserver reverts it. Use decorations (preferred) or a NodeView.
   *Exception:* widget-decoration DOM (e.g. our `.pm-drop-gap` "INSERT HERE" bar)
   is NOT observed, so imperative transform writes on it are fine — that's why
   the bar's FLIP tween works.

---

## Q1 — Decoration class/style change: in place or recreate?

**In place.** `prosemirror-view` reconciles via
`NodeViewDesc.update()` → `updateOuterDeco()` → `patchOuterDeco()` →
`patchAttributes()`. `patchAttributes` updates classes incrementally (removes
only classes no longer present, adds only new ones) and styles by name — it does
**not** rebuild the element.

Recreation is forced **only** when:
- `node.sameMarkup()` is false — the *document node's* type/attrs change
  (`setNodeMarkup`, paragraph→heading). A pure decoration change does NOT trip this.
- The decoration sets a different `nodeName` (we don't).
- A genuine reconciliation bug (one existed for identical-content blocks
  differing only by decoration — fixed in prosemirror-view commit `31e7cdf`;
  keep the package current).
- Optimization: if node + decorations are deep-equal to before, `update()` isn't
  called at all ("not calling update is the intended behavior" — Marijn).

**Takeaway:** decoration transforms + a CSS transition is the correct, supported
way to animate during-drag displacement. It survives in-place patching.

## Q2 — FLIP (for non-drag reorders / actual layout moves)

First-Last-Invert-Play:
1. **First** — before the transaction, record each block's `getBoundingClientRect()`.
2. **Last** — apply the reorder; let PM redraw (new layout).
3. **Invert** — set `el.style.transform = translateY(oldTop - newTop)` synchronously
   after redraw (an `requestAnimationFrame` is the sync point).
4. **Play** — next frame, `el.style.transform = ''` with `transition: transform` → slides.

**PM caveat:** writing `el.style.transform` on a doc-content block is what the
MutationObserver fights. For FLIP-after-reorder, either do it in a NodeView, or
keep the transform value in a decoration. We use FLIP only for:
- the **drop-gap "INSERT HERE" bar** (a *widget* deco DOM — not observed, safe), and
- the **drop settle** (`flipReorder` on commit).

For *during-drag* displacement we do NOT need FLIP — decoration transforms +
transition is simpler and correct (and is what we do).

## Q3 — Does the MutationObserver revert imperative style writes? Sanctioned way?

**Yes** — inline `style`/`class`/`id` writes onto editable doc-content DOM get
reverted ("adding inline styles, classes, or IDs gets instantly erased").
Marijn's only offered hack (`el.innerHTML = el.innerHTML`) is explicitly NOT a
sanctioned API.

Sanctioned, in order of preference:
1. **`Decoration.node`** — the intended mechanism. PM applies/removes the
   class/style itself, so there's nothing for the observer to revert. *This is
   what we do for displacement.*
2. **NodeView** with a wrapper element you own + `ignoreMutation()` returning
   true for attribute/style mutations on the wrapper (never ignore mutations
   inside `contentDOM`).
3. **Overlay element outside the editable** — observer never sees it (this is how
   we render the cursor ghost and the drop bar).

## Q4 — NodeViews for redraw-surviving transitions

Right tool when an animation must persist across PM redraws (continuous
transition, or transform state that must not blink on an unrelated edit).
Implement `update(node, decorations)` → return `true` to keep DOM and animate
within it; add `ignoreMutation()` so imperative writes on the NodeView's own
(non-content) DOM aren't reverted. Marijn's two endorsed options for animatable
attribute changes are exactly **decorations** OR **a NodeView with `update`**.
For our during-drag displacement, decorations are lighter and sufficient; reach
for NodeViews only if mid-drag redraws ever interrupt a transition.

## Q5 — Prior art (how others animate displacement)

Honest finding: **almost none of the mainstream PM/TipTap drag libraries animate
the displacement of surrounding blocks.** They show a drop indicator and SNAP:
- **prosemirror-dropcursor** — decoration drop-cursor line only; no displacement anim.
- **TipTap Drag Handle** — floating-ui handle + native HTML5 DnD → reorder txn;
  blocks snap; docs only suggest CSS `transition` on the handle/indicator.
- **BlockNote** (Notion-style) — side-menu + drag handle, dragged-block preview +
  insertion separator overlay, then a txn. No FLIP slide of neighbors.
- **Notion-style tutorials / tact-app/blocks** — per-block NodeView + handle;
  movement is a txn; displacement unanimated.

The pattern that *does* animate displacement (the few that bother) is exactly
**ours**: transient `Decoration.node` transform (`translateY(±h)`) on the shifted
blocks + CSS `transition: transform`. The dragged element itself is an
**overlay/ghost rendered outside `contentEditable`** so the observer/redraws
don't touch it. **Animated displacement is custom work** — there's no library to
lean on.

---

## How OUR implementation maps to the guidance (it lines up)

| Concern | Guidance | What `BlockDragHandle.js` does |
|---|---|---|
| Displacement of neighbors | Decoration transform + transition | `pm-shift-up/down` node decos + base-class transition ✓ |
| Combined transition | One `transition` on base; feature classes value-only | `.pm-drag-block` owns `transform,opacity`; `.pm-dim`/`.pm-shift-*` value-only ✓ (the fix) |
| Cursor ghost | Overlay outside editable | `.pm-drag-ghost` appended to `<body>`, `position:fixed` ✓ |
| Drop bar ("INSERT HERE") | Widget deco (not observed) → imperative FLIP OK | persistent widget node + `view().update()` FLIP tween (`offsetTop` measure) ✓ |
| Drop settle | FLIP after the reorder txn | `flipReorder()` on commit ✓ |
| Flash | Decoration class (survives autosave re-render) | `pm-flash-drop/neighbor` via `animation`, not `transition` (no collision) ✓ |
| Stagger ripple | `transition-delay` keyed on index distance | parked behind eslint-disable; re-enable now that base anim fires |
| NEVER imperative style on block DOM | Use deco/NodeView | confirmed — earlier imperative `applyDisplacement` was reverted by the observer; removed ✓ |

**Open item:** re-enable the **staggered ripple** (`STAGGER_MS` / `STAGGER_MAX_MS`
/ `prevGapIndex`, currently eslint-disabled) by adding the per-block
`transition-delay` — and per the research, do it as a **value** layered on the
decoration/element WITHOUT re-declaring `transition`, so it can't reintroduce the
override bug.

## Authoritative sources
- prosemirror-view source (`patchAttributes`/`patchOuterDeco`/`NodeViewDesc.update`):
  https://github.com/ProseMirror/prosemirror-view/blob/master/src/viewdesc.ts
- Reconciliation bug fix: https://github.com/ProseMirror/prosemirror-view/commit/31e7cdf8880ff777ea724bd0c8c2e9950cf484e4
- CSS Transitions (Marijn: decorations preserve DOM; or NodeView.update):
  https://discuss.prosemirror.net/t/css-transitions/1989
- Repainting Decorated Nodes: https://discuss.prosemirror.net/t/repainting-decorated-nodes/1434
- NodeView update() On Decoration change: https://discuss.prosemirror.net/t/nodeview-update-on-decoration-change/2290
- Node decorations before custom node view causes rerender:
  https://discuss.prosemirror.net/t/node-decorations-before-custom-node-view-causes-rerender/3924
- Pause MutationObserver to allow styling (observer reverts imperative styles):
  https://discuss.prosemirror.net/t/pause-mutationobserver-to-allow-styling/5536
- ignoreMutation for node views: https://discuss.prosemirror.net/t/ignoremutation-for-node-views-prevent-update-of-child-nodes/1944/4
- How to check decoration attributes in a nodeView update:
  https://discuss.prosemirror.net/t/how-to-check-decoration-attributes-in-a-nodeview-update/7923
- TipTap Drag Handle: https://tiptap.dev/docs/editor/extensions/functionality/drag-handle
- prosemirror-dropcursor: https://github.com/ProseMirror/prosemirror-dropcursor
- BlockNote: https://github.com/TypeCellOS/BlockNote
- FLIP technique (CSS-Tricks): https://css-tricks.com/everything-you-need-to-know-about-flip-animations-in-react/
