<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="1200" scrollable>
    <v-card class="sot-modal-card">
      <v-card-title class="d-flex align-center bg-orange-darken-2 text-white">
        <v-icon class="mr-2">mdi-video-outline</v-icon>
        Create SOT (Sound-on-Tape) Item
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel" color="white">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text class="pb-2">
        <v-form ref="sotFormRef" v-model="formValid">
          <!-- Slug (required) -->
          <v-text-field
            v-model="formData.slug"
            label="Slug"
            placeholder="short-descriptive-name"
            :rules="slugRules"
            required
            variant="outlined"
            density="comfortable"
            class="mb-3"
          >
            <template #append-inner>
              <span class="text-error">*</span>
            </template>
          </v-text-field>

          <!-- Title -->
          <v-text-field
            v-model="formData.title"
            label="Title"
            placeholder="SOT Title"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <!-- Video Selection and Duration Row -->
          <v-row class="mb-3">
            <v-col cols="8">
              <v-label class="text-subtitle-2 mb-2">Select Video <span class="text-error">*</span></v-label>
              
              <div class="d-flex gap-2 mb-3">
                <v-btn
                  @click="$refs.sotFileInput.click()"
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-folder-open"
                >
                  Browse Video Files
                </v-btn>
                
                <v-btn
                  v-if="hasVideo"
                  @click="clearVideo"
                  color="error"
                  variant="outlined"
                  prepend-icon="mdi-delete"
                >
                  Clear Video
                </v-btn>
              </div>

              <!-- Hidden file input -->
              <input
                ref="sotFileInput"
                type="file"
                accept="video/*"
                @change="handleVideoSelect"
                style="display: none;"
              />

              <v-alert
                v-if="videoError"
                type="error"
                variant="tonal"
                class="mb-3"
              >
                {{ videoError }}
              </v-alert>
            </v-col>

            <v-col cols="4">
              <!-- Duration (auto-detected) -->
              <v-text-field
                v-model="formData.duration"
                label="Duration (HH:MM:SS:FF)"
                placeholder="00:00:00:00"
                :rules="durationRules"
                variant="outlined"
                density="comfortable"
                readonly
                hint="Auto-detected from video"
                persistent-hint
              />
            </v-col>
          </v-row>

          <!-- Video Player -->
          <div v-if="hasVideo" class="video-player-container mb-4">
            <div class="video-wrapper">
              <video
                ref="videoPlayer"
                :src="videoPreviewUrl"
                controls
                preload="metadata"
                @loadedmetadata="handleVideoMetadata"
                @timeupdate="handleTimeUpdate"
                class="sot-video-player"
              />
            
            </div>
            
            <!-- Video Info Overlay -->
            <div class="video-info-overlay">
              <div class="video-specs">
                <div><strong>{{ videoFileName }}</strong></div>
                <div>{{ videoSpecs.resolution }} • {{ videoSpecs.framerate }}fps</div>
                <div>Duration: {{ videoSpecs.durationDisplay }}</div>
                <div>Current: {{ currentTimecodeDisplay }}</div>
              </div>
            </div>

            <!-- Video Controls -->
            <div class="video-controls mt-2">
              <v-row>
                <v-col cols="6">
                  <v-text-field
                    v-model="cutData.start"
                    label="Mark In (Start)"
                    placeholder="00:00:00:00"
                    variant="outlined"
                    density="compact"
                    append-icon="mdi-content-cut"
                    @click:append="markIn"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="cutData.end"
                    label="Mark Out (End)"
                    placeholder="00:00:00:00"
                    variant="outlined"
                    density="compact"
                    append-icon="mdi-content-cut"
                    @click:append="markOut"
                  />
                </v-col>
              </v-row>
              
              <div class="d-flex gap-2 mb-3">
                <v-btn @click="goToMarkIn" size="small" variant="outlined">Go to In</v-btn>
                <v-btn @click="goToMarkOut" size="small" variant="outlined">Go to Out</v-btn>
                <v-btn @click="previewCut" size="small" color="primary">Preview Cut</v-btn>
                <v-btn @click="addCut" size="small" color="success" prepend-icon="mdi-plus">Add Cut</v-btn>
              </div>
            </div>
          </div>

          <!-- Cut Information Dictionary -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">Cut Information</v-card-title>
            <v-card-text>
              <div v-if="Object.keys(formData.cuts).length === 0" class="text-center py-4 text-medium-emphasis">
                No cuts defined. Use video controls above to mark and add cuts.
              </div>
              
              <div v-for="(cut, index) in Object.entries(formData.cuts)" :key="index" class="cut-item mb-3">
                <v-row align="center">
                  <v-col cols="3">
                    <v-text-field
                      v-model="cut[0]"
                      label="Cut Name"
                      variant="outlined"
                      density="compact"
                      @update:model-value="(newKey) => updateCutKey(cut[0], newKey, cut[1])"
                    />
                  </v-col>
                  <v-col cols="3">
                    <v-text-field
                      v-model="cut[1].start"
                      label="Start (HH:MM:SS:FF)"
                      variant="outlined"
                      density="compact"
                    />
                  </v-col>
                  <v-col cols="3">
                    <v-text-field
                      v-model="cut[1].end"
                      label="End (HH:MM:SS:FF)"
                      variant="outlined"
                      density="compact"
                    />
                  </v-col>
                  <v-col cols="2">
                    <v-text-field
                      :model-value="calculateCutDuration(cut[1])"
                      label="Duration"
                      variant="outlined"
                      density="compact"
                      readonly
                    />
                  </v-col>
                  <v-col cols="1">
                    <v-btn
                      @click="removeCut(cut[0])"
                      icon
                      size="small"
                      color="error"
                      variant="text"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>

          <!-- Credits/Lower Thirds -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6">Credits/Lower Thirds</v-card-title>
            <v-card-text>
              <div v-if="Object.keys(formData.credits).length === 0" class="text-center py-4 text-medium-emphasis">
                No credits defined. Click "Add Credit" to add lower thirds information.
              </div>
              
              <div v-for="(credit, key) in formData.credits" :key="key" class="credit-item mb-3">
                <v-row align="center">
                  <v-col cols="5">
                    <v-text-field
                      :model-value="key"
                      label="Credit Type (e.g., Name, Title)"
                      variant="outlined"
                      density="compact"
                      @update:model-value="(newKey) => updateCreditKey(key, newKey)"
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="formData.credits[key]"
                      label="Credit Value"
                      variant="outlined"
                      density="compact"
                    />
                  </v-col>
                  <v-col cols="1">
                    <v-btn
                      @click="removeCredit(key)"
                      icon
                      size="small"
                      color="error"
                      variant="text"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
              </div>
              
              <v-btn
                @click="addCredit"
                size="small"
                color="primary"
                prepend-icon="mdi-plus"
                variant="outlined"
              >
                Add Credit
              </v-btn>
            </v-card-text>
          </v-card>

          <!-- Description -->
          <v-textarea
            v-model="formData.description"
            label="Description"
            placeholder="Description of the SOT content"
            variant="outlined"
            rows="3"
            auto-grow
            class="mb-3"
          />

          <!-- Transcription (only shown if transcript exists) -->
          <v-textarea
            v-if="formData.transcription"
            v-model="formData.transcription"
            label="Transcription"
            placeholder="Full transcription of the video content"
            variant="outlined"
            rows="4"
            auto-grow
            class="mb-3"
          />

          <!-- Error Display -->
          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            class="mb-3"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>
      
      <v-card-actions class="px-6 pb-4">
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel" variant="outlined">
          Cancel
        </v-btn>
        <v-btn 
          color="orange-darken-2" 
          @click="createSOTItem"
          :disabled="!formValid || !hasVideo"
          :loading="loading"
          variant="elevated"
          class="ml-2"
        >
          <v-icon left>mdi-plus</v-icon>
          Create SOT Item
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:show', 'submit'])

// Template refs
const sotFormRef = ref(null)
const sotFileInput = ref(null)
const videoPlayer = ref(null)

// Data
const formValid = ref(false)
const loading = ref(false)
const error = ref('')
const videoError = ref('')
const videoPreviewUrl = ref(null)
const videoFileName = ref('')
const videoBlob = ref(null)
const currentTimecodeDisplay = ref('00:00:00:00')
const videoSpecs = reactive({
  duration: 0,
  durationDisplay: '00:00:00:00',
  resolution: 'Unknown',
  framerate: 30,
  width: 0,
  height: 0
})
const cutData = reactive({
  start: '',
  end: ''
})
const formData = reactive({
  slug: '',
  title: '',
  duration: '00:00:00:00',
  description: '',
  transcription: '',
  type: 'sot',
  status: 'draft',
  cuts: {}, // Dictionary of cut information: { "cutName": { start: "00:00:10:00", end: "00:00:20:00" } }
  credits: {} // Dictionary of credits: { "Name": "John Doe", "Title": "Expert" }
})

// Computed
const hasVideo = computed(() => {
  return !!videoBlob.value
})

const slugRules = computed(() => {
  return [
    v => !!v || 'Slug is required'
  ]
})

const durationRules = computed(() => {
  return [
    v => !v || /^\d{2}:\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS:FF format'
  ]
})

// Watch
watch(() => props.show, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})

// Lifecycle
onBeforeUnmount(() => {
  // Clean up video URL
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }
})

// Timecode utilities
function secondsToTimecode(seconds, showFrames = true) {
  if (!seconds || isNaN(seconds)) return '00:00:00:00'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  const frames = Math.floor((seconds % 1) * videoSpecs.framerate)

  const h = hours.toString().padStart(2, '0')
  const m = minutes.toString().padStart(2, '0')
  const s = secs.toString().padStart(2, '0')
  const f = frames.toString().padStart(2, '0')

  return showFrames ? `${h}:${m}:${s}:${f}` : `${h}:${m}:${s}`
}

function timecodeToSeconds(timecode) {
  if (!timecode || typeof timecode !== 'string') return 0

  const parts = timecode.split(':')
  if (parts.length !== 4) return 0

  const hours = parseInt(parts[0]) || 0
  const minutes = parseInt(parts[1]) || 0
  const seconds = parseInt(parts[2]) || 0
  const frames = parseInt(parts[3]) || 0

  return hours * 3600 + minutes * 60 + seconds + (frames / videoSpecs.framerate)
}

// Video handling methods
function handleVideoSelect(event) {
  const file = event.target.files[0]
  if (!file) return

  videoError.value = ''

  if (!file.type.startsWith('video/')) {
    videoError.value = 'Please select a video file'
    return
  }

  // Clean up previous video URL
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }

  videoBlob.value = file
  videoFileName.value = file.name
  videoPreviewUrl.value = URL.createObjectURL(file)

  console.log(`Video selected: ${file.name}`)
  // $toast?.success(`Video selected: ${file.name}`)
}

function clearVideo() {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }

  videoBlob.value = null
  videoFileName.value = ''
  videoPreviewUrl.value = null
  formData.duration = '00:00:00:00'
  videoSpecs.duration = 0
  videoSpecs.durationDisplay = '00:00:00:00'
  videoSpecs.resolution = 'Unknown'
  videoSpecs.framerate = 30
  videoSpecs.width = 0
  videoSpecs.height = 0
  formData.cuts = {}
  cutData.start = ''
  cutData.end = ''

  // Reset file input
  if (sotFileInput.value) {
    sotFileInput.value.value = ''
  }

  console.log('Video cleared')
  // $toast?.success('Video cleared')
}

function handleVideoMetadata() {
  const video = videoPlayer.value
  if (!video) return

  const duration = video.duration
  videoSpecs.duration = duration
  videoSpecs.durationDisplay = secondsToTimecode(duration)
  videoSpecs.width = video.videoWidth
  videoSpecs.height = video.videoHeight
  videoSpecs.resolution = `${video.videoWidth}×${video.videoHeight}`

  // Auto-detect framerate (assume 30fps, could be enhanced)
  videoSpecs.framerate = 30

  // Set form duration
  formData.duration = secondsToTimecode(duration)

  console.log('Video metadata loaded:', videoSpecs)
}

function handleTimeUpdate() {
  const video = videoPlayer.value
  if (!video) return

  currentTimecodeDisplay.value = secondsToTimecode(video.currentTime)
}

// Video control methods
function markIn() {
  const video = videoPlayer.value
  if (!video) return

  cutData.start = secondsToTimecode(video.currentTime)
}

function markOut() {
  const video = videoPlayer.value
  if (!video) return

  cutData.end = secondsToTimecode(video.currentTime)
}

function goToMarkIn() {
  const video = videoPlayer.value
  if (!video || !cutData.start) return

  video.currentTime = timecodeToSeconds(cutData.start)
}

function goToMarkOut() {
  const video = videoPlayer.value
  if (!video || !cutData.end) return

  video.currentTime = timecodeToSeconds(cutData.end)
}

async function previewCut() {
  const video = videoPlayer.value
  if (!video || !cutData.start || !cutData.end) {
    console.error('Please set both Mark In and Mark Out points')
    // $toast?.error('Please set both Mark In and Mark Out points')
    return
  }

  const startTime = timecodeToSeconds(cutData.start)
  const endTime = timecodeToSeconds(cutData.end)

  if (startTime >= endTime) {
    console.error('Mark In must be before Mark Out')
    // $toast?.error('Mark In must be before Mark Out')
    return
  }

  // Go to start and play
  video.currentTime = startTime
  await video.play()

  // Set timeout to pause at end
  const duration = (endTime - startTime) * 1000
  setTimeout(() => {
    video.pause()
    console.log('Preview complete')
    // $toast?.success('Preview complete')
  }, duration)

  console.log('Playing preview...')
  // $toast?.info('Playing preview...')
}

// Cut management methods
function addCut() {
  if (!cutData.start || !cutData.end) {
    console.error('Please set both Mark In and Mark Out points')
    // $toast?.error('Please set both Mark In and Mark Out points')
    return
  }

  const startTime = timecodeToSeconds(cutData.start)
  const endTime = timecodeToSeconds(cutData.end)

  if (startTime >= endTime) {
    console.error('Mark In must be before Mark Out')
    // $toast?.error('Mark In must be before Mark Out')
    return
  }

  // Generate cut name
  const cutNumber = Object.keys(formData.cuts).length + 1
  const cutName = `Cut ${cutNumber}`

  // Add cut to dictionary (Vue 3 syntax)
  formData.cuts[cutName] = {
    start: cutData.start,
    end: cutData.end
  }

  // Clear current cut data
  cutData.start = ''
  cutData.end = ''

  console.log(`${cutName} added`)
  // $toast?.success(`${cutName} added`)
}

function updateCutKey(oldKey, newKey, cutDataVal) {
  if (oldKey === newKey) return

  // Remove old key and add new key (Vue 3 syntax)
  delete formData.cuts[oldKey]
  formData.cuts[newKey] = cutDataVal
}

function removeCut(cutName) {
  delete formData.cuts[cutName]
  console.log(`${cutName} removed`)
  // $toast?.success(`${cutName} removed`)
}

function calculateCutDuration(cut) {
  if (!cut.start || !cut.end) return '00:00:00:00'

  const startSeconds = timecodeToSeconds(cut.start)
  const endSeconds = timecodeToSeconds(cut.end)
  const duration = endSeconds - startSeconds

  return secondsToTimecode(Math.max(0, duration))
}

// Credits management methods
function addCredit() {
  const creditNumber = Object.keys(formData.credits).length + 1
  const creditKey = `Credit ${creditNumber}`

  formData.credits[creditKey] = ''
}

function updateCreditKey(oldKey, newKey) {
  if (oldKey === newKey) return

  const value = formData.credits[oldKey]
  delete formData.credits[oldKey]
  formData.credits[newKey] = value
}

function removeCredit(creditKey) {
  delete formData.credits[creditKey]
  console.log(`${creditKey} removed`)
  // $toast?.success(`${creditKey} removed`)
}

// Main creation method
async function createSOTItem() {
  if (!sotFormRef.value.validate()) {
    return
  }

  if (!hasVideo.value) {
    error.value = 'Please select a video file'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Create the SOT item data
    const sotItem = {
      ...formData,
      // Video will be handled by the parent component
      videoBlob: videoBlob.value,
      videoFileName: videoFileName.value,
      videoSpecs: { ...videoSpecs },
      // Additional fields for SOT items
      subtitle: '',
      airdate: '',
      priority: '',
      guests: '',
      tags: '',
      server_message: '',
      customer: '',
      link: ''
    }

    console.log('Creating SOT item with cuts:', sotItem.cuts)
    console.log('Creating SOT item with credits:', sotItem.credits)

    // Emit the item creation
    emit('submit', sotItem)

    // Reset form
    resetForm()

    // Close modal
    cancel()

  } catch (err) {
    console.error('Error creating SOT item:', err)
    error.value = 'Failed to create SOT item. Please try again.'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formData.slug = ''
  formData.title = ''
  formData.duration = '00:00:00:00'
  formData.description = ''
  formData.transcription = ''
  formData.type = 'sot'
  formData.status = 'draft'
  formData.cuts = {}
  formData.credits = {}
  clearVideo()
  error.value = ''
  videoError.value = ''
  cutData.start = ''
  cutData.end = ''
}

function cancel() {
  resetForm()
  emit('update:show', false)
}
</script>

<style scoped>
.sot-modal-card {
  max-height: 95vh;
  overflow-y: auto;
}

.video-player-container {
  position: relative;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: #000;
  contain: layout style;
  min-height: 200px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  min-height: 200px;
  max-height: 500px;
  overflow: visible;
  contain: layout;
}

.sot-video-player {
  width: 100%;
  max-height: 500px;
  height: auto;
  display: block;
  object-fit: contain;
  min-height: 200px;
}

.video-info-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.3;
  z-index: 10;
}

.video-controls {
  background: #f5f5f5;
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  margin-top: 8px;
  border-radius: 0 0 8px 8px;
}

.cut-item, .credit-item {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
}

.cut-item:hover, .credit-item:hover {
  background: #f0f0f0;
}
</style>