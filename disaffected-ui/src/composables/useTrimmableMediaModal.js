/**
 * useTrimmableMediaModal — shared timeline-panel logic for SotModal and VoModal.
 *
 * Owns the state and actions that are identical between any "load a video,
 * scrub through it, mark in/out, trim, pick a thumbnail, play/preview"
 * modal. Does NOT own:
 *   - File upload (each modal posts to its own endpoint)
 *   - Waveform extraction (use ./useWaveform separately — kept generic)
 *   - Form submission shape (each cue type has its own payload)
 *   - Cut mode / multi-clip / clipping logic (SotModal-only)
 *   - Transcription (SotModal-only)
 *
 * Scope of this extract is intentionally narrow ("mid extract" per the
 * approved plan): video player control, trim state, playback navigation,
 * speed indicator, frame counter. Future work can pull file-upload and
 * form scaffolding in too if it becomes worthwhile.
 *
 * Usage:
 *   import { ref } from 'vue'
 *   import { useTrimmableMediaModal } from '@/composables/useTrimmableMediaModal'
 *
 *   const videoPlayerRef = ref(null)
 *   const trim = useTrimmableMediaModal({ videoPlayerRef })
 *   // template binds <video ref="videoPlayerRef"> and the buttons call
 *   // trim.performMarkInAction() etc.; timecodes are trim.currentTimecode etc.
 *
 * The parent owns the videoPlayerRef. The composable mutates the underlying
 * HTMLVideoElement via `videoPlayerRef.value.currentTime = ...`. No two-way
 * v-model coupling — the composable reads `currentTime` on demand and
 * writes when an action fires.
 */
import { ref, computed, onBeforeUnmount } from 'vue'

const PRESET_SPEEDS = [0.25, 0.5, 1.0, 1.5, 2.0, 4.0]

export function useTrimmableMediaModal(options = {}) {
  const {
    videoPlayerRef,
    defaultFramerate = 30,
    // Optional: pass a Vue Toastification instance so the composable can
    // emit styled mark-in / mark-out / preview-warning toasts itself.
    // If null (default), no toasts — callers can wire their own.
    toast = null,
    // Master flag: when true, the composable fires action toasts on
    // mark/preview/speed change. Independent from `toast` being present
    // so callers can wire `toast` without action toasts if desired.
    emitActionFeedback = true,
  } = options

  if (!videoPlayerRef) {
    throw new Error('useTrimmableMediaModal: videoPlayerRef is required (a Vue ref to the <video> element)')
  }

  const _shouldToast = () => emitActionFeedback && toast

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  // Trim points (display strings — HH:MM:SS or HH:MM:SS:FF format).
  const trimStart = ref('00:00:00')
  const trimEnd = ref('00:00:00')

  // Playback / display state
  const currentFramerate = ref(defaultFramerate)
  const isPlaying = ref(false)
  const currentTimecode = ref('00:00:00:00')
  const durationTimecode = ref('00:00:00:00')
  const remainingTimecode = ref('00:00:00:00')
  const duration = ref('') // user-entered duration string (legacy)

  // Preview-mode interval (auto-stop at OUT point)
  const previewInterval = ref(null)

  // Action feedback overlay (small text shown briefly after each action)
  const currentActionDisplay = ref('')

  // Thumbnail timecode (the moment the user marked for thumbnail extraction)
  const thumbnailTimecode = ref('')

  // Speed indicator state
  const playbackSpeed = ref(1.0)
  const showSpeedIndicator = ref(false)
  let speedIndicatorTimer = null

  // Frame-counter overlay state (briefly shows current frame / total frames
  // after a frame-step action)
  const showFrameCounter = ref(false)
  let frameCounterTimer = null
  const currentFrameNumber = ref(0)
  const totalFrames = ref(0)
  const frameStepDirection = ref('') // '+1f' / '-1s' / etc

  // Multi-clip workflow state. Owned here so both SotModal and VoModal
  // share a single source of truth. Modals (and useMediaModalClips) read
  // and mutate these. clippingMethod auto-switches from 'none' to
  // 'single-trim' on the first mark-in / mark-out action.
  // Valid values: 'none' | 'single-trim' | 'individual-clips' | 'removal' | 'montage'
  const clippingMethod = ref('none')
  const clipSlug = ref('')
  const clips = ref([])
  const clipCounter = ref(1)

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  /** Clip duration in seconds (out - in). Returns 0 if not both set. */
  const clipDuration = computed(() => {
    const startSec = timecodeToSeconds(trimStart.value)
    const endSec = timecodeToSeconds(trimEnd.value)
    if (endSec <= startSec) return 0
    return endSec - startSec
  })

  /** In-point as seconds — for binding to the waveform/scrubber's marker. */
  const inPointSeconds = computed(() => timecodeToSeconds(trimStart.value) || null)

  /** Out-point as seconds — same. */
  const outPointSeconds = computed(() => {
    const v = timecodeToSeconds(trimEnd.value)
    return v > 0 ? v : null
  })

  /** Human label for the current speed setting. */
  const speedLabel = computed(() => {
    const s = playbackSpeed.value
    if (s === 1.0) return 'Normal'
    if (s < 1.0) return `Slow ${s.toFixed(2)}×`
    return `Fast ${s.toFixed(2)}×`
  })

  // ---------------------------------------------------------------------------
  // Pure utility functions
  // ---------------------------------------------------------------------------

  function secondsToTimecode(seconds, showFrames = true) {
    if (!Number.isFinite(seconds) || seconds < 0) seconds = 0
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const frames = Math.floor((seconds % 1) * currentFramerate.value)
    const pad = (n) => n.toString().padStart(2, '0')
    if (showFrames) return `${pad(hours)}:${pad(minutes)}:${pad(secs)}:${pad(frames)}`
    return `${pad(hours)}:${pad(minutes)}:${pad(secs)}`
  }

  function timecodeToSeconds(timecode) {
    if (!timecode || typeof timecode !== 'string') return 0
    const parts = timecode.split(':').map(p => parseInt(p, 10))
    if (parts.some(p => Number.isNaN(p))) return 0
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if (parts.length === 4) {
      const frames = parts[3] / currentFramerate.value
      return parts[0] * 3600 + parts[1] * 60 + parts[2] + frames
    }
    return 0
  }

  function formatFileSize(bytes) {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  // ---------------------------------------------------------------------------
  // Button visual effects (used by the 3x8 control grid)
  // ---------------------------------------------------------------------------

  function getDarkerColor(color) {
    const hex = color.replace('#', '')
    const r = Math.max(0, parseInt(hex.substr(0, 2), 16) - 30)
    const g = Math.max(0, parseInt(hex.substr(2, 2), 16) - 30)
    const b = Math.max(0, parseInt(hex.substr(4, 2), 16) - 30)
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
  }

  function hoverButton(e, baseColor) {
    const darkerColor = getDarkerColor(baseColor)
    e.currentTarget.querySelectorAll('div').forEach((div, idx) => {
      if (idx === 0) div.style.background = getDarkerColor(darkerColor)
      else div.style.background = darkerColor
    })
    e.currentTarget.style.transform = 'scale(1.05)'
    e.currentTarget.style.zIndex = '100'
    e.currentTarget.style.boxShadow = `0 4px 12px ${baseColor}66`
  }

  function unhoverButton(e, baseColor) {
    const sections = e.currentTarget.querySelectorAll('div')
    if (sections.length >= 2) {
      sections[0].style.background = getDarkerColor(baseColor)
      sections[1].style.background = baseColor
    }
    e.currentTarget.style.transform = 'scale(1)'
    e.currentTarget.style.zIndex = '13'
    e.currentTarget.style.boxShadow = 'none'
  }

  function animateButtonPress(button) {
    if (!button) return
    button.style.transform = 'scale(0.95)'
    setTimeout(() => { button.style.transform = 'scale(1)' }, 100)
  }

  // ---------------------------------------------------------------------------
  // Mark / go-to actions
  // ---------------------------------------------------------------------------

  /**
   * Internal: switch from 'none' to 'single-trim' on first mark action.
   * Modal callers can opt out by setting clippingMethod themselves before
   * the user touches mark in/out (e.g. when restoring from initialData
   * for an edit).
   */
  function _autoSwitchToSingleTrim() {
    if (clippingMethod.value === 'none') {
      clippingMethod.value = 'single-trim'
      if (_shouldToast()) {
        toast('Clipping mode switched to SINGLE TRIM', {
          type: 'success',
          position: 'top-center',
          timeout: 2500,
          icon: '✂️'
        })
      }
    }
  }

  /** Mark current playback position as the IN point. */
  function performMarkInAction() {
    const v = videoPlayerRef.value
    if (!v) return
    trimStart.value = secondsToTimecode(v.currentTime)
    currentActionDisplay.value = `IN @ ${trimStart.value}`
    _autoSwitchToSingleTrim()
    if (_shouldToast()) {
      toast(`IN point set: ${trimStart.value}`, {
        type: 'info',
        position: 'top-left',
        timeout: 2000,
        toastClassName: 'mark-in-toast',
        icon: '◄'
      })
    }
  }

  /** Mark current playback position as the OUT point. */
  function performMarkOutAction() {
    const v = videoPlayerRef.value
    if (!v) return
    trimEnd.value = secondsToTimecode(v.currentTime)
    currentActionDisplay.value = `OUT @ ${trimEnd.value}`
    _autoSwitchToSingleTrim()
    if (_shouldToast()) {
      toast(`OUT point set: ${trimEnd.value}`, {
        type: 'info',
        position: 'top-right',
        timeout: 2000,
        toastClassName: 'mark-out-toast',
        icon: '►'
      })
    }
  }

  /** Seek to the IN point. */
  function performGoToInAction() {
    const v = videoPlayerRef.value
    if (!v) return
    v.currentTime = timecodeToSeconds(trimStart.value)
    currentActionDisplay.value = 'GO IN'
  }

  /** Seek to the OUT point. */
  function performGoToOutAction() {
    const v = videoPlayerRef.value
    if (!v) return
    v.currentTime = timecodeToSeconds(trimEnd.value)
    currentActionDisplay.value = 'GO OUT'
  }

  /**
   * Click on the waveform → seek to that time.
   * @param {number} timeSec
   */
  function handleWaveformSeek(timeSec) {
    const v = videoPlayerRef.value
    if (!v) return
    v.currentTime = timeSec
  }

  // ---------------------------------------------------------------------------
  // Play / pause / preview
  // ---------------------------------------------------------------------------

  function performPlayPauseAction() {
    const v = videoPlayerRef.value
    if (!v) return
    if (v.paused) {
      v.play()
      currentActionDisplay.value = 'PLAY'
    } else {
      v.pause()
      currentActionDisplay.value = 'PAUSE'
    }
    isPlaying.value = !v.paused
  }

  /** Play from IN to OUT, then auto-stop. */
  function performPreviewAction() {
    const v = videoPlayerRef.value
    if (!v) return
    const startSec = timecodeToSeconds(trimStart.value)
    const endSec = timecodeToSeconds(trimEnd.value)
    if (endSec <= startSec) {
      currentActionDisplay.value = 'PREVIEW (no range)'
      if (_shouldToast()) {
        toast.warning('Out point must be after In point', {
          position: 'top-center',
          timeout: 2500
        })
      }
      return
    }
    v.currentTime = startSec
    v.play()
    isPlaying.value = true
    currentActionDisplay.value = 'PREVIEW'
    if (previewInterval.value) clearInterval(previewInterval.value)
    previewInterval.value = setInterval(() => {
      if (!videoPlayerRef.value) {
        clearInterval(previewInterval.value)
        previewInterval.value = null
        return
      }
      if (videoPlayerRef.value.currentTime >= endSec) {
        videoPlayerRef.value.pause()
        isPlaying.value = false
        clearInterval(previewInterval.value)
        previewInterval.value = null
        currentActionDisplay.value = 'PREVIEW done'
      }
    }, 50)
  }

  // ---------------------------------------------------------------------------
  // Frame stepping
  // ---------------------------------------------------------------------------

  function _stepBy(deltaSec, label) {
    const v = videoPlayerRef.value
    if (!v) return
    if (!v.paused) v.pause()
    isPlaying.value = false
    v.currentTime = Math.max(0, Math.min(v.duration || 0, v.currentTime + deltaSec))
    currentActionDisplay.value = label
    showFrameCounterBriefly(label)
  }

  function performStepBackFrame()    { _stepBy(-1 / currentFramerate.value, '-1f') }
  function performStepForwardFrame() { _stepBy(+1 / currentFramerate.value, '+1f') }
  function performStepBackSecond()   { _stepBy(-1, '-1s') }
  function performStepForwardSecond() { _stepBy(+1, '+1s') }
  function performJumpBackTenSeconds()    { _stepBy(-10, '-10s') }
  function performJumpForwardTenSeconds() { _stepBy(+10, '+10s') }

  // ---------------------------------------------------------------------------
  // Thumbnail timecode
  // ---------------------------------------------------------------------------

  /** Mark the current playback time as the chosen thumbnail position. */
  function setThumbnailTimecode() {
    const v = videoPlayerRef.value
    if (!v) return
    thumbnailTimecode.value = secondsToTimecode(v.currentTime)
    currentActionDisplay.value = `Thumbnail @ ${thumbnailTimecode.value}`
  }

  // ---------------------------------------------------------------------------
  // Playback speed
  // ---------------------------------------------------------------------------

  function setPlaybackSpeed(speed) {
    const v = videoPlayerRef.value
    if (!v) return
    const clamped = Math.max(0.25, Math.min(4.0, speed))
    playbackSpeed.value = clamped
    v.playbackRate = clamped
    showSpeedIndicatorBriefly()
  }

  function increasePlaybackSpeed() {
    const cur = playbackSpeed.value
    const next = PRESET_SPEEDS.find(s => s > cur)
    if (next !== undefined) setPlaybackSpeed(next)
  }

  function decreasePlaybackSpeed() {
    const cur = playbackSpeed.value
    const candidates = PRESET_SPEEDS.filter(s => s < cur)
    if (candidates.length) setPlaybackSpeed(candidates[candidates.length - 1])
  }

  function resetPlaybackSpeed() {
    setPlaybackSpeed(1.0)
  }

  function showSpeedIndicatorBriefly() {
    showSpeedIndicator.value = true
    if (speedIndicatorTimer) clearTimeout(speedIndicatorTimer)
    speedIndicatorTimer = setTimeout(() => {
      showSpeedIndicator.value = false
      speedIndicatorTimer = null
    }, 2000)
  }

  // ---------------------------------------------------------------------------
  // Frame counter overlay
  // ---------------------------------------------------------------------------

  function showFrameCounterBriefly(direction) {
    const v = videoPlayerRef.value
    if (!v || !v.duration) return
    frameStepDirection.value = direction || ''
    currentFrameNumber.value = Math.floor(v.currentTime * currentFramerate.value)
    totalFrames.value = Math.floor(v.duration * currentFramerate.value)
    showFrameCounter.value = true
    if (frameCounterTimer) clearTimeout(frameCounterTimer)
    frameCounterTimer = setTimeout(() => {
      showFrameCounter.value = false
      frameCounterTimer = null
    }, 1500)
  }

  // ---------------------------------------------------------------------------
  // Live timecode update (called on the video element's timeupdate event)
  // ---------------------------------------------------------------------------

  function updateTimecode() {
    const v = videoPlayerRef.value
    if (!v) return
    const cur = v.currentTime || 0
    const dur = v.duration || 0
    currentTimecode.value = secondsToTimecode(cur)
    durationTimecode.value = secondsToTimecode(dur)
    remainingTimecode.value = secondsToTimecode(Math.max(0, dur - cur))
  }

  function updatePlayPauseState() {
    const v = videoPlayerRef.value
    if (!v) return
    isPlaying.value = !v.paused
  }

  // ---------------------------------------------------------------------------
  // Lifecycle cleanup
  // ---------------------------------------------------------------------------

  onBeforeUnmount(() => {
    if (previewInterval.value) {
      clearInterval(previewInterval.value)
      previewInterval.value = null
    }
    if (speedIndicatorTimer) {
      clearTimeout(speedIndicatorTimer)
      speedIndicatorTimer = null
    }
    if (frameCounterTimer) {
      clearTimeout(frameCounterTimer)
      frameCounterTimer = null
    }
  })

  // ---------------------------------------------------------------------------
  // Public surface
  // ---------------------------------------------------------------------------

  return {
    // State
    trimStart,
    trimEnd,
    duration,
    currentFramerate,
    isPlaying,
    currentTimecode,
    durationTimecode,
    remainingTimecode,
    previewInterval,
    currentActionDisplay,
    thumbnailTimecode,
    playbackSpeed,
    showSpeedIndicator,
    showFrameCounter,
    currentFrameNumber,
    totalFrames,
    frameStepDirection,

    // Multi-clip state (consumed by useMediaModalClips and the modals)
    clippingMethod,
    clipSlug,
    clips,
    clipCounter,

    // Computed
    clipDuration,
    inPointSeconds,
    outPointSeconds,
    speedLabel,

    // Pure utilities
    secondsToTimecode,
    timecodeToSeconds,
    formatFileSize,
    getDarkerColor,

    // UI feedback
    hoverButton,
    unhoverButton,
    animateButtonPress,

    // Mark / go-to
    performMarkInAction,
    performMarkOutAction,
    performGoToInAction,
    performGoToOutAction,
    handleWaveformSeek,

    // Play / pause / preview
    performPlayPauseAction,
    performPreviewAction,

    // Frame stepping
    performStepBackFrame,
    performStepForwardFrame,
    performStepBackSecond,
    performStepForwardSecond,
    performJumpBackTenSeconds,
    performJumpForwardTenSeconds,

    // Thumbnail
    setThumbnailTimecode,

    // Speed
    setPlaybackSpeed,
    increasePlaybackSpeed,
    decreasePlaybackSpeed,
    resetPlaybackSpeed,
    showSpeedIndicatorBriefly,

    // Frame counter
    showFrameCounterBriefly,

    // Live updates
    updateTimecode,
    updatePlayPauseState,
  }
}
