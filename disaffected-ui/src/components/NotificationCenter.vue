<template>
  <div class="notification-center">
    <!-- Notification Bell Icon -->
    <v-btn
      icon
      variant="text"
      @click="togglePanel"
      class="notification-bell"
    >
      <v-badge
        :content="unreadCount"
        :model-value="unreadCount > 0"
        color="error"
        overlap
      >
        <v-icon>mdi-bell{{ unreadCount > 0 ? '' : '-outline' }}</v-icon>
      </v-badge>
    </v-btn>

    <!-- Notification Panel -->
    <v-menu
      v-model="panelOpen"
      :close-on-content-click="false"
      location="bottom end"
      max-width="400"
      max-height="600"
      offset="8"
    >
      <template #activator="{ props }">
        <div v-bind="props" style="display: none;"></div>
      </template>

      <v-card class="notification-panel">
        <!-- Header -->
        <v-card-title class="notification-header d-flex align-center">
          <v-icon class="mr-2">mdi-bell</v-icon>
          <span>Notifications</span>
          <v-spacer></v-spacer>
          <v-chip
            v-if="unreadCount > 0"
            size="small"
            color="error"
            class="mr-2"
          >
            {{ unreadCount }}
          </v-chip>
          <v-btn
            icon
            size="small"
            variant="text"
            @click="clearAll"
            v-if="notifications.length > 0"
          >
            <v-icon size="small">mdi-delete-sweep</v-icon>
            <v-tooltip activator="parent" location="bottom">Clear All</v-tooltip>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <!-- Priority Filter -->
        <v-card-text class="pa-2">
          <v-chip-group
            v-model="priorityFilter"
            multiple
            selected-class="text-primary"
            density="compact"
            class="priority-filter"
          >
            <v-chip
              size="small"
              filter
              variant="outlined"
              value="critical"
              color="error"
            >
              Critical
            </v-chip>
            <v-chip
              size="small"
              filter
              variant="outlined"
              value="high"
              color="warning"
            >
              High
            </v-chip>
            <v-chip
              size="small"
              filter
              variant="outlined"
              value="normal"
              color="info"
            >
              Normal
            </v-chip>
            <v-chip
              size="small"
              filter
              variant="outlined"
              value="low"
              color="grey"
            >
              Low
            </v-chip>
          </v-chip-group>
        </v-card-text>

        <v-divider></v-divider>

        <!-- Notification List -->
        <v-list class="notification-list pa-0">
          <div v-if="filteredNotifications.length === 0" class="empty-state pa-4 text-center">
            <v-icon size="48" color="grey-lighten-1">mdi-bell-off-outline</v-icon>
            <div class="text-body-2 text-grey mt-2">No notifications</div>
          </div>

          <v-list-item
            v-for="notification in filteredNotifications"
            :key="notification.id"
            :class="[
              'notification-item',
              `priority-${notification.priority}`,
              { 'unread': !notification.read }
            ]"
            @click="markRead(notification.id)"
          >
            <!-- Priority Indicator -->
            <template #prepend>
              <v-icon
                :color="getPriorityColor(notification.priority)"
                size="small"
                class="priority-icon"
              >
                {{ getPriorityIcon(notification.priority) }}
              </v-icon>
            </template>

            <!-- Content -->
            <v-list-item-title class="notification-title">
              {{ notification.title }}
            </v-list-item-title>
            <v-list-item-subtitle class="notification-message">
              <div
                :class="['message-text', { 'message-expanded': notification.expanded }]"
                @click.stop="toggleExpanded(notification.id)"
              >
                {{ notification.message }}
              </div>
              <v-btn
                v-if="notification.message && notification.message.length > 60"
                variant="text"
                size="x-small"
                color="primary"
                class="expand-btn mt-1"
                @click.stop="toggleExpanded(notification.id)"
              >
                {{ notification.expanded ? 'Show less' : 'Show more' }}
                <v-icon size="x-small" class="ml-1">
                  {{ notification.expanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                </v-icon>
              </v-btn>
            </v-list-item-subtitle>

            <!-- Timestamp -->
            <div class="notification-time text-caption text-grey">
              {{ formatTime(notification.timestamp) }}
            </div>

            <!-- Success/Error Indicator -->
            <v-icon
              v-if="notification.success === true"
              color="success"
              size="small"
              class="status-icon"
            >
              mdi-check-circle
            </v-icon>
            <v-icon
              v-else-if="notification.success === false"
              color="error"
              size="small"
              class="status-icon"
            >
              mdi-alert-circle
            </v-icon>

            <!-- Dismiss Button -->
            <template #append>
              <v-btn
                icon
                size="x-small"
                variant="text"
                @click.stop="dismiss(notification.id)"
              >
                <v-icon size="small">mdi-close</v-icon>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useLLMState } from '@/composables/useLLMState'

const llmState = useLLMState()
const panelOpen = ref(false)
const priorityFilter = ref(['critical', 'high', 'normal', 'low'])
const notifications = llmState.notifications

// Toggle panel
function togglePanel() {
  panelOpen.value = !panelOpen.value
}

// Filtered notifications based on priority
const filteredNotifications = computed(() => {
  return llmState.notifications.filter(n =>
    priorityFilter.value.includes(n.priority)
  ).sort((a, b) => {
    // Sort by timestamp only - newest first (descending)
    return b.timestamp - a.timestamp
  })
})

// Unread count
const unreadCount = computed(() => llmState.unreadCount.value)

// Mark notification as read
function markRead(notificationId) {
  llmState.markAsRead(notificationId)
}

// Toggle expanded state
function toggleExpanded(notificationId) {
  const notification = llmState.notifications.find(n => n.id === notificationId)
  if (notification) {
    notification.expanded = !notification.expanded
  }
}

// Dismiss notification
function dismiss(notificationId) {
  llmState.dismissNotification(notificationId)
}

// Clear all notifications
function clearAll() {
  if (confirm('Clear all notifications?')) {
    llmState.clearAllNotifications()
  }
}

// Get priority color
function getPriorityColor(priority) {
  const colors = {
    critical: 'error',
    high: 'warning',
    normal: 'info',
    low: 'grey'
  }
  return colors[priority] || 'grey'
}

// Get priority icon
function getPriorityIcon(priority) {
  const icons = {
    critical: 'mdi-alert-octagon',
    high: 'mdi-alert',
    normal: 'mdi-information',
    low: 'mdi-chat-outline'
  }
  return icons[priority] || 'mdi-bell'
}

// Format timestamp
function formatTime(timestamp) {
  const now = Date.now()
  const diff = now - timestamp

  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`

  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
}

// Auto-mark as read when panel opens
watch(panelOpen, (isOpen) => {
  if (isOpen) {
    // Mark all as read after a short delay
    setTimeout(() => {
      llmState.notifications.forEach(n => {
        if (!n.read) {
          llmState.markAsRead(n.id)
        }
      })
    }, 1000)
  }
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-bell {
  margin-left: 8px;
}

.notification-panel {
  border-radius: 0 !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.notification-header {
  background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
  color: white;
  padding: 12px 16px;
  font-weight: 600;
}

.priority-filter {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  border-left: 4px solid transparent;
  transition: all 0.2s ease;
  position: relative;
  padding: 12px 16px;
}

.notification-item.unread {
  background: rgba(33, 150, 243, 0.05);
  font-weight: 500;
}

.notification-item.priority-critical {
  border-left-color: #F44336;
}

.notification-item.priority-high {
  border-left-color: #FF9800;
}

.notification-item.priority-normal {
  border-left-color: #2196F3;
}

.notification-item.priority-low {
  border-left-color: #9E9E9E;
}

.notification-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.priority-icon {
  margin-right: 8px;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  margin-bottom: 4px;
}

.message-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  transition: all 0.3s ease;
  word-wrap: break-word;
  word-break: break-word;
}

.message-text.message-expanded {
  -webkit-line-clamp: unset;
  display: block;
}

.expand-btn {
  text-transform: none;
  font-size: 11px;
  padding: 0 4px;
  height: 20px;
  min-width: auto;
}

.notification-time {
  font-size: 11px;
  opacity: 0.7;
}

.status-icon {
  position: absolute;
  bottom: 8px;
  right: 40px;
}

.empty-state {
  color: #9E9E9E;
}

/* Scrollbar styling */
.notification-list::-webkit-scrollbar {
  width: 6px;
}

.notification-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.notification-list::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.notification-list::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
