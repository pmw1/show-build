<template>
  <v-card v-if="readiness" class="on-air-rail mb-3" :class="railClass" elevation="2">
    <div class="rail-inner">
      <!-- Episode identity -->
      <router-link :to="`/content-editor/${readiness.episode}`" class="rail-id">
        <span class="rail-ep">{{ readiness.episode }}</span>
        <span class="rail-meta">
          <span class="rail-title">{{ readiness.title || 'Untitled Episode' }}</span>
          <span class="rail-sub">
            {{ readiness.stages.rundown.total }} items · {{ formattedDuration }} built
          </span>
        </span>
      </router-link>

      <!-- Stage tallies -->
      <div class="rail-tallies">
        <span
          v-for="t in tallies"
          :key="t.key"
          class="tally"
          :class="`tally-${t.level}`"
          :title="t.title"
        >
          <span class="tally-dot" />
          {{ t.label }}
        </span>
      </div>

      <!-- Countdown -->
      <div class="rail-clock" :class="`clock-${countdown.level}`">
        <span class="clock-time">{{ countdown.text }}</span>
        <span class="clock-label">{{ countdown.label }}</span>
      </div>
    </div>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  // Episode number to track. When absent the rail stays hidden.
  episode: { type: String, default: null },
  // Readiness is cheap to compute but hits three tables; 30s matches the
  // cadence of the rest of Zone 1.
  pollInterval: { type: Number, default: 30000 }
})

const readiness = ref(null)
const now = ref(new Date())

let pollTimer = null
let clockTimer = null

async function fetchReadiness () {
  if (!props.episode) return
  try {
    const { data } = await axios.get(`/api/episodes/${props.episode}/readiness`)
    readiness.value = data
  } catch (err) {
    console.warn('OnAirRail: failed to load readiness', err)
    readiness.value = null
  }
}

// A stage is a fault if anything is blocked, a warning if incomplete, ok when
// every unit is done. Stages with nothing to do are omitted rather than shown
// as a hollow green chip.
function stageLevel (stage) {
  if (!stage || stage.total === 0) return null
  if (stage.blocked > 0) return 'fault'
  return stage.done >= stage.total ? 'ok' : 'warn'
}

const STAGE_LABELS = {
  scripts: 'SCRIPTS',
  sots: 'SOT',
  graphics: 'GFX',
  timing: 'TIMED'
}

const tallies = computed(() => {
  const stages = readiness.value?.stages || {}
  return Object.entries(STAGE_LABELS)
    .map(([key, label]) => {
      const stage = stages[key]
      const level = stageLevel(stage)
      if (!level) return null
      const blocked = stage.blocked > 0 ? ` · ${stage.blocked} failed` : ''
      return {
        key,
        level,
        label: `${label} ${stage.done}/${stage.total}`,
        title: `${label}: ${stage.done} of ${stage.total} complete${blocked}`
      }
    })
    .filter(Boolean)
})

// Any fault anywhere turns the whole rail red — the point is that a glance at
// the top of the page is enough.
const railClass = computed(() => {
  if (tallies.value.some(t => t.level === 'fault')) return 'rail-fault'
  if (tallies.value.some(t => t.level === 'warn')) return 'rail-warn'
  return 'rail-ok'
})

const formattedDuration = computed(() => {
  const total = readiness.value?.total_duration_seconds || 0
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    : `${m}:${String(s).padStart(2, '0')}`
})

const countdown = computed(() => {
  const airDate = readiness.value?.air_date
  if (!airDate) return { text: '--:--:--', label: 'no air date', level: 'idle' }

  const diff = new Date(airDate) - now.value
  if (diff <= 0) {
    const since = Math.abs(diff)
    // Past its air date — show elapsed rather than a stuck zero.
    return {
      text: formatClock(since),
      label: since > 86400000 ? 'since air' : 'on air',
      level: since > 86400000 ? 'idle' : 'live'
    }
  }
  return {
    text: formatClock(diff),
    label: 'to air',
    level: diff < 3600000 ? 'live' : diff < 21600000 ? 'soon' : 'idle'
  }
})

function formatClock (ms) {
  const total = Math.floor(ms / 1000)
  const d = Math.floor(total / 86400)
  const h = Math.floor((total % 86400) / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const pad = n => String(n).padStart(2, '0')
  return d > 0 ? `${d}d ${pad(h)}:${pad(m)}` : `${pad(h)}:${pad(m)}:${pad(s)}`
}

// The parent resolves the episode number asynchronously, so it is still null on
// mount. Without this the rail would sit empty until the first poll tick.
watch(() => props.episode, fetchReadiness)

onMounted(() => {
  fetchReadiness()
  pollTimer = setInterval(fetchReadiness, props.pollInterval)
  clockTimer = setInterval(() => { now.value = new Date() }, 1000)
})

onBeforeUnmount(() => {
  clearInterval(pollTimer)
  clearInterval(clockTimer)
})

defineExpose({ refresh: fetchReadiness })
</script>

<style scoped>
.on-air-rail {
  border-left: 5px solid var(--rail-accent, #9e9e9e);
  border-radius: 8px !important;
}

.rail-ok    { --rail-accent: #2e7d32; }
.rail-warn  { --rail-accent: #ef6c00; }
.rail-fault { --rail-accent: #c62828; }

.rail-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 18px;
  padding: 10px 14px;
}

/* --- identity --- */
.rail-id {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1 1 260px;
  text-decoration: none;
  color: inherit;
}

.rail-id:hover .rail-title {
  text-decoration: underline;
}

/* Deliberately NOT tinted by the rail state — colouring the episode number red
   reads as "this episode is broken" rather than "a stage needs attention".
   The border, tallies, and clock carry the status. */
.rail-ep {
  font-family: 'Courier New', monospace;
  font-size: 1.6rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.rail-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.rail-title {
  font-size: 0.98rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rail-sub {
  font-size: 0.75rem;
  opacity: 0.7;
  font-variant-numeric: tabular-nums;
}

/* --- tallies --- */
.rail-tallies {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tally {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 3px 9px;
  border-radius: 99px;
  border: 1px solid currentColor;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.tally-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex: none;
}

.tally-ok    { color: #2e7d32; background: rgba(46, 125, 50, 0.10); }
.tally-warn  { color: #ef6c00; background: rgba(239, 108, 0, 0.10); }
.tally-fault { color: #c62828; background: rgba(198, 40, 40, 0.10); }

/* --- countdown --- */
.rail-clock {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: auto;
  line-height: 1.1;
}

.clock-time {
  font-family: 'Courier New', monospace;
  font-size: 1.3rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.clock-label {
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  opacity: 0.65;
}

.clock-live { color: #c62828; }
.clock-soon { color: #ef6c00; }
.clock-idle { color: inherit; }

@media (max-width: 700px) {
  .rail-clock {
    margin-left: 0;
    align-items: flex-start;
  }
}
</style>
