/**
 * Content Origin Indicators — reads indicator color config from interface settings.
 * Provides CSS custom properties and helper functions for any component that
 * needs to apply indicator colors (LLM-generated, imported, approved, etc.).
 *
 * Singleton: settings are loaded once from localStorage and shared.
 */
import { computed } from 'vue'

const DEFAULT_LLM_TEXT = '#7e57c2'
const DEFAULT_LLM_BORDER = '#7e57c2'

function loadIndicators() {
  try {
    const saved = localStorage.getItem('showbuild_interface_settings')
    if (saved) {
      const settings = JSON.parse(saved)
      if (Array.isArray(settings.contentIndicators)) {
        return settings.contentIndicators
      }
    }
  } catch (e) { /* ignore */ }
  return null
}

function getIndicator(key) {
  const indicators = loadIndicators()
  if (!indicators) return null
  return indicators.find(i => i.key === key) || null
}

/**
 * Get colors for a specific indicator by key.
 * Returns { textColor, borderColor } with defaults for llm_generated.
 */
export function getIndicatorColors(key = 'llm_generated') {
  const ind = getIndicator(key)
  if (ind) return { textColor: ind.textColor, borderColor: ind.borderColor }
  if (key === 'llm_generated') return { textColor: DEFAULT_LLM_TEXT, borderColor: DEFAULT_LLM_BORDER }
  return { textColor: '#9e9e9e', borderColor: '#9e9e9e' }
}

/**
 * Composable that returns reactive indicator colors (re-reads on each call).
 */
export function useContentIndicators() {
  const llmColors = computed(() => getIndicatorColors('llm_generated'))

  return {
    llmTextColor: computed(() => llmColors.value.textColor),
    llmBorderColor: computed(() => llmColors.value.borderColor),
    getIndicatorColors
  }
}

/**
 * Apply indicator CSS custom properties to the document root.
 * Call once from App.vue or on settings save.
 */
export function applyIndicatorCSSVars() {
  const llm = getIndicatorColors('llm_generated')
  document.documentElement.style.setProperty('--llm-indicator-text', llm.textColor)
  document.documentElement.style.setProperty('--llm-indicator-border', llm.borderColor)
  // Overlay uses the border color at 85% opacity
  const hex = llm.borderColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  document.documentElement.style.setProperty('--llm-indicator-overlay', `rgba(${r}, ${g}, ${b}, 0.85)`)
}
