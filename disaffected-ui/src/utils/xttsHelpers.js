/**
 * XTTS Helper Utilities
 *
 * Common utility functions for integrating XTTS functionality
 * throughout the Show-Build application.
 */

import { useXtts } from '@/composables/useXtts'

/**
 * Check if XTTS is available for use
 * @returns {boolean} True if XTTS is enabled and configured
 */
export function isXttsReady() {
  const { isXttsAvailable } = useXtts()
  return isXttsAvailable()
}

/**
 * Get XTTS configuration summary for UI display
 * @returns {object} Configuration summary
 */
export function getXttsStatus() {
  const { getConfigSummary } = useXtts()
  return getConfigSummary()
}

/**
 * Generate speech from text using XTTS
 * @param {string} text - Text to convert to speech
 * @param {object} options - Optional TTS parameters
 * @returns {Promise<Blob>} Audio blob
 */
export async function generateSpeech(text, options = {}) {
  const { synthesizeSpeech } = useXtts()
  return await synthesizeSpeech(text, options)
}

/**
 * Play generated speech audio
 * @param {string} text - Text to convert and play
 * @param {object} options - Optional TTS parameters
 */
export async function playText(text, options = {}) {
  if (!isXttsReady()) {
    console.warn('XTTS not available for text-to-speech')
    return
  }

  try {
    const audioBlob = await generateSpeech(text, options)
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)

    audio.onended = () => {
      URL.revokeObjectURL(audioUrl)
    }

    await audio.play()
  } catch (error) {
    console.error('Failed to play text:', error)
    throw error
  }
}

/**
 * Get available speakers for UI dropdowns
 * @returns {Array} Array of speaker objects
 */
export function getAvailableSpeakers() {
  const { availableSpeakers } = useXtts()
  return availableSpeakers.value
}

/**
 * Show XTTS status in UI (for debugging/admin views)
 * @returns {string} Human-readable status
 */
export function getXttsStatusText() {
  const status = getXttsStatus()

  if (!status.enabled) {
    return '❌ XTTS Disabled'
  }

  if (!status.configured) {
    return '⚠️ XTTS Not Configured'
  }

  const speakerText = status.selectedSpeaker ?
    ` (${status.selectedSpeaker})` :
    ' (No speaker selected)'

  return `✅ XTTS Ready${speakerText} - ${status.speakerCount} speakers available`
}

/**
 * Add TTS button to any element
 * @param {HTMLElement} element - Element to add button to
 * @param {string} text - Text to speak when clicked
 * @param {object} options - TTS options
 */
export function addTtsButton(element, text, options = {}) {
  if (!isXttsReady()) return

  const button = document.createElement('button')
  button.innerHTML = '🔊'
  button.title = 'Play with Text-to-Speech'
  button.style.cssText = `
    margin-left: 8px;
    padding: 4px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #f9f9f9;
    cursor: pointer;
    font-size: 14px;
  `

  button.onclick = async (e) => {
    e.preventDefault()
    e.stopPropagation()

    try {
      button.innerHTML = '⏸️'
      button.disabled = true
      await playText(text, options)
    } catch (error) {
      console.error('TTS playback failed:', error)
      alert('Text-to-speech failed: ' + error.message)
    } finally {
      button.innerHTML = '🔊'
      button.disabled = false
    }
  }

  element.appendChild(button)
  return button
}

/**
 * Vue directive for adding TTS to elements
 * Usage: v-tts="'Text to speak'"
 */
export const ttsDirective = {
  mounted(el, binding) {
    if (binding.value && isXttsReady()) {
      addTtsButton(el, binding.value)
    }
  },
  updated(el, binding) {
    if (binding.value !== binding.oldValue) {
      // Remove old button and add new one
      const oldButton = el.querySelector('button[title="Play with Text-to-Speech"]')
      if (oldButton) {
        oldButton.remove()
      }

      if (binding.value && isXttsReady()) {
        addTtsButton(el, binding.value)
      }
    }
  }
}