/**
 * TTS Helper Utilities
 *
 * Common utility functions for integrating TTS functionality
 * throughout the Show-Build application.
 * Supports both Fish Speech (preferred) and XTTS (legacy).
 */

import { useTts } from '@/composables/useTts'

/**
 * Check if TTS is available for use
 * @returns {boolean} True if TTS is enabled and configured
 */
export function isTtsReady() {
  const { isTtsAvailable } = useTts()
  return isTtsAvailable()
}

// Legacy alias
export const isXttsReady = isTtsReady

/**
 * Get TTS configuration summary for UI display
 * @returns {object} Configuration summary
 */
export function getTtsStatus() {
  const { getConfigSummary } = useTts()
  return getConfigSummary()
}

// Legacy alias
export const getXttsStatus = getTtsStatus

/**
 * Generate speech from text using TTS
 * @param {string} text - Text to convert to speech
 * @param {object} options - Optional TTS parameters
 * @returns {Promise<Blob>} Audio blob
 */
export async function generateSpeech(text, options = {}) {
  const { synthesizeSpeech } = useTts()
  return await synthesizeSpeech(text, options)
}

/**
 * Play generated speech audio
 * @param {string} text - Text to convert and play
 * @param {object} options - Optional TTS parameters
 */
export async function playText(text, options = {}) {
  if (!isTtsReady()) {
    console.warn('TTS not available for text-to-speech')
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
  const { availableSpeakers } = useTts()
  return availableSpeakers.value
}

/**
 * Show TTS status in UI (for debugging/admin views)
 * @returns {string} Human-readable status
 */
export function getTtsStatusText() {
  const status = getTtsStatus()

  if (!status.enabled) {
    return 'TTS Disabled'
  }

  if (!status.configured) {
    return 'TTS Not Configured'
  }

  const speakerText = status.selectedSpeaker ?
    ` (${status.selectedSpeaker})` :
    ' (No speaker selected)'

  const serviceName = status.activeService === 'fishspeech' ? 'Fish Speech' : 'TTS'
  return `${serviceName} Ready${speakerText} - ${status.speakerCount} speakers available`
}

// Legacy alias
export const getXttsStatusText = getTtsStatusText

/**
 * Add TTS button to any element
 * @param {HTMLElement} element - Element to add button to
 * @param {string} text - Text to speak when clicked
 * @param {object} options - TTS options
 */
export function addTtsButton(element, text, options = {}) {
  if (!isTtsReady()) return

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
    if (binding.value && isTtsReady()) {
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

      if (binding.value && isTtsReady()) {
        addTtsButton(el, binding.value)
      }
    }
  }
}
