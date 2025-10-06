<template>
  <v-card class="voice-print-recorder">
    <v-card-title class="d-flex align-center bg-deep-purple text-white">
      <v-icon class="mr-2" color="white">mdi-microphone</v-icon>
      Voice Print Recording
      <v-spacer></v-spacer>
      <v-chip v-if="recordingState === 'recording'" color="error" size="small" class="recording-indicator">
        <v-icon size="small" class="mr-1 pulsing">mdi-circle</v-icon>
        REC {{ formatTime(recordingTime) }}
      </v-chip>
    </v-card-title>

    <v-card-text class="pa-6">
      <!-- Instructions -->
      <v-alert v-if="recordingState === 'idle'" type="info" variant="tonal" class="mb-4">
        <v-alert-title>How it works</v-alert-title>
        <ol class="mt-2">
          <li>Click "Start Recording" and begin reading when the text appears</li>
          <li>Read naturally at your normal speaking pace</li>
          <li>The text will auto-scroll as you read</li>
          <li>Click "Finish" when you've completed all text</li>
          <li>We'll calculate your WPM and create a voice profile</li>
        </ol>
      </v-alert>

      <!-- Reading Text Display with Auto-Scroll -->
      <v-card
        v-if="recordingState !== 'idle'"
        variant="outlined"
        class="reading-display mb-4"
        :class="{ 'recording-active': recordingState === 'recording' }"
      >
        <div class="reading-viewport" ref="viewport">
          <div class="reading-content" :style="{ transform: `translateY(${scrollOffset}px)` }">
            <p
              v-for="(paragraph, index) in readingText"
              :key="index"
              class="reading-paragraph"
              :class="{ 'current-paragraph': index === currentParagraphIndex }"
            >
              {{ paragraph }}
            </p>
          </div>
        </div>

        <!-- Scroll Progress -->
        <v-progress-linear
          :model-value="scrollProgress"
          color="deep-purple"
          height="6"
          class="reading-progress"
        ></v-progress-linear>
      </v-card>

      <!-- WPM Display -->
      <v-card v-if="calculatedWPM" variant="tonal" color="success" class="mb-4">
        <v-card-text class="text-center">
          <div class="text-h3 mb-2">{{ Math.round(calculatedWPM) }} WPM</div>
          <div class="text-body-1">Your calculated speaking rate</div>
          <div class="text-caption text-medium-emphasis mt-2">
            {{ wordCount }} words in {{ Math.round(recordingTime) }} seconds
          </div>
        </v-card-text>
      </v-card>

      <!-- Error Display -->
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">
        {{ error }}
      </v-alert>

      <!-- Upload Progress -->
      <v-progress-linear
        v-if="uploading"
        indeterminate
        color="deep-purple"
        class="mb-4"
      ></v-progress-linear>
    </v-card-text>

    <v-card-actions class="px-6 pb-4">
      <v-btn
        v-if="recordingState === 'idle'"
        color="deep-purple"
        variant="elevated"
        size="large"
        @click="startRecording"
        prepend-icon="mdi-microphone"
      >
        Start Recording
      </v-btn>

      <v-btn
        v-if="recordingState === 'recording'"
        color="error"
        variant="elevated"
        size="large"
        @click="stopRecording"
        prepend-icon="mdi-stop"
      >
        Finish Recording
      </v-btn>

      <v-btn
        v-if="recordingState === 'completed' && !uploading"
        color="success"
        variant="elevated"
        size="large"
        @click="uploadVoiceSample"
        prepend-icon="mdi-upload"
      >
        Save Voice Profile
      </v-btn>

      <v-spacer></v-spacer>

      <v-btn
        v-if="recordingState !== 'idle'"
        color="secondary"
        variant="outlined"
        @click="reset"
      >
        Start Over
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import axios from 'axios'

export default {
  name: 'VoicePrintRecorder',
  data() {
    return {
      recordingState: 'idle', // 'idle', 'recording', 'completed'
      mediaRecorder: null,
      audioChunks: [],
      audioBlob: null,
      recordingTime: 0,
      recordingInterval: null,
      currentParagraphIndex: 0,
      scrollOffset: 0,
      scrollInterval: null,
      calculatedWPM: null,
      wordCount: 0,
      error: '',
      uploading: false,

      // Sample reading text (can be customized)
      readingText: [
        "Welcome to the voice print recording system. This tool will help us understand your natural speaking rhythm and create a unique profile for your voice.",
        "As you read this text aloud, the system is recording your audio and measuring how quickly you speak. This measurement is called words per minute, or WPM.",
        "Everyone has their own natural speaking pace. Some people speak quickly, others more slowly. There's no right or wrong speed - we just want to capture your authentic voice.",
        "The recording will also be used to create a voice sample for text-to-speech synthesis. This means in the future, the system might be able to generate speech that sounds like you.",
        "Please read naturally and clearly. Imagine you're narrating a documentary or reading the news. Take your time and enunciate each word.",
        "Thank you for participating in this voice profiling process. Your unique vocal characteristics will be saved and used to enhance your experience in the system."
      ]
    }
  },
  computed: {
    scrollProgress() {
      if (this.readingText.length === 0) return 0
      return (this.currentParagraphIndex / (this.readingText.length - 1)) * 100
    }
  },
  methods: {
    async startRecording() {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

        // Create MediaRecorder
        this.mediaRecorder = new MediaRecorder(stream)
        this.audioChunks = []

        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data)
        }

        this.mediaRecorder.onstop = () => {
          this.audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' })
          this.recordingState = 'completed'
          this.calculateWPM()
        }

        // Start recording
        this.mediaRecorder.start()
        this.recordingState = 'recording'

        // Start timer
        this.recordingTime = 0
        this.recordingInterval = setInterval(() => {
          this.recordingTime++
        }, 1000)

        // Start auto-scroll
        this.startAutoScroll()

        // Count words in reading text
        this.wordCount = this.readingText.join(' ').split(/\s+/).filter(w => w.length > 0).length

      } catch (error) {
        console.error('Error starting recording:', error)
        this.error = 'Failed to access microphone. Please check permissions.'
      }
    },

    stopRecording() {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop()

        // Stop all audio tracks
        this.mediaRecorder.stream.getTracks().forEach(track => track.stop())
      }

      // Stop timer
      if (this.recordingInterval) {
        clearInterval(this.recordingInterval)
        this.recordingInterval = null
      }

      // Stop scroll
      if (this.scrollInterval) {
        clearInterval(this.scrollInterval)
        this.scrollInterval = null
      }
    },

    startAutoScroll() {
      // Auto-scroll based on average reading speed
      // Assume average 150 WPM = 2.5 words/second
      const estimatedSecondsPerParagraph = this.readingText.map(p => {
        const words = p.split(/\s+/).length
        return words / 2.5 // 2.5 words per second
      })

      const totalEstimatedTime = estimatedSecondsPerParagraph.reduce((a, b) => a + b, 0)
      const scrollSpeed = Math.max(totalEstimatedTime / this.readingText.length, 5) // Minimum 5 seconds per paragraph

      let lastScrollTime = 0
      this.scrollInterval = setInterval(() => {
        // Auto-advance paragraph based on elapsed time
        if (this.currentParagraphIndex < this.readingText.length - 1) {
          const shouldAdvance = this.recordingTime - lastScrollTime >= Math.round(scrollSpeed)
          if (shouldAdvance && this.recordingTime > 0) {
            lastScrollTime = this.recordingTime
            this.currentParagraphIndex++
            this.$nextTick(() => {
              this.scrollToCurrentParagraph()
            })
          }
        }
      }, 1000)
    },

    scrollToCurrentParagraph() {
      // Smooth scroll to current paragraph
      const viewport = this.$refs.viewport
      if (!viewport) return

      const paragraphHeight = 100 // Approximate height per paragraph
      this.scrollOffset = -(this.currentParagraphIndex * paragraphHeight)
    },

    calculateWPM() {
      if (this.wordCount > 0 && this.recordingTime > 0) {
        this.calculatedWPM = (this.wordCount / this.recordingTime) * 60
      }
    },

    async uploadVoiceSample() {
      if (!this.audioBlob) {
        this.error = 'No audio recording found'
        return
      }

      this.uploading = true
      this.error = ''

      try {
        const formData = new FormData()
        formData.append('audio_file', this.audioBlob, 'voice_sample.wav')
        formData.append('reading_text', this.readingText.join('\n\n'))
        formData.append('reading_duration_seconds', this.recordingTime)
        formData.append('word_count', this.wordCount)

        const response = await axios.post('/api/voice-samples/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        console.log('Voice sample uploaded:', response.data)

        this.$emit('voice-profile-updated', response.data)

        // Show success message
        this.error = ''
        this.recordingState = 'idle'
        this.reset()

      } catch (error) {
        console.error('Upload failed:', error)
        this.error = error.response?.data?.detail || 'Failed to upload voice sample'
      } finally {
        this.uploading = false
      }
    },

    reset() {
      this.recordingState = 'idle'
      this.audioChunks = []
      this.audioBlob = null
      this.recordingTime = 0
      this.currentParagraphIndex = 0
      this.scrollOffset = 0
      this.calculatedWPM = null
      this.error = ''

      if (this.recordingInterval) {
        clearInterval(this.recordingInterval)
        this.recordingInterval = null
      }

      if (this.scrollInterval) {
        clearInterval(this.scrollInterval)
        this.scrollInterval = null
      }
    },

    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
  },
  beforeUnmount() {
    this.reset()
  }
}
</script>

<style scoped>
.voice-print-recorder {
  max-width: 900px;
  margin: 0 auto;
}

.recording-indicator {
  font-family: monospace;
}

.pulsing {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.reading-display {
  position: relative;
  background: #f5f5f5;
  min-height: 400px;
}

.reading-display.recording-active {
  border: 3px solid #7e57c2;
  box-shadow: 0 0 20px rgba(126, 87, 194, 0.3);
}

.reading-viewport {
  height: 400px;
  overflow: hidden;
  padding: 40px;
  position: relative;
}

.reading-content {
  transition: transform 0.5s ease-in-out;
}

.reading-paragraph {
  font-size: 24px;
  line-height: 1.8;
  margin-bottom: 40px;
  color: #424242;
  transition: all 0.3s ease;
  opacity: 0.5;
}

.reading-paragraph.current-paragraph {
  opacity: 1;
  font-weight: 500;
  color: #7e57c2;
  transform: scale(1.05);
}

.reading-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>
