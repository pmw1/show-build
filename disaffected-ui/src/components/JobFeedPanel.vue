<template>
  <v-card elevation="2">
    <v-card-title class="dash-title dash-drag-handle">
      <v-icon size="small" class="me-2">mdi-cog-sync</v-icon>
      <span>Job Feed</span>
      <v-spacer />
      <v-chip v-if="activeJobs.length" size="x-small" color="info" variant="flat">
        {{ activeJobs.length }} running
      </v-chip>
    </v-card-title>

    <v-card-text class="pa-2">
      <div v-if="loading && !jobs.length" class="jobs-empty">
        <v-progress-circular indeterminate size="22" width="2" color="grey" />
      </div>

      <div v-else-if="!jobs.length" class="jobs-empty">
        <v-icon size="26" color="grey-lighten-1">mdi-sleep</v-icon>
        <span>No recent jobs</span>
      </div>

      <div v-else class="jobs-list">
        <div
          v-for="job in jobs"
          :key="job.task_id"
          class="job"
          :class="`job-${statusClass(job.status)}`"
        >
          <span class="job-dot" />
          <span class="job-body">
            <span class="job-name">{{ job.display_name || job.task_name }}</span>
            <span class="job-meta">
              <span v-if="job.episode">ep {{ job.episode }}</span>
              <span v-if="job.queue">{{ job.queue }}</span>
              <span v-if="job.worker">{{ shortWorker(job.worker) }}</span>
            </span>
            <!-- Failures carry their reason inline; that's the whole point of
                 surfacing them here rather than making the user open a log. -->
            <span v-if="job.status === 'failed' && job.result_summary" class="job-error">
              {{ truncate(job.result_summary) }}
            </span>
          </span>
          <v-progress-circular
            v-if="job.status === 'running'"
            :model-value="job.progress || 0"
            :indeterminate="job.progress == null"
            size="20"
            width="2"
            color="info"
          />
          <span v-else class="job-status">{{ job.status }}</span>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

const props = defineProps({
  limit: { type: Number, default: 8 },
  // Poll faster while work is in flight, slower when the queue is idle.
  activeInterval: { type: Number, default: 15000 },
  idleInterval: { type: Number, default: 60000 }
})

const jobs = ref([])
const loading = ref(false)
let pollTimer = null

const activeJobs = computed(() =>
  jobs.value.filter(j => j.status === 'running' || j.status === 'pending')
)

function statusClass (status) {
  if (status === 'failed') return 'failed'
  if (status === 'running' || status === 'pending') return 'active'
  return 'done'
}

function shortWorker (worker) {
  return String(worker).split('@').pop()
}

function truncate (text, max = 90) {
  const s = String(text).replace(/\s+/g, ' ').trim()
  return s.length > max ? `${s.slice(0, max)}…` : s
}

async function fetchJobs () {
  loading.value = true
  try {
    const { data } = await axios.get('/api/celery-jobs/all', {
      params: { limit: props.limit }
    })
    const all = data?.jobs || []
    // Failures float to the top — they need a human. Everything else keeps
    // the API's newest-first ordering.
    jobs.value = [
      ...all.filter(j => j.status === 'failed'),
      ...all.filter(j => j.status !== 'failed')
    ].slice(0, props.limit)
  } catch (err) {
    console.warn('JobFeedPanel: failed to load jobs', err)
  } finally {
    loading.value = false
    scheduleNext()
  }
}

// Re-arm after each response so a slow request can't stack up overlapping polls.
function scheduleNext () {
  clearTimeout(pollTimer)
  const delay = activeJobs.value.length ? props.activeInterval : props.idleInterval
  pollTimer = setTimeout(fetchJobs, delay)
}

onMounted(fetchJobs)
onBeforeUnmount(() => clearTimeout(pollTimer))
</script>

<style scoped>
.jobs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  font-size: 0.8rem;
  opacity: 0.7;
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.job {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 5px;
  background: rgba(128, 128, 128, 0.07);
}

.job-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex: none;
  background: #9e9e9e;
}

.job-failed .job-dot { background: #c62828; }
.job-active .job-dot { background: #1976d2; }
.job-done   .job-dot { background: #2e7d32; }

.job-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.job-name {
  font-size: 0.79rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.job-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.66rem;
  opacity: 0.65;
  font-family: 'Courier New', monospace;
}

.job-error {
  font-size: 0.68rem;
  color: #c62828;
  line-height: 1.3;
  margin-top: 1px;
}

.job-status {
  font-size: 0.64rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.6;
  flex: none;
}
</style>
