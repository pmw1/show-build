<template>
  <v-menu offset="6" location="bottom end" @update:model-value="onMenuToggle">
    <template #activator="{ props: activatorProps }">
      <v-btn
        v-bind="activatorProps"
        icon
        size="small"
        class="presence-btn"
        :title="`${onlineUsers.length} online`"
      >
        <v-icon size="20">mdi-account-multiple</v-icon>
        <v-badge
          v-if="onlineUsers.length > 0"
          color="success"
          :content="onlineUsers.length"
          floating
          offset-x="-2"
          offset-y="-2"
        />
      </v-btn>
    </template>

    <v-card min-width="240" max-width="320" class="presence-card">
      <v-card-title class="text-subtitle-2 d-flex align-center">
        <v-icon size="small" class="me-2">mdi-account-multiple</v-icon>
        People
        <v-spacer />
        <span class="text-caption text-grey">{{ onlineUsers.length }} online</span>
      </v-card-title>
      <v-divider />

      <!-- Mute notifications toggle (per-user pref) -->
      <div class="pa-2 px-3 mute-row d-flex align-center">
        <v-icon size="x-small" class="me-2" :color="muted ? 'error' : 'grey-darken-1'">
          {{ muted ? 'mdi-bell-off' : 'mdi-bell' }}
        </v-icon>
        <span class="text-caption flex-grow-1">
          {{ muted ? 'Notifications muted' : 'Notifications on' }}
        </span>
        <v-switch
          :model-value="muted"
          @update:model-value="setMuted"
          density="compact"
          hide-details
          color="error"
          class="mute-switch"
          inset
        />
      </div>
      <v-divider />
      <v-list density="compact" class="pa-0">
        <!-- Self row at the top — click jumps to profile editor -->
        <v-list-item
          v-if="selfUser"
          @click="goToProfile"
          class="presence-item presence-self"
        >
          <template #prepend>
            <v-avatar :color="selfUser.chip_color || 'primary'" size="28" class="presence-avatar">
              <v-img v-if="selfUser.profile_picture" :src="selfUser.profile_picture" />
              <span v-else class="text-caption text-white">{{ initials(selfUser) }}</span>
            </v-avatar>
          </template>
          <v-list-item-title class="text-body-2">
            {{ selfUser.display_name || selfUser.username }}
            <v-chip size="x-small" variant="tonal" color="primary" class="ms-1">You</v-chip>
          </v-list-item-title>
          <v-list-item-subtitle class="text-caption text-grey">
            <v-icon size="x-small">mdi-pencil-outline</v-icon>
            Edit profile
          </v-list-item-subtitle>
        </v-list-item>
        <v-divider v-if="selfUser" class="my-1" />

        <v-list-item
          v-for="u in others"
          :key="u.id"
          @click="$emit('compose-to', u)"
          class="presence-item"
        >
          <template #prepend>
            <v-avatar
              :color="u.chip_color || 'primary'"
              size="28"
              class="presence-avatar"
            >
              <v-img v-if="u.profile_picture" :src="u.profile_picture" />
              <span v-else class="text-caption text-white">{{ initials(u) }}</span>
            </v-avatar>
          </template>
          <v-list-item-title class="text-body-2">
            {{ u.display_name || u.username }}
            <v-icon
              size="8"
              :color="u.online ? 'success' : 'grey-lighten-1'"
              class="ms-1 presence-dot"
            >mdi-circle</v-icon>
          </v-list-item-title>
          <v-list-item-subtitle v-if="u.online && u.current_location" class="text-caption presence-location">
            <v-icon size="x-small" class="me-1">{{ locationIcon(u.current_location) }}</v-icon>
            {{ locationLabel(u.current_location) }}
          </v-list-item-subtitle>
          <v-list-item-subtitle v-else-if="!u.online && u.last_seen_at" class="text-caption">
            seen {{ relativeTime(u.last_seen_at) }}
          </v-list-item-subtitle>
          <template #append>
            <v-btn
              v-if="canJumpTo(u)"
              icon="mdi-arrow-right-circle-outline"
              size="x-small"
              variant="text"
              color="primary"
              :title="`Jump to ${u.display_name || u.username}'s location`"
              @click.stop="jumpTo(u)"
            />
          </template>
        </v-list-item>
        <v-list-item v-if="others.length === 0" class="text-center">
          <v-list-item-subtitle>No other users yet</v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
</template>

<script setup>
import { computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useMessages } from '@/composables/useMessages'
import { useUserPrefs } from '@/composables/useUserPrefs'

const messages = useMessages()
const router = useRouter()
const userPrefs = useUserPrefs()

const muted = computed({
  get: () => !!userPrefs.get('messages.notifications.muted', false),
  set: (v) => userPrefs.set('messages.notifications.muted', !!v)
})

function setMuted(v) {
  muted.value = !!v
}

// While the menu is open, refresh /api/users every 15s so presence dots
// and locations feel live. We also kick an immediate refetch on open.
let _liveTimer = null
function onMenuToggle(open) {
  if (open) {
    messages.fetchUsers()
    if (_liveTimer) clearInterval(_liveTimer)
    _liveTimer = setInterval(() => {
      if (!document.hidden) messages.fetchUsers()
    }, 15000)
  } else if (_liveTimer) {
    clearInterval(_liveTimer)
    _liveTimer = null
  }
}
const users = computed(() => messages.users.value)
const onlineUsers = computed(() => messages.onlineUsers.value)

const currentUserId = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user-data') || '{}')?.id || null
  } catch { return null }
})

const selfUser = computed(() => users.value.find(u => u.id === currentUserId.value) || null)
const others = computed(() => users.value.filter(u => u.id !== currentUserId.value))

function goToProfile() {
  router.push('/profile')
}

defineEmits(['compose-to'])

function initials(u) {
  const name = u.display_name || u.username || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return (parts[0]?.slice(0, 2) || '??').toUpperCase()
}

function locationIcon(loc) {
  if (!loc) return 'mdi-circle-outline'
  switch (loc.view) {
    case 'content-editor': return 'mdi-file-document-edit'
    case 'dashboard': return 'mdi-view-dashboard'
    case 'episodes': return 'mdi-television-classic'
    case 'whiteboard': return 'mdi-notebook-edit'
    case 'settings': return 'mdi-cog'
    default: return 'mdi-circle-outline'
  }
}

function locationLabel(loc) {
  if (!loc) return ''
  if (loc.view === 'content-editor') {
    let s = loc.episode_number ? `Editing ${loc.episode_number}` : 'Editing'
    if (loc.segment_title) s += ` — ${loc.segment_title}`
    return s
  }
  return loc.view ? loc.view.replace(/-/g, ' ') : ''
}

function canJumpTo(u) {
  const loc = u?.current_location
  return !!(u?.online && loc && loc.view === 'content-editor' && loc.episode_number)
}

function jumpTo(u) {
  const loc = u?.current_location
  if (!canJumpTo(u)) return
  const query = {}
  if (loc.segment_id) query.segment = loc.segment_id
  if (loc.mode) query.mode = loc.mode
  router.push({
    path: `/content-editor/${loc.episode_number}`,
    query
  })
}

onBeforeUnmount(() => {
  if (_liveTimer) {
    clearInterval(_liveTimer)
    _liveTimer = null
  }
})

function relativeTime(iso) {
  const t = new Date(iso).getTime()
  if (!t) return ''
  const sec = Math.max(1, Math.round((Date.now() - t) / 1000))
  if (sec < 60) return `${sec}s ago`
  const min = Math.round(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.round(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.round(hr / 24)
  return `${d}d ago`
}
</script>

<style scoped>
.presence-btn {
  margin-right: 4px;
}
.presence-card {
  background: #fff;
}
.presence-item {
  cursor: pointer;
}
.presence-item:hover {
  background: rgba(25, 118, 210, 0.04);
}
.presence-self {
  background: rgba(0, 0, 0, 0.02);
}
.mute-row {
  background: rgba(0, 0, 0, 0.015);
}
.mute-switch {
  flex: 0 0 auto;
}
.mute-switch :deep(.v-selection-control) {
  min-height: 24px;
}
.presence-avatar {
  font-weight: 600;
}
.presence-dot {
  vertical-align: middle;
  margin-bottom: 2px;
}
.presence-location {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 240px;
}
</style>
