<template>
  <teleport to="body">
    <transition name="notification-slide">
      <div
        v-if="isVisible"
        class="standard-notification"
        :style="{
          '--notification-color': currentColor,
          '--fade-duration': `${fadeDuration}ms`,
          top: `${positionTop}px`,
          left: `${positionLeft}px`,
          transform: dynamicTransform
        }"
      >
        <div class="notification-content" v-html="message"></div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref } from 'vue'

const isVisible = ref(false)
const message = ref('')
const currentColor = ref('#2196F3')
const fadeDuration = ref(300)
const positionTop = ref(70)
const positionLeft = ref(50)
const dynamicTransform = ref('translateX(-50%)')

const notifyUserStandard = (text, color = '#2196F3', duration = 3000, targetElement = null, attachToPanel = false) => {
  message.value = text
  currentColor.value = color

  // Calculate position based on target element
  if (targetElement && attachToPanel) {
    // PANEL MODE: Attach to the bottom-left corner of the rundown panel
    const rect = targetElement.getBoundingClientRect()
    positionTop.value = rect.bottom - 70 // Near bottom of panel
    positionLeft.value = rect.left // Align with left edge of panel
    dynamicTransform.value = 'translateX(0)' // No centering, align left edge
  } else if (targetElement) {
    // ELEMENT MODE: Position on top of the element
    const rect = targetElement.getBoundingClientRect()
    positionTop.value = rect.top - 60 // 60px above the element
    positionLeft.value = rect.left + (rect.width / 2) // Centered on element
    dynamicTransform.value = 'translateX(-50%)' // Keep centered
  } else {
    // DEFAULT MODE: top-center of viewport
    positionTop.value = 70
    positionLeft.value = window.innerWidth / 2 // Center of viewport
    dynamicTransform.value = 'translateX(-50%)'
  }

  isVisible.value = true

  // Auto-dismiss after specified duration + 1 second
  setTimeout(() => {
    isVisible.value = false
  }, duration + 1000)
}

// Expose the function to parent components
defineExpose({
  notifyUserStandard
})
</script>

<style scoped>
.standard-notification {
  position: fixed;
  /* Position set dynamically via inline styles */
  z-index: 99999; /* Above everything including modals and their overlays */
  min-width: 800px;
  max-width: 1400px;
  padding: 32px 48px;
  border-radius: 16px;
  /* High contrast box with dark background and colored left border */
  background: linear-gradient(135deg, rgba(30, 30, 30, 0.98), rgba(20, 20, 20, 0.98));
  border-left: 8px solid var(--notification-color, #2196F3);
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.5),
    0 16px 48px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  pointer-events: none;
  will-change: transform, opacity;
}

.notification-content {
  color: #ffffff;
  font-size: 28px;
  font-weight: 600;
  text-align: left;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  user-select: none;
  line-height: 1.4;
}

.notification-content :deep(small) {
  display: block;
  font-size: 20px;
  font-weight: 400;
  opacity: 0.85;
  margin-top: 8px;
}

/* Drop down from top, pause, then fall with gravity */
.notification-slide-enter-active {
  animation: notificationDropIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.notification-slide-leave-active {
  animation: notificationFallOut 0.8s cubic-bezier(0.55, 0.085, 0.68, 0.53);
}

@keyframes notificationDropIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-150px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* Fall with gravity acceleration (ease-in = acceleration) */
@keyframes notificationFallOut {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  20% {
    opacity: 1;
    transform: translateX(-50%) translateY(20px);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(calc(100vh + 200px));
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .standard-notification {
    min-width: 250px;
    max-width: 90vw;
    padding: 12px 20px;
    top: 70px;
  }

  .notification-content {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .standard-notification {
    min-width: 200px;
    max-width: 95vw;
    padding: 10px 16px;
    top: 60px;
  }

  .notification-content {
    font-size: 13px;
  }
}
</style>
