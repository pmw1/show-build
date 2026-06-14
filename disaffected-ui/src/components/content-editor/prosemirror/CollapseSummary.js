/**
 * Collapsed-paragraph summaries for the Show-Build script editor.
 *
 * When whole-editor collapse mode is ON, each paragraph is shown as a single
 * line:  "first five words …"   (left)   …   "… last three words"  (right).
 * The real paragraph text is hidden (CSS) and these two summaries are drawn as
 * node-decoration attributes that CSS renders via ::before / ::after.
 *
 * Collapse state is read from editor.storage.collapse.on (set by ScriptEditor
 * from its `collapsed` prop). The decoration set rebuilds when the doc changes
 * or when a 'collapseToggle' meta is dispatched.
 */

import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export const collapseSummaryPluginKey = new PluginKey('collapseSummary');

const FIRST_WORDS = 5;
const LAST_WORDS = 3;

function summarize(text) {
  const words = (text || '').trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return { left: '(empty)', right: '' };
  if (words.length <= FIRST_WORDS) {
    // Short paragraph: show it all on the left, nothing on the right.
    return { left: words.join(' '), right: '' };
  }
  const left = words.slice(0, FIRST_WORDS).join(' ') + ' …';
  // Avoid the left and right halves overlapping for medium-length paragraphs.
  const remaining = words.length - FIRST_WORDS;
  const right = remaining > 0 ? '… ' + words.slice(-Math.min(LAST_WORDS, remaining)).join(' ') : '';
  return { left, right };
}

function buildDecorations(doc, on) {
  if (!on) return DecorationSet.empty;
  const decos = [];
  doc.descendants((node, pos) => {
    if (node.type.name === 'paragraph') {
      const { left, right } = summarize(node.textContent);
      // Node decoration: add the class that hides the real text + lays out the
      // row (flex). The summary itself is drawn by WIDGET decorations below
      // (real DOM spans with their own color) rather than CSS attr(), which
      // some ProseMirror builds strip for non-standard data-* attributes —
      // that produced the "white on white" (hidden text, empty pseudo) bug.
      // Layout is set INLINE on the <p> (not just via the class) because some
      // paragraphs carry an inherited speaker text-align (centered/right) and a
      // 34px drag gutter; scoped CSS wasn't reliably winning, so centered rows
      // appeared indented. Inline style can't be defeated by selector reach or
      // specificity. font-size:0 hides the paragraph's own bare text; the widget
      // spans (own font-size/color) carry the visible summary.
      // The <p> is a fixed-height positioning context. We hide its real text
      // (font-size:0) and ABSOLUTELY position the two summaries + the line
      // number into it. Absolute positioning removes ALL dependence on flex,
      // inherited text-align, or the 34px drag gutter — so every row's left
      // summary starts at exactly the same x (no more inconsistent indent).
      decos.push(
        Decoration.node(pos, pos + node.nodeSize, {
          class: 'pm-collapsed-para',
          // height must be an ABSOLUTE unit — `1.4em` of a font-size:0 element
          // is 0, which collapsed the row and clipped the absolute summaries
          // (overflow:hidden), making all lines disappear.
          // margin-bottom in PIXELS (em would be 0 at font-size:0) — one blank
          // line (~24px) of space between collapsed rows.
          style: 'position:relative;display:block;'
            + 'white-space:nowrap;overflow:visible;font-size:0;'
            + 'background:transparent;margin-bottom:24px;'
            + 'height:24px;min-height:24px;padding:0;text-indent:0;',
        })
      );
      // Left summary "first five words …" — absolute at x=64px: leaves room for
      // the line number (0–26px) THEN the drag grabber (28–62px) to its left.
      decos.push(
        Decoration.widget(pos + 1, () => {
          const el = document.createElement('span');
          el.className = 'pm-collapse-left';
          el.setAttribute('contenteditable', 'false');
          el.textContent = left;
          el.style.cssText =
            'position:absolute;left:64px;top:2px;max-width:55%;'
            + 'color:#000;font-size:var(--editor-script-font-size,16px);'
            + 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left;';
          return el;
        }, { side: -1, key: `cl-${pos}-${left}` })
      );
      // Right summary "… last three words" — absolute at the right edge.
      if (right) {
        decos.push(
          Decoration.widget(pos + 1, () => {
            const el = document.createElement('span');
            el.className = 'pm-collapse-right';
            el.setAttribute('contenteditable', 'false');
            el.textContent = right;
            el.style.cssText =
              'position:absolute;right:0;top:2px;'
              + 'color:#000;font-size:var(--editor-script-font-size,16px);'
              + 'white-space:nowrap;text-align:right;';
            return el;
          }, { side: -1, key: `cr-${pos}-${right}` })
        );
      }
      return false;
    }
    return false; // only top-level paragraphs
  });
  return DecorationSet.create(doc, decos);
}

export const CollapseSummary = Extension.create({
  name: 'collapseSummary',

  addStorage() {
    return {};
  },

  addProseMirrorPlugins() {
    const extension = this;
    // Collapse state is authoritatively carried on the 'collapseToggle' meta
    // (dispatched by ScriptEditor). We cache it in plugin state so doc edits
    // while collapsed keep rebuilding correctly. Fallback to editor storage.
    return [
      new Plugin({
        key: collapseSummaryPluginKey,
        state: {
          init(_, { doc }) {
            const on = !!(extension.editor?.storage?.collapse?.on);
            return { on, decos: buildDecorations(doc, on) };
          },
          apply(tr, old) {
            const toggle = tr.getMeta('collapseToggle');
            const on = toggle !== undefined ? !!toggle : old.on;
            if (tr.docChanged || toggle !== undefined) {
              return { on, decos: buildDecorations(tr.doc, on) };
            }
            return old;
          },
        },
        props: {
          decorations(state) {
            return collapseSummaryPluginKey.getState(state)?.decos || null;
          },
        },
      }),
    ];
  },
});

export default CollapseSummary;
