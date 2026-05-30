/**
 * TipTap inline mark for revision proposals (replaces the legacy inline-<rev>-HTML
 * approach, see useContentSanitizer.stripRevisionMarkup).
 *
 * A revision proposal wraps a span of text the user proposes to cut or replace.
 * In the legacy system this was raw HTML `<rev user="" ts="">original|replacement</rev>`
 * that had to be regex-stripped on save (unresolved == rejected, keep original).
 *
 * As a ProseMirror mark the proposal is structured data, not stringly-typed HTML:
 *   attrs { user, ts, replacement }   ('' replacement == pure cut/kill proposal)
 *
 * SAVE behavior (Phase 4 serializer): unresolved revision marks are dropped and the
 * ORIGINAL marked text is kept — identical "reject-on-save" semantics, but with no
 * fragile HTML stripping. Accepting a proposal applies it as a normal edit and
 * removes the mark; rejecting removes the mark and keeps the original text.
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export const RevisionMark = Mark.create({
  name: 'revision',
  inclusive: false,
  excludes: '', // proposals may overlap other marks

  addAttributes() {
    return {
      user: { default: '' },
      ts: { default: '' },
      replacement: { default: '' }, // proposed replacement; '' = cut-only proposal
    };
  },

  parseHTML() {
    return [{ tag: 'rev' }];
  },

  renderHTML({ HTMLAttributes }) {
    // In-editor DOM chrome only; never serialized to the saved markdown (the
    // Phase 4 doc->markdown serializer omits revision marks, keeping originals).
    return [
      'rev',
      mergeAttributes(HTMLAttributes, { class: 'pm-revision' }),
      0,
    ];
  },

  addCommands() {
    return {
      // Alt+. — propose an addition/replacement for the current selection.
      proposeRevision:
        ({ user = '', ts = '', replacement = '' } = {}) =>
        ({ commands }) =>
          commands.setMark(this.name, { user, ts, replacement }),
      // Alt+/ — propose cutting the current selection (replacement stays '').
      proposeCut:
        ({ user = '', ts = '' } = {}) =>
        ({ commands }) =>
          commands.setMark(this.name, { user, ts, replacement: '' }),
      // Accept: drop the mark, keep current text (the proposal was already applied
      // as the visible text when accepted by the UI).
      acceptRevision:
        () =>
        ({ commands }) =>
          commands.unsetMark(this.name),
      // Reject: drop the mark, keep original (UI restores original text first).
      rejectRevision:
        () =>
        ({ commands }) =>
          commands.unsetMark(this.name),
    };
  },

  addKeyboardShortcuts() {
    // Match the legacy bindings (keyboardShortcuts.js): Alt+/ cut, Alt+. add.
    return {
      'Alt-/': () => this.editor.commands.proposeCut(),
      'Alt-.': () => this.editor.commands.proposeRevision(),
    };
  },
});

export default RevisionMark;
