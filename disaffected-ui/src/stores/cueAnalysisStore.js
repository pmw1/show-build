/**
 * cueAnalysisStore.js
 *
 * Universal Pinia store for managing asynchronous LLM analysis of cue block fields.
 * Supports ANY cue type (FSQ, SOT, PKG, VO, NAT, etc.) and ANY field requiring analysis.
 *
 * Analysis persists across component lifecycle - when user inserts cue during analysis,
 * the analysis continues in background and results are stored for later retrieval.
 *
 * @example
 * // Start analysis for FSQ quote field
 * const analysisId = await cueAnalysisStore.startAnalysis({
 *   cueType: 'FSQ',
 *   fieldName: 'quote',
 *   fieldValue: 'Here is the corrected text...',
 *   assetId: 'FSQ2BVX15C41J3P',
 *   analysisType: 'split_recommendation'
 * })
 *
 * // Check status later
 * const state = cueAnalysisStore.getAnalysisState(analysisId)
 * if (state === 'needs_review') {
 *   const recommendations = cueAnalysisStore.getRecommendations(analysisId)
 * }
 */

import { defineStore } from 'pinia'
import { useLLM } from '@/composables/useLLM'

export const useCueAnalysisStore = defineStore('cueAnalysis', {
  state: () => ({
    // Map<analysisId, AnalysisRecord>
    // analysisId format: {cueType}_{fieldName}_{assetId}_{timestamp}
    analyses: new Map(),

    // Track active analysis requests (for cancellation)
    activeRequests: new Map(), // Map<analysisId, AbortController>
  }),

  getters: {
    /**
     * Get analysis state for a specific cue/field
     * @param {string} analysisId - Unique analysis identifier
     * @returns {string|null} 'analyzing' | 'complete' | 'needs_review' | 'error' | null
     */
    getAnalysisState: (state) => (analysisId) => {
      const analysis = state.analyses.get(analysisId)
      return analysis ? analysis.state : null
    },

    /**
     * Get analysis recommendations for a specific cue/field
     * @param {string} analysisId - Unique analysis identifier
     * @returns {object|null} Recommendations object or null
     */
    getRecommendations: (state) => (analysisId) => {
      const analysis = state.analyses.get(analysisId)
      return analysis ? analysis.recommendations : null
    },

    /**
     * Get all analyses for a specific cue (by AssetID)
     * @param {string} assetId - Cue AssetID
     * @returns {Array} Array of analysis records for this cue
     */
    getAnalysesForCue: (state) => (assetId) => {
      const results = []
      state.analyses.forEach((analysis, id) => {
        if (analysis.assetId === assetId) {
          results.push({ id, ...analysis })
        }
      })
      return results
    },

    /**
     * Check if any analysis for a cue needs user review
     * @param {string} assetId - Cue AssetID
     * @returns {boolean} True if any field needs review
     */
    cueNeedsReview: (state) => (assetId) => {
      for (const analysis of state.analyses.values()) {
        if (analysis.assetId === assetId && analysis.state === 'needs_review') {
          return true
        }
      }
      return false
    },

    /**
     * Check if any analysis for a cue is still processing
     * @param {string} assetId - Cue AssetID
     * @returns {boolean} True if any field is analyzing
     */
    cueIsAnalyzing: (state) => (assetId) => {
      for (const analysis of state.analyses.values()) {
        if (analysis.assetId === assetId && analysis.state === 'analyzing') {
          return true
        }
      }
      return false
    }
  },

  actions: {
    /**
     * Generate unique analysis ID
     * @param {string} cueType - FSQ, SOT, PKG, etc.
     * @param {string} fieldName - quote, transcript, script, etc.
     * @param {string} assetId - Cue AssetID
     * @returns {string} Unique analysis ID
     */
    generateAnalysisId(cueType, fieldName, assetId) {
      const timestamp = Date.now()
      return `${cueType}_${fieldName}_${assetId}_${timestamp}`
    },

    /**
     * Start asynchronous LLM analysis for a cue field
     * @param {object} config - Analysis configuration
     * @param {string} config.cueType - FSQ, SOT, PKG, VO, NAT, etc.
     * @param {string} config.fieldName - Field being analyzed (quote, transcript, etc.)
     * @param {string} config.fieldValue - Current field value
     * @param {string} config.assetId - Cue AssetID
     * @param {string} config.analysisType - Type of analysis (split_recommendation, cleanup, enhancement, etc.)
     * @param {object} config.analysisParams - Additional parameters for analysis
     * @param {function} config.analyzerFunction - Custom analyzer function (optional)
     * @returns {Promise<string>} analysisId
     */
    async startAnalysis({
      cueType,
      fieldName,
      fieldValue,
      assetId,
      analysisType,
      analysisParams = {},
      analyzerFunction = null
    }) {
      const analysisId = this.generateAnalysisId(cueType, fieldName, assetId)

      // Create analysis record
      this.analyses.set(analysisId, {
        cueType,
        fieldName,
        fieldValue,
        assetId,
        analysisType,
        analysisParams,
        state: 'analyzing',
        recommendations: null,
        error: null,
        startedAt: new Date().toISOString(),
        completedAt: null
      })

      console.log(`🔍 Starting analysis: ${analysisId}`)
      console.log(`   Type: ${cueType}.${fieldName} (${analysisType})`)

      // Create abort controller for cancellation
      const abortController = new AbortController()
      this.activeRequests.set(analysisId, abortController)

      try {
        let recommendations = null

        // Use custom analyzer function if provided, otherwise use default LLM
        if (analyzerFunction && typeof analyzerFunction === 'function') {
          recommendations = await analyzerFunction(fieldValue, analysisParams, abortController.signal)
        } else {
          // Default LLM analysis using useLLM composable
          const llm = useLLM()
          recommendations = await llm.analyzeField({
            cueType,
            fieldName,
            fieldValue,
            analysisType,
            analysisParams,
            signal: abortController.signal
          })
        }

        // Analysis complete - update record
        const analysis = this.analyses.get(analysisId)
        if (analysis) {
          analysis.state = recommendations && this.shouldReview(recommendations) ? 'needs_review' : 'complete'
          analysis.recommendations = recommendations
          analysis.completedAt = new Date().toISOString()

          console.log(`✅ Analysis complete: ${analysisId}`)
          console.log(`   State: ${analysis.state}`)
          if (analysis.state === 'needs_review') {
            console.log(`   Recommendations: ${JSON.stringify(recommendations).substring(0, 100)}...`)
          }
        }

        // Clean up abort controller
        this.activeRequests.delete(analysisId)

        return analysisId

      } catch (error) {
        // Analysis failed - update record
        const analysis = this.analyses.get(analysisId)
        if (analysis) {
          if (error.name === 'AbortError') {
            console.log(`⏸️ Analysis cancelled: ${analysisId}`)
            analysis.state = 'cancelled'
          } else {
            console.error(`❌ Analysis error: ${analysisId}`, error)
            analysis.state = 'error'
            analysis.error = error.message
            analysis.completedAt = new Date().toISOString()
          }
        }

        // Clean up abort controller
        this.activeRequests.delete(analysisId)

        throw error
      }
    },

    /**
     * Determine if recommendations require user review
     * @param {object} recommendations - Analysis recommendations
     * @returns {boolean} True if user should review
     */
    shouldReview(recommendations) {
      if (!recommendations) return false

      // FSQ split recommendations
      if (recommendations.shouldSplit || recommendations.splitRecommendations) {
        return true
      }

      // Generic action recommendations
      if (recommendations.action && recommendations.action !== 'none') {
        return true
      }

      // Any modifications suggested
      if (recommendations.modifications && recommendations.modifications.length > 0) {
        return true
      }

      return false
    },

    /**
     * Cancel ongoing analysis
     * @param {string} analysisId - Analysis to cancel
     */
    cancelAnalysis(analysisId) {
      const abortController = this.activeRequests.get(analysisId)
      if (abortController) {
        console.log(`⏸️ Cancelling analysis: ${analysisId}`)
        abortController.abort()
        this.activeRequests.delete(analysisId)
      }

      // Update analysis state
      const analysis = this.analyses.get(analysisId)
      if (analysis && analysis.state === 'analyzing') {
        analysis.state = 'cancelled'
        analysis.completedAt = new Date().toISOString()
      }
    },

    /**
     * Cancel all analyses for a specific cue
     * @param {string} assetId - Cue AssetID
     */
    cancelAnalysesForCue(assetId) {
      this.analyses.forEach((analysis, id) => {
        if (analysis.assetId === assetId && analysis.state === 'analyzing') {
          this.cancelAnalysis(id)
        }
      })
    },

    /**
     * Mark analysis as reviewed/resolved
     * @param {string} analysisId - Analysis ID
     */
    markReviewed(analysisId) {
      const analysis = this.analyses.get(analysisId)
      if (analysis) {
        console.log(`✅ Marked as reviewed: ${analysisId}`)
        analysis.state = 'complete'
      }
    },

    /**
     * Delete analysis record
     * @param {string} analysisId - Analysis ID to remove
     */
    deleteAnalysis(analysisId) {
      this.cancelAnalysis(analysisId) // Cancel if still running
      this.analyses.delete(analysisId)
      console.log(`🗑️ Deleted analysis: ${analysisId}`)
    },

    /**
     * Clean up old completed analyses (older than 24 hours)
     */
    cleanupOldAnalyses() {
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
      let cleaned = 0

      this.analyses.forEach((analysis, id) => {
        if (analysis.completedAt) {
          const completedDate = new Date(analysis.completedAt)
          if (completedDate < oneDayAgo) {
            this.analyses.delete(id)
            cleaned++
          }
        }
      })

      if (cleaned > 0) {
        console.log(`🧹 Cleaned up ${cleaned} old analysis records`)
      }
    }
  }
})
