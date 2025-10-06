// Global reference to the standard notification component
let standardNotificationComponent = null

// Global function to show standard notification from anywhere
export function notifyUserStandard(message, color = '#2196F3', duration = 2000, targetElement = null, attachToPanel = false) {
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

// Common color presets for convenience
export const NOTIFICATION_COLORS = {
  SUCCESS: '#4CAF50',
  ERROR: '#F44336',
  WARNING: '#FF9800',
  INFO: '#2196F3',
  PRIMARY: '#1976D2',
  PURPLE: '#9C27B0',
  TEAL: '#009688',
  INDIGO: '#3F51B5',
  PINK: '#E91E63',
  AMBER: '#FFC107'
}
