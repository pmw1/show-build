/**
 * Revision proposals for the Show-Build script editor (#51).
 *
 * A revision proposal wraps a span of text the user proposes to cut or replace.
 * Stored as a ProseMirror mark, attrs { user, ts, replacement }:
 *   - replacement '' .......... pure CUT proposal (delete the marked text)
 *   - replacement non-empty ... REPLACE the marked (kill) text with `replacement`
 *
 * Round-trips through markdown as <rev user ts>kill|add</rev> (utils/prosemirror/
 * markdown.js), so an UNRESOLVED proposal survives save/reload until accepted or
 * rejected.
 *
 * UI: a plugin paints, after each revision span, a small inline chrome — the
 * proposed replacement (green) when present + a user·time meta + ✓ (accept) /
 * ✗ (reject) buttons. Ports the legacy contenteditable <rev-block> look.
 *
 * Resolve:
 *   - ACCEPT: replace the whole marked range with `replacement` (or delete it for
 *     a cut), in ONE undoable transaction; the mark goes away with the old text.
 *   - REJECT: just remove the mark over the range, keeping the original text.
 */

import { Mark, mergeAttributes } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export const revisionPluginKey = new PluginKey('revisionChrome');

/** user·relativeTime label (mirrors legacy _relativeTime). */
function relativeTime(ts) {
  if (!ts) return '';
  const t = Date.parse(ts);
  if (Number.isNaN(t)) return '';
  const mins = Math.floor((Date.now() - t) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

/**
 * Find the contiguous range of the revision mark that covers position `pos`
 * (or the mark just before pos, so a collapsed cursor at the span's end still
 * resolves it). Returns { from, to, mark } or null.
 */
function revisionRangeAt(doc, pos) {
  const $pos = doc.resolve(pos);
  const parent = $pos.parent;
  if (!parent || !parent.isTextblock) return null;
  const start = $pos.start();

  // Find the revision mark whose run contains pos (or ends exactly at pos).
  let target = null;
  parent.forEach((child, offset) => {
    if (target || !child.isText) return;
    const m = child.marks.find((mk) => mk.type.name === 'revision');
    if (!m) return;
    const childFrom = start + offset;
    const childTo = childFrom + child.nodeSize;
    if (pos >= childFrom && pos <= childTo) target = m;
  });
  if (!target) return null;

  const sameProposal = (mk) =>
    mk.type.name === 'revision' &&
    mk.attrs.user === target.attrs.user &&
    mk.attrs.ts === target.attrs.ts &&
    mk.attrs.replacement === target.attrs.replacement;

  // Collect contiguous runs of the same proposal; return the one covering pos.
  const ranges = [];
  let runStart = null;
  let prevTo = null;
  parent.forEach((child, offset) => {
    const childFrom = start + offset;
    const childTo = childFrom + child.nodeSize;
    const has = child.isText && child.marks.some(sameProposal);
    if (has) {
      if (runStart == null) runStart = childFrom;
      prevTo = childTo;
    } else if (runStart != null) {
      ranges.push([runStart, prevTo]); runStart = null;
    }
  });
  if (runStart != null) ranges.push([runStart, prevTo]);
  const hit = ranges.find(([a, b]) => pos >= a && pos <= b);
  return hit ? { from: hit[0], to: hit[1], mark: target } : null;
}

export const RevisionMark = Mark.create({
  name: 'revision',
  inclusive: false,
  excludes: '',

  addAttributes() {
    return {
      user: { default: '' },
      ts: { default: '' },
      replacement: { default: '' },
    };
  },

  parseHTML() {
    return [{ tag: 'rev' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ['rev', mergeAttributes(HTMLAttributes, { class: 'pm-revision' }), 0];
  },

  addCommands() {
    return {
      // Propose a replacement over the current selection (Alt+.). The host opens
      // the inline popup and re-issues this with the typed replacement.
      proposeRevision:
        ({ user = '', ts = '', replacement = '' } = {}) =>
        ({ commands }) =>
          commands.setMark(this.name, { user, ts, replacement }),
      // Propose cutting the current selection (Alt+/), replacement stays ''.
      proposeCut:
        ({ user = '', ts = '' } = {}) =>
        ({ commands }) =>
          commands.setMark(this.name, { user, ts, replacement: '' }),
      // Set/replace the replacement text on the proposal covering `pos` without
      // changing the marked (kill) text — used when the popup commits.
      setRevisionReplacement:
        (pos, replacement) =>
        ({ state, dispatch }) => {
          const range = revisionRangeAt(state.doc, pos);
          if (!range) return false;
          const { from, to, mark } = range;
          if (dispatch) {
            const tr = state.tr;
            tr.removeMark(from, to, state.schema.marks.revision);
            tr.addMark(from, to, state.schema.marks.revision.create({
              user: mark.attrs.user, ts: mark.attrs.ts, replacement,
            }));
            dispatch(tr.scrollIntoView());
          }
          return true;
        },
      // ACCEPT the proposal covering `pos`: replace marked text with replacement
      // (delete for a cut) in one undoable tr.
      acceptRevisionAt:
        (pos) =>
        ({ state, dispatch }) => {
          const range = revisionRangeAt(state.doc, pos);
          if (!range) return false;
          const { from, to, mark } = range;
          if (dispatch) {
            const tr = state.tr;
            const repl = mark.attrs.replacement || '';
            if (repl) tr.replaceWith(from, to, state.schema.text(repl));
            else tr.delete(from, to);
            tr.setMeta('addToHistory', true);
            dispatch(tr.scrollIntoView());
          }
          return true;
        },
      // REJECT the proposal covering `pos`: keep original, drop the mark.
      rejectRevisionAt:
        (pos) =>
        ({ state, dispatch }) => {
          const range = revisionRangeAt(state.doc, pos);
          if (!range) return false;
          const { from, to } = range;
          if (dispatch) {
            const tr = state.tr;
            tr.removeMark(from, to, state.schema.marks.revision);
            tr.setMeta('addToHistory', true);
            dispatch(tr.scrollIntoView());
          }
          return true;
        },
    };
  },

  addKeyboardShortcuts() {
    // Alt+/ (revise/cut) and Alt+. (add) hand off to the host (ScriptEditor) via
    // the editor.options.onProposeRevision bridge, which marks the selection and
    // opens the inline replacement popup. Falls back to a bare mark if no bridge.
    const bridge = (mode) => {
      const fn = this.editor?.options?.onProposeRevision;
      if (typeof fn === 'function') { fn(mode); return true; }
      // Fallback: mark selection (revise) so something visible happens.
      if (mode === 'revise') return this.editor.commands.proposeCut();
      return false;
    };
    return {
      'Alt-/': () => bridge('revise'),
      'Alt-.': () => bridge('add'),
    };
  },

  // Inline chrome: a widget after each revision run showing the proposed add
  // (green), a user·time meta, and ✓/✗ buttons. Clicking dispatches the
  // accept/reject command at the run's position.
  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: revisionPluginKey,
        props: {
          decorations: (state) => {
            const decos = [];
            const { doc } = state;
            doc.descendants((node, pos) => {
              if (node.type.name !== 'paragraph') return;
              const start = pos + 1;
              const seen = new Set();
              node.forEach((child, offset) => {
                if (!child.isText) return;
                const m = child.marks.find((mk) => mk.type.name === 'revision');
                if (!m) return;
                const runFrom = start + offset;
                const runTo = runFrom + child.nodeSize;
                // De-dupe: only add chrome once per contiguous proposal run end.
                const key = `${m.attrs.user}|${m.attrs.ts}|${m.attrs.replacement}|${runTo}`;
                if (seen.has(key)) return;
                seen.add(key);
                decos.push(
                  Decoration.widget(runTo, () => buildRevChrome(m, runFrom), {
                    side: 1,
                    key,
                    ignoreSelection: true,
                  })
                );
              });
            });
            return DecorationSet.create(doc, decos);
          },
          // Click handler for the ✓/✗ buttons in the chrome. Resolves the
          // revision run at the button's recorded position and applies the
          // accept/reject transaction directly on the view (one undo step).
          handleDOMEvents: {
            mousedown: (view, event) => {
              const btn = event.target?.closest?.('rev-btn');
              if (!btn) return false;
              event.preventDefault();
              event.stopPropagation();
              const action = btn.getAttribute('data-rev-action');
              const pos = parseInt(btn.getAttribute('data-rev-pos'), 10);
              if (Number.isNaN(pos)) return false;
              const { state } = view;
              const range = revisionRangeAt(state.doc, pos);
              if (!range) return true;
              const { from, to, mark } = range;
              const tr = state.tr;
              if (action === 'accept') {
                const repl = mark.attrs.replacement || '';
                if (repl) tr.replaceWith(from, to, state.schema.text(repl));
                else tr.delete(from, to);
              } else {
                tr.removeMark(from, to, state.schema.marks.revision);
              }
              tr.setMeta('addToHistory', true);
              view.dispatch(tr.scrollIntoView());
              view.focus();
              return true;
            },
          },
        },
      }),
    ];
  },
});

/** Build the inline chrome DOM for one revision run. */
function buildRevChrome(mark, runFrom) {
  const wrap = document.createElement('rev-actions');
  wrap.setAttribute('contenteditable', 'false');
  const repl = mark.attrs.replacement || '';
  if (repl) {
    const add = document.createElement('rev-add');
    add.textContent = repl;
    wrap.appendChild(add);
  }
  const meta = document.createElement('rev-meta');
  const label = [mark.attrs.user || 'unknown', relativeTime(mark.attrs.ts)].filter(Boolean).join(' · ');
  meta.textContent = label;
  wrap.appendChild(meta);
  const accept = document.createElement('rev-btn');
  accept.setAttribute('data-rev-action', 'accept');
  accept.setAttribute('data-rev-pos', String(runFrom));
  accept.setAttribute('title', 'Accept revision');
  accept.innerHTML = '&#10003;';
  wrap.appendChild(accept);
  const reject = document.createElement('rev-btn');
  reject.setAttribute('data-rev-action', 'reject');
  reject.setAttribute('data-rev-pos', String(runFrom));
  reject.setAttribute('title', 'Reject revision');
  reject.innerHTML = '&#10007;';
  wrap.appendChild(reject);
  return wrap;
}

export default RevisionMark;
