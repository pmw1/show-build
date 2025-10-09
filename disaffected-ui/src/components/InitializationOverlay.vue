<template>
  <transition name="fade">
    <div v-if="show" class="initialization-overlay">
      <div class="initialization-content">
        <div class="spinner"></div>
        <div class="initialization-text">Initializing status check...</div>
        <div class="initialization-subtext">If this is happening frequently, please let Kevin know.</div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useSystemHealth } from '@/composables/useSystemHealth'
import axios from 'axios'

const { health } = useSystemHealth()
const show = ref(true)
const startTime = ref(Date.now())

// Log initialization overlay display
const logOverlayEvent = async (duration, reason) => {
  try {
    const logData = {
      event: 'initialization_overlay_displayed',
      duration_ms: duration,
      reason: reason,
      timestamp: new Date().toISOString(),
      health_status: health.value.status,
      user_agent: navigator.userAgent
    }

    console.log('📊 Logging initialization overlay event:', logData)

    // Send to backend logging endpoint
    await axios.post('/api/logs/client-event', logData, {
      timeout: 2000
    }).catch(err => {
      // Don't block UI if logging fails
      console.warn('Failed to log overlay event:', err.message)
    })
  } catch (error) {
    console.warn('Error logging overlay event:', error)
  }
}

// Hide overlay once we have a valid health status (not 'unknown')
watch(() => health.value.status, (newStatus) => {
  if (newStatus !== 'unknown') {
    const duration = Date.now() - startTime.value

    // Log if health check took longer than 2 seconds
    if (duration > 2000) {
      console.warn(`⚠️ Health check took ${duration}ms - this may indicate a problem`)
      logOverlayEvent(duration, 'health_check_completed')
    }

    // Keep showing for minimum 300ms to avoid flash
    setTimeout(() => {
      show.value = false
    }, 300)
  }
}, { immediate: true })

// Failsafe: Hide after 5 seconds even if health check hasn't completed
onMounted(() => {
  setTimeout(() => {
    if (show.value) {
      const duration = Date.now() - startTime.value
      console.error(`❌ Health check took longer than 5s (${duration}ms), hiding initialization overlay anyway`)

      // Log timeout event
      logOverlayEvent(duration, 'health_check_timeout')

      show.value = false
    }
  }, 5000)
})
</script>

<style scoped>
.initialization-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.initialization-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #2196f3;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.initialization-text {
  font-size: 18px;
  font-weight: 600;
  color: white;
  letter-spacing: 0.05em;
  animation: pulse 1.5s ease-in-out infinite;
}

.initialization-subtext {
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 8px;
  font-style: italic;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
