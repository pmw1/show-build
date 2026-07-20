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
import { BlockMultiSelect } from './BlockMultiSelect.js';
import { LineNumbers } from './LineNumbers.js';
import { CollapseSummary } from './CollapseSummary.js';
import { SpeakerHeaders } from './SpeakerHeaders.js';
import { NeedsAttention } from './NeedsAttention.js';
import { PasteHandler } from './PasteHandler.js';

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
    // Multi-selection of top-level blocks (Ctrl/Shift-click) + bulk ops
    // (delete / swap / join paragraphs / bullet / set-speaker). Self-contained;
    // reuses the same --dropline-color / --draglight-color accent.
    BlockMultiSelect,
    // Per-paragraph line numbers (continuous across the show via offset).
    LineNumbers,
    // Collapsed-paragraph summaries (first5 … last3), only when collapse on.
    CollapseSummary,
    // Speaker-name header above each speaker-run (top of doc / after a cue /
    // when the speaker changes). Decoration-only — never enters the doc/markdown.
    SpeakerHeaders,
    // Needs-attention flag (port of the legacy system): hover flag + delete on
    // paragraphs, red-tint background while flagged; the note panel is rendered
    // by the host (ScriptEditor) via the onFlagParagraph bridge.
    NeedsAttention,
    // Paste pipeline (port of the legacy editor): cleans Google-Docs HTML on
    // paste and red-flags any paragraph containing a legacy cue token
    // ((TYPE/slug)) with flagNote 'Invalid cue code' so the NeedsAttention
    // Convert button appears. Conversion is user-triggered, not on paste.
    PasteHandler,
    UndoRedo,
  ];
}

export default buildScriptExtensions;
