/**
 * Content Origin Indicators — reads indicator color config from interface settings.
 * Provides CSS custom properties and helper functions for any component that
 * needs to apply indicator colors (LLM-generated, imported, approved, etc.).
 *
 * Singleton: settings are loaded once from localStorage and shared.
 */
import { computed } from 'vue'
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'

const DEFAULT_LLM_TEXT = '#7e57c2'
const DEFAULT_LLM_BORDER = '#7e57c2'

/** Darken a #rrggbb hex by `amount` (0..1) -> "#rrggbb". */
function darkenHex(hex, amount) {
  const h = (hex || '').replace('#', '')
  if (h.length !== 6) return hex
  const r = Math.max(0, Math.round(parseInt(h.slice(0, 2), 16) * (1 - amount)))
  const g = Math.max(0, Math.round(parseInt(h.slice(2, 4), 16) * (1 - amount)))
  const b = Math.max(0, Math.round(parseInt(h.slice(4, 6), 16) * (1 - amount)))
  const to2 = (n) => n.toString(16).padStart(2, '0')
  return `#${to2(r)}${to2(g)}${to2(b)}`
}

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

  // #47: the rundown busy/just-generated row color follows the user-configurable
  // "AI Generated" color from the Settings color picker (registry key
  // 'ai-generated'). Set it (and a darker trough for the pulse) as CSS vars so
  // the global llm-visual-feedback.css throb/linger uses the live color.
  const busy = resolveVuetifyColor(getColorValue('ai-generated')) || DEFAULT_LLM_BORDER
  document.documentElement.style.setProperty('--llm-busy-color', busy)
  document.documentElement.style.setProperty('--llm-busy-color-deep', darkenHex(busy, 0.35))
}
