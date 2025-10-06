<template>
  <teleport to="body">
    <transition name="notification-slide">
      <div
        v-if="isVisible"
        class="standard-notification"
        :style="{
          backgroundColor: currentColor,
          '--fade-duration': `${fadeDuration}ms`,
          top: `${positionTop}px`,
          left: `${positionLeft}px`,
          transform: dynamicTransform
        }"
      >
        <div class="notification-content">
          {{ message }}
        </div>
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

const notifyUserStandard = (text, color = '#2196F3', duration = 2000, targetElement = null, attachToPanel = false) => {
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

  // Auto-dismiss after specified duration
  setTimeout(() => {
    isVisible.value = false
  }, duration)
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
  min-width: 300px;
  max-width: 600px;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow:
    0 6px 12px rgba(0, 0, 0, 0.2),
    0 12px 24px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(10px);
  pointer-events: none;
  /* Overlay effect - lays on top without displacing content */
  will-change: transform, opacity;
}

.notification-content {
  color: white;
  font-size: 16px;
  font-weight: 500;
  text-align: center;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  user-select: none;
}

/* Slide in/out animations - slides from BOTTOM-LEFT corner */
.notification-slide-enter-active {
  animation: notificationSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.notification-slide-leave-active {
  animation: notificationSlideOut var(--fade-duration, 300ms) cubic-bezier(0.4, 0, 1, 1);
}

@keyframes notificationSlideIn {
  from {
    opacity: 0;
    transform: translateX(-120%) translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0) translateY(0);
  }
}

@keyframes notificationSlideOut {
  from {
    opacity: 1;
    transform: translateX(0) translateY(0);
  }
  to {
    opacity: 0;
    transform: translateX(-120%) translateY(30px);
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
