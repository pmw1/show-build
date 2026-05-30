/**
 * useMediaModalKeyboard — keyboard shortcut handler for media-editing modals.
 *
 * Hosts the entire shortcut switch lifted from SotModal's
 * `setupKeyboardShortcuts` (lines 1779-2060). Each modal supplies the
 * actions it wants to bind via the options object; unsupplied actions
 * are silently ignored. SotModal binds everything; VoModal v1 binds a
 * subset and grows over time.
 *
 * Listens at document-level with capture=true so it preempts other
 * keyboard handlers (the focus trap also uses capture, but for Tab —
 * they coexist).
 *
 * Usage:
 *   const trim = useTrimmableMediaModal({ videoPlayerRef })
 *   const kbd = useMediaModalKeyboard({
 *     show: () => props.show,
 *     videoPlayerRef,
 *     trim,
 *     onSubmit: handleAddCue,
 *     onTake: performTakeAction,
 *     onPreviewIntoOut: trim.performPreviewAction,
 *     onDoubleEnterTake: handleDoubleEnterTake,
 *     onCutModeSelect: (mode) => selectCutMode(mode, true),
 *     onBrowseFile: triggerFileInput,
 *     onToggleHotkeys: () => { showHotkeys.value = !showHotkeys.value },
 *     onScrollToBottom: scrollToBottomOfModal,
 *     onEscape: handleEscapeKey,
 *     trimStartInputRef, trimEndInputRef,
 *     clippingMethod: trim.clippingMethod,
 *   })
 *   // on modal open:  kbd.install()
 *   // on modal close: kbd.uninstall()
 *
 * Self-cleans on component unmount.
 */
import { onBeforeUnmount } from 'vue'

export function useMediaModalKeyboard(options = {}) {
  const {
    show,              // () => boolean — gate so handler returns early when closed
    videoPlayerRef,
    trim,              // useTrimmableMediaModal instance
    // Action callbacks — all optional. Unsupplied means "ignore that key".
    onSubmit,
    onTake,
    onPreviewIntoOut,
    onDoubleEnterTake, // eslint-disable-line no-unused-vars -- accepted for backward-compat; double-Enter now handled by useDoubleEnterToSlug
    onCutModeSelect,
    onBrowseFile,
    onToggleHotkeys,
    onScrollToBottom,
    onEscape, // eslint-disable-line no-unused-vars -- accepted for backward-compat; ESC handled by useModalStack now
    // Refs to allow arrow-key passthrough in trim input fields
    trimStartInputRef,
    trimEndInputRef,
    // Mode state — was used for double-Enter TAKE gating; kept for
    // backward compatibility with callers, but no longer referenced.
    clippingMethod, // eslint-disable-line no-unused-vars
  } = options

  if (!show || typeof show !== 'function') {
    throw new Error('useMediaModalKeyboard: `show` must be a getter function')
  }
  if (!trim) {
    throw new Error('useMediaModalKeyboard: `trim` (useTrimmableMediaModal instance) is required')
  }

  let handler = null

  function _isTextInput(target) {
    return target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement
  }

  function _isTrimInput(target) {
    return target === trimStartInputRef?.value || target === trimEndInputRef?.value
  }

  function _shouldPassThroughInput(event) {
    if (!_isTextInput(event.target)) return true
    // Ctrl+Enter (TAKE)
    if (event.key === 'Enter' && event.ctrlKey) return true
    // Alt+Enter (Submit)
    if (event.key === 'Enter' && event.altKey) return true
    // Shift+Space (Preview)
    if (event.key === ' ' && event.shiftKey) return true
    // Arrow/Home/End in trim inputs
    if (_isTrimInput(event.target) &&
        ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) {
      return true
    }
    return false
  }

  function install() {
    if (handler) return
    handler = (event) => {
      if (!show()) return

      // ESC is handled by the global modal stack (useModalStack) via
      // registerModalEsc, not here. The composable used to own ESC, but
      // that conflicted with the app-wide LIFO modal stack — now we let
      // the stack route ESC to the topmost modal uniformly.
      if (event.key === 'Escape') return

      if (!_shouldPassThroughInput(event)) return

      // CRITICAL: prevent default for space to avoid page scroll, even
      // if no video is loaded yet. This must happen BEFORE the
      // videoPlayerRef check.
      if (event.key === ' ') {
        event.preventDefault()
        event.stopPropagation()
        event.stopImmediatePropagation()
      }

      // Ctrl+1 — toggle hotkeys sidebar. Works without a video loaded.
      if (event.key === '1' && event.ctrlKey) {
        event.preventDefault()
        event.stopPropagation()
        event.stopImmediatePropagation()
        if (onToggleHotkeys) onToggleHotkeys()
        return
      }

      if (!videoPlayerRef.value) return

      let handled = true

      switch (event.key) {
        case ' ':
          event.preventDefault()
          if (event.shiftKey) {
            if (onPreviewIntoOut) onPreviewIntoOut()
            else trim.performPreviewAction()
          } else {
            trim.performPlayPauseAction()
          }
          break

        case 'j':
        case 'J':
          event.preventDefault()
          trim.performStepBackSecond()
          break

        case 'k':
        case 'K':
          event.preventDefault()
          trim.performPlayPauseAction()
          break

        case 'l':
        case 'L':
          event.preventDefault()
          trim.performStepForwardSecond()
          break

        case 'ArrowLeft':
          event.preventDefault()
          if (event.ctrlKey) {
            trim.performJumpBackTenSeconds()
          } else if (event.shiftKey) {
            const v = videoPlayerRef.value
            if (v) v.currentTime = Math.max(0, v.currentTime - (10 / trim.currentFramerate.value))
          } else {
            trim.performStepBackFrame()
          }
          break

        case 'ArrowRight':
          event.preventDefault()
          if (event.ctrlKey) {
            trim.performJumpForwardTenSeconds()
          } else if (event.shiftKey) {
            const v = videoPlayerRef.value
            if (v) {
              const dur = v.duration || 0
              v.currentTime = Math.min(dur, v.currentTime + (10 / trim.currentFramerate.value))
            }
          } else {
            trim.performStepForwardFrame()
          }
          break

        case 'ArrowUp':
          event.preventDefault()
          trim.performJumpForwardTenSeconds()
          break

        case 'ArrowDown':
          event.preventDefault()
          trim.performJumpBackTenSeconds()
          break

        case 'i':
        case 'I':
          event.preventDefault()
          trim.performMarkInAction()
          break

        case 'o':
        case 'O':
          event.preventDefault()
          trim.performMarkOutAction()
          break

        case 'q':
        case 'Q':
          event.preventDefault()
          trim.performGoToInAction()
          break

        case 'w':
        case 'W':
          event.preventDefault()
          trim.performGoToOutAction()
          break

        case 'Enter':
          if (event.ctrlKey) {
            event.preventDefault()
            if (onTake) onTake()
          } else if (event.altKey) {
            event.preventDefault()
            if (onSubmit) onSubmit()
          } else {
            // Bare Enter (and Shift+Enter) — let through so the universal
            // useDoubleEnterToSlug composable can detect double-tap and
            // jump focus to the slug field. The old double-Enter→TAKE
            // behavior in individual-clips mode has been replaced with
            // jump-to-slug; Ctrl+Enter is the only way to TAKE now.
            handled = false
          }
          break

        case 't':
        case 'T':
          if (event.altKey) {
            event.preventDefault()
            trim.setThumbnailTimecode()
          } else {
            handled = false
          }
          break

        case '.':
          if (event.altKey) {
            event.preventDefault()
            trim.setThumbnailTimecode()
          } else {
            handled = false
          }
          break

        case '[':
          event.preventDefault()
          trim.decreasePlaybackSpeed()
          break

        case ']':
          event.preventDefault()
          trim.increasePlaybackSpeed()
          break

        case '\\':
          event.preventDefault()
          trim.resetPlaybackSpeed()
          break

        case 'PageDown':
          event.preventDefault()
          if (onScrollToBottom) onScrollToBottom()
          else handled = false
          break

        case 'n':
        case 'N':
          event.preventDefault()
          if (onCutModeSelect) onCutModeSelect('none')
          break

        case 's':
        case 'S':
          event.preventDefault()
          if (onCutModeSelect) onCutModeSelect('single-trim')
          break

        case 'm':
        case 'M':
          event.preventDefault()
          if (onCutModeSelect) onCutModeSelect('individual-clips')
          break

        case 'r':
        case 'R':
          event.preventDefault()
          if (onCutModeSelect) onCutModeSelect('removal')
          break

        case 'g':
        case 'G':
          event.preventDefault()
          if (onCutModeSelect) onCutModeSelect('montage')
          break

        case 'b':
        case 'B':
          event.preventDefault()
          if (onBrowseFile) onBrowseFile()
          break

        default:
          handled = false
          break
      }

      // Stop ALL keyboard events from propagating when modal is open and
      // the key was handled — prevents global shortcuts from firing.
      if (handled) {
        event.preventDefault()
        event.stopPropagation()
        event.stopImmediatePropagation()
      }
    }
    document.addEventListener('keydown', handler, true)
  }

  function uninstall() {
    if (!handler) return
    document.removeEventListener('keydown', handler, true)
    handler = null
  }

  onBeforeUnmount(uninstall)

  return { install, uninstall }
}
