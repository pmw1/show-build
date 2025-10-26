/**
 * Composable for requiring an episode to be selected before performing actions
 *
 * Usage:
 * const { requireEpisode, showEpisodeModal, episodeModalAction } = useRequireEpisode()
 *
 * // In your method:
 * const episode = requireEpisode(this.currentEpisode, 'Upload Image')
 * if (!episode) return  // Modal will be shown automatically
 * // Continue with action using episode...
 */

import { ref } from 'vue'

// Global state for the episode requirement modal
const showEpisodeModal = ref(false)
const episodeModalAction = ref('')
const pendingCallback = ref(null)

export function useRequireEpisode() {
  /**
   * Check if an episode is selected, show modal if not
   * @param {string} currentEpisode - The currently selected episode
   * @param {string} actionDescription - Description of the action requiring episode
   * @param {Function} callback - Optional callback to execute after episode selection
   * @returns {string|null} Episode number if available, null if modal shown
   */
  const requireEpisode = (currentEpisode, actionDescription = 'perform this action', callback = null) => {
    // Check if we have a valid episode
    if (currentEpisode && currentEpisode.trim() !== '') {
      console.log('✅ Episode requirement satisfied:', currentEpisode)
      return currentEpisode
    }

    // Check sessionStorage as fallback
    const savedEpisode = sessionStorage.getItem('currentEpisodeId')
    if (savedEpisode && savedEpisode.trim() !== '') {
      console.warn('⚠️ Using sessionStorage episode (may be stale):', savedEpisode)
      return savedEpisode.padStart(4, '0')
    }

    // No episode available - show modal
    console.warn('⚠️ No episode selected - showing selection modal')
    episodeModalAction.value = actionDescription
    pendingCallback.value = callback
    showEpisodeModal.value = true
    return null
  }

  /**
   * Handle episode selection from modal
   * @param {string} selectedEpisode - The episode number selected by user
   */
  const handleEpisodeSelected = (selectedEpisode) => {
    console.log('✅ Episode selected from modal:', selectedEpisode)

    // Execute pending callback if provided
    if (pendingCallback.value && typeof pendingCallback.value === 'function') {
      console.log('🔄 Executing pending callback with episode:', selectedEpisode)
      pendingCallback.value(selectedEpisode)
      pendingCallback.value = null
    }
  }

  /**
   * Handle modal cancellation
   */
  const handleModalCancelled = () => {
    console.log('❌ Episode selection cancelled')
    pendingCallback.value = null
    episodeModalAction.value = ''
  }

  /**
   * Clear the modal state
   */
  const clearModalState = () => {
    showEpisodeModal.value = false
    episodeModalAction.value = ''
    pendingCallback.value = null
  }

  return {
    requireEpisode,
    showEpisodeModal,
    episodeModalAction,
    handleEpisodeSelected,
    handleModalCancelled,
    clearModalState
  }
}
