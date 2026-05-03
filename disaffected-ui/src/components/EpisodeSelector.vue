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

<script setup>
import { computed } from 'vue'

const props = defineProps({
  episodes: { type: Array, required: true },
  currentEpisode: { type: String, default: null },
  buttonClass: { type: String, default: '' },
  buttonStyle: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['episode-changed'])

const currentEpisodeLabel = computed(() => {
  const savedEpisode = sessionStorage.getItem('selectedEpisode')
  if (savedEpisode) {
    const episode = props.episodes.find(e => e.value === savedEpisode)
    if (episode) return episode.title
  }
  return props.currentEpisode
    ? props.episodes.find(e => e.value === props.currentEpisode)?.title || 'Select Episode'
    : 'Select Episode'
})

function selectEpisode(episode) {
  sessionStorage.setItem('selectedEpisode', episode.value)
  emit('episode-changed', episode)
}
</script>
