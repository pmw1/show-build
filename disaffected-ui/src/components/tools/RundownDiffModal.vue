<template>
  <v-dialog v-model="dialogOpen" max-width="700" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" size="small" color="primary" v-bind="props">
        View Diff
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center bg-primary text-white">
        <v-icon class="me-2">mdi-compare</v-icon>
        Rundown Overview
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

        <!-- Loading -->
        <div v-if="isRunning" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4 text-body-1">Loading rundown...</p>
        </div>

        <!-- Results -->
        <div v-if="result && !isRunning">
          <!-- Summary Cards -->
          <v-row class="mb-4">
            <v-col cols="3">
              <v-card variant="outlined" class="text-center pa-2">
                <div class="text-h5">{{ result.summary?.total_items || 0 }}</div>
                <div class="text-caption text-grey">Total Items</div>
              </v-card>
            </v-col>
            <v-col cols="3">
              <v-card variant="outlined" class="text-center pa-2">
                <div class="text-h5">{{ result.summary?.with_scripts || 0 }}</div>
                <div class="text-caption text-grey">With Scripts</div>
              </v-card>
            </v-col>
            <v-col cols="6">
              <v-card variant="outlined" class="text-center pa-2">
                <div class="text-h5">{{ result.summary?.total_duration || '00:00:00' }}</div>
                <div class="text-caption text-grey">Total Duration</div>
              </v-card>
            </v-col>
          </v-row>

          <!-- By Type -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-2 py-2">By Type</v-card-title>
            <v-card-text class="py-2">
              <v-chip
                v-for="(count, type) in result.summary?.by_type"
                :key="type"
                :color="getTypeColor(type)"
                size="small"
                class="me-2 mb-1"
              >
                {{ type }}: {{ count }}
              </v-chip>
            </v-card-text>
          </v-card>

          <!-- By Status -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-2 py-2">By Status</v-card-title>
            <v-card-text class="py-2">
              <v-chip
                v-for="(count, status) in result.summary?.by_status"
                :key="status"
                :color="getStatusColor(status)"
                size="small"
                class="me-2 mb-1"
              >
                {{ status }}: {{ count }}
              </v-chip>
            </v-card-text>
          </v-card>

          <!-- Items List -->
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon class="me-2">mdi-format-list-bulleted</v-icon>
                Rundown Items ({{ result.current_state?.length || 0 }})
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="item in result.current_state"
                    :key="item.id"
                  >
                    <template v-slot:prepend>
                      <span class="text-caption text-grey me-2" style="width: 30px;">
                        {{ item.order }}
                      </span>
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ item.title || item.slug }}
                    </v-list-item-title>
                    <template v-slot:append>
                      <v-chip
                        :color="getTypeColor(item.item_type)"
                        size="x-small"
                        class="me-1"
                      >
                        {{ item.item_type }}
                      </v-chip>
                      <v-icon
                        v-if="item.has_script"
                        size="small"
                        color="success"
                      >
                        mdi-script-text
                      </v-icon>
                      <v-icon
                        v-else
                        size="small"
                        color="grey"
                      >
                        mdi-script-text-outline
                      </v-icon>
                    </template>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </div>

        <!-- Error -->
        <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
          {{ error }}
        </v-alert>

        <!-- Initial State -->
        <div v-if="!result && !isRunning && !error" class="text-center py-8">
          <v-icon size="64" color="grey">mdi-compare</v-icon>
          <p class="mt-4 text-body-1 text-grey">
            View rundown structure and item summary
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
          @click="loadRundown"
        >
          <v-icon class="me-1">mdi-refresh</v-icon>
          Load Rundown
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useToolsRunner } from '@/composables/useToolsRunner'

const { isRunning, result, error, runRundownDiff, reset } = useToolsRunner()

const dialogOpen = ref(false)
const episodeNumber = ref('')

const loadRundown = async () => {
  if (!episodeNumber.value) return
  reset()
  try {
    await runRundownDiff(episodeNumber.value)
  } catch (err) {
    console.error('Load rundown failed:', err)
  }
}

const getTypeColor = (type) => {
  const colors = {
    segment: 'primary',
    ad: 'success',
    promo: 'purple',
    cta: 'orange',
    trans: 'cyan',
    cold_open: 'pink'
  }
  return colors[type] || 'grey'
}

const getStatusColor = (status) => {
  const colors = {
    draft: 'grey',
    approved: 'success',
    production: 'primary',
    completed: 'teal'
  }
  return colors[status] || 'grey'
}
</script>
