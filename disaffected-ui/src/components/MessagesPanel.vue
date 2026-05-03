<template>
  <span>
    <v-btn
      icon
      size="small"
      class="messages-btn"
      :title="`${unreadCount} unread`"
      @click="open = true"
    >
      <v-icon size="20">mdi-message-text-outline</v-icon>
      <v-badge
        v-if="unreadCount > 0"
        color="error"
        :content="unreadCount"
        floating
        offset-x="-2"
        offset-y="-2"
      />
    </v-btn>

    <v-dialog v-model="open" max-width="780" scrollable>
      <v-card class="messages-card d-flex flex-column" height="70vh">
        <v-card-title class="d-flex align-center pa-2 pl-4 messages-header">
          <v-icon class="me-2" size="small">mdi-message-text-outline</v-icon>
          <span class="text-subtitle-1">Messages</span>
          <v-chip v-if="unreadCount > 0" size="x-small" color="error" variant="flat" class="ms-2">
            {{ unreadCount }} unread
          </v-chip>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" size="small" @click="open = false" />
        </v-card-title>
        <v-divider />

        <v-card-text class="pa-0 d-flex flex-grow-1" style="overflow: hidden;">
          <!-- Left: thread list -->
          <div class="thread-list">
            <v-list density="compact" class="pa-0">
              <!-- Admin-only: broadcast to everyone -->
              <v-list-item
                v-if="isAdmin"
                @click="selectBroadcast"
                :active="isBroadcastActive"
                color="error"
                class="thread-item broadcast-item"
              >
                <template #prepend>
                  <v-avatar color="error" size="28">
                    <v-icon size="16" color="white">mdi-bullhorn</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2 font-weight-medium">
                  Broadcast
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  All users
                </v-list-item-subtitle>
              </v-list-item>
              <v-divider v-if="isAdmin" class="my-1" />

              <v-list-subheader>People</v-list-subheader>
              <v-list-item
                v-for="u in users"
                :key="u.id"
                @click="selectThread(u)"
                :active="activeUser?.id === u.id && !isBroadcastActive"
                color="primary"
                class="thread-item"
              >
                <template #prepend>
                  <v-avatar :color="u.chip_color || 'primary'" size="28">
                    <v-img v-if="u.profile_picture" :src="u.profile_picture" />
                    <span v-else class="text-caption text-white">{{ initials(u) }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ u.display_name || u.username }}
                  <v-icon size="8" :color="u.online ? 'success' : 'grey-lighten-1'">mdi-circle</v-icon>
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </div>

          <v-divider vertical />

          <!-- Right: active thread (DM or broadcast composer) -->
          <div class="thread-pane d-flex flex-column">
            <div v-if="!activeUser && !isBroadcastActive" class="inbox-overview d-flex flex-column">
              <div class="thread-header pa-2 px-3">
                <v-icon class="me-2" size="small">mdi-inbox</v-icon>
                <span class="text-subtitle-2">Recent messages</span>
                <v-spacer />
                <v-chip v-if="unreadCount > 0" size="x-small" color="error" variant="flat" class="me-2">
                  {{ unreadCount }} unread
                </v-chip>
                <v-btn
                  v-if="unreadCount > 0"
                  size="x-small"
                  variant="text"
                  prepend-icon="mdi-email-open-outline"
                  :loading="markingAllRead"
                  @click="markAllRead"
                >
                  Mark all read
                </v-btn>
              </div>
              <v-divider />
              <div class="inbox-feed flex-grow-1 pa-2">
                <div v-if="inbox.length === 0" class="empty-state">
                  <v-icon size="48" color="grey-lighten-1">mdi-message-outline</v-icon>
                  <p class="text-body-2 text-grey">No messages yet — pick a person on the left to say hi.</p>
                </div>
                <v-list v-else density="compact" class="pa-0">
                  <v-list-item
                    v-for="m in inbox.slice(0, 12)"
                    :key="m.id"
                    @click="openFromInbox(m)"
                    :class="{ 'inbox-unread': !m.read_at && m.from_user_id !== currentUserId }"
                    class="inbox-item"
                  >
                    <template #prepend>
                      <v-avatar
                        :color="senderChipColor(m)"
                        size="32"
                      >
                        <span class="text-caption text-white">{{ senderInitials(m) }}</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="text-body-2 d-flex align-center">
                      <span>{{ m.from_display || m.from_username || 'Unknown' }}</span>
                      <v-chip v-if="m.to_user_id === null" size="x-small" color="error" variant="tonal" class="ms-2">
                        Broadcast
                      </v-chip>
                      <v-icon
                        v-if="!m.read_at && m.from_user_id !== currentUserId"
                        size="8"
                        color="error"
                        class="ms-2"
                      >mdi-circle</v-icon>
                      <v-spacer />
                      <span class="text-caption text-grey">{{ relativeTime(m.sent_at) }}</span>
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-caption inbox-preview">
                      {{ m.content }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>
            </div>

            <!-- Broadcast composer (admin-only) -->
            <template v-else-if="isBroadcastActive">
              <div class="thread-header pa-2 px-3 broadcast-header">
                <v-avatar color="error" size="28" class="me-2">
                  <v-icon size="16" color="white">mdi-bullhorn</v-icon>
                </v-avatar>
                <span class="text-subtitle-2 text-error">Broadcast to all users</span>
              </div>
              <v-divider />
              <div class="thread-messages flex-grow-1 pa-4">
                <v-alert type="warning" variant="tonal" density="compact" class="mb-3">
                  This message goes to <strong>every</strong> active user. They'll see it
                  in their inbox and a toast on their screen if they're online.
                </v-alert>
                <div class="text-caption text-grey-darken-1">
                  Use sparingly — broadcasts can't be recalled.
                </div>
              </div>
              <v-divider />
              <div class="thread-compose pa-2">
                <v-textarea
                  v-model="draft"
                  placeholder="What do you want to broadcast?"
                  variant="outlined"
                  density="compact"
                  hide-details
                  rows="3"
                  auto-grow
                  :disabled="sending"
                  autofocus
                />
                <div class="d-flex justify-end mt-2">
                  <v-btn
                    color="error"
                    variant="elevated"
                    prepend-icon="mdi-bullhorn"
                    :disabled="!draft.trim() || sending"
                    :loading="sending"
                    @click="onSendBroadcast"
                  >
                    Send broadcast
                  </v-btn>
                </div>
              </div>
            </template>

            <!-- Direct-message thread -->
            <template v-else>
              <div class="thread-header pa-2 px-3">
                <v-avatar :color="activeUser.chip_color || 'primary'" size="28" class="me-2">
                  <v-img v-if="activeUser.profile_picture" :src="activeUser.profile_picture" />
                  <span v-else class="text-caption text-white">{{ initials(activeUser) }}</span>
                </v-avatar>
                <span class="text-subtitle-2">{{ activeUser.display_name || activeUser.username }}</span>
                <v-icon size="8" :color="activeUser.online ? 'success' : 'grey-lighten-1'" class="ms-1">mdi-circle</v-icon>
              </div>
              <v-divider />
              <div class="thread-messages flex-grow-1 pa-3" ref="threadScrollRef">
                <div
                  v-for="m in thread"
                  :key="m.id"
                  class="msg-row"
                  :class="{ 'msg-mine': m.from_user_id === currentUserId }"
                >
                  <div class="msg-bubble">
                    <div class="msg-content">{{ m.content }}</div>
                    <div class="msg-meta">{{ formatTime(m.sent_at) }}</div>
                  </div>
                </div>
                <div v-if="thread.length === 0" class="text-center text-grey text-caption mt-4">
                  No messages yet — say hi.
                </div>
              </div>
              <v-divider />
              <div class="thread-compose pa-2">
                <v-text-field
                  v-model="draft"
                  placeholder="Type a message…"
                  variant="outlined"
                  density="compact"
                  hide-details
                  @keydown.enter="onSend"
                  :disabled="sending"
                  autofocus
                >
                  <template #append-inner>
                    <v-btn
                      icon="mdi-send"
                      size="small"
                      variant="text"
                      color="primary"
                      :disabled="!draft.trim() || sending"
                      @click="onSend"
                    />
                  </template>
                </v-text-field>
              </div>
            </template>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </span>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useMessages } from '@/composables/useMessages'

const messages = useMessages()
const open = ref(false)
const activeUser = ref(null)
const isBroadcastActive = ref(false)
const thread = ref([])
const draft = ref('')
const sending = ref(false)
const markingAllRead = ref(false)
const threadScrollRef = ref(null)

const users = computed(() => messages.users.value)
const inbox = computed(() => messages.inbox.value)
const unreadCount = computed(() => messages.unreadCount.value)
const currentUserId = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user-data') || '{}')
    return u.id || null
  } catch {
    return null
  }
})

const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user-data') || '{}')
    if (u.is_admin || u.is_superuser) return true
    if (u.access_level === 'admin') return true
    if (typeof u.role === 'string' && u.role.toLowerCase().includes('admin')) return true
    if (Array.isArray(u.roles) && u.roles.some(r => String(r).toLowerCase().includes('admin'))) return true
    if (Array.isArray(u.permissions) && (u.permissions.includes('admin.*') || u.permissions.includes('*'))) return true
  } catch { /* noop */ }
  return false
})

function selectBroadcast() {
  isBroadcastActive.value = true
  activeUser.value = null
  messages.setActiveThread(null)
  thread.value = []
  draft.value = ''
}

async function onSendBroadcast() {
  const content = draft.value.trim()
  if (!content || sending.value) return
  if (!confirm('Send this message to ALL active users? This cannot be undone.')) return
  sending.value = true
  try {
    await messages.sendMessage({ to_user_id: null, content })
    draft.value = ''
    isBroadcastActive.value = false
  } catch (err) {
    console.warn('Broadcast send failed:', err)
    alert('Broadcast failed — see console.')
  } finally {
    sending.value = false
  }
}

defineExpose({
  composeTo(user) {
    open.value = true
    selectThread(user)
  }
})

async function selectThread(user) {
  isBroadcastActive.value = false
  activeUser.value = user
  messages.setActiveThread(user?.id || null)
  thread.value = await messages.fetchThread(user.id)
  await nextTick()
  scrollToBottom()
  // Mark any unread inbox messages from this user as read.
  for (const m of messages.inbox.value) {
    if (!m.read_at && m.from_user_id === user.id) {
      messages.markRead(m.id)
    }
  }
}

async function onSend() {
  const content = draft.value.trim()
  if (!content || !activeUser.value || sending.value) return
  sending.value = true
  try {
    const msg = await messages.sendMessage({ to_user_id: activeUser.value.id, content })
    thread.value = [...thread.value, msg]
    draft.value = ''
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.warn('Send failed:', err)
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  const el = threadScrollRef.value
  if (el) el.scrollTop = el.scrollHeight
}

function initials(u) {
  const name = u.display_name || u.username || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return (parts[0]?.slice(0, 2) || '??').toUpperCase()
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', month: 'short', day: 'numeric' })
}

function relativeTime(iso) {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  if (!t) return ''
  const sec = Math.max(1, Math.round((Date.now() - t) / 1000))
  if (sec < 60) return `${sec}s`
  const min = Math.round(sec / 60)
  if (min < 60) return `${min}m`
  const hr = Math.round(min / 60)
  if (hr < 24) return `${hr}h`
  const d = Math.round(hr / 24)
  return `${d}d`
}

function senderChipColor(m) {
  const u = users.value.find(x => x.id === m.from_user_id)
  return u?.chip_color || (m.to_user_id === null ? 'error' : 'primary')
}

function senderInitials(m) {
  const name = m.from_display || m.from_username || '?'
  const parts = String(name).trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return (parts[0]?.slice(0, 2) || '??').toUpperCase()
}

async function markAllRead() {
  markingAllRead.value = true
  try {
    const myId = currentUserId.value
    // Mark every unread message that's NOT from me. Run in parallel.
    const targets = inbox.value.filter(m => !m.read_at && m.from_user_id !== myId)
    await Promise.all(targets.map(m => messages.markRead(m.id)))
  } catch (err) {
    console.warn('mark all read failed:', err)
  } finally {
    markingAllRead.value = false
  }
}

function openFromInbox(m) {
  // Click on a feed row → open that sender's thread (or for broadcasts,
  // just mark read — there's no thread to open).
  if (m.to_user_id === null) {
    if (!m.read_at) messages.markRead(m.id)
    return
  }
  const sender = users.value.find(u => u.id === m.from_user_id)
  if (sender) selectThread(sender)
}

// Refresh inbox when the dialog opens; clear active-thread tracking on close.
watch(open, (v) => {
  if (v) {
    messages.fetchInbox()
  } else {
    messages.setActiveThread(null)
  }
})

// Live-update an open thread when new messages arrive in the inbox.
// Avoids a manual refresh when chatting with someone in real time.
watch(() => messages.inbox.value, (fresh) => {
  if (!activeUser.value || isBroadcastActive.value) return
  const knownIds = new Set(thread.value.map(m => m.id))
  let added = false
  for (const m of fresh) {
    if (knownIds.has(m.id)) continue
    // Only append messages that belong to the active conversation.
    const involvesActive = (m.from_user_id === activeUser.value.id && m.to_user_id === currentUserId.value)
                        || (m.from_user_id === currentUserId.value && m.to_user_id === activeUser.value.id)
    if (involvesActive) {
      thread.value.push(m)
      added = true
      // Auto-mark read since the user is actively viewing this thread.
      if (!m.read_at && m.from_user_id === activeUser.value.id) {
        messages.markRead(m.id)
      }
    }
  }
  if (added) {
    // Sort by sent_at to keep proper order if messages arrive out of sequence.
    thread.value.sort((a, b) => new Date(a.sent_at) - new Date(b.sent_at))
    nextTick(() => scrollToBottom())
  }
}, { deep: true })
</script>

<style scoped>
.messages-btn {
  margin-right: 4px;
}
.messages-card {
  background: #fafafa;
}
.messages-header {
  background: #fff;
}
.thread-list {
  width: 220px;
  min-width: 220px;
  background: #fff;
  overflow-y: auto;
}
.thread-item {
  cursor: pointer;
}
.broadcast-item {
  background: rgba(244, 67, 54, 0.04);
}
.broadcast-header {
  background: rgba(244, 67, 54, 0.06);
}
.thread-pane {
  flex: 1;
  background: #fafafa;
  min-width: 0;
}
.thread-header {
  display: flex;
  align-items: center;
  background: #fff;
}
.thread-messages {
  overflow-y: auto;
}
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.inbox-overview {
  flex: 1;
  background: #fff;
  min-width: 0;
}
.inbox-feed {
  overflow-y: auto;
}
.inbox-item {
  cursor: pointer;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.inbox-item:hover {
  background: rgba(25, 118, 210, 0.04);
}
.inbox-item.inbox-unread {
  background: rgba(244, 67, 54, 0.04);
}
.inbox-preview {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgba(0, 0, 0, 0.65);
}
.msg-row {
  display: flex;
  margin-bottom: 8px;
}
.msg-row.msg-mine {
  justify-content: flex-end;
}
.msg-bubble {
  max-width: 70%;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 6px 10px;
}
.msg-mine .msg-bubble {
  background: #1976D2;
  border-color: #1976D2;
  color: #fff;
}
.msg-content {
  font-size: 0.88rem;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-meta {
  font-size: 0.65rem;
  opacity: 0.7;
  margin-top: 2px;
  text-align: right;
}
.thread-compose {
  background: #fff;
}
</style>
