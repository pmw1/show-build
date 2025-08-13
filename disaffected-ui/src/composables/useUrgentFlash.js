// Global reference to the flash component
let urgentFlashComponent = null

// Global function to show urgent flash from anywhere
export function showUrgentFlash(message, backgroundColor = 'red') {
  if (urgentFlashComponent) {
    urgentFlashComponent.showFlash(message, backgroundColor)
  } else {
    console.warn('UrgentFlash component not initialized. Make sure it is mounted in your App.vue')
  }
}

// Hook for setting up the flash component
export function useUrgentFlash() {
  const registerFlashComponent = (component) => {
    urgentFlashComponent = component
  }
  
  return {
    registerFlashComponent,
    showUrgentFlash
  }
}

// Direct export for global access
window.showUrgentFlash = showUrgentFlash