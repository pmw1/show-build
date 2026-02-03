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

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

export default {
  name: 'AudioWaveform',
  props: {
    waveformData: {
      type: Array,
      required: true,
      default: () => []
    },
    currentTime: {
      type: Number,
      default: null
    },
    duration: {
      type: Number,
      default: 0
    },
    height: {
      type: Number,
      default: 60
    },
    backgroundColor: {
      type: String,
      default: 'rgba(0, 0, 0, 0.5)'
    },
    waveColor: {
      type: String,
      default: '#4CAF50'
    },
    progressColor: {
      type: String,
      default: '#81C784'
    },
    playheadColor: {
      type: String,
      default: '#FF5722'
    }
  },
  emits: ['seek'],
  setup(props, { emit }) {
    const waveformCanvas = ref(null)
    const canvasWidth = ref(800)
    const canvasHeight = computed(() => props.height)
    const resizeObserver = ref(null)
    const isDragging = ref(false)
    const hoverTime = ref(null)
    const hoverX = ref(0)

    // Container style
    const containerStyle = computed(() => ({
      width: '100%',
      height: `${props.height}px`,
      position: 'relative',
      background: props.backgroundColor,
      borderRadius: '4px',
      overflow: 'hidden'
    }))

    // Playhead position style
    const playheadStyle = computed(() => {
      if (props.currentTime === null || props.duration === 0) return {}

      const progress = (props.currentTime / props.duration) * 100
      return {
        left: `${progress}%`,
        transform: 'translateX(-50%)'
      }
    })

    // Hover indicator style
    const hoverIndicatorStyle = computed(() => {
      return {
        left: `${hoverX.value}px`,
        transform: 'translateX(-50%)'
      }
    })

    // Format time for display (HH:MM:SS)
    const formatTime = (seconds) => {
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = Math.floor(seconds % 60)
      return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }

    // Calculate time from mouse position
    const getTimeFromEvent = (event) => {
      if (!waveformCanvas.value || props.duration === 0) return null
      const rect = waveformCanvas.value.getBoundingClientRect()
      const x = event.clientX - rect.left
      const progress = Math.max(0, Math.min(1, x / rect.width))
      return progress * props.duration
    }

    // Handle click to seek
    const handleClick = (event) => {
      const time = getTimeFromEvent(event)
      if (time !== null) {
        emit('seek', time)
      }
    }

    // Handle mouse down for drag scrubbing
    const handleMouseDown = (event) => {
      isDragging.value = true
      const time = getTimeFromEvent(event)
      if (time !== null) {
        emit('seek', time)
      }
    }

    // Handle mouse move for hover preview and drag scrubbing
    const handleMouseMove = (event) => {
      const rect = waveformCanvas.value?.getBoundingClientRect()
      if (rect) {
        hoverX.value = event.clientX - rect.left
        hoverTime.value = getTimeFromEvent(event)
      }

      if (isDragging.value) {
        const time = getTimeFromEvent(event)
        if (time !== null) {
          emit('seek', time)
        }
      }
    }

    // Handle mouse up to stop dragging
    const handleMouseUp = () => {
      isDragging.value = false
      hoverTime.value = null
    }

    /**
     * Draw waveform on canvas
     */
    const drawWaveform = () => {
      if (!waveformCanvas.value || props.waveformData.length === 0) return

      const canvas = waveformCanvas.value
      const ctx = canvas.getContext('2d')
      const width = canvas.width
      const height = canvas.height

      // Clear canvas
      ctx.clearRect(0, 0, width, height)

      // Draw waveform
      const barWidth = width / props.waveformData.length
      const centerY = height / 2

      props.waveformData.forEach((amplitude, index) => {
        const x = index * barWidth
        const barHeight = amplitude * (height * 0.9) // Use 90% of height for safety

        // Determine color based on playback progress
        const progress = props.currentTime !== null && props.duration > 0
          ? props.currentTime / props.duration
          : 0
        const barProgress = index / props.waveformData.length

        const color = barProgress <= progress ? props.progressColor : props.waveColor

        // Draw waveform bar (centered vertically)
        ctx.fillStyle = color
        ctx.fillRect(
          x,
          centerY - barHeight / 2,
          Math.max(1, barWidth - 1), // Ensure at least 1px width, with 1px gap
          barHeight
        )
      })
    }

    /**
     * Handle canvas resize
     */
    const handleResize = () => {
      if (!waveformCanvas.value) return

      const container = waveformCanvas.value.parentElement
      if (container) {
        canvasWidth.value = container.clientWidth
        nextTick(() => {
          drawWaveform()
        })
      }
    }

    // Watch for waveform data changes
    watch(() => props.waveformData, () => {
      nextTick(() => {
        drawWaveform()
      })
    }, { deep: true })

    // Watch for current time changes (playhead movement)
    watch(() => props.currentTime, () => {
      drawWaveform()
    })

    // Initial render and resize observer
    onMounted(() => {
      handleResize()

      // Set up resize observer
      if (waveformCanvas.value && waveformCanvas.value.parentElement) {
        resizeObserver.value = new ResizeObserver(handleResize)
        resizeObserver.value.observe(waveformCanvas.value.parentElement)
      }
    })

    // Cleanup
    onBeforeUnmount(() => {
      if (resizeObserver.value) {
        resizeObserver.value.disconnect()
      }
    })

    return {
      waveformCanvas,
      canvasWidth,
      canvasHeight,
      containerStyle,
      playheadStyle,
      hoverIndicatorStyle,
      hoverTime,
      formatTime,
      handleClick,
      handleMouseDown,
      handleMouseMove,
      handleMouseUp
    }
  }
}
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
</style>
