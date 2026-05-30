import { watch, onBeforeUnmount } from 'vue'

/**
 * useModalStack — global modal registry + ESC handler
 *
 * Problem this solves: show-build has 27 modals. ~21 implement their own
 * `document.addEventListener('keydown', handleEscape)` to close themselves on
 * ESC. The other ~6 don't, so ESC behavior is inconsistent. ContentEditor.vue
 * also has a central ESC-closes-all-modals handler — but only fires when a
 * modal owned by ContentEditor is open, leaving Settings/Dashboard/Profile
 * modals out in the cold.
 *
 * Approach: a single app-wide ESC handler (installed once from App.vue) walks
 * a LIFO stack of registered modals and closes the topmost one. Each modal
 * calls `register(closeFn)` when it opens and unregisters when it closes.
 * The handler stops propagation so per-modal handlers don't double-fire
 * during the migration.
 *
 * Usage in a modal:
 *   import { useModalStack } from '@/composables/useModalStack'
 *   const modalStack = useModalStack()
 *   watch(() => props.show, (open) => {
 *     if (open) modalStack.register(() => emit('update:show', false))
 *     else modalStack.unregisterTop()
 *   })
 *
 * Or simpler — let Vuetify's :model-value handle it if you can drop
 * :persistent. The global handler still acts as a fallback.
 */

const _stack = []
let _installed = false

function _onKeydown(event) {
  if (event.key !== 'Escape') return
  if (_stack.length === 0) return

  // Top of stack wins.
  const top = _stack[_stack.length - 1]
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  try {
    top.close()
  } catch (err) {
    console.warn('[modalStack] close handler threw:', err)
  }
}

export function installModalStackHandler() {
  if (_installed) return
  // capture=true so we win the race against per-modal listeners in the bubble
  // phase. They've been running for years; we want to be the new bottleneck.
  document.addEventListener('keydown', _onKeydown, true)
  _installed = true
}

export function uninstallModalStackHandler() {
  if (!_installed) return
  document.removeEventListener('keydown', _onKeydown, true)
  _installed = false
  _stack.length = 0
}

export function useModalStack() {
  function register(close, label = 'modal') {
    const entry = { close, label, id: Symbol(label) }
    _stack.push(entry)
    return entry.id
  }

  function unregister(id) {
    const idx = _stack.findIndex(e => e.id === id)
    if (idx >= 0) _stack.splice(idx, 1)
  }

  function unregisterTop() {
    _stack.pop()
  }

  function depth() {
    return _stack.length
  }

  return { register, unregister, unregisterTop, depth }
}

/**
 * registerModalEsc — one-liner helper for modals using the
 * `:model-value="show"` + `@update:show` pattern.
 *
 * Call from a modal's <script setup> like:
 *   registerModalEsc(() => props.show, () => emit('update:show', false), 'SotModal')
 *
 * Handles register-on-open, unregister-on-close, and cleanup on unmount.
 */
export function registerModalEsc(showGetter, closeFn, label = 'modal') {
  const stack = useModalStack()
  let id = null

  const stop = watch(
    showGetter,
    (open) => {
      if (open && id == null) {
        id = stack.register(closeFn, label)
      } else if (!open && id != null) {
        stack.unregister(id)
        id = null
      }
    },
    { immediate: true }
  )

  onBeforeUnmount(() => {
    if (id != null) stack.unregister(id)
    stop()
  })
}
