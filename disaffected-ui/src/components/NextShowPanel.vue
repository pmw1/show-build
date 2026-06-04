<template>
  <v-card class="next-show-panel" elevation="2">
    <v-card-title class="next-show-title bg-gradient-primary text-white">
      <v-icon size="small" class="me-2">mdi-clock-fast</v-icon>
      <span>Next Show</span>
      <v-spacer />
      <LiveClock v-if="nextShow" />
    </v-card-title>

    <v-card-text v-if="loading" class="pa-2">
      <v-skeleton-loader type="article, actions" />
    </v-card-text>

    <v-card-text v-else-if="error" class="text-center pa-3">
      <v-icon color="grey" size="32" class="mb-1">mdi-alert-circle</v-icon>
      <p class="text-caption text-grey mb-0">{{ error }}</p>
    </v-card-text>

    <v-card-text v-else-if="!nextShow" class="text-center pa-3">
      <v-icon color="grey" size="40" class="mb-1">mdi-calendar-clock</v-icon>
      <p class="text-body-2 text-grey mb-2">No upcoming show scheduled</p>
      <v-btn block size="small" color="primary" variant="outlined" @click="$router.push('/tools')">
        Create New Episode
      </v-btn>
    </v-card-text>

    <v-card-text v-else class="pa-0">
      <!-- Dummy Episode Banner -->
      <div v-if="nextShow.is_dummy" class="dummy-banner-large">
        <v-icon size="small" class="me-2">mdi-alert</v-icon>
        DUMMY EPISODE - FOR TESTING ONLY
      </div>

      <!-- Full-width progress status bar (workflow stage: draft/approved/production/completed) -->
      <div class="progress-status-bar" :style="{ backgroundColor: getStatusBgColor(nextShow.status) }">
        {{ nextShow.status?.toUpperCase() || 'DRAFT' }}
      </div>

      <!-- Episode Header -->
      <div class="episode-header pa-2">
        <div class="min-width-0 mb-2">
          <div class="next-show-overline">{{ formatDaysUntil(nextShow.air_date) }}</div>
          <div class="next-show-title">{{ nextShow.title || 'Untitled Episode' }}</div>
          <div class="next-show-number">Episode {{ nextShow.number }}</div>
          <div v-if="nextShow.subtitle" class="text-caption text-grey">{{ nextShow.subtitle }}</div>
        </div>

        <!-- Air Date + Total Duration side-by-side -->
        <div class="info-row-pair">
          <div class="info-row info-row-half">
            <v-icon size="small" color="primary" class="me-2">mdi-calendar-star</v-icon>
            <div class="info-content">
              <div class="info-label">Air Date</div>
              <div class="info-value">{{ formatAirDate(nextShow.air_date) }}</div>
              <div class="info-hint">{{ formatTimeUntil(nextShow.air_date) }}</div>
            </div>
          </div>

          <div v-if="nextShow.duration" class="info-row info-row-half">
            <v-icon size="small" color="primary" class="me-2">mdi-timer</v-icon>
            <div class="info-content">
              <div class="info-label">Total Duration</div>
              <div class="info-value">{{ nextShow.duration }}</div>
            </div>
          </div>
        </div>

        <div v-if="nextShow.guest" class="info-row">
          <v-icon size="small" color="primary" class="me-2">mdi-account</v-icon>
          <div class="info-content">
            <div class="info-label">Guest</div>
            <div class="info-value">{{ nextShow.guest }}</div>
          </div>
        </div>

        <div v-if="nextShow.description" class="info-row">
          <v-icon size="small" color="primary" class="me-2">mdi-text</v-icon>
          <div class="info-content">
            <div class="info-label">Description</div>
            <div class="info-desc">{{ nextShow.description }}</div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <v-divider />
      <div class="pa-2">
        <v-btn
          block
          size="small"
          color="primary"
          variant="elevated"
          class="dash-row-btn mb-1"
          :to="`/content-editor/${nextShow.number}`"
          prepend-icon="mdi-pencil"
        >
          Edit Show
        </v-btn>
        <v-btn
          block
          size="small"
          color="grey"
          variant="outlined"
          class="dash-row-btn"
          disabled
          prepend-icon="mdi-clock-outline"
        >
          Timing &amp; Stack
        </v-btn>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import axios from 'axios'
import LiveClock from './LiveClock.vue'
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'

const theme = useTheme()

const nextShow = ref(null)
const loading = ref(true)
const error = ref(null)

async function fetchNextShow() {
  try {
    loading.value = true
    error.value = null

    const response = await axios.get('/api/episodes', {
      params: { status: 'all', sort_by: 'air_date', sort_order: 'asc', limit: 10 }
    })

    const episodes = response.data?.episodes || response.data || []

    if (episodes.length > 0) {
      const today = new Date()
      today.setHours(0, 0, 0, 0)

      const upcoming = episodes.find(ep => {
        const dateField = ep.air_date || ep.airdate
        if (!dateField) return false
        const airDate = new Date(dateField)
        airDate.setHours(0, 0, 0, 0)
        return airDate >= today
      })

      if (upcoming) {
        nextShow.value = {
          ...upcoming,
          air_date: upcoming.air_date || upcoming.airdate,
          number: upcoming.episode_number || upcoming.number
        }

        try {
          await axios.get(`/api/episodes/${nextShow.value.number}/statistics`)
        } catch (statsError) {
          console.warn('Could not fetch episode statistics:', statsError)
        }
      } else {
        error.value = 'No upcoming episodes scheduled'
      }
    } else {
      error.value = 'No episodes found'
    }
  } catch (err) {
    console.error('Error fetching next show:', err)
    error.value = 'Failed to load next show information'
  } finally {
    loading.value = false
  }
}

function formatAirDate(dateString) {
  if (!dateString) return 'Not scheduled'
  return new Date(dateString).toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })
}

function formatDaysUntil(dateString) {
  if (!dateString) return 'Not scheduled'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const airDate = new Date(dateString)
  airDate.setHours(0, 0, 0, 0)
  const diffDays = Math.ceil((airDate - today) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'AIRING TODAY'
  if (diffDays === 1) return 'AIRING TOMORROW'
  if (diffDays < 0) return `AIRED ${Math.abs(diffDays)} DAYS AGO`
  return `IN ${diffDays} DAYS`
}

function formatTimeUntil(dateString) {
  if (!dateString) return ''
  const diffTime = new Date(dateString) - new Date()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor((diffTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  if (diffDays === 0) {
    return diffHours > 0 ? `${diffHours} hours remaining` : 'Airing soon'
  }
  if (diffDays === 1) return 'Airing tomorrow'
  if (diffDays < 7) return `${diffDays} days remaining`
  const weeks = Math.floor(diffDays / 7)
  return weeks === 1 ? '1 week away' : `${weeks} weeks away`
}

function getStatusBgColor(status) {
  // Status colors are user-configurable via Settings → Colors (status category).
  // resolveVuetifyColor returns a concrete hex so it applies cleanly as a CSS
  // background value.
  const key = status?.toLowerCase() || 'draft'
  return resolveVuetifyColor(getColorValue(key), theme)
}

onMounted(() => {
  fetchNextShow()
  setInterval(fetchNextShow, 5 * 60 * 1000)
})

// LiveClock is auto-registered via <script setup> import
void LiveClock
</script>

<style scoped>
.next-show-panel {
  height: 100%;
}

.next-show-title {
  display: flex;
  align-items: center;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  padding: 6px 10px !important;
  min-height: 0 !important;
  letter-spacing: 0.3px;
}

.bg-gradient-primary {
  background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
}

.episode-header {
  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
}

.progress-status-bar {
  width: 100%;
  color: #ffffff;
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 1.2px;
  text-align: center;
  text-transform: uppercase;
  padding: 8px 0;
  border-radius: 0;
}

.next-show-overline,
.next-show-title,
.next-show-number {
  display: block;
  text-align: left;
  padding-left: 0;
  margin-left: 0;
  text-indent: 0;
}

.next-show-overline {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.8px;
  color: #888;
  text-transform: uppercase;
  line-height: 1.2;
}

.next-show-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  margin-top: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.next-show-number {
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0;
  line-height: 1.2;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 1px;
}

.min-width-0 {
  min-width: 0;
}

.info-row-pair {
  display: flex;
  gap: 6px;
  margin-bottom: 3px;
}

.info-row-half {
  flex: 1;
  min-width: 0;
  margin-bottom: 0;
}

.info-row {
  display: flex;
  align-items: flex-start;
  padding: 5px 6px;
  margin-bottom: 3px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.015);
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-content {
  flex: 1;
  min-width: 0;
}

.info-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  line-height: 1;
}

.info-value {
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.2;
  margin-top: 1px;
}

.info-hint {
  font-size: 0.68rem;
  color: #888;
  line-height: 1.1;
  margin-top: 1px;
}

.info-desc {
  font-size: 0.75rem;
  line-height: 1.3;
  color: rgba(0, 0, 0, 0.75);
  margin-top: 1px;
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

.dummy-banner-large {
  background: repeating-linear-gradient(
    45deg,
    #ff0000,
    #ff0000 10px,
    #ffff00 10px,
    #ffff00 20px
  );
  color: #000;
  font-weight: bold;
  text-align: center;
  padding: 4px;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: banner-pulse 2s infinite;
}

@keyframes banner-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}
</style>
