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

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  actionDescription: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:show', 'episode-selected', 'cancelled']);

const selectedEpisode = ref('');
const episodes = ref([]);
const loadingEpisodes = ref(false);

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadEpisodes();
  }
});

async function loadEpisodes() {
  loadingEpisodes.value = true;
  try {
    const response = await axios.get('/api/episodes');
    if (response.data && response.data.episodes) {
      episodes.value = response.data.episodes.map(ep => ({
        text: `${ep.episode_number} - ${ep.title || 'Untitled'}`,
        value: ep.episode_number
      }));
    }
  } catch (error) {
    console.error('Failed to load episodes:', error);
  } finally {
    loadingEpisodes.value = false;
  }
}

function confirm() {
  if (!selectedEpisode.value) return;

  // Emit the selected episode
  emit('episode-selected', selectedEpisode.value);

  // Update sessionStorage to persist selection
  sessionStorage.setItem('currentEpisodeId', selectedEpisode.value);
  sessionStorage.setItem('selectedEpisode', selectedEpisode.value);

  // Close modal
  emit('update:show', false);
}

function cancel() {
  emit('cancelled');
  emit('update:show', false);
}

function handleKeydown(event) {
  if (event.key === 'Escape' && props.show) {
    event.preventDefault();
    event.stopPropagation();
    cancel();
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.bg-warning {
  background-color: rgb(var(--v-theme-warning)) !important;
  color: white !important;
}
</style>
