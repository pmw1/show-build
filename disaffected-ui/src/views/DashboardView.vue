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
        <div class="d-flex align-center mb-2">
          <h2 class="text-h5 font-weight-bold">Dashboard</h2>
          <v-spacer />
          <v-btn size="x-small" variant="text" color="grey" @click="resetLayout">
            <v-icon size="small" start>mdi-restore</v-icon>
            Reset Layout
          </v-btn>
        </div>

        <!-- Draggable block columns (headers are drag handles) -->
        <div class="dashboard-columns dashboard-compact">
          <div
            v-for="(col, colIndex) in columns"
            :key="`col-wrap-${colIndex}`"
            class="dashboard-column"
          >
            <!-- Next Show Panel pinned at top of first column (not draggable) -->
            <NextShowPanel v-if="colIndex === 0" />

          <draggable
            :list="col"
            group="dashboard-blocks"
            :item-key="el => el"
            class="dashboard-column-inner"
            handle=".dash-drag-handle"
            animation="180"
            ghost-class="drag-ghost"
            @end="saveLayout"
          >
            <template #item="{ element }">
              <div class="block-wrap" :class="`block-${BLOCK_COLORS[element] || 'grey'}`">

                <!-- Current Show (in-production episode) -->
                <CurrentShowPanel v-if="element === 'current-show'" class="dash-drag-handle-wrap" />

                <!-- Tools & Actions (merged Active Tools + Quick Actions) -->
                <v-card v-else-if="element === 'tools-actions'" elevation="2">
                  <v-card-title class="dash-title dash-drag-handle">
                    <v-icon size="small" class="me-2">mdi-lightning-bolt</v-icon>
                    <span>Tools &amp; Actions</span>
                  </v-card-title>
                  <v-card-text class="pa-2">
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" @click="createNewEpisode">
                      <v-icon start size="small">mdi-plus-circle</v-icon>
                      New Episode
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" @click="$router.push('/consolidation')">
                      <v-icon start size="small">mdi-folder-sync</v-icon>
                      Episode Consolidation
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" to="/assets">
                      <v-icon start size="small">mdi-cloud-upload</v-icon>
                      Upload Assets
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" to="/templates">
                      <v-icon start size="small">mdi-file-document</v-icon>
                      Manage Templates
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" @click="openVoiceTest">
                      <v-icon start size="small">mdi-microphone</v-icon>
                      Test Voice Synthesis
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" @click="exportData">
                      <v-icon start size="small">mdi-download</v-icon>
                      Export Data
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn mb-1" to="/settings">
                      <v-icon start size="small">mdi-cog</v-icon>
                      System Settings
                    </v-btn>
                    <v-btn block variant="outlined" class="dash-row-btn" @click="$router.push('/tools')">
                      <v-icon start size="small">mdi-dots-horizontal-circle-outline</v-icon>
                      More Tools
                    </v-btn>
                  </v-card-text>
                </v-card>

                <!-- Announcements -->
                <AnnouncementsPanel v-else-if="element === 'announcements'" class="dash-drag-handle-wrap" />

                <!-- Todo Panel -->
                <TodoPanel v-else-if="element === 'todo'" class="dash-drag-handle-wrap" />

                <!-- Preproduction -->
                <v-card v-else-if="element === 'preproduction'" elevation="2">
                  <v-card-title class="dash-title dash-drag-handle">
                    <v-icon size="small" class="me-2">mdi-lightbulb-on</v-icon>
                    <span>Preproduction</span>
                  </v-card-title>
                  <v-card-text class="pa-2">
                    <v-btn block variant="outlined" color="purple" class="dash-row-btn mb-1" @click="$router.push('/whiteboard')">
                      <v-icon start size="small">mdi-notebook-edit</v-icon>
                      Whiteboard
                    </v-btn>
                    <v-btn block variant="outlined" color="purple" class="dash-row-btn mb-1" @click="$router.push('/generator')">
                      <v-icon start size="small">mdi-creation</v-icon>
                      Generator
                    </v-btn>
                    <v-btn block variant="outlined" color="purple" class="dash-row-btn" @click="$router.push('/voice-meeting')">
                      <v-icon start size="small">mdi-microphone</v-icon>
                      Production Meeting
                    </v-btn>
                  </v-card-text>
                </v-card>

                <!-- System Health -->
                <v-card v-else-if="element === 'system-health'" elevation="2">
                  <v-card-title class="dash-title dash-drag-handle">
                    <v-icon size="small" class="me-2">mdi-heart-pulse</v-icon>
                    <span>System Health</span>
                  </v-card-title>
                  <v-card-text class="pa-2">
                    <div class="health-grid">
                      <div
                        v-for="row in healthRows"
                        :key="row.key"
                        class="health-row"
                        :class="row.healthy ? 'health-row-ok' : 'health-row-error'"
                      >
                        <v-icon size="small" class="me-1">{{ row.icon }}</v-icon>
                        <span class="health-label">{{ row.label }}</span>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>

              </div>
            </template>
          </draggable>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Episode Creation Modal (hidden activator, triggered programmatically) -->
    <EpisodeScaffoldModal ref="episodeModalRef" @episode-created="onEpisodeCreated" />
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import draggable from 'vuedraggable'
import { useSystemHealth } from '@/composables/useSystemHealth'
import { useUserPrefs } from '@/composables/useUserPrefs'
import AnnouncementsPanel from '@/components/AnnouncementsPanel.vue'
import TodoPanel from '@/components/TodoPanel.vue'
import NextShowPanel from '@/components/NextShowPanel.vue'
import CurrentShowPanel from '@/components/CurrentShowPanel.vue'
import EpisodeScaffoldModal from '@/components/EpisodeScaffoldModal.vue'

const router = useRouter()

// ===== Draggable dashboard layout =====
// Each block has a stable id and a color name used for the header background.
const BLOCK_COLORS = {
  'current-show': 'orange',
  'tools-actions': 'deep-purple',
  'announcements': 'amber',
  'todo': 'teal',
  'preproduction': 'purple',
  'system-health': 'green'
}

const DEFAULT_LAYOUT = [
  ['current-show', 'tools-actions'],
  ['announcements', 'preproduction'],
  ['todo', 'system-health']
]

// Per-user pref key for the persisted layout. Legacy localStorage key is
// still read once for migration; new writes go to /api/user/prefs.
const PREF_KEY = 'dashboard.layout'
const LEGACY_LAYOUT_KEY = 'dashboard-layout-v3'

const userPrefs = useUserPrefs()
const columns = ref(structuredClone(DEFAULT_LAYOUT))

function _validateAndApply(parsed) {
  if (!Array.isArray(parsed) || !parsed.every(Array.isArray)) return false
  const known = Object.keys(BLOCK_COLORS)
  const flat = parsed.flat()
  const missing = known.filter(k => !flat.includes(k))
  if (missing.length > 0) parsed[0].push(...missing)
  columns.value = parsed.map(col => col.filter(id => known.includes(id)))
  return true
}

function loadLayout() {
  // 1. Per-user pref (DB) wins.
  const userValue = userPrefs.get(PREF_KEY, null)
  if (userValue && _validateAndApply(structuredClone(userValue))) return

  // 2. Fall back to legacy localStorage (and migrate forward).
  try {
    const saved = localStorage.getItem(LEGACY_LAYOUT_KEY)
    if (!saved) return
    const parsed = JSON.parse(saved)
    if (_validateAndApply(parsed)) {
      // Persist to user prefs so future loads are DB-backed.
      userPrefs.set(PREF_KEY, columns.value)
    }
  } catch (e) {
    console.warn('Failed to load dashboard layout:', e)
  }
}

function saveLayout() {
  try {
    localStorage.setItem(LEGACY_LAYOUT_KEY, JSON.stringify(columns.value))  // offline fallback
    userPrefs.set(PREF_KEY, columns.value)
  } catch (e) {
    console.warn('Failed to save dashboard layout:', e)
  }
}

function resetLayout() {
  columns.value = structuredClone(DEFAULT_LAYOUT)
  localStorage.removeItem(LEGACY_LAYOUT_KEY)
  userPrefs.remove(PREF_KEY)
}

// Episode creation modal ref
const episodeModalRef = ref(null)
const { health } = useSystemHealth()

// System health rows - computed as a list so the template can iterate
const healthRows = computed(() => {
  const s = health.value?.services || {}
  const rows = [
    {
      key: 'database',
      icon: 'mdi-database',
      label: 'Database',
      healthy: s.database === 'connected',
      status: s.database || 'unknown'
    },
    {
      key: 'redis',
      icon: 'mdi-memory',
      label: 'Redis',
      healthy: !!s.redis?.connected,
      status: s.redis?.latency ? `${s.redis.latency}ms` : 'disconnected'
    },
    {
      key: 'celery',
      icon: 'mdi-hammer-wrench',
      label: 'Workers',
      healthy: (s.celery?.workers?.length || 0) > 0,
      status: `${s.celery?.workers?.length || 0} active`
    }
  ]
  if (s.ollama) {
    rows.push({
      key: 'ollama',
      icon: 'mdi-robot',
      label: 'Ollama',
      healthy: s.ollama.status === 'connected',
      status: s.ollama.model || 'offline'
    })
  }
  // Prefer the new "tts" service (Fish Speech / whatever is currently wired up);
  // fall back to legacy "xtts" only if no "tts" is reported and xtts isn't deprecated.
  const tts = s.tts
  if (tts) {
    rows.push({
      key: 'tts',
      icon: 'mdi-microphone',
      label: tts.label ? `TTS (${tts.label})` : 'TTS',
      healthy: !!tts.connected,
      status: tts.connected ? 'online' : (tts.error || 'offline')
    })
  } else if (s.xtts && s.xtts.status !== 'deprecated') {
    rows.push({
      key: 'xtts',
      icon: 'mdi-microphone',
      label: 'TTS',
      healthy: !!s.xtts.connected,
      status: s.xtts.connected ? 'online' : 'offline'
    })
  }
  if (s.nfs) {
    rows.push({
      key: 'nfs',
      icon: 'mdi-folder-network',
      label: 'NFS Storage',
      healthy: s.nfs.status === 'connected',
      status: s.nfs.writable ? 'read/write' : 'error'
    })
  }
  return rows
})

// Reactive data
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

// Quick action handlers
const openEpisodeModal = () => {
  episodeModalRef.value?.open()
}

const createNewEpisode = () => {
  openEpisodeModal()
}

const onEpisodeCreated = (episode) => {
  console.log('Episode created:', episode)
  // Refresh latest-episode info for the iPad banner
  fetchLatestEpisode()
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
  loadLayout()
  fetchLatestEpisode()
})
</script>

<style scoped>
/* ===== Compact dashboard style ===== */
.dash-title {
  display: flex;
  align-items: center;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  padding: 6px 10px !important;
  min-height: 0 !important;
  letter-spacing: 0.3px;
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

/* Deep overrides to compact imported panels (NextShowPanel, TodoPanel, AnnouncementsPanel) */
.dashboard-compact :deep(.v-card-title) {
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  padding: 6px 10px !important;
  min-height: 0 !important;
}

.dashboard-compact :deep(.v-card-text) {
  padding: 8px !important;
  font-size: 0.8rem !important;
}

.dashboard-compact :deep(.v-list-item) {
  min-height: 32px !important;
  padding-inline: 8px !important;
}

.dashboard-compact :deep(.v-list-item__content) {
  padding-block: 2px !important;
}

.dashboard-compact :deep(.v-list-item-title) {
  font-size: 0.85rem !important;
  line-height: 1.2 !important;
}

.dashboard-compact :deep(.v-list-item-subtitle) {
  font-size: 0.72rem !important;
  line-height: 1.2 !important;
}

.dashboard-compact :deep(.v-btn) {
  text-transform: none;
}

/* ===== System Health rows with colored backgrounds ===== */
.health-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
}

.health-row {
  display: flex;
  align-items: center;
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
}

.health-row .health-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.health-row-ok {
  background: #2e7d32; /* darker green for contrast with white text */
  color: #ffffff;
}

.health-row-error {
  background: #c62828; /* darker red for contrast with white text */
  color: #ffffff;
}

.health-row-ok :deep(.v-icon),
.health-row-error :deep(.v-icon) {
  color: #ffffff !important;
}

.health-label {
  flex-shrink: 0;
}

.health-status {
  font-size: 0.72rem;
  opacity: 0.95;
  text-transform: lowercase;
}

/* ===== Draggable column layout ===== */
.dashboard-columns {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.dashboard-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dashboard-column-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 60px; /* allow drop into empty columns */
}

.block-wrap {
  width: 100%;
}

/* Drag handle cursor on headers */
.dash-drag-handle {
  cursor: grab;
  user-select: none;
}

.dash-drag-handle:active {
  cursor: grabbing;
}

/* For imported panels we put the handle class on the wrapper so the title bar is draggable */
.dash-drag-handle-wrap :deep(.v-card-title) {
  cursor: grab;
  user-select: none;
}

.dash-drag-handle-wrap :deep(.v-card-title:active) {
  cursor: grabbing;
}

/* Drag ghost (placeholder where item will land) */
.drag-ghost {
  opacity: 0.4;
  background: rgba(25, 118, 210, 0.1);
  border: 2px dashed #1976d2;
  border-radius: 4px;
}

/* ===== Universal header color for all dashboard blocks (light blue) ===== */
.block-wrap :deep(.v-card-title),
.block-wrap .dash-title {
  background: #64b5f6 !important; /* light blue */
  color: #ffffff !important;
}
.block-wrap :deep(.v-card-title .v-icon),
.block-wrap .dash-title .v-icon {
  color: #ffffff !important;
}

/* ===== Universal button color inside dashboard blocks (blue) ===== */
.block-wrap :deep(.v-btn),
.dashboard-compact :deep(.v-btn) {
  color: #ffffff;
}
.block-wrap :deep(.v-card-title .v-btn),
.block-wrap .dash-title .v-btn {
  color: #ffffff !important;
}
.block-wrap :deep(.v-card-text .v-btn:not(.v-btn--icon)),
.dashboard-compact :deep(.v-card-text .v-btn:not(.v-btn--icon)) {
  background-color: #1976d2 !important;
  color: #ffffff !important;
}

/* Responsive: collapse columns on smaller screens */
@media (max-width: 1264px) {
  .dashboard-columns {
    flex-wrap: wrap;
  }
  .dashboard-column {
    flex: 1 1 calc(33.333% - 10px);
    min-width: 220px;
  }
}

@media (max-width: 960px) {
  .dashboard-column {
    flex: 1 1 calc(50% - 10px);
  }
}

@media (max-width: 600px) {
  .dashboard-column {
    flex: 1 1 100%;
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