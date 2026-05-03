/**
 * Script Compare Utility
 * Parses comparator files (exported Google Docs), matches sections to rundown items,
 * and computes word-level diffs between plain-text representations.
 */
import { diffWords } from 'diff'

/**
 * Extract plain text from rundown item's script content.
 * - Replaces cue blocks with {TYPE/slug} placeholders
 * - Strips all HTML tags
 * - Normalizes whitespace
 */
export function extractPlainText(rawMarkdown) {
  if (!rawMarkdown) return ''

  // Replace cue blocks with placeholder tokens
  let text = rawMarkdown.replace(
    /<!-- Begin Cue -->([\s\S]*?)<!-- End Cue -->/g,
    (match, inner) => {
      const typeMatch = inner.match(/\[Type:\s*([^\]]+)\]/i)
      const slugMatch = inner.match(/\[Slug:\s*([^\]]+)\]/i)
      const type = typeMatch ? typeMatch[1].trim() : 'CUE'
      const slug = slugMatch ? slugMatch[1].trim() : ''
      return `\n{${type}/${slug}}\n`
    }
  )

  // Strip HTML tags, keep text content
  text = text.replace(/<[^>]+>/g, '')

  // Decode common HTML entities
  text = text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(code))

  // Normalize whitespace: collapse multiple newlines, trim lines
  text = text
    .split('\n')
    .map(line => line.trim())
    .filter((line, i, arr) => !(line === '' && arr[i - 1] === ''))
    .join('\n')
    .trim()

  return text
}

/**
 * Parse a comparator file (Google Doc text export) into sections.
 * Each section has a heading (rundown item title) and body text.
 *
 * Headings are detected as lines that:
 * - Are mostly uppercase (70%+ uppercase letters)
 * - Are short (under 80 chars)
 * - Don't start with { (replacement pattern)
 * - Are not attribution lines (starting with - or —)
 */
export function parseComparatorFile(fileContent, rundownItems) {
  if (!fileContent) return []

  // Build a set of known rundown item titles/slugs for matching
  const knownTitles = new Set()
  for (const item of (rundownItems || [])) {
    if (item.title) knownTitles.add(normalizeForMatch(item.title))
    if (item.slug) knownTitles.add(normalizeForMatch(item.slug))
  }

  const lines = fileContent.split('\n')
  const sections = []
  let currentHeading = null
  let currentBody = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()

    if (isHeadingLine(trimmed, knownTitles)) {
      // Save previous section
      if (currentHeading !== null) {
        sections.push({
          heading: currentHeading,
          body: currentBody.join('\n').trim()
        })
      }
      currentHeading = trimmed
      currentBody = []
    } else {
      currentBody.push(line)
    }
  }

  // Save last section
  if (currentHeading !== null) {
    sections.push({
      heading: currentHeading,
      body: currentBody.join('\n').trim()
    })
  }

  return sections
}

/**
 * Determine if a line is a section heading.
 */
function isHeadingLine(line, knownTitles) {
  if (!line || line.length === 0 || line.length > 80) return false
  // Not a replacement pattern
  if (line.startsWith('{')) return false
  // Not an attribution line
  if (line.startsWith('-') || line.startsWith('—') || line.startsWith('–')) return false

  // Check if it matches a known rundown item title
  const normalized = normalizeForMatch(line)
  if (knownTitles.has(normalized)) return true

  // Check if mostly uppercase (likely a segment header)
  const letters = line.replace(/[^a-zA-Z]/g, '')
  if (letters.length > 2) {
    const upperRatio = (line.replace(/[^A-Z]/g, '').length) / letters.length
    if (upperRatio >= 0.7) return true
  }

  return false
}

/**
 * Normalize a string for fuzzy matching: lowercase, strip punctuation, collapse whitespace
 */
export function normalizeForMatch(str) {
  return (str || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Compute similarity between two strings (0-1 score).
 * Uses token overlap (Jaccard similarity).
 */
export function similarity(a, b) {
  const tokensA = new Set(normalizeForMatch(a).split(' ').filter(Boolean))
  const tokensB = new Set(normalizeForMatch(b).split(' ').filter(Boolean))
  if (tokensA.size === 0 && tokensB.size === 0) return 1
  if (tokensA.size === 0 || tokensB.size === 0) return 0

  let intersection = 0
  for (const t of tokensA) {
    if (tokensB.has(t)) intersection++
  }
  const union = new Set([...tokensA, ...tokensB]).size
  return intersection / union
}

/**
 * Match comparator sections to rundown items.
 * Returns array of { rundownIndex, comparatorIndex, confidence }
 */
export function matchSections(comparatorSections, rundownItems) {
  const matches = []
  const usedRundown = new Set()
  const usedComparator = new Set()

  // First pass: exact matches
  for (let ci = 0; ci < comparatorSections.length; ci++) {
    const section = comparatorSections[ci]
    const normHeading = normalizeForMatch(section.heading)

    for (let ri = 0; ri < rundownItems.length; ri++) {
      if (usedRundown.has(ri)) continue
      const item = rundownItems[ri]
      const normTitle = normalizeForMatch(item.title || '')
      const normSlug = normalizeForMatch(item.slug || '')

      if (normHeading === normTitle || normHeading === normSlug) {
        matches.push({ rundownIndex: ri, comparatorIndex: ci, confidence: 1.0 })
        usedRundown.add(ri)
        usedComparator.add(ci)
        break
      }
    }
  }

  // Second pass: fuzzy matches for unmatched sections
  for (let ci = 0; ci < comparatorSections.length; ci++) {
    if (usedComparator.has(ci)) continue
    const section = comparatorSections[ci]

    let bestRi = -1
    let bestScore = 0

    for (let ri = 0; ri < rundownItems.length; ri++) {
      if (usedRundown.has(ri)) continue
      const item = rundownItems[ri]
      const titleScore = similarity(section.heading, item.title || '')
      const slugScore = similarity(section.heading, item.slug || '')
      const score = Math.max(titleScore, slugScore)

      if (score > bestScore) {
        bestScore = score
        bestRi = ri
      }
    }

    if (bestRi >= 0 && bestScore >= 0.4) {
      matches.push({ rundownIndex: bestRi, comparatorIndex: ci, confidence: bestScore })
      usedRundown.add(bestRi)
      usedComparator.add(ci)
    }
  }

  // Sort by rundown index for display order
  matches.sort((a, b) => a.rundownIndex - b.rundownIndex)
  return matches
}

/**
 * Normalize comparator body text:
 * - Convert replacement patterns {TYPE/slug} and multi-line FS QUOTE blocks to tokens
 * - Strip whitespace
 */
export function normalizeComparatorBody(bodyText) {
  if (!bodyText) return ''

  let text = bodyText

  // Handle multi-line FS QUOTE patterns:
  // {FS QUOTE/slug}
  // quote text...
  // -Attribution
  text = text.replace(
    /\{(FS\s*QUOTE|FSQ)\/([^}]+)\}\s*\n([\s\S]*?)(?=\n[-–—]([^\n]+))/gi,
    (_match, _type, slug) => {
      return `{FS QUOTE/${slug.trim()}}`
    }
  )

  // Handle simple replacement patterns: {TYPE/slug}
  // Already in the right format, just normalize type names
  text = text.replace(
    /\{([^/}]+)\/([^}]+)\}/g,
    (match, type, slug) => `{${type.trim().toUpperCase()}/${slug.trim()}}`
  )

  // Normalize whitespace
  text = text
    .split('\n')
    .map(line => line.trim())
    .filter((line, i, arr) => !(line === '' && arr[i - 1] === ''))
    .join('\n')
    .trim()

  return text
}

/**
 * Compute word-level diff between rundown text and comparator text.
 * Returns array of { value, added, removed } chunks.
 * Cue/replacement placeholders are treated as atomic tokens.
 */
export function computeDiff(rundownText, comparatorText) {
  return diffWords(rundownText, comparatorText, { ignoreWhitespace: true })
}

/**
 * Check if a replacement pattern {TYPE/slug} fuzzy-matches a cue block placeholder.
 */
export function cuePatternMatch(comparatorToken, rundownToken) {
  const compMatch = comparatorToken.match(/\{([^/]+)\/([^}]+)\}/)
  const rdMatch = rundownToken.match(/\{([^/]+)\/([^}]+)\}/)
  if (!compMatch || !rdMatch) return false

  const compType = compMatch[1].trim().toUpperCase()
  const rdType = rdMatch[1].trim().toUpperCase()
  const compSlug = normalizeForMatch(compMatch[2])
  const rdSlug = normalizeForMatch(rdMatch[2])

  // Type must match
  if (compType !== rdType) return false

  // Slug fuzzy match
  return similarity(compSlug, rdSlug) >= 0.5
}
