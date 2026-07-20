/**
 * convertLegacyToken — converts {SOT/foo}-style legacy tokens to canonical cue blocks.
 *
 * INTERIM IMPLEMENTATION (2026-05): the per-type field/default tables
 * imported from ./patterns.js are a LOCAL hand-mirror of what each cue's
 * modal produces today (SotModal, ImgCueModal, FsqModal, GfxModal,
 * NatModal, VoModal, PkgModal, DirModal, RifModal, and the library-backed
 * BumpModal/StingModal/MusModal/LiveModal/VoxModal). Parity tests in
 * __tests__/conversion.test.js guard against drift.
 *
 * MIGRATION PATH (TODO-1 in the dashboard todo panel + ACTIVE_WORK_QUEUE.md
 * + ICR post): once the shared cueTypeSchema utility exists and the 16
 * modals are refactored to consume it, the per-type tables in
 * patterns.js are DELETED and convertLegacyToken imports the schema
 * directly. Parity tests are retired. See README.md.
 *
 * TODO(cueTypeSchema): replace DEFAULT_DURATION_BY_TYPE imports with
 * cueTypeSchema lookups. Replace the per-type cue-block string
 * concatenation in buildCueBlock() with cueTypeSchema.buildCueBlock().
 */

import axios from 'axios'
import {
  ALIAS_MAP,
  DEFAULT_DURATION_BY_TYPE,
  LEGACY_CUE_REGEX_GLOBAL,
  MEDIA_BEARING_TYPES,
  VIDEO_CUE_LOOSE_REGEX,
  normalizeTokenType,
  sanitizeSlug,
} from './patterns'

/**
 * Public entry point. Convert every legacy cue token in a paragraph's
 * content into a real cue block, preserving prose around each token,
 * and stripping any leading `***` Auto Scrub marker.
 *
 * @param {Object} args
 * @param {Object} args.paragraphSegment - The flagged paragraph segment.
 *   Expected shape: { content, speaker, ... }. `content` is the inner
 *   HTML of the <p> (no <p> tags; may contain <b>/<i>/<u>/<a> markup
 *   from prose). May start with "*** " (the Auto Scrub flag prefix).
 * @param {string} args.episode - Episode number (e.g. "0272") for
 *   AssetID context and find-media lookups.
 * @param {string|number} [args.segmentId] - Rundown item id, used as
 *   AssetID generation context (audit trail only).
 *
 * @returns {Promise<{
 *   replacementSegments: Array,
 *   audit: Array<{ from: string, to: string, assetId: string|null }>
 * }>}
 *
 *   replacementSegments is a flat list of new segments to splice into
 *   scriptSegments at the original paragraph's index. Each entry is
 *   either { type: 'text', content, speaker, needsParagraphTags: true,
 *   needsAttention: false, flagNote: '' } OR { type: 'cue', cueType,
 *   data: { rawData: <parsed cue object> } }. Empty text segments
 *   between adjacent tokens are filtered out.
 *
 * @throws Error on hard failures (paragraph contained no recognizable
 *   token; AssetID generation network exception that we couldn't
 *   recover from; etc.). For soft failures (AssetID server returns
 *   non-2xx), the cue lands with [AssetID: pending] and the caller
 *   gets the audit entry annotated accordingly.
 */
export async function convertLegacyToken({ paragraphSegment, episode, segmentId = null }) {
  const original = paragraphSegment?.content || ''
  if (!original) {
    throw new Error('convertLegacyToken: empty paragraph content')
  }
  const speaker = paragraphSegment.speaker || 'josh'

  // Strip leading "*** " (Auto Scrub flag marker) — we're fixing the
  // flag, so the marker comes off.
  const stripped = original.replace(/^\s*\*\*\*\s*/, '')

  // Find all legacy tokens via the global regex.
  const matches = [...stripped.matchAll(LEGACY_CUE_REGEX_GLOBAL)]
  if (matches.length === 0) {
    throw new Error('convertLegacyToken: no legacy cue token found in paragraph')
  }

  const replacementSegments = []
  const audit = []
  let cursor = 0

  for (const match of matches) {
    const tokenStart = match.index
    const tokenEnd = tokenStart + match[0].length
    const rawType = match[1]
    const rawSlug = match[2]

    // Capture any prose between the previous cursor and this token.
    if (tokenStart > cursor) {
      const prose = stripped.slice(cursor, tokenStart).trim()
      if (prose) {
        replacementSegments.push({
          type: 'text',
          content: prose,
          speaker,
          needsParagraphTags: true,
          needsAttention: false,
          flagNote: '',
        })
      }
    }

    // Resolve canonical type via the alias map. Tokens like CUE that
    // are intentionally absent from ALIAS_MAP fall through here as
    // unconvertible — we keep the raw token in the prose so nothing
    // is silently lost.
    const normalized = normalizeTokenType(rawType)
    const canonicalType = ALIAS_MAP[normalized]
    const slug = sanitizeSlug(rawSlug)

    if (!canonicalType || !slug) {
      // Fall back: keep the original token as text so the user can fix it.
      replacementSegments.push({
        type: 'text',
        content: match[0],
        speaker,
        needsParagraphTags: true,
        needsAttention: false,
        flagNote: '',
      })
      audit.push({
        from: match[0],
        to: null,
        assetId: null,
        reason: canonicalType ? 'empty-slug' : 'unconvertible-type',
      })
      cursor = tokenEnd
      continue
    }

    // Generate (or retry) AssetID. Soft-fail to "pending" so a network
    // hiccup doesn't block the whole conversion.
    const assetIdResult = await generateAssetId({
      type: canonicalType,
      slug,
      episode,
      segmentId,
      originalToken: match[0],
    })

    // Try to find a matching media file in preshow/ for media-bearing
    // types. The endpoint returns null when nothing clears the
    // threshold; the cue still lands, just without [MediaURL].
    //
    // When find-media returns a hit, also call import-media to copy
    // the file to its canonical assets/ home and (for SOT/VO) kick off
    // the FFmpeg pipeline. The MediaURL we put on the new cue points
    // to that canonical destination, so the cue ends up indistinguishable
    // from a manually-entered one.
    let mediaUrl = null
    let processingJobId = null
    if (MEDIA_BEARING_TYPES.has(canonicalType)) {
      const placement = await findAndImportMedia({
        episode,
        slug,
        cueType: canonicalType,
        assetId: assetIdResult.assetId,
      })
      mediaUrl = placement.mediaUrl
      processingJobId = placement.processingJobId
    }

    // Build the cue block markdown.
    const cueBlockMd = buildCueBlock({
      canonicalType,
      assetId: assetIdResult.assetId,
      slug,
      mediaUrl,
      originalToken: match[0],
    })

    // Convert the markdown block back to a parsed cue segment so the
    // editor can render it. We rely on the caller passing us a
    // CueParser reference (avoids the module needing to import the
    // utils path directly — keeps the dependency surface narrow).
    // Convention: we attach the raw markdown string and let the editor
    // re-parse on emit. This works because EditorPanel reconstructs
    // the script via reconstructRawContent which feeds CueParser.
    replacementSegments.push({
      type: 'cue',
      cueType: canonicalType,
      data: {
        rawData: parseCueBlockToRawData(cueBlockMd),
      },
      // Keep the raw markdown around so callers that stringify
      // segments directly (rather than going through formatCueToMarkdown)
      // still get the right output.
      rawContent: cueBlockMd,
    })

    audit.push({
      from: match[0],
      to: cueBlockMd,
      assetId: assetIdResult.assetId,
      pending: assetIdResult.pending,
      mediaMatched: !!mediaUrl,
      processingJobId,
    })

    cursor = tokenEnd
  }

  // Trailing prose after the last token.
  if (cursor < stripped.length) {
    const tail = stripped.slice(cursor).trim()
    if (tail) {
      replacementSegments.push({
        type: 'text',
        content: tail,
        speaker,
        needsParagraphTags: true,
        needsAttention: false,
        flagNote: '',
      })
    }
  }

  return { replacementSegments, audit }
}

/**
 * convertVideoBlockWithLLM — LLM-extraction path for host-pasted VIDEO cue
 * blocks (SOT/VO/NAT). Hosts paste multi-line blocks with random whitespace:
 *
 *   (SOT/keysha eight)
 *   IN-02:54:58 "do you think"
 *   to
 *   OUT-02:57:31 "too tripped up in his lies"
 *
 * The regex path (convertLegacyToken) would convert the token but discard
 * the IN/OUT/quote data as prose. This path sends the WHOLE block plus
 * surrounding script context (Josh often notes the source file nearby) to
 * POST /api/legacy-cue-convert/extract-cue (local Ollama), then for each
 * extracted cue: AssetID → find-media (with the extracted source-file hint)
 * → import-media (with the extracted trim points, so the SOT/VO Celery
 * pipeline on the media queue trims to the host's in/out) → cue block md.
 *
 * Returns the same { replacementSegments, audit } shape as
 * convertLegacyToken so ScriptEditor handles both paths identically.
 * Throws when the LLM extracts nothing — callers should fall back to
 * convertLegacyToken.
 */
/**
 * Optional `pickMedia` callback (provided by ScriptEditor): invoked when
 * find-media cannot determine a source video for a cue. Receives
 * { label, slug, cueType, sourceHint } and must return:
 *   { filename, source_dir }  — the user picked a file (proceed with it)
 *   null                      — the user cancelled (cue fails, cancelled:true)
 *   false                     — no candidate files exist for this episode
 */
export async function convertVideoBlockWithLLM({ blockText, contextText = '', episode, speaker = 'josh', segmentId = null, pickMedia = null }) {
  const stripped = (blockText || '').replace(/^\s*\*\*\*\s*/, '').trim()
  if (!stripped) {
    throw new Error('convertVideoBlockWithLLM: empty block text')
  }

  const res = await axios.post('/api/legacy-cue-convert/extract-cue', {
    episode,
    block_text: stripped,
    context_text: contextText || '',
  })
  const cues = res.data?.cues || []
  if (cues.length === 0) {
    throw new Error('convertVideoBlockWithLLM: LLM extracted no cues')
  }

  const replacementSegments = []
  const audit = []

  // Preserve any prose BEFORE the first token on the anchor line — the
  // block gatherer hands us whole paragraphs, and a host sometimes leads
  // with a sentence before the (SOT/...) token.
  const tokenMatch = stripped.match(VIDEO_CUE_LOOSE_REGEX)
  if (tokenMatch && tokenMatch.index > 0) {
    const lead = stripped.slice(0, tokenMatch.index).trim()
    if (lead) {
      replacementSegments.push({
        type: 'text',
        content: lead,
        speaker,
        needsParagraphTags: true,
        needsAttention: false,
        flagNote: '',
      })
    }
  }

  const firstLine = stripped.split('\n')[0].slice(0, 120)

  // ALL-OR-NOTHING (per user direction): the conversion either produces a
  // COMPLETE cue block for every extracted cue — AssetID issued, media
  // matched, and (for SOT/VO) the Celery pipeline dispatched — or it throws
  // a structured error (err.failures) that the editor surfaces in a modal,
  // leaving the block flagged for retry. No partial/half-filled cues land.
  const failures = []

  for (const cue of cues) {
    const canonicalType = cue.type // backend already normalized to SOT/VO/NAT
    const label = `${canonicalType}/${cue.slug}`
    const slug = sanitizeSlug(cue.slug)
    if (!slug) {
      failures.push({ cue: label, reason: 'Could not derive a usable slug from the extracted data.' })
      continue
    }

    const assetIdResult = await generateAssetId({
      type: canonicalType,
      slug,
      episode,
      segmentId,
      originalToken: firstLine,
    })
    if (assetIdResult.pending) {
      failures.push({ cue: label, reason: 'AssetID generation failed (server unreachable or errored).' })
      continue
    }

    // Source-video resolution. The extract-cue LLM now sees the episode's
    // full (recursive) preshow file list and picks each cue's source video
    // itself: a VERIFIED pick (backend confirmed the file exists) imports
    // directly with no fuzzy matching. Otherwise fall back to find-media
    // (deterministic + LLM tiebreaker) with the unverified name as a hint,
    // then the manual picker.
    let mediaUrl = null
    let processingJobId = null
    let importMethod = null
    try {
      let filename = null
      let sourceDir = 'preshow'
      let candidatesConsidered = 0
      if (cue.source_file_verified && cue.source_file) {
        filename = cue.source_file
      } else {
        const found = await axios.post('/api/legacy-cue-convert/find-media', {
          episode,
          slug,
          cue_type: canonicalType,
          filename_hint: cue.source_file || null,
          // With trims present the backend searches preshow/ ONLY — the
          // source must be a recording, never a finished assets/ clip.
          trim_start: cue.in_point || null,
          trim_end: cue.out_point || null,
        })
        filename = found.data?.matched_filename
        sourceDir = found.data?.source_dir || 'preshow'
        candidatesConsidered = found.data?.candidates_considered ?? 0
      }

      // No automatic match → let the user pick the source video from the
      // episode's preshow folder (per user direction). Cancel = this cue
      // fails with a cancelled marker; no candidates at all = plain failure.
      if (!filename && typeof pickMedia === 'function') {
        const choice = await pickMedia({
          label,
          slug,
          cueType: canonicalType,
          sourceHint: cue.source_file || null,
        })
        if (choice === null) {
          failures.push({ cue: label, reason: 'No source video selected (picker cancelled).', cancelled: true })
          continue
        }
        if (choice === false) {
          failures.push({
            cue: label,
            reason: `No matching media found, and the episode has no ${canonicalType} ` +
              `candidate files in preshow/ or assets/video to choose from.`,
          })
          continue
        }
        filename = choice.filename
        sourceDir = choice.source_dir || 'preshow'
      }

      if (!filename) {
        // Lead with the LLM's own verdict when it looked at the episode's
        // file list and reported it could not identify the source video.
        const llmVerdict = cue.source_file_error
          ? `The AI was ${cue.source_file_error} among the episode's preshow files. `
          : ''
        failures.push({
          cue: label,
          reason: `${llmVerdict}No matching media found in preshow/ or assets/video ` +
            `(searched for "${slug}"${cue.source_file ? ` and source hint "${cue.source_file}"` : ''}, ` +
            `${candidatesConsidered} candidate file(s) considered).`,
        })
        continue
      }
      const placed = await axios.post('/api/legacy-cue-convert/import-media', {
        episode,
        slug,
        cue_type: canonicalType,
        source_filename: filename,
        source_dir: sourceDir,
        asset_id: assetIdResult.assetId,
        trim_start: cue.in_point || null,
        trim_end: cue.out_point || null,
      })
      mediaUrl = placed.data?.media_url || null
      processingJobId = placed.data?.processing_job_id || null
      importMethod = placed.data?.method || null
    } catch (err) {
      failures.push({
        cue: label,
        reason: `Media import failed: ${err.response?.data?.detail || err.message}`,
      })
      continue
    }

    // SOT/VO must have actually dispatched the processing pipeline; NAT has
    // no pipeline (preshow_link) so a MediaURL alone is complete for it.
    const needsPipeline = canonicalType === 'SOT' || canonicalType === 'VO'
    if (needsPipeline && !processingJobId) {
      failures.push({
        cue: label,
        reason: `Media matched but the ${canonicalType} processing pipeline was not dispatched (import method: ${importMethod || 'unknown'}).`,
      })
      continue
    }
    if (!needsPipeline && !mediaUrl) {
      failures.push({ cue: label, reason: 'Media matched but no MediaURL was returned.' })
      continue
    }

    const cueBlockMd = buildVideoCueBlock({
      canonicalType,
      assetId: assetIdResult.assetId,
      slug,
      cue,
      mediaUrl,
      processingJobId,
      originalToken: firstLine,
    })

    replacementSegments.push({
      type: 'cue',
      cueType: canonicalType,
      data: { rawData: parseCueBlockToRawData(cueBlockMd) },
      rawContent: cueBlockMd,
    })

    audit.push({
      from: firstLine,
      to: cueBlockMd,
      assetId: assetIdResult.assetId,
      pending: false,
      mediaMatched: true,
      processingJobId,
      llmExtracted: true,
    })
  }

  if (failures.length > 0) {
    const err = new Error(
      `convertVideoBlockWithLLM: ${failures.length} of ${cues.length} cue(s) could not be completed`
    )
    err.failures = failures
    err.extractedCount = cues.length
    throw err
  }

  return { replacementSegments, audit }
}

/**
 * COMPLETE cue-block markdown for an LLM-extracted video cue — mirrors the
 * fieldset ContentEditor.submitMultipleSots writes on a manual SOT modal
 * submit, so the converted cue renders and tracks exactly like a manually
 * created one (PlaceholderCueCard processing state, SourceJobId linkage,
 * pipeline field updates by AssetID).
 *
 * SOT/VO (pipeline dispatched): MediaURL/Duration/Transcription carry the
 * "Processing..." placeholders the pipeline overwrites on completion, plus
 * [SourceJobId] and [ProcessingStatus: Queued].
 * NAT (no pipeline): real MediaURL (preshow link) + computed/default
 * Duration — complete as-is.
 */
function buildVideoCueBlock({ canonicalType, assetId, slug, cue, mediaUrl, processingJobId, originalToken }) {
  const trimStart = cue.in_point || '00:00:00'
  const trimEnd = cue.out_point || '00:00:00'
  const hasTrims = !!(cue.in_point || cue.out_point)
  const pipeline = !!processingJobId && (canonicalType === 'SOT' || canonicalType === 'VO')

  let md = '<!-- Begin Cue -->\n'
  md += `[Type: ${canonicalType}]\n`
  md += `[AssetID: ${assetId}]\n`
  md += `[Slug: ${slug}]\n`
  md += `[Description: ]\n`
  if (pipeline) {
    md += '[MediaURL: Processing...]\n'
    md += '[Duration: Calculating...]\n'
  } else {
    md += `[MediaURL: ${mediaUrl || ''}]\n`
    const duration = computeDuration(cue.in_point, cue.out_point) || DEFAULT_DURATION_BY_TYPE[canonicalType]
    md += `[Duration: ${duration}]\n`
  }
  md += `[TrimStart: ${trimStart}]\n`
  md += `[TrimEnd: ${trimEnd}]\n`
  if (hasTrims) md += '[ClippingMethod: single-trim]\n'
  if (pipeline) {
    md += `[SourceJobId: ${processingJobId}]\n`
    md += `[OriginalTrimStart: ${trimStart}]\n`
    md += `[OriginalTrimEnd: ${trimEnd}]\n`
    md += '[Transcription: Processing...]\n'
    md += '[ThumbnailURL: ]\n'
  }
  if (cue.in_cue) md += `[Incue: ${cue.in_cue}]\n`
  if (cue.out_cue) md += `[Outcue: ${cue.out_cue}]\n`
  if (cue.source_url) md += `[SourceURL: ${cue.source_url}]\n`
  md += '[Credits: {}]\n'
  if (pipeline) md += '[ProcessingStatus: Queued]\n'
  md += `[ConvertedFrom: ${originalToken}]\n`
  md += '<!-- End Cue -->'
  return md
}

/** 'HH:MM:SS' in/out → 'HH:MM:SS:00' duration, or null when not computable. */
function computeDuration(inPoint, outPoint) {
  const toSecs = (tc) => {
    const m = /^(\d{1,2}):(\d{2}):(\d{2})$/.exec(tc || '')
    return m ? (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) : null
  }
  const a = toSecs(inPoint)
  const b = toSecs(outPoint)
  if (a === null || b === null || b <= a) return null
  const d = b - a
  const h = String(Math.floor(d / 3600)).padStart(2, '0')
  const mn = String(Math.floor((d % 3600) / 60)).padStart(2, '0')
  const s = String(d % 60).padStart(2, '0')
  return `${h}:${mn}:${s}:00`
}

/**
 * Generate a properly-typed AssetID via the modern endpoint. On any
 * failure (network, non-2xx, missing field) returns { assetId: 'pending',
 * pending: true } — the cue still lands with [AssetID: pending] so the
 * user can retry later.
 */
async function generateAssetId({ type, slug, episode, segmentId, originalToken }) {
  try {
    const res = await axios.post('/assetid/generate', {
      entity_type: type.toLowerCase(),
      reason: 'convert_legacy_token',
      context: {
        converted_from: originalToken,
        source_episode: episode,
        source_segment_id: segmentId,
        slug,
        trigger: 'auto_scrub_attempt_conversion',
      },
    })
    const id = res.data?.asset_id
    if (!id) {
      console.warn('[legacyCueConvert] generate-asset-id returned no asset_id', res.data)
      return { assetId: 'pending', pending: true }
    }
    return { assetId: id, pending: false }
  } catch (err) {
    console.warn('[legacyCueConvert] generate-asset-id failed:', err)
    return { assetId: 'pending', pending: true }
  }
}

/**
 * Resolve a media file in preshow/ AND place it (copy/rename/process)
 * the same way the manual modal would. Two-step:
 *   1. POST /api/legacy-cue-convert/find-media — locate the best match
 *      (deterministic + LLM tiebreaker).
 *   2. POST /api/legacy-cue-convert/import-media — copy it to assets/
 *      and (for SOT/VO) dispatch the FFmpeg Celery pipeline. Returns
 *      the canonical MediaURL we put on the new cue.
 *
 * Returns:
 *   { mediaUrl: string|null, processingJobId: string|null }
 */
async function findAndImportMedia({ episode, slug, cueType, assetId }) {
  try {
    const found = await axios.post('/api/legacy-cue-convert/find-media', {
      episode,
      slug,
      cue_type: cueType,
    })
    const filename = found.data?.matched_filename
    if (!filename) return { mediaUrl: null, processingJobId: null }
    // find-media now searches preshow/ AND assets/{subdir}; pass the source_dir
    // it reported through so import-media reads from the right folder.
    const sourceDir = found.data?.source_dir || 'preshow'

    const placed = await axios.post('/api/legacy-cue-convert/import-media', {
      episode,
      slug,
      cue_type: cueType,
      source_filename: filename,
      source_dir: sourceDir,
      asset_id: assetId,
    })
    return {
      mediaUrl: placed.data?.media_url || null,
      processingJobId: placed.data?.processing_job_id || null,
    }
  } catch (err) {
    console.warn('[legacyCueConvert] find-and-import-media failed:', err)
    return { mediaUrl: null, processingJobId: null }
  }
}

/**
 * Build the cue-block markdown for a single legacy token. Hand-mirrors
 * the field set + ordering each modal uses today.
 *
 * INTERIM — see file header. Future cueTypeSchema makes this a one-liner.
 */
function buildCueBlock({ canonicalType, assetId, slug, mediaUrl, originalToken }) {
  let md = '<!-- Begin Cue -->\n'
  md += `[Type: ${canonicalType}]\n`
  if (assetId) {
    md += `[AssetID: ${assetId}]\n`
  }
  md += `[Slug: ${slug}]\n`

  const duration = DEFAULT_DURATION_BY_TYPE[canonicalType]
  if (duration) {
    md += `[Duration: ${duration}]\n`
  }

  // NOTE-specific scaffold per the approved plan: DIR token converts
  // to NOTE cue with `[Note For: unknown]` placeholder.
  if (canonicalType === 'NOTE') {
    md += '[Note For: unknown]\n'
    md += '[Note Text: ]\n'
  }

  if (mediaUrl) {
    md += `[MediaURL: ${mediaUrl}]\n`
  }

  // Audit trail: the original token is preserved on the cue itself
  // so future tooling (or a confused operator) can trace where the
  // cue came from.
  md += `[ConvertedFrom: ${originalToken}]\n`

  md += '<!-- End Cue -->'
  return md
}

/**
 * Parse a cue-block markdown string into the rawData shape the editor's
 * CueParser produces. Mirrors the field-extraction logic in
 * cueParser.parseCueBlock so we don't need to import it (keeps the
 * module's dependency surface narrow).
 *
 * Field names are stored in camelCase (e.g. "Asset Id" → "assetId")
 * to match what the rest of the editor expects.
 */
function parseCueBlockToRawData(cueBlockMd) {
  // Pull out the inner content (between the markers).
  const inner = cueBlockMd
    .replace(/^<!-- Begin Cue -->\s*\n?/, '')
    .replace(/\s*<!-- End Cue -->\s*$/, '')

  const data = {}
  const fieldRegex = /\[([^:\n[\]]+):\s*([\s\S]*?)\](?=\s*(?:\n\s*\[|\n\s*<!--|$))/g
  let m
  while ((m = fieldRegex.exec(inner)) !== null) {
    const fieldName = m[1].trim()
    const fieldValue = m[2].trim()
    data[toCamelCase(fieldName)] = fieldValue
  }
  return data
}

function toCamelCase(fieldName) {
  // Mirror cueParser.toCamelCase: PascalCase → words → first lowercase, rest TitleCase.
  const spaced = fieldName.replace(/([a-z])([A-Z])/g, '$1 $2')
  return spaced
    .split(/[\s_-]+/)
    .map((w, i) => i === 0 ? w.toLowerCase() : (w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()))
    .join('')
}
