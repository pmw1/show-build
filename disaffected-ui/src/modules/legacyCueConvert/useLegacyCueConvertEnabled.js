/**
 * useLegacyCueConvertEnabled
 *
 * Reads/writes the Legacy Cue Convert module's enabled flag from
 * localStorage so the editor and the Settings UI stay in sync without
 * a backend round-trip. Same pattern as the shrink-guard toggle in
 * useScriptCore.js.
 *
 * Default: ON. Per the approved plan, the module is on by default for
 * users with no prior preference.
 *
 * IMPORTANT (per Q5 in the plan): the toggle does NOT control whether
 * Auto Scrub flags legacy tokens — Auto Scrub keeps detecting them
 * regardless. The toggle only controls whether the "Convert to Cue"
 * button renders on the flag-note panel. When OFF, users still see
 * the red `***` flag and the flag-note popup; they just can't
 * one-click-convert.
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'

const LS_KEY = 'show-build:legacyCueConvertEnabled'

function readFromLocalStorage() {
  try {
    const v = localStorage.getItem(LS_KEY)
    if (v === null) return true
    return v === 'true'
  } catch (_e) {
    return true
  }
}

export function useLegacyCueConvertEnabled() {
  const enabled = ref(readFromLocalStorage())

  function setEnabled(v) {
    enabled.value = !!v
    try {
      localStorage.setItem(LS_KEY, enabled.value ? 'true' : 'false')
    } catch (_e) { /* ignore */ }
  }

  // Watch for changes from another tab (Settings UI in a separate tab,
  // for example). The 'storage' event fires when localStorage changes
  // in OTHER tabs — same-tab writes don't trigger it, which is what we
  // want (the local writer already updated `enabled.value`).
  function onStorageChange(e) {
    if (e.key === LS_KEY) {
      enabled.value = readFromLocalStorage()
    }
  }

  onMounted(() => {
    window.addEventListener('storage', onStorageChange)
  })
  onBeforeUnmount(() => {
    window.removeEventListener('storage', onStorageChange)
  })

  return { enabled, setEnabled }
}

export const LEGACY_CUE_CONVERT_LS_KEY = LS_KEY
