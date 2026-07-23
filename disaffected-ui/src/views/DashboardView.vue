<template>
  <v-container fluid class="pa-2">
    <!-- On-air rail: fixed at the top, never draggable. Answers "are we ready". -->
    <OnAirRail :episode="railEpisodeNumber" />

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

        <!-- Three fixed zones ordered by urgency. Blocks reorder freely WITHIN a
             zone (drag group is per-zone), so the thing you need in a hurry never
             migrates somewhere unexpected. -->
        <div class="dashboard-zones dashboard-compact">
          <section
            v-for="zone in ZONES"
            :key="zone.id"
            class="zone"
            :class="`zone-${zone.id}`"
          >
            <header class="zone-header">
              <span class="zone-name">{{ zone.label }}</span>
              <span class="zone-hint">{{ zone.hint }}</span>
            </header>

            <!-- Zone 1 leads with the panels that answer "are we ready", pinned
                 ahead of anything draggable. -->
            <div v-if="zone.id === 'tonight'" class="zone-pinned">
              <CurrentShowPanel />
              <BlockersPanel :episode="railEpisodeNumber" />
              <NextShowPanel />
            </div>

            <draggable
              :list="layout[zone.id]"
              :group="`zone-${zone.id}`"
              :item-key="el => el"
              class="zone-grid"
              handle=".dash-drag-handle"
              animation="180"
              ghost-class="drag-ghost"
              @end="saveLayout"
            >
              <template #item="{ element }">
                <div class="block-wrap">

                  <!-- Job feed -->
                  <JobFeedPanel v-if="element === 'job-feed'" class="dash-drag-handle-wrap" />

                  <!-- Announcements -->
                  <AnnouncementsPanel v-else-if="element === 'announcements'" class="dash-drag-handle-wrap" />

                  <!-- Whiteboard: board stats + capture inbox for tonight's
                       episode, with a jump straight to its board. -->
                  <WhiteboardPanel
                    v-else-if="element === 'whiteboard'"
                    :episode="railEpisodeNumber"
                    class="dash-drag-handle-wrap"
                  />

                  <!-- Shortcuts: what survives of the old Tools & Actions and
                       Preproduction button walls. Three destinations, not eleven —
                       the sidebar already covers navigation. -->
                  <v-card v-else-if="element === 'shortcuts'" elevation="2">
                    <v-card-title class="dash-title dash-drag-handle">
                      <v-icon size="small" class="me-2">mdi-lightning-bolt</v-icon>
                      <span>Shortcuts</span>
                    </v-card-title>
                    <v-card-text class="pa-2">
                      <v-btn block variant="outlined" class="dash-row-btn mb-1" @click="createNewEpisode">
                        <v-icon start size="small">mdi-plus-circle</v-icon>
                        New Episode
                      </v-btn>
                      <v-btn block variant="outlined" class="dash-row-btn mb-1" to="/assets">
                        <v-icon start size="small">mdi-cloud-upload</v-icon>
                        Upload Assets
                      </v-btn>
                      <v-btn block variant="outlined" class="dash-row-btn" @click="$router.push('/consolidation')">
                        <v-icon start size="small">mdi-folder-sync</v-icon>
                        Episode Consolidation
                      </v-btn>
                    </v-card-text>
                  </v-card>

                  <!-- Queue coverage: consumers per queue. Catches the failure
                       worker-count can't — every worker up, nobody on `fsq`. -->
                  <v-card v-else-if="element === 'queue-coverage'" elevation="2">
                    <v-card-title class="dash-title dash-drag-handle">
                      <v-icon size="small" class="me-2">mdi-tray-full</v-icon>
                      <span>Queue Coverage</span>
                    </v-card-title>
                    <v-card-text class="pa-2">
                      <div v-if="!queueRows.length" class="text-caption text-grey">
                        No queue data reported
                      </div>
                      <div v-else class="health-grid">
                        <div
                          v-for="q in queueRows"
                          :key="q.name"
                          class="health-row"
                          :class="q.consumers > 0 ? 'health-row-ok' : 'health-row-error'"
                          :title="`${q.name}: ${q.consumers} consumer(s)`"
                        >
                          <span class="health-label">{{ q.name }}</span>
                          <span class="health-count">{{ q.consumers }}</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- System Health -->
                  <v-card v-else-if="element === 'system-health'" elevation="2">
                    <v-card-title class="dash-title dash-drag-handle">
                      <v-icon size="small" class="me-2">mdi-heart-pulse</v-icon>
                      <span>Services</span>
                    </v-card-title>
                    <v-card-text class="pa-2">
                      <div class="health-grid">
                        <div
                          v-for="row in healthRows"
                          :key="row.key"
                          class="health-row"
                          :class="row.healthy ? 'health-row-ok' : 'health-row-error'"
                          :title="`${row.label}: ${row.status}`"
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
          </section>
        </div>
      </v-col>
    </v-row>

    <!-- Episode Creation Modal (hidden activator, triggered programmatically) -->
    <EpisodeScaffoldModal ref="episodeModalRef" @episode-created="onEpisodeCreated" />
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import draggable from 'vuedraggable'
import { useSystemHealth } from '@/composables/useSystemHealth'
import { useUserPrefs } from '@/composables/useUserPrefs'
import AnnouncementsPanel from '@/components/AnnouncementsPanel.vue'
import NextShowPanel from '@/components/NextShowPanel.vue'
import CurrentShowPanel from '@/components/CurrentShowPanel.vue'
import EpisodeScaffoldModal from '@/components/EpisodeScaffoldModal.vue'
import OnAirRail from '@/components/OnAirRail.vue'
import BlockersPanel from '@/components/BlockersPanel.vue'
import JobFeedPanel from '@/components/JobFeedPanel.vue'
import WhiteboardPanel from '@/components/WhiteboardPanel.vue'

// ===== Zone-based dashboard layout =====
// Zones are fixed and ordered by urgency; only their contents rearrange. A new
// panel joins by naming its zone here — no per-panel layout code.
const ZONES = [
  { id: 'tonight', label: 'Tonight', hint: 'the on-air episode' },
  { id: 'pipeline', label: 'Pipeline', hint: 'work in flight' },
  { id: 'system', label: 'System', hint: 'infrastructure' }
]

const DEFAULT_LAYOUT = {
  tonight: [],
  pipeline: ['job-feed', 'whiteboard', 'announcements'],
  system: ['queue-coverage', 'system-health', 'shortcuts']
}

const KNOWN_BLOCKS = Object.values(DEFAULT_LAYOUT).flat()

// Blocks retired in the zone redesign (plus 'todo', retired 2026-07-23 — the
// task list was a dev-era panel). Old persisted layouts still name them, so
// drop them on load rather than rendering an empty slot.
const RETIRED_BLOCKS = ['current-show', 'tools-actions', 'preproduction', 'todo']

// Per-user pref key for the persisted layout. Bumped from `dashboard.layout`
// because the stored shape changed from an array of columns to a zone map.
const PREF_KEY = 'dashboard.zones'
const LEGACY_LAYOUT_KEY = 'dashboard-layout-v3'

const userPrefs = useUserPrefs()
const layout = ref(structuredClone(DEFAULT_LAYOUT))

// Accepts only the zone-map shape. Unknown/retired ids are dropped and any
// block missing entirely is appended to its default zone, so adding a block in
// a later release doesn't leave existing users unable to see it.
function _validateAndApply(parsed) {
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return false
  if (!ZONES.some(z => Array.isArray(parsed[z.id]))) return false

  const next = {}
  const placed = new Set()
  for (const zone of ZONES) {
    next[zone.id] = (parsed[zone.id] || []).filter(id => {
      if (!KNOWN_BLOCKS.includes(id) || RETIRED_BLOCKS.includes(id)) return false
      if (placed.has(id)) return false  // guard against a block duplicated across zones
      placed.add(id)
      return true
    })
  }
  for (const [zoneId, blocks] of Object.entries(DEFAULT_LAYOUT)) {
    for (const id of blocks) {
      if (!placed.has(id)) next[zoneId].push(id)
    }
  }
  layout.value = next
  return true
}

function loadLayout() {
  const userValue = userPrefs.get(PREF_KEY, null)
  if (userValue && _validateAndApply(structuredClone(userValue))) return

  // Pre-zone layouts were an array of columns with no zone information, so
  // there's nothing meaningful to carry forward — start from the defaults and
  // clear the stale key.
  try {
    localStorage.removeItem(LEGACY_LAYOUT_KEY)
  } catch (e) {
    console.warn('Failed to clear legacy dashboard layout:', e)
  }
}

function saveLayout() {
  try {
    userPrefs.set(PREF_KEY, layout.value)
  } catch (e) {
    console.warn('Failed to save dashboard layout:', e)
  }
}

function resetLayout() {
  layout.value = structuredClone(DEFAULT_LAYOUT)
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

// Per-queue consumer counts. A queue at zero consumers is the outage a worker
// count can't show, so those sort to the front.
const queueRows = computed(() => {
  const queues = health.value?.services?.celery?.queues || []
  return [...queues].sort((a, b) => (a.consumers > 0) - (b.consumers > 0))
})

// Reactive data
const latestEpisodeNumber = ref(null)
const productionEpisode = ref(null)

// The rail tracks whatever is on air now, falling back to the newest episode so
// it still reports something useful between productions.
const railEpisodeNumber = computed(
  () => productionEpisode.value?.episode_number || latestEpisodeNumber.value || null
)

// Episode numbers arrive zero-padded ("0283"), so compare them numerically —
// string subtraction happens to coerce today but breaks on any non-numeric id.
const episodeSortKey = (ep) => parseInt(ep?.episode_number ?? ep?.number, 10) || 0

// The list endpoint spells the air date `airdate` and flags test rows as
// `is_dummy`; other callers use `air_date`/`is_test_data`. Normalize once here
// so the rest of this view can read a single shape (matches NextShowPanel).
const normalizeEpisode = (ep) => ({
  ...ep,
  air_date: ep.air_date || ep.airdate,
  number: ep.episode_number || ep.number
})

const isTestEpisode = (ep) => Boolean(ep?.is_dummy ?? ep?.is_test_data)

// Fetch production episode and latest episode for iPad mode buttons
const fetchLatestEpisode = async () => {
  try {
    const response = await axios.get('/api/episodes')
    const episodes = response.data?.episodes || response.data || []
    if (episodes.length > 0) {
      const real = episodes.filter(e => !isTestEpisode(e)).map(normalizeEpisode)

      // Find the episode currently in production
      const inProduction = real.find(e => e.status === 'production')
      if (inProduction) {
        productionEpisode.value = inProduction
      }

      // Sort by episode number descending, pick the highest as fallback
      const sorted = [...real].sort((a, b) => episodeSortKey(b) - episodeSortKey(a))
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

/* Deep overrides to compact imported panels (NextShowPanel, AnnouncementsPanel, WhiteboardPanel) */
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

/* ===== Zone layout ===== */
.dashboard-zones {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.zone-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding-bottom: 5px;
  margin-bottom: 9px;
  border-bottom: 1px solid rgba(128, 128, 128, 0.28);
}

.zone-name {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.13em;
}

.zone-hint {
  font-size: 0.7rem;
  opacity: 0.6;
}

/* Panels tile across the zone and wrap, so a zone grows downward as blocks are
   added rather than forcing a fixed column count. */
.zone-pinned,
.zone-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 10px;
  align-items: start;
}

/* Only separate the pinned row from draggable blocks when there actually are
   some — Tonight has none today, and the gap would otherwise read as a bug. */
.zone-pinned:not(:last-child) {
  margin-bottom: 10px;
}

/* A zone with no draggable blocks (Tonight, today) must not reserve height —
   :empty collapses it, while a zone the user has dragged empty keeps a drop
   target because vuedraggable leaves whitespace/comment nodes behind. */
.zone-grid {
  min-height: 40px; /* allow drop into an emptied zone */
}

.zone-grid:empty {
  min-height: 0;
  display: none;
}

.block-wrap {
  width: 100%;
}

.health-count {
  margin-left: auto;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
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

/* The zone grids are auto-fit, so they reflow without breakpoints. Below the
   minmax floor, drop to a single column. */
@media (max-width: 600px) {
  .zone-pinned,
  .zone-grid {
    grid-template-columns: 1fr;
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