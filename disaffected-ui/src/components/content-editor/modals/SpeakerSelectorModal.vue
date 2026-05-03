<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="400">
    <v-card>
      <v-card-title class="text-h6">
        <v-icon left>mdi-account-voice</v-icon>
        Select Speaker
      </v-card-title>

      <v-card-text>
        <div class="speaker-options">
          <v-btn
            v-for="option in speakerOptions"
            :key="option.value"
            :variant="selectedSpeaker === option.value ? 'elevated' : 'outlined'"
            :color="selectedSpeaker === option.value ? 'primary' : 'default'"
            class="speaker-option-btn"
            @click="selectedSpeaker = option.value"
          >
            <div class="speaker-option-content">
              <div class="speaker-color-indicator" :style="{ backgroundColor: option.color }"></div>
              <span class="speaker-label">{{ option.label }}</span>
            </div>
          </v-btn>
        </div>

        <!-- Custom Speaker Input -->
        <v-divider class="my-4"></v-divider>

        <v-text-field
          v-model="customSpeaker"
          label="Custom Speaker"
          placeholder="Enter custom speaker name"
          variant="outlined"
          density="comfortable"
          @keyup.enter="handleCustomSpeaker"
        >
          <template #append-inner>
            <v-btn
              icon
              size="small"
              @click="handleCustomSpeaker"
              :disabled="!customSpeaker.trim()"
            >
              <v-icon>mdi-plus</v-icon>
            </v-btn>
          </template>
        </v-text-field>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="$emit('update:show', false)">
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          @click="confirmSelection"
          :disabled="!selectedSpeaker"
        >
          Select
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import CueParser from '../../../utils/cueParser.js'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  currentSpeaker: {
    type: String,
    default: 'josh'
  }
})

const emit = defineEmits(['update:show', 'speaker-selected'])

const selectedSpeaker = ref('')
const customSpeaker = ref('')

const speakerOptions = computed(() => {
  return CueParser.getSpeakerOptions()
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    selectedSpeaker.value = props.currentSpeaker
    customSpeaker.value = ''
  }
})

function confirmSelection() {
  if (selectedSpeaker.value) {
    emit('speaker-selected', selectedSpeaker.value)
    emit('update:show', false)
  }
}

function handleCustomSpeaker() {
  if (customSpeaker.value.trim()) {
    const customValue = customSpeaker.value.toLowerCase().replace(/\s+/g, '-')
    selectedSpeaker.value = customValue
    customSpeaker.value = ''
  }
}
</script>

<style scoped>
.speaker-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.speaker-option-btn {
  height: 60px !important;
  padding: 8px !important;
}

.speaker-option-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.speaker-color-indicator {
  width: 20px;
  height: 4px;
  border-radius: 2px;
}

.speaker-label {
  font-size: 0.875rem;
  font-weight: 500;
}

/* Responsive Design */
@media (max-width: 500px) {
  .speaker-options {
    grid-template-columns: 1fr;
  }

  .speaker-option-btn {
    height: 50px !important;
  }
}
</style>