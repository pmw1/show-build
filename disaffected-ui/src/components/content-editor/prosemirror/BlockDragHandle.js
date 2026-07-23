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

// CSS injected once per page. Kept inline (not a scoped .vue block) because this
// plugin's DOM is created imperatively and lives inside the ProseMirror surface.
const STYLE_ID = 'pm-block-drag-handle-styles';
const STYLE_TEXT = `
/* Open a 30px left gutter on every top-level block for the handle to live in. */
.ProseMirror .pm-drag-block {
  position: relative;
  padding-left: 34px;
  transition: margin 0.12s ease;
}
/* The grab handle ("drag tag") in the left gutter — mirrors .drag-handle-column. */
.pm-drag-handle {
  position: absolute;
  left: 0;
  top: 0;
  width: 30px;
  height: 100%;
  min-height: 1.4em;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 2px;
  opacity: 0.3;
  transition: opacity 0.2s ease, background 0.2s ease;
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
  border-radius: 6px;
  z-index: 5;
}
.pm-drag-handle:hover {
  opacity: 1;
  background: rgba(33, 150, 243, 0.08);
}
.pm-drag-handle.pm-dragging {
  cursor: grabbing;
  opacity: 1;
}
/* The 6-dot grip glyph. */
.pm-drag-handle-grip {
  color: rgba(0, 0, 0, 0.4);
  font-size: 16px;
  line-height: 1;
  transition: color 0.2s ease;
  pointer-events: none;
}
.pm-drag-handle:hover .pm-drag-handle-grip {
  color: ${DROPLINE};
}
/* The dragged source block: draglight highlight + drop-shadow glow. */
.ProseMirror .pm-drag-source {
  background: ${DRAGLIGHT};
  box-shadow: 0 0 0 2px ${DROPLINE}, 0 0 12px ${DROPLINE};
  border-radius: 4px;
  opacity: 0.9;
}
/* Live displacement: the block just AFTER the target gap is pushed down, and the
   block just BEFORE it is pushed up — surrounding rows reflow around the line. */
.ProseMirror .pm-displace-after { margin-top: 26px; }
.ProseMirror .pm-displace-before { margin-bottom: 26px; }
/* The drop indicator / drag line widget. */
.pm-drop-gap {
  position: relative;
  display: block;
  height: 0;
  margin: 0;
}
.pm-drop-gap::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 12px;
  height: 3px;
  background: ${DROPLINE};
  border-radius: 2px;
  box-shadow: 0 0 8px ${DROPLINE};
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
    blocks.push({ index, start: offset, end: offset + node.nodeSize });
  });
  return blocks;
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
    // (b) gutter class on every top-level block.
    const classes = ['pm-drag-block'];

    if (dragState && dragState.active) {
      if (b.index === dragState.sourceIndex) classes.push('pm-drag-source');
      // Live displacement around the target gap: the block right after the gap
      // shifts down, the block right before it shifts up.
      else if (b.index === dragState.gapIndex) classes.push('pm-displace-after');
      else if (b.index === dragState.gapIndex - 1) classes.push('pm-displace-before');
    }

    decos.push(
      Decoration.node(b.start, b.end, { class: classes.join(' ') }, { blockIndex: b.index })
    );

    // (a) the grab handle widget anchored at the block start. side:-1 keeps it
    // before the block content; ignoreSelection stops it from interfering with
    // text selection/caret placement inside paragraphs.
    decos.push(
      Decoration.widget(b.start, () => makeHandle(b.index), {
        side: -1,
        key: `pm-drag-handle-${b.index}`,
        ignoreSelection: true,
      })
    );
  });

  // (c) the drag line widget at the target gap (between blocks).
  if (dragState && dragState.active && dragState.gapIndex != null) {
    const gi = dragState.gapIndex;
    const gapPos = gi >= blocks.length ? state.doc.content.size : blocks[gi].start;
    // Only show the line when the drop is a real move (not the source's own gaps).
    const noop = gi === dragState.sourceIndex || gi === dragState.sourceIndex + 1;
    if (!noop) {
      const line = document.createElement('div');
      line.className = 'pm-drop-gap';
      decos.push(Decoration.widget(gapPos, line, { side: -1, key: 'pm-drop-gap' }));
    }
  }

  return DecorationSet.create(state.doc, decos);
}

function makeHandle(blockIndex) {
  const handle = document.createElement('span');
  handle.className = 'pm-drag-handle';
  handle.setAttribute('contenteditable', 'false');
  handle.setAttribute('data-pm-drag-handle', String(blockIndex));
  handle.title = 'Drag to reorder';

  const grip = document.createElement('span');
  grip.className = 'pm-drag-handle-grip';
  grip.textContent = '⁙'; // ⁙ dotted grip glyph
  handle.appendChild(grip);

  // Pointer-based drag. Using pointer events (not HTML5 DnD) means text
  // selection inside paragraphs is never affected — a move only ever starts
  // from this handle.
  handle.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    if (!editorView) return;
    event.preventDefault();
    event.stopPropagation();
    startDrag(editorView, blockIndex, handle, event);
  });

  return handle;
}

function startDrag(view, sourceIndex, handle, downEvent) {
  handle.classList.add('pm-dragging');
  try {
    handle.setPointerCapture(downEvent.pointerId);
  } catch {
    /* setPointerCapture can throw if the pointer is gone; ignore. */
  }

  const setDrag = (patch) => {
    const tr = view.state.tr.setMeta(blockDragHandleKey, patch);
    tr.setMeta('addToHistory', false); // drag preview must not enter undo stack
    view.dispatch(tr);
  };

  // Seed the drag state; gap starts at the source's leading gap (a no-op spot).
  setDrag({ active: true, sourceIndex, gapIndex: sourceIndex });

  const onMove = (moveEvent) => {
    const gapIndex = nearestGap(view, moveEvent.clientY);
    const cur = blockDragHandleKey.getState(view.state);
    if (!cur || cur.gapIndex !== gapIndex) {
      setDrag({ active: true, sourceIndex, gapIndex });
    }
  };

  const onUp = () => {
    handle.classList.remove('pm-dragging');
    try {
      handle.releasePointerCapture(downEvent.pointerId);
    } catch {
      /* ignore */
    }
    window.removeEventListener('pointermove', onMove, true);
    window.removeEventListener('pointerup', onUp, true);
    window.removeEventListener('pointercancel', onUp, true);

    const cur = blockDragHandleKey.getState(view.state);
    // Clear the drag-preview state first.
    setDrag({ active: false, sourceIndex: null, gapIndex: null });

    if (cur && cur.active && cur.gapIndex != null) {
      const moveTr = buildMoveTransaction(view.state, sourceIndex, cur.gapIndex);
      if (moveTr) view.dispatch(moveTr);
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
