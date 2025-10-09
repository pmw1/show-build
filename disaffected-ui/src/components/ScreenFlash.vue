<template>
  <transition name="flash">
    <div
      v-if="showFlash"
      class="screen-flash"
      :style="{ backgroundColor: flashColor }"
    >
      <div v-if="flashMessage" class="flash-message" :class="flashMessageStyle">
        {{ flashMessage }}
      </div>
    </div>
  </transition>
</template>

<script setup>
import { useScreenFlash } from '@/composables/useScreenFlash'

const { showFlash, flashColor, flashMessage, flashMessageStyle } = useScreenFlash()
</script>

<style scoped>
.screen-flash {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 99999;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flash-message {
  font-size: 48px;
  font-weight: bold;
  color: white;
  text-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
  pointer-events: none;
}

.flash-message.urgent {
  font-size: 96px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  animation: pulse-urgent 0.2s ease-in-out 2;
}

@keyframes pulse-urgent {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.flash-enter-active {
  animation: flash-in 0.15s ease-out;
}

.flash-leave-active {
  animation: flash-out 0.15s ease-in;
}

@keyframes flash-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 0.4;
  }
}

@keyframes flash-out {
  from {
    opacity: 0.4;
  }
  to {
    opacity: 0;
  }
}
</style>
