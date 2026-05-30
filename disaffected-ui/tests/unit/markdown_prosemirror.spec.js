/**
 * Phase 1 unit tests for the markdown <-> ProseMirror round-trip.
 * Run: npx jest tests/unit/markdown_prosemirror.spec.js
 *
 * Covers: the 3 Phase-0 bug fixes, frontmatter, malformed cues, field/img
 * ordering, idempotency, the loss-assertion, AND a round-trip over the real
 * episode corpus when present (corpus.jsonl is gitignored; tests that need it
 * are skipped gracefully in CI environments without the DB extract).
 */

/* global describe, test, expect */
import fs from 'fs';
import path from 'path';
import { markdownToDoc, docToMarkdown, splitFrontmatter, assertNoLoss } from '@/utils/prosemirror/markdown.js';

const roundTrip = (md) => {
  const { doc, frontmatter } = markdownToDoc(md);
  return docToMarkdown(doc, frontmatter);
};

describe('paragraph round-trip', () => {
  test('bare markdown is preserved (BUG 1 fix)', () => {
    const md = '## Notes\nsome text\n\n## Script\nmore text';
    const out = roundTrip(md);
    expect(out).toContain('## Notes');
    expect(out).toContain('some text');
    expect(out).toContain('## Script');
    expect(out).toContain('more text');
  });

  test('bare markdown + one stray <p> does NOT wipe surrounding text (BUG 1)', () => {
    const md = '## Notes\nimportant body text here\n<p class="josh"></p>';
    const out = roundTrip(md);
    expect(out).toContain('important body text here');
    expect(out).toContain('## Notes');
  });

  test('speaker, bullet, attention flags survive', () => {
    const md = '<p class="scott bullet" data-needs-attention="true" data-flag-note="check">Line</p>';
    const out = roundTrip(md);
    expect(out).toContain('class="scott bullet"');
    expect(out).toContain('data-needs-attention="true"');
    expect(out).toContain('data-flag-note="check"');
    expect(out).toContain('>Line<');
  });

  test('default speaker is josh', () => {
    const { doc } = markdownToDoc('plain line');
    expect(doc.firstChild.attrs.speaker).toBe('josh');
  });
});

describe('cue round-trip', () => {
  const fsq = [
    '<!-- Begin Cue -->',
    '[Type: FSQ]',
    '[AssetID: abc123]',
    '[Slug: a-quote]',
    '[Quote: "the words"]',
    '[Attribution: Someone]',
    '<!-- End Cue -->',
  ].join('\n');

  test('cue count preserved', () => {
    expect(roundTrip(fsq).match(/<!-- Begin Cue -->/g)).toHaveLength(1);
  });

  test('all field values survive', () => {
    const out = roundTrip(fsq);
    for (const v of ['abc123', 'a-quote', 'the words', 'Someone']) {
      expect(out).toContain(v);
    }
  });

  test('field labels preserved verbatim (no casing drift)', () => {
    const out = roundTrip(fsq);
    expect(out).toContain('[AssetID: abc123]'); // NOT "Asset Id"
  });

  test('mediaUrl field and <img> both survive (BUG 2 fix)', () => {
    const gfx = [
      '<!-- Begin Cue -->',
      '[Type: GFX]',
      '[Slug: pic]',
      '[MediaURL: ../assets/graphics/pic.png]',
      '<img src="../assets/graphics/pic.png" width="200" />',
      '<!-- End Cue -->',
    ].join('\n');
    const out = roundTrip(gfx);
    expect(out).toContain('[MediaURL: ../assets/graphics/pic.png]');
    expect(out).toContain('<img src="../assets/graphics/pic.png"');
  });

  test('field immediately before <img> survives re-parse (BUG 3 fix / idempotency)', () => {
    const gfx = [
      '<!-- Begin Cue -->',
      '[Type: GFX]',
      '[Slug: pic]',
      '<img src="pic.png" />',
      '<!-- End Cue -->',
    ].join('\n');
    const once = roundTrip(gfx);
    const twice = roundTrip(once);
    expect(once).toContain('[Slug: pic]');
    expect(twice).toContain('[Slug: pic]');
    expect(once).toBe(twice); // idempotent
  });

  test('malformed cue (missing End) is not merged into the next cue', () => {
    const md = [
      '<!-- Begin Cue -->',
      '[Type: SOT]',
      '[Slug: first]',
      '<!-- Begin Cue -->',
      '[Type: IMG]',
      '[Slug: second]',
      '<!-- End Cue -->',
    ].join('\n');
    const { doc } = markdownToDoc(md);
    const cues = [];
    doc.forEach((n) => n.type.name === 'cue' && cues.push(n));
    // Only the well-formed second cue becomes a cue node; the first stays text.
    expect(cues).toHaveLength(1);
    expect(cues[0].attrs.fields.Slug).toBe('second');
  });
});

describe('frontmatter', () => {
  test('split detects --- frontmatter', () => {
    const { frontmatter, body } = splitFrontmatter('---\ntitle: x\n---\n\nbody');
    expect(frontmatter).toContain('title: x');
    expect(body.trim()).toBe('body');
  });

  test('frontmatter is re-prepended on serialize', () => {
    const md = '---\ntitle: x\n---\n\n<p class="josh">hi</p>';
    const out = roundTrip(md);
    expect(out.startsWith('---')).toBe(true);
    expect(out).toContain('title: x');
    expect(out).toContain('>hi<');
  });

  test('no frontmatter is left untouched', () => {
    const { frontmatter } = splitFrontmatter('<p class="josh">hi</p>');
    expect(frontmatter).toBe('');
  });
});

describe('revision markup (reject-on-save)', () => {
  test('replacement proposal keeps the original (left of pipe)', () => {
    const md = '<p class="josh">Hello <rev user="k" ts="t">old|new</rev> world</p>';
    const out = roundTrip(md);
    expect(out).toContain('Hello old world');
    expect(out).not.toContain('<rev');
    expect(out).not.toContain('new');
  });

  test('cut-only proposal keeps the marked text', () => {
    const md = '<p class="josh">Keep <rev user="k" ts="t">this</rev> text</p>';
    const out = roundTrip(md);
    expect(out).toContain('Keep this text');
    expect(out).not.toContain('<rev');
  });

  test('DOM-form rev chrome is stripped, original kept', () => {
    const md = '<p class="josh">A <rev-kill>orig</rev-kill><rev-add>prop</rev-add> B</p>';
    const out = roundTrip(md);
    expect(out).toContain('orig');
    expect(out).not.toContain('prop');
    expect(out).not.toContain('<rev');
  });
});

describe('loss assertion', () => {
  test('clean round-trip reports ok', () => {
    const md = '<!-- Begin Cue -->\n[Type: SOT]\n[Slug: x]\n<!-- End Cue -->';
    expect(assertNoLoss(md, roundTrip(md)).ok).toBe(true);
  });

  test('detects a dropped cue', () => {
    const md = '<!-- Begin Cue -->\n[Type: SOT]\n[Slug: x]\n<!-- End Cue -->';
    const r = assertNoLoss(md, '<p class="josh">nothing</p>');
    expect(r.ok).toBe(false);
    expect(r.cueDelta).toBe(-1);
  });

  test('detects undefined poisoning', () => {
    const r = assertNoLoss('<p class="josh">x</p>', '<p class="undefined">x</p>');
    expect(r.ok).toBe(false);
    expect(r.hasUndefined).toBe(true);
  });
});

describe('real episode corpus (skipped if extract absent)', () => {
  const corpusPath = path.join(__dirname, '..', '..', 'src', 'utils', '__phase0__', 'corpus.jsonl');
  const hasCorpus = fs.existsSync(corpusPath);
  const maybe = hasCorpus ? test : test.skip;

  maybe('round-trips all real items with zero loss and idempotency', () => {
    const lines = fs.readFileSync(corpusPath, 'utf8').split('\n').filter(Boolean);
    for (const line of lines) {
      const { id, b64 } = JSON.parse(line);
      const raw = Buffer.from(b64.replace(/\s+/g, ''), 'base64').toString('utf8');
      const once = roundTrip(raw);
      const twice = roundTrip(once);
      const loss = assertNoLoss(raw, once);
      expect(`${id}:${loss.ok}`).toBe(`${id}:true`);
      expect(`${id}:idempotent`).toBe(`${id}:${once === twice ? 'idempotent' : 'CHANGED'}`);
    }
  });
});
