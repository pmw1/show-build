/**
 * Per-user preference cache backed by /api/user/prefs.
 *
 * Singleton: the cache is module-level so any component sees the same data.
 * Reads from cache; writes go to the API and update cache; falls through
 * to a caller-supplied default when the user has no override.
 *
 *   const { get, set, remove, hydrate, isReady } = useUserPrefs()
 *   const layout = get('dashboard.layout', DEFAULT_LAYOUT)
 *   await set('dashboard.layout', newLayout)
 *
 * Call hydrate() once after login (auth store does this). On logout,
 * call clearCache() to wipe.
 *
 * The reactive `cache` ref is exposed for components that want
 * `computed(() => useUserPrefs().get('foo', def))` style auto-updates.
 */
import { ref, readonly } from 'vue'
import axios from 'axios'

const PREFIX = '/api/user/prefs'

// Module-level shared state (singleton).
const cache = ref({})            // { key: value }
const isReady = ref(false)        // true after hydrate() resolves
let hydratePromise = null         // dedupes concurrent hydrate calls

// Write scope: 'user' (default) writes the current user's override.
// 'global' writes the global default (admin-only at the API layer).
// Set via setScope(); SettingsView toggles this when the admin flips
// the page-level "Editing for: Personal | Site-wide" switch.
const writeScope = ref('user')

function setScope(scope) {
  writeScope.value = (scope === 'global') ? 'global' : 'user'
}

function getScope() {
  return writeScope.value
}

function authHeaders() {
  const token = localStorage.getItem('auth-token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function hydrate() {
  if (hydratePromise) return hydratePromise
  hydratePromise = (async () => {
    try {
      const res = await axios.get(PREFIX, { headers: authHeaders() })
      cache.value = res.data || {}
      isReady.value = true
    } catch (err) {
      // 401 (logged out) → leave cache empty; other errors → log and continue
      if (err.response?.status !== 401) {
        console.warn('[useUserPrefs] hydrate failed:', err)
      }
      cache.value = {}
      isReady.value = false
    }
    return cache.value
  })()
  return hydratePromise
}

function clearCache() {
  cache.value = {}
  isReady.value = false
  hydratePromise = null
}

function get(key, defaultValue = null) {
  if (key in cache.value) return cache.value[key]
  return defaultValue
}

async function set(key, value, opts = {}) {
  const scope = opts.scope || writeScope.value
  const url = `${PREFIX}/${encodeURIComponent(key)}${scope === 'global' ? '?scope=global' : ''}`

  if (scope === 'global') {
    // Global writes target the global default row, not the user's
    // override. We still update the local cache when the user has NO
    // personal override for this key — otherwise the bound UI would
    // snap back to the previous default (the cache is what `get` reads).
    // If a personal override exists, leave it alone — it still wins.
    const hadOverride = key in cache.value
    if (!hadOverride) {
      cache.value = { ...cache.value, [key]: value }
    }
    try {
      await axios.put(url, { value },
        { headers: { ...authHeaders(), 'Content-Type': 'application/json' } })
      // Re-hydrate user-pref cache (best-effort, non-blocking) so any
      // out-of-band changes are reconciled.
      hydratePromise = null
      hydrate()
      return true
    } catch (err) {
      // Roll back the optimistic cache update on failure.
      if (!hadOverride) {
        const next = { ...cache.value }
        delete next[key]
        cache.value = next
      }
      console.warn(`[useUserPrefs] set("${key}", scope=global) failed:`, err)
      return false
    }
  }

  // Per-user scope — optimistic local update; rollback on failure.
  const prev = cache.value[key]
  cache.value = { ...cache.value, [key]: value }
  try {
    await axios.put(url, { value },
      { headers: { ...authHeaders(), 'Content-Type': 'application/json' } })
    return true
  } catch (err) {
    if (prev === undefined) {
      const next = { ...cache.value }
      delete next[key]
      cache.value = next
    } else {
      cache.value = { ...cache.value, [key]: prev }
    }
    console.warn(`[useUserPrefs] set("${key}") failed:`, err)
    return false
  }
}

async function remove(key, opts = {}) {
  const scope = opts.scope || writeScope.value
  const url = `${PREFIX}/${encodeURIComponent(key)}${scope === 'global' ? '?scope=global' : ''}`

  if (scope === 'global') {
    // Removing the global default. If the user had no personal override,
    // they're now seeing the in-code fallback — drop our cache mirror so
    // the UI reflects that.
    const hadGlobalEcho = key in cache.value && !cache.value._userOverrides_only_
    const prev = cache.value[key]
    try {
      await axios.delete(url, { headers: authHeaders() })
      hydratePromise = null
      const refreshed = await hydrate()
      // After re-hydrate, if the cache no longer has this key (it was
      // only an echo of the global value, not a personal override), good.
      // Otherwise leave the personal override alone — that's the desired
      // behavior since personal overrides survive global deletes.
      void refreshed
      return true
    } catch (err) {
      if (hadGlobalEcho) {
        cache.value = { ...cache.value, [key]: prev }
      }
      console.warn(`[useUserPrefs] remove("${key}", scope=global) failed:`, err)
      return false
    }
  }

  const prev = cache.value[key]
  if (prev !== undefined) {
    const next = { ...cache.value }
    delete next[key]
    cache.value = next
  }
  try {
    await axios.delete(url, { headers: authHeaders() })
    return true
  } catch (err) {
    if (prev !== undefined) {
      cache.value = { ...cache.value, [key]: prev }
    }
    console.warn(`[useUserPrefs] remove("${key}") failed:`, err)
    return false
  }
}

export function useUserPrefs() {
  return {
    cache: readonly(cache),
    isReady: readonly(isReady),
    writeScope: readonly(writeScope),
    setScope,
    getScope,
    hydrate,
    clearCache,
    get,
    set,
    remove,
  }
}
