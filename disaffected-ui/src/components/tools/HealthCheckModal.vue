<template>
  <v-dialog v-model="dialogOpen" max-width="800" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" size="small" color="primary" v-bind="props">
        Run Check
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center bg-primary text-white">
        <v-icon class="me-2">mdi-heart-pulse</v-icon>
        System Health Check
      </v-card-title>

      <v-card-text class="pa-4" style="max-height: 600px;">
        <!-- Loading State -->
        <div v-if="isRunning" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4 text-body-1">Running diagnostics...</p>
        </div>

        <!-- Results -->
        <div v-else-if="result">
          <!-- Overall Status -->
          <v-alert
            :type="getStatusType(result.status)"
            variant="tonal"
            class="mb-4"
          >
            <strong>System Status:</strong> {{ result.status.toUpperCase() }}
            <span v-if="result.issues?.length" class="ms-2">
              ({{ result.issues.length }} issue{{ result.issues.length > 1 ? 's' : '' }})
            </span>
          </v-alert>

          <!-- Issues List -->
          <v-alert
            v-if="result.issues?.length"
            type="warning"
            variant="outlined"
            class="mb-4"
          >
            <div class="font-weight-bold mb-2">Issues Detected:</div>
            <ul class="ms-4">
              <li v-for="(issue, idx) in result.issues" :key="idx">{{ issue }}</li>
            </ul>
          </v-alert>

          <!-- Services Grid -->
          <v-row>
            <!-- Database -->
            <v-col cols="12" md="6">
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1 pb-0">
                  <v-icon class="me-2" :color="getStatusColor(result.database?.status)">
                    mdi-database
                  </v-icon>
                  Database
                </v-card-title>
                <v-card-text>
                  <v-chip
                    :color="getStatusColor(result.database?.status)"
                    size="small"
                    class="mb-2"
                  >
                    {{ result.database?.status || 'unknown' }}
                  </v-chip>
                  <div v-if="result.database?.table_counts" class="text-caption">
                    <div v-for="(count, table) in result.database.table_counts" :key="table">
                      {{ table }}: {{ count }}
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- Redis -->
            <v-col cols="12" md="6">
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1 pb-0">
                  <v-icon class="me-2" :color="getStatusColor(result.redis?.status)">
                    mdi-memory
                  </v-icon>
                  Redis
                </v-card-title>
                <v-card-text>
                  <v-chip
                    :color="getStatusColor(result.redis?.status)"
                    size="small"
                    class="mb-2"
                  >
                    {{ result.redis?.status || 'unknown' }}
                  </v-chip>
                  <div v-if="result.redis?.latency_ms" class="text-caption">
                    Latency: {{ result.redis.latency_ms }}ms
                  </div>
                  <div v-if="result.redis?.used_memory_human" class="text-caption">
                    Memory: {{ result.redis.used_memory_human }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- Celery -->
            <v-col cols="12" md="6">
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1 pb-0">
                  <v-icon class="me-2" :color="getStatusColor(result.celery?.status)">
                    mdi-cog-sync
                  </v-icon>
                  Celery Workers
                </v-card-title>
                <v-card-text>
                  <v-chip
                    :color="getStatusColor(result.celery?.status)"
                    size="small"
                    class="mb-2"
                  >
                    {{ result.celery?.total_workers || 0 }} worker(s)
                  </v-chip>
                  <div v-if="result.celery?.workers" class="text-caption">
                    <div v-for="(info, worker) in result.celery.workers" :key="worker">
                      {{ worker.split('@')[1] || worker }}: {{ info.active_tasks }} active
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- Storage -->
            <v-col cols="12" md="6">
              <v-card variant="outlined">
                <v-card-title class="text-subtitle-1 pb-0">
                  <v-icon class="me-2" color="primary">mdi-harddisk</v-icon>
                  Storage
                </v-card-title>
                <v-card-text>
                  <div v-for="(info, name) in result.storage" :key="name" class="mb-2">
                    <div class="d-flex align-center justify-space-between">
                      <span class="text-caption">{{ name }}</span>
                      <v-chip
                        :color="getStatusColor(info.status)"
                        size="x-small"
                      >
                        {{ info.free_gb }}GB free
                      </v-chip>
                    </div>
                    <v-progress-linear
                      :model-value="info.used_percent || 0"
                      :color="info.used_percent > 80 ? 'warning' : 'primary'"
                      height="4"
                      class="mt-1"
                    />
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- APIs -->
          <v-card variant="outlined" class="mt-4" v-if="Object.keys(result.apis || {}).length">
            <v-card-title class="text-subtitle-1">
              <v-icon class="me-2">mdi-api</v-icon>
              External APIs
            </v-card-title>
            <v-card-text>
              <v-chip
                v-for="(info, name) in result.apis"
                :key="name"
                :color="getStatusColor(info.status)"
                size="small"
                class="me-2 mb-2"
              >
                {{ name }}: {{ info.status }}
              </v-chip>
            </v-card-text>
          </v-card>

          <!-- Timestamp -->
          <div class="text-caption text-grey mt-4">
            Checked: {{ formatTimestamp(result.timestamp) }}
          </div>
        </div>

        <!-- Error State -->
        <v-alert v-else-if="error" type="error" variant="tonal">
          {{ error }}
        </v-alert>

        <!-- Initial State -->
        <div v-else class="text-center py-8">
          <v-icon size="64" color="grey">mdi-heart-pulse</v-icon>
          <p class="mt-4 text-body-1 text-grey">
            Click "Run Check" to perform system diagnostics
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
          @click="runCheck"
        >
          <v-icon class="me-1">mdi-refresh</v-icon>
          Run Check
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useToolsRunner } from '@/composables/useToolsRunner'

const { isRunning, result, error, runHealthCheck } = useToolsRunner()

const dialogOpen = ref(false)

// Run check when dialog opens
watch(dialogOpen, (open) => {
  if (open && !result.value) {
    runCheck()
  }
})

const runCheck = async () => {
  try {
    await runHealthCheck()
  } catch (err) {
    console.error('Health check failed:', err)
  }
}

const getStatusType = (status) => {
  switch (status) {
    case 'healthy': return 'success'
    case 'warning': return 'warning'
    case 'degraded':
    case 'error': return 'error'
    default: return 'info'
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'healthy':
    case 'connected': return 'success'
    case 'warning': return 'warning'
    case 'error':
    case 'degraded':
    case 'connection_refused':
    case 'timeout': return 'error'
    case 'not_configured': return 'grey'
    default: return 'info'
  }
}

const formatTimestamp = (ts) => {
  if (!ts) return 'N/A'
  return new Date(ts).toLocaleString()
}
</script>
