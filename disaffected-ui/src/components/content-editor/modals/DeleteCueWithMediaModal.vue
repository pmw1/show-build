<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="560">
    <v-card>
      <v-card-title class="d-flex align-center bg-red-darken-2">
        <v-icon class="mr-2" color="white">mdi-delete-alert</v-icon>
        <span class="text-white">Delete Cue</span>
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel" color="white">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pt-4">
        <p class="text-body-1 mb-3">
          Delete <strong>{{ cueType }}</strong> cue<span v-if="cueSlug"> &ldquo;{{ cueSlug }}&rdquo;</span>
          from the script.
        </p>

        <p class="text-body-2 text-medium-emphasis mb-1">
          This cue is linked to {{ mediaFiles.length }} media file<span v-if="mediaFiles.length !== 1">s</span>.
          Choose what to do with {{ mediaFiles.length === 1 ? 'it' : 'them' }}:
        </p>

        <div class="mt-2 pa-3 bg-surface-variant rounded media-list">
          <div
            v-for="(f, i) in mediaFiles"
            :key="i"
            class="d-flex align-center gap-2 mb-1"
          >
            <v-icon size="small" color="primary">{{ iconFor(f) }}</v-icon>
            <span class="text-caption font-mono">{{ f }}</span>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4 flex-wrap">
        <v-btn color="secondary" variant="text" @click="cancel">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="error" variant="outlined" class="ma-1" @click="deleteOnly">
          Delete Cue
          <v-tooltip activator="parent" location="top">Remove the cue but leave the media files on disk</v-tooltip>
        </v-btn>
        <v-btn color="grey-darken-1" variant="tonal" class="ma-1" @click="releaseToPool">
          <v-icon start size="small">mdi-archive-arrow-down</v-icon>
          Release Media to Pool
          <v-tooltip activator="parent" location="top">
            Remove the cue and move its media into the show media pool (reusable later)
          </v-tooltip>
        </v-btn>
        <v-btn color="error" variant="elevated" class="ma-1" @click="deleteWithMedia">
          Delete Cue &amp; Media
          <v-tooltip activator="parent" location="top">Remove the cue and permanently delete its media files</v-tooltip>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { registerModalEsc } from '@/composables/useModalStack'

const props = defineProps({
  show: { type: Boolean, default: false },
  cueType: { type: String, default: '' },
  cueSlug: { type: String, default: '' },
  mediaFiles: { type: Array, default: () => [] }
})

const emit = defineEmits([
  'update:show',
  'delete-only',
  'delete-with-media',
  'delete-release-to-pool'
])

registerModalEsc(() => props.show, () => emit('update:show', false), 'DeleteCueWithMediaModal')

function iconFor(path) {
  const p = (path || '').toLowerCase()
  if (/\.(mp4|mov|mkv|webm|avi)$/.test(p)) return 'mdi-file-video'
  if (/\.(mp3|wav|aac|m4a|flac|ogg)$/.test(p)) return 'mdi-file-music'
  if (/\.(png|jpg|jpeg|gif|webp|svg)$/.test(p)) return 'mdi-file-image'
  return 'mdi-file'
}

function deleteOnly() {
  emit('delete-only')
  emit('update:show', false)
}

function deleteWithMedia() {
  emit('delete-with-media')
  emit('update:show', false)
}

function releaseToPool() {
  emit('delete-release-to-pool')
  emit('update:show', false)
}

function cancel() {
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
.media-list { max-height: 180px; overflow-y: auto; }
</style>
