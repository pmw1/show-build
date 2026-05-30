/**
 * useMediaModalClips — multi-clip (take/remove/double-Enter) logic.
 *
 * Owns the actions; state (clips array, clipSlug, clipCounter,
 * clippingMethod) lives in useTrimmableMediaModal and is read/mutated
 * through the injected `trim` instance.
 *
 * Usage:
 *   const trim = useTrimmableMediaModal({ videoPlayerRef, toast })
 *   const clipSlugInputRef = ref(null)
 *   const clipsApi = useMediaModalClips({
 *     videoPlayerRef, trim, toast,
 *     clipSlugInputRef,
 *     locatorFlashColor,   // ref<string>
 *     slug,                // ref<string> — main slug for auto-generation
 *   })
 *
 * Reactive state for "needs attention" lives here (not in the trim
 * composable) because it's animation-specific UX, not media state.
 */
import { ref, nextTick } from 'vue'

export function useMediaModalClips(options = {}) {
  const {
    videoPlayerRef,
    trim,
    toast,
    clipSlugInputRef,
    locatorFlashColor,
    slug,
  } = options

  if (!trim) {
    throw new Error('useMediaModalClips: `trim` (useTrimmableMediaModal instance) is required')
  }
  if (!toast) {
    throw new Error('useMediaModalClips: `toast` (Vue Toastification instance) is required')
  }

  const { trimStart, trimEnd, clipSlug, clips, clipCounter, clippingMethod } = trim
  const { secondsToTimecode, timecodeToSeconds } = trim

  // Local "needs attention" state — feedback for failed double-Enter
  // attempts when no clip slug is set.
  const clipSlugNeedsAttention = ref(false)
  const pendingTakeOnSlug = ref(false)

  function handleTakeClip() {
    if (!trimStart.value || !trimEnd.value) {
      toast.warning('Please set both time start and time end')
      return
    }

    const startSec = timecodeToSeconds(trimStart.value)
    const endSec = timecodeToSeconds(trimEnd.value)

    if (endSec <= startSec) {
      toast.warning('Time end must be after time start')
      return
    }

    // Promote to frame-accurate timecodes if a video player exists
    let timeStartWithFrames = trimStart.value
    let timeEndWithFrames = trimEnd.value
    if (videoPlayerRef?.value) {
      if (trimStart.value.split(':').length < 4) {
        timeStartWithFrames = secondsToTimecode(startSec, true)
      }
      if (trimEnd.value.split(':').length < 4) {
        timeEndWithFrames = secondsToTimecode(endSec, true)
      }
    }

    // Auto-generate clip slug if empty
    let finalClipSlug = clipSlug.value.trim()
    if (!finalClipSlug) {
      const baseSlug = (slug?.value || '').trim() || 'clip'
      if (clippingMethod.value === 'individual-clips') {
        finalClipSlug = `${baseSlug}_CLIP_${clipCounter.value}`
        clipCounter.value++
      } else if (clippingMethod.value === 'montage') {
        finalClipSlug = `${baseSlug}_MONTAGE`
      }
    }

    clips.value.push({
      slug: finalClipSlug,
      time_start: timeStartWithFrames,
      time_end: timeEndWithFrames,
      duration_seconds: endSec - startSec,
      transcript: ''
    })

    toast.success(`Clip "${finalClipSlug}" added`)

    // Clear fields for next clip
    if (clippingMethod.value === 'individual-clips') {
      clipSlug.value = ''
    }
    // For montage, keep the slug

    trimStart.value = '00:00:00'
    trimEnd.value = '00:00:00'
  }

  function removeClip(index) {
    const removed = clips.value[index]
    if (!removed) return
    clips.value.splice(index, 1)
    toast.info(`Removed clip "${removed.slug}"`)
  }

  // Triple-blink the clip slug input with locator color
  async function blinkClipSlugInput() {
    const input = clipSlugInputRef?.value
    if (!input) return

    const flashColor = locatorFlashColor?.value || '#FF5722'
    const originalBorder = input.style.border
    const originalBoxShadow = input.style.boxShadow

    for (let i = 0; i < 3; i++) {
      input.style.border = `3px solid ${flashColor}`
      input.style.boxShadow = `0 0 15px ${flashColor}, 0 0 30px ${flashColor}80`
      await new Promise(resolve => setTimeout(resolve, 120))
      input.style.border = originalBorder || '1px solid #ddd'
      input.style.boxShadow = originalBoxShadow || 'none'
      await new Promise(resolve => setTimeout(resolve, 80))
    }
  }

  // Double-Enter TAKE — fires from the keyboard composable when in
  // individual-clips mode with two Enters within 400ms. Validates state
  // before delegating to handleTakeClip.
  async function handleDoubleEnterTake() {
    if (clippingMethod.value !== 'individual-clips') return false

    if (!trimStart.value || !trimEnd.value ||
        trimStart.value === '00:00:00' || trimEnd.value === '00:00:00') {
      toast.warning('Please set IN and OUT points first (I and O keys)')
      return false
    }

    const hasSlug = clipSlug.value.trim().length > 0
    if (!hasSlug) {
      clipSlugNeedsAttention.value = true
      pendingTakeOnSlug.value = true
      await blinkClipSlugInput()
      nextTick(() => {
        if (clipSlugInputRef?.value) {
          clipSlugInputRef.value.focus()
          clipSlugInputRef.value.select()
        }
      })
      toast.warning('Please enter a clip slug to TAKE')
      return false
    }

    handleTakeClip()
    return true
  }

  function handleClipSlugInput() {
    if (clipSlugNeedsAttention.value && clipSlug.value.trim().length > 0) {
      clipSlugNeedsAttention.value = false
    }
  }

  function handleClipSlugEnter(event) {
    if (pendingTakeOnSlug.value && clipSlug.value.trim().length > 0) {
      event.preventDefault()
      event.stopPropagation()
      pendingTakeOnSlug.value = false
      clipSlugNeedsAttention.value = false
      handleTakeClip()
      nextTick(() => {
        if (clipSlugInputRef?.value) clipSlugInputRef.value.blur()
      })
    }
  }

  return {
    // State
    clipSlugNeedsAttention,
    pendingTakeOnSlug,
    // Actions
    handleTakeClip,
    removeClip,
    blinkClipSlugInput,
    handleDoubleEnterTake,
    handleClipSlugInput,
    handleClipSlugEnter,
  }
}
