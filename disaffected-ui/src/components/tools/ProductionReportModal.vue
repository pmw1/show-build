<template>
  <v-dialog v-model="dialogOpen" max-width="600" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" size="small" color="primary" v-bind="props">
        Generate
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center bg-primary text-white">
        <v-icon class="me-2">mdi-file-document-outline</v-icon>
        Generate Production Report
      </v-card-title>

      <v-card-text class="pa-4">
        <!-- Configuration -->
        <v-text-field
          v-model="episodeNumber"
          label="Episode Number"
          placeholder="e.g., 0249"
          variant="outlined"
          density="comfortable"
          :rules="[v => !!v || 'Episode number is required']"
          class="mb-4"
          :disabled="isRunning"
        />

        <!-- Options -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-2 py-2">Report Options</v-card-title>
          <v-card-text class="py-2">
            <v-checkbox
              v-model="options.includeAssets"
              label="Include asset inventory"
              density="compact"
              hide-details
              :disabled="isRunning"
            />
            <v-checkbox
              v-model="options.includeScripts"
              label="Include script status"
              density="compact"
              hide-details
              :disabled="isRunning"
            />
            <v-checkbox
              v-model="options.includeTimeline"
              label="Include timeline"
              density="compact"
              hide-details
              :disabled="isRunning"
            />
          </v-card-text>
        </v-card>

        <!-- Progress -->
        <div v-if="isRunning" class="mb-4">
          <v-progress-linear
            :model-value="progress"
            color="primary"
            height="8"
            rounded
          />
          <p class="text-caption text-center mt-2">
            Generating report... {{ progress }}%
          </p>
        </div>

        <!-- Result -->
        <div v-if="result && !isRunning">
          <v-alert type="success" variant="tonal" class="mb-4">
            <strong>Report Generated Successfully!</strong>
          </v-alert>

          <!-- Summary -->
          <v-card variant="outlined" class="mb-4">
            <v-card-text>
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2">Total Items:</span>
                <span class="font-weight-medium">{{ result.summary?.by_type ? Object.values(result.summary.by_type).reduce((a, b) => a + b, 0) : 0 }}</span>
              </div>
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2">Scripts Complete:</span>
                <span class="font-weight-medium">{{ result.summary?.scripts_complete || 0 }}</span>
              </div>
              <div class="d-flex justify-space-between align-center">
                <span class="text-body-2">Total Duration:</span>
                <span class="font-weight-medium">{{ result.summary?.total_duration || '00:00:00' }}</span>
              </div>
            </v-card-text>
          </v-card>

          <!-- Download Button -->
          <v-btn
            color="success"
            variant="flat"
            block
            :href="getDownloadUrl()"
            target="_blank"
          >
            <v-icon class="me-2">mdi-download</v-icon>
            Open Report
          </v-btn>
        </div>

        <!-- Error -->
        <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
          {{ error }}
        </v-alert>

        <!-- Initial State -->
        <div v-if="!result && !isRunning && !error" class="text-center py-4">
          <v-icon size="48" color="grey">mdi-file-document-outline</v-icon>
          <p class="mt-2 text-body-2 text-grey">
            Generates an HTML report with episode overview, rundown status, and asset inventory
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
          :disabled="!episodeNumber"
          @click="generateReport"
        >
          <v-icon class="me-1">mdi-play</v-icon>
          Generate Report
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, inject } from 'vue'
import { useToolsRunner } from '@/composables/useToolsRunner'

const { isRunning, progress, result, error, generateProductionReport, reset } = useToolsRunner()

// Inject API base URL
const apiBaseUrl = inject('apiBaseUrl', 'https://192.168.51.210:8888')

const dialogOpen = ref(false)
const episodeNumber = ref('')
const options = reactive({
  includeAssets: true,
  includeScripts: true,
  includeTimeline: true
})

const generateReport = async () => {
  if (!episodeNumber.value) return
  reset()
  try {
    await generateProductionReport(episodeNumber.value, options)
  } catch (err) {
    console.error('Report generation failed:', err)
  }
}

const getDownloadUrl = () => {
  if (!result.value?.download_url) return '#'
  // Construct full URL using the API base
  return `${apiBaseUrl}${result.value.download_url}`
}
</script>
