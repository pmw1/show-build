/**
 * useAsyncAnalysis.js
 *
 * Reusable composable for managing asynchronous LLM analysis of cue fields.
 * Works with cueAnalysisStore to provide persistent analysis across component lifecycle.
 *
 * @example
 * // In any modal component
 * import { useAsyncAnalysis } from '@/composables/useAsyncAnalysis'
 *
 * const { analyzeField, getState, cancel } = useAsyncAnalysis()
 *
 * // Start analysis
 * const analysisId = await analyzeField({
 *   cueType: 'FSQ',
 *   fieldName: 'quote',
 *   fieldValue: quoteText.value,
 *   assetId: assetId.value,
 *   analysisType: 'split_recommendation',
 *   analyzerFunction: customAnalyzer
 * })
 *
 * // Check state
 * const state = getState(analysisId) // 'analyzing' | 'needs_review' | 'complete' | 'error'
 *
 * // Cancel if needed
 * cancel(analysisId)
 */

import { ref, computed } from 'vue'
import { useCueAnalysisStore } from '@/stores/cueAnalysisStore'

export function useAsyncAnalysis() {
  const cueAnalysisStore = useCueAnalysisStore()

  // Track current analysis IDs for this component instance
  const currentAnalysisIds = ref([])

  /**
   * Start persistent analysis for a cue field
   * Analysis continues even if component unmounts
   *
   * @param {object} config - Analysis configuration
   * @param {string} config.cueType - FSQ, SOT, PKG, VO, NAT, etc.
   * @param {string} config.fieldName - Field being analyzed
   * @param {string} config.fieldValue - Current field value
   * @param {string} config.assetId - Cue AssetID (optional, generated if not provided)
   * @param {string} config.analysisType - Type of analysis
   * @param {object} config.analysisParams - Additional parameters
   * @param {function} config.analyzerFunction - Custom analyzer (optional)
   * @returns {Promise<string>} analysisId
   */
  async function analyzeField({
    cueType,
    fieldName,
    fieldValue,
    assetId,
    analysisType,
    analysisParams = {},
    analyzerFunction = null
  }) {
    console.log(`🔍 useAsyncAnalysis: Starting analysis for ${cueType}.${fieldName}`)

    try {
      const analysisId = await cueAnalysisStore.startAnalysis({
        cueType,
        fieldName,
        fieldValue,
        assetId,
        analysisType,
        analysisParams,
        analyzerFunction
      })

      // Track this analysis ID
      currentAnalysisIds.value.push(analysisId)

      return analysisId

    } catch (error) {
      console.error(`❌ useAsyncAnalysis: Analysis failed`, error)
      throw error
    }
  }

  /**
   * Get current analysis state
   * @param {string} analysisId - Analysis ID
   * @returns {string|null} 'analyzing' | 'complete' | 'needs_review' | 'error' | 'cancelled' | null
   */
  function getState(analysisId) {
    return cueAnalysisStore.getAnalysisState(analysisId)
  }

  /**
   * Get analysis recommendations
   * @param {string} analysisId - Analysis ID
   * @returns {object|null} Recommendations object or null
   */
  function getRecommendations(analysisId) {
    return cueAnalysisStore.getRecommendations(analysisId)
  }

  /**
   * Cancel specific analysis
   * @param {string} analysisId - Analysis ID to cancel
   */
  function cancel(analysisId) {
    cueAnalysisStore.cancelAnalysis(analysisId)

    // Remove from tracked IDs
    const index = currentAnalysisIds.value.indexOf(analysisId)
    if (index > -1) {
      currentAnalysisIds.value.splice(index, 1)
    }
  }

  /**
   * Cancel all analyses started by this component instance
   */
  function cancelAll() {
    console.log(`⏸️ useAsyncAnalysis: Cancelling ${currentAnalysisIds.value.length} analyses`)

    currentAnalysisIds.value.forEach(id => {
      cueAnalysisStore.cancelAnalysis(id)
    })

    currentAnalysisIds.value = []
  }

  /**
   * Get all analyses for a specific cue
   * @param {string} assetId - Cue AssetID
   * @returns {Array} Analysis records
   */
  function getAnalysesForCue(assetId) {
    return cueAnalysisStore.getAnalysesForCue(assetId)
  }

  /**
   * Check if cue needs review
   * @param {string} assetId - Cue AssetID
   * @returns {boolean} True if any field needs review
   */
  function cueNeedsReview(assetId) {
    return cueAnalysisStore.cueNeedsReview(assetId)
  }

  /**
   * Check if cue is analyzing
   * @param {string} assetId - Cue AssetID
   * @returns {boolean} True if any field is analyzing
   */
  function cueIsAnalyzing(assetId) {
    return cueAnalysisStore.cueIsAnalyzing(assetId)
  }

  /**
   * Mark analysis as reviewed/resolved
   * @param {string} analysisId - Analysis ID
   */
  function markReviewed(analysisId) {
    cueAnalysisStore.markReviewed(analysisId)

    // Remove from tracked IDs
    const index = currentAnalysisIds.value.indexOf(analysisId)
    if (index > -1) {
      currentAnalysisIds.value.splice(index, 1)
    }
  }

  /**
   * Delete analysis record
   * @param {string} analysisId - Analysis ID
   */
  function deleteAnalysis(analysisId) {
    cueAnalysisStore.deleteAnalysis(analysisId)

    // Remove from tracked IDs
    const index = currentAnalysisIds.value.indexOf(analysisId)
    if (index > -1) {
      currentAnalysisIds.value.splice(index, 1)
    }
  }

  // Computed property for component-wide analysis state
  const hasActiveAnalyses = computed(() => {
    return currentAnalysisIds.value.some(id => {
      const state = getState(id)
      return state === 'analyzing'
    })
  })

  const hasPendingReviews = computed(() => {
    return currentAnalysisIds.value.some(id => {
      const state = getState(id)
      return state === 'needs_review'
    })
  })

  return {
    // Core methods
    analyzeField,
    getState,
    getRecommendations,
    cancel,
    cancelAll,

    // Cue-level queries
    getAnalysesForCue,
    cueNeedsReview,
    cueIsAnalyzing,

    // Analysis management
    markReviewed,
    deleteAnalysis,

    // Component state
    currentAnalysisIds,
    hasActiveAnalyses,
    hasPendingReviews
  }
}
