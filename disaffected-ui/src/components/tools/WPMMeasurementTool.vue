<template>
  <v-dialog v-model="show" max-width="900" persistent>
    <v-card>
      <v-card-title class="d-flex align-center bg-primary">
        <v-icon class="mr-2">mdi-speedometer</v-icon>
        WPM Measurement Tool - Teleprompter Mode
        <v-spacer></v-spacer>
        <v-btn icon @click="close" variant="text">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-4">
        <!-- Instructions -->
        <v-alert type="info" variant="tonal" class="mb-4" v-if="!measuring && !completed">
          <v-alert-title>How to Use</v-alert-title>
          <ol class="mt-2">
            <li>Enter or paste a script sample below (at least 50 words recommended)</li>
            <li>Click "Start Reading" when ready</li>
            <li>Read the text naturally at your normal pace</li>
            <li>Click "Finish" when done reading</li>
            <li>Your WPM will be calculated automatically</li>
          </ol>
        </v-alert>

        <!-- Script Input / Teleprompter View -->
        <v-card variant="outlined" class="mb-4">
          <v-card-text>
            <div class="d-flex align-center mb-2" v-if="!measuring">
              <v-spacer></v-spacer>
              <v-btn
                @click="generateScript"
                color="primary"
                variant="tonal"
                size="small"
                :loading="generatingScript"
                :disabled="generatingScript"
              >
                <v-icon left size="small">mdi-auto-fix</v-icon>
                Generate Sample Script
              </v-btn>
            </div>
            <v-textarea
              v-if="!measuring"
              v-model="scriptText"
              label="Script Text"
              placeholder="Paste or type the script you'll read..."
              rows="8"
              variant="outlined"
              :rules="[v => v && v.length > 0 || 'Script text is required']"
              counter
              ref="scriptTextareaRef"
              :class="llmState.getVisualClass('field', 'wpm-script-textarea')"
            ></v-textarea>

            <!-- Teleprompter Mode -->
            <div v-else class="teleprompter-container" ref="teleprompterRef">
              <div class="teleprompter-text" :style="{ fontSize: teleprompterFontSize + 'px' }">
                {{ scriptText }}
              </div>
            </div>

            <!-- Font Size Control (Teleprompter Mode) -->
            <v-row v-if="measuring" class="mt-2">
              <v-col>
                <v-slider
                  v-model="teleprompterFontSize"
                  label="Font Size"
                  min="16"
                  max="48"
                  step="2"
                  thumb-label
                  prepend-icon="mdi-format-font-size-decrease"
                  append-icon="mdi-format-font-size-increase"
                ></v-slider>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Timer and Word Count -->
        <v-row class="mb-4">
          <v-col cols="4">
            <v-card variant="tonal" color="primary">
              <v-card-text class="text-center">
                <div class="text-h4">{{ wordCount }}</div>
                <div class="text-caption">Words</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card variant="tonal" :color="measuring ? 'success' : 'grey'">
              <v-card-text class="text-center">
                <div class="text-h4">{{ formattedTime }}</div>
                <div class="text-caption">Time Elapsed</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card variant="tonal" :color="completed ? 'success' : 'grey'">
              <v-card-text class="text-center">
                <div class="text-h4">{{ calculatedWPM }}</div>
                <div class="text-caption">WPM</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Speaker Info (When Completed) -->
        <v-expand-transition>
          <v-card v-if="completed" variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">Save to Speaker Profile</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12">
                  <v-select
                    v-model="selectedSpeakerId"
                    :items="speakerOptions"
                    label="Select Speaker"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-account"
                    :loading="loadingSpeakers"
                    item-title="text"
                    item-value="value"
                  >
                    <template v-slot:item="{ props, item }">
                      <v-list-item v-bind="props">
                        <template v-slot:prepend>
                          <v-icon v-if="item.raw.isSelf">mdi-account-circle</v-icon>
                          <v-icon v-else>mdi-account</v-icon>
                        </template>
                        <template v-slot:append v-if="item.raw.wpm">
                          <v-chip size="x-small" color="primary">{{ item.raw.wpm }} WPM</v-chip>
                        </template>
                      </v-list-item>
                    </template>
                  </v-select>
                </v-col>
              </v-row>

              <v-alert type="success" variant="tonal">
                <strong>Calculated WPM: {{ calculatedWPM }}</strong><br>
                <small>Comfortable range: {{ minWPM }} - {{ maxWPM }} WPM</small>
              </v-alert>
            </v-card-text>
          </v-card>
        </v-expand-transition>
      </v-card-text>

      <!-- Actions -->
      <v-card-actions class="px-4 pb-4">
        <v-btn @click="close" variant="text">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn
          v-if="!measuring && !completed"
          @click="startMeasurement"
          color="primary"
          variant="elevated"
          :disabled="wordCount < 10"
        >
          <v-icon left>mdi-play</v-icon>
          Start Reading
        </v-btn>
        <v-btn
          v-if="measuring"
          @click="finishMeasurement"
          color="success"
          variant="elevated"
        >
          <v-icon left>mdi-stop</v-icon>
          Finish
        </v-btn>
        <v-btn
          v-if="completed"
          @click="saveSpeaker"
          color="primary"
          variant="elevated"
          :disabled="!selectedSpeakerId"
        >
          <v-icon left>mdi-content-save</v-icon>
          Save to Profile
        </v-btn>
        <v-btn
          v-if="completed"
          @click="reset"
          variant="text"
        >
          Measure Again
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount, getCurrentInstance } from 'vue'
import { useLLMState } from '@/composables/useLLMState'
import { useLLM } from '@/composables/useLLM'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'speaker-saved', 'show-message'])

const llmState = useLLMState()
const { smartCall } = useLLM()

// Get axios from global properties
const $axios = getCurrentInstance()?.appContext.config.globalProperties.$axios

// Data
const scriptText = ref('')
const measuring = ref(false)
const completed = ref(false)
const startTime = ref(null)
const endTime = ref(null) // eslint-disable-line no-unused-vars
const elapsedSeconds = ref(0)
const timerInterval = ref(null)
const teleprompterFontSize = ref(24) // eslint-disable-line no-unused-vars
const generatingScript = ref(false)
const scriptTextareaRef = ref(null) // eslint-disable-line no-unused-vars
const teleprompterRef = ref(null) // eslint-disable-line no-unused-vars

// Speaker data
const speakers = ref([])
const loadingSpeakers = ref(false)
const selectedSpeakerId = ref(null)
const currentUser = ref(null)

// Computed
const show = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  }
})

const wordCount = computed(() => {
  if (!scriptText.value) return 0
  return scriptText.value.trim().split(/\s+/).filter(w => w.length > 0).length
})

const formattedTime = computed(() => {
  const minutes = Math.floor(elapsedSeconds.value / 60)
  const seconds = elapsedSeconds.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const calculatedWPM = computed(() => {
  if (!completed.value || elapsedSeconds.value === 0) return 0
  const minutes = elapsedSeconds.value / 60
  return Math.round(wordCount.value / minutes)
})

const minWPM = computed(() => {
  return Math.max(100, Math.round(calculatedWPM.value * 0.85))
})

const maxWPM = computed(() => {
  return Math.round(calculatedWPM.value * 1.15)
})

const speakerOptions = computed(() => {
  if (!currentUser.value) return []

  const isAdmin = currentUser.value.access_level === 'admin' || currentUser.value.access_level === 'super_admin'

  // Find user's own speaker profile
  const userSpeaker = speakers.value.find(s => s.user_id === currentUser.value.id)

  if (isAdmin) {
    // Admin can save to any speaker
    return speakers.value.map(speaker => ({
      text: speaker.name + (speaker.user_id === currentUser.value.id ? ' (You)' : ''),
      value: speaker.id,
      isSelf: speaker.user_id === currentUser.value.id,
      wpm: speaker.wpm
    }))
  } else {
    // Non-admin can only save to their own profile
    if (userSpeaker) {
      return [{
        text: userSpeaker.name + ' (You)',
        value: userSpeaker.id,
        isSelf: true,
        wpm: userSpeaker.wpm
      }]
    } else {
      // User doesn't have a profile yet - will create on save
      return [{
        text: currentUser.value.full_name || currentUser.value.username + ' (You)',
        value: 'me',
        isSelf: true,
        wpm: null
      }]
    }
  }
})

// Watch
watch(show, (newVal) => {
  if (newVal) {
    fetchSpeakers()
    fetchCurrentUser()
  }
})

// Methods
async function fetchCurrentUser() {
  try {
    const response = await $axios.get('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    currentUser.value = response.data
  } catch (error) {
    console.error('Error fetching current user:', error)
  }
}

async function fetchSpeakers() {
  try {
    loadingSpeakers.value = true
    const response = await $axios.get('/api/speakers/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.data.success) {
      speakers.value = response.data.data

      // Auto-select user's own speaker if it exists
      if (currentUser.value) {
        const userSpeaker = speakers.value.find(s => s.user_id === currentUser.value.id)
        if (userSpeaker) {
          selectedSpeakerId.value = userSpeaker.id
        } else {
          selectedSpeakerId.value = 'me'
        }
      }
    }
  } catch (error) {
    console.error('Error fetching speakers:', error)
  } finally {
    loadingSpeakers.value = false
  }
}

function startMeasurement() {
  measuring.value = true
  startTime.value = Date.now()
  timerInterval.value = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 100)
}

function finishMeasurement() {
  measuring.value = false
  completed.value = true
  endTime.value = Date.now()
  clearInterval(timerInterval.value)
}

async function saveSpeaker() {
  try {
    let response

    if (selectedSpeakerId.value === 'me') {
      // Create/update user's own speaker profile
      response = await $axios.post('/api/speakers/me/measure-wpm', {
        word_count: wordCount.value,
        elapsed_seconds: elapsedSeconds.value,
        script_text: scriptText.value
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
        }
      })
    } else {
      // Update existing speaker profile (admin only)
      const minutes = elapsedSeconds.value / 60
      const calculatedWpm = Math.round(wordCount.value / minutes)
      const wpmMin = Math.max(100, Math.round(calculatedWpm * 0.85))
      const wpmMax = Math.round(calculatedWpm * 1.15)

      response = await $axios.patch(`/api/speakers/${selectedSpeakerId.value}`, {
        wpm: calculatedWpm,
        wpm_min: wpmMin,
        wpm_max: wpmMax
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
        }
      })
    }

    if (response.data.success) {
      emit('speaker-saved', response.data.data)

      // Show success message
      emit('show-message', {
        type: 'success',
        text: response.data.message || 'Speaker profile updated successfully'
      })

      close()
    }
  } catch (error) {
    console.error('Error saving speaker profile:', error)
    emit('show-message', {
      type: 'error',
      text: error.response?.data?.detail || 'Failed to save speaker profile'
    })
  }
}

async function generateScript() {
  try {
    generatingScript.value = true
    console.log('🎯 Generate Script clicked - starting LLM operation')

    // Use Universal LLM Framework with visual feedback
    const result = await llmState.withLLM(
      'field',
      'wpm-script-textarea',
      'generating',
      async () => {
        console.log('📝 Inside withLLM - about to call smartCall')
        // Generate script using Qwen
        const prompt = `Generate a natural, conversational broadcast script suitable for reading aloud.
The script should be between 150-250 words and cover a current events topic or interesting story.
Write in a friendly, engaging tone as if speaking directly to viewers.
Do not include any stage directions, just the spoken text.`

        const response = await smartCall(
          prompt,
          {
            preferredService: 'ollama',
            preferredModel: 'qwen2.5-coder:7b'
          }
        )

        return response
      },
      {
        state: llmState.STATE.GENERATING,  // Blue color for generating
        message: 'Generating WPM test script with Qwen...',
        notificationTitle: 'WPM Script Generation',
        notify: false,  // We'll add custom notification after
        priority: llmState.PRIORITY.NORMAL
      }
    )

    if (result) {
      // smartCall returns the text directly, not wrapped in {response: ...}
      scriptText.value = typeof result === 'string' ? result.trim() : (result.response || result).toString().trim()
      console.log('✅ Script generated and inserted:', scriptText.value.substring(0, 100) + '...')

      // Add custom success notification with word count
      nextTick(() => {
        const words = wordCount.value
        llmState.addNotification({
          title: 'WPM Test Script Generated',
          message: `Generated ${words} word broadcast script for WPM testing`,
          priority: llmState.PRIORITY.NORMAL,
          type: 'success',
          success: true
        })
      })
    }

  } catch (error) {
    console.error('Error generating script:', error)
    emit('show-message', {
      type: 'error',
      text: error.message || 'Failed to generate script'
    })
  } finally {
    generatingScript.value = false
  }
}

function reset() {
  scriptText.value = ''
  measuring.value = false
  completed.value = false
  startTime.value = null
  endTime.value = null
  elapsedSeconds.value = 0
  clearInterval(timerInterval.value)

  // Reset speaker selection to user's profile
  if (currentUser.value) {
    const userSpeaker = speakers.value.find(s => s.user_id === currentUser.value.id)
    selectedSpeakerId.value = userSpeaker ? userSpeaker.id : 'me'
  }
}

function close() {
  reset()
  show.value = false
}

onBeforeUnmount(() => {
  clearInterval(timerInterval.value)
})
</script>

<style scoped>
.teleprompter-container {
  min-height: 300px;
  max-height: 500px;
  overflow-y: auto;
  background: #000;
  color: #fff;
  padding: 32px;
  border-radius: 8px;
  text-align: center;
}

.teleprompter-text {
  line-height: 1.8;
  font-family: 'Arial', sans-serif;
  user-select: none;
}

/* Smooth scrolling for teleprompter */
.teleprompter-container::-webkit-scrollbar {
  width: 8px;
}

.teleprompter-container::-webkit-scrollbar-track {
  background: #222;
}

.teleprompter-container::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.teleprompter-container::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style>
