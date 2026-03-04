<template>
  <v-container fluid class="pa-2">
    <!-- iPad Script Mode Banner - Production episode (primary) -->
    <v-card
      v-if="productionEpisode"
      class="ipad-mode-card mb-3"
      :to="`/ipad-scroll/${productionEpisode.episode_number}`"
      hover
      ripple
    >
      <div class="ipad-mode-inner d-flex align-center justify-space-between pa-4">
        <div class="d-flex align-center">
          <v-icon size="48" color="white" class="me-4">mdi-tablet</v-icon>
          <div>
            <div class="ipad-mode-title">iPad Script Mode</div>
            <div class="ipad-mode-subtitle">
              Episode {{ productionEpisode.episode_number }}
              <span v-if="productionEpisode.title"> — {{ productionEpisode.title }}</span>
            </div>
            <v-chip size="x-small" color="orange" variant="flat" class="mt-1">IN PRODUCTION</v-chip>
          </div>
        </div>
        <v-icon size="36" color="white">mdi-arrow-right-circle</v-icon>
      </div>
    </v-card>

    <!-- Fallback: latest episode if no production episode -->
    <v-card
      v-else-if="latestEpisodeNumber"
      class="ipad-mode-card ipad-mode-card-fallback mb-3"
      :to="`/ipad-scroll/${latestEpisodeNumber}`"
      hover
      ripple
    >
      <div class="ipad-mode-inner ipad-mode-inner-fallback d-flex align-center justify-space-between pa-3">
        <div class="d-flex align-center">
          <v-icon size="36" color="white" class="me-3">mdi-tablet</v-icon>
          <div>
            <div class="ipad-mode-title-sm">iPad Script Mode — Episode {{ latestEpisodeNumber }}</div>
          </div>
        </div>
        <v-icon size="28" color="white">mdi-arrow-right-circle</v-icon>
      </div>
    </v-card>

    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-4">Dashboard</h2>

        <!-- All Dashboard Panels - True Masonry Grid -->
        <div class="masonry-grid">
          <!-- Next Show Panel - Featured -->
          <div class="masonry-item masonry-item-wide">
            <NextShowPanel />
          </div>

          <!-- Active Tools Panel -->
          <div class="masonry-item">
            <v-card class="elevation-4">
              <v-card-title class="d-flex align-center bg-primary text-white">
                <v-icon class="me-2">mdi-star-circle</v-icon>
                <span>Active Tools</span>
              </v-card-title>
              <v-card-text class="pa-2">
                <v-card variant="outlined" class="hover-card mb-2" @click="$router.push('/consolidation')">
                  <v-card-text class="d-flex align-center pa-3">
                    <v-icon color="primary" size="32" class="me-3">mdi-folder-sync</v-icon>
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">Episode Consolidation</div>
                      <div class="text-caption text-grey">Sync Drive & Syncthing</div>
                    </div>
                  </v-card-text>
                </v-card>
                <v-card variant="outlined" class="hover-card" @click="$router.push('/tools')">
                  <v-card-text class="d-flex align-center pa-3">
                    <v-icon color="grey" size="32" class="me-3">mdi-dots-horizontal-circle-outline</v-icon>
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">More Tools</div>
                      <div class="text-caption text-grey">View all available tools</div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-card-text>
            </v-card>
          </div>

          <!-- Announcements -->
          <div class="masonry-item">
            <AnnouncementsPanel />
          </div>

          <!-- Todo Panel -->
          <div class="masonry-item">
            <TodoPanel />
          </div>

          <!-- Quick Actions Panel -->
          <div class="masonry-item">
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
          </div>

          <!-- Upcoming Episodes Section - Only show if episodes exist -->
          <div v-if="upcomingEpisodes.length > 0" class="masonry-item">
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

              <v-card-text v-else class="pa-2">
                <v-expansion-panels variant="accordion">
                  <v-expansion-panel
                    v-for="episodeData in upcomingEpisodes.slice(0, 5)"
                    :key="episodeData.episode.number"
                  >
                    <v-expansion-panel-title class="py-2">
                      <div class="d-flex align-center justify-space-between w-100 me-2">
                        <div class="d-flex align-center">
                          <span class="text-body-2 font-weight-bold text-primary me-2">
                            {{ episodeData.episode.number }}
                          </span>
                          <span v-if="episodeData.episode.title" class="text-body-2 me-2">
                            {{ episodeData.episode.title }}
                          </span>
                        </div>
                        <div class="d-flex align-center ga-2">
                          <span class="text-caption text-grey">
                            {{ formatAirDateShort(episodeData.episode.air_date) }}
                          </span>
                          <v-chip
                            :color="getStatusColor(episodeData.episode.status)"
                            size="x-small"
                            variant="flat"
                          >
                            {{ episodeData.episode.status?.toUpperCase() || 'DRAFT' }}
                          </v-chip>
                        </div>
                      </div>
                    </v-expansion-panel-title>

                    <v-expansion-panel-text>
                      <!-- Dummy Episode Banner -->
                      <div v-if="episodeData.episode.is_dummy" class="dummy-banner dummy-banner-top mb-2">
                        DUMMY EPISODE
                      </div>

                      <!-- Episode Statistics -->
                      <v-row v-if="episodeData.statistics" dense class="mb-2">
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
                        class="mb-2"
                      />

                      <!-- Guest Information -->
                      <div v-if="episodeData.episode.guest?.name" class="guest-info mb-2">
                        <v-icon size="small" color="primary" class="me-1">mdi-account</v-icon>
                        <span class="text-body-2 font-weight-medium">{{ episodeData.episode.guest.name }}</span>
                      </div>

                      <!-- Quick Actions -->
                      <div class="episode-actions">
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
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

                <!-- Show more link -->
                <div v-if="upcomingEpisodes.length > 5" class="text-center mt-3">
                  <v-btn
                    variant="text"
                    :to="`/episodes`"
                    append-icon="mdi-arrow-right"
                    size="small"
                  >
                    View All {{ upcomingEpisodes.length }} Upcoming
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </div>

          <!-- Preproduction Panel -->
          <div class="masonry-item">
            <v-card class="elevation-4">
              <v-card-title class="d-flex align-center bg-purple text-white">
                <v-icon class="me-2">mdi-lightbulb-on</v-icon>
                <span>Preproduction</span>
              </v-card-title>
              <v-card-text class="pa-2">
                <v-card variant="outlined" class="hover-card mb-2" @click="$router.push('/whiteboard')">
                  <v-card-text class="d-flex align-center pa-3">
                    <v-icon color="purple" size="32" class="me-3">mdi-notebook-edit</v-icon>
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">Whiteboard</div>
                      <div class="text-caption text-grey">Brainstorm ideas and links</div>
                    </div>
                  </v-card-text>
                </v-card>
                <v-card variant="outlined" class="hover-card mb-2" @click="$router.push('/generator')">
                  <v-card-text class="d-flex align-center pa-3">
                    <v-icon color="purple" size="32" class="me-3">mdi-creation</v-icon>
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">Generator</div>
                      <div class="text-caption text-grey">AI content generation</div>
                    </div>
                  </v-card-text>
                </v-card>
                <v-card variant="outlined" class="hover-card" @click="$router.push('/voice-meeting')">
                  <v-card-text class="d-flex align-center pa-3">
                    <v-icon color="purple" size="32" class="me-3">mdi-microphone</v-icon>
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">Production Meeting</div>
                      <div class="text-caption text-grey">Voice conference call</div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-card-text>
            </v-card>
          </div>

          <!-- System Health -->
          <div class="masonry-item">
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
          </div>

          <!-- Storage & Usage -->
          <div class="masonry-item">
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
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Episode Creation Modal (hidden activator, triggered programmatically) -->
    <EpisodeScaffoldModal ref="episodeModalRef" @episode-created="onEpisodeCreated" />
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSystemHealth } from '@/composables/useSystemHealth'
import AnnouncementsPanel from '@/components/AnnouncementsPanel.vue'
import TodoPanel from '@/components/TodoPanel.vue'
import NextShowPanel from '@/components/NextShowPanel.vue'
import EpisodeScaffoldModal from '@/components/EpisodeScaffoldModal.vue'

const router = useRouter()

// Episode creation modal ref
const episodeModalRef = ref(null)
const { health } = useSystemHealth()

// Reactive data
const upcomingEpisodes = ref([])
const loadingEpisodes = ref(true)
const episodeError = ref('')
const latestEpisodeNumber = ref(null)
const productionEpisode = ref(null)

// Fetch production episode and latest episode for iPad mode buttons
const fetchLatestEpisode = async () => {
  try {
    const response = await axios.get('/api/episodes')
    const episodes = response.data || []
    if (episodes.length > 0) {
      const real = episodes.filter(e => !e.is_test_data)

      // Find the episode currently in production
      const inProduction = real.find(e => e.status === 'production')
      if (inProduction) {
        productionEpisode.value = inProduction
      }

      // Sort by episode number descending, pick the highest as fallback
      const sorted = [...real].sort((a, b) => (b.episode_number || 0) - (a.episode_number || 0))
      if (sorted.length > 0) {
        latestEpisodeNumber.value = sorted[0].episode_number
      }
    }
  } catch (error) {
    console.error('Failed to fetch latest episode:', error)
  }
}

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

// Format air date short (for collapsed episode rows)
const formatAirDateShort = (dateString) => {
  if (!dateString) return 'TBD'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'America/New_York'
  })
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
const openEpisodeModal = () => {
  episodeModalRef.value?.open()
}

const createNewEpisode = () => {
  openEpisodeModal()
}

const onEpisodeCreated = (episode) => {
  console.log('Episode created:', episode)
  // Optionally refresh dashboard data
  fetchUpcomingEpisodes()
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
  fetchLatestEpisode()
  fetchUpcomingEpisodes()
})
</script>

<style scoped>
/* True masonry layout using CSS columns */
.masonry-grid {
  column-count: 4;
  column-gap: 10px;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 10px;
  display: inline-block;
  width: 100%;
}

.masonry-item-wide {
  column-span: all;
}

@media (max-width: 1264px) {
  .masonry-grid {
    column-count: 3;
  }
}

@media (max-width: 960px) {
  .masonry-grid {
    column-count: 2;
  }
}

@media (max-width: 600px) {
  .masonry-grid {
    column-count: 1;
  }
}

.hover-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.hover-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

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

/* iPad Mode Banner Card */
.ipad-mode-card {
  cursor: pointer;
  border-radius: 12px !important;
  overflow: hidden;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.ipad-mode-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(103, 58, 183, 0.4) !important;
}

.ipad-mode-inner {
  background: linear-gradient(135deg, #512da8 0%, #7c4dff 50%, #651fff 100%);
  min-height: 80px;
}

.ipad-mode-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  letter-spacing: 0.5px;
}

.ipad-mode-subtitle {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 2px;
}

/* Fallback (non-production) variant - smaller, less prominent */
.ipad-mode-inner-fallback {
  background: linear-gradient(135deg, #455a64 0%, #607d8b 100%);
  min-height: 56px;
}

.ipad-mode-title-sm {
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  letter-spacing: 0.5px;
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