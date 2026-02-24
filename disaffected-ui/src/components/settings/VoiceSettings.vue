<template>
  <v-card>
    <v-card-title>
      <v-icon left>mdi-microphone</v-icon>
      Voice Services Configuration
    </v-card-title>
    <v-card-text>
      <v-row>
        <!-- Whisper Configuration -->
        <v-col cols="12">
          <v-card variant="outlined" class="pa-4">
            <div class="d-flex align-center mb-3">
              <v-icon class="mr-3" size="large">mdi-microphone</v-icon>
              <v-card-title class="text-subtitle-1 pa-0 flex-grow-1">Whisper (Speech-to-Text)</v-card-title>
              <v-switch
                :model-value="whisperConfig.enabled || false"
                label="Enable"
                color="primary"
                density="compact"
                hide-details
                @update:model-value="updateVoiceConfig('whisper', 'enabled', $event)"
              />
            </div>

            <v-expand-transition>
              <div v-if="whisperConfig.enabled">
                <v-divider class="mb-4" />
                <v-text-field
                  :model-value="whisperConfig.host || ''"
                  label="Host URL"
                  placeholder="http://192.168.51.197:8887"
                  persistent-hint
                  hint="Local Whisper transcription endpoint"
                  @update:model-value="updateVoiceConfig('whisper', 'host', $event)"
                />
                <v-text-field
                  :model-value="whisperConfig.endpoint || ''"
                  label="Transcription Endpoint"
                  placeholder="/v1/audio/transcriptions"
                  persistent-hint
                  hint="API endpoint for speech-to-text conversion"
                  @update:model-value="updateVoiceConfig('whisper', 'endpoint', $event)"
                />
                <v-btn
                  v-if="whisperConfig.host"
                  color="primary"
                  variant="outlined"
                  size="small"
                  class="mt-2"
                  @click="testConnection('whisper')"
                >
                  <v-icon left>mdi-connection</v-icon>
                  Test Connection
                </v-btn>
              </div>
            </v-expand-transition>
          </v-card>
        </v-col>

        <!-- XTTS Configuration -->
        <v-col cols="12">
          <v-card variant="outlined" class="pa-4">
            <div class="d-flex align-center mb-3">
              <v-icon class="mr-3" size="large">mdi-account-voice</v-icon>
              <v-card-title class="text-subtitle-1 pa-0 flex-grow-1">XTTS (Text-to-Speech)</v-card-title>
              <v-switch
                :model-value="xttsConfig.enabled || false"
                label="Enable"
                color="primary"
                density="compact"
                hide-details
                @update:model-value="updateVoiceConfig('xtts', 'enabled', $event)"
              />
            </div>

            <v-expand-transition>
              <div v-if="xttsConfig.enabled">
                <v-divider class="mb-4" />
                <v-text-field
                  :model-value="xttsConfig.host || ''"
                  label="Host URL"
                  placeholder="http://192.168.51.197:5001"
                  persistent-hint
                  hint="XTTS text-to-speech service endpoint"
                  @update:model-value="updateVoiceConfig('xtts', 'host', $event)"
                />
                <v-text-field
                  :model-value="xttsConfig.endpoint || ''"
                  label="TTS Endpoint"
                  placeholder="/v1/audio/speech"
                  persistent-hint
                  hint="XTTS API endpoint for text-to-speech"
                  @update:model-value="updateVoiceConfig('xtts', 'endpoint', $event)"
                />
                <v-text-field
                  :model-value="xttsConfig.language || ''"
                  label="Default Language"
                  placeholder="en"
                  persistent-hint
                  hint="Default language code (e.g., en, es, fr)"
                  @update:model-value="updateVoiceConfig('xtts', 'language', $event)"
                />
                <v-text-field
                  :model-value="xttsConfig.speed || 1.0"
                  label="Speech Speed"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="4.0"
                  persistent-hint
                  hint="Speed multiplier for speech synthesis (0.1 to 4.0)"
                  @update:model-value="updateVoiceConfig('xtts', 'speed', parseFloat($event) || 1.0)"
                />
                <v-select
                  :model-value="xttsConfig.speaker || ''"
                  :items="availableSpeakers"
                  label="Available Speakers"
                  persistent-hint
                  hint="Select a voice speaker for text-to-speech (OpenAI + XTTS speakers)"
                  density="compact"
                  item-title="name"
                  item-value="id"
                  clearable
                  :loading="loadingSpeakers"
                  @update:model-value="updateVoiceConfig('xtts', 'speaker', $event)"
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item
                      v-if="item.raw.id === '---separator---'"
                      :title="item.raw.name"
                      disabled
                      class="text-center font-weight-bold text-grey-darken-1"
                    />
                    <v-list-item v-else v-bind="props" />
                  </template>
                  <template v-slot:no-data>
                    <v-list-item>
                      <v-list-item-title>{{ speakersError || 'No speakers available' }}</v-list-item-title>
                    </v-list-item>
                  </template>
                </v-select>
                <v-btn
                  v-if="xttsConfig.host"
                  color="secondary"
                  variant="outlined"
                  size="small"
                  :loading="loadingSpeakers"
                  @click="fetchAvailableSpeakers()"
                  class="mt-2 mr-2"
                >
                  <v-icon left>mdi-account-voice</v-icon>
                  Fetch Speakers
                </v-btn>
                <v-btn
                  v-if="xttsConfig.host"
                  color="primary"
                  variant="outlined"
                  size="small"
                  @click="testConnection('xtts')"
                  class="mt-2 mr-2"
                >
                  <v-icon left>mdi-connection</v-icon>
                  Test Connection
                </v-btn>
                <v-btn
                  v-if="xttsConfig.host && xttsConfig.enabled"
                  color="success"
                  variant="outlined"
                  size="small"
                  :loading="testingVoice"
                  @click="testVoiceSynthesis()"
                  class="mt-2"
                >
                  <v-icon left>mdi-play-circle</v-icon>
                  Test Voice
                </v-btn>
              </div>
            </v-expand-transition>
          </v-card>
        </v-col>

        <!-- Fish Speech Configuration -->
        <v-col cols="12">
          <v-card variant="outlined" class="pa-4">
            <div class="d-flex align-center mb-3">
              <v-icon class="mr-3" size="large">mdi-fish</v-icon>
              <v-card-title class="text-subtitle-1 pa-0 flex-grow-1">Fish Speech (Text-to-Speech)</v-card-title>
              <v-switch
                :model-value="fishspeechConfig.enabled || false"
                label="Enable"
                color="primary"
                density="compact"
                hide-details
                @update:model-value="updateVoiceConfig('fishspeech', 'enabled', $event)"
              />
            </div>

            <v-expand-transition>
              <div v-if="fishspeechConfig.enabled">
                <v-divider class="mb-4" />
                <v-alert type="info" variant="tonal" class="mb-4">
                  Fish Speech provides high-quality, natural-sounding text-to-speech synthesis with support for fine-tuned custom voices.
                </v-alert>
                <v-text-field
                  :model-value="fishspeechConfig.host || ''"
                  label="Host URL"
                  placeholder="http://192.168.51.197:8080"
                  persistent-hint
                  hint="Fish Speech API endpoint"
                  @update:model-value="updateVoiceConfig('fishspeech', 'host', $event)"
                />
                <v-text-field
                  :model-value="fishspeechConfig.endpoint || ''"
                  label="TTS Endpoint"
                  placeholder="/v1/audio/speech"
                  persistent-hint
                  hint="API endpoint for text-to-speech synthesis"
                  @update:model-value="updateVoiceConfig('fishspeech', 'endpoint', $event)"
                />
                <v-text-field
                  :model-value="fishspeechConfig.voice || ''"
                  label="Voice/Reference"
                  placeholder="kairo_main"
                  persistent-hint
                  hint="Voice reference ID or name"
                  @update:model-value="updateVoiceConfig('fishspeech', 'voice', $event)"
                />
                <v-select
                  :model-value="fishspeechConfig.format || 'wav'"
                  :items="['wav', 'mp3', 'flac', 'ogg']"
                  label="Audio Format"
                  persistent-hint
                  hint="Output audio format"
                  @update:model-value="updateVoiceConfig('fishspeech', 'format', $event)"
                />
                <v-btn
                  v-if="fishspeechConfig.host"
                  color="primary"
                  variant="outlined"
                  size="small"
                  class="mt-2"
                  @click="testConnection('fishspeech')"
                >
                  <v-icon left>mdi-connection</v-icon>
                  Test Connection
                </v-btn>
              </div>
            </v-expand-transition>
          </v-card>
        </v-col>
      </v-row>

      <!-- Voice Model Training Section -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-card variant="outlined" class="pa-4" :disabled="true" style="opacity: 0.6;">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <v-icon left>mdi-brain</v-icon>
              Voice Model Training
              <v-chip size="small" color="orange" class="ml-3">Coming Soon</v-chip>
            </v-card-title>
            <v-card-text>
              <v-alert type="info" variant="tonal" class="mb-4">
                Progressive voice sample collection and model training for speaker-specific voice synthesis.
              </v-alert>

              <div class="d-flex flex-column" style="gap: 12px;">
                <div class="d-flex align-center">
                  <v-icon color="grey">mdi-microphone-variant</v-icon>
                  <span class="ml-3 text-grey">Weekly audio sample ingestion</span>
                </div>
                <div class="d-flex align-center">
                  <v-icon color="grey">mdi-text-box-outline</v-icon>
                  <span class="ml-3 text-grey">Whisper transcription integration</span>
                </div>
                <div class="d-flex align-center">
                  <v-icon color="grey">mdi-waveform</v-icon>
                  <span class="ml-3 text-grey">Voice segment extraction (5-10 sec chunks)</span>
                </div>
                <div class="d-flex align-center">
                  <v-icon color="grey">mdi-robot</v-icon>
                  <span class="ml-3 text-grey">XTTS model fine-tuning</span>
                </div>
              </div>

              <v-divider class="my-4"></v-divider>

              <div class="text-caption text-grey">
                <strong>Current Status:</strong> Infrastructure complete, processing pipelines pending<br>
                <strong>API Endpoints:</strong> /api/voice-model/ingest-sample, /api/voice-model/train<br>
                <strong>Documentation:</strong> docs/VOICE_MODEL_TRAINING_GUIDE.md
              </div>

              <div class="mt-4">
                <v-btn disabled variant="outlined" size="small" class="mr-2">
                  <v-icon left>mdi-upload</v-icon>
                  Upload Voice Sample
                </v-btn>
                <v-btn disabled variant="outlined" size="small" class="mr-2">
                  <v-icon left>mdi-folder-open</v-icon>
                  View Samples
                </v-btn>
                <v-btn disabled variant="outlined" size="small">
                  <v-icon left>mdi-play</v-icon>
                  Train Model
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Save Button -->
      <v-row class="mt-6">
        <v-col class="text-center">
          <v-btn
            color="primary"
            @click="saveVoiceSettings"
            :loading="saving"
            size="large"
          >
            <v-icon left>mdi-content-save</v-icon>
            Save Voice Configuration
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

// Create individual computed properties to avoid recursive update issues
const whisperConfig = computed(() => props.modelValue?.whisper || {})
const xttsConfig = computed(() => props.modelValue?.xtts || {})
const fishspeechConfig = computed(() => props.modelValue?.fishspeech || {})
const allConfigs = computed(() => props.modelValue || {})

const saving = ref(false)
const availableSpeakers = ref([])
const loadingSpeakers = ref(false)
const speakersError = ref('')
const testingVoice = ref(false)

// Auto-fetch speakers when component mounts (but avoid triggering reactive loops)
onMounted(() => {
  // Only fetch speakers if XTTS is enabled and has a host - don't fetch on every mount
  if (xttsConfig.value?.enabled && xttsConfig.value?.host) {
    console.log('XTTS is enabled with host, fetching speakers...')
    fetchAvailableSpeakers()
  } else {
    console.log('XTTS not enabled or no host configured, skipping speaker fetch')
  }
})

function updateVoiceConfig(service, field, value) {
  const newConfigs = { ...allConfigs.value }

  if (!newConfigs[service]) {
    newConfigs[service] = {
      host: '',
      endpoint: service === 'xtts' ? '/v1/audio/speech' :
                service === 'fishspeech' ? '/v1/audio/speech' :
                '/v1/audio/transcriptions',
      enabled: false
    }

    if (service === 'xtts') {
      newConfigs[service] = {
        ...newConfigs[service],
        language: 'en',
        speaker: '',
        speed: 1.0
      }
    } else if (service === 'fishspeech') {
      newConfigs[service] = {
        ...newConfigs[service],
        voice: 'kairo_main',
        format: 'wav'
      }
    }
  }

  newConfigs[service][field] = value
  emit('update:modelValue', newConfigs)

  // Handle XTTS-specific side effects without updating global state
  if (service === 'xtts') {
    // Special handling for enabled field
    // Only fetch if not already loading (prevent recursive loops)
    if (field === 'enabled' && value && !loadingSpeakers.value) {
      fetchAvailableSpeakers()
    }

    // If host URL changes, refetch speakers
    // Only fetch if not already loading (prevent recursive loops)
    if (field === 'host' && value && !loadingSpeakers.value) {
      fetchAvailableSpeakers()
    }
  }
}

async function fetchAvailableSpeakers() {
  // Prevent recursive calls
  if (loadingSpeakers.value) {
    console.log('Already fetching speakers, skipping...')
    return
  }

  loadingSpeakers.value = true
  speakersError.value = ''

  try {
    const response = await fetch('/api/settings/xtts/speakers', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()

    if (data.success && Array.isArray(data.speakers)) {
      availableSpeakers.value = data.speakers
      console.log(`Fetched ${data.count} speakers from ${data.xtts_host}:`, availableSpeakers.value)
      speakersError.value = ''
    } else {
      availableSpeakers.value = []
      speakersError.value = data.message || 'No speakers data received'
      console.log('Speaker fetch result:', data.message || 'No speakers available')
    }

  } catch (error) {
    console.error('Error fetching speakers:', error)
    speakersError.value = `Failed to fetch speakers: ${error.message}`
    availableSpeakers.value = []
  } finally {
    loadingSpeakers.value = false
  }
}

async function testConnection(service) {
  try {
    const config = allConfigs.value[service]

    // For fishspeech, test the health endpoint directly if it has one
    if (service === 'fishspeech' && config.host) {
      try {
        const healthUrl = `${config.host}/v1/health`
        const healthResponse = await fetch(healthUrl, {
          method: 'GET',
          signal: AbortSignal.timeout(5000)
        })
        if (healthResponse.ok) {
          alert(`Fish Speech connection successful! Service is healthy.`)
          return
        }
      } catch (e) {
        console.warn('Fish Speech health check failed, trying backend proxy:', e)
      }
    }

    // Use backend proxy for testing
    const response = await fetch(`/api/settings/test/${service}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      },
      body: JSON.stringify(config)
    })

    if (response.ok) {
      const result = await response.json()
      const serviceName = service === 'fishspeech' ? 'Fish Speech' :
                          service === 'xtts' ? 'XTTS' :
                          service === 'whisper' ? 'Whisper' : service
      alert(`${serviceName} connection successful! ${result.message || ''}`)
    } else {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Connection failed')
    }
  } catch (error) {
    console.error(`Error testing ${service} connection:`, error)
    const serviceName = service === 'fishspeech' ? 'Fish Speech' :
                        service === 'xtts' ? 'XTTS' :
                        service === 'whisper' ? 'Whisper' : service
    alert(`Failed to connect to ${serviceName}: ${error.message}`)
  }
}

async function testVoiceSynthesis() {
  if (!xttsConfig.value.enabled) {
    alert('Please enable XTTS first')
    return
  }

  if (!xttsConfig.value.speaker) {
    alert('Please select a speaker first')
    return
  }

  // Debug: log the current configuration
  console.log('XTTS Configuration:', xttsConfig.value)
  console.log('Selected speaker:', xttsConfig.value.speaker)
  console.log('Available speakers:', availableSpeakers.value)

  testingVoice.value = true

  try {
    // Create the test message
    const testMessage = `Success.  Text to speech is being synthesized in Ravena New York`

    // Prepare request data
    const requestBody = {
      text: testMessage,
      speaker: xttsConfig.value.speaker,
      language: xttsConfig.value.language || 'en',
      speed: xttsConfig.value.speed || 1.0
    }

    const requestHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
    }

    // Synthesize speech using backend proxy
    const ttsResponse = await fetch('/api/settings/xtts/synthesize', {
      method: 'POST',
      headers: requestHeaders,
      body: JSON.stringify(requestBody)
    })

    if (!ttsResponse.ok) {
      const errorText = await ttsResponse.text()
      throw new Error(`TTS failed: ${errorText}`)
    }

    // Get audio blob and play it
    const audioBlob = await ttsResponse.blob()
    console.log('Audio blob received:', {
      size: audioBlob.size,
      type: audioBlob.type || 'unknown',
      contentType: ttsResponse.headers.get('content-type')
    })

    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)

    // Set up event handlers
    audio.onloadstart = () => console.log('Audio loading started')
    audio.oncanplay = () => console.log('Audio can start playing')
    audio.onended = () => {
      console.log('Audio playback ended')
      URL.revokeObjectURL(audioUrl)
    }

    audio.onerror = (e) => {
      console.error('Audio error:', e, audio.error)
      URL.revokeObjectURL(audioUrl)
      throw new Error(`Failed to play audio: ${audio.error?.message || 'Unknown audio error'}`)
    }

    // Try to play with better error handling
    try {
      console.log('Attempting to play audio...')
      await audio.play()
      console.log('✅ XTTS test voice synthesis successful:', testMessage)
    } catch (playError) {
      console.error('Audio play failed:', playError)
      if (playError.name === 'NotAllowedError') {
        console.warn('⚠️ Voice synthesis successful, but browser blocked autoplay. Check browser console for audio blob info.')
      } else {
        throw playError
      }
    }

  } catch (error) {
    console.error('Voice test failed:', error)
    alert(`Voice test failed: ${error.message}`)
  } finally {
    testingVoice.value = false
  }
}

async function saveVoiceSettings() {
  saving.value = true
  try {
    emit('save', allConfigs.value)
    alert('Voice configuration saved successfully')
  } catch (error) {
    console.error('Error saving voice configuration:', error)
    alert('Failed to save voice configuration')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-card--outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}
</style>