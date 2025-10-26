import { ref, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { notifyUserStandard, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'

/**
 * Composable for tracking SOT processing jobs and auto-refreshing content
 * Polls for active jobs and triggers content refresh when updates occur
 * Shows toast notifications for phase changes
 */
export function useSOTProcessing() {
  const activeJobs = ref([])
  const pollInterval = ref(null)
  const POLL_FREQUENCY = 3000 // Poll every 3 seconds

  /**
   * Check for active processing jobs for a given episode
   */
  const checkActiveJobs = async (episodeNumber) => {
    if (!episodeNumber) return []

    try {
      const response = await axios.get(`/api/sot/active-jobs/${episodeNumber}`)
      return response.data.jobs || []
    } catch (error) {
      console.error('Failed to check active SOT jobs:', error)
      return []
    }
  }

  /**
   * Start polling for processing updates
   * @param {string} episodeNumber - Episode to monitor
   * @param {Function} onUpdate - Callback when processing progresses (receives job data)
   * @param {Function} onComplete - Callback when processing completes (receives job data)
   */
  const startPolling = (episodeNumber, onUpdate, onComplete) => {
    if (!episodeNumber) {
      console.warn('Cannot start SOT polling without episode number')
      return
    }

    // Clear any existing interval
    stopPolling()

    console.log(`🎬 Starting SOT processing poll for episode ${episodeNumber}`)

    // Initial check
    pollForUpdates(episodeNumber, onUpdate, onComplete)

    // Set up interval
    pollInterval.value = setInterval(() => {
      pollForUpdates(episodeNumber, onUpdate, onComplete)
    }, POLL_FREQUENCY)
  }

  /**
   * Poll once for updates
   */
  const pollForUpdates = async (episodeNumber, onUpdate, onComplete) => {
    const jobs = await checkActiveJobs(episodeNumber)

    // Update active jobs list
    const previousJobs = [...activeJobs.value]
    activeJobs.value = jobs

    // Check for status changes
    jobs.forEach(job => {
      const previousJob = previousJobs.find(j => j.temp_job_id === job.temp_job_id)

      if (!previousJob) {
        // New job detected
        console.log(`🆕 New SOT job detected: ${job.temp_job_id} (${job.current_phase})`)

        // Show slide-in notification for new job
        notifyUserStandard(
          `🎬 ${job.slug}: ${job.phase_message || job.current_phase}`,
          NOTIFICATION_COLORS.INFO,
          3000
        )

        if (onUpdate) onUpdate(job)
      } else if (previousJob.current_phase !== job.current_phase) {
        // Phase change detected
        console.log(`📊 SOT job phase change: ${job.temp_job_id} ${previousJob.current_phase} → ${job.current_phase}`)

        // Show slide-in notification for phase change
        notifyUserStandard(
          `🎬 ${job.slug}: ${job.phase_message || job.current_phase}`,
          NOTIFICATION_COLORS.INFO,
          3000
        )

        if (onUpdate) onUpdate(job)
      }

      // Check for completion
      if (job.status === 'completed' && previousJob?.status !== 'completed') {
        console.log(`✅ SOT job completed: ${job.temp_job_id}`)

        // Show success slide-in notification
        notifyUserStandard(
          `✅ ${job.slug}: Processing complete`,
          NOTIFICATION_COLORS.SUCCESS,
          5000
        )

        if (onComplete) onComplete(job)
      }

      // Check for partial completion (testing mode)
      if (job.status === 'partial_complete' && previousJob?.status !== 'partial_complete') {
        console.log(`🧪 SOT job partial complete: ${job.temp_job_id}`)

        // Show warning slide-in notification for testing mode
        notifyUserStandard(
          `🧪 ${job.slug}: Testing phase complete (partial)`,
          NOTIFICATION_COLORS.WARNING,
          5000
        )

        if (onComplete) onComplete(job)
      }

      // Check for failure
      if (job.status === 'failed' && previousJob?.status !== 'failed') {
        console.log(`❌ SOT job failed: ${job.temp_job_id}`)

        // Show error slide-in notification
        notifyUserStandard(
          `❌ ${job.slug}: Processing failed - click cue block to retry`,
          NOTIFICATION_COLORS.ERROR,
          10000
        )

        if (onUpdate) onUpdate(job)
      }
    })

    // Stop polling if no active jobs
    if (jobs.length === 0 && previousJobs.length > 0) {
      console.log('🛑 No more active SOT jobs, stopping poll')
      stopPolling()
    }
  }

  /**
   * Stop polling
   */
  const stopPolling = () => {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
      console.log('🛑 Stopped SOT processing poll')
    }
  }

  /**
   * Get processing status for a specific asset_id
   */
  const getJobByAssetId = (assetId) => {
    return activeJobs.value.find(job => job.asset_id === assetId)
  }

  /**
   * Check if there are any active jobs
   */
  const hasActiveJobs = () => {
    return activeJobs.value.length > 0
  }

  /**
   * Retry a failed processing job
   * @param {string} tempJobId - The temp_job_id to retry
   * @returns {Promise<boolean>} - Success status
   */
  const retryFailedJob = async (tempJobId) => {
    if (!tempJobId) {
      console.error('Cannot retry: no temp_job_id provided')
      return false
    }

    try {
      console.log(`🔄 Retrying failed job: ${tempJobId}`)

      const response = await axios.post(`/api/sot/retry/${tempJobId}`)

      if (response.status === 200) {
        notifyUserStandard(
          `🔄 Retrying video processing...`,
          NOTIFICATION_COLORS.INFO,
          3000
        )
        return true
      }

      return false
    } catch (error) {
      console.error('Failed to retry job:', error)

      const errorMsg = error.response?.data?.detail || 'Retry failed'
      notifyUserStandard(
        `❌ Retry failed: ${errorMsg}`,
        NOTIFICATION_COLORS.ERROR,
        5000
      )

      return false
    }
  }

  /**
   * Reprocess a SOT completely - Clean up and restart
   * @param {string} assetId - The AssetID to reprocess
   * @returns {Promise<boolean>} - Success status
   */
  const reprocessJob = async (assetId) => {
    if (!assetId) {
      console.error('Cannot reprocess: no assetId provided')
      return false
    }

    try {
      console.log(`🔄 Reprocessing SOT: ${assetId}`)

      const response = await axios.post(`/api/sot/reprocess/${assetId}`)

      if (response.status === 200) {
        notifyUserStandard(
          `🔄 Cleaning up and restarting video processing...`,
          NOTIFICATION_COLORS.INFO,
          3000
        )
        return true
      }

      return false
    } catch (error) {
      console.error('Failed to reprocess:', error)

      const errorMsg = error.response?.data?.detail || 'Reprocess failed'
      notifyUserStandard(
        `❌ Reprocess failed: ${errorMsg}`,
        NOTIFICATION_COLORS.ERROR,
        5000
      )

      return false
    }
  }

  // Cleanup on unmount
  onBeforeUnmount(() => {
    stopPolling()
  })

  return {
    activeJobs,
    startPolling,
    stopPolling,
    checkActiveJobs,
    getJobByAssetId,
    hasActiveJobs,
    retryFailedJob,
    reprocessJob
  }
}
