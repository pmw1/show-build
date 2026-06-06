/**
 * BlockDragHandle — drag-and-drop reordering of top-level script blocks.
 *
 * The script document is a FLAT sequence of top-level blocks:
 *     doc -> (paragraph | cue)+
 * (see src/utils/prosemirror/schema.js). This extension lets the user reorder
 * those top-level blocks by dragging a grab handle rendered in a ~30px left
 * gutter of each block. It NEVER nests blocks — a drag only moves one top-level
 * node to a different top-level gap.
 *
 * Implementation = "Option B" from the migration plan: a thin TipTap
 * Extension whose only job is addProseMirrorPlugins() returning ONE custom
 * ProseMirror Plugin. The plugin:
 *
 *   - props.decorations renders, every redraw:
 *       (a) a widget decoration at each top-level block start = the left-gutter
 *           grab handle (the "drag tag");
 *       (b) a node decoration on every block = the `pm-drag-block` class that
 *           opens the 30px gutter and makes the block position:relative so the
 *           handle can sit in it;
 *       (c) WHILE dragging: a `pm-drag-source` node decoration on the dragged
 *           block (drop-shadow glow + draglight highlight), and a `pm-drop-gap`
 *           widget at the target gap = the drag line / drop indicator. The gap
 *           moves live as the pointer moves, so surrounding rows visibly reflow
 *           (the row above/below the line gets margin pushed apart).
 *
 *   - Drag is driven by POINTER events on the handle (not HTML5 DnD): pointer
 *     events never touch text selection inside paragraphs, so normal editing is
 *     untouched — only the handle initiates a move. dragstart records the
 *     dragged block's top-level index; pointermove computes the nearest
 *     top-level gap from the pointer Y vs each block's DOM rect and stores it in
 *     plugin state (dispatched as a meta tx so decorations redraw); pointerup
 *     builds ONE transaction that deletes the source block and re-inserts the
 *     same node at the target gap.
 *
 * Undo: the move is a single transaction, so the existing UndoRedo extension
 * covers it (no separate history here).
 *
 * Styling reuses the SAME runtime CSS vars the legacy editor sets on
 * document.documentElement (EditorPanel sets --dropline-color / --draglight-color):
 *   --dropline-color  : drag line / drop-indicator color (fallback rgb(33,150,243))
 *   --draglight-color : displacement / dragged-row highlight bg (fallback rgba(33,150,243,0.15))
 * The dragged-row glow reuses --dropline-color (no dedicated shadow var exists).
 * The gutter mirrors the legacy `.drag-handle-column` (30px, opacity 0.3 -> 1 on
 * hover, hover bg rgba(33,150,243,0.08), icon color rgb(33,150,243) on hover).
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export const blockDragHandleKey = new PluginKey('blockDragHandle');

// Module-scoped live EditorView ref, set by the plugin's view() lifecycle so
// decorations() (which only receives state) can call view.nodeDOM for the
// rect-based gap detection. The plugin is created once per editor and this app
// mounts a single ScriptEditor instance.
let editorView = null;

const DROPLINE = 'var(--dropline-color, rgb(33, 150, 243))';
const DRAGLIGHT = 'var(--draglight-color, rgba(33, 150, 243, 0.15))';

// ── Drag animation tuning (todo #39) ───────────────────────────────────────
// One-knob feel, mirroring the rundown panel's SortableJS :animation="200".
// Displacement is GPU-composited (transform: translateY) — no per-frame reflow.
const DRAG_SHIFT_PX = 64;          // how far blocks slide down to open the drop space
const DRAG_ANIM_MS = 200;          // displacement + FLIP-settle duration
const DRAG_EASE = 'cubic-bezier(0.2, 0, 0, 1)';  // smooth, no overshoot

// ── Auto-scroll while dragging near an edge (todo #48) ──────────────────────
const AUTOSCROLL_ZONE_PX = 70;     // distance from top/bottom edge that triggers scroll
const AUTOSCROLL_MAX_PX = 16;      // max px scrolled per frame (at the very edge)

// Find the scrollable container holding the editor (the .script-editor-host with
// overflow-y:auto), falling back to the nearest scrollable ancestor of view.dom.
function getScrollContainer(view) {
  let el = view.dom && view.dom.parentElement;
  while (el) {
    if (el.classList && el.classList.contains('script-editor-host')) return el;
    const oy = getComputedStyle(el).overflowY;
    if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight) return el;
    el = el.parentElement;
  }
  return null;
}

// CSS injected once per page. Kept inline (not a scoped .vue block) because this
// plugin's DOM is created imperatively and lives inside the ProseMirror surface.
const STYLE_ID = 'pm-block-drag-handle-styles';
const STYLE_TEXT = `
/* All draggable blocks are position:relative (for the grip anchor + displacement).
   Displacement is driven by transform:translateY (GPU-composited — no per-frame
   layout reflow, unlike the old margin animation), so it stays smooth (todo #39). */
.ProseMirror .pm-drag-block {
  position: relative;
  transition: transform ${DRAG_ANIM_MS}ms ${DRAG_EASE};
}
/* Only pay the compositing cost while a drag is live. */
.ProseMirror.pm-dragging-active .pm-drag-block {
  will-change: transform;
}
/* PARAGRAPHS get a 34px left gutter with a grip drawn via ::before. Cue cards do
   NOT (they have their own mdi-drag-vertical handle). */
.ProseMirror .pm-drag-gutter {
  padding-left: 34px;
}
.ProseMirror .pm-drag-gutter::before {
  /* Match the cue card's handle: the same Material Design Icons "drag-vertical"
     glyph (\\F01DD) the cue renders via <v-icon size="small">mdi-drag-vertical</v-icon>. */
  content: "\\F01DD";
  font-family: "Material Design Icons";
  font-weight: normal;
  font-style: normal;
  position: absolute;
  left: 0;
  top: 0;
  width: 34px;
  height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 2px;
  color: rgba(0, 0, 0, 0.4);
  /* Match the cue card's drag handle visual size. */
  font-size: 24px;
  line-height: 1;
  opacity: 0.3;
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
  border-radius: 6px;
  transition: opacity 0.2s ease, background 0.2s ease, color 0.2s ease;
  z-index: 5;
}
.ProseMirror .pm-drag-gutter:hover::before {
  opacity: 1;
  /* No hover background: it tinted the left gutter a faint blue-grey on every
     paragraph hover, which reads as an unwanted grey band — especially over a
     bulleted paragraph's wide left indent. The icon darkening to DROPLINE below
     is enough of a grab affordance; keep the zone the same white as the page. */
  background: transparent;
  color: ${DROPLINE};
}
.ProseMirror .pm-drag-gutter.pm-grabbing::before {
  cursor: grabbing;
  opacity: 1;
  color: ${DROPLINE};
}
/* The dragged source block: draglight highlight + drop-shadow glow. */
.ProseMirror .pm-drag-source {
  background: ${DRAGLIGHT};
  box-shadow: 0 0 0 2px ${DROPLINE}, 0 0 12px ${DROPLINE};
  border-radius: 4px;
  opacity: 0.9;
}
/* Live displacement: the dropline indicator stays cast in place at the target
   gap, and the gap opens EVENLY around it — blocks above slide up by half and
   blocks at/below slide down by half, so whitespace is balanced top & bottom
   (todo #39). */
.ProseMirror .pm-shift-down { transform: translateY(${DRAG_SHIFT_PX / 2}px); }
.ProseMirror .pm-shift-up   { transform: translateY(-${DRAG_SHIFT_PX / 2}px); }
/* While dragging, every block EXCEPT the dragged one (and the flashing ones on
   drop) dims to 75% so the field recedes and the drag/drop reads clearly. Returns
   to full when the flash sequence ends (todo #46). Transition so it eases in/out. */
.ProseMirror .pm-dim {
  opacity: 0.65;
  transition: opacity ${DRAG_ANIM_MS}ms ${DRAG_EASE};
}
/* FLIP helper: during the invert step we set an inline transform with NO
   transition so the block jumps to its old position, then clearing the inline
   transform animates (via .pm-drag-block's transition) the glide to its new spot. */
.ProseMirror .pm-flip-no-anim { transition: none !important; }
/* Drop-confirmation flash (todo #46). Pattern (per Kevin):
   - NEIGHBOURS (above/below the dropped block) pulse 3x FAST.
   - The DROPPED block snaps ON once, then SLOWLY fades out over a duration equal
     to (the neighbours' 3 fast pulses) x 2 — i.e. it lingers/glows down while the
     neighbours strobe and for the same length again after.
   Colours read on bare <p> (the old 0.15 alpha was invisible; cue cards masked it
   via their solid card bg): drop fill ~0.45 + dropline ring; neighbour ~0.225. */
/* Both flashes fill with the theme's --draglight-color (no ring). The TARGET
   starts at the FULL draglight opacity and slowly fades out; the NEIGHBOURS peak
   at 50% of that (via the element opacity) and strobe (#46, per Kevin). */
@keyframes pm-flash-drop {
  0%   { background-color: ${DRAGLIGHT}; }
  100% { background-color: transparent; }
}
@keyframes pm-flash-neighbor {
  /* 50% of the draglight fill — mixed 50/50 with transparent so only the BG tint
     is halved (NOT the text, which element opacity would dim). color-mix is
     widely supported; the same draglight var feeds it. */
  0%, 100% { background-color: transparent; }
  50%      { background-color: color-mix(in srgb, ${DRAGLIGHT} 50%, transparent); }
}
/* Paragraphs are full-width and padding-less; a flash bg butts right to the edge.
   Round the corners a touch so the fill reads as a block, not a full-bleed bar. */
.ProseMirror .pm-flash-drop,
.ProseMirror .pm-flash-neighbor {
  border-radius: 4px;
}
/* Neighbour fast pulse: 0.2s x 3 = 0.6s. Dropped-block fade: that x 2 = 1.2s, run
   once with an ease-out so it fades fast then lingers. Keep these two in sync —
   if you change the neighbour pulse, the drop fade = (pulse * 3) * 2. */
.ProseMirror .pm-flash-neighbor {
  animation: pm-flash-neighbor 0.2s ease-in-out 3 !important;
}
.ProseMirror .pm-flash-drop {
  animation: pm-flash-drop 1.2s ease-out 1 !important;
}
/* The drop target — a "DROP HERE" block (mirrors the legacy .ghost-segment),
   using the theme's dropline + draglight colors. Sits in the opened gap. */
/* The "DROP HERE" block at the target gap (mirrors the legacy .ghost-segment),
   theme-colored. Fades + grows in when it appears at a new gap. */
@keyframes pm-drop-gap-in {
  from { opacity: 0; transform: scaleY(0.5); }
  to   { opacity: 1; transform: scaleY(1); }
}
.pm-drop-gap {
  position: relative;
  display: block;
  height: 52px;
  margin: 6px 0;
  box-sizing: border-box;
  background: ${DRAGLIGHT};
  border: 3px dashed ${DROPLINE};
  border-radius: 6px;
  box-shadow: 0 0 12px ${DROPLINE};
  transform-origin: center;
  /* Fade-in fires ONCE (first-appear); repositioning the cast indicator to a new
     gap reuses the same element, so it no longer re-flashes on every move (#39). */
  animation: pm-drop-gap-in 0.16s cubic-bezier(0.2, 0.8, 0.2, 1);
}
/* Cursor-attached drag ghost — a floating chip showing what's being dragged.
   Appended to <body>, fixed at 0,0, moved via transform:translate to the cursor. */
.pm-drag-ghost {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  max-width: 640px;
  max-height: 280px;
  overflow: hidden;
  padding: 8px 12px;
  background: var(--v-theme-surface, #fff);
  border: 2px solid ${DROPLINE};
  border-radius: 8px;
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  opacity: 0.92;
  will-change: transform;
}
/* The cloned full block inside the ghost — non-interactive, fades at the bottom
   if the block is taller than the ghost's max-height. */
.pm-drag-ghost-clone {
  pointer-events: none;
  -webkit-mask-image: linear-gradient(to bottom, #000 78%, transparent 100%);
  mask-image: linear-gradient(to bottom, #000 78%, transparent 100%);
}
.pm-drag-ghost-clone * {
  pointer-events: none !important;
}
.pm-drag-ghost-label {
  display: block;
  max-width: 296px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
  font-weight: 700;
  color: color-mix(in srgb, ${DROPLINE} 65%, black);
}
.pm-drop-gap-label {
  position: absolute;
  top: 50%;
  left: 14px;
  transform: translateY(-50%);
  max-width: calc(100% - 28px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  /* Same hue as the dropline (theme color), just darker — mix it with black.
     Falls back to the plain dropline color where color-mix isn't supported. */
  color: ${DROPLINE};
  color: color-mix(in srgb, ${DROPLINE} 65%, black);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
  pointer-events: none;
}
`;

function ensureStyles() {
  if (typeof document === 'undefined') return;
  if (document.getElementById(STYLE_ID)) return;
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = STYLE_TEXT;
  document.head.appendChild(el);
}

/**
 * Walk the doc's top-level children and return their boundaries.
 * @returns {Array<{index:number, start:number, end:number}>}
 *   start = position BEFORE the block, end = position AFTER the block.
 */
function topLevelBlocks(doc) {
  const blocks = [];
  doc.forEach((node, offset, index) => {
    blocks.push({ index, start: offset, end: offset + node.nodeSize, type: node.type.name });
  });
  return blocks;
}

/**
 * Label for the drop-target box, previewing the block being dragged:
 *   - cue:       "{CUE TYPE} {slug}"  (e.g. "SOT the-odyssee")
 *   - paragraph: "first five words… …last three words" (collapsed if short)
 */
function dragLabel(node) {
  if (!node) return 'Move here';
  if (node.type.name === 'cue') {
    const f = node.attrs.fields || {};
    const cueType = (node.attrs.cueType || f.Type || f.type || 'CUE').toString().toUpperCase();
    const slug = (f.Slug || f.slug || '').toString().trim();
    return slug ? `${cueType}  ${slug}` : cueType;
  }
  // Paragraph: first 5 … last 3 words.
  const text = (node.textContent || '').trim().replace(/\s+/g, ' ');
  if (!text) return 'Empty paragraph';
  const words = text.split(' ');
  if (words.length <= 8) return text; // short enough to show whole
  const head = words.slice(0, 5).join(' ');
  const tail = words.slice(-3).join(' ');
  return `${head}…  …${tail}`;
}

/**
 * Build the move transaction: delete the source block, then re-insert the SAME
 * node object at the target gap. Position validity is preserved by mapping the
 * insertion point through the delete step.
 *
 * @param {EditorState} state
 * @param {number} sourceIndex top-level index being moved
 * @param {number} gapIndex insertion gap (0..childCount); the node lands BEFORE
 *   the block currently at gapIndex (or at the very end if gapIndex===childCount)
 * @returns {Transaction|null}
 */
function buildMoveTransaction(state, sourceIndex, gapIndex) {
  const { doc } = state;
  const blocks = topLevelBlocks(doc);
  if (sourceIndex < 0 || sourceIndex >= blocks.length) return null;

  // A gap on either side of the source block is a no-op (lands in the same spot).
  if (gapIndex === sourceIndex || gapIndex === sourceIndex + 1) return null;

  const src = blocks[sourceIndex];
  const node = doc.child(sourceIndex); // whole node (cue atom or paragraph) w/ attrs

  // Absolute position of the chosen gap in the ORIGINAL doc: start of the block
  // at gapIndex, or end of doc if inserting at the very end.
  const gapPos = gapIndex >= blocks.length ? doc.content.size : blocks[gapIndex].start;

  let tr = state.tr;
  // 1) Remove the source block. tr.delete records a mapping step.
  tr = tr.delete(src.start, src.end);
  // 2) Map the gap position THROUGH the delete so it stays valid afterward.
  //    (If the gap was after the deleted range it shifts left by the block size;
  //    if before, it is unchanged.) -1 bias keeps an insertion at a deleted
  //    boundary on the correct side.
  const mappedGap = tr.mapping.map(gapPos, -1);
  // 3) Insert the same node at the mapped gap.
  tr = tr.insert(mappedGap, node);
  tr.setMeta('blockDragHandle', { type: 'move' });
  return tr;
}

function buildDecorations(state, dragState) {
  const decos = [];
  const blocks = topLevelBlocks(state.doc);

  blocks.forEach((b) => {
    // Every block is a drag participant (for displacement + source styling), but
    // only PARAGRAPHS get the left-gutter grip. Cue cards already have their OWN
    // drag handle (the mdi-drag-vertical icon in the card), so adding a gutter
    // grip to them would be a confusing second handle — the cue's handle drives
    // the drag instead (see handleDOMEvents: pointerdown on .drag-handle).
    const classes = ['pm-drag-block'];
    if (b.type !== 'cue') classes.push('pm-drag-gutter');

    if (dragState && dragState.active && b.index === dragState.sourceIndex) {
      classes.push('pm-drag-source');
    }

    // Displacement (todo #39): the dropline stays cast and the gap opens EVENLY
    // around it — blocks ABOVE the gap slide up by half, blocks AT/BELOW slide
    // down by half, so there's equal whitespace above and below the indicator.
    // Computed in the DECORATION class list (not toggled imperatively) so a
    // decoration redraw doesn't strip it — ProseMirror updates the class IN PLACE
    // on the same DOM element, so the transform transition fires smoothly. The
    // dragged source itself never shifts.
    if (dragState && dragState.active && dragState.gapIndex != null) {
      const gi = dragState.gapIndex;
      const noop = gi === dragState.sourceIndex || gi === dragState.sourceIndex + 1;
      if (!noop && b.index !== dragState.sourceIndex) {
        if (b.index >= gi) classes.push('pm-shift-down');
        else classes.push('pm-shift-up');
      }
    }

    // Drop-confirmation flash (todo #46): applied via the DECORATION (not an
    // imperative class) so it survives the autosave round-trip that re-renders
    // the paragraph DOM right after a drop — that re-render was wiping any class
    // set imperatively on the freshly-rebuilt <p>, so paragraphs never flashed
    // (cue NodeViews kept their DOM, which is why only cues flashed). ProseMirror
    // re-applies the decoration class on every redraw, so the keyframe runs.
    const isFlashing = dragState && dragState.flash &&
      (b.index === dragState.flash.landed ||
       b.index === dragState.flash.landed - 1 ||
       b.index === dragState.flash.landed + 1);
    if (dragState && dragState.flash) {
      if (b.index === dragState.flash.landed) classes.push('pm-flash-drop');
      else if (b.index === dragState.flash.landed - 1 || b.index === dragState.flash.landed + 1) {
        classes.push('pm-flash-neighbor');
      }
    }

    // Dim the field (todo #46): while DRAGGING, every block except the dragged one
    // dims to 75%; during the post-drop FLASH, every block except the flashing
    // ones (which return to full as they flash) stays dimmed until the sequence
    // ends. The dim is cleared with the same meta dispatch that clears the flash.
    const dimWhileDragging = dragState && dragState.active && b.index !== dragState.sourceIndex;
    const dimWhileFlashing = dragState && dragState.flash && !isFlashing;
    if (dimWhileDragging || dimWhileFlashing) classes.push('pm-dim');

    // The grab handle is NOT a separate widget (a widget at b.start renders
    // BETWEEN blocks and anchors to the editor root, so they all piled up at the
    // top — only block 0 was visible, and atom cues got none). Instead the
    // .pm-drag-block class opens a 34px left gutter and draws the grip via a
    // ::before pseudo-element that nests inside EACH block (paragraph AND cue).
    // Drag-start is detected by a pointerdown in that gutter region (handleDOMEvents).
    decos.push(
      Decoration.node(b.start, b.end, { class: classes.join(' ') }, { blockIndex: b.index })
    );
  });

  // (c) the drop-target block widget at the target gap. Its label previews the
  // block being DRAGGED: for a paragraph "first five … last three" words; for a
  // cue "{CUE TYPE} {slug}". Recreated when the gap changes (fades in).
  if (dragState && dragState.active && dragState.gapIndex != null) {
    const gi = dragState.gapIndex;
    const gapPos = gi >= blocks.length ? state.doc.content.size : blocks[gi].start;
    const noop = gi === dragState.sourceIndex || gi === dragState.sourceIndex + 1;
    if (!noop) {
      const sourceNode = (dragState.sourceIndex != null && dragState.sourceIndex < state.doc.childCount)
        ? state.doc.child(dragState.sourceIndex)
        : null;
      const box = document.createElement('div');
      box.className = 'pm-drop-gap';
      const label = document.createElement('span');
      label.className = 'pm-drop-gap-label';
      label.textContent = dragLabel(sourceNode);
      box.appendChild(label);
      // Stable key (NOT gap-indexed) so ProseMirror REUSES the same widget DOM
      // when the gap moves — it repositions instead of destroy+recreate, so the
      // fade-in fires once on first appear rather than re-flashing each move (#39).
      decos.push(Decoration.widget(gapPos, box, { side: -1, key: 'pm-drop-gap' }));
    }
  }

  return DecorationSet.create(state.doc, decos);
}

// ── Cursor-attached drag ghost ─────────────────────────────────────────────
// A floating element that follows the pointer while dragging (we use pointer
// events, not native HTML5 DnD, so there is no built-in drag image). Shows the
// same preview as the drop box: paragraph "first…last" words / "{TYPE} slug".
let dragGhost = null;

function createGhost(node, sourceEl) {
  removeGhost();
  const g = document.createElement('div');
  g.className = 'pm-drag-ghost';
  if (node && node.type.name === 'cue') g.classList.add('pm-drag-ghost-cue');

  // Show the FULL dragged content: clone the actual source block DOM (the whole
  // paragraph text / the whole cue card) and lock its rendered width so it looks
  // like a lifted copy of the real element. Fall back to the short label if the
  // clone is unavailable.
  if (sourceEl && sourceEl.cloneNode) {
    const clone = sourceEl.cloneNode(true);
    clone.classList.remove('pm-grabbing', 'pm-shift-down', 'pm-shift-up', 'pm-flip-no-anim', 'pm-drag-source');
    clone.style.margin = '0';
    clone.style.transform = '';
    clone.style.width = `${Math.round(sourceEl.getBoundingClientRect().width)}px`;
    const inner = document.createElement('div');
    inner.className = 'pm-drag-ghost-clone';
    inner.appendChild(clone);
    g.appendChild(inner);
  } else {
    const label = document.createElement('span');
    label.className = 'pm-drag-ghost-label';
    label.textContent = dragLabel(node);
    g.appendChild(label);
  }
  document.body.appendChild(g);
  dragGhost = g;
}

function moveGhost(clientX, clientY) {
  if (!dragGhost) return;
  // Offset slightly down-right of the cursor so it doesn't sit under the pointer.
  dragGhost.style.transform = `translate(${clientX + 14}px, ${clientY + 10}px)`;
}

function removeGhost() {
  if (dragGhost && dragGhost.parentElement) dragGhost.parentElement.removeChild(dragGhost);
  dragGhost = null;
}

function startDrag(view, sourceIndex, blockEl, downEvent) {
  // blockEl is the .pm-drag-block element; it carries the pm-grabbing class
  // (added by the caller) for the grabbing cursor while the drag is live.
  try {
    blockEl.setPointerCapture(downEvent.pointerId);
  } catch {
    /* setPointerCapture can throw if the pointer is gone; ignore. */
  }

  // Attach the cursor ghost showing what's being dragged (full content clone).
  const srcNode = sourceIndex < view.state.doc.childCount ? view.state.doc.child(sourceIndex) : null;
  createGhost(srcNode, blockEl);
  moveGhost(downEvent.clientX, downEvent.clientY);

  // Mark the editor as actively dragging so the will-change compositing hint
  // applies only during the drag (todo #39).
  if (view.dom && view.dom.classList) view.dom.classList.add('pm-dragging-active');

  const setDrag = (patch) => {
    const tr = view.state.tr.setMeta(blockDragHandleKey, patch);
    tr.setMeta('addToHistory', false); // drag preview must not enter undo stack
    view.dispatch(tr);
  };

  // Seed the drag state; gap starts at the source's leading gap (a no-op spot).
  setDrag({ active: true, sourceIndex, gapIndex: sourceIndex });

  // Auto-scroll state (todo #48): the scroll container + the last pointer Y, so
  // the rAF loop can scroll AND recompute the drop gap from the current pointer
  // even when the pointer is held still in an edge zone.
  const scroller = getScrollContainer(view);
  let lastClientX = downEvent.clientX;
  let lastClientY = downEvent.clientY;
  let scrollRaf = null;

  // Refresh the drop gap from the current pointer (used by onMove + scroll loop).
  const refreshGap = () => {
    const gapIndex = nearestGap(view, lastClientY);
    const cur = blockDragHandleKey.getState(view.state);
    if (!cur || cur.gapIndex !== gapIndex) {
      // setDrag updates the gapIndex → buildDecorations recomputes which blocks
      // carry pm-shift-down → ProseMirror updates the class in place → the
      // transform transition animates the slide (todo #39). No imperative DOM.
      setDrag({ active: true, sourceIndex, gapIndex });
    }
  };

  // Edge auto-scroll loop: while the pointer is within AUTOSCROLL_ZONE_PX of the
  // container's top/bottom edge, scroll toward it each frame (speed ramps up the
  // closer to the edge) and re-evaluate the drop gap, so the user can drop at a
  // position that isn't currently on screen (todo #48).
  const stopAutoScroll = () => {
    if (scrollRaf != null) { cancelAnimationFrame(scrollRaf); scrollRaf = null; }
  };
  const autoScrollTick = () => {
    if (!scroller) { scrollRaf = null; return; }
    const rect = scroller.getBoundingClientRect();
    const distTop = lastClientY - rect.top;
    const distBottom = rect.bottom - lastClientY;
    let dy = 0;
    if (distTop < AUTOSCROLL_ZONE_PX) {
      dy = -Math.ceil(AUTOSCROLL_MAX_PX * (1 - Math.max(0, distTop) / AUTOSCROLL_ZONE_PX));
    } else if (distBottom < AUTOSCROLL_ZONE_PX) {
      dy = Math.ceil(AUTOSCROLL_MAX_PX * (1 - Math.max(0, distBottom) / AUTOSCROLL_ZONE_PX));
    }
    if (dy !== 0) {
      const before = scroller.scrollTop;
      scroller.scrollTop += dy;
      if (scroller.scrollTop !== before) {
        moveGhost(lastClientX, lastClientY); // keep the ghost glued to the cursor
        refreshGap();                        // drop target tracks while scrolling
      }
      scrollRaf = requestAnimationFrame(autoScrollTick);
    } else {
      scrollRaf = null; // left the edge zone — stop until re-entered
    }
  };
  const maybeAutoScroll = () => {
    if (!scroller || scrollRaf != null) return;
    const rect = scroller.getBoundingClientRect();
    const inZone = (lastClientY - rect.top) < AUTOSCROLL_ZONE_PX ||
                   (rect.bottom - lastClientY) < AUTOSCROLL_ZONE_PX;
    if (inZone) scrollRaf = requestAnimationFrame(autoScrollTick);
  };

  const onMove = (moveEvent) => {
    lastClientX = moveEvent.clientX;
    lastClientY = moveEvent.clientY;
    moveGhost(moveEvent.clientX, moveEvent.clientY); // ghost tracks the cursor
    refreshGap();
    maybeAutoScroll(); // start the edge-scroll loop if near an edge
  };

  const onUp = () => {
    blockEl.classList.remove('pm-grabbing');
    try {
      blockEl.releasePointerCapture(downEvent.pointerId);
    } catch {
      /* ignore */
    }
    window.removeEventListener('pointermove', onMove, true);
    window.removeEventListener('pointerup', onUp, true);
    window.removeEventListener('pointercancel', onUp, true);
    stopAutoScroll(); // halt the edge auto-scroll loop (todo #48)
    removeGhost(); // detach the cursor ghost
    if (view.dom && view.dom.classList) view.dom.classList.remove('pm-dragging-active');

    const cur = blockDragHandleKey.getState(view.state);
    const didMove = cur && cur.active && cur.gapIndex != null &&
      cur.gapIndex !== sourceIndex && cur.gapIndex !== sourceIndex + 1;

    if (didMove) {
      // Clear ONLY the displacement (gapIndex) but keep active=true so the field
      // stays dimmed (no un-dim flicker) until the flash takes over the dim.
      setDrag({ active: true, sourceIndex, gapIndex: sourceIndex });
      const moveTr = buildMoveTransaction(view.state, sourceIndex, cur.gapIndex);
      if (moveTr) {
        // FLIP settle: dispatch the move inside flipReorder so every block glides
        // from its old to new position instead of snapping (todo #39).
        flipReorder(view, () => view.dispatch(moveTr));
        // Drop flash + field dim (todo #46): set flash AND clear active in ONE
        // dispatch so the dim never lifts between drag-end and flash. The flash is
        // a DECORATION (survives the autosave re-render). Cleared after the
        // animation finishes — which also returns the dimmed blocks to full.
        const landedIndex = cur.gapIndex > sourceIndex ? cur.gapIndex - 1 : cur.gapIndex;
        setTimeout(() => {
          const t1 = view.state.tr.setMeta(blockDragHandleKey,
            { active: false, sourceIndex: null, gapIndex: null, flash: { landed: landedIndex } });
          t1.setMeta('addToHistory', false);
          view.dispatch(t1);
          setTimeout(() => {
            const t2 = view.state.tr.setMeta(blockDragHandleKey, { flash: null });
            t2.setMeta('addToHistory', false);
            view.dispatch(t2);
          }, 1350); // a touch past the dropped block's 1.2s slow fade-out (#46)
        }, 120);
      }
    } else {
      // No move (dropped in place) — just clear the drag state.
      setDrag({ active: false, sourceIndex: null, gapIndex: null });
    }
    view.focus();
  };

  window.addEventListener('pointermove', onMove, true);
  window.addEventListener('pointerup', onUp, true);
  window.addEventListener('pointercancel', onUp, true);
}

/**
 * Compute the nearest top-level GAP index for a given pointer Y (viewport
 * coords) by comparing against each block's DOM rect midpoint. Returns 0..N.
 */
function nearestGap(view, clientY) {
  const blocks = topLevelBlocks(view.state.doc);
  if (!blocks.length) return 0;

  for (let i = 0; i < blocks.length; i += 1) {
    const dom = view.nodeDOM(blocks[i].start);
    const el = dom && dom.nodeType === 1 ? dom : (dom && dom.parentElement);
    if (!el || !el.getBoundingClientRect) continue;
    const rect = el.getBoundingClientRect();
    const mid = rect.top + rect.height / 2;
    if (clientY < mid) return i; // pointer is above this block's middle -> gap before it
  }
  return blocks.length; // below everything -> trailing gap
}

// FLIP settle (todo #39): capture each block's position BEFORE the reorder, run
// `commitFn` (which dispatches the move, reordering the DOM), then on the next
// frame invert each block to its old spot (no transition) and clear it so the
// .pm-drag-block transition glides each block from old -> new position — the same
// FLIP technique SortableJS uses, so the drop reads as a smooth settle, not a snap.
function flipReorder(view, commitFn) {
  // FIRST: snapshot current top of every block element.
  const before = new Map();
  const blocksBefore = topLevelBlocks(view.state.doc);
  for (const b of blocksBefore) {
    const dom = view.nodeDOM(b.start);
    const el = dom && dom.nodeType === 1 ? dom : (dom && dom.parentElement);
    if (el && el.getBoundingClientRect) before.set(el, el.getBoundingClientRect().top);
  }

  commitFn(); // LAST: the doc reorders; DOM moves to final positions.

  requestAnimationFrame(() => {
    const blocksAfter = topLevelBlocks(view.state.doc);
    const movers = [];
    for (const b of blocksAfter) {
      const dom = view.nodeDOM(b.start);
      const el = dom && dom.nodeType === 1 ? dom : (dom && dom.parentElement);
      if (!el || !el.getBoundingClientRect) continue;
      const oldTop = before.get(el);
      if (oldTop == null) continue;
      const delta = oldTop - el.getBoundingClientRect().top;
      if (!delta) continue;
      // INVERT: jump back to the old position with no animation.
      el.classList.add('pm-flip-no-anim');
      el.style.transform = `translateY(${delta}px)`;
      movers.push(el);
    }
    if (!movers.length) return;
    // PLAY: next frame, drop the no-anim flag + clear the transform so the
    // .pm-drag-block transition animates each block to its real (new) spot.
    requestAnimationFrame(() => {
      for (const el of movers) {
        el.classList.remove('pm-flip-no-anim');
        el.style.transform = '';
      }
      // Clean up will-change after the settle completes.
      setTimeout(() => { for (const el of movers) el.style.transform = ''; }, DRAG_ANIM_MS + 50);
    });
  });
}

export const BlockDragHandle = Extension.create({
  name: 'blockDragHandle',

  addProseMirrorPlugins() {
    ensureStyles();
    return [
      new Plugin({
        key: blockDragHandleKey,

        state: {
          init() {
            return { active: false, sourceIndex: null, gapIndex: null };
          },
          apply(tr, value) {
            const meta = tr.getMeta(blockDragHandleKey);
            if (meta) return { ...value, ...meta };
            return value;
          },
        },

        props: {
          decorations(state) {
            // `this` is the plugin. decorations() only receives state, so we use
            // the module-scoped editorView (set by view() below) for the
            // rect-based gap detection inside buildDecorations.
            const dragState = this.getState(state);
            return buildDecorations(state, dragState);
          },

          handleDOMEvents: {
            // Start a drag when the user presses in the left GUTTER (the ~34px
            // handle strip) of any top-level block — works uniformly for
            // paragraphs AND cue cards. We detect the gutter by hit-testing the
            // pointer X against the .pm-drag-block element's left edge. Pressing
            // in the block's content area is ignored, so text selection / cue
            // card buttons are untouched.
            pointerdown(view, event) {
              if (event.button !== 0) return false;
              if (!event.target.closest) return false;
              const blockEl = event.target.closest('.pm-drag-block');
              if (!blockEl) return false;

              // Two ways to start a drag:
              //  1. CUE: pointerdown on the cue card's own handle (.drag-handle,
              //     the mdi-drag-vertical icon). The cue has no gutter grip.
              //  2. PARAGRAPH: pointerdown in the left gutter strip (≤34px from
              //     the block's left edge), where the ::before grip lives.
              const onCueHandle = !!event.target.closest('.drag-handle');
              const rect = blockEl.getBoundingClientRect();
              // The grip lives in the left gutter. In COLLAPSE mode the row puts
              // the line number first (0–26px) and pushes the grip to ~28–62px,
              // so the clickable strip must extend further (≤66px) to stay over
              // the visible grip. Normal mode keeps the original ≤34px strip.
              const gutterWidth = blockEl.classList.contains('pm-collapsed-para') ? 66 : 34;
              const inGutter = (event.clientX - rect.left) <= gutterWidth
                && blockEl.classList.contains('pm-drag-gutter');
              if (!onCueHandle && !inGutter) return false;

              // Find this block's top-level index.
              const blocks = topLevelBlocks(view.state.doc);
              let sourceIndex = -1;
              for (let i = 0; i < blocks.length; i += 1) {
                const dom = view.nodeDOM(blocks[i].start);
                const el = dom && dom.nodeType === 1 ? dom : dom && dom.parentElement;
                if (el === blockEl || (el && el.contains(blockEl)) || (blockEl.contains && blockEl.contains(el))) {
                  sourceIndex = i;
                  break;
                }
              }
              if (sourceIndex < 0) return false;
              event.preventDefault();
              event.stopPropagation();
              blockEl.classList.add('pm-grabbing');
              startDrag(view, sourceIndex, blockEl, event);
              return true;
            },
          },
        },

        view(view) {
          // Capture the live EditorView so decorations() (which only receives
          // state) can call view.nodeDOM for rect-based gap detection.
          editorView = view;
          return {
            destroy() {
              if (editorView === view) editorView = null;
            },
          };
        },
      }),
    ];
  },
});

export default BlockDragHandle;
