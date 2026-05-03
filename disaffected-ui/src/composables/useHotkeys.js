import { ref, reactive } from 'vue'

/**
 * Global hotkey registry.
 *
 * Any component can register hotkeys with `registerHotkeys(section, entries)`
 * and unregister with `unregisterHotkeys(section)`.
 *
 * The HotkeyModal reads from the shared registry to show all available shortcuts,
 * sorted so the current section's hotkeys appear first.
 */

// Shared reactive state (singleton across all imports)
const showModal = ref(false)
const registry = reactive({})       // { sectionName: [ { keys, description, category } ] }
const activeSection = ref(null)     // Which section the user is currently in

// Built-in global hotkeys that are always available
const GLOBAL_HOTKEYS = [
  { keys: 'Alt + 1', description: 'Toggle hotkey reference', category: 'Navigation' },
  { keys: 'Escape', description: 'Close modals / cancel action', category: 'Navigation' },
]

export function useHotkeys() {
  /**
   * Register hotkeys for a named section of the app.
   * Call from onMounted (or setup). Entries are an array of:
   *   { keys: 'Ctrl + S', description: 'Save all', category: 'Editing' }
   */
  function registerHotkeys(section, entries) {
    registry[section] = entries
  }

  /** Remove a section's hotkeys (call from onUnmounted). */
  function unregisterHotkeys(section) {
    delete registry[section]
  }

  /** Mark which section the user is currently viewing. */
  function setActiveSection(section) {
    activeSection.value = section
  }

  /** Toggle the hotkey modal open/closed. */
  function toggleModal() {
    showModal.value = !showModal.value
  }

  /**
   * Return all registered hotkeys grouped by section,
   * with the active section first, then globals, then the rest.
   */
  function getSortedHotkeys() {
    const groups = []

    // Active section first
    if (activeSection.value && registry[activeSection.value]) {
      groups.push({
        section: activeSection.value,
        active: true,
        entries: registry[activeSection.value]
      })
    }

    // Global hotkeys
    groups.push({
      section: 'Global',
      active: false,
      entries: GLOBAL_HOTKEYS
    })

    // Remaining sections alphabetically
    const remaining = Object.keys(registry)
      .filter(s => s !== activeSection.value)
      .sort()
    for (const section of remaining) {
      groups.push({
        section,
        active: false,
        entries: registry[section]
      })
    }

    return groups
  }

  return {
    showModal,
    activeSection,
    registry,
    registerHotkeys,
    unregisterHotkeys,
    setActiveSection,
    toggleModal,
    getSortedHotkeys
  }
}
