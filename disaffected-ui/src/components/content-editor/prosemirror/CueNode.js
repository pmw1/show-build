/**
 * TipTap Cue node extension for Show-Build script mode.
 *
 * A cue is an ATOM block widget: the document treats it as a single opaque unit
 * (no editable text inside), drag-reorderable via ProseMirror's own selection.
 * Its attributes mirror the Phase 1 schema:
 *   - cueType : the cue type string (open-ended; unknown types still render)
 *   - fields  : ordered { label -> value } map (the source field bag)
 *   - imgTag  : raw embedded <img> tag, kept distinct from the mediaUrl field
 *
 * Rendering is delegated to CueNodeView.vue via VueNodeViewRenderer, which
 * dispatches on cueType to the existing card components (PlaceholderCueCard /
 * ImageCueCard / cue-types/*). The cards are reused as-is — Phase 2 wraps, it
 * does not rewrite them.
 *
 * NOTE: the SAVE format is owned by src/utils/prosemirror/markdown.js. This node
 * has no DOM parse rule because cues are produced only by that markdown parser;
 * renderHTML here is a fallback for copy/paste and headless serialization.
 */

import { Node, mergeAttributes } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';
import CueNodeView from './CueNodeView.vue';

export const CueNode = Node.create({
  name: 'cue',
  group: 'block',
  atom: true,
  selectable: true,
  draggable: true,

  addAttributes() {
    return {
      cueType: { default: 'NOTE' },
      fields: { default: {} },
      imgTag: { default: '' },
      // Per-cue collapsed UI state. Lives on the node so it survives drag-drop
      // (BlockDragHandle reuses the same node object on move) and is persisted
      // into the saved markdown via the Begin-Cue marker suffix (see markdown.js).
      collapsed: { default: false },
    };
  },

  parseHTML() {
    // Cues are not authored as DOM; only the markdown parser produces them.
    // A data-attribute hook is provided for paste/serialization symmetry.
    return [{ tag: 'div[data-cue]' }];
  },

  renderHTML({ HTMLAttributes, node }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-cue': '',
        'data-cue-type': node.attrs.cueType,
      }),
    ];
  },

  addNodeView() {
    return VueNodeViewRenderer(CueNodeView);
  },

  addCommands() {
    return {
      insertCue:
        (attrs) =>
        ({ commands }) =>
          commands.insertContent({ type: this.name, attrs }),
    };
  },
});

export default CueNode;
