/**
 * TipTap Paragraph extension for Show-Build script mode.
 *
 * Carries the speaker / bullet / attention-flag attributes on each paragraph and
 * renders them to the exact legacy `<p class="speaker[ bullet]" data-*>` DOM form,
 * so the existing themeColorMap speaker styling and the saved markdown both stay
 * identical. Parsing reads the same attributes back off the DOM.
 *
 * The markdown<->doc conversion in src/utils/prosemirror/markdown.js is the
 * source of truth for the SAVE format; this extension governs the in-editor DOM.
 */

import { Node, mergeAttributes } from '@tiptap/core';

const MODIFIERS = new Set(['bullet']);

export const ScriptParagraph = Node.create({
  name: 'paragraph',
  group: 'block',
  content: 'inline*',
  priority: 1000, // override the default paragraph if StarterKit-like sets are present

  addAttributes() {
    return {
      speaker: {
        default: 'josh',
        parseHTML: (el) => {
          const tokens = (el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
          return tokens.find((t) => !MODIFIERS.has(t)) || 'josh';
        },
        // class is rendered wholesale in renderHTML; don't emit per-attr here
        renderHTML: () => ({}),
      },
      bullet: {
        default: false,
        parseHTML: (el) => (el.getAttribute('class') || '').split(/\s+/).includes('bullet'),
        renderHTML: () => ({}),
      },
      needsAttention: {
        default: false,
        parseHTML: (el) => el.getAttribute('data-needs-attention') === 'true',
        renderHTML: (attrs) => (attrs.needsAttention ? { 'data-needs-attention': 'true' } : {}),
      },
      flagNote: {
        default: '',
        parseHTML: (el) => el.getAttribute('data-flag-note') || '',
        renderHTML: (attrs) => (attrs.flagNote ? { 'data-flag-note': attrs.flagNote } : {}),
      },
    };
  },

  parseHTML() {
    return [{ tag: 'p' }];
  },

  renderHTML({ node, HTMLAttributes }) {
    const speaker = node.attrs.speaker || 'josh';
    const cls = node.attrs.bullet ? `${speaker} bullet` : speaker;
    return ['p', mergeAttributes(HTMLAttributes, { class: cls }), 0];
  },

  addCommands() {
    return {
      setSpeaker:
        (speaker) =>
        ({ commands }) =>
          commands.updateAttributes('paragraph', { speaker }),
      toggleBullet:
        () =>
        ({ commands, editor }) =>
          commands.updateAttributes('paragraph', {
            bullet: !editor.getAttributes('paragraph').bullet,
          }),
    };
  },
});

export default ScriptParagraph;
