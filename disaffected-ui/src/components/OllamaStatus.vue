<template>
  <div class="clock-display status-display">
    <div class="label-primary">OLLAMA</div>
    <div class="status-indicator" :class="statusClass">{{ statusText }}</div>
    <div class="label-secondary">{{ modelName || 'LOCAL INFERENCE' }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSystemHealth } from '@/composables/useSystemHealth'

const { health } = useSystemHealth()

const statusText = computed(() => {
  const status = health.value.services?.ollama?.status || 'unknown'

  switch (status) {
    case 'connected':
      return 'ONLINE'
    case 'disabled':
      return 'DISABLED'
    case 'no_config':
      return 'NO CONFIG'
    case 'timeout':
      return 'TIMEOUT'
    case 'connection_refused':
      return 'OFFLINE'
    case 'error':
      return 'ERROR'
    case 'unknown':
    default:
      return 'CHECKING...'
  }
})

const statusClass = computed(() => {
  const status = health.value.services?.ollama?.status || 'unknown'

  switch (status) {
    case 'connected':
      return 'status-green'
    case 'disabled':
      return 'status-gray'
    case 'timeout':
    case 'connection_refused':
    case 'error':
      return 'status-red'
    case 'no_config':
      return 'status-yellow'
    case 'unknown':
    default:
      return 'status-gray'
  }
})

const modelName = computed(() => {
  const model = health.value.services?.ollama?.model
  if (!model) return null

  // Shorten model name if too long (e.g., "llama3:latest" -> "LLAMA3")
  return model.split(':')[0].toUpperCase()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');

.clock-display {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.05);
  padding: 0;
  border-radius: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  min-width: 140px;
  overflow: visible;
  height: 100%;
  justify-content: flex-start;
}

.label-primary {
  font-size: 0.56rem;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  text-align: center;
  margin-bottom: 0;
  background-color: #1976d2;
  padding: 2px 10px 2px 10px;
  border-radius: 0;
}

.status-indicator {
  font-family: 'Courier New', Courier, monospace;
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: 1.2px;
  text-align: center;
  align-self: center;
  width: 100%;
  margin-bottom: 0;
  padding: 2px 10px 0 10px;
}

.label-secondary {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.56rem;
  color: rgba(0, 0, 0, 0.7);
  font-weight: bold;
  text-align: center;
  text-transform: uppercase;
  padding: 0 8px 0 8px;
  margin-top: -4px;
}

.status-green {
  color: #4caf50;
}

.status-yellow {
  color: #ffc107;
}

.status-red {
  color: #f44336;
  animation: pulse 2s infinite;
}

.status-gray {
  color: #9e9e9e;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style>
