<template>
  <v-card class="next-show-panel elevation-4">
    <v-card-title class="d-flex align-center bg-gradient-primary text-white">
      <v-icon class="me-2">mdi-clock-fast</v-icon>
      <span>Next Show</span>
      <v-spacer />
      <LiveClock v-if="nextShow" />
    </v-card-title>

    <v-card-text v-if="loading" class="pa-4">
      <v-skeleton-loader type="article, actions" />
    </v-card-text>

    <v-card-text v-else-if="error" class="text-center pa-4">
      <v-icon color="grey" size="48" class="mb-2">mdi-alert-circle</v-icon>
      <p class="text-grey">{{ error }}</p>
    </v-card-text>

    <v-card-text v-else-if="!nextShow" class="text-center pa-4">
      <v-icon color="grey" size="64" class="mb-3">mdi-calendar-clock</v-icon>
      <p class="text-h6 text-grey">No upcoming show scheduled</p>
      <v-btn color="primary" variant="outlined" class="mt-2" @click="$router.push('/tools')">
        Create New Episode
      </v-btn>
    </v-card-text>

    <v-card-text v-else class="pa-0">
      <!-- Dummy Episode Banner -->
      <div v-if="nextShow.is_dummy" class="dummy-banner-large">
        <v-icon class="me-2">mdi-alert</v-icon>
        DUMMY EPISODE - FOR TESTING ONLY
      </div>

      <!-- Episode Header -->
      <div class="episode-header pa-4">
        <div class="d-flex align-center justify-space-between mb-3">
          <div class="flex-grow-1">
            <div class="text-overline text-grey">{{ formatDaysUntil(nextShow.air_date) }}</div>
            <h2 class="text-h4 font-weight-bold mb-1">Episode {{ nextShow.number }}</h2>
            <h3 class="text-h6 mb-2">{{ nextShow.title || 'Untitled Episode' }}</h3>
            <div v-if="nextShow.subtitle" class="text-body-1 text-grey mb-2">{{ nextShow.subtitle }}</div>
          </div>
          <v-chip
            :color="getStatusColor(nextShow.status)"
            size="large"
            variant="flat"
            class="px-4"
          >
            {{ nextShow.status?.toUpperCase() || 'DRAFT' }}
          </v-chip>
        </div>

        <!-- Air Date & Time -->
        <v-card variant="outlined" class="mb-3">
          <v-card-text class="pa-3">
            <div class="d-flex align-center">
              <v-icon color="primary" size="32" class="me-3">mdi-calendar-star</v-icon>
              <div>
                <div class="text-caption text-grey">Air Date</div>
                <div class="text-h6 font-weight-bold">{{ formatAirDate(nextShow.air_date) }}</div>
                <div class="text-caption text-grey">{{ formatTimeUntil(nextShow.air_date) }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Guest Information -->
        <v-card v-if="nextShow.guest" variant="outlined" class="mb-3">
          <v-card-text class="pa-3">
            <div class="d-flex align-center">
              <v-avatar color="primary" size="48" class="me-3">
                <v-icon color="white">mdi-account</v-icon>
              </v-avatar>
              <div class="flex-grow-1">
                <div class="text-caption text-grey">Guest</div>
                <div class="text-h6 font-weight-bold">{{ nextShow.guest }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Episode Description -->
        <v-card v-if="nextShow.description" variant="outlined" class="mb-3">
          <v-card-text class="pa-3">
            <div class="text-caption text-grey mb-1">Description</div>
            <p class="text-body-2 mb-0">{{ nextShow.description }}</p>
          </v-card-text>
        </v-card>

        <!-- Episode Statistics Grid -->
        <v-row v-if="statistics" dense class="mb-3">
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="primary">
              <v-card-text class="text-center pa-3">
                <div class="text-h4 font-weight-bold">{{ statistics.total_items || 0 }}</div>
                <div class="text-caption">Total Items</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="warning">
              <v-card-text class="text-center pa-3">
                <div class="text-h4 font-weight-bold">{{ statistics.by_status?.draft || 0 }}</div>
                <div class="text-caption">Draft</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="success">
              <v-card-text class="text-center pa-3">
                <div class="text-h4 font-weight-bold">{{ (statistics.by_status?.approved || 0) + (statistics.by_status?.completed || 0) }}</div>
                <div class="text-caption">Ready</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" :color="getProgressColor(statistics.progress_percentage)">
              <v-card-text class="text-center pa-3">
                <div class="text-h4 font-weight-bold">{{ statistics.progress_percentage || 0 }}%</div>
                <div class="text-caption">Complete</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Progress Bar -->
        <v-card variant="outlined" class="mb-3">
          <v-card-text class="pa-3">
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-caption text-grey">Production Progress</span>
              <span class="text-caption font-weight-bold">{{ statistics?.progress_percentage || 0 }}%</span>
            </div>
            <v-progress-linear
              :model-value="statistics?.progress_percentage || 0"
              :color="getProgressColor(statistics?.progress_percentage)"
              height="8"
              rounded
            />
          </v-card-text>
        </v-card>

        <!-- Content Breakdown by Type -->
        <v-card v-if="statistics?.by_type" variant="outlined" class="mb-3">
          <v-card-text class="pa-3">
            <div class="text-caption text-grey mb-2">Content Breakdown</div>
            <v-row dense>
              <v-col v-for="(count, type) in statistics.by_type" :key="type" cols="6">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">{{ formatTypeName(type) }}</span>
                  <v-chip size="small" variant="flat">{{ count }}</v-chip>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Duration -->
        <v-card v-if="nextShow.duration" variant="outlined" class="mb-3">
          <v-card-text class="pa-3">
            <div class="d-flex align-center">
              <v-icon color="primary" class="me-3">mdi-timer</v-icon>
              <div>
                <div class="text-caption text-grey">Total Duration</div>
                <div class="text-h6 font-weight-bold">{{ nextShow.duration }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </div>

      <!-- Quick Actions -->
      <v-divider />
      <v-card-actions class="pa-3">
        <v-btn
          color="primary"
          variant="elevated"
          block
          size="large"
          :to="`/content-editor/${nextShow.number}`"
          prepend-icon="mdi-pencil"
        >
          Open Content Editor
        </v-btn>
      </v-card-actions>
      <v-card-actions class="pa-3 pt-0">
        <v-btn
          color="secondary"
          variant="outlined"
          block
          :to="`/stack/${nextShow.number}`"
          prepend-icon="mdi-clock-outline"
        >
          Timing & Stack
        </v-btn>
      </v-card-actions>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import LiveClock from './LiveClock.vue'

export default {
  name: 'NextShowPanel',
  components: {
    LiveClock
  },
  setup() {
    const nextShow = ref(null)
    const statistics = ref(null)
    const loading = ref(true)
    const error = ref(null)

    const fetchNextShow = async () => {
      try {
        loading.value = true
        error.value = null

        // Fetch episodes with upcoming air dates
        const response = await axios.get('/api/episodes', {
          params: {
            status: 'all',
            sort_by: 'air_date',
            sort_order: 'asc',
            limit: 10
          }
        })

        if (response.data && response.data.length > 0) {
          // Find the next show (first episode with air_date in future or today)
          const today = new Date()
          today.setHours(0, 0, 0, 0)

          const upcoming = response.data.find(ep => {
            if (!ep.air_date) return false
            const airDate = new Date(ep.air_date)
            airDate.setHours(0, 0, 0, 0)
            return airDate >= today
          })

          if (upcoming) {
            nextShow.value = upcoming

            // Fetch statistics for this episode
            try {
              const statsResponse = await axios.get(`/api/episodes/${upcoming.number}/statistics`)
              statistics.value = statsResponse.data
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

    const formatAirDate = (dateString) => {
      if (!dateString) return 'Not scheduled'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const formatDaysUntil = (dateString) => {
      if (!dateString) return 'Not scheduled'
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const airDate = new Date(dateString)
      airDate.setHours(0, 0, 0, 0)

      const diffTime = airDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays === 0) return 'AIRING TODAY'
      if (diffDays === 1) return 'AIRING TOMORROW'
      if (diffDays < 0) return `AIRED ${Math.abs(diffDays)} DAYS AGO`
      return `IN ${diffDays} DAYS`
    }

    const formatTimeUntil = (dateString) => {
      if (!dateString) return ''
      const today = new Date()
      const airDate = new Date(dateString)

      const diffTime = airDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      const diffHours = Math.floor((diffTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))

      if (diffDays === 0) {
        if (diffHours > 0) return `${diffHours} hours remaining`
        return 'Airing soon'
      }
      if (diffDays === 1) return 'Airing tomorrow'
      if (diffDays < 7) return `${diffDays} days remaining`
      const weeks = Math.floor(diffDays / 7)
      if (weeks === 1) return '1 week away'
      return `${weeks} weeks away`
    }

    const getStatusColor = (status) => {
      const statusColors = {
        'draft': 'grey',
        'approved': 'success',
        'production': 'warning',
        'completed': 'primary',
        'promotion': 'purple'
      }
      return statusColors[status?.toLowerCase()] || 'grey'
    }

    const getProgressColor = (percentage) => {
      if (!percentage) return 'grey'
      if (percentage >= 80) return 'success'
      if (percentage >= 50) return 'warning'
      return 'error'
    }

    const formatTypeName = (type) => {
      const typeNames = {
        'segment': 'Segments',
        'ad': 'Ads',
        'promo': 'Promos',
        'cta': 'CTAs',
        'trans': 'Transitions',
        'cold_open': 'Cold Open',
        'tease': 'Teases'
      }
      return typeNames[type] || type.charAt(0).toUpperCase() + type.slice(1)
    }

    onMounted(() => {
      fetchNextShow()
      // Refresh every 5 minutes
      setInterval(fetchNextShow, 5 * 60 * 1000)
    })

    return {
      nextShow,
      statistics,
      loading,
      error,
      formatAirDate,
      formatDaysUntil,
      formatTimeUntil,
      getStatusColor,
      getProgressColor,
      formatTypeName
    }
  }
}
</script>

<style scoped>
.next-show-panel {
  height: 100%;
}

.bg-gradient-primary {
  background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
}

.episode-header {
  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
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
  padding: 12px;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: banner-pulse 2s infinite;
}

@keyframes banner-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.stat-item {
  text-align: center;
  padding: 12px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.6);
  letter-spacing: 0.5px;
}
</style>
