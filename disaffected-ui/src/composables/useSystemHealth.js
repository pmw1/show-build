import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

/**
 * Centralized system health monitoring composable — SINGLETON.
 *
 * All components that call useSystemHealth() share ONE health ref, ONE poll
 * timer, and ONE set of computed properties. This prevents the status bar
 * and dashboard from showing different data due to independent polling.
 *
 * Polling starts when the first consumer mounts and stops when the last
 * consumer unmounts (ref-counted).
 */

// ---- Singleton state (module-level, shared across all callers) ----

const POLL_INTERVAL = 10000

const health = ref({
  status: 'unknown',
  timestamp: null,
  services: {
    database: 'unknown',
    ollama: {
      status: 'unknown',
      model: null,
      url: null
    },
    redis: {
      status: 'unknown',
      connected: false,
      latency: null,
      error: null
    },
    celery: {
      status: 'unknown',
      workers: [],
      error: null
    },
    asterisk: {
      status: 'unknown',
      connected: false,
      host: null,
      error: null
    },
    google_drive: {
      status: 'unknown',
      connected: false,
      can_list: false,
      can_write: false,
      error: null
    },
    xtts: {
      status: 'unknown',
      host: null,
      error: null
    },
    tts: {
      status: 'unknown',
      service: null,
      label: null,
      host: null,
      error: null
    },
    vmix: {
      status: 'unknown',
      connected: false,
      host: null,
      error: null
    }
  }
})

const isLoading = ref(false)
const lastError = ref(null)
let pollTimer = null
let consumerCount = 0

// ---- Redis ----
const redisConnected = computed(() => health.value.services.redis?.connected || false)
const redisLatency = computed(() => health.value.services.redis?.latency || null)
const redisError = computed(() => health.value.services.redis?.error || null)

const redisStatus = computed(() => {
  if (redisError.value) return 'error'
  if (!redisConnected.value) return 'warning'
  if (redisLatency.value && redisLatency.value > 100) return 'warning'
  return 'success'
})

const redisStatusText = computed(() => {
  if (redisError.value) return 'Disconnected'
  if (!redisConnected.value) return 'Unknown'
  if (redisLatency.value && redisLatency.value > 100) return 'Slow'
  return 'Connected'
})

const redisStatusColor = computed(() => {
  switch (redisStatus.value) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'grey'
  }
})

const redisStatusIcon = computed(() => {
  switch (redisStatus.value) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert-circle'
    case 'error': return 'mdi-close-circle'
    default: return 'mdi-help-circle'
  }
})

// ---- Celery ----
const workers = computed(() => health.value.services.celery?.workers || [])
const workerCount = computed(() => workers.value.length)
const celeryError = computed(() => health.value.services.celery?.error || null)

const celeryStatus = computed(() => {
  if (celeryError.value) return 'error'
  if (workers.value.length === 0) return 'warning'
  return 'success'
})

const celeryStatusText = computed(() => {
  if (celeryError.value) return 'Error'
  if (workers.value.length === 0) return 'No Workers'
  return `${workers.value.length} Active`
})

const celeryStatusColor = computed(() => {
  switch (celeryStatus.value) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'grey'
  }
})

const celeryStatusIcon = computed(() => {
  switch (celeryStatus.value) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert-circle'
    case 'error': return 'mdi-close-circle'
    default: return 'mdi-help-circle'
  }
})

// ---- SIP/Asterisk ----
const sipConnected = computed(() => health.value.services.asterisk?.connected || false)
const sipHost = computed(() => health.value.services.asterisk?.host || null)
const sipError = computed(() => health.value.services.asterisk?.error || null)

const sipStatus = computed(() => {
  if (sipError.value) return 'error'
  if (!sipConnected.value) return 'warning'
  return 'success'
})

const sipStatusText = computed(() => {
  if (sipError.value) return 'Disconnected'
  if (!sipConnected.value) return 'Unknown'
  return 'Connected'
})

const sipStatusColor = computed(() => {
  switch (sipStatus.value) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'grey'
  }
})

const sipStatusIcon = computed(() => {
  switch (sipStatus.value) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert-circle'
    case 'error': return 'mdi-close-circle'
    default: return 'mdi-help-circle'
  }
})

// ---- Google Drive ----
const driveConnected = computed(() => health.value.services.google_drive?.connected || false)
const driveCanList = computed(() => health.value.services.google_drive?.can_list || false)
const driveCanWrite = computed(() => health.value.services.google_drive?.can_write || false)
const driveError = computed(() => health.value.services.google_drive?.error || null)

const driveStatus = computed(() => {
  const status = health.value.services.google_drive?.status || 'unknown'
  if (status === 'error') return 'error'
  if (status === 'not_configured') return 'warning'
  if (status === 'warning') return 'warning'
  if (status === 'connected') return 'success'
  return 'warning'
})

const driveStatusText = computed(() => {
  const status = health.value.services.google_drive?.status || 'unknown'
  if (status === 'error') return 'Error'
  if (status === 'not_configured') return 'Not Configured'
  if (status === 'warning') return 'Warning'
  if (status === 'connected') return 'Connected'
  return 'Unknown'
})

const driveStatusColor = computed(() => {
  switch (driveStatus.value) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'grey'
  }
})

const driveStatusIcon = computed(() => {
  switch (driveStatus.value) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert-circle'
    case 'error': return 'mdi-close-circle'
    default: return 'mdi-help-circle'
  }
})

// ---- TTS (Fish Speech / XTTS) ----
const ttsHost = computed(() => health.value.services.tts?.host || health.value.services.xtts?.host || null)
const ttsError = computed(() => health.value.services.tts?.error || health.value.services.xtts?.error || null)
const isFishSpeechActive = computed(() => {
  const tts = health.value.services.tts
  return tts && tts.service === 'fishspeech' && tts.status !== 'unknown'
})
const ttsDisplayLabel = computed(() => {
  if (isFishSpeechActive.value) return health.value.services.tts?.label || 'Fish'
  return 'TTS'
})
const isXttsDeprecated = computed(() => {
  return health.value.services.xtts?.status === 'deprecated'
})

const ttsStatus = computed(() => {
  if (isFishSpeechActive.value) {
    const status = health.value.services.tts?.status || 'unknown'
    if (status === 'error') return 'error'
    if (status === 'not_configured') return 'warning'
    if (status === 'warning') return 'warning'
    if (status === 'connected') return 'success'
    return 'warning'
  }
  const status = health.value.services.xtts?.status || 'unknown'
  if (status === 'deprecated') return 'deprecated'
  if (status === 'error') return 'error'
  if (status === 'not_configured') return 'warning'
  if (status === 'warning') return 'warning'
  if (status === 'connected') return 'success'
  return 'warning'
})

const ttsStatusText = computed(() => {
  if (isFishSpeechActive.value) {
    const status = health.value.services.tts?.status || 'unknown'
    if (status === 'error') return 'Error'
    if (status === 'not_configured') return 'Not Configured'
    if (status === 'warning') return 'Warning'
    if (status === 'connected') return 'Connected'
    return 'Unknown'
  }
  const status = health.value.services.xtts?.status || 'unknown'
  if (status === 'deprecated') return 'Deprecated'
  if (status === 'error') return 'Error'
  if (status === 'not_configured') return 'Not Configured'
  if (status === 'warning') return 'Warning'
  if (status === 'connected') return 'Connected'
  return 'Unknown'
})

const ttsStatusColor = computed(() => {
  switch (ttsStatus.value) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    case 'deprecated': return 'grey'
    default: return 'grey'
  }
})

const ttsStatusIcon = computed(() => {
  switch (ttsStatus.value) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert-circle'
    case 'error': return 'mdi-close-circle'
    case 'deprecated': return 'mdi-minus-circle'
    default: return 'mdi-help-circle'
  }
})

// ---- vMix ----
const vmixConnected = computed(() => health.value.services.vmix?.connected || false)
const vmixHost = computed(() => health.value.services.vmix?.host || null)
const vmixError = computed(() => health.value.services.vmix?.error || null)

const vmixStatus = computed(() => {
  const status = health.value.services.vmix?.status || 'unknown'
  if (status === 'error') return 'error'
  if (status === 'disabled') return 'warning'
  if (status === 'not_configured') return 'warning'
  if (status === 'connected') return 'success'
  return 'warning'
})

const vmixStatusText = computed(() => {
  const status = health.value.services.vmix?.status || 'unknown'
  if (status === 'error') return 'Disconnected'
  if (status === 'disabled') return 'Disabled'
  if (status === 'not_configured') return 'Not Configured'
  if (status === 'connected') return 'Connected'
  return 'Unknown'
})

const vmixStatusColor = computed(() => {
  switch (vmixStatus.value) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'grey'
  }
})

const vmixStatusIcon = computed(() => {
  switch (vmixStatus.value) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert-circle'
    case 'error': return 'mdi-close-circle'
    default: return 'mdi-help-circle'
  }
})

const loading = computed(() => isLoading.value)

// ---- Fetch / polling (shared, not per-component) ----

const saveHealthToStorage = (healthData) => {
  try {
    localStorage.setItem('system-health-status', JSON.stringify({
      data: healthData,
      savedAt: new Date().toISOString()
    }))
  } catch (error) {
    console.warn('Failed to save health status to localStorage:', error)
  }
}

const loadHealthFromStorage = () => {
  try {
    const saved = localStorage.getItem('system-health-status')
    if (!saved) return null
    const { data, savedAt } = JSON.parse(saved)
    const age = Date.now() - new Date(savedAt).getTime()
    const maxAge = 5 * 60 * 1000
    if (age < maxAge) {
      return data
    }
    return null
  } catch (error) {
    return null
  }
}

const fetchHealth = async () => {
  try {
    isLoading.value = true
    lastError.value = null
    const response = await axios.get('/health')
    health.value = {
      ...health.value,
      ...response.data,
      services: {
        ...health.value.services,
        ...response.data.services
      }
    }
    saveHealthToStorage(health.value)
  } catch (error) {
    console.error('Health check failed:', error)
    lastError.value = error.message
    if (health.value.timestamp !== null) {
      health.value = {
        status: 'error',
        timestamp: new Date().toISOString(),
        services: {
          database: 'error',
          ollama: { status: 'error', model: null, url: null },
          redis: { status: 'error', connected: false, latency: null, error: 'Health check failed' },
          celery: { status: 'error', workers: [], error: 'Health check failed' }
        }
      }
      saveHealthToStorage(health.value)
    }
  } finally {
    isLoading.value = false
  }
}

const fetchServiceHealth = async (serviceName) => {
  try {
    const response = await axios.get(`/health/${serviceName}`)
    if (serviceName === 'backend') {
      health.value.status = response.data.status
      health.value.timestamp = response.data.timestamp
    } else {
      health.value.services[serviceName] = response.data
    }
  } catch (error) {
    console.error(`Health check failed for ${serviceName}:`, error)
  }
}

const fetchHealthProgressive = async () => {
  isLoading.value = true
  lastError.value = null
  try {
    const response = await axios.get('/health/critical', { timeout: 3000 })
    health.value.status = response.data.status
    health.value.timestamp = response.data.timestamp
    health.value.services.database = response.data.services.database
  } catch (error) {
    console.error('Critical health check failed:', error)
    if (health.value.timestamp === null) return
  }
  setTimeout(async () => {
    try {
      const response = await axios.get('/health/secondary', { timeout: 5000 })
      if (response.data.services) {
        health.value.services = { ...health.value.services, ...response.data.services }
      }
    } catch (error) {
      console.error('Secondary health check failed:', error)
    } finally {
      isLoading.value = false
    }
  }, 100)
}

function startPolling() {
  if (pollTimer) return // Already running
  // Seed from localStorage to avoid flash, then fetch fresh immediately
  const saved = loadHealthFromStorage()
  if (saved) health.value = saved
  fetchHealth()
  pollTimer = setInterval(fetchHealth, POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// ---- Public composable (ref-counted lifecycle) ----

export function useSystemHealth() {
  onMounted(() => {
    consumerCount++
    if (consumerCount === 1) startPolling()
  })

  onUnmounted(() => {
    consumerCount--
    if (consumerCount <= 0) {
      consumerCount = 0
      stopPolling()
    }
  })

  return {
    health,
    isLoading,
    lastError,
    refresh: fetchHealth,
    startPolling,
    stopPolling,
    checkHealth: fetchHealth,
    fetchServiceHealth,
    fetchHealthProgressive,
    // Redis
    redisConnected, redisLatency, redisError,
    redisStatus, redisStatusText, redisStatusColor, redisStatusIcon,
    // Celery
    workers, workerCount, celeryError,
    celeryStatus, celeryStatusText, celeryStatusColor, celeryStatusIcon,
    // SIP/Asterisk
    sipConnected, sipHost, sipError,
    sipStatus, sipStatusText, sipStatusColor, sipStatusIcon,
    // Google Drive
    driveConnected, driveCanList, driveCanWrite, driveError,
    driveStatus, driveStatusText, driveStatusColor, driveStatusIcon,
    // TTS
    ttsHost, ttsError,
    ttsStatus, ttsStatusText, ttsStatusColor, ttsStatusIcon,
    ttsDisplayLabel, isFishSpeechActive, isXttsDeprecated,
    // vMix
    vmixConnected, vmixHost, vmixError,
    vmixStatus, vmixStatusText, vmixStatusColor, vmixStatusIcon,
    loading,
    // Legacy aliases
    xttsHost: ttsHost,
    xttsError: ttsError,
    xttsStatus: ttsStatus,
    xttsStatusText: ttsStatusText,
    xttsStatusColor: ttsStatusColor,
    xttsStatusIcon: ttsStatusIcon
  }
}
