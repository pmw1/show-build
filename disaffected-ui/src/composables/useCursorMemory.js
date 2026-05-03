/**
 * Remembered cursor positions per (episode, segment).
 *
 * Two tiers:
 *   - In-memory Map (capped at 200 entries) for instant per-tab reuse.
 *   - Per-user pref `editor.cursorMemory` (capped at 50 entries) so the
 *     same memory survives logout / login / different browsers. Writes
 *     are debounced 5 s so a typing spree doesn't hammer the API.
 *
 * On hydrate (auth store fires it after login) the in-memory Map is
 * pre-populated from the pref so the first segment switch already has
 * the data available.
 *
 *   const { save, get, clear, clearEpisode, hydrateFromPrefs, flush } = useCursorMemory()
 */
import { useUserPrefs } from './useUserPrefs'

const PREF_KEY = 'editor.cursorMemory'
const memory = new Map()           // tab-local cache
const MAX_ENTRIES = 200             // in-memory cap
const PERSIST_CAP = 50              // DB cap (smaller — last N most recent)
const PERSIST_DEBOUNCE_MS = 5000

let persistTimer = null
let dirty = false

function _key(episode, segment) {
  return `${String(episode || '')}:${String(segment || '')}`
}

function _schedulePersist() {
  dirty = true
  if (persistTimer) return
  persistTimer = setTimeout(() => {
    persistTimer = null
    if (!dirty) return
    dirty = false
    try {
      // Take the most recent PERSIST_CAP entries (Map preserves insertion
      // order; we re-insert on save to put newest at the end).
      const entries = [...memory.entries()]
      const tail = entries.slice(-PERSIST_CAP)
      const obj = {}
      for (const [k, v] of tail) obj[k] = v
      useUserPrefs().set(PREF_KEY, obj)
    } catch (e) {
      console.debug('cursor memory persist skipped:', e)
    }
  }, PERSIST_DEBOUNCE_MS)
}

function save(episode, segment, position) {
  if (!episode || !segment || !position) return
  const k = _key(episode, segment)
  memory.delete(k)
  memory.set(k, { ...position, savedAt: Date.now() })
  if (memory.size > MAX_ENTRIES) {
    const oldestKey = memory.keys().next().value
    memory.delete(oldestKey)
  }
  _schedulePersist()
}

function get(episode, segment) {
  if (!episode || !segment) return null
  return memory.get(_key(episode, segment)) || null
}

function clear(episode, segment) {
  memory.delete(_key(episode, segment))
  _schedulePersist()
}

function clearEpisode(episode) {
  const prefix = `${String(episode)}:`
  for (const k of [...memory.keys()]) {
    if (k.startsWith(prefix)) memory.delete(k)
  }
  _schedulePersist()
}

/** Force-write any pending debounced persist (call on logout / page unload). */
function flush() {
  if (persistTimer) {
    clearTimeout(persistTimer)
    persistTimer = null
  }
  if (!dirty) return
  dirty = false
  try {
    const entries = [...memory.entries()]
    const tail = entries.slice(-PERSIST_CAP)
    const obj = {}
    for (const [k, v] of tail) obj[k] = v
    useUserPrefs().set(PREF_KEY, obj)
  } catch { /* noop */ }
}

/**
 * Pull the persisted cursor map into the in-memory cache. Idempotent;
 * called automatically the first time `get` runs and may also be invoked
 * directly after login.
 */
let _hydrated = false
function hydrateFromPrefs() {
  if (_hydrated) return
  _hydrated = true
  try {
    const stored = useUserPrefs().get(PREF_KEY, null)
    if (stored && typeof stored === 'object') {
      for (const [k, v] of Object.entries(stored)) {
        if (v && typeof v === 'object') memory.set(k, v)
      }
    }
  } catch { /* noop */ }
}

// Persist any pending writes when the tab closes / refreshes.
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    if (dirty) flush()
  })
}

export function useCursorMemory() {
  // Lazy hydrate — first caller triggers the population from prefs.
  if (!_hydrated) hydrateFromPrefs()
  return { save, get, clear, clearEpisode, hydrateFromPrefs, flush }
}
