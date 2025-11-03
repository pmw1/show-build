/**
 * Job Monitoring Composable
 * Tracks all SOT processing jobs with real-time updates
 */
import { ref, computed } from 'vue'
import axios from 'axios'

const activeJobs = ref([])
const recentJobs = ref([])
const pollInterval = ref(null)
const isPolling = ref(false)

export function useJobMonitor() {
  /**
   * Fetch all active jobs from the API
   */
  const fetchActiveJobs = async () => {
    try {
      const response = await axios.get('/api/sot/jobs/active')
      activeJobs.value = response.data.jobs || []

      console.log(`📊 Active jobs: ${activeJobs.value.length}`)

      return activeJobs.value
    } catch (error) {
      console.error('Failed to fetch active jobs:', error)
      return []
    }
  }

  /**
   * Fetch recent completed/failed jobs
   */
  const fetchRecentJobs = async (limit = 10) => {
    try {
      const response = await axios.get(`/api/sot/jobs/recent?limit=${limit}`)
      recentJobs.value = response.data.jobs || []

      return recentJobs.value
    } catch (error) {
      console.error('Failed to fetch recent jobs:', error)
      return []
    }
  }

  /**
   * Start polling for job updates
   */
  const startPolling = (intervalMs = 3000) => {
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

    console.log('📡 Started job monitoring')
  }

  /**
   * Stop polling for job updates
   */
  const stopPolling = () => {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
      isPolling.value = false
      console.log('🛑 Stopped job monitoring')
    }
  }

  /**
   * Get total active job count
   */
  const activeJobCount = computed(() => activeJobs.value.length)

  /**
   * Get count of stalled jobs
   */
  const stalledJobCount = computed(() => {
    return activeJobs.value.filter(job => job.is_stalled).length
  })

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
    return stalledJobCount.value > 0 || recentFailureCount.value > 0
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
   * Get phase display name
   */
  const getPhaseDisplayName = (phase) => {
    const phaseNames = {
      'phase0': 'Pre-Analysis',
      'phase0.5': 'Transcription',
      'phase1': 'Video Normalization',
      'phase1.1': 'Audio Channel Analysis',
      'phase2': 'Audio Normalization',
      'phase3': 'Trimming',
      'phase4': 'Clip Extraction',
      'phase5': 'Moving to Final Location',
      'phase6': 'Thumbnail Generation',
      'phase7': 'Post-Analysis',
      'phase8': 'Verification'
    }
    return phaseNames[phase] || phase
  }

  /**
   * Get status color for badge
   */
  const getStatusColor = (job) => {
    if (job.is_stalled) return 'warning'

    const colors = {
      'queued': 'info',
      'processing': 'primary',
      'completed': 'success',
      'failed': 'error'
    }
    return colors[job.status] || 'default'
  }

  return {
    // State
    activeJobs,
    recentJobs,
    isPolling,

    // Computed
    activeJobCount,
    stalledJobCount,
    recentFailureCount,
    hasIssues,

    // Methods
    fetchActiveJobs,
    fetchRecentJobs,
    startPolling,
    stopPolling,
    getTimeAgo,
    getPhaseDisplayName,
    getStatusColor
  }
}
