/**
 * Legacy Cue Convert — patterns and alias map.
 *
 * Single source of truth for what a "legacy cue token" looks like
 * in pasted/imported scripts and how each token's type maps to a
 * canonical cue type for conversion.
 *
 * NOTE: this file is a stable boundary. The Auto Scrub feature in
 * EditorPanel.vue imports LEGACY_CUE_REGEX and LEGACY_CUE_FLAG_LABEL
 * directly. The conversion module's conversion.js consumes ALIAS_MAP
 * + DEFAULT_DURATION_BY_TYPE + MEDIA_BEARING_TYPES. Future work that
 * extracts a shared cue-type schema (see TODO in conversion.js) will
 * pull DEFAULT_DURATION_BY_TYPE from there instead of hard-coding it
 * here, but the regex and alias map will remain.
 */

/**
 * Matches both `{TYPE/slug}` and `(TYPE/slug)` forms in pasted prose.
 *
 * Capture groups:
 *   1: the cue-type token (uppercase or mixed case; FS QUOTE allows whitespace)
 *   2: the slug (everything between the `/` and the closing bracket)
 *
 * Bracket pairs are not strictly required to match — `{TYPE/slug)` and
 * `(TYPE/slug}` will also match. That's intentional: pasted residue is
 * often messy and we'd rather flag a half-broken token than miss it.
 *
 * The /i flag makes the type group case-insensitive so `{sot/foo}`
 * still matches — that's important because legacy scripts vary in case.
 */
export const LEGACY_CUE_REGEX = /[{(](SOT|VO|VOT|NAT|FSQ|FS\s*QUOTE|GFX|IMG|PKG|DIR|BUMP|STING|VOX|MUS|LIVE|RIF|CUE)\s*\/([^})]+)[})]/i

/** Same pattern with /g for `matchAll()` over multi-token paragraphs. */
export const LEGACY_CUE_REGEX_GLOBAL = new RegExp(LEGACY_CUE_REGEX.source, 'gi')

/**
 * The exact string Auto Scrub writes to `data-flag-note` on flagged
 * paragraphs containing legacy-cue tokens. The ConvertButton renders
 * if and only if `segment.flagNote === LEGACY_CUE_FLAG_LABEL`.
 *
 * Don't change this string casually — Auto Scrub's un-flag step
 * (EditorPanel.vue applyAutoFormatting step 3c) keys off it too.
 */
export const LEGACY_CUE_FLAG_LABEL = 'Invalid cue code'

/**
 * Token-type → canonical cue type. The token is whatever the regex
 * captured (possibly with whitespace, possibly mixed case). Lookup
 * is done against the upper-cased, whitespace-stripped form.
 *
 * Per user direction:
 *   - VOT: typo / variant of SOT — convert as SOT
 *   - DIR: convert to NOTE cue type with `Note For: unknown`
 *   - FS QUOTE: alternate spelling for FSQ
 *   - CUE: detected (still flags via Auto Scrub) but the convert
 *     button does NOT render — too ambiguous for auto-conversion.
 *     This entry is intentionally absent so callers checking
 *     `ALIAS_MAP[normalized]` get `undefined` and short-circuit.
 */
export const ALIAS_MAP = {
  SOT: 'SOT',
  VOT: 'SOT',          // typo correction
  VO:  'VO',
  NAT: 'NAT',
  FSQ:     'FSQ',
  FSQUOTE: 'FSQ',      // matches "FS QUOTE" after whitespace strip
  GFX:  'GFX',
  IMG:  'IMG',
  PKG:  'PKG',
  DIR:  'NOTE',        // DIR markdown → NOTE cue, with Note For:unknown
  BUMP:  'BUMP',
  STING: 'STING',
  VOX:   'VOX',
  MUS:   'MUS',
  LIVE:  'LIVE',
  RIF:   'RIF',
  // CUE intentionally omitted — see docstring above
}

/**
 * Default `[Duration: ...]` per canonical cue type for converted cues.
 * NOTE and RIF have no duration line. This table is hand-mirrored from
 * each modal's buildCueBlock — the cue-type-schema TODO will replace
 * this with a single dynamic lookup eventually.
 */
export const DEFAULT_DURATION_BY_TYPE = {
  SOT:  '00:00:30:00',
  VO:   '00:00:30:00',
  NAT:  '00:00:30:00',
  PKG:  '00:00:30:00',
  BUMP: '00:00:30:00',
  STING:'00:00:30:00',
  VOX:  '00:00:30:00',
  MUS:  '00:00:30:00',
  LIVE: '00:00:30:00',
  // Image-type cues use a shorter default
  FSQ: '00:00:15:00',
  GFX: '00:00:15:00',
  IMG: '00:00:15:00',
  // NOTE and RIF: no duration line at all
}

/**
 * Cue types whose conversion attempts a media-file lookup in the
 * episode's preshow/ folder. Listed types pass through find-media;
 * unlisted types convert to a media-less cue.
 *
 * NAT and PKG are listed — they get a `[MediaURL]` linking directly
 * to the preshow file (no copy, no processing) because their backend
 * processing pipelines are currently broken. See ACTIVE_WORK_QUEUE.md.
 */
export const MEDIA_BEARING_TYPES = new Set([
  'SOT', 'VO', 'NAT', 'PKG',
  'IMG', 'GFX',
  'BUMP', 'STING', 'MUS', 'VOX',
])

/**
 * Normalize the captured token to look up in ALIAS_MAP.
 *   "FS QUOTE" → "FSQUOTE"
 *   "sot"      → "SOT"
 *   " VOT "    → "VOT"
 */
export function normalizeTokenType(rawToken) {
  return (rawToken || '').toUpperCase().replace(/\s+/g, '')
}

/**
 * Sanitize a slug exactly the way ImgCueModal does today
 * (disaffected-ui/src/components/content-editor/modals/ImgCueModal.vue:425).
 *
 * Pulled here so the conversion module doesn't depend on importing
 * a function out of a Vue SFC.
 */
export function sanitizeSlug(raw) {
  return (raw || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
}
