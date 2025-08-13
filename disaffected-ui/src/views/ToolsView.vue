<template>
  <v-container fluid class="pa-0">
    <v-row class="header-row ma-0">
      <v-col cols="12" class="pa-4">
        <h2 class="text-h4 font-weight-bold">Tools</h2>
        <p class="text-body-1 text-grey-darken-1 mt-2">
          Episode creation and workflow tools for managing your show content
        </p>
      </v-col>
    </v-row>
    
    <!-- Episode Management Tools -->
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="primary">mdi-television-play</v-icon>
            <span>Episode Management</span>
          </v-card-title>
          <v-card-text>
            <v-row>
              <!-- Episode Scaffolding -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100">
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="primary" class="mb-3">mdi-plus-circle-outline</v-icon>
                    <h3 class="text-h6 mb-2">Create New Episode</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Scaffold a new episode with the complete directory structure and template files
                    </p>
                    <EpisodeScaffoldModal @episode-created="handleEpisodeCreated" />
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Episode Processing (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-cogs</v-icon>
                    <h3 class="text-h6 mb-2">Process Episode</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Run complete episode processing workflow: quotes, media compilation, video preprocessing
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Episode Validation (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-check-circle-outline</v-icon>
                    <h3 class="text-h6 mb-2">Validate Episode</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Check episode structure, validate cue blocks, and ensure content integrity
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Content Processing Tools -->
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="primary">mdi-file-multiple</v-icon>
            <span>Content Processing</span>
          </v-card-title>
          <v-card-text>
            <v-row>
              <!-- Quote Generation (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-format-quote-close</v-icon>
                    <h3 class="text-h6 mb-2">Generate Quotes</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Extract and generate quote images from episode rundown files
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Media Processing (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-video-box</v-icon>
                    <h3 class="text-h6 mb-2">Process Media</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Convert and optimize video/audio files for broadcast compatibility
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Cue Management (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-playlist-edit</v-icon>
                    <h3 class="text-h6 mb-2">Fix Cue Blocks</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Validate and fix malformed cue block syntax in rundown files
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Distribution Tools -->
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="primary">mdi-cloud-upload</v-icon>
            <span>Distribution & Publishing</span>
          </v-card-title>
          <v-card-text>
            <v-row>
              <!-- Distribution Orchestration (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-rocket-launch</v-icon>
                    <h3 class="text-h6 mb-2">Distribute Episode</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Orchestrate multi-platform distribution and publishing workflows
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Platform Upload (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-upload-network</v-icon>
                    <h3 class="text-h6 mb-2">Platform Upload</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Upload episodes to podcast platforms, YouTube, and social media
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- Transcription (Future) -->
              <v-col cols="12" md="6" lg="4">
                <v-card variant="outlined" class="h-100" disabled>
                  <v-card-text class="text-center pa-6">
                    <v-icon size="48" color="grey" class="mb-3">mdi-transcribe</v-icon>
                    <h3 class="text-h6 mb-2">Transcribe Audio</h3>
                    <p class="text-body-2 text-grey-darken-1 mb-4">
                      Generate transcripts from audio files using AI speech recognition
                    </p>
                    <v-btn variant="outlined" disabled>
                      Coming Soon
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Success Snackbar -->
    <v-snackbar
      v-model="showSuccessMessage"
      color="success"
      timeout="4000"
    >
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="showSuccessMessage = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import EpisodeScaffoldModal from '@/components/EpisodeScaffoldModal.vue'

// Reactive data
const showSuccessMessage = ref(false)
const successMessage = ref('')

// Event handlers
const handleEpisodeCreated = (episode) => {
  successMessage.value = `Episode ${episode.episode_number} created successfully!`
  showSuccessMessage.value = true
}
</script>

<style scoped>
.header-row {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(25, 118, 210, 0.05) 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.v-card {
  transition: transform 0.2s ease-in-out;
}

.v-card:not([disabled]):hover {
  transform: translateY(-2px);
}

.v-card[disabled] {
  opacity: 0.6;
}
</style>