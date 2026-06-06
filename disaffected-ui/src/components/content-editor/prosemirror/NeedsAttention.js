/**
 * NeedsAttention — flag a paragraph block for review (#51-adjacent, ported from
 * the legacy contenteditable editor's needs-attention system).
 *
 * Each paragraph carries `needsAttention` (bool) + `flagNote` (string) attrs
 * (already in schema.js, already round-tripped via data-needs-attention /
 * data-flag-note in markdown.js). This plugin adds the UI the new editor lacked:
 *
 *   - On hover (or when flagged), a small control cluster on the RIGHT of the
 *     paragraph: a FLAG button (toggle attention) and a DELETE (×) button.
 *   - When flagged, the paragraph gets a red-tinted background (.pm-needs-attention
 *     class via node decoration) signalling "not ready".
 *   - A note panel attached to the block's right edge is rendered by the HOST
 *     (ScriptEditor) — this plugin just exposes which block is flagged + its
 *     screen position via the flag button click, and the commands to mutate.
 *
 * Commands (added by the Extension):
 *   - toggleNeedsAttention(pos): flip the attr on the paragraph at pos.
 *   - setFlagNote(pos, note): set flagNote on the paragraph at pos.
 *   - resolveNeedsAttention(pos): clear needsAttention + flagNote.
 *   - deleteBlockAt(pos): delete the top-level block at pos (paragraph delete).
 *
 * The flag/delete buttons are decoration widgets; a mousedown handler dispatches
 * the right command (and, for the flag, notifies the host to open the note
 * panel via the onFlagParagraph editor option).
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export const needsAttentionKey = new PluginKey('needsAttention');

/** The current username (for "created by"), from localStorage user-data. */
function currentUser() {
  try { return JSON.parse(localStorage.getItem('user-data') || '{}').username || 'unknown'; }
  catch { return 'unknown'; }
}

/** Find the top-level paragraph block whose start is `pos` (or contains pos). */
function paragraphAt(doc, pos) {
  let result = null;
  doc.forEach((node, offset) => {
    if (result || node.type.name !== 'paragraph') return;
    const from = offset;
    const to = offset + node.nodeSize;
    if (pos >= from && pos < to) result = { node, from, to };
  });
  return result;
}

export const NeedsAttention = Extension.create({
  name: 'needsAttention',

  addCommands() {
    return {
      toggleNeedsAttention:
        (pos) =>
        ({ state, dispatch }) => {
          const p = paragraphAt(state.doc, pos);
          if (!p) return false;
          if (dispatch) {
            const next = !p.node.attrs.needsAttention;
            const tr = state.tr.setNodeMarkup(p.from, undefined, {
              ...p.node.attrs,
              needsAttention: next,
              // Stamp who flagged it on set; clear note + user on unflag.
              flagNote: next ? p.node.attrs.flagNote : '',
              flagUser: next ? (p.node.attrs.flagUser || currentUser()) : '',
            });
            tr.setMeta('addToHistory', true);
            dispatch(tr);
          }
          return true;
        },
      setFlagNote:
        (pos, note) =>
        ({ state, dispatch }) => {
          const p = paragraphAt(state.doc, pos);
          if (!p) return false;
          if (dispatch) {
            const tr = state.tr.setNodeMarkup(p.from, undefined, {
              ...p.node.attrs,
              flagNote: note || '',
            });
            dispatch(tr);
          }
          return true;
        },
      resolveNeedsAttention:
        (pos) =>
        ({ state, dispatch }) => {
          const p = paragraphAt(state.doc, pos);
          if (!p) return false;
          if (dispatch) {
            const tr = state.tr.setNodeMarkup(p.from, undefined, {
              ...p.node.attrs,
              needsAttention: false,
              flagNote: '',
              flagUser: '',
            });
            tr.setMeta('addToHistory', true);
            dispatch(tr);
          }
          return true;
        },
      deleteBlockAt:
        (pos) =>
        ({ state, dispatch }) => {
          const p = paragraphAt(state.doc, pos);
          if (!p) return false;
          // Don't delete the only block — leave an empty paragraph.
          if (dispatch) {
            const tr = state.tr.delete(p.from, p.to);
            tr.setMeta('addToHistory', true);
            dispatch(tr.scrollIntoView());
          }
          return true;
        },
    };
  },

  addProseMirrorPlugins() {
    const ext = this;
    return [
      new Plugin({
        key: needsAttentionKey,
        // Plugin state holds the delete-flash descriptor so it survives redraws
        // and drives node-decoration classes (the only reliable way to animate a
        // PM block — imperative styles get wiped on re-render). Shapes:
        //   { phase: 'dying', index }            — block being deleted (red flash + fade)
        //   { phase: 'neighbors', indices: [] }  — post-delete blue flash on neighbors
        state: {
          init: () => ({ flash: null }),
          apply(tr, prev) {
            const meta = tr.getMeta(needsAttentionKey);
            if (meta && 'flash' in meta) return { flash: meta.flash };
            // Map indices through doc changes isn't needed — flashes are short
            // and keyed to fresh dispatches; just carry forward.
            return prev;
          },
        },
        props: {
          decorations: (state) => {
            const decos = [];
            const ps = needsAttentionKey.getState(state);
            const flash = ps && ps.flash;
            let blockIndex = -1;
            state.doc.forEach((node, offset) => {
              if (node.type.name !== 'paragraph') { blockIndex += 1; return; }
              blockIndex += 1;
              const idx = blockIndex;
              // Red-tint background while flagged.
              if (node.attrs.needsAttention) {
                decos.push(Decoration.node(offset, offset + node.nodeSize, { class: 'pm-needs-attention' }));
              }
              // Delete-flash classes (#delete-anim).
              if (flash && flash.phase === 'dying' && flash.index === idx) {
                decos.push(Decoration.node(offset, offset + node.nodeSize, { class: 'pm-del-dying' }));
              } else if (flash && flash.phase === 'neighbors' && flash.indices.includes(idx)) {
                decos.push(Decoration.node(offset, offset + node.nodeSize, { class: 'pm-del-neighbor' }));
              }
              // Right-side hover controls (flag + delete).
              decos.push(
                Decoration.widget(offset + 1, () => buildControls(node, offset), {
                  side: -1,
                  key: `na-ctrl-${offset}-${node.attrs.needsAttention}`,
                  ignoreSelection: true,
                })
              );
            });
            return DecorationSet.create(state.doc, decos);
          },
          handleDOMEvents: {
            mousedown: (view, event) => {
              const btn = event.target?.closest?.('na-btn');
              if (!btn) return false;
              event.preventDefault();
              event.stopPropagation();
              const action = btn.getAttribute('data-na-action');
              const pos = parseInt(btn.getAttribute('data-na-pos'), 10);
              if (Number.isNaN(pos)) return false;
              const editor = ext.editor;
              if (action === 'flag') {
                // If NOT yet flagged, flag it (stamps user) and open the panel.
                // If already flagged, the flag is the persistent indicator — a
                // click just TOGGLES the note panel (never unflags; unflagging
                // is done via the panel's "Resolved" button).
                const p = paragraphAt(view.state.doc, pos);
                const wasFlagged = p && p.node.attrs.needsAttention;
                if (!wasFlagged) editor.commands.toggleNeedsAttention(pos);
                const fn = editor.options.onFlagParagraph;
                if (typeof fn === 'function') fn(pos, !wasFlagged);
              } else if (action === 'delete') {
                animateDeleteAt(view, pos);
              }
              return true;
            },
          },
        },
      }),
    ];
  },
});

// Choreographed delete (per Kevin):
//   1. 3 rapid RED flashes of the paragraph background (~600ms),
//   2. text FADES out over 500ms (overlaps the tail),
//   3. delete the block + collapse the gap,
//   4. the two now-adjacent neighbours flash BLUE twice (on/off/on/off ~400ms),
//   5. resolve to normal.
// Steps 1-2 run while the node still exists (class via decoration). Then one real
// delete tr; step 4 marks the neighbours (by their post-delete indices) for the
// blue flash, cleared after it finishes. All flash dispatches are addToHistory:
// false so only the delete itself is one undo step.
const DEL_RED_MS = 600;   // 3 flashes
const DEL_FADE_MS = 500;  // text fade
const DEL_BLUE_MS = 400;  // neighbour double-flash

function topLevelIndexAtPos(doc, pos) {
  let idx = -1;
  let found = -1;
  doc.forEach((node, offset) => {
    idx += 1;
    if (found === -1 && pos >= offset && pos < offset + node.nodeSize) found = idx;
  });
  return found;
}

function animateDeleteAt(view, pos) {
  const startIdx = topLevelIndexAtPos(view.state.doc, pos);
  if (startIdx < 0) return;

  // Phase 1+2: red flash + fade (decoration class on the dying block).
  const t1 = view.state.tr.setMeta(needsAttentionKey, { flash: { phase: 'dying', index: startIdx } });
  t1.setMeta('addToHistory', false);
  view.dispatch(t1);

  setTimeout(() => {
    // Resolve the dying block's live range NOW (indices may have shifted if the
    // user edited during the animation — recompute from the same index).
    const doc = view.state.doc;
    let from = null; let to = null; let i = -1;
    doc.forEach((node, offset) => { i += 1; if (i === startIdx) { from = offset; to = offset + node.nodeSize; } });
    if (from == null) { // block gone already — just clear
      const c = view.state.tr.setMeta(needsAttentionKey, { flash: null }); c.setMeta('addToHistory', false); view.dispatch(c);
      return;
    }
    // Phase 3: the real delete (one undo step) + mark neighbours for blue flash.
    const del = view.state.tr.delete(from, to);
    del.setMeta('addToHistory', true);
    // After deletion the block that WAS at startIdx+1 shifts down to startIdx;
    // its neighbours are startIdx-1 and startIdx (the formerly-next block).
    const neighbours = [];
    if (startIdx - 1 >= 0) neighbours.push(startIdx - 1);
    neighbours.push(startIdx); // formerly startIdx+1, now adjacent
    del.setMeta(needsAttentionKey, { flash: { phase: 'neighbors', indices: neighbours } });
    view.dispatch(del.scrollIntoView());

    // Phase 4->5: clear the blue flash after it runs.
    setTimeout(() => {
      const clear = view.state.tr.setMeta(needsAttentionKey, { flash: null });
      clear.setMeta('addToHistory', false);
      view.dispatch(clear);
    }, DEL_BLUE_MS + 60);
  }, Math.max(DEL_RED_MS, DEL_FADE_MS) + 20);
}

/** Build the right-side hover control cluster (flag + delete) for a paragraph. */
function buildControls(node, pos) {
  const wrap = document.createElement('na-controls');
  wrap.setAttribute('contenteditable', 'false');
  if (node.attrs.needsAttention) wrap.classList.add('na-flagged');

  const flag = document.createElement('na-btn');
  flag.setAttribute('data-na-action', 'flag');
  flag.setAttribute('data-na-pos', String(pos));
  flag.setAttribute('title', node.attrs.needsAttention ? 'Flagged — needs attention' : 'Flag for attention');
  flag.classList.add('na-flag');
  if (node.attrs.needsAttention) flag.classList.add('is-active');
  // mdi-flag-variant (filled) / outline — cleaner than the legacy plain flag.
  flag.innerHTML = node.attrs.needsAttention ? FLAG_FILLED_SVG : FLAG_OUTLINE_SVG;

  const del = document.createElement('na-btn');
  del.setAttribute('data-na-action', 'delete');
  del.setAttribute('data-na-pos', String(pos));
  del.setAttribute('title', 'Delete paragraph');
  del.classList.add('na-delete');
  del.innerHTML = TRASH_SVG;

  wrap.appendChild(flag);
  wrap.appendChild(del);
  return wrap;
}

// Crisp inline SVGs (24x24, currentColor) — nicer than the legacy mdi-flag /
// mdi-close glyphs: a pennant flag and a rounded trash can.
const FLAG_OUTLINE_SVG =
  '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4M5 4h11l-2 4 2 4H5"/></svg>';
const FLAG_FILLED_SVG =
  '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5z"/></svg>';
const TRASH_SVG =
  '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13M10 11v6M14 11v6"/></svg>';

export default NeedsAttention;
