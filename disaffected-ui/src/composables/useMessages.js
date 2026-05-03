/**
 * Inter-user messaging + presence client.
 *
 *   const {
 *     inbox, unreadCount, users,
 *     fetchInbox, fetchUsers, sendMessage, markRead, fetchThread,
 *     startPolling, stopPolling
 *   } = useMessages()
 *
 * Singleton: shared reactive state across the app. Polls every 30s for
 * inbox and 60s for the user directory while the tab is visible.
 */
import { ref, computed } from 'vue'
import axios from 'axios'

const inbox = ref([])
const unreadCount = ref(0)
const users = ref([])
const newMessage = ref(null)  // last freshly-received message (for toast triggering)

// Thread that the user is currently viewing in MessagesPanel — set by
// the panel via setActiveThread(senderUserId). Used to suppress toasts
// for messages the user is already looking at.
const activeViewingUserId = ref(null)
function setActiveThread(userId) { activeViewingUserId.value = userId || null }

let inboxTimer = null
let usersTimer = null
let visibilityHandler = null
let _seenIds = new Set()      // tracked IDs so we only "new-fire" once per message

const INBOX_POLL_MS = 30_000
const USERS_POLL_MS = 60_000

function authHeaders() {
  const token = localStorage.getItem('auth-token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function fetchInbox() {
  try {
    const res = await axios.get('/api/messages/inbox', { headers: authHeaders() })
    const fresh = res.data?.messages || []
    // Detect newly-arrived messages we haven't seen this session and weren't
    // sent BY the current user. The first fetch primes _seenIds without
    // firing toasts (so the user doesn't get an avalanche on login).
    const isPriming = _seenIds.size === 0
    let myId = null
    try {
      myId = JSON.parse(localStorage.getItem('user-data') || '{}')?.id || null
    } catch { /* noop */ }
    let latestNew = null
    for (const m of fresh) {
      if (_seenIds.has(m.id)) continue
      _seenIds.add(m.id)
      if (!isPriming && !m.read_at && m.from_user_id !== myId) {
        // Suppress toast if the user is already actively viewing this
        // sender's thread (the message will appear in the thread instead).
        if (activeViewingUserId.value && m.from_user_id === activeViewingUserId.value) continue
        latestNew = m  // remember the most recent so a single toast covers a burst
      }
    }
    inbox.value = fresh
    unreadCount.value = res.data?.unread_count || 0
    if (latestNew) newMessage.value = latestNew
  } catch (err) {
    if (err.response?.status !== 401) {
      console.warn('[useMessages] fetchInbox failed:', err)
    }
  }
}

async function fetchUsers() {
  try {
    const res = await axios.get('/api/users', { headers: authHeaders() })
    users.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    if (err.response?.status !== 401) {
      console.warn('[useMessages] fetchUsers failed:', err)
    }
  }
}

async function sendMessage({ to_user_id = null, content, reply_to = null }) {
  const res = await axios.post('/api/messages',
    { to_user_id, content, reply_to },
    { headers: { ...authHeaders(), 'Content-Type': 'application/json' } }
  )
  // Refresh inbox so the sender's own UI sees the message in the thread.
  fetchInbox()
  return res.data
}

async function markRead(messageId) {
  try {
    await axios.patch(`/api/messages/${messageId}/read`, {}, { headers: authHeaders() })
    // Optimistically update local cache without a full refetch.
    const m = inbox.value.find(x => x.id === messageId)
    if (m && !m.read_at) {
      m.read_at = new Date().toISOString()
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  } catch (err) {
    console.warn('[useMessages] markRead failed:', err)
  }
}

async function fetchThread(otherUserId) {
  try {
    const res = await axios.get(`/api/messages/thread/${otherUserId}`, { headers: authHeaders() })
    return Array.isArray(res.data) ? res.data : []
  } catch (err) {
    if (err.response?.status !== 401) {
      console.warn('[useMessages] fetchThread failed:', err)
    }
    return []
  }
}

function _onVisibilityChange() {
  if (document.hidden) return
  // Tab regained focus — refresh both immediately so the user sees fresh state.
  fetchInbox()
  fetchUsers()
}

function startPolling() {
  if (inboxTimer || usersTimer) return  // already running
  fetchInbox()
  fetchUsers()
  inboxTimer = setInterval(() => { if (!document.hidden) fetchInbox() }, INBOX_POLL_MS)
  usersTimer = setInterval(() => { if (!document.hidden) fetchUsers() }, USERS_POLL_MS)
  if (!visibilityHandler) {
    visibilityHandler = _onVisibilityChange
    document.addEventListener('visibilitychange', visibilityHandler)
  }
}

function stopPolling() {
  if (inboxTimer) { clearInterval(inboxTimer); inboxTimer = null }
  if (usersTimer) { clearInterval(usersTimer); usersTimer = null }
  if (visibilityHandler) {
    document.removeEventListener('visibilitychange', visibilityHandler)
    visibilityHandler = null
  }
  // Reset seen set so re-login (different user) primes fresh.
  _seenIds = new Set()
}

const onlineUsers = computed(() => users.value.filter(u => u.online))

export function useMessages() {
  return {
    inbox,
    unreadCount,
    users,
    onlineUsers,
    newMessage,
    fetchInbox,
    fetchUsers,
    fetchThread,
    sendMessage,
    markRead,
    startPolling,
    stopPolling,
    setActiveThread,
  }
}
