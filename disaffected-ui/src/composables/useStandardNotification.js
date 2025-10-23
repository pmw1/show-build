// Global reference to the standard notification component
let standardNotificationComponent = null

// Global function to show standard notification from anywhere
export function notifyUserStandard(message, color = '#2196F3', duration = 3000, targetElement = null, attachToPanel = false) {
  if (standardNotificationComponent) {
    standardNotificationComponent.notifyUserStandard(message, color, duration, targetElement, attachToPanel)
  } else {
    console.warn('StandardNotification component not initialized. Make sure it is mounted in your App.vue')
  }
}

// Hook for setting up the notification component
export function useStandardNotification() {
  const registerNotificationComponent = (component) => {
    standardNotificationComponent = component
  }

  return {
    registerNotificationComponent,
    notifyUserStandard
  }
}

// Direct export for global access
window.notifyUserStandard = notifyUserStandard

// Import centralized color system
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'

// Common color presets - now pulling from centralized database config
// Using getters to dynamically fetch colors from database
export const NOTIFICATION_COLORS = {
  // Status colors from database (with fallbacks) - resolved to hex codes
  get SUCCESS() { return resolveVuetifyColor(getColorValue('success')) || '#4CAF50' },
  get ERROR() { return resolveVuetifyColor(getColorValue('error')) || '#F44336' },
  get WARNING() { return resolveVuetifyColor(getColorValue('warning')) || '#FF9800' },
  get INFO() { return resolveVuetifyColor(getColorValue('info')) || '#2196F3' },

  // Rundown item type colors from database (with fallbacks) - resolved to hex codes
  get SEGMENT() { return resolveVuetifyColor(getColorValue('segment')) || '#1976D2' },
  get AD() { return resolveVuetifyColor(getColorValue('ad')) || '#4CAF50' },
  get PROMO() { return resolveVuetifyColor(getColorValue('promo')) || '#9C27B0' },
  get CTA() { return resolveVuetifyColor(getColorValue('cta')) || '#FF9800' },
  get TEASE() { return resolveVuetifyColor(getColorValue('tease')) || '#E91E63' },
  get COLDOPEN() { return resolveVuetifyColor(getColorValue('coldopen')) || '#F44336' },
  get OUTRO() { return resolveVuetifyColor(getColorValue('outro')) || '#009688' },

  // LLM operation colors from database (with fallbacks) - resolved to hex codes
  get ANALYZING() { return resolveVuetifyColor(getColorValue('llm-analyzing')) || '#9C27B0' },
  get GENERATING() { return resolveVuetifyColor(getColorValue('llm-generating')) || '#2196F3' },
  get MODIFYING() { return resolveVuetifyColor(getColorValue('llm-modifying')) || '#FF9800' },
  get EXTRACTING() { return resolveVuetifyColor(getColorValue('llm-extracting')) || '#4CAF50' },
  get COMPOSING() { return resolveVuetifyColor(getColorValue('llm-composing')) || '#E91E63' },
  get REFACTORING() { return resolveVuetifyColor(getColorValue('llm-refactoring')) || '#FFC107' },

  // Fallback static colors (for backward compatibility)
  PRIMARY: '#1976D2',
  PURPLE: '#9C27B0',
  TEAL: '#009688',
  INDIGO: '#3F51B5',
  PINK: '#E91E63',
  AMBER: '#FFC107'
}
