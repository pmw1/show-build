// Phase 0 — ProseMirror schema + markdown<->doc round-trip PROOF.
//
// Schema:  doc -> (paragraph | cue)+    (flat, ordinal, no nesting — matches reality)
//   paragraph: attrs { speaker, bullet, needsAttention, flagNote }, inline text
//   cue:       atom block, attrs { cueType, fields: {label->value}, imgTag }
//
// The parser parses the WHOLE markdown string into a block sequence (fixing BUG 1:
// no "regex-for-<p>-else-raw" branch that discards bare text). The serializer emits
// the legacy markdown form (<p class> + <!-- Begin/End Cue -->) so the DB contract
// is preserved, keeping mediaUrl distinct from the embedded <img> (fixing BUG 2).

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
      },
    },
    cue: {
      group: 'block',
      atom: true,
      selectable: true,
      attrs: {
        cueType: { default: 'NOTE' },
        fields: { default: {} }, // ordered label->value map (open-ended)
        imgTag: { default: '' }, // raw <img ...> if present, kept distinct from mediaUrl
      },
    },
  },
  marks: {},
});

const BEGIN = '<!-- Begin Cue -->';
const END = '<!-- End Cue -->';

// ---- markdown -> doc -------------------------------------------------------
export function markdownToDoc(md) {
  const blocks = [];
  let idx = 0;

  const emitTextRegion = (text) => {
    if (!text.trim()) return;
    // Parse the WHOLE region into paragraphs. Handle BOTH <p> tags AND bare
    // markdown in the same region (BUG 1 fix): split into <p>...</p> tokens and
    // the bare text between/around them, in document order.
    const pRe = /<p(?:\s+class="([^"]*)")?([^>]*)>([\s\S]*?)<\/p>/g;
    let last = 0;
    let m;
    const pushBare = (s) => {
      for (const para of s.split(/\n\s*\n/)) {
        const t = para.trim();
        if (t) blocks.push(paragraphNode(t, {}));
      }
    };
    while ((m = pRe.exec(text)) !== null) {
      pushBare(text.slice(last, m.index)); // bare text BEFORE this <p> — never discarded
      const cls = (m[1] || '').split(/\s+/).filter(Boolean);
      const speaker = cls.find((c) => c !== 'bullet') || 'josh';
      const bullet = cls.includes('bullet');
      const attrs = m[2] || '';
      const needsAttention = /data-needs-attention=["']true["']/.test(attrs);
      const flagNote = (attrs.match(/data-flag-note="([^"]*)"/) || [])[1] || '';
      const inner = m[3].trim();
      if (inner) blocks.push(paragraphNode(inner, { speaker, bullet, needsAttention, flagNote }));
      last = pRe.lastIndex;
    }
    pushBare(text.slice(last)); // bare text AFTER the last <p>
  };

  while (true) {
    const b = md.indexOf(BEGIN, idx);
    if (b === -1) {
      emitTextRegion(md.slice(idx));
      break;
    }
    emitTextRegion(md.slice(idx, b));
    const e = md.indexOf(END, b);
    const nextB = md.indexOf(BEGIN, b + BEGIN.length);
    if (e === -1 || (nextB !== -1 && nextB < e)) {
      // malformed cue: treat the Begin marker as text, continue (don't merge cues)
      emitTextRegion(md.slice(b, b + BEGIN.length));
      idx = b + BEGIN.length;
      continue;
    }
    blocks.push(cueNode(md.slice(b + BEGIN.length, e)));
    idx = e + END.length;
  }

  if (blocks.length === 0) blocks.push(paragraphNode('', {}));
  return schema.node('doc', null, blocks);
}

function paragraphNode(text, { speaker = 'josh', bullet = false, needsAttention = false, flagNote = '' }) {
  return schema.node('paragraph', { speaker, bullet, needsAttention, flagNote }, text ? [schema.text(text)] : []);
}

function cueNode(block) {
  const fields = {}; // ordered insertion preserves source order
  // Terminator lookahead must accept the next field marker (\n[), the end-cue
  // comment (\n<!--), an embedded <img> on the next line (\n<img), OR end of input.
  // Without the \n<img alternative, a [Field:] immediately followed by an <img>
  // line fails to match on re-parse — silently dropping that field (non-idempotent).
  const fieldRe = /\[([^:\n[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|\n\s*<img|$))/g;
  let m;
  while ((m = fieldRe.exec(block)) !== null) {
    fields[m[1].trim()] = m[2].trim();
  }
  const img = block.match(/<img[^>]*>/);
  const cueType = fields.Type || fields.type || 'NOTE';
  return schema.node('cue', { cueType, fields, imgTag: img ? img[0] : '' });
}

// ---- doc -> markdown -------------------------------------------------------
export function docToMarkdown(doc) {
  const out = [];
  doc.forEach((node) => {
    if (node.type.name === 'paragraph') {
      const a = node.attrs;
      const cls = a.bullet ? `${a.speaker} bullet` : a.speaker;
      const na = a.needsAttention ? ' data-needs-attention="true"' : '';
      const fn = a.flagNote ? ` data-flag-note="${a.flagNote.replace(/"/g, '&quot;')}"` : '';
      out.push(`<p class="${cls}"${na}${fn}>${node.textContent}</p>`);
    } else if (node.type.name === 'cue') {
      out.push(serializeCue(node));
    }
  });
  return out.join('\n\n');
}

function serializeCue(node) {
  let s = BEGIN + '\n';
  // preserve source field order exactly (fixes field-reorder churn AND keeps mediaUrl)
  for (const [label, value] of Object.entries(node.attrs.fields)) {
    if (value === '') continue; // drop empties (matches legacy; harmless)
    s += `[${label}: ${value}]\n`;
  }
  if (node.attrs.imgTag) s += `${node.attrs.imgTag}\n`;
  s += END;
  return s;
}
