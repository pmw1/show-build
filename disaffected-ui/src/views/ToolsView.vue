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

                <v-list-item @click="showMp3Modal = true">
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-music</v-icon>
                  </template>
                  <v-list-item-title class="font-weight-bold">Generate MP3</v-list-item-title>
                  <v-list-item-subtitle>Extract audio from episode master video to MP3</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-btn variant="outlined" size="small" color="primary">Open</v-btn>
                  </template>
                </v-list-item>

                <v-divider />

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
                <v-list-item @click="showScriptGeneratorModal = true">
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-script-text</v-icon>
                  </template>
                  <v-list-item-title class="font-weight-bold">Generate Host Script</v-list-item-title>
                  <v-list-item-subtitle>Create formatted HTML script for host/teleprompter</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-btn variant="outlined" size="small" color="primary">Generate</v-btn>
                  </template>
                </v-list-item>

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

          <!-- Production Tools (Disabled - Pending Testing) -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-icon class="me-2" color="grey">mdi-wrench-cog</v-icon>
                <span class="text-h6">Production Tools</span>
                <v-chip size="x-small" color="warning" class="ms-2">Testing</v-chip>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list lines="two">
                <!-- Health Check -->
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-heart-pulse</v-icon>
                  </template>
                  <v-list-item-title>System Health Check</v-list-item-title>
                  <v-list-item-subtitle>Extended diagnostics for database, Redis, Celery, storage, and APIs</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Pending Test</v-chip>
                  </template>
                </v-list-item>

                <v-divider class="my-2" />

                <!-- Asset Validator -->
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-check-decagram</v-icon>
                  </template>
                  <v-list-item-title>Asset Metadata Validator</v-list-item-title>
                  <v-list-item-subtitle>Scan cue blocks for missing fields and invalid values</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Pending Test</v-chip>
                  </template>
                </v-list-item>

                <v-divider class="my-2" />

                <!-- Duration Reconciliation -->
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-timer-sync</v-icon>
                  </template>
                  <v-list-item-title>Duration Reconciliation</v-list-item-title>
                  <v-list-item-subtitle>Compare database durations with actual media file durations</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Pending Test</v-chip>
                  </template>
                </v-list-item>

                <v-divider class="my-2" />

                <!-- Rundown Overview -->
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-compare</v-icon>
                  </template>
                  <v-list-item-title>Rundown Overview</v-list-item-title>
                  <v-list-item-subtitle>View rundown structure, item counts, and summary statistics</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Pending Test</v-chip>
                  </template>
                </v-list-item>

                <v-divider class="my-2" />

                <!-- Production Report -->
                <v-list-item disabled>
                  <template v-slot:prepend>
                    <v-icon>mdi-file-document-outline</v-icon>
                  </template>
                  <v-list-item-title>Production Report</v-list-item-title>
                  <v-list-item-subtitle>Generate comprehensive HTML report for an episode</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-chip size="small" variant="outlined">Pending Test</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>

    <!-- Generate MP3 Modal -->
    <v-dialog v-model="showMp3Modal" max-width="900" persistent>
      <v-card>
        <v-card-title class="d-flex align-center bg-primary text-white">
          <v-icon class="me-2">mdi-music</v-icon>
          Generate MP3 from Episode Video
        </v-card-title>
        <v-card-text class="pa-5">
          <v-row>
            <!-- Left Column: Episode Selection + Source File -->
            <v-col cols="12" md="7">
              <!-- Eligible Episodes Table -->
              <div class="d-flex align-center mb-3">
                <span class="text-subtitle-1 font-weight-bold">Select Episode</span>
                <v-spacer />
                <v-btn
                  size="small"
                  variant="text"
                  prepend-icon="mdi-refresh"
                  :loading="mp3LoadingEligible"
                  @click="loadEligibleEpisodes"
                >
                  Refresh
                </v-btn>
              </div>

              <v-card variant="outlined" class="mb-4">
                <div v-if="mp3LoadingEligible" class="pa-6 text-center">
                  <v-progress-circular indeterminate color="primary" size="24" />
                </div>
                <v-table v-else-if="mp3EligibleEpisodes.length > 0" density="compact" class="mp3-table">
                  <thead>
                    <tr>
                      <th style="width: 30px"></th>
                      <th>Episode</th>
                      <th>Title</th>
                      <th>MP3</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="ep in mp3EligibleEpisodes"
                      :key="ep.episode"
                      :class="{ 'bg-blue-lighten-5': mp3SelectedEpisode === ep.episode }"
                      style="cursor: pointer"
                      @click="selectEpisode(ep)"
                    >
                      <td>
                        <v-radio-group
                          v-model="mp3SelectedEpisode"
                          hide-details
                          density="compact"
                          class="ma-0 pa-0"
                        >
                          <v-radio :value="ep.episode" density="compact" />
                        </v-radio-group>
                      </td>
                      <td class="font-weight-bold">{{ ep.episode }}</td>
                      <td class="text-truncate" style="max-width: 180px">{{ ep.title }}</td>
                      <td>
                        <v-chip
                          v-if="ep.mp3_exists"
                          size="x-small"
                          color="success"
                          variant="flat"
                        >
                          {{ ep.mp3_size_mb }} MB
                        </v-chip>
                        <v-chip v-else size="x-small" color="warning" variant="outlined">
                          None
                        </v-chip>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
                <div v-else class="pa-4 text-center text-grey">
                  No episodes with master video files found
                </div>
              </v-card>

              <!-- Source Video File Selector -->
              <div v-if="mp3SelectedEpisode && selectedEpisodeData">
                <span class="text-subtitle-2 font-weight-bold d-block mb-2">Source Video File</span>
                <v-select
                  v-model="mp3SelectedSourceFile"
                  :items="selectedEpisodeData.candidate_files"
                  item-title="filename"
                  item-value="filename"
                  variant="outlined"
                  density="comfortable"
                  class="mb-1"
                  prepend-inner-icon="mdi-video-outline"
                >
                  <template v-slot:selection="{ item }">
                    <span class="text-body-2">{{ item.raw.filename }}</span>
                    <v-chip size="x-small" class="ml-2" variant="outlined">{{ item.raw.size_mb }} MB</v-chip>
                  </template>
                  <template v-slot:item="{ item, props: itemProps }">
                    <v-list-item v-bind="itemProps">
                      <template v-slot:prepend>
                        <v-icon size="small">mdi-filmstrip</v-icon>
                      </template>
                      <template v-slot:subtitle>
                        {{ item.raw.path }} &mdash; {{ item.raw.size_mb }} MB
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
                <p class="text-caption text-grey-darken-1 mt-n1 mb-3">
                  {{ selectedEpisodeData.exports_path }}/{{ mp3SelectedSourceFile }}
                </p>
              </div>
            </v-col>

            <!-- Right Column: Thumbnail + Profile + Actions -->
            <v-col cols="12" md="5">
              <!-- Thumbnail Placeholder -->
              <span class="text-subtitle-2 font-weight-bold d-block mb-2">Episode Thumbnail</span>
              <v-card variant="outlined" class="mb-4 d-flex align-center justify-center" style="height: 160px; background: #f5f5f5;">
                <div class="text-center text-grey">
                  <v-icon size="48" color="grey-lighten-1">mdi-image-outline</v-icon>
                  <p class="text-caption mt-1">Thumbnail preview<br>(coming soon)</p>
                </div>
              </v-card>

              <!-- Encoding Profile Selector -->
              <span class="text-subtitle-2 font-weight-bold d-block mb-2">Encoding Profile</span>
              <v-select
                v-model="mp3SelectedProfileId"
                :items="mp3Profiles"
                item-title="name"
                item-value="id"
                variant="outlined"
                density="comfortable"
                class="mb-1"
                prepend-inner-icon="mdi-tune-variant"
              >
                <template v-slot:selection="{ item }">
                  <span>{{ item.raw.name }}</span>
                  <v-chip v-if="item.raw.is_default" size="x-small" color="primary" class="ml-2" variant="flat">default</v-chip>
                </template>
                <template v-slot:item="{ item, props: itemProps }">
                  <v-list-item v-bind="itemProps">
                    <template v-slot:prepend>
                      <v-icon size="small" :color="item.raw.is_default ? 'primary' : undefined">
                        {{ item.raw.is_default ? 'mdi-star' : 'mdi-tune-variant' }}
                      </v-icon>
                    </template>
                    <template v-slot:subtitle>
                      {{ item.raw.bitrate }} / {{ item.raw.sample_rate }} Hz / {{ item.raw.channels === 1 ? 'Mono' : 'Stereo' }}
                      {{ item.raw.quality != null ? '(VBR)' : '(CBR)' }}
                    </template>
                  </v-list-item>
                </template>
              </v-select>
              <p v-if="selectedProfileDetail" class="text-caption text-grey-darken-1 mt-n1 mb-3">
                {{ selectedProfileDetail }}
              </p>
            </v-col>
          </v-row>

          <!-- Progress / Status (full width) -->
          <v-alert
            v-if="mp3TaskStatus === 'running'"
            type="info"
            variant="tonal"
            class="mb-2"
          >
            <div class="d-flex align-center">
              <v-progress-circular indeterminate size="20" width="2" class="me-3" />
              <span>Encoding MP3 for episode {{ mp3SelectedEpisode }}...</span>
            </div>
            <v-progress-linear
              v-if="mp3TaskProgress > 0"
              :model-value="mp3TaskProgress"
              color="primary"
              class="mt-2"
              height="6"
              rounded
            />
          </v-alert>

          <v-alert
            v-if="mp3TaskStatus === 'completed'"
            type="success"
            variant="tonal"
            class="mb-2"
          >
            MP3 generated successfully!
            <span v-if="mp3TaskResult">
              {{ mp3TaskResult.file_size_mb }} MB
              ({{ mp3TaskResult.profile }}, {{ mp3TaskResult.bitrate }})
            </span>
          </v-alert>

          <v-alert
            v-if="mp3TaskStatus === 'failed'"
            type="error"
            variant="tonal"
            class="mb-2"
          >
            MP3 generation failed: {{ mp3TaskError }}
          </v-alert>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="closeMp3Modal">Close</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="mp3TaskStatus === 'running'"
            :disabled="!mp3SelectedEpisode || !mp3SelectedProfileId || !mp3SelectedSourceFile || mp3TaskStatus === 'running'"
            @click="startMp3Generation"
          >
            <v-icon class="me-1">mdi-music</v-icon>
            Generate MP3
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Script Generator Modal -->
    <v-dialog v-model="showScriptGeneratorModal" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center bg-primary text-white">
          <v-icon class="me-2">mdi-script-text</v-icon>
          Generate Host Script
        </v-card-title>
        <v-card-text class="pa-4">
          <v-text-field
            v-model="scriptEpisodeNumber"
            label="Episode Number"
            placeholder="e.g., 0249"
            variant="outlined"
            density="comfortable"
            :rules="[v => !!v || 'Episode number is required']"
            class="mb-4"
          />
          <p class="text-body-2 text-grey-darken-1">
            This will generate an HTML script from the episode's rundown data,
            formatted for the host with block headers, cue blocks, and speaker attribution.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showScriptGeneratorModal = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="generatingScript"
            :disabled="!scriptEpisodeNumber"
            @click="generateHostScript"
          >
            Generate Script
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import axios from 'axios'
import EpisodeScaffoldModal from '@/components/EpisodeScaffoldModal.vue'
import EpisodeNameNormalizerModal from '@/components/EpisodeNameNormalizerModal.vue'

const authHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('auth-token')}` }
})

// Reactive data
const showSuccessMessage = ref(false)
const successMessage = ref('')

// Script generator state
const showScriptGeneratorModal = ref(false)
const scriptEpisodeNumber = ref('')
const generatingScript = ref(false)

// ─── MP3 Generation State ────────────────────────────────────
const showMp3Modal = ref(false)
const mp3EligibleEpisodes = ref([])
const mp3LoadingEligible = ref(false)
const mp3Profiles = ref([])
const mp3SelectedEpisode = ref(null)
const mp3SelectedSourceFile = ref(null)
const mp3SelectedProfileId = ref(null)
const mp3TaskId = ref(null)
const mp3TaskStatus = ref(null) // null, 'running', 'completed', 'failed'
const mp3TaskProgress = ref(0)
const mp3TaskResult = ref(null)
const mp3TaskError = ref(null)
let mp3PollTimer = null

// Computed: data object for the currently selected episode
const selectedEpisodeData = computed(() => {
  if (!mp3SelectedEpisode.value) return null
  return mp3EligibleEpisodes.value.find(ep => ep.episode === mp3SelectedEpisode.value) || null
})

// Computed: profile detail text for the selected profile
const selectedProfileDetail = computed(() => {
  if (!mp3SelectedProfileId.value) return null
  const profile = mp3Profiles.value.find(p => p.id === mp3SelectedProfileId.value)
  if (!profile) return null
  const mode = profile.quality != null ? `VBR Q${profile.quality}` : `CBR ${profile.bitrate}`
  const norm = profile.normalize_audio ? ', Loudness Normalized' : ''
  return `${mode}, ${profile.sample_rate} Hz, ${profile.channels === 1 ? 'Mono' : 'Stereo'}${norm}`
})

// Select episode and auto-pick preferred source file
const selectEpisode = (ep) => {
  mp3SelectedEpisode.value = ep.episode
  mp3SelectedSourceFile.value = ep.source_file
}

const loadEligibleEpisodes = async () => {
  mp3LoadingEligible.value = true
  try {
    const response = await axios.get('/api/tools/generate-mp3/eligible', authHeaders())
    mp3EligibleEpisodes.value = response.data.eligible || []
  } catch (error) {
    console.error('Failed to load eligible episodes:', error)
  } finally {
    mp3LoadingEligible.value = false
  }
}

const loadMp3Profiles = async () => {
  try {
    const response = await axios.get('/api/settings/mp3-profiles/', {
      params: { is_active: true },
      ...authHeaders()
    })
    mp3Profiles.value = response.data || []
    // Select default profile
    const defaultProfile = mp3Profiles.value.find(p => p.is_default)
    if (defaultProfile) {
      mp3SelectedProfileId.value = defaultProfile.id
    } else if (mp3Profiles.value.length > 0) {
      mp3SelectedProfileId.value = mp3Profiles.value[0].id
    }
  } catch (error) {
    console.error('Failed to load MP3 profiles:', error)
  }
}

const startMp3Generation = async () => {
  if (!mp3SelectedEpisode.value || !mp3SelectedProfileId.value || !mp3SelectedSourceFile.value) return

  mp3TaskStatus.value = 'running'
  mp3TaskProgress.value = 0
  mp3TaskResult.value = null
  mp3TaskError.value = null

  try {
    const response = await axios.post('/api/tools/generate-mp3', {
      episode: mp3SelectedEpisode.value,
      profile_id: mp3SelectedProfileId.value,
      source_file: mp3SelectedSourceFile.value
    }, authHeaders())
    mp3TaskId.value = response.data.task_id
    startMp3Polling()
  } catch (error) {
    mp3TaskStatus.value = 'failed'
    mp3TaskError.value = error.response?.data?.detail || error.message
  }
}

const startMp3Polling = () => {
  stopMp3Polling()
  mp3PollTimer = setInterval(pollMp3Status, 3000)
}

const stopMp3Polling = () => {
  if (mp3PollTimer) {
    clearInterval(mp3PollTimer)
    mp3PollTimer = null
  }
}

const pollMp3Status = async () => {
  if (!mp3TaskId.value) return

  try {
    const response = await axios.get(`/api/tools/generate-mp3/status/${mp3TaskId.value}`, authHeaders())
    const data = response.data

    if (data.status === 'running' || data.status === 'pending') {
      mp3TaskStatus.value = 'running'
      mp3TaskProgress.value = data.progress || 0
    } else if (data.status === 'completed') {
      mp3TaskStatus.value = 'completed'
      mp3TaskResult.value = data.result
      mp3TaskProgress.value = 100
      stopMp3Polling()
      // Refresh episode list to show updated MP3 status
      loadEligibleEpisodes()
    } else if (data.status === 'failed') {
      mp3TaskStatus.value = 'failed'
      mp3TaskError.value = data.error || 'Unknown error'
      stopMp3Polling()
    }
  } catch (error) {
    console.error('Failed to poll MP3 status:', error)
    mp3TaskStatus.value = 'failed'
    mp3TaskError.value = 'Lost connection to task'
    stopMp3Polling()
  }
}

const closeMp3Modal = () => {
  showMp3Modal.value = false
  stopMp3Polling()
  // Reset status on close only if not running
  if (mp3TaskStatus.value !== 'running') {
    mp3TaskStatus.value = null
    mp3TaskProgress.value = 0
    mp3TaskResult.value = null
    mp3TaskError.value = null
  }
}

// Load data when MP3 modal opens
watch(showMp3Modal, (val) => {
  if (val) {
    loadEligibleEpisodes()
    loadMp3Profiles()
  }
})

onBeforeUnmount(() => {
  stopMp3Polling()
})

// ─── Event Handlers ──────────────────────────────────────────
const handleEpisodeCreated = (episode) => {
  successMessage.value = `Episode ${episode.episode_number} created successfully!`
  showSuccessMessage.value = true
}

// Generate host script
const generateHostScript = async () => {
  if (!scriptEpisodeNumber.value) return

  generatingScript.value = true
  try {
    const response = await axios.post(`/api/scripts/host/${scriptEpisodeNumber.value}`, {}, authHeaders())

    if (response.data.success) {
      successMessage.value = `Host script generated: ${response.data.output_path}`
      showSuccessMessage.value = true
      showScriptGeneratorModal.value = false
      scriptEpisodeNumber.value = ''
    } else {
      successMessage.value = `Error: ${response.data.error}`
      showSuccessMessage.value = true
    }
  } catch (error) {
    console.error('Script generation failed:', error)
    successMessage.value = `Failed to generate script: ${error.response?.data?.detail || error.message}`
    showSuccessMessage.value = true
  } finally {
    generatingScript.value = false
  }
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

.mp3-table {
  max-height: 280px;
  overflow-y: auto;
}
</style>