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

  const loading = computed(() => isLoading.value)

  /**
   * Fetch current health status from backend
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

    } catch (error) {
      console.error('Health check failed:', error)
      lastError.value = error.message

      // Set all services to error state
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
    } finally {
      isLoading.value = false
    }
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
    loading
  }
}
