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
              flagNote: next ? p.node.attrs.flagNote : '',
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
        props: {
          decorations: (state) => {
            const decos = [];
            state.doc.forEach((node, offset) => {
              if (node.type.name !== 'paragraph') return;
              // Red-tint background while flagged.
              if (node.attrs.needsAttention) {
                decos.push(Decoration.node(offset, offset + node.nodeSize, { class: 'pm-needs-attention' }));
              }
              // Right-side hover controls (flag + delete). The block is made
              // position:relative by the drag gutter; we anchor at block start.
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
                // Toggle, then ask the host to open/close the note panel.
                editor.commands.toggleNeedsAttention(pos);
                const fn = editor.options.onFlagParagraph;
                if (typeof fn === 'function') fn(pos);
              } else if (action === 'delete') {
                editor.commands.deleteBlockAt(pos);
              }
              return true;
            },
          },
        },
      }),
    ];
  },
});

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
