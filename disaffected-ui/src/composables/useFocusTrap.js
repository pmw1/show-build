/**
 * useFocusTrap — keep Tab/Shift+Tab focus cycling within a container.
 *
 * Used by SotModal and VoModal to prevent focus from escaping the
 * dialog (otherwise Tab can land on the background page's focusable
 * elements, which is disorienting in a media-editing context).
 *
 * Listens at the document level with capture=true so it intercepts
 * before component-level handlers. Coexists with modal-stack ESC
 * (different keys) and with the keyboard shortcut composable (this one
 * only handles Tab; the other handles the rest).
 *
 * Usage:
 *   const modalCardRef = ref(null)
 *   const focusTrap = useFocusTrap(modalCardRef)
 *   // on modal open:  focusTrap.install()
 *   // on modal close: focusTrap.uninstall()
 *
 * Self-cleans on component unmount as a safety net.
 *
 * @param {import('vue').Ref<HTMLElement|{$el:HTMLElement}>} containerRef
 * @returns {{ install: () => void, uninstall: () => void }}
 */
import { onBeforeUnmount } from 'vue'

const FOCUSABLE_SELECTORS = [
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"]):not([disabled])',
  'a[href]'
].join(', ')

export function useFocusTrap(containerRef) {
  if (!containerRef) {
    throw new Error('useFocusTrap: containerRef is required')
  }

  let handler = null

  function _getContainerEl() {
    const v = containerRef.value
    if (!v) return null
    return v.$el || v
  }

  function _getFocusable(modalEl) {
    const els = modalEl.querySelectorAll(FOCUSABLE_SELECTORS)
    return Array.from(els).filter(el => {
      return el.offsetParent !== null && !el.closest('[style*="display: none"]')
    })
  }

  function install() {
    if (handler) return
    handler = (e) => {
      if (e.key !== 'Tab') return
      const modalEl = _getContainerEl()
      if (!modalEl) return

      const focusable = _getFocusable(modalEl)
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      const currentFocus = document.activeElement
      const isInModal = modalEl.contains(currentFocus)

      if (!isInModal) {
        e.preventDefault()
        first.focus()
        return
      }

      if (e.shiftKey) {
        if (currentFocus === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (currentFocus === last) {
          e.preventDefault()
          first.focus()
        }
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
