// Phase 0 PROOF: run the real corpus through the ProseMirror round-trip and check
// the acceptance bar from PHASE0_FINDINGS.md:
//   1. zero cue loss   2. zero cue field-VALUE loss   3. zero paragraph-TEXT loss
//   4. idempotent: docToMarkdown(markdownToDoc(x)) stable on a second pass
//
// Comparison uses a per-cue, per-paragraph semantic model (the corrected version of
// value_fidelity, keyed per-block so multi-cue slug collisions don't false-positive).

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { markdownToDoc, docToMarkdown } from './pm_schema.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const lines = readFileSync(join(here, 'corpus.jsonl'), 'utf8').split('\n').filter(Boolean);
const decode = (b64) => Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');

const normVal = (s) => s.replace(/\s+/g, ' ').trim();
const normText = (s) => s.replace(/<\/?p[^>]*>/g, '').replace(/\s+/g, ' ').trim();

// Per-BLOCK semantic model: ordered list of cue records (each a sorted field-value
// set + img path) and an ordered list of paragraph texts. Per-cue keying avoids the
// cross-cue slug false-positive noted in PHASE0_FINDINGS.
function model(md) {
  const doc = markdownToDoc(md);
  const cues = [];
  const texts = [];
  doc.forEach((node) => {
    if (node.type.name === 'cue') {
      const vals = new Set();
      for (const [, v] of Object.entries(node.attrs.fields)) {
        const nv = normVal(String(v)).replace(/^["']|["']$/g, '');
        if (nv) vals.add(nv);
      }
      const img = (node.attrs.imgTag.match(/src="([^"]+)"/) || [])[1];
      if (img) vals.add(normVal(img));
      cues.push(vals);
    } else if (node.type.name === 'paragraph') {
      const t = normText(node.textContent);
      if (t) texts.push(t);
    }
  });
  return { cues, texts };
}

function lostValues(rawM, newM) {
  // cue field values: compare per-cue by index (order is preserved)
  const lostFields = [];
  rawM.cues.forEach((vals, i) => {
    const nv = newM.cues[i] || new Set();
    for (const v of vals) if (!nv.has(v)) lostFields.push(`cue#${i}: ${v.slice(0, 40)}`);
  });
  const newTexts = new Set(newM.texts);
  const lostTexts = rawM.texts.filter((t) => !newTexts.has(t)).map((t) => t.slice(0, 50));
  return { lostFields, lostTexts, rawCues: rawM.cues.length, newCues: newM.cues.length };
}

let cueOk = 0;
let valOk = 0;
let textOk = 0;
let idemOk = 0;
const problems = [];

for (const line of lines) {
  const { id, b64 } = JSON.parse(line);
  const raw = decode(b64);

  const doc1 = markdownToDoc(raw);
  const md1 = docToMarkdown(doc1);
  const md2 = docToMarkdown(markdownToDoc(md1)); // second pass for idempotency

  const rawM = model(raw);
  const newM = model(md1);
  const { lostFields, lostTexts, rawCues, newCues } = lostValues(rawM, newM);

  const cuePreserved = rawCues === newCues;
  const valuePreserved = lostFields.length === 0;
  const textPreserved = lostTexts.length === 0;
  const idempotent = md1 === md2;

  if (cuePreserved) cueOk++;
  if (valuePreserved) valOk++;
  if (textPreserved) textOk++;
  if (idempotent) idemOk++;

  if (!cuePreserved || !valuePreserved || !textPreserved || !idempotent) {
    problems.push({ id, rawCues, newCues, lostFields, lostTexts, idempotent });
  }
}

const n = lines.length;
console.log('=== PHASE 0 PROOF: ProseMirror markdown<->doc round-trip over real corpus ===\n');
console.log(`cue count preserved:     ${cueOk}/${n}`);
console.log(`cue field VALUES kept:    ${valOk}/${n}`);
console.log(`paragraph TEXT kept:      ${textOk}/${n}   <- BUG 1 was here (legacy failed)`);
console.log(`idempotent (stable 2nd):  ${idemOk}/${n}`);
console.log('');
if (problems.length === 0) {
  console.log('✅ PHASE 0 PASSES — the ProseMirror model clears the bar on all 18 real items.');
  console.log('   Zero cue loss, zero value loss, zero text loss, fully idempotent.');
} else {
  console.log(`⚠️ ${problems.length} item(s) need attention:\n`);
  for (const p of problems) {
    console.log(`item ${p.id}: cues ${p.rawCues}->${p.newCues} idempotent=${p.idempotent}`);
    if (p.lostFields.length) console.log('  lost values:', p.lostFields.slice(0, 8));
    if (p.lostTexts.length) console.log('  lost texts:', p.lostTexts.slice(0, 8));
  }
}
