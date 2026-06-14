/**
 * BlockMultiSelect — multi-selection of top-level script blocks + bulk ops.
 *
 * Ports the legacy contenteditable editor's multi-select feature (EditorPanel
 * `multiSelectedSegments`) to the TipTap/ProseMirror script editor. The script
 * document is a FLAT sequence of top-level blocks (doc -> (paragraph | cue)+,
 * see src/utils/prosemirror/schema.js); this plugin lets the user select several
 * of those blocks at once and act on them in bulk.
 *
 * Selection gestures (mirrors the legacy behavior):
 *   - Ctrl/Cmd+Click a block  -> toggle that block in/out of the selection.
 *   - Shift+Click a block      -> range-select from the last anchor to here
 *                                 (replaces the current selection with the
 *                                 contiguous block run, like the old _selectRange).
 *   - Plain click / typing / Escape -> clears the multi-selection.
 *
 * Bulk operations (exposed as editor commands so the toolbar can call them):
 *   - deleteSelectedBlocks()   -> remove every selected block in ONE transaction.
 *   - swapSelectedBlocks()     -> swap exactly two selected blocks.
 *   - joinSelectedParagraphs() -> merge 2+ selected PARAGRAPHS' text into the
 *                                 first (cues are skipped; join is text-only).
 *   - toggleBulletOnSelection()-> toggle the `bullet` attr on selected paragraphs
 *                                 (turns ON if any selected paragraph lacks it).
 *   - setSpeakerOnSelection(s) -> set `speaker` on every selected paragraph.
 *   - clearBlockSelection()    -> drop the selection.
 * Each command returns the selection metadata the host needs (e.g. the selected
 * paragraph count) so the toolbar in ScriptEditor.vue can drive its buttons.
 *
 * Implementation mirrors BlockDragHandle.js: a thin TipTap Extension whose
 * addProseMirrorPlugins() returns ONE Plugin. Selected indices live in plugin
 * state (a Set of top-level indices + an anchor); a node Decoration paints the
 * `pm-multi-selected` class on each selected block. Bulk edits are single
 * transactions so the existing UndoRedo extension covers them. The plugin reads
 * the same --dropline-color / --draglight-color CSS vars the drag plugin uses, so
 * the highlight matches the editor's existing accent.
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export const blockMultiSelectKey = new PluginKey('blockMultiSelect');

const SELECT_BG = 'var(--draglight-color, rgba(33, 150, 243, 0.15))';
const SELECT_BORDER = 'var(--dropline-color, rgb(33, 150, 243))';

const STYLE_ID = 'pm-block-multiselect-styles';
const STYLE_TEXT = `
.ProseMirror .pm-multi-selected {
  position: relative;
  background: ${SELECT_BG};
  box-shadow: inset 3px 0 0 0 ${SELECT_BORDER};
  border-radius: 3px;
  transition: background 0.12s ease, box-shadow 0.12s ease;
}
/* A selected cue card: tint its frame the same way without fighting the card's
   own background. The inset bar reads as the selection marker. */
.ProseMirror .pm-multi-selected.pm-drag-block { box-shadow: inset 3px 0 0 0 ${SELECT_BORDER}; }
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
 * Top-level block boundaries (same shape as BlockDragHandle.topLevelBlocks).
 * @returns {Array<{index:number, start:number, end:number, type:string}>}
 */
function topLevelBlocks(doc) {
  const blocks = [];
  doc.forEach((node, offset, index) => {
    blocks.push({ index, start: offset, end: offset + node.nodeSize, type: node.type.name });
  });
  return blocks;
}

/** Resolve a DOM target to its top-level block index, or -1. */
function blockIndexFromEvent(view, event) {
  if (!event.target || !event.target.closest) return -1;
  const blockEl = event.target.closest('.pm-drag-block') || event.target.closest('p, .cue-node-view');
  if (!blockEl) return -1;
  const blocks = topLevelBlocks(view.state.doc);
  for (let i = 0; i < blocks.length; i += 1) {
    const dom = view.nodeDOM(blocks[i].start);
    const el = dom && dom.nodeType === 1 ? dom : dom && dom.parentElement;
    if (!el) continue;
    if (el === blockEl || el.contains(blockEl) || (blockEl.contains && blockEl.contains(el))) {
      return i;
    }
  }
  return -1;
}

function emptyState() {
  return { selected: new Set(), anchor: null };
}

/** Build the node decorations highlighting the selected blocks. */
function buildDecorations(state, pluginState) {
  if (!pluginState || !pluginState.selected || pluginState.selected.size === 0) {
    return DecorationSet.empty;
  }
  const blocks = topLevelBlocks(state.doc);
  const decos = [];
  pluginState.selected.forEach((idx) => {
    const b = blocks[idx];
    if (b) decos.push(Decoration.node(b.start, b.end, { class: 'pm-multi-selected' }));
  });
  return DecorationSet.create(state.doc, decos);
}

/** Dispatch a plugin-state patch as a meta transaction (not added to history). */
function setSelection(view, patch) {
  const tr = view.state.tr.setMeta(blockMultiSelectKey, patch);
  tr.setMeta('addToHistory', false);
  view.dispatch(tr);
}

/** Sorted ascending array of currently-selected top-level indices. */
function selectedIndices(state) {
  const ps = blockMultiSelectKey.getState(state);
  if (!ps) return [];
  return Array.from(ps.selected).sort((a, b) => a - b);
}

export const BlockMultiSelect = Extension.create({
  name: 'blockMultiSelect',

  addProseMirrorPlugins() {
    ensureStyles();
    return [
      new Plugin({
        key: blockMultiSelectKey,

        state: {
          init() {
            return emptyState();
          },
          apply(tr, value) {
            const meta = tr.getMeta(blockMultiSelectKey);
            if (meta) {
              // `clear` resets to empty; otherwise merge the patch (selected/anchor).
              if (meta.clear) return emptyState();
              return {
                selected: meta.selected ? new Set(meta.selected) : value.selected,
                anchor: 'anchor' in meta ? meta.anchor : value.anchor,
              };
            }
            // A doc-changing transaction that ISN'T one of our meta edits (e.g. the
            // user typed) drops the multi-selection — stale indices would point at
            // the wrong blocks after an edit. Our own bulk ops set meta.clear, so
            // they reset cleanly and don't trip this.
            if (tr.docChanged && value.selected.size > 0) return emptyState();
            return value;
          },
        },

        props: {
          decorations(state) {
            return buildDecorations(state, this.getState(state));
          },

          handleDOMEvents: {
            // Ctrl/Cmd+Click toggles a block; Shift+Click range-selects from the
            // anchor. We act on mousedown so the gesture wins before the browser
            // moves the text caret. A plain click (no modifier) falls through to
            // normal editing AND clears any existing multi-selection.
            mousedown(view, event) {
              if (event.button !== 0) return false;
              // Don't hijack clicks on the drag gutter / cue handle — that's the
              // drag plugin's gesture.
              if (event.target.closest && event.target.closest('.drag-handle')) return false;

              const ctrl = event.ctrlKey || event.metaKey;
              const shift = event.shiftKey;
              const ps = blockMultiSelectKey.getState(view.state);

              if (!ctrl && !shift) {
                // Plain click clears any multi-selection, then lets PM handle it.
                if (ps && ps.selected.size > 0) setSelection(view, { clear: true });
                return false;
              }

              const idx = blockIndexFromEvent(view, event);
              if (idx < 0) return false;

              event.preventDefault();
              event.stopPropagation();

              if (shift && ps && ps.anchor != null) {
                // Range-select from anchor to here (replaces selection).
                const lo = Math.min(ps.anchor, idx);
                const hi = Math.max(ps.anchor, idx);
                const range = [];
                for (let i = lo; i <= hi; i += 1) range.push(i);
                setSelection(view, { selected: range, anchor: ps.anchor });
              } else {
                // Ctrl/Cmd+Click toggles this block; it becomes the new anchor.
                const next = new Set(ps ? ps.selected : []);
                if (next.has(idx)) next.delete(idx);
                else next.add(idx);
                setSelection(view, { selected: Array.from(next), anchor: idx });
              }
              return true;
            },

            // Escape drops the multi-selection (and lets other Escape handlers run).
            keydown(view, event) {
              if (event.key !== 'Escape') return false;
              const ps = blockMultiSelectKey.getState(view.state);
              if (ps && ps.selected.size > 0) {
                setSelection(view, { clear: true });
                return true;
              }
              return false;
            },
          },
        },
      }),
    ];
  },

  addCommands() {
    return {
      // Replace the current selection with an explicit index list (used rarely).
      setBlockSelection:
        (indices) =>
        ({ view }) => {
          setSelection(view, { selected: indices, anchor: indices.length ? indices[indices.length - 1] : null });
          return true;
        },

      clearBlockSelection:
        () =>
        ({ view }) => {
          setSelection(view, { clear: true });
          return true;
        },

      // Delete every selected block in ONE transaction (descending order so the
      // earlier deletes don't invalidate the later positions).
      deleteSelectedBlocks:
        () =>
        ({ state, dispatch, view }) => {
          const idxs = selectedIndices(state).sort((a, b) => b - a);
          if (!idxs.length) return false;
          const blocks = topLevelBlocks(state.doc);
          let tr = state.tr;
          idxs.forEach((i) => {
            const b = blocks[i];
            if (b) tr = tr.delete(tr.mapping.map(b.start), tr.mapping.map(b.end));
          });
          tr.setMeta(blockMultiSelectKey, { clear: true });
          if (dispatch) dispatch(tr);
          view && view.focus();
          return true;
        },

      // Swap exactly two selected blocks (cue or paragraph — whole node objects).
      swapSelectedBlocks:
        () =>
        ({ state, dispatch, view }) => {
          const idxs = selectedIndices(state);
          if (idxs.length !== 2) return false;
          const [a, b] = idxs; // a < b
          const blocks = topLevelBlocks(state.doc);
          const nodeA = state.doc.child(a);
          const nodeB = state.doc.child(b);
          const blkA = blocks[a];
          const blkB = blocks[b];
          // Replace the LATER block first so the earlier block's positions stay valid.
          let tr = state.tr;
          tr = tr.replaceWith(blkB.start, blkB.end, nodeA);
          tr = tr.replaceWith(blkA.start, blkA.end, nodeB);
          tr.setMeta(blockMultiSelectKey, { clear: true });
          if (dispatch) dispatch(tr);
          view && view.focus();
          return true;
        },

      // Merge 2+ selected PARAGRAPHS' text into the first selected paragraph
      // (in document order), then remove the others. Cues in the selection are
      // ignored. Text is joined with a single space, matching the legacy join.
      joinSelectedParagraphs:
        () =>
        ({ state, dispatch, view, editor }) => {
          const idxs = selectedIndices(state);
          // Only paragraphs participate.
          const paraIdxs = idxs.filter((i) => state.doc.child(i).type.name === 'paragraph');
          if (paraIdxs.length < 2) return false;

          const keepIndex = paraIdxs[0];
          const blocks = topLevelBlocks(state.doc);
          const joinedText = paraIdxs
            .map((i) => (state.doc.child(i).textContent || '').trim())
            .filter((t) => t.length > 0)
            .join(' ');

          const schema = editor.schema;
          const keptAttrs = state.doc.child(keepIndex).attrs;
          const newPara = schema.nodes.paragraph.create(
            keptAttrs,
            joinedText ? schema.text(joinedText) : null
          );

          let tr = state.tr;
          // Remove the OTHER selected paragraphs from last to first (keep positions valid).
          const toRemove = paraIdxs.slice(1).sort((a, b) => b - a);
          toRemove.forEach((i) => {
            const b = blocks[i];
            tr = tr.delete(tr.mapping.map(b.start), tr.mapping.map(b.end));
          });
          // Replace the kept paragraph with the joined one.
          const keepBlk = blocks[keepIndex];
          tr = tr.replaceWith(tr.mapping.map(keepBlk.start), tr.mapping.map(keepBlk.end), newPara);
          tr.setMeta(blockMultiSelectKey, { clear: true });
          if (dispatch) dispatch(tr);
          view && view.focus();
          return true;
        },

      // Toggle bullet on every selected paragraph. Turns the bullet ON if ANY
      // selected paragraph currently lacks it (so a mixed selection unifies to
      // bulleted), otherwise turns it OFF for all.
      toggleBulletOnSelection:
        () =>
        ({ state, dispatch, view }) => {
          const idxs = selectedIndices(state).filter((i) => state.doc.child(i).type.name === 'paragraph');
          if (!idxs.length) return false;
          const anyUnbulleted = idxs.some((i) => !state.doc.child(i).attrs.bullet);
          const nextBullet = anyUnbulleted; // ON if any was off
          const blocks = topLevelBlocks(state.doc);
          let tr = state.tr;
          idxs.forEach((i) => {
            const b = blocks[i];
            const node = state.doc.child(i);
            tr = tr.setNodeMarkup(b.start, undefined, { ...node.attrs, bullet: nextBullet });
          });
          // Keep the selection so the user can keep toggling.
          if (dispatch) dispatch(tr);
          view && view.focus();
          return true;
        },

      // Set the speaker on every selected paragraph.
      setSpeakerOnSelection:
        (speaker) =>
        ({ state, dispatch, view }) => {
          const idxs = selectedIndices(state).filter((i) => state.doc.child(i).type.name === 'paragraph');
          if (!idxs.length || !speaker) return false;
          const blocks = topLevelBlocks(state.doc);
          let tr = state.tr;
          idxs.forEach((i) => {
            const b = blocks[i];
            const node = state.doc.child(i);
            tr = tr.setNodeMarkup(b.start, undefined, { ...node.attrs, speaker });
          });
          if (dispatch) dispatch(tr);
          view && view.focus();
          return true;
        },
    };
  },
});

/**
 * Read the current multi-selection summary from an editor instance — used by the
 * toolbar in ScriptEditor.vue to drive button visibility/labels without poking
 * at plugin internals.
 * @returns {{count:number, paragraphCount:number, indices:number[], anyParagraphUnbulleted:boolean}}
 */
export function readMultiSelection(editor) {
  if (!editor || !editor.state) return { count: 0, paragraphCount: 0, indices: [], anyParagraphUnbulleted: false };
  const ps = blockMultiSelectKey.getState(editor.state);
  if (!ps || ps.selected.size === 0) {
    return { count: 0, paragraphCount: 0, indices: [], anyParagraphUnbulleted: false };
  }
  const childCount = editor.state.doc.childCount;
  const indices = Array.from(ps.selected)
    .filter((i) => i >= 0 && i < childCount)
    .sort((a, b) => a - b);
  const paraIdxs = indices.filter((i) => editor.state.doc.child(i).type.name === 'paragraph');
  const anyParagraphUnbulleted = paraIdxs.some((i) => !editor.state.doc.child(i).attrs.bullet);
  return { count: indices.length, paragraphCount: paraIdxs.length, indices, anyParagraphUnbulleted };
}

export default BlockMultiSelect;
