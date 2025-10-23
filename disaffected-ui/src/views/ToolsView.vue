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

    <!-- Active Tools - Always Visible -->
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card class="mb-4 elevation-4">
          <v-card-title class="d-flex align-center bg-primary text-white">
            <v-icon class="me-2">mdi-star-circle</v-icon>
            <span>Active Tools</span>
          </v-card-title>
          <v-list lines="two">
            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-plus-circle-outline</v-icon>
              </template>
              <v-list-item-title class="font-weight-bold">Create New Episode</v-list-item-title>
              <v-list-item-subtitle>Scaffold new episode with directory structure</v-list-item-subtitle>
              <template v-slot:append>
                <EpisodeScaffoldModal @episode-created="handleEpisodeCreated" />
              </template>
            </v-list-item>

            <v-divider></v-divider>

            <v-list-item to="/consolidation">
              <template v-slot:prepend>
                <v-icon color="primary">mdi-folder-sync</v-icon>
              </template>
              <v-list-item-title class="font-weight-bold">Episode Consolidation</v-list-item-title>
              <v-list-item-subtitle>Sync episode files between Google Drive and Syncthing</v-list-item-subtitle>
              <template v-slot:append>
                <v-btn variant="outlined" size="small" color="primary">Open Tool</v-btn>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <!-- All Tools (Collapsible Sections) -->
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-expansion-panels variant="accordion">
          <!-- Episode Management Tools -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-icon class="me-2" color="primary">mdi-television-play</v-icon>
                <span class="text-h6">Episode Management</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list lines="two">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-plus-circle-outline</v-icon>
                  </template>
                  <v-list-item-title class="font-weight-bold">Create New Episode</v-list-item-title>
                  <v-list-item-subtitle>Scaffold new episode with directory structure</v-list-item-subtitle>
                  <template v-slot:append>
                    <EpisodeScaffoldModal @episode-created="handleEpisodeCreated" />
                  </template>
                </v-list-item>

                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-cogs</v-icon>
                  </template>
                  <v-list-item-title>Process Episode</v-list-item-title>
                  <v-list-item-subtitle>Complete episode processing workflow</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>

                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-check-circle-outline</v-icon>
                  </template>
                  <v-list-item-title>Validate Episode</v-list-item-title>
                  <v-list-item-subtitle>Check structure and content integrity</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- Content Processing Tools -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-icon class="me-2" color="primary">mdi-file-multiple</v-icon>
                <span class="text-h6">Content Processing</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list lines="two">
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-format-quote-close</v-icon>
                  </template>
                  <v-list-item-title>Generate Quotes</v-list-item-title>
                  <v-list-item-subtitle>Extract quote images from rundown</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>

                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-video-box</v-icon>
                  </template>
                  <v-list-item-title>Process Media</v-list-item-title>
                  <v-list-item-subtitle>Convert and optimize media files</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>

                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-playlist-edit</v-icon>
                  </template>
                  <v-list-item-title>Fix Cue Blocks</v-list-item-title>
                  <v-list-item-subtitle>Validate and fix cue block syntax</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- Distribution Tools -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-icon class="me-2" color="primary">mdi-cloud-upload</v-icon>
                <span class="text-h6">Distribution & Publishing</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list lines="two">
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-rocket-launch</v-icon>
                  </template>
                  <v-list-item-title>Distribute Episode</v-list-item-title>
                  <v-list-item-subtitle>Multi-platform distribution workflows</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>

                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-upload-network</v-icon>
                  </template>
                  <v-list-item-title>Platform Upload</v-list-item-title>
                  <v-list-item-subtitle>Upload to podcast platforms and social media</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>

                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-transcribe</v-icon>
                  </template>
                  <v-list-item-title>Transcribe Audio</v-list-item-title>
                  <v-list-item-subtitle>Generate transcripts using AI</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Coming Soon</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- File System Management -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-icon class="me-2" color="primary">mdi-folder-cog</v-icon>
                <span class="text-h6">File System Management</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list lines="two">
                <v-list-item to="/consolidation">
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-folder-sync</v-icon>
                  </template>
                  <v-list-item-title class="font-weight-bold">Episode Consolidation</v-list-item-title>
                  <v-list-item-subtitle>Sync episode files between Google Drive and Syncthing</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-btn variant="outlined" size="small" color="primary">Open Tool</v-btn>
                  </template>
                </v-list-item>

                <v-divider class="my-2" />

                <!-- Utilities Subsection -->
                <v-list-subheader class="text-subtitle-2 font-weight-bold text-grey-darken-2">
                  <v-icon size="small" class="me-2">mdi-wrench</v-icon>
                  Utilities
                </v-list-subheader>

                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-folder-edit</v-icon>
                  </template>
                  <v-list-item-title class="font-weight-bold">Normalize Episode Names</v-list-item-title>
                  <v-list-item-subtitle>Fix episode folder names in Google Drive (remove date suffixes, extra text)</v-list-item-subtitle>
                  <template v-slot:append>
                    <EpisodeNameNormalizerModal />
                  </template>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
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
import EpisodeNameNormalizerModal from '@/components/EpisodeNameNormalizerModal.vue'

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