<template>
  <div class="clock-display">
    <div class="label-primary">TODAY</div>
    <div class="time">{{ currentTime }}</div>
    <div class="label-secondary">{{ currentDate }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const currentDate = ref('')
const currentTime = ref('')

let clockInterval = null

// Update current time display
const updateCurrentTime = () => {
  const now = new Date()

  // Convert to New York timezone
  const nyTime = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}))

  // Format date: "Wednesday - October 2, 2025"
  const dateOptions = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'America/New_York'
  }
  currentDate.value = nyTime.toLocaleDateString('en-US', dateOptions)

  // Format time: "15:42:37" (24-hour format)
  const timeOptions = {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'America/New_York'
  }
  currentTime.value = nyTime.toLocaleTimeString('en-US', timeOptions)
}

onMounted(() => {
  updateCurrentTime()
  clockInterval = setInterval(updateCurrentTime, 1000)
})

onUnmounted(() => {
  if (clockInterval) {
    clearInterval(clockInterval)
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');

.clock-display {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.05);
  padding: 0;
  border-radius: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  min-width: 224px;
  overflow: visible;
  height: 100%;
  justify-content: flex-start;
}

.label-primary {
  font-size: 0.56rem;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  text-align: center;
  margin-bottom: 0;
  background-color: #1976d2;
  padding: 2px 10px 2px 10px;
  border-radius: 0;
}

.time {
  font-family: 'Courier New', Courier, monospace;
  font-size: 1.6rem;
  font-weight: 900;
  color: #4caf50;
  letter-spacing: 2.4px;
  text-align: center;
  align-self: center;
  width: 100%;
  margin-bottom: 0;
  padding: 2px 10px 0 10px;
}

.label-secondary {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.56rem;
  color: rgba(0, 0, 0, 0.7);
  font-weight: bold;
  text-align: center;
  text-transform: uppercase;
  padding: 0 8px 1px 8px;
  margin-top: -6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
