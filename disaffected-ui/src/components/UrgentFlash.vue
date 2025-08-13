<template>
  <teleport to="body">
    <div
      v-if="isVisible"
      class="urgent-flash-overlay"
      :class="[
        { 'urgent-flash-overlay--fading': isFading },
        `urgent-flash-overlay--${backgroundColor}`
      ]"
    >
      <div class="urgent-flash-text">
        {{ message }}
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref } from 'vue'

const isVisible = ref(false)
const isFading = ref(false)
const message = ref('')

const backgroundColor = ref('red')

const showFlash = (text, bgColor = 'red') => {
  message.value = text
  backgroundColor.value = bgColor
  isVisible.value = true
  isFading.value = false
  
  // Immediately start fading out
  setTimeout(() => {
    isFading.value = true
    
    // Remove after animation completes
    setTimeout(() => {
      isVisible.value = false
      isFading.value = false
      message.value = ''
      backgroundColor.value = 'red' // Reset to default
    }, 500)
  }, 300) // Flash duration before fade starts
}

// Expose the function to parent components
defineExpose({
  showFlash
})
</script>

<style scoped>
.urgent-flash-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
  animation: urgentFadeIn 0.05s ease-in;
}

/* Background color variants */
.urgent-flash-overlay--red {
  background-color: rgba(220, 38, 38, 0.75);
}

.urgent-flash-overlay--green {
  background-color: rgba(34, 197, 94, 0.75);
}

.urgent-flash-overlay--yellow {
  background-color: rgba(234, 179, 8, 0.75);
}

.urgent-flash-overlay--blue {
  background-color: rgba(59, 130, 246, 0.75);
}

.urgent-flash-overlay--fading {
  animation: urgentFadeOut 0.5s ease-out forwards;
}

.urgent-flash-text {
  font-size: clamp(3rem, 8vw, 8rem);
  font-weight: 900;
  color: white;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  text-shadow: 
    3px 3px 0px #000,
    -3px -3px 0px #000,
    3px -3px 0px #000,
    -3px 3px 0px #000,
    3px 0px 0px #000,
    -3px 0px 0px #000,
    0px 3px 0px #000,
    0px -3px 0px #000,
    5px 5px 10px rgba(0, 0, 0, 0.8);
  user-select: none;
  pointer-events: none;
  animation: textPulse 0.3s ease-in-out;
}

@keyframes urgentFadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes urgentFadeOut {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.95);
  }
}

@keyframes textPulse {
  0% {
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

/* Ensure it works on all screen sizes */
@media (max-width: 768px) {
  .urgent-flash-text {
    padding: 1rem;
    font-size: clamp(2rem, 12vw, 4rem);
  }
}

@media (max-width: 480px) {
  .urgent-flash-text {
    font-size: clamp(1.5rem, 15vw, 3rem);
    text-shadow: 
      2px 2px 0px #000,
      -2px -2px 0px #000,
      2px -2px 0px #000,
      -2px 2px 0px #000,
      2px 0px 0px #000,
      -2px 0px 0px #000,
      0px 2px 0px #000,
      0px -2px 0px #000,
      3px 3px 6px rgba(0, 0, 0, 0.8);
  }
}
</style>