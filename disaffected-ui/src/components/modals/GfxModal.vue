<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600">
    <v-card>
      <v-card-title>Add GFX</v-card-title>
      <v-card-text>
        <v-text-field
          label="Slug"
          :model-value="slug"
          @update:model-value="$emit('update:slug', $event)"
          required
        ></v-text-field>
        <v-textarea
          label="Description"
          :model-value="description"
          @update:model-value="$emit('update:description', $event)"
          rows="3"
          required
        ></v-textarea>
        <div class="d-flex justify-space-between mt-4">
          <v-btn color="primary" @click="$emit('paste-from-clipboard')">Paste from Clipboard</v-btn>
          <v-btn color="primary" @click="$emit('select-file')">Select File</v-btn>
          <v-btn color="primary" @click="$emit('paste-url')">Paste URL</v-btn>
        </div>
        <v-img
          v-if="graphicPreview"
          :src="graphicPreview"
          max-height="200"
          class="mt-4"
        ></v-img>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="$emit('submit')">Attach</v-btn>
        <v-btn color="secondary" @click="$emit('update:show', false)">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'GfxModal',
  props: {
    show: { type: Boolean, required: true },
    slug: { type: String, default: '' },
    description: { type: String, default: '' },
    graphicPreview: { type: String, default: '' },
  },
  emits: [
    'update:show',
    'update:slug',
    'update:description',
    'paste-from-clipboard',
    'select-file',
    'paste-url',
    'submit',
  ],
};
</script>
