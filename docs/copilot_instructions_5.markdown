# Copilot Instructions 5: Complete Disaffected Production Suite Fixes and Align Obsidian Plugin

## Overview
Copilot, your partial execution of `copilot_instructions_4.md` (July 8, 2025) fixed Issues 14 (`ContentEditor.vue` `itemTypes`), 15 (drag-and-drop test), and authentication (`router/index.js`), but failed on Issue 18 (`VO`, `NAT`, `PKG` modals), virtual scrolling, asset/template management, and documentation. Modal visibility names in `ContentEditor.vue` are inconsistent, and the Obsidian plugin (`main.js`) lacks `VO`, `NAT`, `PKG` modals. This document provides explicit steps to complete these tasks, standardize naming, align the plugin with the frontend, and prepare for potential new element cue types (e.g., `VOX`, `MUS`, `LIVE`). Use Claude Sonnet 4 with DeepSeek V3 (local, 128k tokens) for validation.

## Critique of Copilot’s Work
- **Successes**: Fixed Issue 14 (`ad` in `itemTypes`), Issue 15 (drag-and-drop test), authentication (`useAuth`).
- **Failures**:
  - Issue 18: `VoModal`, `NatModal`, `PkgModal` unimplemented.
  - Virtual Scrolling: Missing in `RundownManager.vue`.
  - Asset/Template Management: `AssetsView.vue`, `TemplatesView.vue` unverified.
  - Documentation: No updates.
  - Modal Naming: Inconsistent (`showAssetBrowser`, `showGfxModal`, `showGraphicModal`).
  - Plugin: `main.js` lacks `VO`, `NAT`, `PKG` modals.
- **Impact**: Incomplete modals and misalignment hinder broadcast workflow; naming inconsistency reduces maintainability.

## Status
- **Fully Fixed (18/19)**: Issues 1–7, 9–13, 15–17, 19, 14.
- **Not Fixed (1/19)**: Issue 18.
- **Additional Tasks**: Virtual scrolling, asset/template management, documentation, modal naming, plugin alignment, future element cues.

## Step-by-Step Fixes
### 1. Issue 18: Implement `VO`, `NAT`, `PKG` Modals
**Problem**: `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` are placeholders.
**Fix**:
1. **VoModal.vue** (`disaffected-ui/src/components/modals/VoModal.vue`):
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
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
           <v-btn color="error" @click="show = false">Cancel</v-btn>
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
     data() {
       return { slug: '', text: '', duration: '', timestamp: '', file: null };
     },
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
           this.$emit('submit', {
             text: this.text,
             duration: this.duration,
             timestamp: this.timestamp,
             slug: normalizedSlug,
             assetID,
             mediaURL
           });
           this.$toast.success('VO cue added');
           this.reset();
         } catch (error) {
           this.$toast.error('Failed to add VO cue');
         }
       },
       reset() {
         this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false;
       }
     },
     watch: { show(val) { if (!val) this.reset(); } }
   }
   </script>
   <style scoped>
   .v-card { padding: 16px; }
   </style>
   ```
2. **NatModal.vue** (`disaffected-ui/src/components/modals/NatModal.vue`):
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
       <v-card>
         <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
         <v-card-text>
           <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
           <v-textarea v-model="description" label="Description" required :rules="[v => !!v || 'Description is required']" rows="4"></v-textarea>
           <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
         </v-card-text>
         <v-card-actions>
           <v-spacer></v-spacer>
           <v-btn color="error" @click="show = false">Cancel</v-btn>
           <v-btn color="success" @click="submit" :disabled="!slug || !description || !duration">Submit</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>
   <script>
   import axios from 'axios';
   export default {
     name: 'NatModal',
     props: { show: Boolean, episode: String, duplicateSlugs: Array },
     data() {
       return { slug: '', description: '', duration: '', timestamp: '', file: null };
     },
     methods: {
       async submit() {
         const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
         try {
           const formData = new FormData();
           formData.append('type', 'nat');
           formData.append('slug', normalizedSlug);
           const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           const assetID = response.data.id;
           let mediaURL = '';
           if (this.file) {
             const uploadForm = new FormData();
             uploadForm.append('type', 'nat');
             uploadForm.append('episode', this.episode);
             uploadForm.append('asset_id', assetID);
             uploadForm.append('file', this.file);
             uploadForm.append('slug', normalizedSlug);
             uploadForm.append('duration', this.duration);
             uploadForm.append('timestamp', this.timestamp || 'itlement cue types (e.g., `VOX`, `MUS`, `LIVE`) if confirmed in Copilot’s new session or future requirements.

### Next Steps
- **Copilot Session**: Once Copilot’s new session is fully rehydrated, share