/**
 * Tracks which preference keys are user-overridable.
 *
 * The map lives in a single global Settings row (key="pref_overridable",
 * user_id=NULL) and is loaded once per session. Components don't query
 * this directly — they use the <OverridableDot> wrapper, which calls
 * `isOverridable(key)` and shows the orange / green / red indicator.
 *
 *   const { isOverridable, hasOverride, hydrate, setOverridable } = useOverridableSettings()
 *
 * State machine for a key:
 *   - overridable: true,  user has no override   → 🟠 orange (can personalize)
 *   - overridable: true,  user has an override   → 🟢 green  (currently personal)
 *   - overridable: false                          → ⛔ red    (admin disallowed)
 *
 * `hydrate()` is called automatically the first time `isOverridable` is
 * invoked; it can also be called explicitly on app boot.
 */
import { ref, readonly } from 'vue'
import axios from 'axios'
import { useUserPrefs } from './useUserPrefs'

const META_URL = '/api/user/prefs/_metadata'

const metadata = ref({})           // { key: { overridable: bool, reason?: string } }
const isReady = ref(false)
let hydratePromise = null

function authHeaders() {
  const token = localStorage.getItem('auth-token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function hydrate() {
  if (hydratePromise) return hydratePromise
  hydratePromise = (async () => {
    try {
      const res = await axios.get(META_URL, { headers: authHeaders() })
      metadata.value = res.data || {}
      isReady.value = true
    } catch (err) {
      if (err.response?.status !== 401) {
        console.warn('[useOverridableSettings] hydrate failed:', err)
      }
      metadata.value = {}
      isReady.value = false
    }
    return metadata.value
  })()
  return hydratePromise
}

/**
 * Is this key allowed to be a per-user override?
 * Default for unknown keys is `true` — every key is overridable unless
 * an admin has explicitly flagged it otherwise.
 */
function isOverridable(key) {
  if (!isReady.value && !hydratePromise) hydrate()
  const entry = metadata.value[key]
  if (!entry) return true
  return entry.overridable !== false
}

/**
 * Optional admin reason text shown in the popover when overridable=false.
 */
function reasonFor(key) {
  return metadata.value[key]?.reason || ''
}

/**
 * Does the current user already have a personal value set for this key?
 */
function hasOverride(key) {
  const { cache } = useUserPrefs()
  return key in (cache.value || {})
}

/**
 * Admin-only: set whether a key is overridable. The popover surfaces this
 * when the current user has admin perms.
 */
async function setOverridable(key, overridable, reason) {
  try {
    const body = { overridable }
    if (reason) body.reason = reason
    await axios.put(`${META_URL}/${encodeURIComponent(key)}`, body,
      { headers: { ...authHeaders(), 'Content-Type': 'application/json' } })
    metadata.value = { ...metadata.value, [key]: { overridable, ...(reason ? { reason } : {}) } }
    return true
  } catch (err) {
    console.warn(`[useOverridableSettings] setOverridable("${key}") failed:`, err)
    return false
  }
}

function clearCache() {
  metadata.value = {}
  isReady.value = false
  hydratePromise = null
}

export function useOverridableSettings() {
  return {
    metadata: readonly(metadata),
    isReady: readonly(isReady),
    hydrate,
    clearCache,
    isOverridable,
    hasOverride,
    reasonFor,
    setOverridable,
  }
}
