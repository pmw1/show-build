<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title>Add Voice Over (VO) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="$emit('update:show', false)">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'VoModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'vo');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'vo');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('VO cue added');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add VO cue'); }
    },
    reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.$emit('update:show', false); }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
