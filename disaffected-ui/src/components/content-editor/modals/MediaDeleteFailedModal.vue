<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600" persistent>
    <v-card>
      <v-card-title class="d-flex align-center bg-amber-darken-3">
        <v-icon class="mr-2" color="white">mdi-alert</v-icon>
        <span class="text-white">Media {{ actionVerb }} Failed</span>
      </v-card-title>

      <v-card-text class="pt-4">
        <p class="text-body-1 mb-3">
          The cue has been deleted from the script, but the associated media
          could not be {{ actionPastTense }}:
        </p>

        <div class="error-list pa-3 bg-surface-variant rounded">
          <div v-for="(e, i) in errors" :key="i" class="mb-3">
            <div class="d-flex align-center gap-2">
              <v-icon size="small" color="error">mdi-file-alert</v-icon>
              <span class="text-caption font-mono">{{ e.path }}</span>
            </div>
            <div class="text-caption text-error ml-6">
              {{ e.reason }}
            </div>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4 flex-wrap">
        <v-btn color="secondary" variant="text" class="ma-1" @click="acknowledge">
          Acknowledge
          <v-tooltip activator="parent" location="top">Leave the cue deleted; do nothing about the media</v-tooltip>
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="outlined" class="ma-1" @click="retry">
          <v-icon start size="small">mdi-refresh</v-icon>
          Acknowledge, Try Again
          <v-tooltip activator="parent" location="top">Retry the media {{ actionVerb.toLowerCase() }}</v-tooltip>
        </v-btn>
        <v-btn color="error" variant="elevated" class="ma-1" @click="restore">
          <v-icon start size="small">mdi-undo</v-icon>
          Cancel Deletion, Restore Cue
          <v-tooltip activator="parent" location="top">Put the cue back in the script and leave the media untouched</v-tooltip>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  errors: { type: Array, default: () => [] },
  // 'delete' | 'pool'
  action: { type: String, default: 'delete' }
})

const emit = defineEmits(['update:show', 'acknowledge', 'retry', 'restore'])

const actionVerb = computed(() => (props.action === 'pool' ? 'Release' : 'Delete'))
const actionPastTense = computed(() => (props.action === 'pool' ? 'released to the pool' : 'deleted'))

function acknowledge() {
  emit('acknowledge')
  emit('update:show', false)
}
function retry() {
  emit('retry')
  // Parent keeps modal open if the retry also fails.
}
function restore() {
  emit('restore')
  emit('update:show', false)
}
</script>

<style scoped>
.font-mono {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.75rem;
  word-break: break-all;
}
.gap-2 { gap: 8px; }
.error-list { max-height: 240px; overflow-y: auto; }
</style>
