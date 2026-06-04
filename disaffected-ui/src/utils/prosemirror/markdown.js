/**
 * Markdown <-> ProseMirror document conversion for the Show-Build script editor.
 *
 * This is the production successor to CueParser.parseContent /
 * reconstructContent. It preserves the on-disk markdown contract exactly (the DB
 * script_content format does NOT change) while fixing the three data-loss bugs
 * Phase 0 surfaced in the legacy parser:
 *
 *   BUG 1: bare markdown + a stray <p> tag wiped the script. Fixed by parsing the
 *          WHOLE text region into blocks (no "regex-for-<p>-else-raw" branch).
 *   BUG 2: [MediaURL:] dropped when an <img> was present. Fixed by keeping imgTag
 *          and the mediaUrl field as distinct cue attributes.
 *   BUG 3: a [Field:] immediately before an <img> line was dropped on re-parse.
 *          Fixed by adding \n<img as a valid field terminator.
 *
 * Frontmatter is treated as out-of-band document metadata: stripped on parse,
 * re-prepended on serialize (matching useContentSanitizer + useScriptCore).
 */

import { schema } from './schema.js';

const BEGIN = '<!-- Begin Cue -->';
// A collapsed cue carries a suffix on its Begin marker. The prefix is identical
// to BEGIN, so every existing scan (indexOf(BEGIN), countCues, the legacy
// cueParser) still finds the cue; the suffix is inert text outside any field.
// Default (expanded) cues emit the plain BEGIN, so untouched scripts are
// byte-identical and no cue churns.
const BEGIN_COLLAPSED = '<!-- Begin Cue collapsed -->';
const END = '<!-- End Cue -->';

// Find the next Begin-Cue marker (either the plain or the collapsed variant) at
// or after `from`. Returns { index, markerLen, collapsed } or null. The two
// markers share no usable substring (`<!-- Begin Cue -->` is NOT inside
// `<!-- Begin Cue collapsed -->`), so we scan for both and take the earliest.
function findBegin(body, from) {
  const p = body.indexOf(BEGIN, from);
  const c = body.indexOf(BEGIN_COLLAPSED, from);
  if (p === -1 && c === -1) return null;
  if (c === -1 || (p !== -1 && p <= c)) {
    return { index: p, markerLen: BEGIN.length, collapsed: false };
  }
  return { index: c, markerLen: BEGIN_COLLAPSED.length, collapsed: true };
}

// Field terminator: next field marker, end-cue comment, an <img> line, or EOF.
const FIELD_RE = /\[([^:\n[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|\n\s*<img|$))/g;
const P_RE = /<p(?:\s+class="([^"]*)")?([^>]*)>([\s\S]*?)<\/p>/g;

const MODIFIERS = new Set(['bullet']);

/**
 * Strip unresolved revision markup from paragraph text, keeping the ORIGINAL
 * (reject-on-save semantics — identical to useContentSanitizer.stripRevisionMarkup).
 * `<rev ...>original|replacement</rev>` -> `original` (left of pipe);
 * `<rev ...>kill</rev>` (no pipe) -> `kill` (kept). Used on parse so saved content
 * never carries proposal chrome; live proposals live as ProseMirror revision marks.
 */
function stripRevisionMarkup(text) {
  if (!text || !text.includes('<rev')) return text;
  let r = text.replace(/<rev\s+[^>]*>([\s\S]*?)<\/rev>/gi, (_m, inner) => {
    const pipe = inner.indexOf('|');
    return pipe === -1 ? inner : inner.slice(0, pipe);
  });
  r = r.replace(/<rev-actions>[\s\S]*?<\/rev-actions>/gi, '');
  r = r.replace(/<rev-meta[^>]*>[\s\S]*?<\/rev-meta>/gi, '');
  r = r.replace(/<rev-btn[^>]*>[\s\S]*?<\/rev-btn>/gi, '');
  r = r.replace(/<rev-add[^>]*>[\s\S]*?<\/rev-add>/gi, '');
  r = r.replace(/<rev-kill[^>]*>([\s\S]*?)<\/rev-kill>/gi, '$1');
  r = r.replace(/<rev-block[^>]*>([\s\S]*?)<\/rev-block>/gi, '$1');
  return r;
}

// ---------------------------------------------------------------------------
// Frontmatter (out-of-band)
// ---------------------------------------------------------------------------

const isFmDelimiter = (line) => {
  const t = line.trim();
  return t === '---' || t === '- - -';
};

/** Split a raw string into { frontmatter, body }. frontmatter is '' if none. */
export function splitFrontmatter(content) {
  if (!content) return { frontmatter: '', body: '' };
  const trimmed = content.trimStart();
  if (!(trimmed.startsWith('---') || trimmed.startsWith('- - -'))) {
    return { frontmatter: '', body: content };
  }
  const lines = content.split('\n');
  for (let i = 1; i < lines.length; i++) {
    if (isFmDelimiter(lines[i])) {
      return {
        frontmatter: lines.slice(0, i + 1).join('\n'),
        body: lines.slice(i + 1).join('\n').replace(/^\n+/, ''),
      };
    }
  }
  return { frontmatter: '', body: content };
}

// ---------------------------------------------------------------------------
// markdown -> doc
// ---------------------------------------------------------------------------

function paragraphNode(text, attrs = {}) {
  const a = { speaker: 'josh', bullet: false, needsAttention: false, flagNote: '', ...attrs };
  // Unresolved revision proposals are rejected on parse (keep original text);
  // live proposals are re-created as ProseMirror revision marks in the editor.
  const clean = stripRevisionMarkup(text);
  return schema.node('paragraph', a, clean ? [schema.text(clean)] : []);
}

function parseCueBlock(block, collapsed = false) {
  const fields = {};
  let m;
  FIELD_RE.lastIndex = 0;
  while ((m = FIELD_RE.exec(block)) !== null) {
    fields[m[1].trim()] = m[2].trim();
  }
  const img = block.match(/<img[^>]*>/);
  const cueType = fields.Type || fields.type || 'NOTE';
  return schema.node('cue', { cueType, fields, imgTag: img ? img[0] : '', collapsed });
}

// Emit blocks for a region of plain/HTML text — handles <p> tags AND bare
// markdown in document order, never discarding the bare text (BUG 1 fix).
function emitTextRegion(text, blocks) {
  if (!text.trim()) return;
  let last = 0;
  let m;
  const pushBare = (s) => {
    for (const para of s.split(/\n\s*\n/)) {
      const t = para.trim();
      if (t) blocks.push(paragraphNode(t));
    }
  };
  P_RE.lastIndex = 0;
  while ((m = P_RE.exec(text)) !== null) {
    pushBare(text.slice(last, m.index));
    const cls = (m[1] || '').split(/\s+/).filter(Boolean);
    const speaker = cls.find((c) => !MODIFIERS.has(c)) || 'josh';
    const bullet = cls.includes('bullet');
    const attrs = m[2] || '';
    const needsAttention = /data-needs-attention=["']true["']/.test(attrs);
    const flagNote = (attrs.match(/data-flag-note="([^"]*)"/) || [])[1] || '';
    const inner = m[3].trim();
    if (inner) {
      // A single <p> may itself contain blank-line-separated paragraphs.
      const parts = inner.split(/\n\s*\n/).filter((p) => p.trim());
      for (const part of parts.length ? parts : [inner]) {
        blocks.push(paragraphNode(part.trim(), { speaker, bullet, needsAttention, flagNote }));
      }
    }
    last = P_RE.lastIndex;
  }
  pushBare(text.slice(last));
}

/**
 * Parse a raw script_content string into a ProseMirror doc.
 * @returns {{ doc: Node, frontmatter: string }}
 */
export function markdownToDoc(raw) {
  const { frontmatter, body } = splitFrontmatter(raw || '');
  const blocks = [];
  let idx = 0;

  let m = findBegin(body, idx);
  while (m) {
    emitTextRegion(body.slice(idx, m.index), blocks);
    const e = body.indexOf(END, m.index);
    const next = findBegin(body, m.index + m.markerLen);
    // Malformed cue (no End before the next Begin): treat Begin marker as text,
    // do NOT merge into the next cue (matches CueParser's imperative scan).
    if (e === -1 || (next && next.index < e)) {
      emitTextRegion(body.slice(m.index, m.index + m.markerLen), blocks);
      idx = m.index + m.markerLen;
    } else {
      // The marker after its length is the cue body; the ` collapsed` suffix (if
      // any) is consumed as part of markerLen so it never reaches the field parser.
      blocks.push(parseCueBlock(body.slice(m.index + m.markerLen, e), m.collapsed));
      idx = e + END.length;
    }
    m = findBegin(body, idx);
  }
  emitTextRegion(body.slice(idx), blocks);

  if (blocks.length === 0) blocks.push(paragraphNode(''));
  return { doc: schema.node('doc', null, blocks), frontmatter };
}

// ---------------------------------------------------------------------------
// doc -> markdown
// ---------------------------------------------------------------------------

function serializeParagraph(node) {
  const { speaker, bullet, needsAttention, flagNote } = node.attrs;
  const cls = bullet ? `${speaker || 'josh'} bullet` : speaker || 'josh';
  const na = needsAttention ? ' data-needs-attention="true"' : '';
  const fn = flagNote ? ` data-flag-note="${String(flagNote).replace(/"/g, '&quot;')}"` : '';
  return `<p class="${cls}"${na}${fn}>${node.textContent}</p>`;
}

function serializeCue(node) {
  let s = (node.attrs.collapsed ? BEGIN_COLLAPSED : BEGIN) + '\n';
  for (const [label, value] of Object.entries(node.attrs.fields)) {
    if (value === '' || value == null) continue; // drop empties (harmless; matches legacy)
    s += `[${label}: ${value}]\n`;
  }
  if (node.attrs.imgTag) s += `${node.attrs.imgTag}\n`;
  s += END;
  return s;
}

/**
 * Serialize a ProseMirror doc back to a raw script_content string.
 * @param {Node} doc
 * @param {string} frontmatter - re-prepended verbatim if non-empty
 * @returns {string}
 */
export function docToMarkdown(doc, frontmatter = '') {
  const out = [];
  doc.forEach((node) => {
    if (node.type.name === 'paragraph') out.push(serializeParagraph(node));
    else if (node.type.name === 'cue') out.push(serializeCue(node));
  });
  const body = out.join('\n\n');
  return frontmatter ? `${frontmatter}\n\n${body}` : body;
}

// ---------------------------------------------------------------------------
// Loss assertion — successor to safeEmitScriptContent
// ---------------------------------------------------------------------------

// Match the Begin-Cue marker whether or not it carries the ` collapsed` suffix,
// so the loss tripwire counts collapsed cues correctly (a collapsed cue must not
// read as a "lost" cue).
const countCues = (s) => (s.match(/<!-- Begin Cue(?: collapsed)? -->/g) || []).length;

/**
 * Compare a serialized output against its source and report any structural loss.
 * Returns { ok, cueDelta, hasUndefined, droppedFields } — callers (Phase 4 save
 * path) abort the save when !ok, mirroring the existing tripwire behavior.
 */
export function assertNoLoss(rawInput, serializedOutput) {
  const cueDelta = countCues(serializedOutput) - countCues(rawInput);
  const hasUndefined = /class="undefined"|>undefined<|\[undefined/i.test(serializedOutput);

  // Per-cue field-value preservation: every non-empty field value in the input's
  // cues must survive in the output (order-preserving, per-cue).
  const cueFieldValues = (s) => {
    const result = [];
    let idx = 0;
    let beg = findBegin(s, idx);
    while (beg) {
      const e = s.indexOf(END, beg.index);
      if (e === -1) break;
      const vals = new Set();
      const block = s.slice(beg.index + beg.markerLen, e);
      let m;
      FIELD_RE.lastIndex = 0;
      while ((m = FIELD_RE.exec(block)) !== null) {
        const v = m[2].trim().replace(/^["']|["']$/g, '');
        if (v) vals.add(v.replace(/\s+/g, ' '));
      }
      result.push(vals);
      idx = e + END.length;
      beg = findBegin(s, idx);
    }
    return result;
  };

  const inCues = cueFieldValues(rawInput);
  const outCues = cueFieldValues(serializedOutput);
  const droppedFields = [];
  inCues.forEach((vals, i) => {
    const out = outCues[i] || new Set();
    for (const v of vals) if (!out.has(v)) droppedFields.push({ cueIndex: i, value: v.slice(0, 60) });
  });

  return {
    ok: cueDelta >= 0 && !hasUndefined && droppedFields.length === 0,
    cueDelta,
    hasUndefined,
    droppedFields,
  };
}
