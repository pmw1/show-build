<template>
  <div>
    <h1>Episode List Test</h1>
    <v-btn @click="fetchEpisodes">Fetch Episodes</v-btn>
    <div v-if="loading">Loading...</div>
    <div v-if="error">{{ error }}</div>
    <ul v-if="episodes.length">
      <li v-for="episode in episodes" :key="episode.value">
        {{ episode.title }}
      </li>
    </ul>
    <div v-else>
      No episodes found.
    </div>
     <pre><code>{{ rawData }}</code></pre>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const episodes = ref([])
const loading = ref(false)
const error = ref(null)
const rawData = ref(null)

async function fetchEpisodes() {
  loading.value = true
  error.value = null
  rawData.value = null
  try {
    const response = await axios.get('/api/episodes')
    rawData.value = response.data
    const episodesData = response.data.episodes || response.data
    episodes.value = Array.isArray(episodesData)
      ? episodesData.map(ep => ({ title: `${ep.episode_number}: ${ep.title || 'Untitled'}`, value: ep.episode_number }))
      : []
  } catch {
    error.value = 'Failed to fetch episodes. See console for details.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
pre {
  background-color: #f4f4f4;
  border: 1px solid #ddd;
  padding: 10px;
  white-space: pre-wrap;
}
</style>
