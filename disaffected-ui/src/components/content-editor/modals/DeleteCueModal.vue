<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600" persistent>
    <!-- Red overlay background -->
    <template #default="{ isActive }">
      <div v-if="isActive" class="delete-cue-overlay"></div>
      <v-card class="delete-cue-card">
        <v-card-title class="d-flex align-center text-error">
          <v-icon class="mr-2" color="error" size="large">mdi-alert-circle</v-icon>
          Delete Cue Block
        </v-card-title>
        
        <v-card-text class="py-4">
          <div class="mb-4">
            <p class="text-h6 mb-2">Are you sure you want to delete this cue?</p>
            <p class="text-body-2 text-medium-emphasis">This action cannot be undone.</p>
          </div>
          
          <!-- Cue Details -->
          <v-card variant="outlined" class="cue-details-card mb-4">
            <v-card-text class="py-3">
              <div class="d-flex align-center mb-2">
                <v-chip :color="getCueColor(cueData.type)" size="small" class="mr-2">
                  {{ cueData.type }}
                </v-chip>
                <span class="text-subtitle-2">{{ cueData.slug || 'No slug' }}</span>
              </div>
              
              <div v-if="cueData.description" class="mb-2">
                <span class="text-body-2 text-medium-emphasis">Description: </span>
                <span class="text-body-2">{{ cueData.description }}</span>
              </div>
              
              <div v-if="cueData.mediaUrl" class="mb-2">
                <span class="text-body-2 text-medium-emphasis">Media: </span>
                <span class="text-body-2">{{ cueData.mediaUrl }}</span>
              </div>
              
              <div v-if="cueData.assetId" class="mb-2">
                <span class="text-body-2 text-medium-emphasis">Asset ID: </span>
                <code class="text-body-2">{{ cueData.assetId }}</code>
              </div>
              
              <div class="text-caption text-medium-emphasis">
                Lines {{ startLine + 1 }} - {{ endLine + 1 }}
              </div>
            </v-card-text>
          </v-card>
        </v-card-text>
        
        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="secondary" @click="cancel" variant="outlined">
            Cancel
          </v-btn>
          <v-btn 
            color="error" 
            @click="confirmDelete"
            variant="elevated"
            class="ml-2"
          >
            <v-icon left>mdi-delete</v-icon>
            Delete Cue
          </v-btn>
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  cueData: {
    type: Object,
    default: () => ({})
  },
  startLine: {
    type: Number,
    default: 0
  },
  endLine: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:show', 'delete', 'cancel'])

function handleKeydown(event) {
  if (event.key === 'Escape' && props.show) {
    cancel()
  }
}

function getCueColor(cueType) {
  if (!cueType) return '#666'
  const colorName = getColorValue(cueType.toLowerCase())
  return resolveVuetifyColor(colorName)
}

function cancel() {
  emit('update:show', false)
  emit('cancel')
}

function confirmDelete() {
  emit('delete', {
    startLine: props.startLine,
    endLine: props.endLine,
    cueData: props.cueData
  })
  emit('update:show', false)
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.delete-cue-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(244, 67, 54, 0.1);
  z-index: 1000;
  pointer-events: none;
}

.delete-cue-card {
  position: relative;
  z-index: 1001;
  border: 2px solid #f44336;
  box-shadow: 0 8px 32px rgba(244, 67, 54, 0.3);
}

.cue-details-card {
  background-color: #fafafa;
  border-left: 4px solid #f44336;
}
</style>