import { ref } from 'vue'
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'

const showFlash = ref(false)
const flashColor = ref('#2196F3')
const flashMessage = ref('')
const flashMessageStyle = ref('normal') // 'normal' or 'urgent'

/**
 * Screen flash composable for modal triggers and abort messages
 * Uses cue type colors from theme configuration
 */
export function useScreenFlash() {

  /**
   * Flash screen with cue type color
   * @param {string} cueType - The cue type (SOT, VO, NAT, etc.)
   * @param {number} duration - Flash duration in ms (default 300)
   */
  const flashForCue = (cueType, duration = 300) => {
    const colorName = getColorValue(cueType.toLowerCase())
    const color = resolveVuetifyColor(colorName)

    flashColor.value = color
    flashMessage.value = ''
    flashMessageStyle.value = 'normal'
    showFlash.value = true

    setTimeout(() => {
      showFlash.value = false
    }, duration)
  }

  /**
   * Flash urgent message (like ABORT)
   * @param {string} message - Message to display
   * @param {string} color - Color for the flash (default red)
   * @param {number} duration - Flash duration in ms (default 500)
   */
  const flashUrgent = (message, color = '#F44336', duration = 500) => {
    flashColor.value = color
    flashMessage.value = message
    flashMessageStyle.value = 'urgent'
    showFlash.value = true

    setTimeout(() => {
      showFlash.value = false
      flashMessage.value = ''
    }, duration)
  }

  /**
   * Clear any active flash
   */
  const clearFlash = () => {
    showFlash.value = false
    flashMessage.value = ''
  }

  /**
   * Flash blue 3 times fast to indicate successful save
   * Used after autosave debounce completes
   */
  const flashSaveSuccess = async () => {
    const saveColor = '#2196F3' // Blue
    flashMessage.value = ''
    flashMessageStyle.value = 'normal'

    // Flash 3 times fast (80ms on, 80ms off)
    for (let i = 0; i < 3; i++) {
      flashColor.value = saveColor
      showFlash.value = true
      await new Promise(resolve => setTimeout(resolve, 80))
      showFlash.value = false
      await new Promise(resolve => setTimeout(resolve, 80))
    }
  }

  return {
    showFlash,
    flashColor,
    flashMessage,
    flashMessageStyle,
    flashForCue,
    flashUrgent,
    clearFlash,
    flashSaveSuccess
  }
}
