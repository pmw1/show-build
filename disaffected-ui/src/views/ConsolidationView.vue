<template>
  <v-container fluid class="pa-0">
    <v-row class="header-row ma-0">
      <v-col cols="12" class="pa-4">
        <h2 class="text-h4 font-weight-bold">Episode Consolidation</h2>
        <p class="text-body-1 text-grey-darken-1 mt-2">
          Consolidate episode media files between Google Drive and Syncthing storage
        </p>
      </v-col>
    </v-row>

    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card>
          <v-card-text>
            <p class="text-body-2 mb-4">
              This tool helps you synchronize episode media files between your Google Drive episode folders
              and local Syncthing episode directories. Select an episode below to begin.
            </p>

            <!-- Episode Selection and Mode Selector -->
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="selectedEpisode"
                  :items="episodes"
                  item-title="display"
                  item-value="episode_number"
                  label="Select Episode"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-television"
                  @update:model-value="loadEpisodeComparison"
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props">
                      <template v-slot:title>
                        <span class="font-weight-medium">{{ item.raw.episode_number }}</span>
                        <span v-if="item.raw.title" class="text-grey ms-2">- {{ item.raw.title }}</span>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
              </v-col>
              <v-col cols="12" md="6" class="d-flex align-center">
                <v-btn-toggle
                  v-model="consolidationMode"
                  color="primary"
                  variant="outlined"
                  divided
                  mandatory
                  @update:model-value="onModeChange"
                >
                  <v-btn value="smart" prepend-icon="mdi-brain">
                    Smart Mode
                  </v-btn>
                  <v-btn value="hard" prepend-icon="mdi-cog">
                    Hard Mode
                  </v-btn>
                </v-btn-toggle>
              </v-col>
            </v-row>

            <!-- Empty Placeholder Panels (shown before episode selection) -->
            <v-row v-if="!selectedEpisode" class="mt-4">
              <v-col cols="12" md="6">
                <v-card class="text-center" min-height="300">
                  <v-card-title class="bg-primary text-white">
                    <v-icon class="me-2">mdi-folder-sync</v-icon>
                    Show Build File System
                  </v-card-title>
                  <v-card-text class="d-flex align-center justify-center" style="min-height: 250px;">
                    <div class="text-grey">
                      <v-icon size="64" color="grey-lighten-1">mdi-folder-outline</v-icon>
                      <p class="text-body-2 mt-4">Select an episode to view file system</p>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="6">
                <v-card class="text-center" min-height="300">
                  <v-card-title class="bg-success text-white">
                    <v-icon class="me-2">mdi-google-drive</v-icon>
                    Google Drive File System
                  </v-card-title>
                  <v-card-text class="d-flex align-center justify-center" style="min-height: 250px;">
                    <div class="text-grey">
                      <v-icon size="64" color="grey-lighten-1">mdi-cloud-outline</v-icon>
                      <p class="text-body-2 mt-4">Select an episode to view file system</p>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Dual Column Comparison View - Always show if episode selected -->
            <v-row v-if="selectedEpisode" class="mt-4">
              <!-- Left Column: Show Build File System -->
              <v-col cols="12" md="6">
                <v-card
                  :style="llmScanning ? getVisualStyle('episode', `episode-${selectedEpisode}-syncthing`) : {}"
                  class="llm-scan-panel"
                  min-height="300"
                >
                  <v-card-title class="bg-primary text-white d-flex align-center">
                    <v-icon class="me-2">mdi-folder-sync</v-icon>
                    <span>Show Build File System</span>
                    <v-spacer></v-spacer>
                    <!-- LLM Prompt Usage Badges -->
                    <div v-if="llmPromptsUsed.length > 0" class="d-flex align-center gap-1 me-2">
                      <v-chip
                        v-for="(prompt, index) in llmPromptsUsed"
                        :key="index"
                        :color="llmScanning && index === llmPromptsUsed.length - 1 ? 'purple' : 'purple-lighten-2'"
                        size="x-small"
                        variant="flat"
                        class="text-white"
                      >
                        <v-icon v-if="llmScanning && index === llmPromptsUsed.length - 1" start size="small">mdi-robot</v-icon>
                        {{ prompt }}
                      </v-chip>
                    </div>
                    <!-- Compliance Status Badge -->
                    <v-chip
                      v-if="validation && !loading"
                      :color="validation.compliant ? 'success' : 'warning'"
                      size="small"
                      variant="flat"
                      class="text-white"
                    >
                      <v-icon start size="small">
                        {{ validation.compliant ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                      </v-icon>
                      {{ validation.compliant ? 'Compliant' : 'Non-Compliant' }}
                    </v-chip>
                  </v-card-title>

                  <!-- Loading State for Show Build -->
                  <v-card-text v-if="loading" class="d-flex align-center justify-center" style="min-height: 250px;">
                    <div class="text-center">
                      <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
                      <p class="text-body-2 text-grey mt-4">Loading Show Build file system...</p>
                    </div>
                  </v-card-text>

                  <!-- Content when loaded -->
                  <template v-else>
                    <!-- LLM Scan Progress Indicator -->
                    <v-slide-y-transition>
                      <v-card-text v-if="llmScanning" class="pa-3 bg-purple-lighten-5 border-b">
                        <div class="d-flex align-center">
                          <v-progress-circular
                            indeterminate
                            color="purple"
                            size="24"
                            width="3"
                            class="me-3"
                          ></v-progress-circular>
                          <div>
                            <div class="text-body-2 font-weight-medium text-purple-darken-2">
                              LLM Analysis in Progress
                            </div>
                            <div class="text-caption text-grey-darken-1">
                              Please stand by, this typically takes a few minutes...
                            </div>
                          </div>
                        </div>
                      </v-card-text>
                    </v-slide-y-transition>

                    <!-- Info Panel -->
                    <v-card-text class="pa-3 bg-grey-lighten-4">
                    <div class="text-caption">
                      <div class="mb-1"><strong>Path:</strong> {{ syncthingPath }}</div>
                      <div class="mb-1"><strong>Total Size:</strong> {{ formatSize(syncthingTotalSize) }}</div>
                      <div><strong>Files:</strong> {{ syncthingFileCount }}</div>
                    </div>
                  </v-card-text>

                  <!-- Validation Details (expandable) -->
                  <v-expansion-panels v-if="validation && !validation.compliant" variant="accordion" class="mb-0">
                    <v-expansion-panel>
                      <v-expansion-panel-title class="text-caption bg-warning-lighten-4">
                        <v-icon start size="small" color="warning">mdi-alert</v-icon>
                        <strong>Structure Issues Found</strong>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div v-if="validation.missing_folders && validation.missing_folders.length > 0" class="mb-3">
                          <div class="text-caption font-weight-bold mb-1">Missing Folders ({{ validation.missing_folders.length }}):</div>
                          <v-chip
                            v-for="folder in validation.missing_folders"
                            :key="folder"
                            size="x-small"
                            color="error"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ folder }}
                          </v-chip>
                        </div>
                        <div v-if="validation.missing_files && validation.missing_files.length > 0" class="mb-3">
                          <div class="text-caption font-weight-bold mb-1">Missing Files ({{ validation.missing_files.length }}):</div>
                          <v-chip
                            v-for="file in validation.missing_files"
                            :key="file"
                            size="x-small"
                            color="error"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ file }}
                          </v-chip>
                        </div>
                        <div v-if="validation.extra_folders && validation.extra_folders.length > 0">
                          <div class="text-caption font-weight-bold mb-1">Extra/Non-Standard Folders ({{ validation.extra_folders.length }}):</div>
                          <v-chip
                            v-for="folder in validation.extra_folders"
                            :key="folder"
                            size="x-small"
                            color="warning"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ folder }}
                          </v-chip>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>

                  <!-- LLM Scan Results (expandable) -->
                  <v-expansion-panels v-if="llmScanResults" variant="accordion" class="mb-0">
                    <v-expansion-panel>
                      <v-expansion-panel-title class="text-caption bg-purple-lighten-5">
                        <v-icon start size="small" color="purple">mdi-robot</v-icon>
                        <strong>LLM Semantic File Classification Results</strong>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <!-- Statistics Summary -->
                        <div class="mb-3 pa-2 bg-grey-lighten-4 rounded">
                          <div class="text-caption mb-2"><strong>Scan Summary</strong></div>
                          <v-row dense>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">Files Scanned</div>
                              <div class="text-body-2 font-weight-bold">{{ llmScanResults.statistics.total_files_scanned }}</div>
                            </v-col>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">Slots Filled</div>
                              <div class="text-body-2 font-weight-bold text-success">
                                {{ llmScanResults.statistics.slots_filled }}/{{ llmScanResults.statistics.total_slots }}
                              </div>
                            </v-col>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">Files Matched</div>
                              <div class="text-body-2 font-weight-bold text-primary">{{ llmScanResults.statistics.files_matched }}</div>
                            </v-col>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">LLM Calls</div>
                              <div class="text-body-2 font-weight-bold text-purple">{{ llmScanResults.statistics.llm_calls_made }}</div>
                            </v-col>
                          </v-row>
                          <div v-if="llmScanResults.json_file" class="mt-2 text-caption text-grey">
                            <strong>Saved to:</strong> {{ llmScanResults.json_file }}
                          </div>
                        </div>

                        <!-- Filled Slots -->
                        <div v-if="llmScanResults.statistics.slots_filled > 0" class="mb-3">
                          <div class="text-caption font-weight-bold mb-2 text-success">
                            ✓ Filled Slots ({{ llmScanResults.statistics.slots_filled }}):
                          </div>
                          <div
                            v-for="(result, slotName) in llmScanResults.slot_results"
                            :key="slotName"
                            class="mb-2"
                          >
                            <div v-if="result.matches && result.matches.length > 0">
                              <div class="text-caption font-weight-bold text-grey-darken-2">{{ slotName }}</div>
                              <div class="text-caption text-grey mb-1">{{ result.reasoning }} (confidence: {{ result.confidence }}%)</div>
                              <v-chip
                                v-for="(match, idx) in result.matches"
                                :key="idx"
                                size="x-small"
                                color="success"
                                variant="outlined"
                                class="ma-1"
                              >
                                {{ match }}
                              </v-chip>
                            </div>
                          </div>
                        </div>

                        <!-- Empty Slots -->
                        <div v-if="llmScanResults.statistics.slots_empty > 0">
                          <div class="text-caption font-weight-bold mb-2 text-grey">
                            ○ Empty Slots ({{ llmScanResults.statistics.slots_empty }}):
                          </div>
                          <v-chip
                            v-for="(result, slotName) in llmScanResults.slot_results"
                            :key="slotName"
                            v-show="!result.matches || result.matches.length === 0"
                            size="x-small"
                            color="grey"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ slotName }}
                          </v-chip>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>

                  <!-- Directory Tree -->
                  <v-card-text class="pa-0">
                    <v-treeview
                      :items="syncthingTree"
                      v-model:opened="openItemsSyncthing"
                      density="compact"
                      item-value="path"
                      open-on-click
                    >
                      <template v-slot:prepend="{ item }">
                        <v-icon v-if="item.type === 'folder'" size="small">
                          mdi-folder
                        </v-icon>
                        <v-icon v-else size="small" :color="getFileIconColor(item.title)">
                          {{ getFileIcon(item.title) }}
                        </v-icon>
                      </template>
                      <template v-slot:append="{ item }">
                        <span v-if="item.type === 'file'" class="text-caption text-grey">
                          {{ formatSize(item.size) }}
                        </span>
                      </template>
                    </v-treeview>
                  </v-card-text>
                  </template>
                </v-card>
              </v-col>

              <!-- Right Column: Google Drive File System -->
              <v-col cols="12" md="6">
                <v-card
                  min-height="300"
                  :style="llmDriveScanning ? getVisualStyle('episode', `episode-${selectedEpisode}-google_drive`) : {}"
                  class="llm-scan-panel"
                >
                  <v-card-title class="bg-success text-white d-flex align-center">
                    <v-icon class="me-2">mdi-google-drive</v-icon>
                    <span>Google Drive File System</span>
                    <v-spacer></v-spacer>
                    <!-- LLM Prompt Usage Badges -->
                    <div v-if="llmDrivePromptsUsed.length > 0" class="d-flex align-center gap-1 me-2">
                      <v-chip
                        v-for="(prompt, index) in llmDrivePromptsUsed"
                        :key="index"
                        :color="llmDriveScanning && index === llmDrivePromptsUsed.length - 1 ? 'purple' : 'purple-lighten-2'"
                        size="x-small"
                        variant="flat"
                        class="text-white"
                      >
                        <v-icon v-if="llmDriveScanning && index === llmDrivePromptsUsed.length - 1" start size="small">mdi-robot</v-icon>
                        {{ prompt }}
                      </v-chip>
                    </div>
                    <!-- Compliance Status Badge -->
                    <v-chip
                      v-if="driveValidation && !loading"
                      :color="driveValidation.compliant ? 'success' : 'warning'"
                      size="small"
                      variant="flat"
                      class="text-white"
                    >
                      <v-icon start size="small">
                        {{ driveValidation.compliant ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                      </v-icon>
                      {{ driveValidation.compliant ? 'Compliant' : 'Non-Compliant' }}
                    </v-chip>
                  </v-card-title>

                  <!-- Loading State for Google Drive -->
                  <v-card-text v-if="loading" class="d-flex align-center justify-center" style="min-height: 250px;">
                    <div class="text-center">
                      <v-progress-circular indeterminate color="success" size="48"></v-progress-circular>
                      <p class="text-body-2 text-grey mt-4">Loading Google Drive file system...</p>
                    </div>
                  </v-card-text>

                  <!-- Content when loaded -->
                  <template v-else>
                    <!-- LLM Scan Progress Indicator -->
                    <v-slide-y-transition>
                      <v-card-text v-if="llmDriveScanning" class="pa-3 bg-purple-lighten-5 border-b">
                        <div class="d-flex align-center">
                          <v-progress-circular
                            indeterminate
                            color="purple"
                            size="24"
                            width="3"
                            class="me-3"
                          ></v-progress-circular>
                          <div>
                            <div class="text-body-2 font-weight-medium text-purple-darken-2">
                              LLM Analysis in Progress
                            </div>
                            <div class="text-caption text-grey-darken-1">
                              Please stand by, this typically takes a few minutes...
                            </div>
                          </div>
                        </div>
                      </v-card-text>
                    </v-slide-y-transition>

                    <!-- Info Panel -->
                    <v-card-text class="pa-3 bg-grey-lighten-4">
                    <div class="text-caption">
                      <div class="mb-1"><strong>Folder ID:</strong> {{ driveFolderId }}</div>
                      <div class="mb-1"><strong>Total Size:</strong> {{ formatSize(driveTotalSize) }}</div>
                      <div><strong>Files:</strong> {{ driveFileCount }}</div>
                    </div>
                  </v-card-text>

                  <!-- Validation Details (expandable) -->
                  <v-expansion-panels v-if="driveValidation && !driveValidation.compliant" variant="accordion" class="mb-0">
                    <v-expansion-panel>
                      <v-expansion-panel-title class="text-caption bg-warning-lighten-4">
                        <v-icon start size="small" color="warning">mdi-alert</v-icon>
                        <strong>Structure Issues Found</strong>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div v-if="driveValidation.missing_folders && driveValidation.missing_folders.length > 0" class="mb-3">
                          <div class="text-caption font-weight-bold mb-1">Missing Folders ({{ driveValidation.missing_folders.length }}):</div>
                          <v-chip
                            v-for="folder in driveValidation.missing_folders"
                            :key="folder"
                            size="x-small"
                            color="error"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ folder }}
                          </v-chip>
                        </div>
                        <div v-if="driveValidation.missing_files && driveValidation.missing_files.length > 0" class="mb-3">
                          <div class="text-caption font-weight-bold mb-1">Missing Files ({{ driveValidation.missing_files.length }}):</div>
                          <v-chip
                            v-for="file in driveValidation.missing_files"
                            :key="file"
                            size="x-small"
                            color="error"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ file }}
                          </v-chip>
                        </div>
                        <div v-if="driveValidation.extra_folders && driveValidation.extra_folders.length > 0">
                          <div class="text-caption font-weight-bold mb-1">Extra/Non-Standard Folders ({{ driveValidation.extra_folders.length }}):</div>
                          <v-chip
                            v-for="folder in driveValidation.extra_folders"
                            :key="folder"
                            size="x-small"
                            color="warning"
                            variant="outlined"
                            class="ma-1"
                          >
                            {{ folder }}
                          </v-chip>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>

                  <!-- LLM Scan Results (expandable) -->
                  <v-expansion-panels v-if="llmDriveScanResults" variant="accordion" class="mb-0">
                    <v-expansion-panel>
                      <v-expansion-panel-title class="text-caption bg-purple-lighten-5">
                        <v-icon start size="small" color="purple">mdi-robot</v-icon>
                        <strong>LLM Semantic File Classification Results (Google Drive)</strong>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <!-- Statistics Summary -->
                        <div class="mb-3 pa-2 bg-grey-lighten-4 rounded">
                          <div class="text-caption mb-2"><strong>Scan Summary</strong></div>
                          <v-row dense>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">Files Scanned</div>
                              <div class="text-body-2 font-weight-bold">{{ llmDriveScanResults.statistics.total_files_scanned }}</div>
                            </v-col>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">Slots Filled</div>
                              <div class="text-body-2 font-weight-bold text-success">
                                {{ llmDriveScanResults.statistics.slots_filled }}/{{ llmDriveScanResults.statistics.total_slots }}
                              </div>
                            </v-col>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">Files Matched</div>
                              <div class="text-body-2 font-weight-bold text-primary">{{ llmDriveScanResults.statistics.files_matched }}</div>
                            </v-col>
                            <v-col cols="6" sm="3">
                              <div class="text-caption text-grey">LLM Calls</div>
                              <div class="text-body-2 font-weight-bold text-purple">{{ llmDriveScanResults.statistics.llm_calls_made }}</div>
                            </v-col>
                          </v-row>
                          <div v-if="llmDriveScanResults.json_file" class="mt-2 text-caption text-grey">
                            <strong>Saved to:</strong> {{ llmDriveScanResults.json_file }}
                          </div>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>

                  <!-- Directory Tree -->
                  <v-card-text class="pa-0">
                    <v-treeview
                      :items="driveTree"
                      v-model:opened="openItemsDrive"
                      density="compact"
                      item-value="id"
                      open-on-click
                    >
                      <template v-slot:prepend="{ item }">
                        <v-icon v-if="item.type === 'folder'" size="small">
                          mdi-folder
                        </v-icon>
                        <v-icon v-else size="small" :color="getFileIconColor(item.title)">
                          {{ getFileIcon(item.title) }}
                        </v-icon>
                      </template>
                      <template v-slot:append="{ item }">
                        <span v-if="item.type === 'file'" class="text-caption text-grey">
                          {{ formatSize(item.size) }}
                        </span>
                      </template>
                    </v-treeview>
                  </v-card-text>
                  </template>
                </v-card>
              </v-col>
            </v-row>

            <!-- Hard Mode: Transfer List -->
            <v-row v-if="consolidationMode === 'hard' && missingFilesInShowBuild.length > 0" class="mt-4">
              <v-col cols="12">
                <v-card>
                  <v-card-title class="bg-warning text-white d-flex align-center">
                    <v-icon class="me-2">mdi-file-move</v-icon>
                    <span>Files to Transfer from Google Drive to Show Build</span>
                    <v-spacer></v-spacer>
                    <v-chip color="white" text-color="warning" size="small">
                      {{ missingFilesInShowBuild.length }} files
                    </v-chip>
                  </v-card-title>
                  <v-card-text class="pa-0">
                    <v-list density="compact">
                      <v-list-item
                        v-for="(file, index) in missingFilesInShowBuild"
                        :key="index"
                        class="border-b"
                      >
                        <template v-slot:prepend>
                          <v-icon :color="getFileIconColor(file.name)">
                            {{ getFileIcon(file.name) }}
                          </v-icon>
                        </template>
                        <v-list-item-title>
                          <span class="font-weight-medium">{{ file.name }}</span>
                        </v-list-item-title>
                        <v-list-item-subtitle class="text-caption">
                          {{ file.path }}
                        </v-list-item-subtitle>
                        <template v-slot:append>
                          <span class="text-caption text-grey me-4">
                            {{ formatSize(file.size) }}
                          </span>
                          <v-btn
                            icon="mdi-download"
                            size="small"
                            variant="text"
                            color="primary"
                            @click="transferFile(file)"
                          >
                          </v-btn>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                  <v-card-actions class="pa-4">
                    <v-btn
                      color="primary"
                      variant="elevated"
                      prepend-icon="mdi-download-multiple"
                      @click="transferAllFiles"
                    >
                      Transfer All Files
                    </v-btn>
                    <v-spacer></v-spacer>
                    <v-btn
                      color="grey"
                      variant="text"
                      @click="missingFilesInShowBuild = []"
                    >
                      Clear List
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>

          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLLMState } from '@/composables/useLLMState'
import { useStandardNotification, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { fetchJson } from '@/utils/apiHelpers'

const { notifyUserStandard } = useStandardNotification()
const { startOperation, stopOperation, failOperation, getVisualStyle, STATE } = useLLMState()

const selectedEpisode = ref(null)
const episodes = ref([])
const loading = ref(false)
const comparisonData = ref(null)
const consolidationMode = ref('smart') // 'smart' or 'hard'

// Hard mode - file transfer list
const missingFilesInShowBuild = ref([]) // Files in Google Drive but not in Show Build

// Syncthing (Show Build) data
const syncthingTree = ref([])
const syncthingTotalSize = ref(0)
const syncthingFileCount = ref(0)
const validation = ref(null)
const openItemsSyncthing = ref(['exports']) // Only exports folder expanded by default

// Google Drive data
const driveTree = ref([])
const driveTotalSize = ref(0)
const driveFileCount = ref(0)
const driveValidation = ref(null)
const openItemsDrive = ref(['exports']) // Only exports folder expanded by default

// LLM Inventory Scanner state
const llmScanning = ref(false)
const llmScanResults = ref(null)
const llmOperationId = ref(null)
const llmPromptsUsed = ref([]) // Track prompts used during scanning
const llmDriveScanning = ref(false)
const llmDriveScanResults = ref(null)
const llmDriveOperationId = ref(null)
const llmDrivePromptsUsed = ref([]) // Track prompts used during Google Drive scanning

// Computed paths
const syncthingPath = computed(() => {
  return selectedEpisode.value ? `/mnt/sync/disaffected/episodes/${selectedEpisode.value}/` : ''
})

const driveFolderId = computed(() => {
  return comparisonData.value?.drive_folder_id || 'Not configured'
})

onMounted(async () => {
  await loadEpisodes()
})

// Show an error notification. The old backend POST /api/llm/notifications was
// removed (dead endpoint — llm_state_router retired 2026-06-04); surface the
// error via the standard toast instead.
function sendErrorNotification(title, message, operationId = null) {
  void operationId
  try {
    notifyUserStandard(`${title}<small>${message}</small>`, NOTIFICATION_COLORS.ERROR, 6000)
  } catch (error) {
    console.error('Failed to show error notification:', error)
  }
}

// Handle mode change
async function onModeChange(newMode) {
  if (newMode === 'hard') {
    notifyUserStandard('Switching to Hard Mode', 'info', NOTIFICATION_COLORS.INFO)

    // Trigger 1:1 file comparison if episode is selected
    if (selectedEpisode.value && comparisonData.value) {
      await performHardModeComparison()
    }
  } else {
    notifyUserStandard('Switching to Smart Mode', 'info', NOTIFICATION_COLORS.INFO)
    missingFilesInShowBuild.value = [] // Clear transfer list
  }
}

// Perform 1:1 file comparison for Hard Mode
async function performHardModeComparison() {
  try {
    loading.value = true
    missingFilesInShowBuild.value = []

    // Get flat list of all files from both trees
    const syncthingFiles = flattenFileTree(syncthingTree.value)
    const driveFiles = flattenFileTree(driveTree.value)

    // Find files in Google Drive that are NOT in Show Build
    const syncthingFilePaths = new Set(syncthingFiles.map(f => f.path))

    driveFiles.forEach(driveFile => {
      if (!syncthingFilePaths.has(driveFile.path)) {
        missingFilesInShowBuild.value.push({
          name: driveFile.name,
          path: driveFile.path,
          size: driveFile.size,
          type: driveFile.type
        })
      }
    })

    notifyUserStandard(
      `Found ${missingFilesInShowBuild.value.length} files in Google Drive not present in Show Build`,
      'success',
      NOTIFICATION_COLORS.SUCCESS
    )
  } catch (error) {
    console.error('Hard mode comparison failed:', error)
    notifyUserStandard('Failed to perform hard mode comparison', 'error', NOTIFICATION_COLORS.ERROR)
  } finally {
    loading.value = false
  }
}

// Helper function to flatten tree structure into flat file list
function flattenFileTree(tree, parentPath = '') {
  const files = []

  tree.forEach(item => {
    const currentPath = parentPath ? `${parentPath}/${item.name}` : item.name

    if (item.type === 'file') {
      files.push({
        name: item.name,
        path: currentPath,
        size: item.size || 0,
        type: 'file'
      })
    } else if (item.children) {
      // Recursively process children
      files.push(...flattenFileTree(item.children, currentPath))
    }
  })

  return files
}

// Transfer a single file from Google Drive to Show Build
async function transferFile(file) {
  try {
    notifyUserStandard(`Transferring ${file.name}...`, 'info', NOTIFICATION_COLORS.INFO)

    // TODO: Implement file transfer API call
    // This would call an endpoint to download from Google Drive and upload to Show Build

    notifyUserStandard(`Successfully transferred ${file.name}`, 'success', NOTIFICATION_COLORS.SUCCESS)

    // Remove from missing files list
    missingFilesInShowBuild.value = missingFilesInShowBuild.value.filter(f => f.path !== file.path)
  } catch (error) {
    console.error('File transfer failed:', error)
    notifyUserStandard(`Failed to transfer ${file.name}`, 'error', NOTIFICATION_COLORS.ERROR)
  }
}

// Transfer all files from Google Drive to Show Build
async function transferAllFiles() {
  try {
    notifyUserStandard(`Starting batch transfer of ${missingFilesInShowBuild.value.length} files...`, 'info', NOTIFICATION_COLORS.INFO)

    // TODO: Implement batch file transfer API call

    notifyUserStandard('All files transferred successfully', 'success', NOTIFICATION_COLORS.SUCCESS)
    missingFilesInShowBuild.value = []
  } catch (error) {
    console.error('Batch transfer failed:', error)
    notifyUserStandard('Failed to transfer all files', 'error', NOTIFICATION_COLORS.ERROR)
  }
}

async function loadEpisodes() {
  try {
    const data = await fetchJson('/api/episodes')
    // API returns { episodes: [...] }
    const episodesList = data.episodes || data
    episodes.value = episodesList.map(ep => ({
      episode_number: ep.episode_number,
      title: ep.title,
      display: `${ep.episode_number}${ep.title ? ' - ' + ep.title : ''}`
    }))
    console.log('Loaded episodes:', episodes.value)
  } catch (error) {
    console.error('Error loading episodes:', error)
  }
}

async function loadEpisodeComparison(episodeNumber) {
  if (!episodeNumber) return

  loading.value = true
  // Reset LLM scan state
  llmScanResults.value = null
  llmScanning.value = false
  llmDriveScanResults.value = null
  llmDriveScanning.value = false

  // Show initial loading notification
  notifyUserStandard(`Loading file systems for episode ${episodeNumber}...`, NOTIFICATION_COLORS.INFO, 6000)

  try {
    // Call backend API to get directory trees
    const data = await fetchJson(`/api/consolidation/compare/${episodeNumber}`)

    comparisonData.value = data

    // Load Syncthing tree
    syncthingTree.value = data.syncthing_tree || []
    syncthingTotalSize.value = data.syncthing_total_size || 0
    syncthingFileCount.value = data.syncthing_file_count || 0
    validation.value = data.syncthing_validation || null

    // Load Google Drive tree
    driveTree.value = data.drive_tree || []
    driveTotalSize.value = data.drive_total_size || 0
    driveFileCount.value = data.drive_file_count || 0
    driveValidation.value = data.drive_validation || null

    // Set opened folders - only exports folder should be expanded
    openItemsSyncthing.value = ['exports']
    // Find exports folder in Drive tree and get its ID
    const driveExportsFolder = driveTree.value.find(item => item.title === 'exports')
    openItemsDrive.value = driveExportsFolder ? [driveExportsFolder.id] : []

    // Stop loading state BEFORE LLM scans
    loading.value = false

    // Show success notification for file system loading
    notifyUserStandard(`File systems loaded: ${syncthingFileCount.value} files (Show Build), ${driveFileCount.value} files (Google Drive)`, NOTIFICATION_COLORS.SUCCESS, 6000)

    // Wait for success toast to be visible before showing next message
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Announce LLM scan will begin in 5 seconds
    notifyUserStandard('LLM semantic file classification will begin in 5 seconds...', NOTIFICATION_COLORS.INFO, 5000)

    // Wait 5 seconds before starting LLM scans
    await new Promise(resolve => setTimeout(resolve, 5000))

    // Trigger LLM scans after both file systems loaded and visible
    await runLLMInventoryScan(episodeNumber, 'syncthing')

    // Only scan Google Drive if folder was found
    if (data.drive_folder_id && data.drive_folder_id !== 'Not found') {
      await runLLMInventoryScan(episodeNumber, 'google_drive')
    } else {
      notifyUserStandard(`Skipping Google Drive LLM scan - episode ${episodeNumber} not found in Google Drive`, NOTIFICATION_COLORS.WARNING, 5000)
    }
  } catch (error) {
    console.error('Error loading episode comparison:', error)
    const errorMsg = `Error loading file systems: ${error.message}`
    notifyUserStandard(errorMsg, NOTIFICATION_COLORS.ERROR, 6000)
    await sendErrorNotification('File System Load Error', errorMsg)
    loading.value = false
    // Show placeholder data for development
    await loadPlaceholderData(episodeNumber)
  }
}

async function runLLMInventoryScan(episodeNumber, sourceSystem = 'syncthing') {
  const isGoogleDrive = sourceSystem === 'google_drive'
  const systemName = isGoogleDrive ? 'Google Drive' : 'Show Build'

  try {
    // Determine which state variables to use
    const scanningRef = isGoogleDrive ? llmDriveScanning : llmScanning
    const resultsRef = isGoogleDrive ? llmDriveScanResults : llmScanResults
    const operationIdRef = isGoogleDrive ? llmDriveOperationId : llmOperationId
    const promptsUsedRef = isGoogleDrive ? llmDrivePromptsUsed : llmPromptsUsed

    // Clear previous prompts and add the batch matcher prompt
    promptsUsedRef.value = ['batch-match-slots']

    // Start LLM operation with visual feedback
    operationIdRef.value = startOperation(
      'episode',
      `episode-${episodeNumber}-${sourceSystem}`,
      'analyzing',
      {
        state: STATE.ANALYZING,
        model: 'Ollama/OpenAI',
        message: `LLM attempting to classify expected files in ${systemName}...`,
        notify: false, // We'll show custom toast
        metadata: {
          component: 'ConsolidationView',
          episodeNumber,
          sourceSystem
        }
      }
    )

    scanningRef.value = true

    // Show toast notification - long duration to cover entire LLM operation (9 batches can take 1-2 minutes)
    notifyUserStandard(`LLM attempting to classify expected files in ${systemName} filesystem`, NOTIFICATION_COLORS.INFO, 180000)

    // Call batched LLM inventory scanner (3 slots per batch per LLM consultation)
    const data = await fetchJson(`/api/inventory/scan-batched/${episodeNumber}?batch_size=3&source_system=${sourceSystem}`, {
      method: 'POST'
    })

    resultsRef.value = data

    // Check if the scan was successful or just a placeholder
    if (data.success === false) {
      // Feature not implemented yet (like Google Drive scanning)
      stopOperation(operationIdRef.value, {
        success: false,
        notify: false,
        message: data.message
      })
      notifyUserStandard(`${systemName}: ${data.message}`, NOTIFICATION_COLORS.WARNING, 5000)
      // Send persistent notification for failures
      await sendErrorNotification(`${systemName} LLM Scan Failed`, data.message, operationIdRef.value)
    } else {
      // Successful scan
      stopOperation(operationIdRef.value, {
        success: true,
        notify: false, // We'll show custom toast
        message: `LLM scan complete: ${data.statistics.slots_filled}/${data.statistics.total_slots} slots filled`
      })

      // Show success notification with file paths
      const jsonFile = data.json_file ? ` → Saved to ${data.json_file}` : ''
      notifyUserStandard(`${systemName} LLM scan complete: Found ${data.statistics.files_matched} files in ${data.statistics.slots_filled} slots (${data.statistics.llm_calls_made} LLM calls)${jsonFile}`, NOTIFICATION_COLORS.SUCCESS, 5000)
    }
  } catch (error) {
    console.error(`LLM inventory scan failed for ${systemName}:`, error)

    const operationIdRef = isGoogleDrive ? llmDriveOperationId : llmOperationId
    if (operationIdRef.value) {
      failOperation(operationIdRef.value, error)
    }

    const errorMsg = `${systemName} LLM scan failed: ${error.message}`
    notifyUserStandard(errorMsg, NOTIFICATION_COLORS.ERROR, 6000)
    await sendErrorNotification(`${systemName} LLM Scan Failed`, errorMsg, operationIdRef.value)
  } finally {
    const scanningRef = isGoogleDrive ? llmDriveScanning : llmScanning
    scanningRef.value = false
  }
}

// Placeholder data while backend is being implemented
async function loadPlaceholderData(episodeNumber) {
  comparisonData.value = {
    episode: episodeNumber,
    syncthing_path: `/mnt/sync/disaffected/episodes/${episodeNumber}/`,
    drive_folder_id: 'Pending configuration'
  }

  // Mock Syncthing tree
  syncthingTree.value = [
    {
      title: 'assets',
      type: 'folder',
      path: 'assets',
      children: [
        { title: 'video', type: 'folder', path: 'assets/video', children: [] },
        { title: 'images', type: 'folder', path: 'assets/images', children: [] },
        { title: 'audio', type: 'folder', path: 'assets/audio', children: [] }
      ]
    },
    {
      title: 'scripts',
      type: 'folder',
      path: 'scripts',
      children: []
    },
    { title: 'info.md', type: 'file', path: 'info.md', size: 2048 }
  ]
  syncthingTotalSize.value = 157286400 // ~150MB
  syncthingFileCount.value = 23

  // Mock Google Drive tree
  driveTree.value = [
    {
      title: 'assets',
      type: 'folder',
      id: 'folder_1',
      children: [
        { title: 'video', type: 'folder', id: 'folder_2', children: [] },
        { title: 'images', type: 'folder', id: 'folder_3', children: [] }
      ]
    },
    { title: 'info.md', type: 'file', id: 'file_1', size: 2048 }
  ]
  driveTotalSize.value = 104857600 // ~100MB
  driveFileCount.value = 15
}

// Helper functions
function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function getFileIcon(filename) {
  if (!filename) return 'mdi-file'
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    md: 'mdi-file-document',
    mp4: 'mdi-video',
    mov: 'mdi-video',
    mp3: 'mdi-music',
    wav: 'mdi-music',
    jpg: 'mdi-image',
    jpeg: 'mdi-image',
    png: 'mdi-image',
    pdf: 'mdi-file-pdf-box',
    json: 'mdi-code-json'
  }
  return iconMap[ext] || 'mdi-file'
}

function getFileIconColor(filename) {
  if (!filename) return 'grey'
  const ext = filename.split('.').pop()?.toLowerCase()
  const colorMap = {
    mp4: 'purple',
    mov: 'purple',
    mp3: 'blue',
    wav: 'blue',
    jpg: 'green',
    jpeg: 'green',
    png: 'green'
  }
  return colorMap[ext] || 'grey'
}
</script>

<style scoped>
.header-row {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(25, 118, 210, 0.05) 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.llm-scan-panel {
  transition: all 0.3s ease-in-out;
}

/* LLM Analysis animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>
