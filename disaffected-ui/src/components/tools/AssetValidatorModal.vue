<template>
  <v-dialog v-model="dialogOpen" max-width="700" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" size="small" color="primary" v-bind="props">
        Validate
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center bg-primary text-white">
        <v-icon class="me-2">mdi-check-decagram</v-icon>
        Asset Metadata Validator
      </v-card-title>

      <v-card-text class="pa-4" style="max-height: 600px;">
        <!-- Configuration -->
        <v-text-field
          v-model="episodeNumber"
          label="Episode Number (optional)"
          placeholder="e.g., 0249 or leave empty for all"
          variant="outlined"
          density="comfortable"
          hint="Leave empty to validate all episodes"
          persistent-hint
          class="mb-4"
          :disabled="isRunning"
        />

        <!-- Progress -->
        <div v-if="isRunning" class="mb-4">
          <v-progress-linear
            :model-value="progress"
            color="primary"
            height="8"
            rounded
          />
          <p class="text-caption text-center mt-2">
            Validating... {{ progress }}%
          </p>
        </div>

        <!-- Results -->
        <div v-if="result && !isRunning">
          <v-alert
            :type="result.summary?.items_with_issues > 0 ? 'warning' : 'success'"
            variant="tonal"
            class="mb-4"
          >
            <strong>Validation Complete</strong>
            <div class="mt-1">
              Scanned {{ result.summary?.total_items_scanned || 0 }} items,
              found {{ result.summary?.items_with_issues || 0 }} with issues
            </div>
          </v-alert>

          <!-- Summary -->
          <v-row class="mb-4">
            <v-col cols="4">
              <div class="text-center">
                <div class="text-h4">{{ result.summary?.missing_asset_ids || 0 }}</div>
                <div class="text-caption text-grey">Missing AssetIDs</div>
              </div>
            </v-col>
            <v-col cols="4">
              <div class="text-center">
                <div class="text-h4">{{ result.summary?.missing_durations || 0 }}</div>
                <div class="text-caption text-grey">Missing Durations</div>
              </div>
            </v-col>
            <v-col cols="4">
              <div class="text-center">
                <div class="text-h4">{{ result.summary?.invalid_cue_blocks || 0 }}</div>
                <div class="text-caption text-grey">Invalid Cue Blocks</div>
              </div>
            </v-col>
          </v-row>

          <!-- Issues List -->
          <v-expansion-panels v-if="result.issues?.length" variant="accordion">
            <v-expansion-panel
              v-for="item in result.issues"
              :key="item.item_id"
            >
              <v-expansion-panel-title>
                <v-icon class="me-2" color="warning">mdi-alert-circle</v-icon>
                <span class="font-weight-medium">{{ item.slug || item.title }}</span>
                <v-chip size="x-small" class="ms-2">
                  {{ item.issues.length }} issue{{ item.issues.length > 1 ? 's' : '' }}
                </v-chip>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item v-for="(issue, idx) in item.issues" :key="idx">
                    <template v-slot:prepend>
                      <v-icon
                        :color="getSeverityColor(issue.severity)"
                        size="small"
                      >
                        {{ getSeverityIcon(issue.severity) }}
                      </v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ formatIssue(issue) }}
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <v-alert v-else type="success" variant="tonal">
            No issues found! All metadata looks good.
          </v-alert>
        </div>

        <!-- Error -->
        <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
          {{ error }}
        </v-alert>

        <!-- Initial State -->
        <div v-if="!result && !isRunning && !error" class="text-center py-8">
          <v-icon size="64" color="grey">mdi-check-decagram</v-icon>
          <p class="mt-4 text-body-1 text-grey">
            Validates cue blocks for missing fields and invalid values
          </p>
        </div>
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="dialogOpen = false">Close</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="isRunning"
          @click="runValidation"
        >
          <v-icon class="me-1">mdi-play</v-icon>
          Run Validation
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useToolsRunner } from '@/composables/useToolsRunner'

const { isRunning, progress, result, error, runMetadataValidation, reset } = useToolsRunner()

const dialogOpen = ref(false)
const episodeNumber = ref('')

const runValidation = async () => {
  reset()
  try {
    await runMetadataValidation(episodeNumber.value || null)
  } catch (err) {
    console.error('Validation failed:', err)
  }
}

const getSeverityColor = (severity) => {
  switch (severity) {
    case 'error': return 'error'
    case 'warning': return 'warning'
    case 'info': return 'info'
    default: return 'grey'
  }
}

const getSeverityIcon = (severity) => {
  switch (severity) {
    case 'error': return 'mdi-alert-circle'
    case 'warning': return 'mdi-alert'
    case 'info': return 'mdi-information'
    default: return 'mdi-help-circle'
  }
}

const formatIssue = (issue) => {
  const field = issue.field.replace(/_/g, ' ').replace(/cue block \d+/, 'Cue block')
  return `${field}: ${issue.issue.replace(/_/g, ' ')}`
}
</script>
