<template>
  <v-container fluid class="poster-studio pa-0">
    <v-row>
      <!-- Left panel: Controls -->
      <v-col cols="12" md="5" lg="4">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="purple">mdi-image-auto-adjust</v-icon>
            Poster Generator
          </v-card-title>
          <v-card-text>
            <!-- Episode selector -->
            <v-autocomplete
              v-model="selectedEpisode"
              :items="episodes"
              item-title="label"
              item-value="episode_number"
              label="Episode"
              prepend-inner-icon="mdi-television"
              variant="outlined"
              density="compact"
              clearable
              return-object
              class="mb-3"
              @update:model-value="onEpisodeSelected"
            />

            <!-- Workflow selector -->
            <v-select
              v-model="selectedWorkflow"
              :items="workflows"
              item-title="name"
              item-value="id"
              label="Workflow"
              prepend-inner-icon="mdi-sitemap"
              variant="outlined"
              density="compact"
              return-object
              class="mb-3"
            />

            <!-- Prompt -->
            <v-textarea
              v-model="prompt"
              label="Prompt"
              placeholder="Describe the poster you want to generate..."
              variant="outlined"
              density="compact"
              rows="3"
              auto-grow
              class="mb-3"
            />

            <!-- Negative prompt -->
            <v-textarea
              v-model="negativePrompt"
              label="Negative Prompt"
              placeholder="What to avoid..."
              variant="outlined"
              density="compact"
              rows="2"
              class="mb-3"
            />

            <!-- Dimensions -->
            <v-row dense class="mb-3">
              <v-col cols="6">
                <v-select
                  v-model="aspectRatio"
                  :items="aspectRatios"
                  item-title="label"
                  item-value="value"
                  label="Aspect Ratio"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="selectedCheckpoint"
                  :items="checkpoints"
                  label="Checkpoint"
                  variant="outlined"
                  density="compact"
                  :loading="loadingCheckpoints"
                />
              </v-col>
            </v-row>

            <!-- Advanced settings -->
            <v-expansion-panels variant="accordion" class="mb-3">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon size="small" class="mr-2">mdi-tune</v-icon>
                  Advanced Settings
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-text-field
                    v-model.number="seed"
                    label="Seed"
                    type="number"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                    hint="-1 for random"
                    persistent-hint
                  />
                  <v-slider
                    v-model="steps"
                    :min="10"
                    :max="50"
                    :step="1"
                    label="Steps"
                    thumb-label
                    class="mb-2"
                  />
                  <v-slider
                    v-model="cfg"
                    :min="1"
                    :max="15"
                    :step="0.5"
                    label="CFG Scale"
                    thumb-label
                    class="mb-2"
                  />
                  <v-select
                    v-model="sampler"
                    :items="samplers"
                    label="Sampler"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  />
                  <v-select
                    v-model="scheduler"
                    :items="schedulers"
                    label="Scheduler"
                    variant="outlined"
                    density="compact"
                  />
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <!-- Generate button -->
            <v-btn
              color="purple"
              block
              size="large"
              :loading="generating"
              :disabled="!prompt || !comfyConnected"
              @click="generatePoster"
            >
              <v-icon start>mdi-creation</v-icon>
              Generate Poster
            </v-btn>

            <!-- ComfyUI status -->
            <div class="d-flex align-center mt-3">
              <v-icon
                :color="comfyConnected ? 'success' : 'error'"
                size="small"
                class="mr-2"
              >
                {{ comfyConnected ? 'mdi-check-circle' : 'mdi-alert-circle' }}
              </v-icon>
              <span class="text-caption" :class="comfyConnected ? 'text-success' : 'text-error'">
                ComfyUI {{ comfyConnected ? 'connected' : 'not available' }}
                <span v-if="comfyConnected && comfyStats"> &mdash; {{ comfyStats }}</span>
              </span>
            </div>
          </v-card-text>
        </v-card>

        <!-- Generation queue -->
        <v-card v-if="jobHistory.length">
          <v-card-title class="text-subtitle-2">
            <v-icon size="small" class="mr-2">mdi-history</v-icon>
            Recent Jobs
          </v-card-title>
          <v-list density="compact">
            <v-list-item
              v-for="job in jobHistory"
              :key="job.prompt_id"
              :class="{ 'bg-purple-lighten-5': job === activeJob }"
              @click="selectJob(job)"
            >
              <template #prepend>
                <v-icon
                  size="small"
                  :color="job.status === 'completed' ? 'success' : job.status === 'running' ? 'warning' : 'error'"
                >
                  {{ job.status === 'completed' ? 'mdi-check' : job.status === 'running' ? 'mdi-loading mdi-spin' : 'mdi-alert' }}
                </v-icon>
              </template>
              <v-list-item-title class="text-caption">{{ job.promptPreview }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption">{{ formatTime(job.created) }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- Right panel: Preview -->
      <v-col cols="12" md="7" lg="8">
        <v-card class="preview-card" min-height="600">
          <v-card-text class="d-flex flex-column align-center justify-center fill-height pa-6">
            <!-- Progress -->
            <div v-if="generating" class="text-center">
              <v-progress-circular
                :model-value="progressPercent"
                :indeterminate="progressPercent === 0"
                color="purple"
                size="80"
                width="6"
              >
                <span v-if="progressPercent > 0" class="text-caption">{{ progressPercent }}%</span>
              </v-progress-circular>
              <p class="text-body-2 mt-4">{{ progressMessage }}</p>
            </div>

            <!-- Generated image -->
            <div v-else-if="generatedImages.length" class="generated-gallery">
              <v-img
                :src="generatedImages[activeImageIndex]"
                max-height="550"
                contain
                class="rounded-lg elevation-2 mb-4"
              />
              <div class="d-flex align-center justify-center ga-2">
                <v-btn
                  v-for="(img, idx) in generatedImages"
                  :key="idx"
                  :color="idx === activeImageIndex ? 'purple' : 'grey'"
                  :variant="idx === activeImageIndex ? 'flat' : 'outlined'"
                  size="x-small"
                  icon
                  @click="activeImageIndex = idx"
                >
                  {{ idx + 1 }}
                </v-btn>
                <v-spacer />
                <v-btn
                  variant="outlined"
                  size="small"
                  color="purple"
                  @click="downloadImage(generatedImages[activeImageIndex])"
                >
                  <v-icon start>mdi-download</v-icon>
                  Download
                </v-btn>
                <v-btn
                  v-if="selectedEpisode"
                  variant="outlined"
                  size="small"
                  color="blue"
                  @click="saveToEpisode"
                >
                  <v-icon start>mdi-content-save</v-icon>
                  Save to Episode
                </v-btn>
              </div>
            </div>

            <!-- Empty state -->
            <div v-else class="text-center">
              <v-icon size="120" color="grey-lighten-2">mdi-image-filter-hdr</v-icon>
              <p class="text-h6 mt-4 text-grey-lighten-1">Generate a poster</p>
              <p class="text-body-2 text-grey">Select an episode, enter a prompt, and hit generate</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// --- State ---
const episodes = ref([])
const selectedEpisode = ref(null)
const selectedWorkflow = ref(null)
const prompt = ref('')
const negativePrompt = ref('text, watermark, blurry, low quality, deformed')
const aspectRatio = ref('16:9')
const selectedCheckpoint = ref('')
const checkpoints = ref([])
const loadingCheckpoints = ref(false)
const seed = ref(-1)
const steps = ref(25)
const cfg = ref(7)
const sampler = ref('euler_ancestral')
const scheduler = ref('normal')
const generating = ref(false)
const progressPercent = ref(0)
const progressMessage = ref('')
const generatedImages = ref([])
const activeImageIndex = ref(0)
const jobHistory = ref([])
const activeJob = ref(null)
const comfyConnected = ref(false)
const comfyStats = ref('')
let ws = null
let pollTimer = null

const aspectRatios = [
  { label: '16:9 (Landscape)', value: '16:9' },
  { label: '9:16 (Portrait)', value: '9:16' },
  { label: '1:1 (Square)', value: '1:1' },
  { label: '4:3 (Standard)', value: '4:3' },
  { label: '3:4 (Portrait Std)', value: '3:4' },
  { label: '21:9 (Ultra Wide)', value: '21:9' }
]

const workflows = ref([
  { id: 'txt2img', name: 'Text to Image' },
  { id: 'img2img', name: 'Image to Image (coming soon)', disabled: true }
])

const samplers = ['euler', 'euler_ancestral', 'dpmpp_2m', 'dpmpp_2m_sde', 'dpmpp_3m_sde', 'ddim', 'uni_pc']
const schedulers = ['normal', 'karras', 'exponential', 'sgm_uniform']

// --- Helpers ---
function getDimensions(ratio) {
  const dims = {
    '16:9': [1024, 576],
    '9:16': [576, 1024],
    '1:1': [1024, 1024],
    '4:3': [1024, 768],
    '3:4': [768, 1024],
    '21:9': [1024, 440]
  }
  return dims[ratio] || [1024, 576]
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString()
}

// --- ComfyUI API ---
async function checkComfyConnection() {
  try {
    const res = await fetch('/api/comfyui/health', {
      headers: { Authorization: `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}` }
    })
    if (res.ok) {
      const data = await res.json()
      comfyConnected.value = data.connected
      comfyStats.value = data.stats || ''
      if (data.checkpoints) {
        checkpoints.value = data.checkpoints
        if (checkpoints.value.length && !selectedCheckpoint.value) {
          selectedCheckpoint.value = checkpoints.value[0]
        }
      }
    }
  } catch {
    comfyConnected.value = false
  }
}

async function generatePoster() {
  if (!prompt.value) return
  generating.value = true
  progressPercent.value = 0
  progressMessage.value = 'Submitting to ComfyUI...'
  generatedImages.value = []
  activeImageIndex.value = 0

  const [width, height] = getDimensions(aspectRatio.value)
  const payload = {
    prompt: prompt.value,
    negative_prompt: negativePrompt.value,
    checkpoint: selectedCheckpoint.value,
    width,
    height,
    seed: seed.value,
    steps: steps.value,
    cfg: cfg.value,
    sampler: sampler.value,
    scheduler: scheduler.value,
    episode_number: selectedEpisode.value?.episode_number || null
  }

  try {
    const res = await fetch('/api/comfyui/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    const data = await res.json()
    const promptId = data.prompt_id

    const job = {
      prompt_id: promptId,
      promptPreview: prompt.value.substring(0, 60),
      status: 'running',
      created: new Date().toISOString()
    }
    jobHistory.value.unshift(job)
    activeJob.value = job

    // Poll for completion
    pollForResult(promptId, job)
  } catch (err) {
    progressMessage.value = `Error: ${err.message}`
    setTimeout(() => { generating.value = false }, 3000)
  }
}

async function pollForResult(promptId, job) {
  progressMessage.value = 'Generating...'
  const maxAttempts = 120  // 10 min max
  let attempts = 0

  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > maxAttempts) {
      clearInterval(pollTimer)
      generating.value = false
      job.status = 'error'
      progressMessage.value = 'Timed out waiting for result'
      return
    }

    try {
      const res = await fetch(`/api/comfyui/status/${promptId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}` }
      })
      if (!res.ok) return

      const data = await res.json()

      if (data.progress !== undefined) {
        progressPercent.value = Math.round(data.progress * 100)
        progressMessage.value = `Generating... ${progressPercent.value}%`
      }

      if (data.status === 'completed' && data.images) {
        clearInterval(pollTimer)
        generatedImages.value = data.images.map(img => `/api/comfyui/image/${img}`)
        job.status = 'completed'
        generating.value = false
        progressMessage.value = ''
      } else if (data.status === 'error') {
        clearInterval(pollTimer)
        job.status = 'error'
        generating.value = false
        progressMessage.value = `Error: ${data.error || 'Generation failed'}`
      }
    } catch {
      // Network error, keep polling
    }
  }, 5000)
}

function selectJob(job) {
  activeJob.value = job
  if (job.status === 'completed' && job.prompt_id) {
    // Reload images for this job
    fetch(`/api/comfyui/status/${job.prompt_id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}` }
    })
      .then(r => r.json())
      .then(data => {
        if (data.images) {
          generatedImages.value = data.images.map(img => `/api/comfyui/image/${img}`)
          activeImageIndex.value = 0
        }
      })
      .catch(() => {})
  }
}

function downloadImage(url) {
  const a = document.createElement('a')
  a.href = url
  a.download = `poster-${Date.now()}.png`
  a.click()
}

async function saveToEpisode() {
  if (!selectedEpisode.value || !generatedImages.value.length) return
  const imgUrl = generatedImages.value[activeImageIndex.value]
  try {
    const res = await fetch('/api/comfyui/save-to-episode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        image_url: imgUrl,
        episode_number: selectedEpisode.value.episode_number
      })
    })
    if (res.ok) {
      // Could show snackbar here
    }
  } catch {
    // Error handling
  }
}

// --- Episodes ---
async function loadEpisodes() {
  try {
    const res = await fetch('/api/episodes', {
      headers: { Authorization: `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}` }
    })
    if (res.ok) {
      const data = await res.json()
      const list = Array.isArray(data) ? data : data.episodes || []
      episodes.value = list.map(e => ({
        ...e,
        label: `${String(e.episode_number).padStart(4, '0')} - ${e.title || 'Untitled'}`
      })).sort((a, b) => b.episode_number - a.episode_number)
    }
  } catch { /* ignore */ }
}

function onEpisodeSelected(ep) {
  if (ep && ep.title && !prompt.value) {
    prompt.value = `Episode poster for "${ep.title}"`
  }
}

// --- Lifecycle ---
onMounted(() => {
  loadEpisodes()
  checkComfyConnection()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (ws) ws.close()
})
</script>

<style scoped>
.poster-studio {
  max-width: 1600px;
}
.preview-card {
  min-height: 600px;
  display: flex;
}
.preview-card .v-card-text {
  flex: 1;
}
.generated-gallery {
  width: 100%;
  text-align: center;
}
</style>
