/**
 * useSegmentLLMData.js - Composable for Segment LLM Preprocessing
 *
 * Provides functions for managing pre-extracted LLM data for segments.
 * Part of the LLM Preprocessing Layer (UFDP-compliant).
 *
 * Features:
 * - Fetch and cache prechewed LLM data per segment
 * - Trigger extraction with UFDP operation tracking
 * - Stale status checking
 * - Batch extraction for multiple segments
 * - Integration with useLLMState for visual feedback
 *
 * @see UNIVERSAL_LLM_FRAMEWORK_UFDP.md for architecture details
 */

import { ref, reactive, computed } from 'vue'
import axios from 'axios'
import { notifyUserStandard, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'

// Cache for LLM data to reduce API calls
const llmDataCache = reactive(new Map())

// Track active extraction operations
const activeExtractions = reactive(new Set())

export function useSegmentLLMData() {
  const loading = ref(false)
  const error = ref(null)

  /**
   * Get auth headers for API requests
   */
  function getAuthHeaders() {
    const token = localStorage.getItem('auth-token')
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  /**
   * Get LLM data for a segment (rundown item)
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @param {boolean} useCache - Use cached data if available (default: true)
   * @returns {Promise<Object>} LLM data object or null
   */
  async function getLLMData(rundownItemId, useCache = true) {
    // Check cache first
    const cacheKey = `item_${rundownItemId}`
    if (useCache && llmDataCache.has(cacheKey)) {
      const cached = llmDataCache.get(cacheKey)
      // Cache valid for 5 minutes
      if (Date.now() - cached.timestamp < 5 * 60 * 1000) {
        return cached.data
      }
    }

    try {
      loading.value = true
      error.value = null

      const response = await axios.get(`/api/segments/${rundownItemId}/llm-data`, {
        headers: getAuthHeaders()
      })

      if (response.data.success) {
        // Cache the result
        llmDataCache.set(cacheKey, {
          data: response.data,
          timestamp: Date.now()
        })
        return response.data
      }

      return null
    } catch (err) {
      console.error(`Failed to get LLM data for item ${rundownItemId}:`, err)
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Trigger LLM extraction for a segment
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @param {Object} options - Extraction options
   * @param {string} options.model - Optional model override
   * @param {boolean} options.force - Force re-extraction
   * @param {boolean} options.notify - Show notification on completion
   * @returns {Promise<Object>} Extraction result
   */
  async function extractLLMData(rundownItemId, options = {}) {
    const { model, force = false, notify = true } = options

    // Prevent duplicate extractions
    if (activeExtractions.has(rundownItemId)) {
      console.warn(`Extraction already in progress for item ${rundownItemId}`)
      return null
    }

    try {
      loading.value = true
      error.value = null
      activeExtractions.add(rundownItemId)

      const response = await axios.post(
        `/api/segments/${rundownItemId}/extract`,
        { model, force },
        { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
      )

      if (response.data.success) {
        // Update cache
        const cacheKey = `item_${rundownItemId}`
        llmDataCache.set(cacheKey, {
          data: {
            success: true,
            has_data: true,
            stale: false,
            data: response.data.data
          },
          timestamp: Date.now()
        })

        if (notify) {
          notifyUserStandard({
            message: 'Entity extraction completed',
            color: NOTIFICATION_COLORS.SUCCESS,
            timeout: 3000
          })
        }

        return response.data
      }

      return null
    } catch (err) {
      console.error(`Failed to extract LLM data for item ${rundownItemId}:`, err)
      error.value = err.message

      if (notify) {
        notifyUserStandard({
          message: `Extraction failed: ${err.message}`,
          color: NOTIFICATION_COLORS.ERROR,
          timeout: 5000
        })
      }

      throw err
    } finally {
      loading.value = false
      activeExtractions.delete(rundownItemId)
    }
  }

  /**
   * Check if a segment's LLM data is stale
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @returns {Promise<Object>} Stale status object
   */
  async function checkStale(rundownItemId) {
    try {
      const response = await axios.get(`/api/segments/${rundownItemId}/stale`, {
        headers: getAuthHeaders()
      })

      return response.data
    } catch (err) {
      console.error(`Failed to check stale status for item ${rundownItemId}:`, err)
      return { stale: true, reason: 'check_failed' }
    }
  }

  /**
   * Check if LLM data is stale (sync version using cache)
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @returns {boolean} True if stale or no data
   */
  function isStale(rundownItemId) {
    const cacheKey = `item_${rundownItemId}`
    const cached = llmDataCache.get(cacheKey)

    if (!cached || !cached.data) return true
    if (cached.data.stale) return true
    if (!cached.data.has_data) return true

    return false
  }

  /**
   * Batch extract LLM data for multiple segments
   *
   * @param {number[]} rundownItemIds - Array of rundown item IDs
   * @param {Object} options - Extraction options
   * @returns {Promise<Object>} Batch results summary
   */
  async function batchExtract(rundownItemIds, options = {}) {
    const { model, force = false, notify = true } = options

    try {
      loading.value = true
      error.value = null

      if (notify) {
        notifyUserStandard({
          message: `Starting extraction for ${rundownItemIds.length} segments...`,
          color: NOTIFICATION_COLORS.INFO,
          timeout: 3000
        })
      }

      const response = await axios.post(
        '/api/segments/batch-extract',
        { rundown_item_ids: rundownItemIds, model, force },
        { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
      )

      if (response.data.success) {
        const results = response.data.results

        // Clear cache for processed items
        rundownItemIds.forEach(id => {
          llmDataCache.delete(`item_${id}`)
        })

        if (notify) {
          const msg = `Extraction complete: ${results.completed}/${results.total} succeeded`
          notifyUserStandard({
            message: msg,
            color: results.failed > 0 ? NOTIFICATION_COLORS.WARNING : NOTIFICATION_COLORS.SUCCESS,
            timeout: 5000
          })
        }

        return results
      }

      return null
    } catch (err) {
      console.error('Batch extraction failed:', err)
      error.value = err.message

      if (notify) {
        notifyUserStandard({
          message: `Batch extraction failed: ${err.message}`,
          color: NOTIFICATION_COLORS.ERROR,
          timeout: 5000
        })
      }

      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get aggregated LLM context for an episode
   *
   * @param {string} episodeNumber - The episode number
   * @returns {Promise<Object>} Episode LLM context
   */
  async function getEpisodeLLMContext(episodeNumber) {
    try {
      loading.value = true
      error.value = null

      const response = await axios.get(
        `/api/segments/episode/${episodeNumber}/llm-context`,
        { headers: getAuthHeaders() }
      )

      if (response.data.success) {
        return response.data.context
      }

      return null
    } catch (err) {
      console.error(`Failed to get episode LLM context for ${episodeNumber}:`, err)
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Get list of stale segments
   *
   * @param {string} episodeNumber - Optional episode filter
   * @returns {Promise<Object[]>} List of stale segment info
   */
  async function getStaleSegments(episodeNumber = null) {
    try {
      const params = episodeNumber ? { episode_number: episodeNumber } : {}

      const response = await axios.get('/api/segments/llm-data/stale', {
        headers: getAuthHeaders(),
        params
      })

      if (response.data.success) {
        return response.data.stale_items
      }

      return []
    } catch (err) {
      console.error('Failed to get stale segments:', err)
      return []
    }
  }

  /**
   * Delete LLM data for a segment (allows re-extraction)
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @returns {Promise<boolean>} Success status
   */
  async function deleteLLMData(rundownItemId) {
    try {
      const response = await axios.delete(
        `/api/segments/${rundownItemId}/llm-data`,
        { headers: getAuthHeaders() }
      )

      if (response.data.success) {
        // Clear cache
        llmDataCache.delete(`item_${rundownItemId}`)
        return true
      }

      return false
    } catch (err) {
      console.error(`Failed to delete LLM data for item ${rundownItemId}:`, err)
      return false
    }
  }

  /**
   * Update LLM data manually
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated data or null
   */
  async function updateLLMData(rundownItemId, updates) {
    try {
      const response = await axios.put(
        `/api/segments/${rundownItemId}/llm-data`,
        updates,
        { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
      )

      if (response.data.success) {
        // Update cache
        const cacheKey = `item_${rundownItemId}`
        llmDataCache.set(cacheKey, {
          data: {
            success: true,
            has_data: true,
            stale: false,
            data: response.data.data
          },
          timestamp: Date.now()
        })

        return response.data.data
      }

      return null
    } catch (err) {
      console.error(`Failed to update LLM data for item ${rundownItemId}:`, err)
      throw err
    }
  }

  /**
   * Clear the LLM data cache
   *
   * @param {number} rundownItemId - Optional specific item to clear
   */
  function clearCache(rundownItemId = null) {
    if (rundownItemId) {
      llmDataCache.delete(`item_${rundownItemId}`)
    } else {
      llmDataCache.clear()
    }
  }

  /**
   * Check if extraction is in progress for a segment
   *
   * @param {number} rundownItemId - The rundown item database ID
   * @returns {boolean}
   */
  function isExtracting(rundownItemId) {
    return activeExtractions.has(rundownItemId)
  }

  // Computed for active extraction count
  const activeExtractionCount = computed(() => activeExtractions.size)

  return {
    // State
    loading,
    error,
    activeExtractionCount,

    // Core functions
    getLLMData,
    extractLLMData,
    checkStale,
    isStale,
    batchExtract,
    getEpisodeLLMContext,
    getStaleSegments,
    deleteLLMData,
    updateLLMData,
    clearCache,
    isExtracting
  }
}
