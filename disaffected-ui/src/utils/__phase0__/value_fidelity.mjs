// Phase 0 value-fidelity check: prove that the legacy round-trip preserves every
// CUE FIELD VALUE and every PARAGRAPH'S TEXT, even when it mutates labels/order/wrapping.
//
// Method: parse BOTH raw and rebuilt into a normalized "semantic model" — a list of
// {kind, ...} records where cue fields are keyed by case-insensitive label with
// whitespace-collapsed values, and paragraphs by their inner text. Then diff the
// models. Any field-value or paragraph-text that exists in raw but not rebuilt is
// REAL loss; label/order/wrapping differences vanish under this normalization.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const lines = readFileSync(join(here, 'corpus.jsonl'), 'utf8').split('\n').filter(Boolean);
const decode = (b64) => Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');

const normLabel = (s) => s.toLowerCase().replace(/[\s_-]+/g, '');
const normVal = (s) => s.replace(/\s+/g, ' ').trim();
const normText = (s) =>
  s
    .replace(/<\/?p[^>]*>/g, '') // strip <p> wrappers
    .replace(/\s+/g, ' ')
    .trim();

// Extract the semantic content of a script string: every cue's field VALUES
// (keyed by normalized label) and every paragraph's normalized text.
function semanticModel(s) {
  const cueFieldValues = new Map(); // normLabel -> Set of normVal
  const texts = new Set();

  // cue blocks
  const BEGIN = '<!-- Begin Cue -->';
  const END = '<!-- End Cue -->';
  let idx = 0;
  let textRegion = '';
  while (true) {
    const b = s.indexOf(BEGIN, idx);
    if (b === -1) {
      textRegion += s.slice(idx);
      break;
    }
    textRegion += s.slice(idx, b);
    const e = s.indexOf(END, b);
    if (e === -1) {
      textRegion += s.slice(b);
      break;
    }
    const block = s.slice(b + BEGIN.length, e);
    const fieldRe = /\[([^:\n[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|$))/g;
    let m;
    while ((m = fieldRe.exec(block)) !== null) {
      const label = normLabel(m[1]);
      let val = normVal(m[2]);
      // legacy strips surrounding quotes on Quote; normalize both sides the same
      if (label === 'quote') val = val.replace(/^["']|["']$/g, '');
      if (val === '') continue; // empty fields carry no information
      if (!cueFieldValues.has(label)) cueFieldValues.set(label, new Set());
      cueFieldValues.get(label).add(val);
    }
    // embedded img src
    const img = block.match(/<img[^>]+src="([^"]+)"/);
    if (img) {
      if (!cueFieldValues.has('imgsrc')) cueFieldValues.set('imgsrc', new Set());
      cueFieldValues.get('imgsrc').add(normVal(img[1]));
    }
    idx = e + END.length;
  }

  // paragraphs from the text regions
  for (const para of textRegion.split(/\n\s*\n/)) {
    const t = normText(para);
    if (t) texts.add(t);
  }

  return { cueFieldValues, texts };
}

function diffModels(rawM, newM) {
  const lostFields = [];
  for (const [label, vals] of rawM.cueFieldValues) {
    const newVals = newM.cueFieldValues.get(label) || new Set();
    for (const v of vals) if (!newVals.has(v)) lostFields.push(`${label}=${v.slice(0, 40)}`);
  }
  const lostTexts = [];
  for (const t of rawM.texts) if (!newM.texts.has(t)) lostTexts.push(t.slice(0, 50));
  return { lostFields, lostTexts };
}

// We need the rebuilt output — import CueParser and reproduce the production path.
const { CueParser } = await import('../cueParser.js');

let perfect = 0;
const problems = [];
for (const line of lines) {
  const { id, b64 } = JSON.parse(line);
  const raw = decode(b64);
  const segs = CueParser.parseContent(raw).map((s) =>
    s.type === 'cue' ? { ...s, data: CueParser.formatForCard(s.data) } : s
  );
  const rebuilt = CueParser.reconstructContent(segs);

  const { lostFields, lostTexts } = diffModels(semanticModel(raw), semanticModel(rebuilt));
  if (lostFields.length === 0 && lostTexts.length === 0) {
    perfect++;
  } else {
    problems.push({ id, lostFields, lostTexts });
  }
}

console.log('=== VALUE FIDELITY: does the legacy round-trip lose any field VALUE or paragraph TEXT? ===\n');
if (problems.length === 0) {
  console.log(`✅ ${perfect}/${lines.length} items: ZERO value/text loss.`);
  console.log('   All byte-diffs are label-casing, field-order, empty-field pruning, or <p> wrapping.');
} else {
  console.log(`⚠️ ${perfect}/${lines.length} clean; ${problems.length} with REAL loss:\n`);
  for (const p of problems) {
    console.log(`item ${p.id}:`);
    if (p.lostFields.length) console.log('  lost field values:', p.lostFields);
    if (p.lostTexts.length) console.log('  lost paragraph texts:', p.lostTexts);
  }
}
