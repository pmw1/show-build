/**
 * useDoubleEnterToSlug — universal "Enter Enter" → focus Slug field.
 *
 * Drop in a single line per modal:
 *
 *   const slugFieldRef = ref(null)
 *   useDoubleEnterToSlug(() => props.show, slugFieldRef)
 *
 * Behavior:
 *   - Document-level keydown listener (capture phase) gated to active modal.
 *   - Detects two Enters within 400ms.
 *   - Focuses and selects the slug field on the second Enter.
 *   - Skips if focus is ALREADY on the slug field (so users can press
 *     Enter normally to submit form when the slug field is active).
 *   - Skips if the second Enter arrived too slow OR if any non-Enter
 *     key arrived between the two Enters.
 *   - No-op if slugFieldRef is null (modal hasn't rendered yet).
 *
 * Self-installs/uninstalls based on the showGetter so multiple modals
 * coexist; only the topmost open modal's listener actually fires (the
 * showGetter check returns early for others).
 *
 * Plays nicely with:
 *   - useMediaModalKeyboard (which used to grab double-Enter for TAKE
 *     in SOT/VO individual-clips mode — that branch has been removed).
 *   - useModalStack (different key, no conflict).
 *   - useFocusTrap (Tab key only; no conflict).
 *
 * @param {() => boolean} showGetter — returns true when the modal is open.
 * @param {import('vue').Ref<HTMLElement | { focus: () => void, $el?: HTMLElement }>} slugFieldRef
 */
import { watch, onBeforeUnmount } from 'vue'

const THRESHOLD_MS = 400

export function useDoubleEnterToSlug(showGetter, slugFieldRef) {
  if (typeof showGetter !== 'function') {
    throw new Error('useDoubleEnterToSlug: showGetter must be a function returning boolean')
  }

  let handler = null
  let lastEnterTime = 0

  function _getInputEl(ref) {
    const v = ref?.value
    if (!v) return null
    // Vuetify component: focus is on .$el, but native input lives inside it
    if (v.$el) {
      return v.$el.querySelector('input, textarea') || v.$el
    }
    // Native element or composable returned a plain element
    return v
  }

  function _focusSlug() {
    const target = _getInputEl(slugFieldRef)
    if (!target) return
    try {
      target.focus()
      if (typeof target.select === 'function') target.select()
    } catch (_e) { /* noop */ }
  }

  function install() {
    if (handler) return
    handler = (event) => {
      if (!showGetter()) return
      if (event.key !== 'Enter') {
        // Any non-Enter resets the double-tap clock
        lastEnterTime = 0
        return
      }
      // Don't preempt Ctrl+Enter / Alt+Enter / Shift+Enter combos —
      // those have their own meanings (submit, take, etc.)
      if (event.ctrlKey || event.altKey || event.shiftKey || event.metaKey) {
        lastEnterTime = 0
        return
      }
      // If focus is already on the slug field, let the Enter through
      // (likely a form submit attempt). Reset clock so a second Enter
      // there doesn't re-trigger.
      const target = _getInputEl(slugFieldRef)
      if (target && document.activeElement === target) {
        lastEnterTime = 0
        return
      }

      const now = Date.now()
      const since = now - lastEnterTime
      if (since > 0 && since < THRESHOLD_MS) {
        // Double-Enter detected
        event.preventDefault()
        event.stopPropagation()
        _focusSlug()
        lastEnterTime = 0
      } else {
        lastEnterTime = now
      }
    }
    document.addEventListener('keydown', handler, true)
  }

  function uninstall() {
    if (!handler) return
    document.removeEventListener('keydown', handler, true)
    handler = null
    lastEnterTime = 0
  }

  // Install/uninstall based on show state
  const stopWatch = watch(showGetter, (open) => {
    if (open) install()
    else uninstall()
  }, { immediate: true })

  onBeforeUnmount(() => {
    uninstall()
    stopWatch()
  })

  return { install, uninstall }
}
