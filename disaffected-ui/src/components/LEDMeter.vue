<template>
  <v-card class="led-meter-card">
    <v-card-title>Audio Levels</v-card-title>
    <v-card-text>
      <v-row>
        <v-col
          v-for="(track, index) in tracks"
          :key="index"
          cols="12"
          sm="6"
          md="3"
        >
          <div class="led-meter-container">
            <div class="led-meter-label">{{ track.label }}</div>

            <!-- LED Bar Container -->
            <div class="led-bar-wrapper">
              <!-- LED segments -->
              <div
                v-for="segment in ledSegments"
                :key="segment.value"
                class="led-segment"
                :class="{
                  'led-active': track.level >= segment.value,
                  'led-green': segment.value <= 60,
                  'led-yellow': segment.value > 60 && segment.value <= 85,
                  'led-red': segment.value > 85
                }"
              >
                <div class="led-bar"></div>
              </div>

              <!-- Peak indicator -->
              <div
                v-if="track.peak > 0"
                class="peak-indicator"
                :style="{ bottom: `${track.peak}%` }"
              ></div>

              <!-- Scale markings -->
              <div class="scale-marks">
                <div class="scale-mark" style="bottom: 0%">
                  <span>-∞</span>
                </div>
                <div class="scale-mark" style="bottom: 25%">
                  <span>-20</span>
                </div>
                <div class="scale-mark" style="bottom: 50%">
                  <span>-10</span>
                </div>
                <div class="scale-mark" style="bottom: 75%">
                  <span>0</span>
                </div>
                <div class="scale-mark" style="bottom: 100%">
                  <span>+6</span>
                </div>
              </div>
            </div>

            <!-- Numeric display -->
            <div class="level-display">
              <span :class="{ 'level-warn': track.level > 85, 'level-caution': track.level > 60 }">
                {{ track.level.toFixed(1) }} dB
              </span>
              <span v-if="track.peak > 0" class="peak-value">
                Peak: {{ track.peak.toFixed(1) }}
              </span>
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- Controls -->
      <v-row class="mt-4">
        <v-col>
          <v-btn @click="startRealAudio" :disabled="testing" color="success" size="small">
            <v-icon left>mdi-microphone</v-icon>
            Real Audio
          </v-btn>
          <v-btn @click="startTest" :disabled="testing" color="primary" size="small" class="ml-2">
            <v-icon left>mdi-play</v-icon>
            Test Mode
          </v-btn>
          <v-btn @click="stopTest" :disabled="!testing" color="error" size="small" class="ml-2">
            <v-icon left>mdi-stop</v-icon>
            Stop
          </v-btn>
          <v-btn @click="resetPeaks" size="small" class="ml-2">
            <v-icon left>mdi-refresh</v-icon>
            Reset
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, onUnmounted } from 'vue'

export default {
  name: 'LEDMeter',
  props: {
    audioStream: {
      type: MediaStream,
      default: null
    }
  },
  setup() {
    // Create LED segments (bottom to top) - 8-bit style with fewer, chunkier segments
    const ledSegments = []
    for (let i = 0; i <= 100; i += 5) { // Bigger steps for 8-bit look
      ledSegments.push({ value: i })
    }

    const tracks = ref([
      { label: 'Track 1', level: 0, peak: 0 },
      { label: 'Track 2', level: 0, peak: 0 },
      { label: 'Track 3', level: 0, peak: 0 },
      { label: 'Track 4', level: 0, peak: 0 }
    ])

    const testing = ref(false)
    let testInterval = null
    let peakDecayInterval = null
    let audioContext = null
    let analyser = null
    let dataArray = null
    let animationFrameId = null

    const startRealAudio = async () => {
      try {
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

        // Create audio context and analyser
        audioContext = new (window.AudioContext || window.webkitAudioContext)()
        analyser = audioContext.createAnalyser()
        analyser.fftSize = 2048
        const bufferLength = analyser.frequencyBinCount
        dataArray = new Uint8Array(bufferLength)

        // Connect stream to analyser
        const source = audioContext.createMediaStreamSource(stream)
        source.connect(analyser)

        testing.value = true

        // Analyze audio in real-time
        const updateLevels = () => {
          if (!testing.value) return

          analyser.getByteFrequencyData(dataArray)

          // Split frequency spectrum into 4 bands (like a graphic equalizer)
          const bandSize = Math.floor(bufferLength / 4)

          for (let i = 0; i < 4; i++) {
            const start = i * bandSize
            const end = start + bandSize

            // Calculate average level for this frequency band
            let sum = 0
            for (let j = start; j < end; j++) {
              sum += dataArray[j]
            }
            const average = sum / bandSize

            // Convert to 0-100 scale (255 -> 100)
            const level = (average / 255) * 100

            tracks.value[i].level = level

            // Update peak
            if (level > tracks.value[i].peak) {
              tracks.value[i].peak = level
            }
          }

          animationFrameId = requestAnimationFrame(updateLevels)
        }

        updateLevels()

        // Peak decay
        peakDecayInterval = setInterval(() => {
          tracks.value.forEach(track => {
            if (track.peak > 0) {
              track.peak = Math.max(0, track.peak - 0.5)
            }
          })
        }, 100)

        // Update track labels to show frequency bands
        tracks.value[0].label = 'Bass (20-250Hz)'
        tracks.value[1].label = 'Low-Mid (250-2kHz)'
        tracks.value[2].label = 'Mid-High (2k-8kHz)'
        tracks.value[3].label = 'Treble (8k-20kHz)'

      } catch (error) {
        console.error('Failed to access microphone:', error)
        alert('Microphone access denied. Please grant permission to use audio meters.')
      }
    }

    const startTest = () => {
      testing.value = true

      testInterval = setInterval(() => {
        tracks.value.forEach((track, index) => {
          // Simulate audio levels with some variation
          const base = 30 + Math.sin(Date.now() / 1000 + index) * 20
          const noise = Math.random() * 30
          track.level = Math.max(0, Math.min(100, base + noise))

          // Update peak
          if (track.level > track.peak) {
            track.peak = track.level
          }
        })
      }, 50)

      // Peak decay
      peakDecayInterval = setInterval(() => {
        tracks.value.forEach(track => {
          if (track.peak > 0) {
            track.peak = Math.max(0, track.peak - 0.5)
          }
        })
      }, 100)
    }

    const stopTest = () => {
      testing.value = false

      if (testInterval) {
        clearInterval(testInterval)
        testInterval = null
      }
      if (peakDecayInterval) {
        clearInterval(peakDecayInterval)
        peakDecayInterval = null
      }
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
        animationFrameId = null
      }
      if (audioContext) {
        audioContext.close()
        audioContext = null
      }

      // Decay to zero
      const decayInterval = setInterval(() => {
        let allZero = true
        tracks.value.forEach(track => {
          if (track.level > 0) {
            track.level = Math.max(0, track.level - 2)
            allZero = false
          }
        })
        if (allZero) {
          clearInterval(decayInterval)
        }
      }, 50)

      // Reset labels
      tracks.value.forEach((track, i) => {
        track.label = `Track ${i + 1}`
      })
    }

    const resetPeaks = () => {
      tracks.value.forEach(track => {
        track.peak = 0
      })
    }

    onUnmounted(() => {
      stopTest()
    })

    return {
      ledSegments,
      tracks,
      testing,
      startRealAudio,
      startTest,
      stopTest,
      resetPeaks
    }
  }
}
</script>

<style scoped>
/* 8-bit retro style */
.led-meter-card {
  background: #000;
  color: #0f0;
  border: 2px solid #0f0;
  font-family: 'Courier New', monospace;
}

.led-meter-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: #111;
  border: 1px solid #0f0;
}

.led-meter-label {
  font-size: 11px;
  font-weight: bold;
  margin-bottom: 12px;
  color: #0f0;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}

.led-bar-wrapper {
  position: relative;
  width: 32px;
  height: 250px;
  background: #000;
  border: 2px solid #0f0;
  padding: 2px;
  display: flex;
  flex-direction: column-reverse;
  gap: 2px;
}

.led-segment {
  flex: 1;
  position: relative;
}

.led-bar {
  width: 100%;
  height: 100%;
  background: #002200;
  transition: background-color 0.05s linear;
}

/* Active LED colors - 8-bit bright colors */
.led-segment.led-active.led-green .led-bar {
  background: #00ff00;
}

.led-segment.led-active.led-yellow .led-bar {
  background: #ffff00;
}

.led-segment.led-active.led-red .led-bar {
  background: #ff0000;
}

/* Peak indicator - simple line */
.peak-indicator {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: #ff0000;
  z-index: 10;
  animation: peak-blink 0.5s step-end infinite;
}

@keyframes peak-blink {
  0% { opacity: 1; }
  50% { opacity: 0; }
}

/* Scale marks - minimal */
.scale-marks {
  position: absolute;
  right: -32px;
  top: 0;
  bottom: 0;
  width: 28px;
  pointer-events: none;
}

.scale-mark {
  position: absolute;
  right: 0;
  transform: translateY(50%);
  font-size: 9px;
  color: #0f0;
  font-family: 'Courier New', monospace;
}

.scale-mark::before {
  content: '█';
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  color: #0f0;
  margin-right: 1px;
}

/* Numeric display - retro terminal style */
.level-display {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  min-height: 32px;
}

.level-display > span:first-child {
  color: #0f0;
  font-weight: bold;
}

.level-caution {
  color: #ff0 !important;
}

.level-warn {
  color: #f00 !important;
  animation: text-blink 0.5s step-end infinite;
}

@keyframes text-blink {
  0% { opacity: 1; }
  50% { opacity: 0; }
}

.peak-value {
  font-size: 10px;
  color: #0a0 !important;
  margin-top: 4px;
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .led-bar-wrapper {
    height: 180px;
    width: 24px;
  }

  .scale-marks {
    right: -28px;
    width: 24px;
  }
}
</style>
