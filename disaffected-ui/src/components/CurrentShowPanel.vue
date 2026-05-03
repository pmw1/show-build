<template>
  <v-card class="current-show-panel" elevation="2">
    <v-card-title class="current-show-header dash-drag-handle bg-gradient-production text-white">
      <v-icon size="small" class="me-2">mdi-broadcast</v-icon>
      <span>Current Show</span>
    </v-card-title>

    <v-card-text v-if="loading" class="pa-2">
      <v-skeleton-loader type="list-item-avatar-two-line, actions" />
    </v-card-text>

    <v-card-text v-else-if="error" class="text-center pa-3">
      <v-icon color="grey" size="32" class="mb-1">mdi-alert-circle</v-icon>
      <p class="text-caption text-grey mb-0">{{ error }}</p>
    </v-card-text>

    <v-card-text v-else-if="!currentShow" class="text-center pa-3">
      <v-icon color="grey" size="40" class="mb-1">mdi-broadcast-off</v-icon>
      <p class="text-body-2 text-grey mb-0">No episode currently in production</p>
    </v-card-text>

    <v-card-text v-else class="pa-0">
      <div class="progress-status-bar" :style="{ backgroundColor: getStatusBgColor(currentShow.status) }">
        {{ currentShow.status?.toUpperCase() || 'PRODUCTION' }}
      </div>

      <div class="current-show-body pa-2">
        <div class="current-show-row">
          <div class="thumb-wrap">
            <v-img
              v-if="thumbnailUrl"
              :src="thumbnailUrl"
              :aspect-ratio="16/9"
              cover
              class="thumb-img"
            />
            <div v-else class="thumb-placeholder">
              <v-icon size="32" color="grey-lighten-1">mdi-image-off</v-icon>
            </div>
          </div>
          <div class="current-show-info min-width-0">
            <div class="current-show-title">{{ currentShow.title || 'Untitled Episode' }}</div>
            <div class="current-show-number">Episode {{ currentShow.number }}</div>
            <div class="info-line">
              <v-icon size="x-small" color="primary" class="me-1">mdi-calendar-star</v-icon>
              <span>{{ formatAirDate(currentShow.air_date) }}</span>
            </div>
          </div>
        </div>
      </div>

      <v-divider />
      <div class="pa-2">
        <v-btn
          block
          size="small"
          color="primary"
          variant="elevated"
          class="dash-row-btn"
          :to="`/content-editor/${currentShow.number}`"
          prepend-icon="mdi-pencil"
        >
          Edit Show
        </v-btn>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

const currentShow = ref(null)
const thumbnailUrl = ref(null)
const loading = ref(true)
const error = ref(null)
let refreshTimer = null

async function fetchCurrentShow() {
  try {
    loading.value = true
    error.value = null

    const response = await axios.get('/api/episodes')
    const raw = response.data?.episodes || response.data || []
    const real = raw.filter(e => !e.is_test_data)
    const inProduction = real.find(e => e.status === 'production')

    if (inProduction) {
      currentShow.value = {
        ...inProduction,
        air_date: inProduction.air_date || inProduction.airdate,
        number: inProduction.episode_number || inProduction.number
      }
      await fetchThumbnail(currentShow.value.number)
    } else {
      currentShow.value = null
      thumbnailUrl.value = null
    }
  } catch (err) {
    console.error('Error fetching current show:', err)
    error.value = 'Failed to load current show'
  } finally {
    loading.value = false
  }
}

async function fetchThumbnail(episodeNumber) {
  if (!episodeNumber) {
    thumbnailUrl.value = null
    return
  }
  try {
    const res = await axios.get(`/api/episodes/${episodeNumber}/thumbnail/confirmed`)
    thumbnailUrl.value = res.data?.thumbnail_url || res.data?.url || null
  } catch {
    thumbnailUrl.value = null
  }
}

function formatAirDate(dateString) {
  if (!dateString) return 'Not scheduled'
  return new Date(dateString).toLocaleDateString('en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
  })
}

function getStatusBgColor(status) {
  const map = {
    draft: '#757575',
    approved: '#43a047',
    production: '#fb8c00',
    completed: '#1976d2',
    promotion: '#8e24aa'
  }
  return map[status?.toLowerCase()] || '#fb8c00'
}

onMounted(() => {
  fetchCurrentShow()
  refreshTimer = setInterval(fetchCurrentShow, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.current-show-panel {
  height: 100%;
}

.current-show-header {
  display: flex;
  align-items: center;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  padding: 6px 10px !important;
  min-height: 0 !important;
  letter-spacing: 0.3px;
  cursor: move;
}

.bg-gradient-production {
  background: linear-gradient(135deg, #fb8c00 0%, #e65100 100%);
}

.progress-status-bar {
  width: 100%;
  color: #ffffff;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 1.2px;
  text-align: center;
  text-transform: uppercase;
  padding: 6px 0;
}

.current-show-body {
  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
}

.current-show-row {
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.thumb-wrap {
  flex: 0 0 120px;
  width: 120px;
}

.thumb-img {
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.thumb-placeholder {
  width: 120px;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.04);
  border: 1px dashed rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}

.current-show-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.min-width-0 {
  min-width: 0;
}

.current-show-title {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.current-show-number {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 2px;
}

.info-line {
  margin-top: 4px;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
}

.dash-row-btn {
  justify-content: flex-start !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-size: 0.8rem !important;
  min-height: 30px !important;
  height: 30px !important;
  padding: 0 10px !important;
}
</style>
