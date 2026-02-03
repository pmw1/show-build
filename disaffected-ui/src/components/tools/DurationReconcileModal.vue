<template>
  <v-dialog v-model="dialogOpen" max-width="800" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" size="small" color="primary" v-bind="props">
        Reconcile
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center bg-primary text-white">
        <v-icon class="me-2">mdi-timer-sync</v-icon>
        Duration Reconciliation
      </v-card-title>

      <v-card-text class="pa-4" style="max-height: 600px;">
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

        <!-- Progress -->
        <div v-if="isRunning" class="mb-4">
          <v-progress-linear
            :model-value="progress"
            color="primary"
            height="8"
            rounded
          />
          <p class="text-caption text-center mt-2">
            Analyzing media files... {{ progress }}%
          </p>
        </div>

        <!-- Results -->
        <div v-if="result && !isRunning">
          <v-alert
            :type="result.summary?.mismatches_found > 0 ? 'warning' : 'success'"
            variant="tonal"
            class="mb-4"
          >
            <strong>Reconciliation Complete</strong>
            <div class="mt-1">
              Found {{ result.summary?.mismatches_found || 0 }} duration mismatches
              out of {{ result.summary?.items_with_media || 0 }} media files
            </div>
          </v-alert>

          <!-- Summary Stats -->
          <v-row class="mb-4">
            <v-col cols="3">
              <div class="text-center">
                <div class="text-h4">{{ result.summary?.total_items || 0 }}</div>
                <div class="text-caption text-grey">Total Items</div>
              </div>
            </v-col>
            <v-col cols="3">
              <div class="text-center">
                <div class="text-h4">{{ result.summary?.items_with_media || 0 }}</div>
                <div class="text-caption text-grey">With Media</div>
              </div>
            </v-col>
            <v-col cols="3">
              <div class="text-center">
                <div class="text-h4 text-warning">{{ result.summary?.mismatches_found || 0 }}</div>
                <div class="text-caption text-grey">Mismatches</div>
              </div>
            </v-col>
            <v-col cols="3">
              <div class="text-center">
                <div class="text-h4 text-error">{{ result.summary?.files_not_found || 0 }}</div>
                <div class="text-caption text-grey">Missing Files</div>
              </div>
            </v-col>
          </v-row>

          <!-- Mismatches Table -->
          <v-card v-if="result.mismatches?.length" variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="me-2" color="warning">mdi-alert</v-icon>
              Duration Mismatches
            </v-card-title>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Slug</th>
                  <th>Stored</th>
                  <th>Actual</th>
                  <th>Diff</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="mismatch in result.mismatches" :key="mismatch.item_id">
                  <td>
                    <span class="font-weight-medium">{{ mismatch.slug }}</span>
                    <div class="text-caption text-grey">{{ mismatch.asset_id }}</div>
                  </td>
                  <td>{{ mismatch.stored_duration }}</td>
                  <td class="text-success">{{ mismatch.actual_duration }}</td>
                  <td>
                    <v-chip
                      :color="Math.abs(mismatch.difference_seconds) > 5 ? 'error' : 'warning'"
                      size="x-small"
                    >
                      {{ formatDiff(mismatch.difference_seconds) }}
                    </v-chip>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card>

          <!-- Missing Files -->
          <v-expansion-panels v-if="result.missing_files?.length" variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon class="me-2" color="error">mdi-file-alert</v-icon>
                Missing Media Files ({{ result.missing_files.length }})
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="file in result.missing_files"
                    :key="file.item_id"
                  >
                    <v-list-item-title>{{ file.slug }}</v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ file.asset_id }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <v-alert v-if="!result.mismatches?.length && !result.missing_files?.length" type="success" variant="tonal">
            All durations match! No issues found.
          </v-alert>
        </div>

        <!-- Error -->
        <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
          {{ error }}
        </v-alert>

        <!-- Initial State -->
        <div v-if="!result && !isRunning && !error" class="text-center py-8">
          <v-icon size="64" color="grey">mdi-timer-sync</v-icon>
          <p class="mt-4 text-body-1 text-grey">
            Compares database durations with actual media file durations using ffprobe
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
          @click="runReconciliation"
        >
          <v-icon class="me-1">mdi-play</v-icon>
          Run Reconciliation
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useToolsRunner } from '@/composables/useToolsRunner'

const { isRunning, progress, result, error, runDurationReconciliation, reset } = useToolsRunner()

const dialogOpen = ref(false)
const episodeNumber = ref('')

const runReconciliation = async () => {
  if (!episodeNumber.value) return
  reset()
  try {
    await runDurationReconciliation(episodeNumber.value)
  } catch (err) {
    console.error('Reconciliation failed:', err)
  }
}

const formatDiff = (seconds) => {
  const sign = seconds >= 0 ? '+' : ''
  return `${sign}${seconds.toFixed(1)}s`
}
</script>
