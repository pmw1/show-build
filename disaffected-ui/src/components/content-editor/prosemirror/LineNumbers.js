/**
 * Per-paragraph line numbers for the Show-Build script editor.
 *
 * One number per PARAGRAPH (cues are skipped) — a CONTENT-based count, so two
 * users looking at the same script see identical numbers regardless of font
 * size or window width (unlike a wrapped-visual-row count, which would vary).
 *
 * The count is CONTINUOUS ACROSS THE WHOLE SHOW: numbering does not reset at
 * the top of each rundown item. ScriptEditor only holds the current item's
 * document, so the host passes in `lineNumberOffset` = the number of paragraphs
 * in all rundown items BEFORE this one. The first paragraph of the current item
 * is therefore `offset + 1`.
 *
 * Implementation: a decoration plugin that draws a widget at the start of each
 * top-level paragraph. The number lives in a left gutter (CSS in this file).
 * Decorations recompute on every doc change, so insert/delete/reorder renumber
 * automatically.
 *
 * The offset is read from `editor.storage.lineNumbers.offset` (set by
 * ScriptEditor from its prop) so it can change without rebuilding the plugin.
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export const lineNumbersPluginKey = new PluginKey('lineNumbers');

function buildDecorations(doc, offset) {
  const decos = [];
  let n = offset; // running paragraph count (0-based until we ++ below)
  doc.descendants((node, pos) => {
    // Only number TOP-LEVEL paragraphs. Returning false stops recursion into
    // a node's children, so we never descend below the top block level.
    if (node.type.name === 'paragraph') {
      n += 1;
      const num = n;
      decos.push(
        Decoration.widget(
          pos + 1,
          () => {
            const el = document.createElement('span');
            el.className = 'pm-line-number';
            el.setAttribute('contenteditable', 'false');
            el.textContent = String(num);
            return el;
          },
          { side: -1, key: `ln-${num}-${pos}` }
        )
      );
      return false; // don't descend into inline content
    }
    // Cues and any other top-level blocks: do not number, do not recurse.
    if (node.isBlock && node.type.name !== 'doc') {
      return false;
    }
    return true;
  });
  return DecorationSet.create(doc, decos);
}

export const LineNumbers = Extension.create({
  name: 'lineNumbers',

  addStorage() {
    return { offset: 0 };
  },

  addProseMirrorPlugins() {
    const extension = this;
    return [
      new Plugin({
        key: lineNumbersPluginKey,
        state: {
          init(_, { doc }) {
            return buildDecorations(doc, extension.storage.offset || 0);
          },
          apply(tr, old) {
            // Rebuild when the doc changed OR when an offset-change meta is sent.
            const offsetMeta = tr.getMeta(lineNumbersPluginKey);
            if (tr.docChanged || offsetMeta !== undefined) {
              return buildDecorations(tr.doc, extension.storage.offset || 0);
            }
            return old;
          },
        },
        props: {
          decorations(state) {
            return this.getState(state);
          },
        },
      }),
    ];
  },
});

export default LineNumbers;
