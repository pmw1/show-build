/**
 * The Show-Build script editor's TipTap extension set, assembled in one place so
 * ScriptEditor.vue (Phase 4) imports a single list.
 *
 * Intentionally minimal: only Document, Text, our ScriptParagraph, the CueNode
 * atom, and the RevisionMark. We do NOT use StarterKit — script mode is a flat
 * paragraph/cue document with no headings, lists, blockquotes, or code blocks at
 * the ProseMirror level (those would change the document model the markdown layer
 * round-trips). History (undo/redo) is added here because the editor needs it and
 * it does not alter the schema.
 */

import Document from '@tiptap/extension-document';
import Text from '@tiptap/extension-text';
// TipTap v3 ships undo/redo as UndoRedo in the @tiptap/extensions bundle
// (the v2 `History` extension was renamed).
import { UndoRedo } from '@tiptap/extensions';

import { ScriptParagraph } from './ScriptParagraph.js';
import { CueNode } from './CueNode.js';
import { RevisionMark } from './RevisionMark.js';
import { SlashCommand } from './SlashCommand.js';
import { BlockDragHandle } from './BlockDragHandle.js';
import { LineNumbers } from './LineNumbers.js';
import { CollapseSummary } from './CollapseSummary.js';

/**
 * @param {object} [opts]
 * @param {string} [opts.currentUser] - stamped onto revision proposals.
 * @param {(cueType: string) => void} [opts.onSelectCue] - called when the slash
 *   menu picks a cue type; the host launches the matching cue modal.
 * @returns {Array} TipTap extensions for the script editor.
 */
export function buildScriptExtensions(opts = {}) {
  return [
    Document,
    Text,
    ScriptParagraph,
    CueNode,
    RevisionMark,
    SlashCommand.configure({ onSelectCue: opts.onSelectCue || null }),
    // Drag-and-drop reordering of top-level blocks (left-gutter grab handle,
    // live displacement, single-transaction move). Self-contained; reuses the
    // legacy --dropline-color / --draglight-color CSS vars.
    BlockDragHandle,
    // Per-paragraph line numbers (continuous across the show via offset).
    LineNumbers,
    // Collapsed-paragraph summaries (first5 … last3), only when collapse on.
    CollapseSummary,
    UndoRedo,
  ];
}

export default buildScriptExtensions;
