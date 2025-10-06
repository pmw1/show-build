<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="1200" persistent scrollable>
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

          <!-- Transcription -->
          <v-textarea
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

<script>
export default {
  name: 'NewSOTModal',
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      formValid: false,
      loading: false,
      error: '',
      videoError: '',
      videoPreviewUrl: null,
      videoFileName: '',
      videoBlob: null,
      currentTimecodeDisplay: '00:00:00:00',
      videoSpecs: {
        duration: 0,
        durationDisplay: '00:00:00:00',
        resolution: 'Unknown',
        framerate: 30,
        width: 0,
        height: 0
      },
      cutData: {
        start: '',
        end: ''
      },
      formData: {
        slug: '',
        title: '',
        duration: '00:00:00:00',
        description: '',
        transcription: '',
        type: 'sot',
        status: 'draft',
        cuts: {}, // Dictionary of cut information: { "cutName": { start: "00:00:10:00", end: "00:00:20:00" } }
        credits: {} // Dictionary of credits: { "Name": "John Doe", "Title": "Expert" }
      }
    }
  },
  computed: {
    hasVideo() {
      return !!this.videoBlob
    },
    slugRules() {
      return [
        v => !!v || 'Slug is required'
      ]
    },
    durationRules() {
      return [
        v => !v || /^\d{2}:\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS:FF format'
      ]
    }
  },
  mounted() {
    // Add ESC key listener
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    // Clean up video URL
    if (this.videoPreviewUrl) {
      URL.revokeObjectURL(this.videoPreviewUrl)
    }
  },
  methods: {
    handleKeydown(event) {
      if (event.key === 'Escape' && this.show) {
        this.cancel()
      }
    },

    // Video handling methods
    handleVideoSelect(event) {
      const file = event.target.files[0]
      if (!file) return
      
      this.videoError = ''
      
      if (!file.type.startsWith('video/')) {
        this.videoError = 'Please select a video file'
        return
      }
      
      // Clean up previous video URL
      if (this.videoPreviewUrl) {
        URL.revokeObjectURL(this.videoPreviewUrl)
      }
      
      this.videoBlob = file
      this.videoFileName = file.name
      this.videoPreviewUrl = URL.createObjectURL(file)
      
      console.log(`Video selected: ${file.name}`)
      // this.$toast?.success(`Video selected: ${file.name}`)
    },

    clearVideo() {
      if (this.videoPreviewUrl) {
        URL.revokeObjectURL(this.videoPreviewUrl)
      }
      
      this.videoBlob = null
      this.videoFileName = ''
      this.videoPreviewUrl = null
      this.formData.duration = '00:00:00:00'
      this.videoSpecs = {
        duration: 0,
        durationDisplay: '00:00:00:00',
        resolution: 'Unknown',
        framerate: 30,
        width: 0,
        height: 0
      }
      this.formData.cuts = {}
      this.cutData = { start: '', end: '' }
      
      // Reset file input
      if (this.$refs.sotFileInput) {
        this.$refs.sotFileInput.value = ''
      }
      
      console.log('Video cleared')
      // this.$toast?.success('Video cleared')
    },

    handleVideoMetadata() {
      const video = this.$refs.videoPlayer
      if (!video) return
      
      const duration = video.duration
      this.videoSpecs.duration = duration
      this.videoSpecs.durationDisplay = this.secondsToTimecode(duration)
      this.videoSpecs.width = video.videoWidth
      this.videoSpecs.height = video.videoHeight
      this.videoSpecs.resolution = `${video.videoWidth}×${video.videoHeight}`
      
      // Auto-detect framerate (assume 30fps, could be enhanced)
      this.videoSpecs.framerate = 30
      
      // Set form duration
      this.formData.duration = this.secondsToTimecode(duration)
      
      console.log('Video metadata loaded:', this.videoSpecs)
    },

    handleTimeUpdate() {
      const video = this.$refs.videoPlayer
      if (!video) return
      
      this.currentTimecodeDisplay = this.secondsToTimecode(video.currentTime)
    },

    // Timecode utilities
    secondsToTimecode(seconds, showFrames = true) {
      if (!seconds || isNaN(seconds)) return '00:00:00:00'
      
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      const frames = Math.floor((seconds % 1) * this.videoSpecs.framerate)
      
      const h = hours.toString().padStart(2, '0')
      const m = minutes.toString().padStart(2, '0')
      const s = secs.toString().padStart(2, '0')
      const f = frames.toString().padStart(2, '0')
      
      return showFrames ? `${h}:${m}:${s}:${f}` : `${h}:${m}:${s}`
    },

    timecodeToSeconds(timecode) {
      if (!timecode || typeof timecode !== 'string') return 0
      
      const parts = timecode.split(':')
      if (parts.length !== 4) return 0
      
      const hours = parseInt(parts[0]) || 0
      const minutes = parseInt(parts[1]) || 0
      const seconds = parseInt(parts[2]) || 0
      const frames = parseInt(parts[3]) || 0
      
      return hours * 3600 + minutes * 60 + seconds + (frames / this.videoSpecs.framerate)
    },

    // Video control methods
    markIn() {
      const video = this.$refs.videoPlayer
      if (!video) return
      
      this.cutData.start = this.secondsToTimecode(video.currentTime)
    },

    markOut() {
      const video = this.$refs.videoPlayer
      if (!video) return
      
      this.cutData.end = this.secondsToTimecode(video.currentTime)
    },

    goToMarkIn() {
      const video = this.$refs.videoPlayer
      if (!video || !this.cutData.start) return
      
      video.currentTime = this.timecodeToSeconds(this.cutData.start)
    },

    goToMarkOut() {
      const video = this.$refs.videoPlayer
      if (!video || !this.cutData.end) return
      
      video.currentTime = this.timecodeToSeconds(this.cutData.end)
    },

    async previewCut() {
      const video = this.$refs.videoPlayer
      if (!video || !this.cutData.start || !this.cutData.end) {
        console.error('Please set both Mark In and Mark Out points')
        // this.$toast?.error('Please set both Mark In and Mark Out points')
        return
      }
      
      const startTime = this.timecodeToSeconds(this.cutData.start)
      const endTime = this.timecodeToSeconds(this.cutData.end)
      
      if (startTime >= endTime) {
        console.error('Mark In must be before Mark Out')
        // this.$toast?.error('Mark In must be before Mark Out')
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
        // this.$toast?.success('Preview complete')
      }, duration)
      
      console.log('Playing preview...')
      // this.$toast?.info('Playing preview...')
    },

    // Cut management methods
    addCut() {
      if (!this.cutData.start || !this.cutData.end) {
        console.error('Please set both Mark In and Mark Out points')
        // this.$toast?.error('Please set both Mark In and Mark Out points')
        return
      }
      
      const startTime = this.timecodeToSeconds(this.cutData.start)
      const endTime = this.timecodeToSeconds(this.cutData.end)
      
      if (startTime >= endTime) {
        console.error('Mark In must be before Mark Out')
        // this.$toast?.error('Mark In must be before Mark Out')
        return
      }
      
      // Generate cut name
      const cutNumber = Object.keys(this.formData.cuts).length + 1
      const cutName = `Cut ${cutNumber}`
      
      // Add cut to dictionary (Vue 3 syntax)
      this.formData.cuts[cutName] = {
        start: this.cutData.start,
        end: this.cutData.end
      }
      
      // Clear current cut data
      this.cutData = { start: '', end: '' }
      
      console.log(`${cutName} added`)
      // this.$toast?.success(`${cutName} added`)
    },

    updateCutKey(oldKey, newKey, cutData) {
      if (oldKey === newKey) return
      
      // Remove old key and add new key (Vue 3 syntax)
      delete this.formData.cuts[oldKey]
      this.formData.cuts[newKey] = cutData
    },

    removeCut(cutName) {
      delete this.formData.cuts[cutName]
      console.log(`${cutName} removed`)
      // this.$toast?.success(`${cutName} removed`)
    },

    calculateCutDuration(cut) {
      if (!cut.start || !cut.end) return '00:00:00:00'
      
      const startSeconds = this.timecodeToSeconds(cut.start)
      const endSeconds = this.timecodeToSeconds(cut.end)
      const duration = endSeconds - startSeconds
      
      return this.secondsToTimecode(Math.max(0, duration))
    },

    // Credits management methods
    addCredit() {
      const creditNumber = Object.keys(this.formData.credits).length + 1
      const creditKey = `Credit ${creditNumber}`
      
      this.formData.credits[creditKey] = ''
    },

    updateCreditKey(oldKey, newKey) {
      if (oldKey === newKey) return
      
      const value = this.formData.credits[oldKey]
      delete this.formData.credits[oldKey]
      this.formData.credits[newKey] = value
    },

    removeCredit(creditKey) {
      delete this.formData.credits[creditKey]
      console.log(`${creditKey} removed`)
      // this.$toast?.success(`${creditKey} removed`)
    },

    // Main creation method
    async createSOTItem() {
      if (!this.$refs.sotFormRef.validate()) {
        return
      }
      
      if (!this.hasVideo) {
        this.error = 'Please select a video file'
        return
      }
      
      this.loading = true
      this.error = ''
      
      try {
        // Create the SOT item data
        const sotItem = {
          ...this.formData,
          // Video will be handled by the parent component
          videoBlob: this.videoBlob,
          videoFileName: this.videoFileName,
          videoSpecs: this.videoSpecs,
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
        this.$emit('submit', sotItem)
        
        // Reset form
        this.resetForm()
        
        // Close modal
        this.cancel()
        
      } catch (error) {
        console.error('Error creating SOT item:', error)
        this.error = 'Failed to create SOT item. Please try again.'
      } finally {
        this.loading = false
      }
    },
    
    resetForm() {
      this.formData = {
        slug: '',
        title: '',
        duration: '00:00:00:00',
        description: '',
        transcription: '',
        type: 'sot',
        status: 'draft',
        cuts: {},
        credits: {}
      }
      this.clearVideo()
      this.error = ''
      this.videoError = ''
      this.cutData = { start: '', end: '' }
    },

    cancel() {
      this.resetForm()
      this.$emit('update:show', false)
    }
  }
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