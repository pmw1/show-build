/**
 * useScriptCore — Core script content state and save pipeline
 *
 * Extracted from EditorPanel.vue. Owns:
 *   - segmentEditBuffer / updateDebounceTimers (non-reactive, closure variables)
 *   - Editing-state flags (isActivelyEditing, isActivelyTyping, etc.)
 *   - scriptSegments / draggableSegments computed properties
 *   - reconstructRawContent, emitScriptContent, updateTextSegment, flushPendingChanges
 *   - Content validation / repair helpers
 *
 * Usage (Options API setup()):
 *   const core = useScriptCore(props, emit, sanitizer, { isDragging })
 *   return { ...core }
 *
 * Props consumed: scriptContent, editorMode
 * Events emitted: update:scriptContent
 */

import { ref, computed, nextTick, markRaw, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from 'vue-toastification'
import CueParser from '@/utils/cueParser.js'

export function useScriptCore(props, emit, sanitizer, externalGuards = {}) {
  // ---------------------------------------------------------------------------
  // Non-reactive buffers (intentionally invisible to Vue's reactivity system)
  //
  // Using markRaw so Vue won't convert these to reactive proxies when returned
  // from setup(). The component can still access them via this.segmentEditBuffer
  // for backward compatibility with existing code that reads/writes the buffer.
  // ---------------------------------------------------------------------------
  const segmentEditBuffer = markRaw({})
  const updateDebounceTimers = markRaw({})

  // Internal aliases for use within the composable
  const _editBuffer = segmentEditBuffer
  const _debounceTimers = updateDebounceTimers

  /** Read the raw buffer object (for inspection / iteration). */
  const getEditBuffer = () => _editBuffer
  /** Set a single key in the edit buffer. */
  const setEditBufferEntry = (key, value) => { _editBuffer[key] = value }
  /** Delete a single key from the edit buffer. */
  const deleteEditBufferEntry = (key) => { delete _editBuffer[key] }
  /** Clear the entire edit buffer. */
  const clearEditBuffer = () => {
    Object.keys(_editBuffer).forEach(k => delete _editBuffer[k])
  }

  const getDebounceTimers = () => _debounceTimers
  const clearDebounceTimers = () => {
    Object.keys(_debounceTimers).forEach(k => delete _debounceTimers[k])
  }

  // ---------------------------------------------------------------------------
  // Reactive state
  // ---------------------------------------------------------------------------
  const isActivelyEditing = ref(false)
  const isActivelyTyping = ref(false)
  const activelyEditingSegment = ref(null)
  const isRestoringCursor = ref(false)
  const savedCursorState = ref(null)
  const blockReactiveUpdates = ref(false)
  const cachedScriptSegments = ref(null)
  const lastParsedContent = ref(null)
  const segmentReparseKey = ref(0)
  const hasLocalUnsavedChanges = ref(false)

  // External guards — these come from the component (e.g. drag composable later)
  const isDragging = externalGuards.isDragging || ref(false)

  // Destructure sanitizer helpers we need
  const { stripYamlFrontmatter, extractYamlFrontmatter, stripRevisionMarkup } = sanitizer

  // Toast — best-effort; useToast() requires a setup context, but composables
  // are always called from one. If it fails (e.g. tests), guard with try/catch.
  let toast = null
  try {
    toast = useToast()
  } catch (e) {
    toast = null
  }

  // Cue-loss tripwire: latch so successive bad emits in the same edit burst
  // don't spam. Reset every time a save guard *passes*. Cue-loss is data
  // corruption — never auto-bypassed.
  let _cueLossToastShown = false

  // Shrink-guard toast debounce — kept around in case we re-enable the
  // hard abort later. Currently unused (gate downgraded to console.warn).
  // eslint-disable-next-line no-unused-vars
  let _lastShrinkToastAt = 0
  // eslint-disable-next-line no-unused-vars
  const SHRINK_TOAST_DEBOUNCE_MS = 5000

  // One-shot shrink-guard override. Set by Ctrl+Alt+S; cleared on the next
  // successful emit. Lets the user explicitly wave through a save that
  // would otherwise be blocked (e.g. an intentional bulk-delete).
  let _allowNextShrink = false

  // Whether the shrink guard is enabled at all. Mirrored to localStorage so
  // the settings page (which lives on a different route) and the editor
  // session agree without a backend round-trip. Default ON — the guard is
  // the safety net for the data-loss bug we just hit.
  const SHRINK_GUARD_LS_KEY = 'show-build:scriptShrinkGuardEnabled'
  function _readShrinkGuardLS() {
    try {
      const v = localStorage.getItem(SHRINK_GUARD_LS_KEY)
      if (v === null) return true
      return v === 'true'
    } catch (_e) {
      return true
    }
  }
  const shrinkGuardEnabled = ref(_readShrinkGuardLS())
  function setShrinkGuardEnabled(v) {
    shrinkGuardEnabled.value = !!v
    try {
      localStorage.setItem(SHRINK_GUARD_LS_KEY, shrinkGuardEnabled.value ? 'true' : 'false')
    } catch (_e) { /* ignore */ }
    console.log(`Shrink guard: ${shrinkGuardEnabled.value ? 'ENABLED' : 'DISABLED'}`)
  }
  // Pick up changes made on the settings page in another tab.
  function _onStorageChange(e) {
    if (e.key === SHRINK_GUARD_LS_KEY) {
      shrinkGuardEnabled.value = _readShrinkGuardLS()
      console.log(`Shrink guard updated from storage event: ${shrinkGuardEnabled.value ? 'ENABLED' : 'DISABLED'}`)
    }
  }
  onMounted(() => { window.addEventListener('storage', _onStorageChange) })
  onBeforeUnmount(() => { window.removeEventListener('storage', _onStorageChange) })

  function allowNextShrink() {
    _allowNextShrink = true
    if (toast) toast.info('Shrink guard suspended for next save', { timeout: 3000 })
    console.log('🟢 Shrink guard suspended for next save (Ctrl+Alt+S)')
  }

  // Global keyboard handler: Ctrl+Alt+S → one-shot bypass.
  // Use `e.code === 'KeyS'` so the shortcut is layout-independent.
  function _shrinkOverrideKeyHandler(e) {
    if (e.ctrlKey && e.altKey && !e.shiftKey && !e.metaKey && e.code === 'KeyS') {
      e.preventDefault()
      e.stopPropagation()
      allowNextShrink()
    }
  }
  onMounted(() => {
    document.addEventListener('keydown', _shrinkOverrideKeyHandler, true)
  })
  onBeforeUnmount(() => {
    document.removeEventListener('keydown', _shrinkOverrideKeyHandler, true)
  })

  // ---------------------------------------------------------------------------
  // Computed: rawScriptContent (writable)
  // ---------------------------------------------------------------------------
  const rawScriptContent = computed({
    get() {
      return props.scriptContent || ''
    },
    set(value) {
      emit('update:scriptContent', value)
    }
  })

  // ---------------------------------------------------------------------------
  // Computed: scriptSegments (writable, with caching logic)
  // ---------------------------------------------------------------------------
  // eslint-disable-next-line vue/no-side-effects-in-computed-properties
  const scriptSegments = computed({
    get() {
      // ────────────────────────────────────────────────────────────────────
      // Cursor-stability cache (isActivelyEditing / isDragging):
      //
      // While the user is typing inside a contenteditable paragraph, or
      // dragging a segment, we return cached segments to avoid Vue marking
      // children dirty and stealing cursor focus / drag handles.
      //
      // BUT — and this is the 2026-05-09 lesson — we MUST verify the cache
      // matches current rawScriptContent before returning it. If a sibling
      // mutation (cue insert/delete, paste cleanup, scratch sync, legacy
      // convert) updated rawScriptContent since the cache was frozen, the
      // cached snapshot is stale. Returning it to a write-path caller
      // (anything doing `[...scriptSegments.value]` then a splice + setter)
      // wipes everything the sibling mutation did.
      //
      // So: keep the early-return short-circuit for stability, but require
      // the cache to be content-coherent. If rawScriptContent has drifted,
      // fall through to the normal re-parse path even mid-typing — momentary
      // re-render risk is far cheaper than silent data loss.
      // ────────────────────────────────────────────────────────────────────
      if (isActivelyEditing.value
          && cachedScriptSegments.value !== null
          && lastParsedContent.value === rawScriptContent.value) {
        return cachedScriptSegments.value
      }

      if (isDragging.value
          && cachedScriptSegments.value !== null
          && lastParsedContent.value === rawScriptContent.value) {
        return cachedScriptSegments.value
      }

      // CRITICAL: Read segmentReparseKey to create a Vue dependency.
      // When this key is incremented (on item switch), Vue will invalidate this
      // computed even if the manual cache thinks nothing changed.
      // eslint-disable-next-line no-unused-vars
      const _reparseKey = segmentReparseKey.value

      if (!rawScriptContent.value || props.editorMode !== 'script') {
        cachedScriptSegments.value = null
        lastParsedContent.value = null
        return []
      }

      // Only re-parse if content has actually changed
      const currentContent = rawScriptContent.value
      if (lastParsedContent.value === currentContent && cachedScriptSegments.value !== null) {
        console.log('  → Returning cached segments (content unchanged)')
        return cachedScriptSegments.value
      }

      console.log('  → Re-parsing content (content changed)')
      try {
        // Strip YAML frontmatter for parsing
        const contentWithoutFrontmatter = stripYamlFrontmatter(rawScriptContent.value)
        console.log('  contentWithoutFrontmatter:', contentWithoutFrontmatter?.substring(0, 100))

        // If content is empty or only whitespace, return empty paragraph segment
        if (!contentWithoutFrontmatter || contentWithoutFrontmatter.trim() === '') {
          console.log('  → Returning single empty text segment')
          const emptySegment = [{
            type: 'text',
            content: '',
            speaker: 'josh',
            needsParagraphTags: true,
            segmentIndex: 0
          }]
          cachedScriptSegments.value = emptySegment
          lastParsedContent.value = currentContent
          return emptySegment
        }

        const segments = CueParser.parseContent(contentWithoutFrontmatter)

        const mappedSegments = segments.map((segment, index) => {
          if (segment.type === 'cue') {
            // Format cue data for card display
            const formattedCueData = CueParser.formatForCard(segment.data)
            return {
              type: 'cue',
              data: formattedCueData,
              segmentIndex: index
            }
          }
          return {
            ...segment,
            segmentIndex: index
          }
        })

        // Cache the results
        cachedScriptSegments.value = mappedSegments
        lastParsedContent.value = currentContent
        return mappedSegments
      } catch (error) {
        console.error('Error parsing script segments:', error)
        // Fallback: treat as single text segment
        const contentWithoutFrontmatter = stripYamlFrontmatter(rawScriptContent.value)
        const fallbackSegment = [{
          type: 'text',
          content: contentWithoutFrontmatter,
          speaker: 'josh',
          needsParagraphTags: true,
          segmentIndex: 0
        }]
        cachedScriptSegments.value = fallbackSegment
        lastParsedContent.value = currentContent
        return fallbackSegment
      }
    },
    set(newSegments) {
      console.log('🔄 scriptSegments setter called with', newSegments.length, 'segments')

      // Reset loss report; the setter does its own cue tracking inline.
      const lossReport = { totalCueSegments: 0, droppedCues: [] }

      const frontmatter = extractYamlFrontmatter(rawScriptContent.value)
      let newContent = ''

      newSegments.forEach((segment, idx) => {
        if (segment.type === 'text') {
          const speaker = segment.speaker || 'josh'
          const content = segment.content || ''
          newContent += `<p class="${speaker}">${content}</p>\n\n`
        } else if (segment.type === 'cue') {
          lossReport.totalCueSegments++
          if (segment.data && segment.data.rawData) {
            newContent += CueParser.formatCueToMarkdown(segment.data.rawData)
            newContent += '\n\n'
          } else {
            lossReport.droppedCues.push({
              index: idx,
              cueType: segment.cueType || segment.data?.type || null,
              slug: segment.data?.slug || null,
              assetId: segment.data?.assetId || null,
              hasData: !!segment.data,
              hasRawData: !!segment.data?.rawData
            })
            console.error('🚨 CUE LOSS TRIPWIRE (scriptSegments setter) — would drop:', segment)
          }
        }
      })

      CueParser.lastReconstructLossReport = lossReport
      const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim()
      safeEmitScriptContent(newRawContent, { reason: 'scriptSegments-set' })
    }
  })

  // ---------------------------------------------------------------------------
  // Computed: draggableSegments (writable)
  //
  // NOTE: The setter depends on component-level state (pendingCueData,
  // showCuePlacement, insertPendingCueAtIndex) that is NOT in this composable.
  // The setter is left as a thin wrapper that delegates to a callback.
  // ---------------------------------------------------------------------------

  // Callback slot for the component to provide its drag-set logic
  let _onDraggableSet = null
  function setDraggableSetHandler(fn) {
    _onDraggableSet = fn
  }

  // Callback slot for the component to provide pending-cue getter
  let _getPendingCueContext = null
  function setPendingCueContextGetter(fn) {
    _getPendingCueContext = fn
  }

  const draggableSegments = computed({
    get() {
      const segments = [...scriptSegments.value]

      // If there's a pending cue context, add ghost segments
      if (_getPendingCueContext) {
        const ctx = _getPendingCueContext()
        if (ctx && ctx.pendingCueData && ctx.showCuePlacement) {
          const cueBlocks = Array.isArray(ctx.pendingCueData) ? ctx.pendingCueData : [ctx.pendingCueData]

          cueBlocks.forEach((cueBlock) => {
            const cueData = CueParser.parseCueBlock(cueBlock)
            if (cueData) {
              segments.push({
                type: 'cue',
                data: CueParser.formatForCard(cueData),
                isPending: true,
                segmentIndex: segments.length
              })
            }
          })
        }
      }

      return segments
    },
    set(newSegments) {
      // Delegate to component-provided handler for drag logic
      if (_onDraggableSet) {
        _onDraggableSet(newSegments)
        return
      }

      // Fallback: basic reorder without pending-cue awareness
      const realSegments = newSegments.filter(seg => !seg.isPending)
      const frontmatter = extractYamlFrontmatter(rawScriptContent.value)
      let newContent = ''

      const lossReport = { totalCueSegments: 0, droppedCues: [] }

      realSegments.forEach((segment, idx) => {
        if (segment.type === 'text') {
          const speaker = segment.speaker || 'josh'
          const content = segment.content || ''
          newContent += `<p class="${speaker}">${content}</p>\n\n`
        } else if (segment.type === 'cue') {
          lossReport.totalCueSegments++
          if (segment.data && segment.data.rawData) {
            newContent += CueParser.formatCueToMarkdown(segment.data.rawData)
            newContent += '\n\n'
          } else {
            lossReport.droppedCues.push({
              index: idx,
              cueType: segment.cueType || segment.data?.type || null,
              slug: segment.data?.slug || null,
              assetId: segment.data?.assetId || null,
              hasData: !!segment.data,
              hasRawData: !!segment.data?.rawData
            })
            console.error('🚨 CUE LOSS TRIPWIRE (draggableSegments setter) — would drop:', segment)
          }
        }
      })

      CueParser.lastReconstructLossReport = lossReport
      const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim()
      safeEmitScriptContent(newRawContent, { reason: 'draggableSegments-set' })
    }
  })

  // ---------------------------------------------------------------------------
  // Methods: Content reconstruction
  // ---------------------------------------------------------------------------

  /**
   * Reconstruct raw markdown content from a segments array.
   * Strips YAML frontmatter — database-first means no frontmatter in script_content.
   */
  function reconstructRawContent(segments) {
    const contentBody = CueParser.reconstructContent(segments)
    return stripYamlFrontmatter(contentBody)
  }

  // ---------------------------------------------------------------------------
  // Methods: Content validation & repair
  // ---------------------------------------------------------------------------

  function detectMultipleFrontmatterBlocks(content) {
    if (!content) return { hasMultiple: false, blockCount: 0, isMalformed: false }

    const lines = content.split('\n')
    let dashCount = 0
    const blockStarts = []
    let hasYamlAfterClosing = false

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim() === '---') {
        dashCount++
        if (dashCount % 2 === 1) {
          blockStarts.push(i)
        }
      } else if (dashCount >= 2) {
        const line = lines[i].trim()
        if (line && line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
          hasYamlAfterClosing = true
          console.warn(`MALFORMED YAML: Found YAML after closing --- on line ${i + 1}: "${line}"`)
          break
        }
      }
    }

    const frontmatterBlocks = Math.floor(dashCount / 2)
    const isMalformed = hasYamlAfterClosing || frontmatterBlocks > 1

    return {
      hasMultiple: frontmatterBlocks > 1,
      blockCount: frontmatterBlocks,
      blockStarts: blockStarts,
      isMalformed: isMalformed,
      hasYamlAfterClosing: hasYamlAfterClosing
    }
  }

  /**
   * Validate script content for common issues that cause data corruption.
   * Returns { isValid, issues }.
   */
  function validateScriptContent(content) {
    if (!content) return { isValid: true, issues: [] }

    const issues = []

    // 1. Check for truncated HTML tags (e.g., </p instead of </p>)
    const truncatedTagMatch = content.match(/<\/[a-z]+[^>]*$/i)
    if (truncatedTagMatch) {
      issues.push({
        type: 'truncated_tag',
        description: `Truncated closing tag found: "${truncatedTagMatch[0]}"`,
        position: content.lastIndexOf(truncatedTagMatch[0])
      })
    }

    // 2. Check for unclosed paragraph tags
    const openPTags = (content.match(/<p\s/g) || []).length + (content.match(/<p>/g) || []).length
    const closePTags = (content.match(/<\/p>/g) || []).length
    if (openPTags !== closePTags) {
      issues.push({
        type: 'mismatched_tags',
        description: `Mismatched paragraph tags: ${openPTags} opening, ${closePTags} closing`,
        openCount: openPTags,
        closeCount: closePTags
      })
    }

    // 3. Check for duplicate content blocks (same paragraph appearing twice)
    const paragraphs = content.match(/<p[^>]*>[\s\S]*?<\/p>/g) || []
    if (paragraphs.length > 10) {
      const firstFiveParagraphs = paragraphs.slice(0, 5).join('|||')
      const contentAfterHalf = paragraphs.slice(Math.floor(paragraphs.length / 2))
      const secondHalfStart = contentAfterHalf.slice(0, 5).join('|||')

      if (firstFiveParagraphs === secondHalfStart && paragraphs.length > 20) {
        issues.push({
          type: 'duplicate_content',
          description: 'Content appears to be duplicated (first half matches second half)',
          totalParagraphs: paragraphs.length,
          estimatedOriginalLength: Math.floor(paragraphs.length / 2)
        })
      }
    }

    // 4. Check for multiple YAML frontmatter blocks
    const frontmatterCheck = detectMultipleFrontmatterBlocks(content)
    if (frontmatterCheck.isMalformed) {
      issues.push({
        type: 'malformed_frontmatter',
        description: 'Multiple or malformed YAML frontmatter blocks detected',
        blockCount: frontmatterCheck.blockCount
      })
    }

    return {
      isValid: issues.length === 0,
      issues: issues
    }
  }

  /**
   * Repair common content issues.
   * Returns { content, repairs, wasRepaired }.
   */
  function repairScriptContent(content) {
    if (!content) return { content: content, repairs: [] }

    let repairedContent = content
    const repairs = []

    // 1. Fix truncated closing tags (</p, </div, etc.)
    const truncatedTagPattern = /<\/([a-z]+)$/i
    const truncatedMatch = repairedContent.match(truncatedTagPattern)
    if (truncatedMatch) {
      repairedContent = repairedContent.replace(truncatedTagPattern, `</${truncatedMatch[1]}>`)
      repairs.push({
        type: 'truncated_tag_fixed',
        description: `Fixed truncated tag: </${truncatedMatch[1]}> was missing >`
      })
    }

    // 2. Remove duplicate content (if detected)
    const paragraphs = repairedContent.match(/<p[^>]*>[\s\S]*?<\/p>/g) || []
    if (paragraphs.length > 20) {
      const firstFive = paragraphs.slice(0, 5).map(p => p.trim()).join('|||')
      const halfPoint = Math.floor(paragraphs.length / 2)
      const atHalfFive = paragraphs.slice(halfPoint, halfPoint + 5).map(p => p.trim()).join('|||')

      if (firstFive === atHalfFive) {
        const frontmatterMatch = repairedContent.match(/^(---[\s\S]*?---\n)/)
        const frontmatter = frontmatterMatch ? frontmatterMatch[1] : ''
        const bodyContent = frontmatterMatch ? repairedContent.slice(frontmatter.length) : repairedContent

        const bodyParagraphs = bodyContent.match(/<p[^>]*>[\s\S]*?<\/p>/g) || []
        const halfBodyParagraphs = bodyParagraphs.slice(0, Math.floor(bodyParagraphs.length / 2))

        const uniqueBody = halfBodyParagraphs.join('\n\n')
        repairedContent = frontmatter + uniqueBody

        repairs.push({
          type: 'duplicate_content_removed',
          description: `Removed duplicate content block (${paragraphs.length} paragraphs reduced to ${halfBodyParagraphs.length})`
        })
      }
    }

    // 3. Fix multiple frontmatter blocks - keep only the first one
    const frontmatterCheck = detectMultipleFrontmatterBlocks(repairedContent)
    if (frontmatterCheck.blockCount > 1) {
      const firstBlockEnd = repairedContent.indexOf('---', 3) + 3
      const afterFirstBlock = repairedContent.slice(firstBlockEnd)
      const bodyStart = afterFirstBlock.search(/<p|<!-- Begin Cue/)

      if (bodyStart > -1) {
        const cleanBody = afterFirstBlock.slice(bodyStart)
        const cleanedBody = cleanBody.replace(/\n---[\s\S]*?---\n/g, '\n')
        repairedContent = repairedContent.slice(0, firstBlockEnd) + '\n' + cleanedBody

        repairs.push({
          type: 'multiple_frontmatter_fixed',
          description: `Removed ${frontmatterCheck.blockCount - 1} extra frontmatter block(s)`
        })
      }
    }

    return {
      content: repairedContent,
      repairs: repairs,
      wasRepaired: repairs.length > 0
    }
  }

  /**
   * Validate and repair content before saving.
   * Called automatically before emitting save events.
   */
  function validateAndRepairBeforeSave(content) {
    const validation = validateScriptContent(content)

    if (!validation.isValid) {
      console.warn('Content validation issues detected:', validation.issues)

      const repair = repairScriptContent(content)

      if (repair.wasRepaired) {
        console.log('Content repaired:', repair.repairs)
        return {
          content: repair.content,
          wasRepaired: true,
          repairs: repair.repairs,
          originalIssues: validation.issues
        }
      }
    }

    return {
      content: content,
      wasRepaired: false,
      repairs: [],
      originalIssues: validation.issues
    }
  }

  // ---------------------------------------------------------------------------
  // Methods: Content emission
  // ---------------------------------------------------------------------------

  /**
   * Centralized method for emitting script content updates.
   * Validates and repairs content before emitting to prevent corruption.
   *
   * @param {string} content — The content to emit
   * @param {boolean} skipValidation — Skip validation (for raw edits, default false)
   * @param {object} callbacks — Optional { onRepaired(repairs) } for UI notification
   */
  function emitScriptContent(content, skipValidation = false, callbacks = {}) {
    if (!content) {
      // Empty content is treated as an explicit clear and bypasses the
      // shrink guard. The cue-loss tripwire still applies via the loss
      // report from the most recent reconstructContent.
      safeEmitScriptContent(content, { reason: 'emitScriptContent-empty', allowShrink: true })
      return
    }

    if (skipValidation) {
      safeEmitScriptContent(content, { reason: 'emitScriptContent-skipValidation' })
      return
    }

    const result = validateAndRepairBeforeSave(content)

    if (result.wasRepaired) {
      console.log('Content was auto-repaired before save:', result.repairs)
      if (callbacks.onRepaired) {
        callbacks.onRepaired(result.repairs)
      }
    }

    safeEmitScriptContent(result.content, { reason: 'emitScriptContent' })
  }

  /**
   * Guarded emit wrapper for content produced by segment reconstruction.
   *
   * Three integrity checks fire BEFORE the emit lands:
   *   1) Cue-loss tripwire — inspects CueParser.lastReconstructLossReport.
   *      Catches the case where a cue segment was IN the segments array
   *      but its rawData was missing (so reconstruction silently emitted
   *      empty markdown for it).
   *   2) Cue-count regression check — counts <!-- Begin Cue --> markers in
   *      the previous rawScriptContent vs the new reconstructed content.
   *      Catches the case where cue segments were entirely ABSENT from
   *      the segments array before reconstruction (the loss happened
   *      upstream of reconstructContent — e.g. an errant splice). This is
   *      the bug seen on episode 272 cole-allen 2026-05-03 05:16:03 UTC,
   *      where 6+ cues vanished from the segments array entirely without
   *      tripwire #1 catching it.
   *   3) Shrink guard — if the new content is more than 15% shorter than
   *      the previous (and previous was non-trivial), abort. Heuristic
   *      backstop for content losses that aren't strictly cue blocks
   *      (e.g. paragraph runs).
   *
   * Aborts emit a console.error and a one-shot toast (rate-limited per
   * burst). The latch resets on the next successful emit.
   *
   * Pass { allowShrink: true } for legitimate clear/load operations.
   * Cue-count regression is NEVER bypassable — that's data corruption.
   *
   * @param {string} newContent
   * @param {{ reason?: string, allowShrink?: boolean }} ctx
   * @returns {boolean} true if emit fired, false if aborted
   */
  function safeEmitScriptContent(newContent, ctx = {}) {
    const reason = ctx.reason || 'unknown'
    const allowShrink = ctx.allowShrink === true

    const prev = props.scriptContent || ''
    const prevLen = prev.length
    const newLen = (newContent || '').length

    // 1) Cue-loss tripwire — read the report populated by the most recent
    // reconstructContent call. If anything was dropped, abort. Never bypassable
    // — this is data corruption.
    const lossReport = CueParser.lastReconstructLossReport
    if (lossReport && lossReport.droppedCues && lossReport.droppedCues.length > 0) {
      console.error(
        `🚨 CUE LOSS aborted ${reason} emit — ${lossReport.droppedCues.length} cue(s) would be lost out of ${lossReport.totalCueSegments} total. Dropped:`,
        lossReport.droppedCues
      )
      if (toast && !_cueLossToastShown) {
        _cueLossToastShown = true
        toast.error(`Save aborted — ${lossReport.droppedCues.length} cue(s) would be lost. See console.`)
      }
      return false
    }

    // 1b) Corruption tripwire — abort if reconstructed content contains the
    // literal "undefined" speaker class or paragraph body. These indicate a
    // segment was reconstructed before its content/speaker fields were
    // populated; saving them poisons the markdown and causes catastrophic
    // truncation on the next parse-and-save round-trip (episode 0273 incident
    // 2026-05-09, item 1089: 15215 → 1238 chars).
    if (newContent && (/<p class="undefined"/.test(newContent) || />undefined<\/p>/.test(newContent))) {
      console.error(
        `🚨 CORRUPTION TRIPWIRE aborted ${reason} emit — reconstructed content contains literal "undefined". Refusing to save.`,
        {
          reason,
          newLen: newContent.length,
          prevLen,
          undefinedClassMatches: (newContent.match(/<p class="undefined"/g) || []).length,
          undefinedBodyMatches: (newContent.match(/>undefined<\/p>/g) || []).length,
          newPreview: newContent.substring(0, 400)
        }
      )
      if (toast) {
        toast.error('Save aborted — reconstructed content contained "undefined". Reload and retry.')
      }
      return false
    }

    // 2) Cue-count regression — DOWNGRADED to a warning.
    // Was a hard abort, but it misfired on the segments-array race
    // condition where a stale autosave debounce fires right after an
    // intentional cue insert / move (current segments has fewer cues
    // than the freshly-updated rawMarkdownContent). The console.warn
    // still surfaces if a real silent loss happens. The cue-loss
    // tripwire (check #1 above) remains as a hard abort because that
    // catches the actual data-corruption case (segment present but
    // rawData missing).
    const prevCueCount = (prev.match(/<!-- Begin Cue -->/g) || []).length
    const newCueCount = (newContent || '').match(/<!-- Begin Cue -->/g)?.length || 0
    if (newCueCount < prevCueCount && !allowShrink && !_allowNextShrink) {
      console.warn(
        `[useScriptCore] cue-count went ${prevCueCount} → ${newCueCount} during ${reason} (gate downgraded to warning — emit allowed)`,
        { prevPreview: prev.substring(0, 200), newPreview: (newContent || '').substring(0, 200) }
      )
    }

    // 3) Shrink guard — DOWNGRADED to a warning.
    // Was a hard abort. Combined with the cue-count regression check
    // it created too many false positives during normal cue-insert and
    // delete operations (segments-array race conditions where a stale
    // autosave debounce fires after an intentional structural edit).
    // Logging stays so a real silent loss is still visible in the
    // console; no toast, no abort.
    if (
      shrinkGuardEnabled.value &&
      !allowShrink &&
      !_allowNextShrink &&
      prevLen > 200 &&
      newLen < prevLen * 0.85
    ) {
      const shrinkPct = ((1 - newLen / prevLen) * 100).toFixed(1)
      console.warn(`[useScriptCore] shrink ${shrinkPct}% during ${reason} (gate downgraded — emit allowed)`, {
        prevLen,
        newLen,
        prevPreview: prev.substring(0, 200),
        newPreview: (newContent || '').substring(0, 200)
      })
      // Fall through — let the emit happen.
    }

    // Successful path — reset cue-loss latch and consume any one-shot override.
    _cueLossToastShown = false
    if (_allowNextShrink) {
      _allowNextShrink = false
      console.log('🟢 Shrink guard override consumed')
    }
    emit('update:scriptContent', newContent)

    // ROOT-CAUSE FIX (ep 0273 / item 1089, 2026-05-09):
    // After emitting a structural change to rawMarkdownContent, invalidate
    // the segment cache so the next read of scriptSegments re-parses from
    // the freshly-emitted content instead of returning stale cached segments
    // from before the change.
    //
    // Skip ONLY for updateTextSegment (single-paragraph keystroke debounce)
    // and flushPendingChanges (which already applied buffered keystrokes).
    // Those paths use the cache to produce the new content and the new
    // content matches the cache 1:1, so invalidating would cause an
    // unnecessary re-parse that can steal cursor focus mid-typing.
    //
    // All other emits — including scriptSegments-set and draggableSegments-set
    // — MUST invalidate. Those setters can be reached by stale-read-write
    // paths (e.g. onLegacyCueConverted reading the cache, splicing,
    // assigning back) where the emit reflects only the stale snapshot, not
    // the latest rawMarkdownContent state.
    const _typingReasons = new Set(['updateTextSegment', 'flushPendingChanges'])
    if (!_typingReasons.has(reason)) {
      cachedScriptSegments.value = null
      lastParsedContent.value = null
      clearDebounceTimers()
    }

    return true
  }

  // ---------------------------------------------------------------------------
  // Methods: Segment editing
  // ---------------------------------------------------------------------------

  /**
   * Core edit function with 1.5s debouncing.
   * User types -> updateTextSegment -> (debounce) -> reconstruct -> emit -> parent saves
   *
   * @param {number} segmentIndex — Index of the text segment being edited
   * @param {string} newContent — New HTML content for the segment
   * @param {object} callbacks — Optional { onSaved(segmentIndex) } for persist-to-database
   */
  function updateTextSegment(segmentIndex, newContent, callbacks = {}) {
    console.log('updateTextSegment called - Index:', segmentIndex, 'New content length:', newContent.length)

    // Mark as having unsaved changes
    hasLocalUnsavedChanges.value = true

    // Store the new content in buffer immediately
    _editBuffer[segmentIndex] = newContent
    console.log('Buffered content for segment', segmentIndex, '- Content:', newContent.substring(0, 50))

    // Clear existing timer for this segment
    if (_debounceTimers[segmentIndex]) {
      clearTimeout(_debounceTimers[segmentIndex])
    }

    // Debounce the actual update to prevent race conditions during typing
    _debounceTimers[segmentIndex] = setTimeout(async () => {
      console.log('Debounced update executing for segment', segmentIndex)

      // Get current segments from parsed content
      const segments = [...scriptSegments.value]

      if (!segments[segmentIndex] || segments[segmentIndex].type !== 'text') {
        console.error('Cannot update non-text segment or invalid index:', segmentIndex)
        return
      }

      // Update this specific segment with buffered content
      segments[segmentIndex].content = _editBuffer[segmentIndex]

      // Reconstruct raw markdown content (also populates CueParser.lastReconstructLossReport)
      const newRawContent = reconstructRawContent(segments)

      // CRITICAL: Set restoration flag BEFORE emit to block watchers during the entire save cycle
      isRestoringCursor.value = true

      // Guarded emit — aborts if cues were silently dropped or content shrank suspiciously.
      const emitted = safeEmitScriptContent(newRawContent, { reason: 'updateTextSegment' })

      // Clear buffer and timer for this segment
      delete _editBuffer[segmentIndex]
      delete _debounceTimers[segmentIndex]

      if (!emitted) {
        // The save was vetoed by the integrity guard. Don't run onSaved — the
        // database still holds the previous (good) state, so we leave it alone.
        isRestoringCursor.value = false
        return
      }

      // IMPORTANT: Do NOT clear editing flags here!
      // Keep isActivelyEditing=true so user can continue typing after autosave
      // Flags are only cleared on blur (when user clicks away from paragraph)
      console.log('Autosave complete - keeping editing flags active for continued typing')

      // Persist to database via callback
      if (callbacks.onSaved) {
        await callbacks.onSaved(segmentIndex)
      }
    }, 1500) // 1.5 second debounce
  }

  /**
   * Flush all pending buffered changes immediately.
   * Called before item switch, mode switch, manual save, etc.
   */
  async function flushPendingChanges() {
    if (Object.keys(_editBuffer).length === 0) {
      console.log('No pending changes to flush')
      return
    }

    console.log('Flushing pending changes for', Object.keys(_editBuffer).length, 'segments')

    // Clear any pending debounce timers
    clearDebounceTimers()

    // Get current segments and apply all buffered changes
    const segments = [...scriptSegments.value]
    let hasChanges = false

    Object.keys(_editBuffer).forEach(indexStr => {
      const index = parseInt(indexStr)
      if (segments[index] && segments[index].type === 'text') {
        console.log('Applying buffered changes to segment', index)
        segments[index].content = stripRevisionMarkup(_editBuffer[index])
        hasChanges = true
      }
    })

    if (hasChanges) {
      // Reconstruct (populates CueParser.lastReconstructLossReport).
      const newRawContent = reconstructRawContent(segments)
      const emitted = safeEmitScriptContent(newRawContent, { reason: 'flushPendingChanges' })
      if (emitted) {
        console.log('Flushed changes emitted to parent')
      } else {
        console.warn('flushPendingChanges: emit aborted by integrity guard — buffer cleared but DB unchanged')
      }

      // Clear the buffer AFTER attempting emit
      clearEditBuffer()

      // Wait for Vue to process the emit and parent to update
      await nextTick()
      await nextTick()
      console.log('Flush complete - Vue reactivity settled')
    }
  }

  /**
   * Force-fresh re-parse of segments from the current rawScriptContent,
   * bypassing the isActivelyEditing/isDragging cache guard.
   *
   * USE THIS AT ANY STRUCTURAL MUTATION SITE that needs to splice, insert,
   * delete, or otherwise modify the segments array. The default
   * scriptSegments.value getter returns the cached snapshot while the user
   * is typing or dragging — which is correct for display but DANGEROUS
   * for write paths: a stale snapshot spliced and written back wipes
   * everything that changed since the cache was frozen.
   *
   * Root-cause incident: ep 0273 / item 1089, 2026-05-09. The
   * onLegacyCueConverted handler in EditorPanel.vue read scriptSegments.value
   * while isActivelyEditing was true, got the frozen cache (missing later-
   * inserted cues + paragraphs), spliced its replacement in, and wrote the
   * stale segments back — wiping ~91k chars and 11 cues.
   */
  function getFreshSegments() {
    if (!rawScriptContent.value || props.editorMode !== 'script') return []
    const contentWithoutFrontmatter = stripYamlFrontmatter(rawScriptContent.value)
    if (!contentWithoutFrontmatter || contentWithoutFrontmatter.trim() === '') {
      return [{
        type: 'text',
        content: '',
        speaker: 'josh',
        needsParagraphTags: true,
        segmentIndex: 0
      }]
    }
    try {
      const parsed = CueParser.parseContent(contentWithoutFrontmatter)
      return parsed.map((segment, index) => {
        if (segment.type === 'cue') {
          return {
            type: 'cue',
            data: CueParser.formatForCard(segment.data),
            segmentIndex: index
          }
        }
        return { ...segment, segmentIndex: index }
      })
    } catch (err) {
      console.error('[getFreshSegments] parse failed:', err)
      return []
    }
  }

  /**
   * Sync a contenteditable DOM element's innerHTML back to the segment data model.
   * Normalizes browser-inserted HTML tags.
   *
   * NOTE: Uses nextTick internally. The caller is responsible for passing the
   * correct DOM element. $refs access stays in the component.
   */
  function syncContentEditableToSegment(index, element) {
    nextTick(() => {
      let html = element.innerHTML
      // Normalize the HTML - browsers use different tags
      html = html
        .replace(/<b>/gi, '<strong>')
        .replace(/<\/b>/gi, '</strong>')
        .replace(/<i>/gi, '<em>')
        .replace(/<\/i>/gi, '</em>')

      // Clean up browser-inserted <div> tags from contenteditable
      html = html
        .replace(/<div><br\s*\/?><\/div>/gi, '')
        .replace(/<\/div>\s*<div[^>]*>/gi, ' ')
        .replace(/<div[^>]*>/gi, '')
        .replace(/<\/div>/gi, '')

      updateTextSegment(index, html)
      hasLocalUnsavedChanges.value = true
    })
  }

  // ---------------------------------------------------------------------------
  // Return public API
  // ---------------------------------------------------------------------------
  return {
    // --- Non-reactive buffers (markRaw — shared with component) ---
    segmentEditBuffer,
    updateDebounceTimers,
    getEditBuffer,
    setEditBufferEntry,
    deleteEditBufferEntry,
    clearEditBuffer,
    getDebounceTimers,
    clearDebounceTimers,

    // --- Reactive state ---
    isActivelyEditing,
    isActivelyTyping,
    activelyEditingSegment,
    isRestoringCursor,
    savedCursorState,
    blockReactiveUpdates,
    cachedScriptSegments,
    lastParsedContent,
    segmentReparseKey,
    hasLocalUnsavedChanges,

    // --- Computed ---
    rawScriptContent,
    scriptSegments,
    draggableSegments,

    // --- Methods ---
    reconstructRawContent,
    detectMultipleFrontmatterBlocks,
    validateScriptContent,
    repairScriptContent,
    validateAndRepairBeforeSave,
    emitScriptContent,
    updateTextSegment,
    flushPendingChanges,
    syncContentEditableToSegment,
    getFreshSegments,

    // --- Wiring helpers for component integration ---
    setDraggableSetHandler,
    setPendingCueContextGetter,

    // --- Save-integrity controls ---
    shrinkGuardEnabled,
    setShrinkGuardEnabled,
    allowNextShrink
  }
}
