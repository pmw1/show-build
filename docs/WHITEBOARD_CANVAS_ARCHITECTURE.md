# Whiteboard Canvas Architecture (Vue Flow)

**Since 2026-07-22 the whiteboard canvas runs on [Vue Flow](https://vueflow.dev)
(`@vue-flow/core` + `@vue-flow/background` + `@vue-flow/minimap`).** Vue Flow
owns the viewport (pan/zoom via d3-zoom), node positioning and dragging, edge
rendering, and drag-to-connect. Everything else — card content, layout solvers,
save/load, media, comments — remains Show-Build code in
`disaffected-ui/src/views/ScratchpadView.vue`.

## The constant-footprint rule (READ THIS before touching zoom/LOD)

A card occupies the **same canvas-space box at every zoom level**. The zoom tier
only changes what is drawn *inside* that box:

| Tier    | Zoom      | Renders |
|---------|-----------|---------|
| detail  | ≥ 0.75    | Everything: body, metadata, comments, actions |
| compact | ≥ 0.45    | Header, media, primary field |
| summary | ≥ 0.20    | Type, thumbnail, title (fixed canvas-unit text) |
| marker  | < 0.20    | Type-coloured plate filling the footprint |

Because the footprint never changes, geometric zoom handles **all** sizing and
spacing proportionally. Do **NOT** reintroduce:

- counter-scaled fonts/padding (`1/zoom` factors) — deleted 2026-07-22
- position spreading at low zoom (`webSpreadFactor`) — deleted
- viewport-width-derived card sizes (`canvasWidth / zoom`) — tree rows are now a
  fixed canvas width (`TREE_WIDTH`)
- the "skeleton" tier that hid child cards — all cards render at every zoom

To make something readable when zoomed out, simplify what the tier *shows*;
never inverse-scale it.

## Data flow

`cards[]` + the link store (`useWhiteboardConnections`) remain the single source
of truth, loaded/saved through the same API as before. Vue Flow nodes/edges are
a **projection** (see the "Flow sync" section at the bottom of the script):

- Node rebuild on card-set or view change (`cardIdsSignature` watcher).
- Position patches when a layout re-solves or free-web x/y are written
  (`resolvedPositions` watcher). The dragged node is skipped mid-gesture.
- `card.x/card.y` are written **only** by free-web user drags (at drag stop) and
  explicit free-web actions (Auto Arrange, snap, tighten, load-time separation).
  Computed layouts (hierarchical / balanced / waterfall) never touch them.
- Edges mirror `nodeLinks` 1:1 (custom `#edge-link` slot: straight
  centre-to-centre under the nodes, elbows in the tree, endpoint dots + label +
  delete in the edge-label layer).

Card templates render through the `#node-card` slot **in the same SFC scope**,
so all handlers/helpers work unchanged. A capture-phase `mousedown` guard on the
card root (`maybeBlockNodeDrag`) keeps presses on inputs/textareas/media
controls from starting a node drag — no per-element `nodrag` classes needed.

## Connections

Each card has a generous hot band OUTSIDE its border: four `.connect-band`
strips forming a frame (~52 screen px thick, zoom-converted, capped at 120
canvas px so far-out zooms don't create huge overlapping frames). The band
never overlaps the card itself — over the card there is no dot and every press
drags the card. While the pointer is in the band, a single **connection dot
follows the mouse along the card's perimeter** (`liveDot` + `trackConnectDot`,
30px on-screen at any zoom). The dot is a live Vue Flow source `Handle`;
pressing it starts the connection (node-internals are rAF-refreshed as it
moves so the rubber band anchors at the grab point). While a connection is in
flight, an invisible full-card target handle accepts the drop anywhere on the
card. Releasing over empty canvas opens the spawn menu; the new card is
auto-linked to the source. Card representations carry `z-index: 1` so content
always beats bands (their own AND a neighbour's) in hit-testing — bands are
only reachable over true empty space.

## Parent hubs (always prominent)

Parent nodes are the board's landmarks and must carry weight at every zoom:

- **Detail/compact**: a large round hub (520px web / 340px tree / 260px
  collapsed — `parentNodeSize`, mirrored by `lodBoxWidth`) with big type
  ("SEGMENT", falling back to "NODE") and a large centred title.
- **Summary/marker**: a solid-colour disc filling the same footprint (parents
  never use the generic summary card in web views).
- **Below the compact tier**, each hub gets a **screen-space label badge**
  ("SEGMENT" + title, `hubLabels` / `.hub-label`) anchored to its centre —
  constant on-screen size, tracks pan/zoom and live drags, `pointer-events:
  none`. This is the map-landmark pattern: geometry scales, labels stay
  readable. It does not touch canvas geometry, so the constant-footprint rule
  holds.
- Edge endpoint dots are NOT rendered on ends anchored at a parent centre —
  they would be invisible under the disc and steal clicks meant for the hub.

**App-wide gotcha:** `styles/vuetify-fixes.css` flattens ALL border-radius with
`* { border-radius: 0 !important }`. Genuinely circular whiteboard elements
(hub discs, connect dots, endpoint/delete dots, hub-label pills) opt back in
with their own `!important` — see the "Circle opt-ins" section of the styles.
Also: `@mdi/font` is pinned at 5.9 — `mdi-hub` does not exist there (renders
blank); the hub fallback icon is `mdi-file-tree`.

## Auto Center (toggle, top-right chip row)

Off by default, persisted per browser (`wb-auto-center`). When ON:

- Selecting a card (click, or focusing one of its fields) **pans** it to the
  viewport centre. The zoom is never touched.
- Double-clicking a card **redistributes the whole board around it** as the
  centre of the universe: directly linked cards on the first ring, their
  neighbours outward by graph distance, unlinked cards on the outermost ring
  (`redistributeAroundCard`). Positions are real free-web coordinates (it
  switches to free-web first, like Auto Arrange), so the result persists. The
  focal card itself does not move; the viewport then centres it — again, no
  zoom change (zoom effects deliberately deferred).

When OFF, double-click keeps the zoom-to-read behaviour (`focusCard`). All card
double-click sites route through `handleCardDblClick`, which branches on the
toggle. Recentring is skipped mid node-drag / mid-connection so the canvas
never pans out from under the pointer.

## Auto Condense (toggle, top-right chip row)

Off by default, persisted per browser (`wb-auto-condense`). When ON and the
view is below the compact tier, RENDERED positions contract uniformly toward
the board centre by the largest factor that keeps every card pair from
touching (`condenseTransform`: O(n²) pair scan, cheaper-axis clearance, floor
0.2, 36px gap) — zoomed-out views waste far less white space while the
arrangement's shape is preserved. **Strictly view-only**: stored `card.x/y`
are untouched; `cardPosition` = `cardPositionRaw` + contraction, and free-web
drag stops write back through the INVERSE transform. Snap/collision helpers
(`positionIsClear`, `snapCardNearAnchor`, the snap-on-link watcher) work in
raw space via `cardPositionRaw`. Skipped in the hierarchical tree (already a
compact column). Zooming back past the compact threshold releases the
contraction with a glide.

## Node context menu + destructive deletes

Right-click on any node opens a screen-space menu (`onFlowNodeContextMenu` /
`.node-context-menu`): **Edit {Type}** (focus-zooms the card and drops the
caret into its first field), **Delete**, and **Delete Full Branch (N nodes)**
(the node plus its `linkedSubtreeOf` — hidden for leaf nodes). A right-click
on a field the user is ACTIVELY editing keeps the native browser menu
(copy/paste); any other right-click on the node opens ours.

Every delete path (buttons, keyboard `Delete`, menu) goes through one stressed
confirmation dialog — "This is not undoable / You cannot Ctrl+Z your way out
of this" — and while it is open, every targeted node is dimmed, desaturated,
and pulses a slow red ring (`.doomed-node`, driven by `deleteTargetIds`), so
the blast radius is visible before committing.

## Gotchas (learned the hard way)

- **`isValidConnection` re-validates EVERY edge passed to `setEdges`**, not just
  interactive attempts. A persisted link re-presenting itself (same id) must be
  accepted, or no stored edge ever renders.
- **The board-open fit must wait for `onNodesInitialized`** — framing before Vue
  Flow measures the nodes lands at an arbitrary viewport.
- **Bump `collapseGeneration` after a view switch** (and any tier/DOM change
  that alters card heights) so the layout solvers re-measure; otherwise tree
  rows overlap.
- Overlays (spawn menu, endpoint popup) are **screen-space**, anchored to a flow
  point via the live `viewport` — constant size at every zoom, no
  counter-scaling.
- The Settings → Whiteboard `default_zoom` option was removed; boards always
  open fit-to-content.
