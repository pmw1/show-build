<template>
  <div>
    <v-card flat class="pa-3 mb-3" color="grey-lighten-5">
      <v-row align="center" no-gutters>
        <v-col cols="12" md="5">
          <v-autocomplete
            v-model="selectedEpisode"
            :items="episodes"
            :loading="loadingEpisodes"
            item-title="display"
            item-value="episode_number"
            label="Episode"
            density="comfortable"
            hide-details
            clearable
            prepend-inner-icon="mdi-television-classic"
          />
        </v-col>
        <v-col cols="12" md="7" class="d-flex align-center justify-end pl-md-3 mt-3 mt-md-0">
          <v-chip
            v-if="sessionsResp"
            size="small"
            class="mr-2"
            variant="tonal"
          >
            {{ sessionsResp.session_count }} session{{ sessionsResp.session_count === 1 ? '' : 's' }}
          </v-chip>
          <v-btn
            variant="text"
            density="comfortable"
            prepend-icon="mdi-refresh"
            :loading="loadingSessions"
            :disabled="!selectedEpisode"
            @click="loadSessions"
          >
            Refresh
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Empty state: no episode picked -->
    <v-card v-if="!selectedEpisode" flat class="pa-8 text-center" color="transparent">
      <v-icon size="64" color="grey-lighten-1">mdi-record-rec</v-icon>
      <h3 class="text-h6 mt-4 text-grey">Pick an episode</h3>
      <p class="text-grey">Choose an episode above to see recording sessions fed back from showtime.</p>
    </v-card>

    <!-- Empty state: episode picked, no sessions -->
    <v-card
      v-else-if="sessionsResp && sessionsResp.session_count === 0"
      flat
      class="pa-8 text-center"
      color="transparent"
    >
      <v-icon size="64" color="grey-lighten-1">mdi-database-off-outline</v-icon>
      <h3 class="text-h6 mt-4 text-grey">No recording sessions yet</h3>
      <p class="text-grey">
        Episode {{ selectedEpisode }} hasn't received any showtime manifest data.
      </p>
    </v-card>

    <!-- Error -->
    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      density="comfortable"
      class="mb-3"
      closable
      @click:close="errorMessage = ''"
    >
      {{ errorMessage }}
    </v-alert>

    <!-- Sessions list -->
    <v-expansion-panels
      v-if="sessionsResp && sessionsResp.sessions.length > 0"
      v-model="openSessionIds"
      multiple
      variant="accordion"
    >
      <v-expansion-panel
        v-for="session in sessionsResp.sessions"
        :key="session.id"
        :value="session.id"
        @group:selected="onSessionExpanded(session.id, $event)"
      >
        <v-expansion-panel-title>
          <div class="d-flex align-center flex-wrap" style="width: 100%; gap: 8px;">
            <v-chip
              size="small"
              :color="sessionKindColor(session.session_kind)"
              variant="flat"
            >
              {{ session.session_kind }}
            </v-chip>
            <v-chip size="small" :color="statusColor(session.status)" variant="tonal">
              {{ session.status }}
            </v-chip>
            <span class="text-body-2 font-weight-medium">
              {{ formatWallclock(session.started_at) }}
            </span>
            <span class="text-caption text-grey">
              {{ session.operator || 'no operator' }}
              {{ session.host_machine ? `@ ${session.host_machine}` : '' }}
            </span>
            <v-spacer />
            <span class="text-caption">
              {{ session.take_count }} take{{ session.take_count === 1 ? '' : 's' }}
              <span v-if="session.total_duration_seconds != null">
                · {{ formatDuration(session.total_duration_seconds) }}
              </span>
            </span>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <SessionDetail
            v-if="sessionDetails[session.id]"
            :session="sessionDetails[session.id]"
          />
          <div v-else-if="loadingSessionId === session.id" class="text-center pa-4">
            <v-progress-circular indeterminate color="amber-darken-2" />
          </div>
          <div v-else class="text-center pa-4 text-grey text-caption">
            Expand to load detail.
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'
import SessionDetail from './SessionDetail.vue'

const episodes = ref([])
const loadingEpisodes = ref(false)
const selectedEpisode = ref(null)

const sessionsResp = ref(null)
const loadingSessions = ref(false)
const errorMessage = ref('')

const openSessionIds = ref([])
const sessionDetails = ref({})
const loadingSessionId = ref(null)

async function loadEpisodes() {
  loadingEpisodes.value = true
  try {
    const resp = await axios.get('/api/episodes')
    const list = Array.isArray(resp.data) ? resp.data : (resp.data?.episodes || [])
    episodes.value = list
      .filter(e => e.episode_number != null)
      .sort((a, b) => Number(b.episode_number) - Number(a.episode_number))
      .map(e => ({
        episode_number: String(e.episode_number),
        display: `${e.episode_number} — ${e.title || e.slug || 'Untitled'}`,
      }))
  } catch (err) {
    errorMessage.value = `Failed to load episodes: ${err.response?.data?.detail || err.message}`
  } finally {
    loadingEpisodes.value = false
  }
}

async function loadSessions() {
  if (!selectedEpisode.value) return
  loadingSessions.value = true
  errorMessage.value = ''
  sessionsResp.value = null
  sessionDetails.value = {}
  openSessionIds.value = []
  try {
    const resp = await axios.get(
      `/api/episodes/${selectedEpisode.value}/recording-sessions`,
    )
    sessionsResp.value = resp.data
  } catch (err) {
    if (err.response?.status === 404) {
      // Episode exists in dropdown but has no recording-sessions endpoint
      // result (treat as zero sessions rather than error).
      sessionsResp.value = {
        episode_number: selectedEpisode.value,
        session_count: 0,
        sessions: [],
      }
    } else {
      errorMessage.value = `Failed to load sessions: ${err.response?.data?.detail || err.message}`
    }
  } finally {
    loadingSessions.value = false
  }
}

async function loadSessionDetail(sessionId) {
  if (sessionDetails.value[sessionId]) return
  loadingSessionId.value = sessionId
  try {
    const resp = await axios.get(`/api/recording-sessions/${sessionId}`)
    sessionDetails.value = { ...sessionDetails.value, [sessionId]: resp.data }
  } catch (err) {
    errorMessage.value = `Failed to load session ${sessionId}: ${err.response?.data?.detail || err.message}`
  } finally {
    loadingSessionId.value = null
  }
}

// v-expansion-panels emits `group:selected` per panel; we just key off
// the visible openSessionIds array via a watcher to keep things simple.
watch(openSessionIds, (now) => {
  for (const id of now) {
    if (!sessionDetails.value[id]) {
      loadSessionDetail(id)
    }
  }
}, { deep: true })

watch(selectedEpisode, () => {
  if (selectedEpisode.value) {
    loadSessions()
  } else {
    sessionsResp.value = null
    sessionDetails.value = {}
    openSessionIds.value = []
  }
})

function onSessionExpanded() {
  // No-op — watcher on openSessionIds handles fetch. Kept for the
  // template binding so future per-panel logic has a hook.
}

function sessionKindColor(kind) {
  switch (kind) {
    case 'live': return 'red-darken-1'
    case 'rehearsal': return 'blue-darken-1'
    case 'retake': return 'orange-darken-2'
    case 'pickup-session': return 'purple-darken-1'
    default: return 'grey-darken-1'
  }
}

function statusColor(status) {
  switch (status) {
    case 'wrapped': return 'green'
    case 'in_progress': return 'amber-darken-2'
    case 'aborted': return 'red'
    default: return 'grey'
  }
}

function formatWallclock(iso) {
  if (!iso) return 'unknown time'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function formatDuration(seconds) {
  if (seconds == null) return ''
  const total = Math.round(seconds)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

onMounted(() => {
  loadEpisodes()
})
</script>

<style scoped>
.unmanaged-data {
  /* nothing yet — parent view sets max-width */
}
</style>
