/**
 * Phase 5 parity gate: prove the new ProseMirror round-trip produces output that
 * is SEMANTICALLY EQUIVALENT to the legacy CueParser round-trip on real content.
 *
 * "Semantically equivalent" (not byte-identical) means: same set of cues with the
 * same field values, same paragraph texts, same speakers. The two serializers
 * differ cosmetically (field label casing, field order, <p> wrapping) — and the
 * NEW one is deliberately BETTER (it fixes the legacy data-loss bugs), so on the
 * items where legacy loses data, parity is expected to DIVERGE in the new
 * editor's favor. This test asserts: the new editor never loses anything the
 * legacy editor kept (new ⊇ legacy), which is the real bar for flipping the flag.
 *
 * Run: npx jest tests/unit/editor_parity.spec.js
 */

/* global describe, test, expect */
import fs from 'fs';
import path from 'path';
import { CueParser } from '@/utils/cueParser.js';
import { markdownToDoc, docToMarkdown } from '@/utils/prosemirror/markdown.js';

// --- round-trips ------------------------------------------------------------
const legacyRoundTrip = (raw) => {
  const segs = CueParser.parseContent(raw).map((s) =>
    s.type === 'cue' ? { ...s, data: CueParser.formatForCard(s.data) } : s
  );
  return CueParser.reconstructContent(segs);
};
const pmRoundTrip = (raw) => {
  const { doc, frontmatter } = markdownToDoc(raw);
  return docToMarkdown(doc, frontmatter);
};

// --- semantic model (per-cue field values + paragraph texts) ----------------
const BEGIN = '<!-- Begin Cue -->';
const END = '<!-- End Cue -->';
const FIELD_RE = /\[([^:\n[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|\n\s*<img|$))/g;
const normVal = (s) => s.replace(/^["']|["']$/g, '').replace(/\s+/g, ' ').trim();
const normText = (s) => s.replace(/<\/?p[^>]*>/g, '').replace(/\s+/g, ' ').trim();

function model(md) {
  const cues = [];
  let idx = 0;
  let textRegion = '';
  let b = md.indexOf(BEGIN, idx);
  while (b !== -1) {
    textRegion += md.slice(idx, b);
    const e = md.indexOf(END, b);
    if (e === -1) break;
    const block = md.slice(b + BEGIN.length, e);
    const vals = new Set();
    let m;
    FIELD_RE.lastIndex = 0;
    while ((m = FIELD_RE.exec(block)) !== null) {
      const v = normVal(m[2]);
      if (v) vals.add(v);
    }
    const img = block.match(/<img[^>]+src="([^"]+)"/);
    if (img) vals.add(normVal(img[1]));
    cues.push(vals);
    idx = e + END.length;
    b = md.indexOf(BEGIN, idx);
  }
  textRegion += md.slice(idx);
  const texts = new Set();
  for (const para of textRegion.split(/\n\s*\n/)) {
    const t = normText(para);
    if (t) texts.add(t);
  }
  return { cues, texts };
}

// new ⊇ legacy: everything legacy kept must also survive in the new editor.
function newSupersetsLegacy(legacyM, newM) {
  const missingCueVals = [];
  legacyM.cues.forEach((vals, i) => {
    const nv = newM.cues[i] || new Set();
    for (const v of vals) if (!nv.has(v)) missingCueVals.push(`cue#${i}:${v.slice(0, 40)}`);
  });
  const missingTexts = [...legacyM.texts].filter((t) => !newM.texts.has(t)).map((t) => t.slice(0, 50));
  return { missingCueVals, missingTexts, cueDelta: newM.cues.length - legacyM.cues.length };
}

const corpusPath = path.join(__dirname, '..', '..', 'src', 'utils', '__phase0__', 'corpus.jsonl');
const hasCorpus = fs.existsSync(corpusPath);
const maybe = hasCorpus ? describe : describe.skip;

maybe('editor parity (new ⊇ legacy on real corpus)', () => {
  const lines = hasCorpus
    ? fs.readFileSync(corpusPath, 'utf8').split('\n').filter(Boolean)
    : [];

  test('new editor loses nothing the legacy editor kept', () => {
    const regressions = [];
    for (const line of lines) {
      const { id, b64 } = JSON.parse(line);
      const raw = Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');
      const legacyM = model(legacyRoundTrip(raw));
      const newM = model(pmRoundTrip(raw));
      const { missingCueVals, missingTexts, cueDelta } = newSupersetsLegacy(legacyM, newM);
      if (missingCueVals.length || missingTexts.length || cueDelta < 0) {
        regressions.push({ id, missingCueVals, missingTexts, cueDelta });
      }
    }
    expect(regressions).toEqual([]);
  });

  test('new editor cue count >= legacy on every item', () => {
    for (const line of lines) {
      const { id, b64 } = JSON.parse(line);
      const raw = Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');
      const legacyCues = model(legacyRoundTrip(raw)).cues.length;
      const newCues = model(pmRoundTrip(raw)).cues.length;
      expect(`${id}:${newCues >= legacyCues}`).toBe(`${id}:true`);
    }
  });
});
