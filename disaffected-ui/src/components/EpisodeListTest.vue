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

<script>
import axios from 'axios';

export default {
  name: 'EpisodeListTest',
  data() {
    return {
      episodes: [],
      loading: false,
      error: null,
      rawData: null,
    };
  },
  methods: {
    async fetchEpisodes() {
      this.loading = true;
      this.error = null;
      this.rawData = null;
      try {
        const response = await axios.get('/api/episodes');
        this.rawData = response.data;
        const episodesData = response.data.episodes || response.data;

        if (Array.isArray(episodesData)) {
            this.episodes = episodesData.map(ep => ({
              title: `${ep.episode_number}: ${ep.title || 'Untitled'}`,
              value: ep.episode_number,
            }));
        } else {
            this.episodes = [];
        }
      } catch (err) {
        this.error = 'Failed to fetch episodes. See console for details.';
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
pre {
  background-color: #f4f4f4;
  border: 1px solid #ddd;
  padding: 10px;
  white-space: pre-wrap;
}
</style>
