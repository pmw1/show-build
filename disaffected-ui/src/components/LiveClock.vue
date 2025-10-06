<template>
  <div class="clock-display countdown-display">
    <div class="label-primary">COUNTDOWN</div>
    <div class="countdown-time" :class="countdownClass">{{ countdownTime }}</div>
    <div class="label-secondary">HOURS UNTIL DISAFFECTED</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const countdownTime = ref('--:--:--')
const countdownClass = ref('countdown-green')

let clockInterval = null
let episodeData = null

// Fetch current episode data
const fetchCurrentEpisode = async () => {
  try {
    const response = await axios.get('/api/episodes/upcoming')
    if (response.data && response.data.episodes && response.data.episodes.length > 0) {
      // Get the first upcoming episode
      episodeData = response.data.episodes[0].episode
      console.log('Next episode loaded:', episodeData)
    } else {
      episodeData = null
      console.log('No upcoming episodes found')
    }
  } catch (error) {
    console.warn('Failed to fetch upcoming episodes:', error)
    episodeData = null
  }
}

// Update countdown display
const updateCountdown = () => {
  if (!episodeData || !episodeData.air_date) {
    countdownTime.value = '--:--:--'
    countdownClass.value = 'countdown-green'
    return
  }

  const now = new Date()
  const nyNow = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}))

  // Parse the episode air date and set to 10pm NY time
  const airDate = new Date(episodeData.air_date)
  const showTime = new Date(airDate.toLocaleString("en-US", {timeZone: "America/New_York"}))
  showTime.setHours(22, 0, 0, 0) // 10:00 PM

  const timeDiff = showTime.getTime() - nyNow.getTime()

  if (timeDiff <= 0) {
    // Show is live or has passed
    countdownTime.value = '00:00:00'
    countdownClass.value = 'countdown-live'
    return
  }

  // Calculate total time remaining in hours, minutes, seconds
  const totalHours = Math.floor(timeDiff / (1000 * 60 * 60))
  const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000)

  // Format as HH:MM:SS
  const hoursStr = String(totalHours).padStart(2, '0')
  const minutesStr = String(minutes).padStart(2, '0')
  const secondsStr = String(seconds).padStart(2, '0')
  countdownTime.value = `${hoursStr}:${minutesStr}:${secondsStr}`

  // Set color class based on time remaining
  if (totalHours > 48) {
    countdownClass.value = 'countdown-green'
  } else if (totalHours > 24) {
    countdownClass.value = 'countdown-yellow'
  } else {
    countdownClass.value = 'countdown-red'
  }
}

onMounted(async () => {
  // Initial load
  await fetchCurrentEpisode()
  updateCountdown()

  // Update every second
  clockInterval = setInterval(updateCountdown, 1000)

  // Refresh episode data every 5 minutes
  setInterval(fetchCurrentEpisode, 5 * 60 * 1000)
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

.countdown-time {
  font-family: 'Courier New', Courier, monospace;
  font-size: 1.6rem;
  font-weight: 900;
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
  padding: 0 8px 0 8px;
  margin-top: -4px;
}

.countdown-green {
  color: #4caf50;
}

.countdown-yellow {
  color: #ffc107;
}

.countdown-red {
  color: #f44336;
}

.countdown-live {
  color: #f44336;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style>