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
    <v-tooltip location="bottom">
      <template v-slot:activator="{ props }">
        <div
          v-bind="props"
          class="health-item"
          :class="{ 'health-error': celeryStatus === 'error', 'health-warning': celeryStatus === 'warning' }"
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
      </template>
      <div>
        <strong>Celery Workers</strong><br>
        Status: {{ celeryStatusText }}<br>
        <span v-if="workerCount > 0">
          Active Workers: {{ workerCount }}<br>
          <span v-for="worker in workers" :key="worker" class="text-caption">
            • {{ worker }}<br>
          </span>
        </span>
        <span v-if="celeryError" class="text-error">{{ celeryError }}</span>
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
  loading,
  checkHealth
} = useSystemHealth()

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
