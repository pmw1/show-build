<template>
  <v-card elevation="2">
    <v-card-title class="dash-title dash-drag-handle">
      <v-icon size="small" class="me-2">mdi-alert-octagon</v-icon>
      <span>Blockers</span>
      <v-spacer />
      <v-chip v-if="blockers.length" size="x-small" color="error" variant="flat">
        {{ blockers.length }}
      </v-chip>
    </v-card-title>

    <v-card-text class="pa-2">
      <div v-if="!episode" class="blockers-empty">
        <v-icon size="28" color="grey-lighten-1">mdi-television-off</v-icon>
        <span>No episode in production</span>
      </div>

      <div v-else-if="loading && !readiness" class="blockers-empty">
        <v-progress-circular indeterminate size="22" width="2" color="grey" />
      </div>

      <div v-else-if="!blockers.length" class="blockers-clear">
        <v-icon size="28" color="success">mdi-check-circle</v-icon>
        <span>Nothing blocking episode {{ episode }}</span>
      </div>

      <div v-else class="blockers-list">
        <button
          v-for="b in blockers"
          :key="b.stage"
          type="button"
          class="blocker"
          :class="`blocker-${b.severity}`"
          @click="goTo(b)"
        >
          <v-icon size="small" class="blocker-icon">{{ iconFor(b.stage) }}</v-icon>
          <span class="blocker-body">
            <span class="blocker-msg">{{ b.message }}</span>
            <span class="blocker-stage">{{ b.stage }}</span>
          </span>
          <v-icon size="small" class="blocker-go">mdi-chevron-right</v-icon>
        </button>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const props = defineProps({
  episode: { type: String, default: null },
  pollInterval: { type: Number, default: 30000 }
})

const router = useRouter()
const readiness = ref(null)
const loading = ref(false)
let pollTimer = null

const blockers = computed(() => readiness.value?.blockers || [])

const STAGE_ICONS = {
  scripts: 'mdi-script-text-outline',
  sots: 'mdi-filmstrip',
  graphics: 'mdi-image-multiple',
  timing: 'mdi-timer-alert-outline'
}

function iconFor (stage) {
  return STAGE_ICONS[stage] || 'mdi-alert'
}

// Each blocker deep-links to the surface that actually resolves it, rather than
// dumping the user on a generic page to hunt for the failure themselves.
function goTo (blocker) {
  if (!props.episode) return
  if (blocker.stage === 'sots' || blocker.stage === 'graphics') {
    router.push('/tools?tab=jobs')
  } else {
    router.push(`/content-editor/${props.episode}`)
  }
}

async function fetchReadiness () {
  if (!props.episode) {
    readiness.value = null
    return
  }
  loading.value = true
  try {
    const { data } = await axios.get(`/api/episodes/${props.episode}/readiness`)
    readiness.value = data
  } catch (err) {
    console.warn('BlockersPanel: failed to load readiness', err)
    readiness.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.episode, fetchReadiness)

onMounted(() => {
  fetchReadiness()
  pollTimer = setInterval(fetchReadiness, props.pollInterval)
})

onBeforeUnmount(() => clearInterval(pollTimer))
</script>

<style scoped>
.blockers-empty,
.blockers-clear {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  font-size: 0.8rem;
  opacity: 0.75;
  text-align: center;
}

.blockers-clear {
  opacity: 1;
}

.blockers-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.blocker {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 7px 9px;
  border-radius: 5px;
  border: 1px solid transparent;
  border-left-width: 3px;
  background: rgba(128, 128, 128, 0.07);
  text-align: left;
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition: background 0.15s ease;
}

.blocker:hover {
  background: rgba(128, 128, 128, 0.16);
}

.blocker-fault {
  border-left-color: #c62828;
  color: #c62828;
}

.blocker-warn {
  border-left-color: #ef6c00;
  color: #ef6c00;
}

.blocker-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.blocker-msg {
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.25;
}

.blocker-stage {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  opacity: 0.7;
}

.blocker-icon,
.blocker-go {
  flex: none;
}

.blocker-go {
  opacity: 0.5;
}
</style>
