<template>
  <v-menu offset-y>
    <template v-slot:activator="{ props }">
      <v-btn text v-bind="props" :class="buttonClass" :style="buttonStyle">
        <v-icon left>mdi-television-play</v-icon>
        {{ currentEpisodeLabel }}
        <v-icon right>mdi-chevron-down</v-icon>
      </v-btn>
    </template>
    <v-list>
      <v-list-item
        v-for="episode in episodes"
        :key="episode.id"
        @click="selectEpisode(episode)"
      >
        <v-list-item-title>{{ episode.title }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script>
export default {
  name: 'EpisodeSelector',
  props: {
    episodes: {
      type: Array,
      required: true,
    },
    currentEpisode: {
      type: String,
      // Can be null initially, so not required
      default: null,
    },
    buttonClass: {
      type: String,
      default: ''
    },
    buttonStyle: {
      type: Object,
      default: () => ({})
    }
  },
  computed: {
    currentEpisodeLabel() {
      const savedEpisode = sessionStorage.getItem('selectedEpisode');
      if (savedEpisode) {
        const episode = this.episodes.find(e => e.value === savedEpisode);
        if (episode) return episode.title;
      }
      return this.currentEpisode
        ? this.episodes.find(e => e.value === this.currentEpisode)?.title || 'Select Episode'
        : 'Select Episode';
    },
  },
  methods: {
    selectEpisode(episode) {
      sessionStorage.setItem('selectedEpisode', episode.value);
      this.$emit('episode-changed', episode);
    },
  },
};
</script>
