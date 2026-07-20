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
export const LEGACY_CUE_REGEX = /[{(]\s*(SOT|VO|VOT|NAT|FSQ|FS\s*QUOTE|GFX|IMG|PKG|DIR|BUMP|STING|VOX|MUS|LIVE|RIF|CUE)\s*\/([^})]+)[})]/i

/** Same pattern with /g for `matchAll()` over multi-token paragraphs. */
export const LEGACY_CUE_REGEX_GLOBAL = new RegExp(LEGACY_CUE_REGEX.source, 'gi')

/**
 * Video cue types (token forms) that route through the LLM extraction
 * path on Attempt Fix instead of the pure-regex conversion. Hosts paste
 * these as multi-line blocks — token line + IN/OUT timecode lines with
 * in-cue/out-cue quotes — that the regex path would discard as prose.
 */
export const VIDEO_CUE_TOKEN_TYPES = new Set(['SOT', 'VO', 'VOT', 'NAT'])

/**
 * Looser anchor for video blocks whose token line is malformed (missing
 * the closing bracket, stray spaces): `( SOT / keysha eight`. Used for
 * paste-time flagging and for deciding the LLM path — NOT for extraction
 * (the LLM does that).
 */
export const VIDEO_CUE_LOOSE_REGEX = /[{(]\s*(SOT|VO|VOT|NAT)\s*[/:]/i

/**
 * A paragraph that CONTINUES a pasted video-cue block. Hosts spread one
 * cue over several short lines with random whitespace:
 *
 *   (SOT/keysha eight)
 *   IN-02:54:58 "do you think"
 *   to
 *   OUT-02:57:31 "too tripped up in his lies"
 *
 * Matched (case-insensitive, liberal whitespace):
 *   - IN/OUT followed by a timecode (any of - – — : as separator)
 *   - a bare "to" line
 *   - a line that is just a quoted phrase
 *   - a bare timecode line
 */
/**
 * IN/OUT timecode marker ANYWHERE in a paragraph (`IN-02:54:58`,
 * `OUT: 2:05`). Used by the ScriptEditor sweeper to catch video-cue
 * blocks whose token anchor is missing entirely — the IN/OUT line itself
 * becomes the Attempt Fix anchor and the LLM derives type/slug from
 * the surrounding context.
 *
 * Deliberately CASE-SENSITIVE (uppercase IN/OUT only), unlike the
 * line-anchored CUE_CONTINUATION_REGEX: this one matches mid-prose, and
 * lowercase would false-positive on things like "tune in: 8:30 tonight"
 * — which the sweeper would then re-flag every 30s.
 */
// Separator after IN/OUT is OPTIONAL (per host practice): `IN-02:54:58`,
// `OUT: 2:05`, and bare `IN 29:14` all match.
export const VIDEO_INOUT_REGEX = /\b(IN|OUT)\s*[-–—:]*\s*\d{1,2}:\d{2}/

/**
 * Technical production line inside (or starting) a host video-cue block:
 * the "FULL VIDEO IS TITLED '…'" source-file line, or a generic all-caps
 * production note ("GRAB THE FULL YOUTUBE UPLOAD"). Consumed by
 * PasteHandler flagging and the ScriptEditor sweeper, where it can
 * anchor a block (when no token/IN-OUT anchor is open above) or join
 * one as a member line.
 *
 * Deliberately CASE-SENSITIVE like VIDEO_INOUT_REGEX: the all-caps
 * alternative works by requiring the absence of lowercase letters, and
 * an /i flag would make the [a-z]/[A-Z] classes meaningless. Hosts type
 * these notes in caps to set them off from prose; a lowercase "full
 * video is titled" will not match — accepted trade-off so ordinary
 * prose never flags.
 *
 * The all-caps alternative requires two capital words and ≥10 chars so
 * bare "OK", one-word shouts, and timecode fragments don't flag. The
 * TITLED alternative is separate because its quoted title tail is
 * usually mixed-case.
 *
 * FROM lines: hosts also name a cue's source video as `FROM: <title>` or
 * `FROM '<title>'` (e.g. `FROM '33LaKeyshaKeysha'`). The title is a fuzzy
 * reference — usually no file extension, casing/wording may drift from the
 * actual filename. Matching here makes the sweeper flag the line as
 * "Video cue data" AND puts it in the gathered block, so the extract-cue
 * LLM sees it and resolves it against the preshow file list. Uppercase
 * FROM + (colon or opening quote) is required so prose sentences starting
 * with "From ..." never flag; a bare all-caps `FROM FULL SURVEILLANCE
 * VIDEO` already matches the generic all-caps alternative.
 */
export const VIDEO_TECH_LINE_REGEX = new RegExp(
  [
    // "FULL VIDEO IS TITLED 'Mixed Case Title'"
    String.raw`^\s*FULL\s+VIDEO\s+IS\s+TITLED\b`,
    // "FROM: title" / "From: title" — colon form, any tail. Title-case
    // "From" is accepted ONLY with the colon (seen live: "From:
    // 32LaKeyshaKeysha"); prose sentences ("From here we see...") have
    // no colon and stay unflagged.
    String.raw`^\s*F(?:ROM|rom)\s*:`,
    // "FROM 'title'" / "FROM "title"" — quoted-title form
    String.raw`^\s*FROM\s+['"‘“]`,
    // bare "FROM 33LaKeyshaKeysha" — no colon, no quotes. Uppercase FROM
    // at line start distinguishes a production note from prose ("From
    // here we see..."); the ≤6-token tail keeps long prose lines out.
    String.raw`^\s*FROM\s+\S+(?:\s+\S+){0,5}\s*$`,
    // generic all-caps production note: no lowercase anywhere, at least
    // two 2+-letter capital words, at least 10 chars total
    String.raw`^(?!.*[a-z])(?=.*[A-Z]{2}.*\s.*[A-Z]{2}).{10,}$`,
  ].join('|')
)

/**
 * Flag note for NON-anchor lines of a detected video-cue block (the
 * IN/OUT/to/quote continuation lines). They get the needs-attention
 * tint so the whole block reads as one box, but NOT the Attempt Fix
 * button (that renders only for LEGACY_CUE_FLAG_LABEL, on the anchor).
 * The sweeper owns this label — it sets and clears it; never set it
 * manually.
 */
export const VIDEO_BLOCK_MEMBER_FLAG_LABEL = 'Video cue data'

export const CUE_CONTINUATION_REGEX = new RegExp(
  [
    String.raw`^\s*(IN|OUT)\s*[-–—:]*\s*\d{1,2}:\d{2}`,
    String.raw`^\s*to\s*$`,
    String.raw`^\s*["“'][^"”']*["”']\s*$`,
    String.raw`^\s*\d{1,2}:\d{2}(:\d{2})?\s*$`,
  ].join('|'),
  'i'
)

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
