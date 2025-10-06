<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-4">Dashboard</h2>

        <!-- Featured Row: Upcoming Episodes and Quick Actions -->
        <v-row class="mb-6">
          <!-- Upcoming Episodes Section -->
          <v-col cols="12" lg="8">
            <v-card class="current-episode-card" elevation="3">
              <v-card-title class="d-flex align-center">
                <v-icon color="primary" class="me-2">mdi-television-classic</v-icon>
                <span>Upcoming Episodes</span>
                <v-spacer />
                <v-chip
                  v-if="upcomingEpisodes.length > 0"
                  color="primary"
                  size="small"
                  variant="flat"
                >
                  {{ upcomingEpisodes.length }} Shows
                </v-chip>
              </v-card-title>

              <v-card-text v-if="loadingEpisodes">
                <v-skeleton-loader type="article" />
              </v-card-text>

              <v-card-text v-else-if="episodeError" class="text-center">
                <v-icon color="grey" size="48" class="mb-2">mdi-television-off</v-icon>
                <p class="text-grey">{{ episodeError }}</p>
              </v-card-text>

              <v-card-text v-else-if="upcomingEpisodes.length === 0" class="text-center">
                <v-icon color="grey" size="48" class="mb-2">mdi-calendar-clock</v-icon>
                <p class="text-grey">No upcoming episodes scheduled</p>
              </v-card-text>

              <v-card-text v-else class="pt-4">
                <!-- Episodes List -->
                <div v-for="(episodeData, index) in upcomingEpisodes.slice(0, 3)" :key="episodeData.episode.number"
                     class="episode-card mb-4"
                     :class="{ 'dummy-episode': episodeData.episode.is_dummy }">

                  <!-- Dummy Episode Top Banner -->
                  <div v-if="episodeData.episode.is_dummy" class="dummy-banner dummy-banner-top">
                    DUMMY EPISODE
                  </div>

                  <div class="d-flex align-center justify-space-between mb-2">
                    <div>
                      <h3 class="text-h6 font-weight-bold text-primary">
                        Episode {{ episodeData.episode.number }}
                      </h3>
                      <h4 class="text-subtitle-1 mb-1">{{ episodeData.episode.title }}</h4>
                      <div class="d-flex align-center text-grey">
                        <v-icon size="small" class="me-1">mdi-calendar</v-icon>
                        <span>{{ formatAirDate(episodeData.episode.air_date) }}</span>
                      </div>
                    </div>
                    <v-chip
                      :color="getStatusColor(episodeData.episode.status)"
                      size="small"
                      variant="flat"
                    >
                      {{ episodeData.episode.status?.toUpperCase() || 'DRAFT' }}
                    </v-chip>
                  </div>

                  <!-- Episode Statistics -->
                  <v-row v-if="episodeData.statistics" class="mb-3">
                    <v-col cols="3">
                      <div class="stat-item-small">
                        <div class="stat-number-small">{{ episodeData.statistics.total_items }}</div>
                        <div class="stat-label-small">Items</div>
                      </div>
                    </v-col>
                    <v-col cols="3">
                      <div class="stat-item-small">
                        <div class="stat-number-small">{{ episodeData.statistics.by_status?.draft || 0 }}</div>
                        <div class="stat-label-small">Draft</div>
                      </div>
                    </v-col>
                    <v-col cols="3">
                      <div class="stat-item-small">
                        <div class="stat-number-small">{{ (episodeData.statistics.by_status?.approved || 0) + (episodeData.statistics.by_status?.completed || 0) }}</div>
                        <div class="stat-label-small">Ready</div>
                      </div>
                    </v-col>
                    <v-col cols="3">
                      <div class="stat-item-small">
                        <div class="stat-number-small">{{ episodeData.statistics.progress_percentage || 0 }}%</div>
                        <div class="stat-label-small">Progress</div>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Progress Bar -->
                  <v-progress-linear
                    :model-value="episodeData.statistics?.progress_percentage || 0"
                    color="primary"
                    height="4"
                    rounded
                    class="mb-3"
                  />

                  <!-- Guest Information -->
                  <div v-if="episodeData.episode.guest?.name" class="guest-info">
                    <v-icon size="small" color="primary" class="me-1">mdi-account</v-icon>
                    <span class="text-body-2 font-weight-medium">{{ episodeData.episode.guest.name }}</span>
                  </div>

                  <!-- Quick Actions for this episode -->
                  <div class="episode-actions mt-2">
                    <v-btn
                      size="small"
                      color="primary"
                      variant="outlined"
                      :to="`/content-editor/${episodeData.episode.number}`"
                      class="me-2"
                    >
                      Content Editor
                    </v-btn>
                    <v-btn
                      size="small"
                      color="secondary"
                      variant="outlined"
                      :to="`/stack/${episodeData.episode.number}`"
                    >
                      Timing
                    </v-btn>
                  </div>

                  <!-- Dummy Episode Bottom Banner -->
                  <div v-if="episodeData.episode.is_dummy" class="dummy-banner dummy-banner-bottom">
                    DUMMY EPISODE
                  </div>

                  <v-divider v-if="index < Math.min(upcomingEpisodes.length, 3) - 1" class="mt-4" />
                </div>

                <!-- Show more link -->
                <div v-if="upcomingEpisodes.length > 3" class="text-center mt-4">
                  <v-btn
                    variant="text"
                    :to="`/episodes`"
                    append-icon="mdi-arrow-right"
                  >
                    View All {{ upcomingEpisodes.length }} Upcoming Episodes
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Quick Actions Panel -->
          <v-col cols="12" lg="4">
            <v-card class="quick-actions-card" elevation="3">
              <v-card-title class="d-flex align-center">
                <v-icon color="primary" class="me-2">mdi-lightning-bolt</v-icon>
                <span>Quick Actions</span>
              </v-card-title>

              <v-card-text class="pb-4">
                <v-list class="pa-0">
                  <v-list-item
                    @click="createNewEpisode"
                    prepend-icon="mdi-plus-circle"
                    title="New Episode"
                    subtitle="Create a new episode from template"
                    class="action-item"
                  />
                  <v-list-item
                    @click="openVoiceTest"
                    prepend-icon="mdi-microphone"
                    title="Test Voice Synthesis"
                    subtitle="Quick XTTS voice test"
                    class="action-item"
                  />
                  <v-list-item
                    to="/assets"
                    prepend-icon="mdi-cloud-upload"
                    title="Upload Assets"
                    subtitle="Add images, videos, or audio"
                    class="action-item"
                  />
                  <v-list-item
                    to="/templates"
                    prepend-icon="mdi-file-document"
                    title="Manage Templates"
                    subtitle="Create or edit episode templates"
                    class="action-item"
                  />
                  <v-list-item
                    @click="exportData"
                    prepend-icon="mdi-download"
                    title="Export Data"
                    subtitle="Download episode data or scripts"
                    class="action-item"
                  />
                  <v-list-item
                    to="/settings"
                    prepend-icon="mdi-cog"
                    title="System Settings"
                    subtitle="Configure Show Builder"
                    class="action-item"
                  />
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Secondary Stats Row -->
        <v-row>
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Recent Activity</v-card-title>
              <v-card-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="n in 3"
                    :key="n"
                    :title="`Activity ${n}`"
                    subtitle="Recent action performed"
                    prepend-icon="mdi-history"
                  />
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>System Health</v-card-title>
              <v-card-text>
                <!-- Database -->
                <div class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <v-icon :color="health.services?.database === 'connected' ? 'green' : 'red'" class="me-2">
                      mdi-database
                    </v-icon>
                    <span>Database</span>
                  </div>
                  <v-chip size="x-small" :color="health.services?.database === 'connected' ? 'green' : 'red'">
                    {{ health.services?.database || 'unknown' }}
                  </v-chip>
                </div>

                <!-- Redis -->
                <div class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <v-icon :color="health.services?.redis?.connected ? 'green' : 'red'" class="me-2">
                      mdi-memory
                    </v-icon>
                    <span>Redis</span>
                  </div>
                  <v-chip size="x-small" :color="health.services?.redis?.connected ? 'green' : 'red'">
                    {{ health.services?.redis?.latency ? `${health.services.redis.latency}ms` : 'disconnected' }}
                  </v-chip>
                </div>

                <!-- Celery Workers -->
                <div class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <v-icon :color="health.services?.celery?.workers?.length > 0 ? 'green' : 'red'" class="me-2">
                      mdi-hammer-wrench
                    </v-icon>
                    <span>Workers</span>
                  </div>
                  <v-chip size="x-small" :color="health.services?.celery?.workers?.length > 0 ? 'green' : 'red'">
                    {{ health.services?.celery?.workers?.length || 0 }} active
                  </v-chip>
                </div>

                <!-- Ollama (if configured) -->
                <div v-if="health.services?.ollama" class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <v-icon :color="health.services?.ollama?.status === 'connected' ? 'green' : 'red'" class="me-2">
                      mdi-robot
                    </v-icon>
                    <span>Ollama</span>
                  </div>
                  <v-chip size="x-small" :color="health.services?.ollama?.status === 'connected' ? 'green' : 'red'">
                    {{ health.services?.ollama?.model || 'offline' }}
                  </v-chip>
                </div>

                <!-- XTTS (if configured) -->
                <div v-if="health.services?.xtts" class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <v-icon :color="health.services?.xtts?.connected ? 'green' : 'red'" class="me-2">
                      mdi-microphone
                    </v-icon>
                    <span>XTTS</span>
                  </div>
                  <v-chip size="x-small" :color="health.services?.xtts?.connected ? 'green' : 'red'">
                    {{ health.services?.xtts?.connected ? 'online' : 'offline' }}
                  </v-chip>
                </div>

                <!-- NFS -->
                <div v-if="health.services?.nfs" class="d-flex align-center justify-space-between">
                  <div class="d-flex align-center">
                    <v-icon :color="health.services?.nfs?.status === 'connected' ? 'green' : 'red'" class="me-2">
                      mdi-folder-network
                    </v-icon>
                    <span>NFS Storage</span>
                  </div>
                  <v-chip size="x-small" :color="health.services?.nfs?.status === 'connected' ? 'green' : 'red'">
                    {{ health.services?.nfs?.writable ? 'read/write' : 'error' }}
                  </v-chip>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Storage & Usage</v-card-title>
              <v-card-text>
                <div class="mb-3">
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-body-2">Assets Storage</span>
                    <span class="text-body-2">2.1 GB</span>
                  </div>
                  <v-progress-linear
                    :model-value="30"
                    color="blue"
                    height="6"
                  />
                </div>
                <div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-body-2">Episodes Created</span>
                    <span class="text-body-2">247</span>
                  </div>
                  <v-progress-linear
                    :model-value="80"
                    color="green"
                    height="6"
                  />
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSystemHealth } from '@/composables/useSystemHealth'

const router = useRouter()
const { health } = useSystemHealth()

// Reactive data
const upcomingEpisodes = ref([])
const loadingEpisodes = ref(true)
const episodeError = ref('')

// Fetch upcoming episodes data
const fetchUpcomingEpisodes = async () => {
  loadingEpisodes.value = true
  episodeError.value = ''

  try {
    const response = await axios.get('/api/episodes/upcoming')

    if (response.data.error) {
      episodeError.value = response.data.error
      upcomingEpisodes.value = []
    } else {
      upcomingEpisodes.value = response.data.episodes || []
    }
  } catch (error) {
    console.error('Failed to fetch upcoming episodes:', error)
    episodeError.value = 'Failed to load upcoming episodes'
    upcomingEpisodes.value = []
  } finally {
    loadingEpisodes.value = false
  }
}

// Format air date for display
const formatAirDate = (dateString) => {
  if (!dateString) return 'No air date set'

  const date = new Date(dateString)
  const options = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'America/New_York'
  }

  return date.toLocaleDateString('en-US', options) + ' ET'
}

// Get status color for chip
const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'green'
    case 'approved':
      return 'blue'
    case 'production':
    case 'in-progress':
      return 'orange'
    case 'draft':
    default:
      return 'grey'
  }
}


// Quick action handlers
const createNewEpisode = () => {
  router.push('/episodes')
  // TODO: Open new episode modal
}

const openVoiceTest = () => {
  router.push('/settings?tab=voice')
  // TODO: Open voice test modal directly
}

const exportData = () => {
  // TODO: Implement export functionality
  console.log('Export data functionality to be implemented')
}

// Load data on component mount
onMounted(() => {
  fetchUpcomingEpisodes()
})
</script>

<style scoped>
.current-episode-card {
  border-left: 4px solid #1976d2;
}

.quick-actions-card {
  border-left: 4px solid #673ab7;
}

.stat-item {
  text-align: center;
  padding: 12px;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1976d2;
}

.stat-label {
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-item-small {
  text-align: center;
  padding: 4px;
}

.stat-number-small {
  font-size: 1rem;
  font-weight: bold;
  color: #1976d2;
}

.stat-label-small {
  font-size: 0.6rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.episode-card {
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.02);
}

.guest-info {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.episode-actions {
  display: flex;
  gap: 8px;
}

.dummy-episode {
  position: relative;
  opacity: 0.7;
  background-color: rgba(150, 150, 150, 0.1) !important;
  border: 1px solid rgba(150, 150, 150, 0.3) !important;
}

.dummy-banner {
  position: absolute;
  left: 0;
  right: 0;
  background: linear-gradient(45deg, #ff9800, #ffc107);
  color: #000;
  text-align: center;
  font-weight: bold;
  font-size: 0.75rem;
  letter-spacing: 1px;
  padding: 4px 8px;
  z-index: 2;
  transform: skew(-15deg);
  margin: 0 -8px;
}

.dummy-banner-top {
  top: -4px;
}

.dummy-banner-bottom {
  bottom: -4px;
}

.action-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.episode-header h3 {
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .stat-number {
    font-size: 1.25rem;
  }

  .stat-label {
    font-size: 0.7rem;
  }
}
</style>