/**
 * useToolsRunner - Composable for running production tools
 *
 * Handles both sync and async (Celery) tool execution with:
 * - Task polling for async operations
 * - Progress tracking
 * - Result handling
 */

import { ref, inject } from 'vue'

export function useToolsRunner() {
  const axios = inject('axios')

  // State
  const isRunning = ref(false)
  const progress = ref(0)
  const currentTask = ref(null)
  const result = ref(null)
  const error = ref(null)

  // Polling configuration
  const POLL_INTERVAL = 3000 // 3 seconds

  /**
   * Run a sync tool (immediate response)
   */
  const runSyncTool = async (endpoint, payload = {}) => {
    isRunning.value = true
    error.value = null
    result.value = null
    progress.value = 0

    try {
      const response = await axios.post(`/tools/${endpoint}`, payload)
      result.value = response.data
      progress.value = 100
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      isRunning.value = false
    }
  }

  /**
   * Run an async tool (Celery task with polling)
   */
  const runAsyncTool = async (endpoint, payload = {}) => {
    isRunning.value = true
    error.value = null
    result.value = null
    progress.value = 0
    currentTask.value = null

    try {
      // Start the task
      const startResponse = await axios.post(`/tools/${endpoint}`, payload)

      if (!startResponse.data.task_id) {
        throw new Error('No task_id returned from server')
      }

      currentTask.value = {
        id: startResponse.data.task_id,
        endpoint,
        status: 'started',
        message: startResponse.data.message
      }

      // Poll for completion
      return await pollTaskStatus(endpoint, startResponse.data.task_id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  /**
   * Poll task status until completion
   */
  const pollTaskStatus = (endpoint, taskId) => {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const response = await axios.get(`/tools/${endpoint}/${taskId}`)
          const taskStatus = response.data

          // Update progress
          if (taskStatus.progress !== undefined) {
            progress.value = taskStatus.progress
          }

          currentTask.value = {
            ...currentTask.value,
            status: taskStatus.status
          }

          switch (taskStatus.status) {
            case 'completed':
              isRunning.value = false
              progress.value = 100
              result.value = taskStatus.result
              resolve(taskStatus.result)
              break

            case 'failed':
              isRunning.value = false
              error.value = taskStatus.error || 'Task failed'
              reject(new Error(taskStatus.error || 'Task failed'))
              break

            case 'pending':
            case 'running':
              // Continue polling
              setTimeout(poll, POLL_INTERVAL)
              break

            default:
              // Unknown status, continue polling
              setTimeout(poll, POLL_INTERVAL)
          }
        } catch (err) {
          isRunning.value = false
          error.value = err.response?.data?.detail || err.message
          reject(err)
        }
      }

      // Start polling
      setTimeout(poll, 1000) // Initial delay before first poll
    })
  }

  /**
   * Cancel current task (if running)
   */
  const cancelTask = () => {
    // Note: Celery task cancellation would need backend support
    isRunning.value = false
    currentTask.value = null
    progress.value = 0
  }

  /**
   * Reset state
   */
  const reset = () => {
    isRunning.value = false
    progress.value = 0
    currentTask.value = null
    result.value = null
    error.value = null
  }

  // ========================================
  // Tool-specific methods
  // ========================================

  /**
   * Run extended health check
   */
  const runHealthCheck = async () => {
    isRunning.value = true
    error.value = null
    result.value = null

    try {
      const response = await axios.get('/tools/health-check')
      result.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      isRunning.value = false
    }
  }

  /**
   * Run rundown diff
   */
  const runRundownDiff = async (episode, versionA = null, versionB = null) => {
    return runSyncTool('rundown-diff', {
      episode,
      version_a: versionA,
      version_b: versionB
    })
  }

  /**
   * Run metadata validation
   */
  const runMetadataValidation = async (episode = null) => {
    return runAsyncTool('validate-metadata', { episode })
  }

  /**
   * Run duration reconciliation
   */
  const runDurationReconciliation = async (episode) => {
    return runAsyncTool('reconcile-durations', { episode })
  }

  /**
   * Generate production report
   */
  const generateProductionReport = async (episode, options = {}) => {
    return runAsyncTool('production-report', {
      episode,
      include_assets: options.includeAssets ?? true,
      include_scripts: options.includeScripts ?? true,
      include_timeline: options.includeTimeline ?? true
    })
  }

  return {
    // State
    isRunning,
    progress,
    currentTask,
    result,
    error,

    // Generic methods
    runSyncTool,
    runAsyncTool,
    cancelTask,
    reset,

    // Tool-specific methods
    runHealthCheck,
    runRundownDiff,
    runMetadataValidation,
    runDurationReconciliation,
    generateProductionReport
  }
}
