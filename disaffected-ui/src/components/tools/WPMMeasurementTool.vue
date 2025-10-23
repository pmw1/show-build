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

<script>
import { useLLMState } from '@/composables/useLLMState'
import { useLLM } from '@/composables/useLLM'

export default {
  name: 'WPMMeasurementTool',
  props: {
    modelValue: Boolean
  },
  emits: ['update:modelValue', 'speaker-saved', 'show-message'],
  setup() {
    const llmState = useLLMState()
    const { smartCall } = useLLM()

    return {
      llmState,
      smartCall
    }
  },
  data() {
    return {
      scriptText: '',
      measuring: false,
      completed: false,
      startTime: null,
      endTime: null,
      elapsedSeconds: 0,
      timerInterval: null,
      teleprompterFontSize: 24,
      generatingScript: false,

      // Speaker data
      speakers: [],
      loadingSpeakers: false,
      selectedSpeakerId: null,
      currentUser: null
    }
  },
  computed: {
    show: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    },
    wordCount() {
      if (!this.scriptText) return 0
      return this.scriptText.trim().split(/\s+/).filter(w => w.length > 0).length
    },
    formattedTime() {
      const minutes = Math.floor(this.elapsedSeconds / 60)
      const seconds = this.elapsedSeconds % 60
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    },
    calculatedWPM() {
      if (!this.completed || this.elapsedSeconds === 0) return 0
      const minutes = this.elapsedSeconds / 60
      return Math.round(this.wordCount / minutes)
    },
    minWPM() {
      return Math.max(100, Math.round(this.calculatedWPM * 0.85))
    },
    maxWPM() {
      return Math.round(this.calculatedWPM * 1.15)
    },
    speakerOptions() {
      if (!this.currentUser) return []

      const isAdmin = this.currentUser.access_level === 'admin' || this.currentUser.access_level === 'super_admin'

      // Find user's own speaker profile
      const userSpeaker = this.speakers.find(s => s.user_id === this.currentUser.id)

      if (isAdmin) {
        // Admin can save to any speaker
        return this.speakers.map(speaker => ({
          text: speaker.name + (speaker.user_id === this.currentUser.id ? ' (You)' : ''),
          value: speaker.id,
          isSelf: speaker.user_id === this.currentUser.id,
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
            text: this.currentUser.full_name || this.currentUser.username + ' (You)',
            value: 'me',
            isSelf: true,
            wpm: null
          }]
        }
      }
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.fetchSpeakers()
        this.fetchCurrentUser()
      }
    }
  },
  methods: {
    async fetchCurrentUser() {
      try {
        const response = await this.$axios.get('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })
        this.currentUser = response.data
      } catch (error) {
        console.error('Error fetching current user:', error)
      }
    },
    async fetchSpeakers() {
      try {
        this.loadingSpeakers = true
        const response = await this.$axios.get('/api/speakers/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })
        if (response.data.success) {
          this.speakers = response.data.data

          // Auto-select user's own speaker if it exists
          if (this.currentUser) {
            const userSpeaker = this.speakers.find(s => s.user_id === this.currentUser.id)
            if (userSpeaker) {
              this.selectedSpeakerId = userSpeaker.id
            } else {
              this.selectedSpeakerId = 'me'
            }
          }
        }
      } catch (error) {
        console.error('Error fetching speakers:', error)
      } finally {
        this.loadingSpeakers = false
      }
    },
    startMeasurement() {
      this.measuring = true
      this.startTime = Date.now()
      this.timerInterval = setInterval(() => {
        this.elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000)
      }, 100)
    },
    finishMeasurement() {
      this.measuring = false
      this.completed = true
      this.endTime = Date.now()
      clearInterval(this.timerInterval)
    },
    async saveSpeaker() {
      try {
        let response

        if (this.selectedSpeakerId === 'me') {
          // Create/update user's own speaker profile
          response = await this.$axios.post('/api/speakers/me/measure-wpm', {
            word_count: this.wordCount,
            elapsed_seconds: this.elapsedSeconds,
            script_text: this.scriptText
          }, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
            }
          })
        } else {
          // Update existing speaker profile (admin only)
          const minutes = this.elapsedSeconds / 60
          const calculatedWpm = Math.round(this.wordCount / minutes)
          const wpmMin = Math.max(100, Math.round(calculatedWpm * 0.85))
          const wpmMax = Math.round(calculatedWpm * 1.15)

          response = await this.$axios.patch(`/api/speakers/${this.selectedSpeakerId}`, {
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
          this.$emit('speaker-saved', response.data.data)

          // Show success message
          this.$emit('show-message', {
            type: 'success',
            text: response.data.message || 'Speaker profile updated successfully'
          })

          this.close()
        }
      } catch (error) {
        console.error('Error saving speaker profile:', error)
        this.$emit('show-message', {
          type: 'error',
          text: error.response?.data?.detail || 'Failed to save speaker profile'
        })
      }
    },
    async generateScript() {
      try {
        this.generatingScript = true
        console.log('🎯 Generate Script clicked - starting LLM operation')

        // Use Universal LLM Framework with visual feedback
        const result = await this.llmState.withLLM(
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

            const response = await this.smartCall(
              prompt,
              {
                preferredService: 'ollama',
                preferredModel: 'qwen2.5-coder:7b'
              }
            )

            return response
          },
          {
            state: this.llmState.STATE.GENERATING,  // Blue color for generating
            message: 'Generating WPM test script with Qwen...',
            notificationTitle: 'WPM Script Generation',
            notify: false,  // We'll add custom notification after
            priority: this.llmState.PRIORITY.NORMAL
          }
        )

        if (result) {
          // smartCall returns the text directly, not wrapped in {response: ...}
          this.scriptText = typeof result === 'string' ? result.trim() : (result.response || result).toString().trim()
          console.log('✅ Script generated and inserted:', this.scriptText.substring(0, 100) + '...')

          // Add custom success notification with word count
          this.$nextTick(() => {
            const words = this.wordCount
            this.llmState.addNotification({
              title: 'WPM Test Script Generated',
              message: `Generated ${words} word broadcast script for WPM testing`,
              priority: this.llmState.PRIORITY.NORMAL,
              type: 'success',
              success: true
            })
          })
        }

      } catch (error) {
        console.error('Error generating script:', error)
        this.$emit('show-message', {
          type: 'error',
          text: error.message || 'Failed to generate script'
        })
      } finally {
        this.generatingScript = false
      }
    },
    reset() {
      this.scriptText = ''
      this.measuring = false
      this.completed = false
      this.startTime = null
      this.endTime = null
      this.elapsedSeconds = 0
      clearInterval(this.timerInterval)

      // Reset speaker selection to user's profile
      if (this.currentUser) {
        const userSpeaker = this.speakers.find(s => s.user_id === this.currentUser.id)
        this.selectedSpeakerId = userSpeaker ? userSpeaker.id : 'me'
      }
    },
    close() {
      this.reset()
      this.show = false
    }
  },
  beforeUnmount() {
    clearInterval(this.timerInterval)
  }
}
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
