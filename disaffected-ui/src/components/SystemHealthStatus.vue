<template>
  <div class="system-health-display">
    <!-- Redis Status -->
    <v-tooltip location="bottom">
      <template v-slot:activator="{ props }">
        <div
          v-bind="props"
          class="health-item"
          :class="{ 'health-error': redisStatus === 'error', 'health-warning': redisStatus === 'warning' }"
        >
          <v-icon
            :color="redisStatusColor"
            size="small"
            class="health-icon"
          >
            {{ redisStatusIcon }}
          </v-icon>
          <span class="health-label">Redis</span>
        </div>
      </template>
      <div>
        <strong>Redis Broker</strong><br>
        Status: {{ redisStatusText }}<br>
        <span v-if="redisLatency">Latency: {{ redisLatency }}ms</span>
        <span v-if="redisError" class="text-error">{{ redisError }}</span>
      </div>
    </v-tooltip>

    <!-- Celery Workers Status -->
    <div
      class="health-item"
      :class="{ 'health-error': celeryStatus === 'error', 'health-warning': celeryStatus === 'warning' }"
      @click="showCeleryModal = true"
    >
      <v-icon
        :color="celeryStatusColor"
        size="small"
        class="health-icon"
      >
        {{ celeryStatusIcon }}
      </v-icon>
      <span class="health-label">Workers</span>
      <v-chip
        v-if="workerCount > 0"
        size="x-small"
        :color="celeryStatusColor"
        class="ml-1"
        style="height: 16px; min-width: 20px; padding: 0 4px;"
      >
        {{ workerCount }}
      </v-chip>
    </div>

    <!-- Celery Workers Modal -->
    <v-dialog v-model="showCeleryModal" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon :color="celeryStatusColor" class="mr-2">{{ celeryStatusIcon }}</v-icon>
          Celery Workers
        </v-card-title>
        <v-card-text>
          <div class="mb-3">
            <strong>Status:</strong> {{ celeryStatusText }}
          </div>
          <div v-if="workerCount > 0" class="mb-3">
            <strong>Active Workers:</strong> {{ workerCount }}
            <v-list density="compact" class="mt-2">
              <v-list-item
                v-for="worker in workers"
                :key="worker"
                :title="worker"
                prepend-icon="mdi-cog"
              />
            </v-list>
          </div>
          <div v-if="celeryError">
            <v-alert type="error" density="compact" class="mt-2">
              {{ celeryError }}
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showCeleryModal = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- SIP/Asterisk Status -->
    <v-tooltip location="bottom">
      <template v-slot:activator="{ props }">
        <div
          v-bind="props"
          class="health-item"
          :class="{ 'health-error': sipStatus === 'error', 'health-warning': sipStatus === 'warning' }"
        >
          <v-icon
            :color="sipStatusColor"
            size="small"
            class="health-icon"
          >
            {{ sipStatusIcon }}
          </v-icon>
          <span class="health-label">SIP</span>
        </div>
      </template>
      <div>
        <strong>Asterisk SIP/AMI</strong><br>
        Status: {{ sipStatusText }}<br>
        <span v-if="sipHost">Host: {{ sipHost }}</span>
        <span v-if="sipError" class="text-error">{{ sipError }}</span>
      </div>
    </v-tooltip>

    <!-- Google Drive Status -->
    <v-tooltip location="bottom">
      <template v-slot:activator="{ props }">
        <div
          v-bind="props"
          class="health-item"
          :class="{ 'health-error': driveStatus === 'error', 'health-warning': driveStatus === 'warning' }"
        >
          <v-icon
            :color="driveStatusColor"
            size="small"
            class="health-icon"
          >
            {{ driveStatusIcon }}
          </v-icon>
          <span class="health-label">Goog</span>
        </div>
      </template>
      <div>
        <strong>Google Drive API</strong><br>
        Status: {{ driveStatusText }}<br>
        <span v-if="driveConnected && driveCanList">✓ Can list files</span><br v-if="driveConnected && driveCanList">
        <span v-if="driveConnected && driveCanWrite">✓ Can write files</span><br v-if="driveConnected && driveCanWrite">
        <span v-if="driveError" class="text-error">{{ driveError }}</span>
      </div>
    </v-tooltip>

    <!-- XTTS Status -->
    <v-tooltip location="bottom">
      <template v-slot:activator="{ props }">
        <div
          v-bind="props"
          class="health-item"
          :class="{ 'health-error': xttsStatus === 'error', 'health-warning': xttsStatus === 'warning' }"
        >
          <v-icon
            :color="xttsStatusColor"
            size="small"
            class="health-icon"
          >
            {{ xttsStatusIcon }}
          </v-icon>
          <span class="health-label">XTTS</span>
        </div>
      </template>
      <div>
        <strong>XTTS TTS Service</strong><br>
        Status: {{ xttsStatusText }}<br>
        <span v-if="xttsHost">Host: {{ xttsHost }}</span>
        <span v-if="xttsError" class="text-error">{{ xttsError }}</span>
      </div>
    </v-tooltip>

    <!-- Refresh Button -->
    <v-btn
      icon
      size="x-small"
      variant="text"
      @click="refreshStatus"
      :loading="loading"
      class="ml-1"
    >
      <v-icon size="small">mdi-refresh</v-icon>
    </v-btn>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSystemHealth } from '@/composables/useSystemHealth'

const {
  redisStatus,
  redisStatusText,
  redisStatusColor,
  redisStatusIcon,
  redisLatency,
  redisError,
  celeryStatus,
  celeryStatusText,
  celeryStatusColor,
  celeryStatusIcon,
  workerCount,
  workers,
  celeryError,
  sipStatus,
  sipStatusText,
  sipStatusColor,
  sipStatusIcon,
  sipHost,
  sipError,
  driveStatus,
  driveStatusText,
  driveStatusColor,
  driveStatusIcon,
  driveConnected,
  driveCanList,
  driveCanWrite,
  driveError,
  xttsStatus,
  xttsStatusText,
  xttsStatusColor,
  xttsStatusIcon,
  xttsHost,
  xttsError,
  loading,
  checkHealth
} = useSystemHealth()

// Modal state
const showCeleryModal = ref(false)

let healthInterval = null

const refreshStatus = async () => {
  await checkHealth()
}

onMounted(() => {
  // Initial check
  checkHealth()

  // Auto-refresh every 30 seconds
  healthInterval = setInterval(checkHealth, 30000)
})

onUnmounted(() => {
  if (healthInterval) {
    clearInterval(healthInterval)
  }
})
</script>

<style scoped>
.system-health-display {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  height: 100%;
  margin-left: 8px;
}

.health-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.health-item:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(0, 0, 0, 0.2);
}

.health-item.health-error {
  background: rgba(244, 67, 54, 0.1);
  border-color: rgba(244, 67, 54, 0.3);
}

.health-item.health-warning {
  background: rgba(255, 152, 0, 0.1);
  border-color: rgba(255, 152, 0, 0.3);
}

.health-icon {
  flex-shrink: 0;
}

.health-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
</style>
