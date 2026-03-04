/**
 * Celery Job Monitoring Composable
 * Tracks all celery tasks dispatched from show-build with real-time status updates
 */
import { ref, computed } from 'vue'
import axios from 'axios'

const activeJobs = ref([])
const recentJobs = ref([])
const pollInterval = ref(null)
const isPolling = ref(false)

export function useJobMonitor() {
  /**
   * Fetch all active (pending/running) jobs from the API
   */
  const fetchActiveJobs = async () => {
    try {
      const response = await axios.get('/api/celery-jobs/active')
      activeJobs.value = response.data.jobs || []
      return activeJobs.value
    } catch (error) {
      console.error('Failed to fetch active celery jobs:', error)
      return []
    }
  }

  /**
   * Fetch recent completed/failed jobs
   */
  const fetchRecentJobs = async (limit = 20) => {
    try {
      const response = await axios.get(`/api/celery-jobs/recent?limit=${limit}`)
      recentJobs.value = response.data.jobs || []
      return recentJobs.value
    } catch (error) {
      console.error('Failed to fetch recent celery jobs:', error)
      return []
    }
  }

  /**
   * Clear completed/failed jobs from the log
   */
  const clearJobs = async (status = null) => {
    try {
      const url = status
        ? `/api/celery-jobs/clear?status=${status}`
        : '/api/celery-jobs/clear'
      const response = await axios.delete(url)
      // Refresh after clearing
      await fetchRecentJobs()
      return response.data
    } catch (error) {
      console.error('Failed to clear celery jobs:', error)
      return null
    }
  }

  /**
   * Start polling for job updates
   */
  const startPolling = (intervalMs = 5000) => {
    if (isPolling.value) return

    isPolling.value = true

    // Fetch immediately
    fetchActiveJobs()
    fetchRecentJobs()

    // Then poll at interval
    pollInterval.value = setInterval(() => {
      fetchActiveJobs()
      fetchRecentJobs()
    }, intervalMs)
  }

  /**
   * Stop polling for job updates
   */
  const stopPolling = () => {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
      isPolling.value = false
    }
  }

  /**
   * Get total active job count
   */
  const activeJobCount = computed(() => activeJobs.value.length)

  /**
   * Get count of failed jobs in recent history
   */
  const recentFailureCount = computed(() => {
    return recentJobs.value.filter(job => job.status === 'failed').length
  })

  /**
   * Check if there are any issues that need attention
   */
  const hasIssues = computed(() => {
    return recentFailureCount.value > 0
  })

  /**
   * Get formatted time ago string
   */
  const getTimeAgo = (isoString) => {
    if (!isoString) return 'Unknown'

    const date = new Date(isoString)
    const now = new Date()
    const seconds = Math.floor((now - date) / 1000)

    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  /**
   * Get status color for badge
   */
  const getStatusColor = (job) => {
    const colors = {
      'pending': 'info',
      'running': 'primary',
      'completed': 'success',
      'failed': 'error'
    }
    return colors[job.status] || 'default'
  }

  /**
   * Get category display color
   */
  const getCategoryColor = (category) => {
    const colors = {
      'tools': 'deep-purple',
      'assets': 'teal',
      'media': 'orange',
      'sot': 'blue',
      'general': 'grey'
    }
    return colors[category] || 'grey'
  }

  return {
    // State
    activeJobs,
    recentJobs,
    isPolling,

    // Computed
    activeJobCount,
    recentFailureCount,
    hasIssues,

    // Methods
    fetchActiveJobs,
    fetchRecentJobs,
    clearJobs,
    startPolling,
    stopPolling,
    getTimeAgo,
    getStatusColor,
    getCategoryColor
  }
}
