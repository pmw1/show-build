<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title class="d-flex align-center bg-error">
        <v-icon class="mr-2" color="white">mdi-alert-circle</v-icon>
        <span class="text-white">Delete Image Cue</span>
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel" color="white">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pt-4">
        <p class="text-body-1 mb-4">
          This will delete the image cue <strong>{{ cueSlug }}</strong> from your script.
        </p>

        <p class="text-body-2 text-medium-emphasis">
          What would you like to do with the associated media file?
        </p>

        <div v-if="imagePath" class="mt-2 pa-3 bg-surface-variant rounded">
          <div class="d-flex align-center gap-2">
            <v-icon size="small" color="primary">mdi-file-image</v-icon>
            <span class="text-caption font-mono">{{ imagePath }}</span>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-btn
          color="secondary"
          variant="outlined"
          @click="cancel"
        >
          Cancel
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          color="warning"
          variant="outlined"
          @click="deletePreserveAssets"
        >
          Delete Cue Only
          <v-tooltip activator="parent" location="top">
            Delete the cue but keep the image file
          </v-tooltip>
        </v-btn>
        <v-btn
          color="error"
          variant="elevated"
          @click="deleteWithAssets"
        >
          Delete Cue & Media
          <v-tooltip activator="parent" location="top">
            Delete both the cue and the image file
          </v-tooltip>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'DeleteImgCueModal',
  emits: ['update:show', 'delete-with-assets', 'delete-preserve-assets'],
  props: {
    show: {
      type: Boolean,
      default: false
    },
    cueSlug: {
      type: String,
      default: ''
    },
    imagePath: {
      type: String,
      default: ''
    }
  },
  methods: {
    deleteWithAssets() {
      this.$emit('delete-with-assets');
      this.$emit('update:show', false);
    },

    deletePreserveAssets() {
      this.$emit('delete-preserve-assets');
      this.$emit('update:show', false);
    },

    cancel() {
      this.$emit('update:show', false);
    }
  }
};
</script>

<style scoped>
.font-mono {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.75rem;
}

.gap-2 {
  gap: 8px;
}
</style>
