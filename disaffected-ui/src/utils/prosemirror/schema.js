/**
 * ProseMirror schema for the Show-Build script editor.
 *
 * The document is a FLAT, ordinal sequence of two block kinds — paragraphs and
 * cues — that interleave but never nest. This mirrors the real markdown model
 * (see docs/SCRIPT_EDITOR_MIGRATION_PLAN.md §2a):
 *
 *     doc -> (paragraph | cue)+
 *
 * paragraph: inline text, attrs { speaker, bullet, needsAttention, flagNote }
 * cue:       atom block widget, attrs { cueType, fields (ordered label->value),
 *            imgTag (raw <img> kept distinct from the mediaUrl field) }
 *
 * The cue node is intentionally an OPEN-ENDED key/value bag rather than one node
 * type per cue type: the cue-type list is open-ended in the data, fields vary
 * loosely, and unknown types must still round-trip. The Vue NodeView (Phase 2)
 * dispatches on attrs.cueType to render the right card.
 */

import { Schema } from 'prosemirror-model';

export const schema = new Schema({
  nodes: {
    doc: { content: 'block+' },

    text: { group: 'inline' },

    paragraph: {
      group: 'block',
      content: 'inline*',
      attrs: {
        speaker: { default: 'josh' },
        bullet: { default: false },
        needsAttention: { default: false },
        flagNote: { default: '' },
        flagUser: { default: '' },
      },
      parseDOM: [{ tag: 'p' }],
      toDOM(node) {
        const { speaker, bullet, needsAttention, flagNote, flagUser } = node.attrs;
        const cls = bullet ? `${speaker} bullet` : speaker;
        const attrs = { class: cls };
        if (needsAttention) attrs['data-needs-attention'] = 'true';
        if (flagNote) attrs['data-flag-note'] = flagNote;
        if (flagUser) attrs['data-flag-user'] = flagUser;
        return ['p', attrs, 0];
      },
    },

    cue: {
      group: 'block',
      atom: true,
      selectable: true,
      draggable: true,
      attrs: {
        cueType: { default: 'NOTE' },
        // Ordered map of original field label -> value. Insertion order is the
        // source order and is preserved on serialize (no churny reordering).
        fields: { default: {} },
        // Raw embedded <img ...> tag, kept verbatim and distinct from the
        // mediaUrl field so neither absorbs the other (Phase 0 BUG 2 fix).
        imgTag: { default: '' },
        // Per-cue collapsed UI state. Persisted via the Begin-Cue marker suffix
        // in markdown.js; survives drag-drop (the node object is reused on move).
        collapsed: { default: false },
      },
      // Cues have no DOM parse rule — they are produced only by the markdown
      // parser. The NodeView (Phase 2) owns their rendering.
    },
  },
  marks: {
    // Revision proposal (#51). A span of text proposed to be cut or replaced.
    // attrs { user, ts, replacement }: replacement '' = pure cut/kill proposal,
    // non-empty = replace the marked (kill) text with `replacement`. MUST match
    // the TipTap RevisionMark (prosemirror/RevisionMark.js) so the editor schema
    // and this round-trip schema agree. Unresolved revisions round-trip through
    // markdown as <rev user ts>kill|add</rev> (markdown.js serialize/parse).
    revision: {
      attrs: {
        user: { default: '' },
        ts: { default: '' },
        replacement: { default: '' },
      },
      inclusive: false,
      parseDOM: [{ tag: 'rev' }],
      toDOM(mark) {
        const { user, ts, replacement } = mark.attrs;
        return ['rev', { class: 'pm-revision', 'data-user': user, 'data-ts': ts, 'data-replacement': replacement }, 0];
      },
    },
  },
});

/** Canonical speaker list (from CueParser.getSpeakerOptions). */
export const SPEAKERS = ['josh', 'scott', 'asian-scott', 'guest', 'caller', 'announcer', 'narrator', 'host'];
