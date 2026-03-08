/**
 * Segment Lock Composable
 * Manages pessimistic locking for rundown item segments to prevent concurrent editing conflicts.
 *
 * Usage:
 * const { isLocked, lockInfo, isMyLock, checkLockStatus, acquireLock, releaseLock } = useSegmentLock()
 */
import { ref, onUnmounted } from 'vue'
import axios from 'axios'

// Heartbeat interval in milliseconds (15 seconds)
const HEARTBEAT_INTERVAL_MS = 15000

export function useSegmentLock() {
  // ============================================================
  // SEGMENT LOCKING DISABLED — all calls are no-ops that succeed
  // Remove this flag (and restore original code below) to re-enable
  // ============================================================
  const LOCKING_DISABLED = true

  // Lock state
  const isLocked = ref(false)
  const lockInfo = ref({
    lockedBy: '',
    lockedById: null,
    lockedAt: null,
    expiresAt: null
  })
  const isMyLock = ref(false)
  const currentAssetId = ref(null)
  const isAcquiring = ref(false)
  const error = ref(null)

  // Heartbeat interval reference
  let heartbeatInterval = null

  /**
   * Format relative time from ISO date string
   */
  const formatRelativeTime = (isoString) => {
    if (!isoString) return ''
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'just now'
    if (diffMins === 1) return '1 minute ago'
    if (diffMins < 60) return `${diffMins} minutes ago`

    const diffHours = Math.floor(diffMins / 60)
    if (diffHours === 1) return '1 hour ago'
    return `${diffHours} hours ago`
  }

  /**
   * Check lock status for a rundown item
   */
  const checkLockStatus = async (assetId) => {
    if (LOCKING_DISABLED) return { locked: false }

    if (!assetId) {
      error.value = 'No asset ID provided'
      return { locked: false }
    }

    try {
      const response = await axios.get(`/api/locks/${assetId}`)
      const data = response.data

      isLocked.value = data.locked
      isMyLock.value = data.is_my_lock || false

      if (data.locked) {
        lockInfo.value = {
          lockedBy: data.locked_by || 'Unknown',
          lockedById: data.locked_by_id,
          lockedAt: data.locked_at,
          expiresAt: data.expires_at
        }
      } else {
        lockInfo.value = {
          lockedBy: '',
          lockedById: null,
          lockedAt: null,
          expiresAt: null
        }
      }

      error.value = null
      return data
    } catch (err) {
      console.error('[SegmentLock] Failed to check lock status:', err)
      error.value = err.message
      return { locked: false, error: err.message }
    }
  }

  /**
   * Acquire a lock on a rundown item
   */
  const acquireLock = async (assetId) => {
    if (LOCKING_DISABLED) {
      currentAssetId.value = assetId
      return { success: true }
    }

    if (!assetId) {
      error.value = 'No asset ID provided'
      return { success: false, error: 'No asset ID provided' }
    }

    if (isAcquiring.value) {
      return { success: false, error: 'Lock acquisition already in progress' }
    }

    isAcquiring.value = true

    try {
      const response = await axios.post(`/api/locks/${assetId}/acquire`)
      const data = response.data

      if (data.success) {
        currentAssetId.value = assetId
        isLocked.value = true
        isMyLock.value = true
        lockInfo.value = {
          lockedBy: 'You',
          lockedById: null,
          lockedAt: new Date().toISOString(),
          expiresAt: data.expires_at
        }

        // Start heartbeat
        startHeartbeat(assetId)

        error.value = null
        return { success: true }
      }

      return { success: false, error: 'Unknown error' }
    } catch (err) {
      console.error('[SegmentLock] Failed to acquire lock:', err)

      // Handle 423 Locked response
      if (err.response && err.response.status === 423) {
        const detail = err.response.data.detail || {}
        isLocked.value = true
        isMyLock.value = false
        lockInfo.value = {
          lockedBy: detail.locked_by || 'Another user',
          lockedById: detail.locked_by_id,
          lockedAt: detail.locked_at,
          expiresAt: detail.expires_at
        }

        return {
          success: false,
          locked: true,
          lockedBy: detail.locked_by
        }
      }

      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      isAcquiring.value = false
    }
  }

  /**
   * Release the current lock
   */
  const releaseLock = async () => {
    if (LOCKING_DISABLED) {
      currentAssetId.value = null
      return { success: true }
    }

    // Stop heartbeat first
    stopHeartbeat()

    if (!currentAssetId.value) {
      return { success: true, message: 'No lock to release' }
    }

    try {
      const response = await axios.post(`/api/locks/${currentAssetId.value}/release`)

      // Reset state
      currentAssetId.value = null
      isLocked.value = false
      isMyLock.value = false
      lockInfo.value = {
        lockedBy: '',
        lockedById: null,
        lockedAt: null,
        expiresAt: null
      }

      error.value = null
      return response.data
    } catch (err) {
      console.error('[SegmentLock] Failed to release lock:', err)
      error.value = err.message

      // Even if release fails, clear local state
      currentAssetId.value = null
      isLocked.value = false
      isMyLock.value = false

      return { success: false, error: err.message }
    }
  }

  /**
   * Send heartbeat to extend lock TTL
   */
  const sendHeartbeat = async (assetId) => {
    if (!assetId) return

    try {
      await axios.post(`/api/locks/${assetId}/heartbeat`)
    } catch (err) {
      console.error('[SegmentLock] Heartbeat failed:', err)

      // If heartbeat fails, the lock may have expired
      if (err.response && err.response.status === 404) {
        stopHeartbeat()
        isMyLock.value = false
        currentAssetId.value = null
        error.value = 'Lock expired'
      }
    }
  }

  /**
   * Start heartbeat interval
   */
  const startHeartbeat = (assetId) => {
    stopHeartbeat() // Clear any existing interval

    heartbeatInterval = setInterval(() => {
      sendHeartbeat(assetId)
    }, HEARTBEAT_INTERVAL_MS)
  }

  /**
   * Stop heartbeat interval
   */
  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
  }

  /**
   * Release all locks held by current user
   */
  const releaseAllLocks = async () => {
    stopHeartbeat()

    try {
      const response = await axios.delete('/api/locks/my-locks')
      currentAssetId.value = null
      isLocked.value = false
      isMyLock.value = false
      return response.data
    } catch (err) {
      console.error('[SegmentLock] Failed to release all locks:', err)
      return { success: false, error: err.message }
    }
  }

  /**
   * Get all locks held by current user
   */
  const getMyLocks = async () => {
    try {
      const response = await axios.get('/api/locks/my-locks')
      return response.data.locks || []
    } catch (err) {
      console.error('[SegmentLock] Failed to get my locks:', err)
      return []
    }
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopHeartbeat()
    // Note: We don't automatically release the lock on unmount
    // because the user may navigate away temporarily.
    // Use releaseLock() explicitly when needed.
  })

  return {
    // State
    isLocked,
    lockInfo,
    isMyLock,
    isAcquiring,
    error,
    currentAssetId,

    // Methods
    checkLockStatus,
    acquireLock,
    releaseLock,
    releaseAllLocks,
    getMyLocks,
    formatRelativeTime,

    // Internal (exposed for advanced use)
    startHeartbeat,
    stopHeartbeat
  }
}
