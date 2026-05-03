<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-bullhorn</v-icon>
      Announcements
    </v-card-title>

    <v-card-text>
      <v-list v-if="announcements.length > 0" density="compact">
        <v-list-item
          v-for="announcement in announcements"
          :key="announcement.id"
          @click="openAnnouncement(announcement)"
          class="announcement-item"
        >
          <template v-slot:prepend>
            <v-icon color="primary">mdi-file-document</v-icon>
          </template>

          <v-list-item-title>{{ announcement.title }}</v-list-item-title>
          <v-list-item-subtitle>{{ formatDate(announcement.date) }}</v-list-item-subtitle>

          <template v-slot:append>
            <v-icon size="small">mdi-chevron-right</v-icon>
          </template>
        </v-list-item>
      </v-list>

      <div v-else class="text-center text-grey py-4">
        No announcements available
      </div>
    </v-card-text>

    <!-- Announcement Modal -->
    <v-dialog
      v-model="showModal"
      max-width="75vw"
      max-height="75vh"
      scrollable
      @keydown.esc="closeModal"
    >
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>{{ selectedAnnouncement?.title }}</span>
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="closeModal"
          ></v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="announcement-content pa-6" style="max-height: 60vh; overflow-y: auto;">
          <div v-if="loading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </div>
          <div v-else-if="error" class="text-center text-error py-8">
            {{ error }}
          </div>
          <div v-else v-html="announcementContent"></div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="closeModal"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const announcements = ref([])
const showModal = ref(false)
const selectedAnnouncement = ref(null)
const announcementContent = ref('')
const loading = ref(false)
const error = ref(null)

function getToken() {
  return localStorage.getItem('auth-token') || localStorage.getItem('token')
}

async function loadAnnouncements() {
  try {
    const response = await fetch('/api/announcements/', {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) {
      announcements.value = await response.json()
    } else {
      console.error('Failed to load announcements:', response.statusText)
    }
  } catch (err) {
    console.error('Error loading announcements:', err)
  }
}

async function openAnnouncement(announcement) {
  selectedAnnouncement.value = announcement
  showModal.value = true
  loading.value = true
  error.value = null
  announcementContent.value = ''

  try {
    const response = await fetch(`/api/announcements/${announcement.id}`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) {
      const data = await response.json()
      announcementContent.value = data.content
    } else {
      error.value = 'Failed to load announcement content'
    }
  } catch (err) {
    console.error('Error loading announcement content:', err)
    error.value = 'Error loading announcement content'
  } finally {
    loading.value = false
  }
}

function closeModal() {
  showModal.value = false
  selectedAnnouncement.value = null
  announcementContent.value = ''
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric'
    })
  } catch {
    return dateStr
  }
}

onMounted(loadAnnouncements)
</script>

<style scoped>
.announcement-item {
  cursor: pointer;
  border-radius: 8px;
  margin-bottom: 4px;
}

.announcement-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.announcement-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
}

/* Style the rendered HTML content */
.announcement-content :deep(h1) {
  font-size: 2em;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
  color: rgb(var(--v-theme-primary));
}

.announcement-content :deep(h2) {
  font-size: 1.5em;
  margin-top: 1em;
  margin-bottom: 0.5em;
  color: rgb(var(--v-theme-primary));
}

.announcement-content :deep(h3) {
  font-size: 1.25em;
  margin-top: 0.8em;
  margin-bottom: 0.4em;
  color: rgb(var(--v-theme-primary));
}

.announcement-content :deep(ul) {
  margin-left: 1.5em;
  margin-bottom: 1em;
}

.announcement-content :deep(li) {
  margin-bottom: 0.5em;
}

.announcement-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.announcement-content :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
}

.announcement-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.announcement-content :deep(hr) {
  margin: 1.5em 0;
  border: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.announcement-content :deep(strong) {
  font-weight: 600;
}

.announcement-content :deep(p) {
  margin-bottom: 1em;
}
</style>
