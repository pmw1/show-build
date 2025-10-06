/**
 * Global XTTS Configuration Composable
 *
 * Provides centralized access to XTTS settings and functionality
 * throughout the Show-Build application.
 */

import { ref, computed } from 'vue'

// Global reactive state
const xttsConfig = ref({
  enabled: false,
  host: '',
  endpoint: '/tts_to_audio/',
  language: 'en',
  speed: 1.0,
  speaker: '',
  availableSpeakers: []
})

const isLoading = ref(false)
const lastError = ref('')

// Global XTTS composable
export function useXtts() {

  // Computed properties for easy access
  const isXttsEnabled = computed(() => xttsConfig.value.enabled)
  const xttsHost = computed(() => xttsConfig.value.host)
  const xttsEndpoint = computed(() => xttsConfig.value.endpoint)
  const selectedSpeaker = computed(() => xttsConfig.value.speaker)
  const availableSpeakers = computed(() => xttsConfig.value.availableSpeakers)

  // Full service URL
  const serviceUrl = computed(() => {
    if (!xttsConfig.value.host || !xttsConfig.value.endpoint) return ''
    return `${xttsConfig.value.host}${xttsConfig.value.endpoint}`
  })

  // Update XTTS configuration
  function updateXttsConfig(newConfig) {
    xttsConfig.value = { ...xttsConfig.value, ...newConfig }

    // Save to localStorage for persistence
    localStorage.setItem('xtts-config', JSON.stringify(xttsConfig.value))

    console.log('XTTS config updated:', xttsConfig.value)
  }

  // Enable/disable XTTS
  function setXttsEnabled(enabled) {
    updateXttsConfig({ enabled })
  }

  // Load configuration from API or localStorage
  async function loadXttsConfig() {
    isLoading.value = true
    lastError.value = ''

    try {
      // Try to load from API first
      const response = await fetch('/api/settings/api-configs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        const apiXtts = data.data?.preproduction?.ai_services?.xtts

        if (apiXtts) {
          updateXttsConfig(apiXtts)
          return
        }
      }

      // Fallback to localStorage
      const saved = localStorage.getItem('xtts-config')
      if (saved) {
        const parsedConfig = JSON.parse(saved)
        xttsConfig.value = { ...xttsConfig.value, ...parsedConfig }
      }

    } catch (error) {
      console.error('Failed to load XTTS config:', error)
      lastError.value = error.message

      // Try localStorage as fallback
      const saved = localStorage.getItem('xtts-config')
      if (saved) {
        try {
          const parsedConfig = JSON.parse(saved)
          xttsConfig.value = { ...xttsConfig.value, ...parsedConfig }
        } catch (parseError) {
          console.error('Failed to parse saved XTTS config:', parseError)
        }
      }
    } finally {
      isLoading.value = false
    }
  }

  // Fetch available speakers
  async function fetchSpeakers() {
    if (!xttsConfig.value.enabled) {
      console.log('XTTS not enabled, skipping speaker fetch')
      return []
    }

    try {
      const response = await fetch('/api/settings/xtts/speakers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && Array.isArray(data.speakers)) {
          updateXttsConfig({ availableSpeakers: data.speakers })
          return data.speakers
        }
      }
    } catch (error) {
      console.error('Failed to fetch XTTS speakers:', error)
    }

    return []
  }

  // Text-to-speech function
  async function synthesizeSpeech(text, options = {}) {
    console.log('🔊 synthesizeSpeech called:', { text: text.substring(0, 50), options, isEnabled: isXttsEnabled.value })

    if (!isXttsEnabled.value) {
      console.error('❌ XTTS is not enabled:', xttsConfig.value)
      throw new Error('XTTS is not enabled')
    }

    const requestOptions = {
      language: xttsConfig.value.language,
      speed: xttsConfig.value.speed,
      speaker: xttsConfig.value.speaker,
      ...options
    }

    console.log('📡 Calling XTTS API with:', requestOptions)

    try {
      // Use existing backend proxy to avoid mixed content issues
      const response = await fetch('/api/settings/xtts/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          text,
          ...requestOptions
        })
      })

      console.log('📥 XTTS API response:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ XTTS API error response:', errorText)
        throw new Error(`XTTS API error: ${response.status} ${response.statusText}`)
      }

      const blob = await response.blob()
      console.log('✅ Received audio blob:', blob.size, 'bytes, type:', blob.type)
      return blob
    } catch (error) {
      console.error('❌ Text-to-speech synthesis failed:', error)
      throw error
    }
  }

  // Check if XTTS is available and properly configured
  function isXttsAvailable() {
    return (
      xttsConfig.value.enabled &&
      xttsConfig.value.host &&
      xttsConfig.value.endpoint
    )
  }

  // Get current configuration summary
  function getConfigSummary() {
    return {
      enabled: xttsConfig.value.enabled,
      configured: isXttsAvailable(),
      host: xttsConfig.value.host,
      speakerCount: xttsConfig.value.availableSpeakers.length,
      selectedSpeaker: xttsConfig.value.speaker,
      language: xttsConfig.value.language,
      speed: xttsConfig.value.speed
    }
  }

  return {
    // State
    xttsConfig: computed(() => xttsConfig.value),
    isLoading,
    lastError,

    // Computed
    isXttsEnabled,
    xttsHost,
    xttsEndpoint,
    selectedSpeaker,
    availableSpeakers,
    serviceUrl,

    // Methods
    updateXttsConfig,
    setXttsEnabled,
    loadXttsConfig,
    fetchSpeakers,
    synthesizeSpeech,
    isXttsAvailable,
    getConfigSummary
  }
}

// Initialize on app start (call this in main.js or App.vue)
export async function initializeXtts() {
  const { loadXttsConfig } = useXtts()
  await loadXttsConfig()
}