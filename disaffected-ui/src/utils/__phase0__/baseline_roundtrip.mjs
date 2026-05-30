// Phase 0 baseline: measure the EXISTING CueParser round-trip fidelity over the
// real-episode corpus. This is the bar the ProseMirror round-trip must MEET OR BEAT.
//
//   raw  --parseContent-->  segments  --reconstructContent-->  rebuilt
//
// We report, per item: byte-identical? and if not, a normalized diff (so we can
// tell "harmless reformatting" from "real data loss"). The whole point of Phase 0
// is to learn what the current pipeline already does, so we don't hold ProseMirror
// to a standard the legacy code itself doesn't meet.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { CueParser } from '../cueParser.js';

const here = dirname(fileURLToPath(import.meta.url));
const lines = readFileSync(join(here, 'corpus.jsonl'), 'utf8').split('\n').filter(Boolean);

// psql base64 output wraps at 76 cols with \n — strip whitespace before decode.
function decode(b64) {
  return Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');
}

// Normalize for "semantic" comparison: collapse runs of blank lines and trim
// trailing whitespace per line. We do NOT normalize cue field order/casing here —
// we want to SEE that drift, since it tells us what the legacy round-trip mutates.
function normalize(s) {
  return s
    .split('\n')
    .map((l) => l.replace(/\s+$/, ''))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// Count cue blocks so we can detect cue loss specifically.
const countCues = (s) => (s.match(/<!-- Begin Cue -->/g) || []).length;

let exactCount = 0;
let semanticCount = 0;
let cueLossCount = 0;
const findings = [];

for (const line of lines) {
  const { id, b64 } = JSON.parse(line);
  const raw = decode(b64);

  let rebuilt;
  try {
    const segments = CueParser.parseContent(raw);
    // Mirror the PRODUCTION path: cue segments are passed through formatForCard
    // (which sets data.rawData) before they ever reach reconstructContent. The
    // editor stores the formatForCard output as segment.data, so reconstruct
    // reads data.rawData. Reproduce that here for a truthful baseline.
    const prodSegments = segments.map((seg) => {
      if (seg.type === 'cue') {
        return { ...seg, data: CueParser.formatForCard(seg.data) };
      }
      return seg;
    });
    rebuilt = CueParser.reconstructContent(prodSegments);
  } catch (e) {
    findings.push({ id, status: 'THREW', error: String(e) });
    continue;
  }

  const rawCues = countCues(raw);
  const newCues = countCues(rebuilt);
  const cueDelta = newCues - rawCues;
  if (cueDelta !== 0) cueLossCount++;

  const exact = raw === rebuilt;
  const semantic = normalize(raw) === normalize(rebuilt);
  if (exact) exactCount++;
  if (semantic) semanticCount++;

  findings.push({
    id,
    rawLen: raw.length,
    rebuiltLen: rebuilt.length,
    rawCues,
    newCues,
    cueDelta,
    exact,
    semantic,
    loss: CueParser.lastReconstructLossReport.droppedCues.length,
  });
}

console.log('=== BASELINE: existing CueParser round-trip over real corpus ===\n');
for (const f of findings) {
  if (f.status === 'THREW') {
    console.log(`item ${f.id}: THREW — ${f.error}`);
    continue;
  }
  const flag = f.exact ? '✅ exact' : f.semantic ? '≈ semantic-equal' : '⚠️ DIFFERS';
  const cueFlag = f.cueDelta === 0 ? '' : ` 🚨 CUE DELTA ${f.cueDelta}`;
  const lossFlag = f.loss ? ` DROPPED=${f.loss}` : '';
  console.log(
    `item ${String(f.id).padStart(5)}: ${flag.padEnd(16)} ` +
      `len ${f.rawLen}->${f.rebuiltLen}  cues ${f.rawCues}->${f.newCues}${cueFlag}${lossFlag}`
  );
}

const n = findings.filter((f) => f.status !== 'THREW').length;
console.log('\n=== SUMMARY ===');
console.log(`items:              ${n}`);
console.log(`byte-exact:         ${exactCount}/${n}`);
console.log(`semantic-equal:     ${semanticCount}/${n}`);
console.log(`cue-count changed:  ${cueLossCount}/${n}  (0 is the requirement — no cue may be lost)`);
