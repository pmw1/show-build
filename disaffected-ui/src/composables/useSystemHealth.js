import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

/**
 * Centralized system health monitoring composable
 * Polls /health endpoint and provides reactive health status for all services
 */
export function useSystemHealth(pollInterval = 10000) {
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
      }
    }
  })

  const isLoading = ref(false)
  const lastError = ref(null)
  let pollTimer = null

  // Redis computed properties
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

  // Celery computed properties
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

  // SIP/Asterisk computed properties
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

  // Google Drive computed properties
  const driveConnected = computed(() => health.value.services.google_drive?.connected || false)
  const driveCanList = computed(() => health.value.services.google_drive?.can_list || false)
  const driveCanWrite = computed(() => health.value.services.google_drive?.can_write || false)
  const driveError = computed(() => health.value.services.google_drive?.error || null)

  const driveStatus = computed(() => {
    const status = health.value.services.google_drive?.status || 'unknown'
    if (status === 'error') return 'error'
    if (status === 'not_configured') return 'warning'
    if (status === 'warning') return 'warning'
    if (status === 'connected' && driveCanList.value && driveCanWrite.value) return 'success'
    return 'warning'
  })

  const driveStatusText = computed(() => {
    const status = health.value.services.google_drive?.status || 'unknown'
    if (status === 'error') return 'Error'
    if (status === 'not_configured') return 'Not Configured'
    if (status === 'warning') return 'Degraded'
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

  // XTTS computed properties
  const xttsHost = computed(() => health.value.services.xtts?.host || null)
  const xttsError = computed(() => health.value.services.xtts?.error || null)

  const xttsStatus = computed(() => {
    const status = health.value.services.xtts?.status || 'unknown'
    if (status === 'error') return 'error'
    if (status === 'not_configured') return 'warning'
    if (status === 'warning') return 'warning'
    if (status === 'connected') return 'success'
    return 'warning'
  })

  const xttsStatusText = computed(() => {
    const status = health.value.services.xtts?.status || 'unknown'
    if (status === 'error') return 'Error'
    if (status === 'not_configured') return 'Not Configured'
    if (status === 'warning') return 'Warning'
    if (status === 'connected') return 'Connected'
    return 'Unknown'
  })

  const xttsStatusColor = computed(() => {
    switch (xttsStatus.value) {
      case 'success': return 'success'
      case 'warning': return 'warning'
      case 'error': return 'error'
      default: return 'grey'
    }
  })

  const xttsStatusIcon = computed(() => {
    switch (xttsStatus.value) {
      case 'success': return 'mdi-check-circle'
      case 'warning': return 'mdi-alert-circle'
      case 'error': return 'mdi-close-circle'
      default: return 'mdi-help-circle'
    }
  })

  const loading = computed(() => isLoading.value)

  /**
   * Fetch individual service health (for progressive updates)
   */
  const fetchServiceHealth = async (serviceName) => {
    try {
      const response = await axios.get(`/health/${serviceName}`)

      // Update just this service
      if (serviceName === 'backend') {
        health.value.status = response.data.status
        health.value.timestamp = response.data.timestamp
      } else {
        health.value.services[serviceName] = response.data
      }
    } catch (error) {
      console.error(`Health check failed for ${serviceName}:`, error)
      // Don't update on error - let it stay in "checking" state
    }
  }

  /**
   * Save health status to localStorage for carryover on reload
   */
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

  /**
   * Load last known health status from localStorage
   * Returns null if no saved status or if it's too old (>5 minutes)
   */
  const loadHealthFromStorage = () => {
    try {
      const saved = localStorage.getItem('system-health-status')
      if (!saved) return null

      const { data, savedAt } = JSON.parse(saved)
      const age = Date.now() - new Date(savedAt).getTime()
      const maxAge = 5 * 60 * 1000 // 5 minutes

      // Only use saved status if it's recent
      if (age < maxAge) {
        console.log(`📦 Loaded health status from localStorage (${Math.round(age / 1000)}s old)`)
        return data
      } else {
        console.log('📦 Saved health status too old, discarding')
        return null
      }
    } catch (error) {
      console.warn('Failed to load health status from localStorage:', error)
      return null
    }
  }

  /**
   * Fetch current health status from backend
   * Progressive loading: backend/db first, then other services
   */
  const fetchHealth = async () => {
    try {
      isLoading.value = true
      lastError.value = null

      const response = await axios.get('/health')

      // Merge response data with existing structure
      health.value = {
        ...health.value,
        ...response.data,
        services: {
          ...health.value.services,
          ...response.data.services
        }
      }

      // Save to localStorage for next reload
      saveHealthToStorage(health.value)

    } catch (error) {
      console.error('Health check failed:', error)
      lastError.value = error.message

      // Only set to error state if we've had at least one successful check before
      // Otherwise keep it as "unknown" to avoid red status on initial load
      if (health.value.timestamp !== null) {
        // We've had a successful check before, so this is a real error
        health.value = {
          status: 'error',
          timestamp: new Date().toISOString(),
          services: {
            database: 'error',
            ollama: {
              status: 'error',
              model: null,
              url: null
            },
            redis: {
              status: 'error',
              connected: false,
              latency: null,
              error: 'Health check failed'
            },
            celery: {
              status: 'error',
              workers: [],
              error: 'Health check failed'
            }
          }
        }
        // Save error state too
        saveHealthToStorage(health.value)
      }
      // else: keep the initial "unknown" state (shows gray, not red)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Progressive health check - checks critical services first
   */
  const fetchHealthProgressive = async () => {
    isLoading.value = true
    lastError.value = null

    // Phase 1: Check backend + database (critical services)
    try {
      const response = await axios.get('/health/critical', { timeout: 3000 })

      health.value.status = response.data.status
      health.value.timestamp = response.data.timestamp
      health.value.services.database = response.data.services.database

      console.log('✅ Critical services (BACK, DB) loaded')
    } catch (error) {
      console.error('Critical health check failed:', error)
      if (health.value.timestamp === null) {
        // First check - keep as unknown
        return
      }
    }

    // Phase 2: Check remaining services in background (non-blocking)
    setTimeout(async () => {
      try {
        const response = await axios.get('/health/secondary', { timeout: 5000 })

        // Update secondary services
        if (response.data.services) {
          health.value.services = {
            ...health.value.services,
            ...response.data.services
          }
        }

        console.log('✅ Secondary services (Ollama, Redis, Celery, etc.) loaded')
      } catch (error) {
        console.error('Secondary health check failed:', error)
      } finally {
        isLoading.value = false
      }
    }, 100) // Small delay to let UI update first
  }

  /**
   * Check health - alias for manual refresh
   */
  const checkHealth = async () => {
    await fetchHealth()
  }

  /**
   * Start polling health status
   */
  const startPolling = () => {
    // Initial fetch
    fetchHealth()

    // Set up polling interval
    pollTimer = setInterval(fetchHealth, pollInterval)
  }

  /**
   * Stop polling health status
   */
  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  /**
   * Manually trigger a health check
   */
  const refresh = async () => {
    await fetchHealth()
  }

  // Auto-start/stop with component lifecycle
  onMounted(() => {
    // Load last known health status from localStorage (carryover from previous session)
    const savedHealth = loadHealthFromStorage()
    if (savedHealth) {
      health.value = savedHealth
      console.log('✅ Using saved health status - no flash on reload!')
    }

    // Then start polling (will update with fresh data in background)
    startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    health,
    isLoading,
    lastError,
    refresh,
    startPolling,
    stopPolling,
    checkHealth,
    fetchServiceHealth,
    fetchHealthProgressive,
    // Redis computed properties
    redisConnected,
    redisLatency,
    redisError,
    redisStatus,
    redisStatusText,
    redisStatusColor,
    redisStatusIcon,
    // Celery computed properties
    workers,
    workerCount,
    celeryError,
    celeryStatus,
    celeryStatusText,
    celeryStatusColor,
    celeryStatusIcon,
    // SIP/Asterisk computed properties
    sipConnected,
    sipHost,
    sipError,
    sipStatus,
    sipStatusText,
    sipStatusColor,
    sipStatusIcon,
    // Google Drive computed properties
    driveConnected,
    driveCanList,
    driveCanWrite,
    driveError,
    driveStatus,
    driveStatusText,
    driveStatusColor,
    driveStatusIcon,
    // XTTS computed properties
    xttsHost,
    xttsError,
    xttsStatus,
    xttsStatusText,
    xttsStatusColor,
    xttsStatusIcon,
    loading
  }
}
