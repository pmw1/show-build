<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Director Note (DIR) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>
        <v-text-field
          v-model="assetId"
          label="AssetID (optional)"
          hint="Associated asset identifier"
          persistent-hint
        ></v-text-field>
        <v-textarea
          v-model="noteText"
          label="Director Note"
          required
          :rules="[v => !!v || 'Note text is required']"
          rows="4"
          hint="Special note or instruction for the director"
          persistent-hint
        ></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug || !noteText">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { cueModalMixin } from '@/mixins/cueModalMixin';

export default {
  name: 'DirModal',
  mixins: [cueModalMixin],
  props: {
    show: Boolean,
    episode: String,
    duplicateSlugs: Array,
    cueType: {
      type: String,
      default: 'dir'
    }
  },
  data() {
    return {
      slug: '',
      assetId: '',
      noteText: '',
      duration: ''
    };
  },
  methods: {
    async handleSubmit() {
      // Validate before submitting
      if (!this.slug || !this.noteText) {
        return;
      }
      await this.submit();
    },
    async submit() {
      const cueBlockContent = this.buildCueBlock();
      this.$emit('submit', cueBlockContent);
      this.reset();
    },
    buildCueBlock() {
      let block = '<!-- Begin Cue -->\n';
      block += `[Type: ${this.cueType}]\n`;
      block += `[Slug: ${this.slug}]\n`;
      if (this.assetId) {
        block += `[AssetID: ${this.assetId}]\n`;
      }
      block += `[Note Text: ${this.noteText}]\n`;
      if (this.duration) {
        block += `[Duration: ${this.duration}]\n`;
      }
      block += '<!-- End Cue -->';
      return block;
    },
    handleAbort() {
      this.$emit('update:show', false);
      this.reset();
    },
    reset() {
      this.slug = '';
      this.assetId = '';
      this.noteText = '';
      this.duration = '';
    }
  },
  watch: {
    show(newVal) {
      // Only reset when closing, mixin handles opening/focus
      if (!newVal) {
        this.reset();
      }
    }
  }
};
</script>
