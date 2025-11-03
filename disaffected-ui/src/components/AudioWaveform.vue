<template>
  <div class="audio-waveform-container" :style="containerStyle">
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
  setup(props) {
    const waveformCanvas = ref(null)
    const canvasWidth = ref(800)
    const canvasHeight = computed(() => props.height)
    const resizeObserver = ref(null)

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
      playheadStyle
    }
  }
}
</script>

<style scoped>
.audio-waveform-container {
  position: relative;
  user-select: none;
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
</style>
