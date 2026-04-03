/**
 * Quote splitting utilities for FSQ (Full Screen Quote) display.
 * Pure functions — no state dependencies.
 */

/**
 * Validate segments returned by LLM
 * Checks for overlaps and coverage of original quote
 */
export function validateAndFixSegments(segments, originalQuote) {
  const promptArtifactPatterns = [
    /^RULES:/i,
    /^OUTPUT:/i,
    /^TEXT:/i,
    /^EXAMPLE/i,
    /^-\s*(?:Outer|Inner)\s*quotes?:/i,
    /^-\s*Apostrophe/i,
    /^Return\s*ONLY/i,
    /^NO\s*explanation/i,
    /<\/?(?:task|rules|output|input|quote)>/i
  ]

  for (const segment of segments) {
    for (const pattern of promptArtifactPatterns) {
      if (pattern.test(segment.trim())) {
        console.error('❌ Prompt artifact detected in segment:', segment.substring(0, 100))
        return { valid: false, segments }
      }
    }
  }

  if (segments.length === 1) {
    return { valid: true, segments }
  }

  const totalLength = segments.reduce((sum, seg) => sum + seg.trim().length, 0)
  const originalLength = originalQuote.trim().length

  const isOverlapping = totalLength > originalLength * 1.1

  if (isOverlapping) {
    console.warn('❌ Segments overlap detected:', {
      totalLength,
      originalLength,
      ratio: (totalLength / originalLength).toFixed(2)
    })
    return { valid: false, segments }
  }

  const reconstructed = segments.join(' ').trim()
  const coverageRatio = reconstructed.length / originalLength

  if (coverageRatio < 0.9) {
    console.warn('❌ Segments don\'t cover full quote:', {
      reconstructedLength: reconstructed.length,
      originalLength,
      coverageRatio: coverageRatio.toFixed(2)
    })
    return { valid: false, segments }
  }

  console.log('✅ Segments validated as non-overlapping and complete')
  return { valid: true, segments }
}

/**
 * Deterministic split algorithm (fallback when LLM fails)
 */
export function deterministicSplit(quote, maxCharsScreen1, minSecondScreen, balanceThreshold, preferSentenceBoundaries = true) {
  const quoteLength = quote.length

  if (quoteLength <= maxCharsScreen1) {
    console.log('📏 Quote fits on single screen')
    return [quote]
  }

  if (quoteLength <= balanceThreshold) {
    const targetSplitPoint = Math.floor(quoteLength / 2)
    console.log(`⚖️ Balanced split at ~${targetSplitPoint} chars (prevents orphan)`)

    const splitPoint = findBestSplitPoint(quote, targetSplitPoint, preferSentenceBoundaries)
    return [
      quote.substring(0, splitPoint).trim(),
      quote.substring(splitPoint).trim()
    ]
  }

  console.log(`📐 Standard split at ~${maxCharsScreen1} chars`)
  const splitPoint = findBestSplitPoint(quote, maxCharsScreen1, preferSentenceBoundaries)

  const firstSegment = quote.substring(0, splitPoint).trim()
  const remainder = quote.substring(splitPoint).trim()

  if (remainder.length > maxCharsScreen1) {
    console.log('🔁 Remainder too long, creating additional segments')
    const additionalSegments = deterministicSplit(
      remainder,
      maxCharsScreen1,
      minSecondScreen,
      balanceThreshold,
      preferSentenceBoundaries
    )
    return [firstSegment, ...additionalSegments]
  }

  return [firstSegment, remainder]
}

/**
 * Find the best split point near a target position.
 * Prefers sentence boundaries, then clause breaks, then word boundaries.
 */
export function findBestSplitPoint(text, targetPosition, preferSentenceBoundaries = true) {
  const searchStart = Math.max(0, targetPosition - 50)
  const searchEnd = Math.min(text.length, targetPosition + 50)
  const searchText = text.substring(searchStart, searchEnd)

  if (preferSentenceBoundaries) {
    const sentenceEndings = ['. ', '! ', '? ']
    for (const ending of sentenceEndings) {
      const relativePos = searchText.lastIndexOf(ending, targetPosition - searchStart)
      if (relativePos !== -1) {
        console.log(`  ✂️ Split at sentence boundary: "${ending.trim()}"`)
        return searchStart + relativePos + ending.length
      }
    }
  }

  const clauseBreaks = [', ', '; ', ': ', ' - ']
  for (const breakChar of clauseBreaks) {
    const relativePos = searchText.lastIndexOf(breakChar, targetPosition - searchStart)
    if (relativePos !== -1) {
      console.log(`  ✂️ Split at clause break: "${breakChar.trim()}"`)
      return searchStart + relativePos + breakChar.length
    }
  }

  const spacePos = text.lastIndexOf(' ', targetPosition)
  if (spacePos !== -1) {
    return spacePos + 1
  }

  return targetPosition
}
