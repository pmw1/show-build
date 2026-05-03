/**
 * Global TTS Configuration Composable
 *
 * Provides centralized access to TTS settings and functionality
 * throughout the Show-Build application.
 * Supports both Fish Speech (preferred) and XTTS (legacy).
 */

import { ref, computed } from 'vue'
import { useUserPrefs } from './useUserPrefs'

// Global reactive state
const ttsConfig = ref({
  enabled: false,
  activeService: null, // 'fishspeech' or 'xtts'
  host: '',
  endpoint: '/tts_to_audio/',
  language: 'en',
  speed: 1.0,
  speaker: '',
  availableSpeakers: []
})

// Legacy alias for backward compatibility
// eslint-disable-next-line no-unused-vars
const xttsConfig = ttsConfig

const isLoading = ref(false)
const lastError = ref('')

// Global TTS composable (supports Fish Speech and XTTS)
export function useTts() {

  // Computed properties for easy access
  const isTtsEnabled = computed(() => ttsConfig.value.enabled)
  const activeService = computed(() => ttsConfig.value.activeService)
  const isFishSpeech = computed(() => ttsConfig.value.activeService === 'fishspeech')
  const ttsHost = computed(() => ttsConfig.value.host)
  const ttsEndpoint = computed(() => ttsConfig.value.endpoint)
  const selectedSpeaker = computed(() => ttsConfig.value.speaker)
  const availableSpeakers = computed(() => ttsConfig.value.availableSpeakers)

  // Full service URL
  const serviceUrl = computed(() => {
    if (!ttsConfig.value.host || !ttsConfig.value.endpoint) return ''
    return `${ttsConfig.value.host}${ttsConfig.value.endpoint}`
  })

  // Update TTS configuration
  function updateTtsConfig(newConfig) {
    ttsConfig.value = { ...ttsConfig.value, ...newConfig }

    // localStorage stays as the offline cache; per-user pref is the
    // cross-device source of truth.
    localStorage.setItem('tts-config', JSON.stringify(ttsConfig.value))
    try { useUserPrefs().set('tts.config', ttsConfig.value) } catch (e) { /* noop */ }

    console.log('TTS config updated:', ttsConfig.value)
  }

  // Enable/disable TTS
  function setTtsEnabled(enabled) {
    updateTtsConfig({ enabled })
  }

  // Load configuration from unified TTS API
  async function loadTtsConfig() {
    isLoading.value = true
    lastError.value = ''

    try {
      // Try to load from unified TTS config API first
      const response = await fetch('/api/settings/tts/config', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()

        if (data.success) {
          const activeService = data.active_service
          const serviceConfig = data.services?.[activeService] || {}

          updateTtsConfig({
            enabled: !!activeService,
            activeService: activeService,
            host: serviceConfig.host || '',
            speaker: serviceConfig.speaker || serviceConfig.reference_id || ''
          })

          console.log(`TTS loaded: ${activeService || 'none'} active`)
          return
        }
      }

      // Fallback to legacy XTTS config API
      const legacyResponse = await fetch('/api/settings/api-configs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        }
      })

      if (legacyResponse.ok) {
        const data = await legacyResponse.json()
        const fishConfig = data.data?.preproduction?.ai_services?.fishspeech
        const legacyXttsConfig = data.data?.preproduction?.ai_services?.xtts

        // Fish Speech takes priority
        if (fishConfig?.enabled) {
          updateTtsConfig({
            enabled: true,
            activeService: 'fishspeech',
            host: fishConfig.host || ''
          })
          return
        }

        if (legacyXttsConfig?.enabled) {
          updateTtsConfig({
            enabled: true,
            activeService: 'xtts',
            ...legacyXttsConfig
          })
          return
        }
      }

      // Fallback to per-user pref first (cross-device), then legacy localStorage.
      try {
        const fromPrefs = useUserPrefs().get('tts.config', null)
        if (fromPrefs && typeof fromPrefs === 'object') {
          ttsConfig.value = { ...ttsConfig.value, ...fromPrefs }
        } else {
          const saved = localStorage.getItem('tts-config')
          if (saved) {
            const parsedConfig = JSON.parse(saved)
            ttsConfig.value = { ...ttsConfig.value, ...parsedConfig }
          }
        }
      } catch (e) { /* noop */ }

    } catch (error) {
      console.error('Failed to load TTS config:', error)
      lastError.value = error.message

      // Try localStorage as fallback
      const saved = localStorage.getItem('tts-config')
      if (saved) {
        try {
          const parsedConfig = JSON.parse(saved)
          ttsConfig.value = { ...ttsConfig.value, ...parsedConfig }
        } catch (parseError) {
          console.error('Failed to parse saved TTS config:', parseError)
        }
      }
    } finally {
      isLoading.value = false
    }
  }

  // Fetch available speakers (unified endpoint)
  async function fetchSpeakers() {
    if (!ttsConfig.value.enabled) {
      console.log('TTS not enabled, skipping speaker fetch')
      return []
    }

    try {
      // Use unified TTS speakers endpoint
      const response = await fetch('/api/settings/tts/speakers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && Array.isArray(data.speakers)) {
          updateTtsConfig({ availableSpeakers: data.speakers })
          console.log(`Fetched ${data.speakers.length} speakers from ${data.service}`)
          return data.speakers
        }
      }
    } catch (error) {
      console.error('Failed to fetch TTS speakers:', error)
    }

    return []
  }

  // Text-to-speech function (unified endpoint - routes to Fish Speech or XTTS)
  async function synthesizeSpeech(text, options = {}) {
    const serviceName = ttsConfig.value.activeService || 'TTS'
    console.log(`synthesizeSpeech called [${serviceName}]:`, { text: text.substring(0, 50), options, isEnabled: isTtsEnabled.value })

    if (!isTtsEnabled.value) {
      console.error('TTS is not enabled:', ttsConfig.value)
      throw new Error('TTS is not enabled')
    }

    const requestOptions = {
      language: ttsConfig.value.language,
      speed: ttsConfig.value.speed,
      speaker: ttsConfig.value.speaker,
      // Fish Speech specific options
      reference_id: ttsConfig.value.speaker,
      ...options
    }

    console.log(`Calling unified TTS API [${serviceName}]:`, requestOptions)

    try {
      // Use unified TTS endpoint - backend routes to correct service
      const response = await fetch('/api/settings/tts/synthesize', {
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

      console.log(`TTS API response [${serviceName}]:`, response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`TTS API error response [${serviceName}]:`, errorText)
        throw new Error(`TTS API error: ${response.status} ${response.statusText}`)
      }

      const blob = await response.blob()
      console.log(`Received audio blob [${serviceName}]:`, blob.size, 'bytes, type:', blob.type)
      return blob
    } catch (error) {
      console.error(`Text-to-speech synthesis failed [${serviceName}]:`, error)
      throw error
    }
  }

  // Check if TTS is available and properly configured
  function isTtsAvailable() {
    return ttsConfig.value.enabled && ttsConfig.value.activeService
  }

  // Get current configuration summary
  function getConfigSummary() {
    return {
      enabled: ttsConfig.value.enabled,
      configured: isTtsAvailable(),
      activeService: ttsConfig.value.activeService,
      host: ttsConfig.value.host,
      speakerCount: ttsConfig.value.availableSpeakers.length,
      selectedSpeaker: ttsConfig.value.speaker,
      language: ttsConfig.value.language,
      speed: ttsConfig.value.speed
    }
  }

  return {
    // State
    ttsConfig: computed(() => ttsConfig.value),
    // Legacy alias
    xttsConfig: computed(() => ttsConfig.value),
    isLoading,
    lastError,

    // Computed
    isTtsEnabled,
    activeService,
    isFishSpeech,
    ttsHost,
    ttsEndpoint,
    selectedSpeaker,
    availableSpeakers,
    serviceUrl,
    // Legacy aliases
    isXttsEnabled: isTtsEnabled,
    xttsHost: ttsHost,
    xttsEndpoint: ttsEndpoint,

    // Methods
    updateTtsConfig,
    setTtsEnabled,
    loadTtsConfig,
    fetchSpeakers,
    synthesizeSpeech,
    isTtsAvailable,
    getConfigSummary,
    // Legacy aliases
    updateXttsConfig: updateTtsConfig,
    setXttsEnabled: setTtsEnabled,
    loadXttsConfig: loadTtsConfig,
    isXttsAvailable: isTtsAvailable
  }
}

// Backward-compat alias
export const useXtts = useTts

// Initialize on app start (call this in main.js or App.vue)
export async function initializeTts() {
  const { loadTtsConfig } = useTts()
  await loadTtsConfig()
}

// Legacy alias
export const initializeXtts = initializeTts
