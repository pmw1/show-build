<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Package (PKG) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>
        <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Video File (optional)" accept="video/mp4,video/mpeg" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug || !title || !duration">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
import { cueModalMixin } from '@/mixins/cueModalMixin';

export default {
  name: 'PkgModal',
  mixins: [cueModalMixin],
  props: {
    show: Boolean,
    episode: String,
    duplicateSlugs: {
      type: Array,
      default: () => []
    },
    cueType: {
      type: String,
      default: 'pkg'
    }
  },
  data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async handleSubmit() {
      // Validate before submitting
      if (!this.slug || !this.title || !this.duration) {
        return;
      }
      await this.submit();
    },
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'pkg');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('/assetid/generate-legacy', formData, {
          headers: {
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'pkg');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_pkg', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/video/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('PKG cue added');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add PKG cue'); }
    },
    reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.$emit('update:show', false); }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
