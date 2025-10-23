<template>
  <v-dialog v-model="dialog" max-width="900px" persistent>
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        variant="outlined"
        size="small"
        color="primary"
        prepend-icon="mdi-folder-edit"
      >
        Normalize Names
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="bg-primary text-white d-flex align-center">
        <v-icon class="me-2">mdi-folder-edit</v-icon>
        <span>Normalize Episode Folder Names</span>
      </v-card-title>

      <v-card-text class="pa-6">
        <v-alert type="info" variant="tonal" class="mb-4">
          <div class="text-body-2">
            This tool fixes episode folder names in Google Drive that have been incorrectly renamed with date suffixes or extra text.
          </div>
          <div class="text-caption mt-2">
            <strong>Example:</strong> "0244.10.12.25" → "0244"
          </div>
        </v-alert>

        <!-- Step 1: Preview (Dry Run) -->
        <div v-if="!previewComplete">
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6 bg-grey-lighten-4">
              Step 1: Preview Changes
            </v-card-title>
            <v-card-text>
              <p class="text-body-2 mb-4">
                First, preview what folders would be renamed without making any actual changes.
              </p>

              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="minEpisode"
                    label="Minimum Episode (Optional)"
                    placeholder="0200"
                    hint="Leave blank to process all"
                    persistent-hint
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="maxEpisode"
                    label="Maximum Episode (Optional)"
                    placeholder="0300"
                    hint="Leave blank to process all"
                    persistent-hint
                    density="comfortable"
                  />
                </v-col>
              </v-row>

              <v-btn
                :loading="loading"
                :disabled="loading"
                color="primary"
                variant="flat"
                prepend-icon="mdi-magnify"
                class="mt-4"
                @click="runPreview"
              >
                Preview Changes
              </v-btn>
            </v-card-text>
          </v-card>
        </div>

        <!-- Preview Results -->
        <div v-if="previewReport && !applyComplete">
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6 bg-grey-lighten-4 d-flex align-center justify-space-between">
              <span>Preview Results</span>
              <v-btn
                size="small"
                variant="text"
                icon="mdi-refresh"
                @click="resetPreview"
              />
            </v-card-title>
            <v-card-text>
              <!-- Summary -->
              <v-row class="mb-4">
                <v-col cols="6" md="3">
                  <v-card variant="tonal" color="success">
                    <v-card-text class="text-center">
                      <div class="text-h4">{{ previewReport.summary.valid }}</div>
                      <div class="text-caption">Valid</div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="6" md="3">
                  <v-card variant="tonal" color="primary">
                    <v-card-text class="text-center">
                      <div class="text-h4">{{ previewReport.summary.renamed }}</div>
                      <div class="text-caption">To Rename</div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="6" md="3">
                  <v-card variant="tonal" color="warning">
                    <v-card-text class="text-center">
                      <div class="text-h4">{{ previewReport.summary.flagged }}</div>
                      <div class="text-caption">Flagged</div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="6" md="3">
                  <v-card variant="tonal" color="error">
                    <v-card-text class="text-center">
                      <div class="text-h4">{{ previewReport.summary.errors }}</div>
                      <div class="text-caption">Errors</div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Folders to Rename -->
              <div v-if="previewReport.report.renamed.length > 0">
                <v-divider class="mb-3" />
                <h4 class="text-subtitle-1 mb-2">📝 Folders to Rename</h4>
                <v-list density="compact" max-height="200" class="overflow-y-auto">
                  <v-list-item
                    v-for="(item, idx) in previewReport.report.renamed"
                    :key="idx"
                    density="compact"
                  >
                    <v-list-item-title class="text-body-2">
                      <span class="text-grey-darken-2">{{ item.current_name }}</span>
                      <v-icon size="x-small" class="mx-2">mdi-arrow-right</v-icon>
                      <span class="text-primary font-weight-bold">{{ item.new_name }}</span>
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </div>

              <!-- Flagged Folders -->
              <div v-if="previewReport.report.flagged.length > 0" class="mt-4">
                <v-divider class="mb-3" />
                <h4 class="text-subtitle-1 mb-2">⚠️ Flagged for Manual Attention</h4>
                <v-list density="compact" max-height="200" class="overflow-y-auto">
                  <v-list-item
                    v-for="(item, idx) in previewReport.report.flagged"
                    :key="idx"
                    density="compact"
                  >
                    <v-list-item-title class="text-body-2 font-weight-bold">
                      {{ item.current_name }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ item.reason }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>
            </v-card-text>
          </v-card>

          <!-- Step 2: Apply Changes -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-h6 bg-grey-lighten-4">
              Step 2: Apply Changes
            </v-card-title>
            <v-card-text>
              <v-alert
                v-if="previewReport.summary.renamed === 0"
                type="success"
                variant="tonal"
                class="mb-4"
              >
                All episode folders are already correctly named!
              </v-alert>
              <div v-else>
                <p class="text-body-2 mb-4">
                  Ready to rename <strong>{{ previewReport.summary.renamed }} folder(s)</strong>?
                </p>
                <v-btn
                  :loading="loading"
                  :disabled="loading || previewReport.summary.renamed === 0"
                  color="success"
                  variant="flat"
                  prepend-icon="mdi-check-circle"
                  @click="applyChanges"
                >
                  Apply Changes
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </div>

        <!-- Apply Results -->
        <div v-if="applyComplete && applyReport">
          <v-alert type="success" variant="tonal" prominent class="mb-4">
            <v-alert-title class="text-h6 mb-2">
              <v-icon class="me-2">mdi-check-circle</v-icon>
              Changes Applied Successfully!
            </v-alert-title>
            <div class="text-body-2">
              Renamed <strong>{{ applyReport.summary.renamed }}</strong> episode folder(s) in Google Drive.
            </div>
          </v-alert>

          <v-btn
            color="primary"
            variant="outlined"
            prepend-icon="mdi-refresh"
            @click="resetAll"
          >
            Run Again
          </v-btn>
        </div>

        <!-- Error Display -->
        <v-alert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          closable
          class="mt-4"
          @click:close="errorMessage = ''"
        >
          {{ errorMessage }}
        </v-alert>
      </v-card-text>

      <v-card-actions class="pa-4 bg-grey-lighten-5">
        <v-spacer />
        <v-btn
          variant="text"
          @click="closeDialog"
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { fetchJson } from '@/utils/apiHelpers'

// Reactive state
const dialog = ref(false)
const loading = ref(false)
const minEpisode = ref('')
const maxEpisode = ref('')
const previewComplete = ref(false)
const applyComplete = ref(false)
const previewReport = ref(null)
const applyReport = ref(null)
const errorMessage = ref('')

// Run preview (dry-run)
async function runPreview() {
  loading.value = true
  errorMessage.value = ''

  try {
    const params = new URLSearchParams({ dry_run: 'true' })
    if (minEpisode.value) params.append('min_episode', minEpisode.value)
    if (maxEpisode.value) params.append('max_episode', maxEpisode.value)

    const data = await fetchJson(`/api/consolidation/normalize-episode-names?${params}`, {
      method: 'POST'
    })

    previewReport.value = data
    previewComplete.value = true
  } catch (error) {
    console.error('Preview failed:', error)
    errorMessage.value = error.message || 'Failed to preview changes'
  } finally {
    loading.value = false
  }
}

// Apply changes (no dry-run)
async function applyChanges() {
  loading.value = true
  errorMessage.value = ''

  try {
    const params = new URLSearchParams({ dry_run: 'false' })
    if (minEpisode.value) params.append('min_episode', minEpisode.value)
    if (maxEpisode.value) params.append('max_episode', maxEpisode.value)

    const data = await fetchJson(`/api/consolidation/normalize-episode-names?${params}`, {
      method: 'POST'
    })

    applyReport.value = data
    applyComplete.value = true
  } catch (error) {
    console.error('Apply failed:', error)
    errorMessage.value = error.message || 'Failed to apply changes'
  } finally {
    loading.value = false
  }
}

// Reset preview
function resetPreview() {
  previewComplete.value = false
  previewReport.value = null
  applyComplete.value = false
  applyReport.value = null
  errorMessage.value = ''
}

// Reset everything
function resetAll() {
  resetPreview()
  minEpisode.value = ''
  maxEpisode.value = ''
}

// Close dialog
function closeDialog() {
  dialog.value = false
  // Reset after animation completes
  setTimeout(resetAll, 300)
}
</script>

<style scoped>
.overflow-y-auto {
  overflow-y: auto;
}
</style>
