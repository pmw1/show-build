<template>
  <v-card class="vu-meter-card">
    <v-card-title>VU Meters</v-card-title>
    <v-card-text>
      <v-row>
        <v-col
          v-for="(track, index) in tracks"
          :key="index"
          cols="12"
          sm="6"
          md="3"
        >
          <div class="vu-meter-container">
            <div class="vu-meter-label">{{ track.label }}</div>
            <svg
              :width="meterWidth"
              :height="meterHeight"
              class="vu-meter-svg"
            >
              <!-- Background arc -->
              <path
                :d="getArcPath()"
                fill="none"
                stroke="#333"
                :stroke-width="arcWidth"
              />

              <!-- Color zones -->
              <path
                :d="getArcPath(0, 60)"
                fill="none"
                stroke="#4CAF50"
                :stroke-width="arcWidth"
                opacity="0.3"
              />
              <path
                :d="getArcPath(60, 85)"
                fill="none"
                stroke="#FFC107"
                :stroke-width="arcWidth"
                opacity="0.3"
              />
              <path
                :d="getArcPath(85, 100)"
                fill="none"
                stroke="#F44336"
                :stroke-width="arcWidth"
                opacity="0.3"
              />

              <!-- Scale marks -->
              <g v-for="mark in scaleMarks" :key="mark.value">
                <line
                  :x1="getMarkPosition(mark.value).x1"
                  :y1="getMarkPosition(mark.value).y1"
                  :x2="getMarkPosition(mark.value).x2"
                  :y2="getMarkPosition(mark.value).y2"
                  stroke="#666"
                  :stroke-width="mark.major ? 2 : 1"
                />
                <text
                  v-if="mark.major"
                  :x="getMarkPosition(mark.value).tx"
                  :y="getMarkPosition(mark.value).ty"
                  text-anchor="middle"
                  fill="#999"
                  font-size="10"
                >
                  {{ mark.label }}
                </text>
              </g>

              <!-- Needle -->
              <g class="needle" :style="{ transformOrigin: `${centerX}px ${centerY}px` }">
                <line
                  :x1="centerX"
                  :y1="centerY"
                  :x2="centerX"
                  :y2="centerY - radius + 10"
                  :stroke="getNeedleColor(track.level)"
                  stroke-width="3"
                  stroke-linecap="round"
                  class="needle-line"
                  :style="{
                    transform: `rotate(${getNeedleAngle(track.level)}deg)`,
                    transformOrigin: 'center',
                    transition: 'transform 0.1s ease-out'
                  }"
                />
                <circle
                  :cx="centerX"
                  :cy="centerY"
                  r="5"
                  fill="#666"
                />
              </g>

              <!-- Peak indicator dot -->
              <circle
                v-if="track.peak > 0"
                :cx="getPeakPosition(track.peak).x"
                :cy="getPeakPosition(track.peak).y"
                r="3"
                :fill="track.peak > 85 ? '#F44336' : '#FFC107'"
                class="peak-indicator"
              />
            </svg>

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

      <!-- Test controls -->
      <v-row class="mt-4">
        <v-col>
          <v-btn @click="startTest" :disabled="testing" color="primary" size="small">
            Start Test
          </v-btn>
          <v-btn @click="stopTest" :disabled="!testing" color="error" size="small" class="ml-2">
            Stop Test
          </v-btn>
          <v-btn @click="resetPeaks" size="small" class="ml-2">
            Reset Peaks
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const meterWidth = 200
const meterHeight = 150
const centerX = meterWidth / 2
const centerY = meterHeight - 20
const radius = 70
const arcWidth = 15
const startAngle = -135
const endAngle = 135

const tracks = ref([
  { label: 'Track 1', level: 0, peak: 0 },
  { label: 'Track 2', level: 0, peak: 0 },
  { label: 'Track 3', level: 0, peak: 0 },
  { label: 'Track 4', level: 0, peak: 0 }
])

const scaleMarks = [
  { value: 0, label: '-\u221E', major: true },
  { value: 20, label: '-20', major: true },
  { value: 40, label: '-10', major: true },
  { value: 60, label: '0', major: true },
  { value: 80, label: '+3', major: true },
  { value: 100, label: '+6', major: true },
  { value: 10, major: false },
  { value: 30, major: false },
  { value: 50, major: false },
  { value: 70, major: false },
  { value: 90, major: false }
]

const testing = ref(false)
let testInterval = null
let peakDecayInterval = null

function polarToCartesian(angle, r) {
  const rad = (angle - 90) * Math.PI / 180
  return { x: centerX + r * Math.cos(rad), y: centerY + r * Math.sin(rad) }
}

function getArcPath(startPercent = 0, endPercent = 100) {
  const a1 = startAngle + (endAngle - startAngle) * (startPercent / 100)
  const a2 = startAngle + (endAngle - startAngle) * (endPercent / 100)
  const s = polarToCartesian(a1, radius)
  const e = polarToCartesian(a2, radius)
  const large = a2 - a1 <= 180 ? '0' : '1'
  return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${large} 1 ${e.x} ${e.y}`
}

function getMarkPosition(value) {
  const angle = startAngle + (endAngle - startAngle) * (value / 100)
  const inner = polarToCartesian(angle, radius - arcWidth / 2 - 5)
  const outer = polarToCartesian(angle, radius - arcWidth / 2 - 12)
  const text = polarToCartesian(angle, radius - arcWidth / 2 - 22)
  return { x1: inner.x, y1: inner.y, x2: outer.x, y2: outer.y, tx: text.x, ty: text.y }
}

function getNeedleAngle(level) {
  return startAngle + (endAngle - startAngle) * (Math.min(100, Math.max(0, level)) / 100)
}

function getPeakPosition(peak) {
  return polarToCartesian(getNeedleAngle(peak), radius - arcWidth / 2)
}

function getNeedleColor(level) {
  if (level > 85) return '#F44336'
  if (level > 60) return '#FFC107'
  return '#4CAF50'
}

function startTest() {
  testing.value = true
  testInterval = setInterval(() => {
    tracks.value.forEach((track, index) => {
      const base = 30 + Math.sin(Date.now() / 1000 + index) * 20
      track.level = Math.max(0, Math.min(100, base + Math.random() * 30))
      if (track.level > track.peak) track.peak = track.level
    })
  }, 50)
  peakDecayInterval = setInterval(() => {
    tracks.value.forEach(track => { if (track.peak > 0) track.peak = Math.max(0, track.peak - 0.5) })
  }, 100)
}

function stopTest() {
  testing.value = false
  if (testInterval) { clearInterval(testInterval); testInterval = null }
  if (peakDecayInterval) { clearInterval(peakDecayInterval); peakDecayInterval = null }
  const decayInterval = setInterval(() => {
    let allZero = true
    tracks.value.forEach(track => { if (track.level > 0) { track.level = Math.max(0, track.level - 2); allZero = false } })
    if (allZero) clearInterval(decayInterval)
  }, 50)
}

function resetPeaks() {
  tracks.value.forEach(track => { track.peak = 0 })
}

onUnmounted(stopTest)
</script>

<style scoped>
.vu-meter-card {
  background: #1a1a1a;
  color: #fff;
}

.vu-meter-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  background: #222;
  border-radius: 8px;
}

.vu-meter-label {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #aaa;
}

.vu-meter-svg {
  display: block;
}

.needle-line {
  filter: drop-shadow(0 0 3px currentColor);
}

.peak-indicator {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.level-display {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: 'Courier New', monospace;
  font-size: 16px;
}

.level-display span {
  color: #4CAF50;
}

.level-caution {
  color: #FFC107 !important;
}

.level-warn {
  color: #F44336 !important;
  font-weight: bold;
}

.peak-value {
  font-size: 12px;
  color: #999 !important;
  margin-top: 4px;
}
</style>
