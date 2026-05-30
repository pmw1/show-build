// Show the actual raw-vs-rebuilt diff for a single corpus item, so we can
// classify what the legacy round-trip mutates (harmless reformat vs real loss).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { CueParser } from '../cueParser.js';

const targetId = Number(process.argv[2]);
const here = dirname(fileURLToPath(import.meta.url));
const lines = readFileSync(join(here, 'corpus.jsonl'), 'utf8').split('\n').filter(Boolean);
const decode = (b64) => Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');

for (const line of lines) {
  const { id, b64 } = JSON.parse(line);
  if (id !== targetId) continue;
  const raw = decode(b64);
  const segments = CueParser.parseContent(raw).map((seg) =>
    seg.type === 'cue' ? { ...seg, data: CueParser.formatForCard(seg.data) } : seg
  );
  const rebuilt = CueParser.reconstructContent(segments);

  const rawLines = raw.split('\n');
  const newLines = rebuilt.split('\n');
  const max = Math.max(rawLines.length, newLines.length);
  console.log(`=== item ${id}: ${raw.length} -> ${rebuilt.length} bytes ===\n`);
  let shown = 0;
  for (let i = 0; i < max && shown < 40; i++) {
    const a = rawLines[i] ?? '<none>';
    const b = newLines[i] ?? '<none>';
    if (a !== b) {
      console.log(`L${i + 1} RAW: ${a.slice(0, 110)}`);
      console.log(`L${i + 1} NEW: ${b.slice(0, 110)}`);
      console.log('');
      shown++;
    }
  }
  if (shown === 0) console.log('(no line-level differences — diff is whitespace/blank-line only)');
}
