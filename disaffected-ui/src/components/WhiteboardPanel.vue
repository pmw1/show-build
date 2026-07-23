<template>
  <v-card elevation="2">
    <v-card-title class="dash-title dash-drag-handle">
      <v-icon size="small" class="me-2">mdi-notebook-edit</v-icon>
      <span>Whiteboard</span>
      <v-spacer />
      <v-chip v-if="pendingCount" size="x-small" color="warning" variant="flat">
        {{ pendingCount }} inbox
      </v-chip>
    </v-card-title>

    <v-card-text class="pa-2">
      <div v-if="!episode" class="wb-empty">
        <v-icon size="28" color="grey-lighten-1">mdi-television-off</v-icon>
        <span>No episode in production</span>
      </div>

      <div v-else-if="loading && !loaded" class="wb-empty">
        <v-progress-circular indeterminate size="22" width="2" color="grey" />
      </div>

      <template v-else>
        <div class="wb-stats">
          <div class="wb-stat">
            <span class="wb-stat-number">{{ cardCount }}</span>
            <span class="wb-stat-label">Cards</span>
          </div>
          <div class="wb-stat">
            <span class="wb-stat-number">{{ linkCount }}</span>
            <span class="wb-stat-label">Links</span>
          </div>
          <div class="wb-stat">
            <span class="wb-stat-number" :class="{ 'wb-attn': pendingCount > 0 }">{{ pendingCount }}</span>
            <span class="wb-stat-label">Inbox</span>
          </div>
        </div>

        <div v-if="pendingCount" class="wb-inbox-hint">
          {{ pendingCount }} capture{{ pendingCount === 1 ? '' : 's' }} waiting to land on the board
        </div>

        <v-btn block variant="outlined" class="wb-open-btn mt-2" @click="openWhiteboard">
          <v-icon start size="small">mdi-notebook-edit</v-icon>
          Open Whiteboard — Ep {{ episode }}
        </v-btn>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const props = defineProps({
  episode: { type: String, default: null },
  pollInterval: { type: Number, default: 30000 }
})

const router = useRouter()
const cardCount = ref(0)
const linkCount = ref(0)
const pendingCount = ref(0)
const loading = ref(false)
const loaded = ref(false)
let pollTimer = null

async function fetchWhiteboardInfo () {
  if (!props.episode) {
    cardCount.value = 0
    linkCount.value = 0
    pendingCount.value = 0
    loaded.value = false
    return
  }
  loading.value = true
  try {
    const [board, captures] = await Promise.all([
      axios.get(`/api/whiteboard/${props.episode}`),
      axios.get(`/api/whiteboard/${props.episode}/captures`, {
        params: { status: 'pending', limit: 200 }
      })
    ])
    cardCount.value = board.data?.items?.length || 0
    linkCount.value = board.data?.node_links?.length || 0
    pendingCount.value = captures.data?.count || 0
    loaded.value = true
  } catch (err) {
    console.warn('WhiteboardPanel: failed to load whiteboard info', err)
  } finally {
    loading.value = false
  }
}

// ScratchpadView resolves its episode from sessionStorage BEFORE the query
// param, so the query alone would open whatever board was last selected there.
// Set both, matching how the episode selector hands off.
function openWhiteboard () {
  if (!props.episode) return
  sessionStorage.setItem('currentEpisode', props.episode)
  router.push({ path: '/whiteboard', query: { episode: props.episode } })
}

watch(() => props.episode, fetchWhiteboardInfo)

onMounted(() => {
  fetchWhiteboardInfo()
  pollTimer = setInterval(fetchWhiteboardInfo, props.pollInterval)
})

onBeforeUnmount(() => clearInterval(pollTimer))
</script>

<style scoped>
.wb-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  font-size: 0.8rem;
  opacity: 0.75;
  text-align: center;
}

.wb-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
}

.wb-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 4px;
  border-radius: 4px;
  background: rgba(128, 128, 128, 0.07);
}

.wb-stat-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1976d2;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.wb-stat-number.wb-attn {
  color: #ef6c00;
}

.wb-stat-label {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.7;
}

.wb-inbox-hint {
  margin-top: 6px;
  font-size: 0.72rem;
  color: #ef6c00;
  text-align: center;
}

.wb-open-btn {
  justify-content: flex-start !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-size: 0.8rem !important;
  min-height: 30px !important;
  height: 30px !important;
  padding: 0 10px !important;
}
</style>
