/**
 * useWaveform.js - Audio Waveform Visualization Composable
 *
 * Extracts audio data from video using Web Audio API and generates
 * waveform visualization data for broadcast-style editing interface.
 */

import { ref, onBeforeUnmount } from 'vue'

export function useWaveform() {
  // State
  const waveformData = ref([])
  const isAnalyzing = ref(false)
  const analysisProgress = ref(0)
  const audioContext = ref(null)
  const sourceNode = ref(null)
  // True when the last extraction found the file has NO audio track (vs a
  // genuine decode error). Lets callers offer "convert to VO" instead of
  // surfacing a scary EncodingError.
  const hasNoAudio = ref(false)

  /**
   * Extract waveform data from video element
   * @param {HTMLVideoElement} videoElement - The video element to analyze
   * @param {number} samples - Number of waveform samples to generate (default: 500)
   * @returns {Promise<Array>} Array of normalized amplitude values (0-1)
   */
  const extractWaveform = async (videoElement, samples = 500) => {
    if (!videoElement || !videoElement.src) {
      console.warn('[Waveform] No video source available')
      return []
    }

    isAnalyzing.value = true
    analysisProgress.value = 0
    hasNoAudio.value = false

    try {
      // Create Audio Context if not exists
      if (!audioContext.value) {
        audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
      }

      // Fetch video as array buffer
      console.log('[Waveform] Fetching video audio data...')
      const response = await fetch(videoElement.src)
      const arrayBuffer = await response.arrayBuffer()
      analysisProgress.value = 30

      // Decode audio data
      console.log('[Waveform] Decoding audio...')
      let audioBuffer
      try {
        audioBuffer = await audioContext.value.decodeAudioData(arrayBuffer)
      } catch (decodeErr) {
        // decodeAudioData throws an EncodingError when the file has no audio
        // track (nothing to decode). Treat that as "no audio" rather than a
        // hard failure — callers can offer to convert the clip to a VO.
        console.warn('[Waveform] decodeAudioData failed — treating as no audio track')
        hasNoAudio.value = true
        waveformData.value = []
        analysisProgress.value = 0
        isAnalyzing.value = false
        return []
      }
      analysisProgress.value = 60

      // A decoded buffer with zero channels also means no usable audio.
      if (!audioBuffer || audioBuffer.numberOfChannels === 0) {
        hasNoAudio.value = true
        waveformData.value = []
        analysisProgress.value = 0
        isAnalyzing.value = false
        return []
      }

      // Get audio channel data (use first channel for mono/stereo)
      const channelData = audioBuffer.getChannelData(0)
      const duration = audioBuffer.duration
      const sampleRate = audioBuffer.sampleRate

      console.log(`[Waveform] Audio duration: ${duration.toFixed(2)}s, Sample rate: ${sampleRate}Hz`)

      // Generate waveform by sampling amplitude at intervals
      const blockSize = Math.floor(channelData.length / samples)
      const waveform = []

      for (let i = 0; i < samples; i++) {
        const start = i * blockSize
        const end = start + blockSize

        // Calculate RMS (Root Mean Square) for this block
        let sum = 0
        for (let j = start; j < end && j < channelData.length; j++) {
          sum += channelData[j] * channelData[j]
        }
        const rms = Math.sqrt(sum / blockSize)

        // Normalize to 0-1 range (with some amplification for visibility)
        const normalized = Math.min(1.0, rms * 3.0)
        waveform.push(normalized)

        // Update progress
        if (i % 50 === 0) {
          analysisProgress.value = 60 + Math.floor((i / samples) * 40)
        }
      }

      waveformData.value = waveform
      analysisProgress.value = 100
      isAnalyzing.value = false

      console.log(`[Waveform] Generated ${waveform.length} samples`)
      return waveform

    } catch (error) {
      console.error('[Waveform] Error extracting waveform:', error)
      isAnalyzing.value = false
      analysisProgress.value = 0
      return []
    }
  }

  /**
   * Clear waveform data and cleanup
   */
  const clearWaveform = () => {
    waveformData.value = []
    analysisProgress.value = 0
    isAnalyzing.value = false

    // Disconnect source node if exists
    if (sourceNode.value) {
      try {
        sourceNode.value.disconnect()
      } catch (e) {
        // Already disconnected
      }
      sourceNode.value = null
    }
  }

  /**
   * Cleanup on unmount
   */
  onBeforeUnmount(() => {
    clearWaveform()

    // Close audio context
    if (audioContext.value && audioContext.value.state !== 'closed') {
      audioContext.value.close()
      audioContext.value = null
    }
  })

  return {
    // State
    waveformData,
    isAnalyzing,
    analysisProgress,
    hasNoAudio,

    // Methods
    extractWaveform,
    clearWaveform
  }
}
