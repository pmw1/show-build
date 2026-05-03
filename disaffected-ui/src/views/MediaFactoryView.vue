<template>
  <v-container fluid class="media-factory pa-4">
    <v-row>
      <v-col>
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="purple">mdi-factory</v-icon>
            <span>MediaFactory</span>
          </v-card-title>
        </v-card>

        <v-tabs v-model="activeTab" color="purple" class="mt-4 mb-4">
          <v-tab value="posters">
            <v-icon class="mr-2">mdi-image-auto-adjust</v-icon>
            Posters
          </v-tab>
          <v-tab value="graphics" disabled>
            <v-icon class="mr-2">mdi-palette</v-icon>
            Graphics
            <v-chip size="x-small" class="ml-2">Soon</v-chip>
          </v-tab>
          <v-tab value="audio" disabled>
            <v-icon class="mr-2">mdi-waveform</v-icon>
            Audio
            <v-chip size="x-small" class="ml-2">Soon</v-chip>
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <v-tabs-window-item value="posters">
            <PosterStudio />
          </v-tabs-window-item>

          <v-tabs-window-item value="graphics">
            <v-card flat class="pa-8 text-center">
              <v-icon size="64" color="grey-lighten-1">mdi-palette-outline</v-icon>
              <h3 class="text-h6 mt-4 text-grey">Graphics Studio</h3>
              <p class="text-grey">Coming soon - Lower thirds, bumpers, and motion graphics</p>
            </v-card>
          </v-tabs-window-item>

          <v-tabs-window-item value="audio">
            <v-card flat class="pa-8 text-center">
              <v-icon size="64" color="grey-lighten-1">mdi-waveform</v-icon>
              <h3 class="text-h6 mt-4 text-grey">Audio Studio</h3>
              <p class="text-grey">Coming soon - Music beds, sound effects, and audio processing</p>
            </v-card>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import PosterStudio from '@/components/mediafactory/PosterStudio.vue' // eslint-disable-line no-unused-vars

const activeTab = ref('posters')
</script>

<style scoped>
.media-factory {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
