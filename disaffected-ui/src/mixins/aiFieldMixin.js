/**
 * aiFieldMixin.js
 *
 * Shared mixin for modal components that have fields requiring LLM analysis.
 * Provides consistent behavior for:
 * - Debounced analysis triggering (2-second delay)
 * - Visual state management (purple border = analyzing, red = needs review)
 * - Analysis cancellation on component unmount
 * - Recommendation display and handling
 *
 * Works with useAsyncAnalysis composable and cueAnalysisStore.
 *
 * @example
 * // In FsqModal.vue, SotModal.vue, etc.
 * import aiFieldMixin from '@/mixins/aiFieldMixin'
 *
 * export default {
 *   mixins: [aiFieldMixin],
 *
 *   methods: {
 *     handleQuoteInput() {
 *       // Trigger analysis with 2-second debounce
 *       this.triggerAnalysis('quote', this.quote, {
 *         cueType: 'FSQ',
 *         analysisType: 'split_recommendation',
 *         analyzerFunction: this.analyzeQuoteSplitting
 *       })
 *     }
 *   }
 * }
 */

import { useAsyncAnalysis } from '@/composables/useAsyncAnalysis'

export default {
  data() {
    return {
      // Analysis state for fields in this modal
      aiAnalysisState: {}, // { fieldName: 'analyzing' | 'needs_review' | 'complete' | 'error' }
      aiRecommendations: {}, // { fieldName: recommendationsObject }
      aiAnalysisIds: {}, // { fieldName: analysisId }

      // Debounce timers for each field
      aiDebounceTimers: {}, // { fieldName: timeoutId }

      // Visual state flags (for backward compatibility)
      aiAnalyzing: false, // True if ANY field is analyzing
      aiAnalysisComplete: false, // True if ANY field has completed
      aiRecommendationExpanded: [] // Backward compat for FSQ
    }
  },

  computed: {
    /**
     * Check if any field is currently analyzing
     */
    hasActiveAnalysis() {
      return Object.values(this.aiAnalysisState).some(state => state === 'analyzing')
    },

    /**
     * Check if any field needs review
     */
    hasReviewPending() {
      return Object.values(this.aiAnalysisState).some(state => state === 'needs_review')
    },

    /**
     * Get border style for field based on analysis state
     * @param {string} fieldName - Field to get style for
     * @returns {object} Style object for v-bind:style
     */
    getFieldBorderStyle() {
      return (fieldName) => {
        const state = this.aiAnalysisState[fieldName]

        if (state === 'analyzing') {
          // Purple border while analyzing
          return {
            border: '7px solid #9C27B0',
            borderRadius: '4px'
          }
        } else if (state === 'needs_review') {
          // Red border when recommendations need review
          return {
            border: '7px solid #D32F2F',
            borderRadius: '4px'
          }
        }

        return {}
      }
    }
  },

  methods: {
    /**
     * Trigger analysis for a field with debouncing
     * @param {string} fieldName - Field to analyze (quote, transcript, script, etc.)
     * @param {string} fieldValue - Current field value
     * @param {object} config - Analysis configuration
     * @param {string} config.cueType - FSQ, SOT, PKG, etc.
     * @param {string} config.analysisType - Type of analysis
     * @param {string} config.assetId - Cue AssetID (optional)
     * @param {object} config.analysisParams - Additional params (optional)
     * @param {function} config.analyzerFunction - Custom analyzer (optional)
     * @param {number} debounceMs - Debounce delay in milliseconds (default: 2000)
     */
    triggerAnalysis(fieldName, fieldValue, config, debounceMs = 2000) {
      // Clear existing debounce timer for this field
      if (this.aiDebounceTimers[fieldName]) {
        clearTimeout(this.aiDebounceTimers[fieldName])
      }

      // Cancel existing analysis for this field if still running
      if (this.aiAnalysisIds[fieldName]) {
        const { cancel } = useAsyncAnalysis()
        cancel(this.aiAnalysisIds[fieldName])
        delete this.aiAnalysisIds[fieldName]
      }

      // Reset state while waiting for debounce
      this.aiAnalysisState[fieldName] = null
      this.aiRecommendations[fieldName] = null

      // Set new debounce timer
      this.aiDebounceTimers[fieldName] = setTimeout(async () => {
        await this.startAnalysis(fieldName, fieldValue, config)
      }, debounceMs)

      console.log(`⏱️ Analysis debounce started for ${fieldName} (${debounceMs}ms)`)
    },

    /**
     * Start analysis immediately (called after debounce)
     * @param {string} fieldName - Field to analyze
     * @param {string} fieldValue - Field value
     * @param {object} config - Analysis configuration
     */
    async startAnalysis(fieldName, fieldValue, config) {
      const { analyzeField } = useAsyncAnalysis()

      // Set analyzing state
      this.aiAnalysisState[fieldName] = 'analyzing'
      this.aiAnalyzing = true // Backward compat flag

      console.log(`🔍 Starting analysis for field: ${fieldName}`)

      try {
        const analysisId = await analyzeField({
          cueType: config.cueType,
          fieldName: fieldName,
          fieldValue: fieldValue,
          assetId: config.assetId || this.generateTempAssetId?.(),
          analysisType: config.analysisType,
          analysisParams: config.analysisParams || {},
          analyzerFunction: config.analyzerFunction || null
        })

        // Store analysis ID for this field
        this.aiAnalysisIds[fieldName] = analysisId

        // Poll for completion (analysis runs in background)
        this.pollAnalysisState(fieldName, analysisId)

      } catch (error) {
        console.error(`❌ Analysis failed for ${fieldName}:`, error)
        this.aiAnalysisState[fieldName] = 'error'
        this.aiAnalyzing = false
      }
    },

    /**
     * Poll analysis state until complete
     * @param {string} fieldName - Field being analyzed
     * @param {string} analysisId - Analysis ID to poll
     */
    pollAnalysisState(fieldName, analysisId) {
      const asyncAnalysis = useAsyncAnalysis()

      const checkState = () => {
        const state = asyncAnalysis.getState(analysisId)

        if (!state || state === 'analyzing') {
          // Still analyzing, check again in 500ms
          setTimeout(checkState, 500)
          return
        }

        // Analysis complete
        this.aiAnalysisState[fieldName] = state
        this.aiAnalyzing = false
        this.aiAnalysisComplete = true

        if (state === 'needs_review') {
          const recommendations = asyncAnalysis.getRecommendations(analysisId)
          this.aiRecommendations[fieldName] = recommendations

          console.log(`✅ Analysis complete for ${fieldName}: needs review`)
          console.log(`   Recommendations:`, recommendations)

          // Backward compat for FSQ
          if (fieldName === 'quote' && recommendations?.splitRecommendations) {
            this.aiRecommendationExpanded = recommendations.splitRecommendations
          }

        } else if (state === 'complete') {
          console.log(`✅ Analysis complete for ${fieldName}: no action needed`)
        } else if (state === 'error') {
          console.error(`❌ Analysis error for ${fieldName}`)
        }
      }

      // Start polling
      checkState()
    },

    /**
     * Cancel analysis for a specific field
     * @param {string} fieldName - Field to cancel
     */
    cancelFieldAnalysis(fieldName) {
      // Clear debounce timer
      if (this.aiDebounceTimers[fieldName]) {
        clearTimeout(this.aiDebounceTimers[fieldName])
        delete this.aiDebounceTimers[fieldName]
      }

      // Cancel analysis
      if (this.aiAnalysisIds[fieldName]) {
        const { cancel } = useAsyncAnalysis()
        cancel(this.aiAnalysisIds[fieldName])
        delete this.aiAnalysisIds[fieldName]
      }

      // Reset state
      this.aiAnalysisState[fieldName] = null
      this.aiRecommendations[fieldName] = null

      // Update global flags
      this.aiAnalyzing = this.hasActiveAnalysis

      console.log(`⏸️ Cancelled analysis for ${fieldName}`)
    },

    /**
     * Cancel all active analyses in this modal
     */
    cancelAllAnalyses() {
      Object.keys(this.aiAnalysisState).forEach(fieldName => {
        this.cancelFieldAnalysis(fieldName)
      })

      this.aiAnalyzing = false
      this.aiAnalysisComplete = false
      this.aiRecommendationExpanded = []

      console.log(`⏸️ Cancelled all analyses`)
    },

    /**
     * Reset all analysis state (call when modal closes)
     */
    resetAnalysisState() {
      // Don't cancel - let analyses continue in background
      // Just reset local UI state

      this.aiAnalysisState = {}
      this.aiRecommendations = {}
      this.aiAnalysisIds = {}
      this.aiDebounceTimers = {}
      this.aiAnalyzing = false
      this.aiAnalysisComplete = false
      this.aiRecommendationExpanded = []

      console.log(`🔄 Reset analysis state`)
    },

    /**
     * Get visual class for field based on analysis state
     * @param {string} fieldName - Field name
     * @returns {string} CSS class name
     */
    getAnalysisClass(fieldName) {
      const state = this.aiAnalysisState[fieldName]

      if (state === 'analyzing') return 'ai-analyzing'
      if (state === 'needs_review') return 'ai-needs-review'
      if (state === 'complete') return 'ai-complete'
      if (state === 'error') return 'ai-error'

      return ''
    }
  },

  beforeUnmount() {
    // Clear debounce timers
    Object.values(this.aiDebounceTimers).forEach(timer => {
      clearTimeout(timer)
    })

    // Don't cancel analyses - they should persist
    // Just clean up local state
    console.log(`🧹 aiFieldMixin: Component unmounting, analyses will continue in background`)
  }
}
