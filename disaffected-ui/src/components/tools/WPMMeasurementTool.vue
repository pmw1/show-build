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
            <v-textarea
              v-if="!measuring"
              v-model="scriptText"
              label="Script Text"
              placeholder="Paste or type the script you'll read..."
              rows="8"
              variant="outlined"
              :rules="[v => v && v.length > 0 || 'Script text is required']"
              counter
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
            <v-card-title class="text-subtitle-1">Save Speaker Profile</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="6">
                  <v-text-field
                    v-model="speakerName"
                    label="Speaker Name"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-account"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="speakerRole"
                    :items="roleOptions"
                    label="Role"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-microphone"
                  ></v-select>
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
          :disabled="!speakerName"
        >
          <v-icon left>mdi-content-save</v-icon>
          Save Speaker
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
export default {
  name: 'WPMMeasurementTool',
  props: {
    modelValue: Boolean
  },
  emits: ['update:modelValue', 'speaker-saved'],
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

      // Speaker data
      speakerName: '',
      speakerRole: 'host',
      roleOptions: [
        { title: 'Host', value: 'host' },
        { title: 'Guest', value: 'guest' },
        { title: 'Narrator', value: 'narrator' },
        { title: 'Voice Talent', value: 'voice_talent' }
      ]
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
    }
  },
  methods: {
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
        // Save WPM measurement to backend (creates/updates user's speaker profile)
        const response = await this.$axios.post('/api/speakers/me/measure-wpm', {
          word_count: this.wordCount,
          elapsed_seconds: this.elapsedSeconds,
          script_text: this.scriptText
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })

        if (response.data.success) {
          this.$emit('speaker-saved', response.data.data)

          // Show success message
          this.$emit('show-message', {
            type: 'success',
            text: response.data.message
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
    reset() {
      this.scriptText = ''
      this.measuring = false
      this.completed = false
      this.startTime = null
      this.endTime = null
      this.elapsedSeconds = 0
      this.speakerName = ''
      this.speakerRole = 'host'
      clearInterval(this.timerInterval)
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
