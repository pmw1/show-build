<template>
  <v-card class="script-compiler">
    <v-card-title>
      <v-icon left>mdi-file-document-edit</v-icon>
      Script Compilation
    </v-card-title>
    
    <v-card-text>
      <v-row>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="episodeId"
            label="Episode Number"
            placeholder="0225"
            :rules="episodeRules"
            outlined
            dense
          />
        </v-col>
        
        <v-col cols="12" md="6">
          <v-select
            v-model="outputFormat"
            :items="formatOptions"
            label="Output Format"
            outlined
            dense
          />
        </v-col>
      </v-row>
      
      <v-row>
        <v-col cols="12" md="6">
          <v-checkbox
            v-model="includeCues"
            label="Include Cue Blocks"
            dense
          />
        </v-col>
        
        <v-col cols="12" md="6">
          <v-checkbox
            v-model="validateOnly"
            label="Validate Only (no output)"
            dense
          />
        </v-col>
      </v-row>
      
      <!-- Progress Display -->
      <v-card 
        v-if="compilationStatus"
        class="mt-4"
        :color="getStatusColor()"
        dark
      >
        <v-card-text>
          <div class="d-flex align-center">
            <v-icon left>{{ getStatusIcon() }}</v-icon>
            <span class="font-weight-medium">{{ compilationStatus.message || 'Processing...' }}</span>
            <v-spacer />
            <span v-if="compilationStatus.progress !== undefined">
              {{ compilationStatus.progress }}%
            </span>
          </div>
          
          <v-progress-linear
            v-if="compilationStatus.progress !== undefined"
            :value="compilationStatus.progress"
            class="mt-2"
            height="6"
            rounded
          />
          
          <!-- Real-time log messages -->
          <div v-if="logMessages.length > 0" class="mt-3">
            <v-divider class="mb-2" />
            <div class="log-container">
              <div
                v-for="(log, index) in logMessages"
                :key="index"
                class="log-message text-caption"
              >
                {{ log.timestamp }} - {{ log.message }}
              </div>
            </div>
          </div>
          
          <!-- Results -->
          <div v-if="compilationResult" class="mt-3">
            <v-divider class="mb-2" />
            <div class="text-subtitle2 mb-1">Compilation Results:</div>
            <div v-if="compilationResult.output_path" class="mb-1">
              <strong>Output File:</strong> {{ compilationResult.output_path }}
            </div>
            <div v-if="compilationResult.validation">
              <strong>Validation:</strong> 
              <span :class="compilationResult.validation.valid ? 'green--text' : 'red--text'">
                {{ compilationResult.validation.valid ? 'PASSED' : 'FAILED' }}
              </span>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-card-text>
    
    <v-card-actions>
      <v-spacer />
      <v-btn
        color="primary"
        :loading="isCompiling"
        :disabled="!episodeId || !isValidEpisode"
        @click="startCompilation"
      >
        <v-icon left>mdi-play</v-icon>
        {{ validateOnly ? 'Validate' : 'Compile Script' }}
      </v-btn>
      
      <v-btn
        v-if="compilationResult && compilationResult.output_path"
        color="success"
        @click="downloadScript"
      >
        <v-icon left>mdi-download</v-icon>
        Download
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue'

const emit = defineEmits(['compilation-complete', 'compilation-error', 'download-requested'])

const episodeId = ref('')
const outputFormat = ref('html')
const includeCues = ref(true)
const validateOnly = ref(false)
const isCompiling = ref(false)
const compilationStatus = ref(null)
const compilationResult = ref(null)
const currentJobId = ref(null)
const logMessages = ref([])
let websocket = null
const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

const formatOptions = [
  { text: 'HTML', value: 'html' },
  { text: 'PDF', value: 'pdf' },
  { text: 'Text', value: 'txt' }
]
const episodeRules = [
  v => !!v || 'Episode number is required',
  v => /^\d{4}$/.test(v) || 'Episode number must be 4 digits (e.g., 0225)'
]

const isValidEpisode = computed(() => /^\d{4}$/.test(episodeId.value))

function addLogMessage(message) {
  const timestamp = new Date().toLocaleTimeString()
  logMessages.value.push({ timestamp, message })
  if (logMessages.value.length > 20) logMessages.value.shift()
}

function initializeWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`
  websocket = new WebSocket(wsUrl)

  websocket.onopen = () => {
    console.log('WebSocket connected for real-time updates')
    addLogMessage('WebSocket connected')
  }
  websocket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if ((data.type === 'job_update' || data.type === 'job_status') && data.job_id === currentJobId.value) {
      updateCompilationStatus(data.data)
    }
  }
  websocket.onclose = () => {
    console.log('WebSocket disconnected')
    addLogMessage('WebSocket disconnected')
    if (isCompiling.value) setTimeout(initializeWebSocket, 3000)
  }
  websocket.onerror = (error) => {
    console.error('WebSocket error:', error)
    addLogMessage('WebSocket error occurred')
  }
}

function updateCompilationStatus(statusData) {
  compilationStatus.value = {
    status: statusData.status,
    progress: statusData.progress || 0,
    message: statusData.message || statusData.status
  }
  addLogMessage(`Status: ${statusData.status} (${statusData.progress || 0}%)`)
  if (statusData.status === 'completed') handleCompilationComplete(statusData)
  else if (statusData.status === 'failed') handleCompilationError({ message: statusData.message })
}

function handleCompilationComplete(statusData) {
  isCompiling.value = false
  compilationResult.value = statusData.result || statusData
  addLogMessage('Compilation completed successfully!')
  if (compilationResult.value.output_path) addLogMessage(`Output saved to: ${compilationResult.value.output_path}`)
  emit('compilation-complete', { episodeId: episodeId.value, result: compilationResult.value })
}

function handleCompilationError(error) {
  isCompiling.value = false
  compilationStatus.value = { status: 'failed', progress: 0, message: error.message || 'Compilation failed' }
  addLogMessage(`Error: ${error.message || 'Unknown error'}`)
  emit('compilation-error', { episodeId: episodeId.value, error })
}

async function startCompilation() {
  if (!isValidEpisode.value) return
  isCompiling.value = true
  compilationStatus.value = { status: 'starting', progress: 0, message: 'Starting compilation...' }
  compilationResult.value = null
  logMessages.value = []
  addLogMessage('Starting script compilation...')

  try {
    const instance = getCurrentInstance()
    const api = instance?.appContext.config.globalProperties.$api
    const response = await api.post(`/episodes/${episodeId.value}/compile-script`, {
      output_format: outputFormat.value,
      include_cues: includeCues.value,
      validate_only: validateOnly.value
    })
    currentJobId.value = response.data.job_id
    addLogMessage(`Job started with ID: ${currentJobId.value}`)
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ type: 'subscribe_job', job_id: currentJobId.value }))
    }
  } catch (error) {
    console.error('Compilation failed:', error)
    handleCompilationError(error)
  }
}

function getStatusColor() {
  if (!compilationStatus.value) return 'grey'
  const map = { completed: 'success', failed: 'error', running: 'info', starting: 'info' }
  return map[compilationStatus.value.status] || 'grey'
}

function getStatusIcon() {
  if (!compilationStatus.value) return 'mdi-help'
  const map = { completed: 'mdi-check-circle', failed: 'mdi-alert-circle', running: 'mdi-loading', starting: 'mdi-loading' }
  return map[compilationStatus.value.status] || 'mdi-information'
}

function downloadScript() {
  if (compilationResult.value?.output_path) {
    emit('download-requested', { episodeId: episodeId.value, filePath: compilationResult.value.output_path })
  }
}

onMounted(initializeWebSocket)
onBeforeUnmount(() => { websocket?.close() })
</script>

<style scoped>
.script-compiler {
  max-width: 800px;
}

.log-container {
  max-height: 200px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 8px;
}

.log-message {
  font-family: monospace;
  margin-bottom: 2px;
  opacity: 0.9;
}

.log-message:last-child {
  margin-bottom: 0;
}
</style>