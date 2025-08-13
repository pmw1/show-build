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

<script>
export default {
  name: 'ScriptCompiler',
  
  data() {
    return {
      episodeId: '',
      outputFormat: 'html',
      includeCues: true,
      validateOnly: false,
      
      // Compilation state
      isCompiling: false,
      compilationStatus: null,
      compilationResult: null,
      currentJobId: null,
      
      // WebSocket connection
      websocket: null,
      clientId: `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      
      // Real-time logging
      logMessages: [],
      
      // Options
      formatOptions: [
        { text: 'HTML', value: 'html' },
        { text: 'PDF', value: 'pdf' },
        { text: 'Text', value: 'txt' }
      ],
      
      // Validation rules
      episodeRules: [
        v => !!v || 'Episode number is required',
        v => /^\d{4}$/.test(v) || 'Episode number must be 4 digits (e.g., 0225)'
      ]
    }
  },
  
  computed: {
    isValidEpisode() {
      return /^\d{4}$/.test(this.episodeId)
    }
  },
  
  mounted() {
    this.initializeWebSocket()
  },
  
  beforeUnmount() {
    if (this.websocket) {
      this.websocket.close()
    }
  },
  
  methods: {
    initializeWebSocket() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`
      
      this.websocket = new WebSocket(wsUrl)
      
      this.websocket.onopen = () => {
        console.log('WebSocket connected for real-time updates')
        this.addLogMessage('WebSocket connected')
      }
      
      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.handleWebSocketMessage(data)
      }
      
      this.websocket.onclose = () => {
        console.log('WebSocket disconnected')
        this.addLogMessage('WebSocket disconnected')
        
        // Reconnect after delay if we're still compiling
        if (this.isCompiling) {
          setTimeout(() => this.initializeWebSocket(), 3000)
        }
      }
      
      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.addLogMessage('WebSocket error occurred')
      }
    },
    
    handleWebSocketMessage(data) {
      if (data.type === 'job_update' && data.job_id === this.currentJobId) {
        this.updateCompilationStatus(data.data)
      } else if (data.type === 'job_status' && data.job_id === this.currentJobId) {
        this.updateCompilationStatus(data.data)
      }
    },
    
    async startCompilation() {
      if (!this.isValidEpisode) return
      
      this.isCompiling = true
      this.compilationStatus = { 
        status: 'starting', 
        progress: 0, 
        message: 'Starting compilation...' 
      }
      this.compilationResult = null
      this.logMessages = []
      this.addLogMessage('Starting script compilation...')
      
      try {
        const response = await this.$api.post(`/episodes/${this.episodeId}/compile-script`, {
          output_format: this.outputFormat,
          include_cues: this.includeCues,
          validate_only: this.validateOnly
        })
        
        this.currentJobId = response.data.job_id
        this.addLogMessage(`Job started with ID: ${this.currentJobId}`)
        
        // Subscribe to job updates via WebSocket
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.send(JSON.stringify({
            type: 'subscribe_job',
            job_id: this.currentJobId
          }))
        }
        
      } catch (error) {
        console.error('Compilation failed:', error)
        this.handleCompilationError(error)
      }
    },
    
    updateCompilationStatus(statusData) {
      this.compilationStatus = {
        status: statusData.status,
        progress: statusData.progress || 0,
        message: statusData.message || statusData.status
      }
      
      this.addLogMessage(`Status: ${statusData.status} (${statusData.progress || 0}%)`)
      
      if (statusData.status === 'completed') {
        this.handleCompilationComplete(statusData)
      } else if (statusData.status === 'failed') {
        this.handleCompilationError({ message: statusData.message })
      }
    },
    
    handleCompilationComplete(statusData) {
      this.isCompiling = false
      this.compilationResult = statusData.result || statusData
      
      this.addLogMessage('Compilation completed successfully!')
      
      if (this.compilationResult.output_path) {
        this.addLogMessage(`Output saved to: ${this.compilationResult.output_path}`)
      }
      
      this.$emit('compilation-complete', {
        episodeId: this.episodeId,
        result: this.compilationResult
      })
    },
    
    handleCompilationError(error) {
      this.isCompiling = false
      this.compilationStatus = {
        status: 'failed',
        progress: 0,
        message: error.message || 'Compilation failed'
      }
      
      this.addLogMessage(`Error: ${error.message || 'Unknown error'}`)
      
      this.$emit('compilation-error', {
        episodeId: this.episodeId,
        error: error
      })
    },
    
    getStatusColor() {
      if (!this.compilationStatus) return 'grey'
      
      switch (this.compilationStatus.status) {
        case 'completed': return 'success'
        case 'failed': return 'error'
        case 'running': case 'starting': return 'info'
        default: return 'grey'
      }
    },
    
    getStatusIcon() {
      if (!this.compilationStatus) return 'mdi-help'
      
      switch (this.compilationStatus.status) {
        case 'completed': return 'mdi-check-circle'
        case 'failed': return 'mdi-alert-circle'
        case 'running': case 'starting': return 'mdi-loading'
        default: return 'mdi-information'
      }
    },
    
    addLogMessage(message) {
      const timestamp = new Date().toLocaleTimeString()
      this.logMessages.push({ timestamp, message })
      
      // Keep only last 20 messages
      if (this.logMessages.length > 20) {
        this.logMessages.shift()
      }
    },
    
    downloadScript() {
      if (this.compilationResult && this.compilationResult.output_path) {
        // This would need to be implemented on the server side
        // For now, just open the file path info
        this.$emit('download-requested', {
          episodeId: this.episodeId,
          filePath: this.compilationResult.output_path
        })
      }
    }
  }
}
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