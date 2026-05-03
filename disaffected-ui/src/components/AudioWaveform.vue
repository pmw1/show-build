<template>
  <div
    class="audio-waveform-container"
    :style="containerStyle"
    @click="handleClick"
    @mousedown="handleMouseDown"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseUp"
  >
    <canvas
      ref="waveformCanvas"
      :width="canvasWidth"
      :height="canvasHeight"
      class="waveform-canvas"
    ></canvas>

    <!-- In point marker line -->
    <div
      v-if="inPoint !== null && duration > 0"
      class="io-marker"
      :style="inBracketStyle"
    ></div>

    <!-- Out point marker line -->
    <div
      v-if="outPoint !== null && duration > 0"
      class="io-marker"
      :style="outBracketStyle"
    ></div>

    <!-- Playhead indicator -->
    <div
      v-if="currentTime !== null && duration > 0"
      class="playhead"
      :style="playheadStyle"
    ></div>

    <!-- Hover time indicator -->
    <div
      v-if="hoverTime !== null"
      class="hover-indicator"
      :style="hoverIndicatorStyle"
    >
      <span class="hover-time">{{ formatTime(hoverTime) }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  waveformData: { type: Array, required: true, default: () => [] },
  currentTime: { type: Number, default: null },
  duration: { type: Number, default: 0 },
  height: { type: Number, default: 60 },
  backgroundColor: { type: String, default: 'rgba(0, 0, 0, 0.5)' },
  waveColor: { type: String, default: '#4CAF50' },
  progressColor: { type: String, default: '#81C784' },
  playheadColor: { type: String, default: '#FF5722' },
  inPoint: { type: Number, default: null },
  outPoint: { type: Number, default: null },
  regionColor: { type: String, default: '#000000' },
  regionBackground: { type: String, default: 'rgba(255, 255, 255, 0.35)' }
})
const emit = defineEmits(['seek'])

const waveformCanvas = ref(null)
const canvasWidth = ref(800)
const canvasHeight = computed(() => props.height)
let resizeObserver = null
const isDragging = ref(false)
const hoverTime = ref(null)
const hoverX = ref(0)

const containerStyle = computed(() => ({
  width: '100%',
  height: `${props.height}px`,
  position: 'relative',
  background: props.backgroundColor,
  borderRadius: '4px',
  overflow: 'hidden'
}))

const playheadStyle = computed(() => {
  if (props.currentTime === null || props.duration === 0) return {}
  const progress = (props.currentTime / props.duration) * 100
  return { left: `${progress}%`, transform: 'translateX(-50%)' }
})

const hoverIndicatorStyle = computed(() => ({
  left: `${hoverX.value}px`,
  transform: 'translateX(-50%)'
}))

const inBracketStyle = computed(() => {
  if (props.inPoint === null || props.duration === 0) return {}
  const pct = (props.inPoint / props.duration) * 100
  return { left: `${pct}%` }
})

const outBracketStyle = computed(() => {
  if (props.outPoint === null || props.duration === 0) return {}
  const pct = (props.outPoint / props.duration) * 100
  return { left: `${pct}%` }
})

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function getTimeFromEvent(event) {
  if (!waveformCanvas.value || props.duration === 0) return null
  const rect = waveformCanvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  return Math.max(0, Math.min(1, x / rect.width)) * props.duration
}

function handleClick(event) {
  const time = getTimeFromEvent(event)
  if (time !== null) emit('seek', time)
}

function handleMouseDown(event) {
  isDragging.value = true
  const time = getTimeFromEvent(event)
  if (time !== null) emit('seek', time)
}

function handleMouseMove(event) {
  const rect = waveformCanvas.value?.getBoundingClientRect()
  if (rect) {
    hoverX.value = event.clientX - rect.left
    hoverTime.value = getTimeFromEvent(event)
  }
  if (isDragging.value) {
    const time = getTimeFromEvent(event)
    if (time !== null) emit('seek', time)
  }
}

function handleMouseUp() {
  isDragging.value = false
  hoverTime.value = null
}

function drawWaveform() {
  if (!waveformCanvas.value || props.waveformData.length === 0) return
  const canvas = waveformCanvas.value
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  ctx.clearRect(0, 0, width, height)

  const barWidth = width / props.waveformData.length
  const centerY = height / 2

  // Draw in/out region background
  const hasInOut = props.inPoint !== null && props.outPoint !== null && props.duration > 0
  if (hasInOut) {
    const inX = (props.inPoint / props.duration) * width
    const outX = (props.outPoint / props.duration) * width
    ctx.fillStyle = props.regionBackground
    ctx.fillRect(inX, 0, outX - inX, height)
  }

  // Determine in/out range as fraction of total bars
  const inFrac = hasInOut ? props.inPoint / props.duration : null
  const outFrac = hasInOut ? props.outPoint / props.duration : null

  props.waveformData.forEach((amplitude, index) => {
    const x = index * barWidth
    const barHeight = amplitude * (height * 0.9)
    const barProgress = index / props.waveformData.length
    const progress = props.currentTime !== null && props.duration > 0 ? props.currentTime / props.duration : 0

    // Check if this bar is inside the in/out region
    const inRegion = hasInOut && barProgress >= inFrac && barProgress <= outFrac

    if (inRegion) {
      ctx.fillStyle = barProgress <= progress ? props.regionColor : '#FFFFFF'
    } else {
      ctx.fillStyle = barProgress <= progress ? props.progressColor : props.waveColor
    }

    ctx.fillRect(x, centerY - barHeight / 2, Math.max(1, barWidth - 1), barHeight)
  })
}

function handleResize() {
  if (!waveformCanvas.value) return
  const container = waveformCanvas.value.parentElement
  if (container) {
    canvasWidth.value = container.clientWidth
    nextTick(drawWaveform)
  }
}

watch(() => props.waveformData, () => nextTick(drawWaveform), { deep: true })
watch(() => props.currentTime, drawWaveform)
watch(() => props.inPoint, drawWaveform)
watch(() => props.outPoint, drawWaveform)

onMounted(() => {
  handleResize()
  if (waveformCanvas.value?.parentElement) {
    resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(waveformCanvas.value.parentElement)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})
</script>

<style scoped>
.audio-waveform-container {
  position: relative;
  user-select: none;
  cursor: pointer;
}

.waveform-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    #FF5722 10%,
    #FF5722 90%,
    transparent 100%
  );
  box-shadow: 0 0 8px rgba(255, 87, 34, 0.8);
  pointer-events: none;
  z-index: 10;
}

.hover-indicator {
  position: absolute;
  top: -30px;
  pointer-events: none;
  z-index: 20;
}

.hover-time {
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Roboto Mono', monospace;
  white-space: nowrap;
}

.io-marker {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #00E676;
  box-shadow: 0 0 6px rgba(0, 230, 118, 0.8);
  pointer-events: none;
  z-index: 15;
  transform: translateX(-50%);
}
</style>
