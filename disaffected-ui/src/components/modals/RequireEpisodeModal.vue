<template>
  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    max-width="500"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center bg-warning">
        <v-icon class="mr-2" color="warning">mdi-alert-circle</v-icon>
        Episode Required
      </v-card-title>

      <v-card-text class="pt-6">
        <v-alert
          type="warning"
          variant="tonal"
          class="mb-4"
        >
          You are trying to perform an action that requires an episode to be selected.
          Please select an episode to work in.
        </v-alert>

        <v-select
          v-model="selectedEpisode"
          :items="episodes"
          label="Select Episode"
          variant="outlined"
          density="comfortable"
          item-title="text"
          item-value="value"
          autofocus
          :loading="loadingEpisodes"
          placeholder="Choose an episode..."
        >
          <template v-slot:prepend-inner>
            <v-icon>mdi-television-play</v-icon>
          </template>
        </v-select>

        <div v-if="actionDescription" class="text-caption text-medium-emphasis mt-2">
          Action: {{ actionDescription }}
        </div>
      </v-card-text>

      <v-card-actions>
        <v-btn
          color="secondary"
          @click="cancel"
          variant="text"
        >
          Cancel
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          @click="confirm"
          :disabled="!selectedEpisode"
          variant="elevated"
        >
          Continue with Selected Episode
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';

export default {
  name: 'RequireEpisodeModal',
  emits: ['update:show', 'episode-selected', 'cancelled'],
  props: {
    show: {
      type: Boolean,
      default: false
    },
    actionDescription: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      selectedEpisode: '',
      episodes: [],
      loadingEpisodes: false
    };
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.loadEpisodes();
      }
    }
  },
  methods: {
    async loadEpisodes() {
      this.loadingEpisodes = true;
      try {
        const response = await axios.get('/api/episodes');
        if (response.data && response.data.episodes) {
          this.episodes = response.data.episodes.map(ep => ({
            text: `${ep.episode_number} - ${ep.title || 'Untitled'}`,
            value: ep.episode_number
          }));
        }
      } catch (error) {
        console.error('Failed to load episodes:', error);
      } finally {
        this.loadingEpisodes = false;
      }
    },

    confirm() {
      if (!this.selectedEpisode) return;

      // Emit the selected episode
      this.$emit('episode-selected', this.selectedEpisode);

      // Update sessionStorage to persist selection
      sessionStorage.setItem('currentEpisodeId', this.selectedEpisode);
      sessionStorage.setItem('selectedEpisode', this.selectedEpisode);

      // Close modal
      this.$emit('update:show', false);
    },

    cancel() {
      this.$emit('cancelled');
      this.$emit('update:show', false);
    },
    handleKeydown(event) {
      if (event.key === 'Escape' && this.show) {
        event.preventDefault();
        event.stopPropagation();
        this.cancel();
      }
    }
  },
  mounted() {
    document.addEventListener('keydown', this.handleKeydown);
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown);
  }
};
</script>

<style scoped>
.bg-warning {
  background-color: rgb(var(--v-theme-warning)) !important;
  color: white !important;
}
</style>
