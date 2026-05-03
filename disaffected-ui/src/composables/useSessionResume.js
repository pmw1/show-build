/**
 * Records the user's "where I was" state so that on next login (or after
 * navigating away) they can be offered a one-click jump back to the exact
 * spot in the content editor.
 *
 *   const { recordLocation, getLastLocation, dismiss } = useSessionResume()
 *
 *   recordLocation({
 *     view: 'content-editor',
 *     episode_number: '0271',
 *     segment_id: 'asset-uuid-here',
 *     cursor: { paragraphIndex: 4, charOffset: 87 },
 *     mode: 'script'
 *   })
 *
 * Storage: `useUserPrefs` under key `session.last_location`. So the state
 * is per-user (DB-backed), follows the user across devices/browsers, and
 * obeys the same hydration lifecycle as everything else.
 *
 * Writes are debounced 1.5 s so cursor movement doesn't hammer the API.
 */
import axios from 'axios'
import { useUserPrefs } from './useUserPrefs'

const PREF_KEY = 'session.last_location'
const DEBOUNCE_MS = 1500

let pendingTimer = null
let pendingPayload = null
let lastShownKey = null  // dedupe the resume snackbar

function _authHeaders() {
  const token = localStorage.getItem('auth-token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function _flush() {
  if (!pendingPayload) return
  // Per-user pref (private — for "resume where you left off" snackbar).
  useUserPrefs().set(PREF_KEY, pendingPayload)
  // Public presence location (visible to other users via /api/users).
  // Strip any fields we don't want broadcast (e.g. cursor character offsets).
  const publicPayload = {
    view: pendingPayload.view,
    episode_number: pendingPayload.episode_number,
    segment_id: pendingPayload.segment_id,
    segment_title: pendingPayload.segment_title,
    mode: pendingPayload.mode,
  }
  axios.put('/api/users/me/location', publicPayload, {
    headers: { ..._authHeaders(), 'Content-Type': 'application/json' }
  }).catch(() => { /* best-effort; don't fail UX on this */ })
  pendingPayload = null
}

function recordLocation(payload) {
  if (!payload || typeof payload !== 'object') return
  pendingPayload = { ...payload, recorded_at: Date.now() }
  if (pendingTimer) clearTimeout(pendingTimer)
  pendingTimer = setTimeout(_flush, DEBOUNCE_MS)
}

/**
 * Return the most recently recorded location, or null if none exists or
 * the cache hasn't hydrated yet.
 */
function getLastLocation() {
  const v = useUserPrefs().get(PREF_KEY, null)
  return v && typeof v === 'object' ? v : null
}

/**
 * Did the user already see (or dismiss) the resume offer for this exact
 * location during this browser session? Prevents the snackbar from
 * re-popping every time the dashboard mounts.
 */
function hasBeenShown(loc) {
  if (!loc) return false
  const key = `${loc.view}:${loc.episode_number}:${loc.segment_id}`
  return key === lastShownKey
}

function markShown(loc) {
  if (!loc) return
  lastShownKey = `${loc.view}:${loc.episode_number}:${loc.segment_id}`
}

function dismiss() {
  // The current snapshot is now "consumed" — don't re-offer it this session.
  markShown(getLastLocation())
}

/**
 * Force-flush any pending debounced write (e.g. on logout or page unload).
 */
function flushNow() {
  if (pendingTimer) {
    clearTimeout(pendingTimer)
    pendingTimer = null
  }
  _flush()
}

export function useSessionResume() {
  return {
    recordLocation,
    getLastLocation,
    hasBeenShown,
    markShown,
    dismiss,
    flushNow,
  }
}
