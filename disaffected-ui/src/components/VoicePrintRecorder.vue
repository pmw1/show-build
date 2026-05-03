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

<script setup>
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'
import axios from 'axios'

const emit = defineEmits(['voice-profile-updated'])

const recordingState = ref('idle')
let mediaRecorder = null
let audioChunks = []
const audioBlob = ref(null)
const recordingTime = ref(0)
let recordingInterval = null
const currentParagraphIndex = ref(0)
const scrollOffset = ref(0)
let scrollInterval = null
const calculatedWPM = ref(null)
const wordCount = ref(0)
const error = ref('')
const uploading = ref(false)
const viewport = ref(null)

const readingText = [
  "Welcome to the voice print recording system. This tool will help us understand your natural speaking rhythm and create a unique profile for your voice.",
  "As you read this text aloud, the system is recording your audio and measuring how quickly you speak. This measurement is called words per minute, or WPM.",
  "Everyone has their own natural speaking pace. Some people speak quickly, others more slowly. There's no right or wrong speed - we just want to capture your authentic voice.",
  "The recording will also be used to create a voice sample for text-to-speech synthesis. This means in the future, the system might be able to generate speech that sounds like you.",
  "Please read naturally and clearly. Imagine you're narrating a documentary or reading the news. Take your time and enunciate each word.",
  "Thank you for participating in this voice profiling process. Your unique vocal characteristics will be saved and used to enhance your experience in the system."
]

const scrollProgress = computed(() => {
  if (readingText.length === 0) return 0
  return (currentParagraphIndex.value / (readingText.length - 1)) * 100
})

function scrollToCurrentParagraph() {
  if (!viewport.value) return
  const paragraphHeight = 100
  scrollOffset.value = -(currentParagraphIndex.value * paragraphHeight)
}

function startAutoScroll() {
  const estimatedSecondsPerParagraph = readingText.map(p => p.split(/\s+/).length / 2.5)
  const totalEstimatedTime = estimatedSecondsPerParagraph.reduce((a, b) => a + b, 0)
  const scrollSpeed = Math.max(totalEstimatedTime / readingText.length, 5)

  let lastScrollTime = 0
  scrollInterval = setInterval(() => {
    if (currentParagraphIndex.value < readingText.length - 1) {
      if (recordingTime.value - lastScrollTime >= Math.round(scrollSpeed) && recordingTime.value > 0) {
        lastScrollTime = recordingTime.value
        currentParagraphIndex.value++
        nextTick(scrollToCurrentParagraph)
      }
    }
  }, 1000)
}

function calculateWPM() {
  if (wordCount.value > 0 && recordingTime.value > 0) {
    calculatedWPM.value = (wordCount.value / recordingTime.value) * 60
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (event) => { audioChunks.push(event.data) }
    mediaRecorder.onstop = () => {
      audioBlob.value = new Blob(audioChunks, { type: 'audio/wav' })
      recordingState.value = 'completed'
      calculateWPM()
    }

    mediaRecorder.start()
    recordingState.value = 'recording'
    recordingTime.value = 0
    recordingInterval = setInterval(() => { recordingTime.value++ }, 1000)
    startAutoScroll()
    wordCount.value = readingText.join(' ').split(/\s+/).filter(w => w.length > 0).length
  } catch (err) {
    console.error('Error starting recording:', err)
    error.value = 'Failed to access microphone. Please check permissions.'
  }
}

function stopRecording() {
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
    mediaRecorder.stream.getTracks().forEach(track => track.stop())
  }
  if (recordingInterval) { clearInterval(recordingInterval); recordingInterval = null }
  if (scrollInterval) { clearInterval(scrollInterval); scrollInterval = null }
}

async function uploadVoiceSample() {
  if (!audioBlob.value) { error.value = 'No audio recording found'; return }
  uploading.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('audio_file', audioBlob.value, 'voice_sample.wav')
    formData.append('reading_text', readingText.join('\n\n'))
    formData.append('reading_duration_seconds', recordingTime.value)
    formData.append('word_count', wordCount.value)
    const response = await axios.post('/api/voice-samples/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    console.log('Voice sample uploaded:', response.data)
    emit('voice-profile-updated', response.data)
    error.value = ''
    recordingState.value = 'idle'
    reset()
  } catch (err) {
    console.error('Upload failed:', err)
    error.value = err.response?.data?.detail || 'Failed to upload voice sample'
  } finally {
    uploading.value = false
  }
}

function reset() {
  recordingState.value = 'idle'
  audioChunks = []
  audioBlob.value = null
  recordingTime.value = 0
  currentParagraphIndex.value = 0
  scrollOffset.value = 0
  calculatedWPM.value = null
  error.value = ''
  if (recordingInterval) { clearInterval(recordingInterval); recordingInterval = null }
  if (scrollInterval) { clearInterval(scrollInterval); scrollInterval = null }
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onBeforeUnmount(reset)
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
