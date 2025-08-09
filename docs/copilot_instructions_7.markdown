# Copilot Instructions 7: Finalize Disaffected Production Suite Tasks

## Overview
Copilot, your execution of `copilot_instructions_6.md` via `update.py` addressed most tasks but lacks verification, and future-proofing for new cue types (`VOX`, `MUS`, `LIVE`) was not implemented. As of July 9, 2025 (07:08 AM EDT), 18/19 issues are resolved, but Issue 18 (cue modals), virtual scrolling, asset/template management, and modal naming need confirmation, and new cue types need support. The user will execute the `update.py` script from `/mnt/process/show-build`. This document provides five specific tasks to verify and complete the remaining work, ensuring production-ready status with compatibility for Markdown files, YAML frontmatter, and directory structure at `/mnt/sync/disaffected/episodes/`. No Obsidian plugin implementation exists; `main.js` is for reference only and must be deleted. Documentation updates are reserved for Grok to ensure consistency. Prepare `update.py` with these tasks, using Claude Sonnet 4 and DeepSeek V3 (`python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code`) for validation. All tasks must achieve green checkmarks.

## Clarification on Obsidian and Rules
- **No Obsidian Implementation**: There is no active Obsidian plugin. References to Obsidian in documentation pertain to compatibility with Markdown files, YAML frontmatter, and directory structure. Delete `disaffected-ui/src/main.js` as it’s no longer relevant.
- **Documentation**: Grok exclusively updates `docs/00_rehydration_main.markdown`, `docs/03_features_and_integrations.markdown`, `docs/06_todo_and_issues.markdown`, and `docs/20_changelog.markdown`. Do not include documentation tasks in `update.py`.
- **Rehydration**: Do not update `rehydrate.md` directly; Grok updates `00_rehydration_main.markdown`, which is concatenated into the next `rehydrate.md` iteration via `generate_rehydrate.sh`.
- **Execution**: The user executes `update.py`; Copilot prepares it.

## Critique of Copilot’s Work
- **Successes**:
  - Fixed 18/19 issues (1–7, 9–13, 15–17, 19), including navigation drawer, rundown item types, unit tests, debouncing, episode selection, and authentication.
  - Removed redundant markdown files (`copilot_instructions_2.md`).
  - Implemented unit tests for `ContentEditor.vue` and `RundownManager.vue`.
- **Failures**:
  - Unverified changes for Issue 18 (`VoModal.vue`, `NatModal.vue`, `PkgModal.vue`), virtual scrolling (`RundownManager.vue`), asset/template management (`AssetsView.vue`, `TemplatesView.vue`), and modal naming (`ContentEditor.vue`, `EditorPanel.vue`).
  - No future-proofing for `VOX`, `MUS`, `LIVE` cue types.
- **Impact**: Unverified changes risk workflow disruptions; missing future-proofing limits scalability.

## Status
- **Fully Fixed (18/19)**: Issues 1–7, 9–13, 15–17, 19.
- **Not Fixed/Unverified (1/19)**: Issue 18 (cue modals, pending validation).
- **Tasks for Copilot**:
  1. Verify/complete Issue 18 (cue modals).
  2. Verify/implement virtual scrolling.
  3. Verify/complete asset/template management.
  4. Verify/standardize modal naming.
  5. Future-proof for `VOX`, `MUS`, `LIVE` cue types and delete `main.js`.

## Step-by-Step Instructions
All file paths are relative to `/mnt/process/show-build`. Verify existing files before overwriting, back up changes to `backup_md_20250709`, and validate with DeepSeek V3. Prepare `update.py` for the user to execute, capturing all outputs (stdout, stderr, tracebacks). Do not modify documentation files (`docs/00_rehydration_main.markdown`, `docs/03_features_and_integrations.markdown`, `docs/06_todo_and_issues.markdown`, `docs/20_changelog.markdown`).

### 1. Verify/Complete Issue 18: Implement `VO`, `NAT`, `PKG` Modals
**Problem**: `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` may have been implemented by `update.py` but lack verification. They must include fields and backend integration.
**Fix**:
1. **Verify Modal Files**:
   - **Paths**:
     - `disaffected-ui/src/components/modals/VoModal.vue`
     - `disaffected-ui/src/components/modals/NatModal.vue`
     - `disaffected-ui/src/components/modals/PkgModal.vue`
   - **Action**: Check if files match the code below. If mismatched or missing, rewrite. Ensure:
     - Fields: slug (required), text/description/title (required), duration (required, HH:MM:SS), timestamp (optional, HH:MM:SS), file (optional, `.mp3`/`.wav` for VO/NAT, `.mp4`/`.mpeg` for PKG).
     - Backend integration: `/next-id` for asset ID, `/preproc_vo`, `/preproc_nat`, `/preproc_pkg` for uploads.
     - Error handling with `vue-toastification`.
   - **VoModal.vue**:
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
         reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>.v-card { padding: 16px; }</style>
     ```
   - **NatModal.vue**:
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
       data() { return { slug: '', description: '', duration: '', timestamp: '', file: null }; },
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
               uploadForm.append('timestamp', this.timestamp || '00:00:00');
               await axios.post('http://192.168.51.210:8888/preproc_nat', uploadForm, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
             }
             this.$emit('submit', { description: this.description, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
             this.$toast.success('NAT cue added');
             this.reset();
           } catch (error) { this.$toast.error('Failed to add NAT cue'); }
         },
         reset() { this.slug = ''; this.description = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>.v-card { padding: 16px; }</style>
     ```
   - **PkgModal.vue**:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Package (PKG) Cue</v-card-title>
           <v-card-text>
             <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
             <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
             <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-file-input label="Video File (optional)" accept="video/mp4,video/mpeg" @change="file = $event"></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'PkgModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'pkg');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
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
         reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>.v-card { padding: 16px; }</style>
     ```
2. **Update ContentEditor.vue**:
   - **Path**: `disaffected-ui/src/components/ContentEditor.vue`
   - **Action**: Ensure modal integration with submit handlers. Add or verify:
     ```javascript
     methods: {
       submitVo(data) {
         this.scriptContent += `[VO: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.text}\n`;
         this.showVoModal = false;
         this.hasUnsavedChanges = true;
       },
       submitNat(data) {
         this.scriptContent += `[NAT: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.description}\n`;
         this.showNatModal = false;
         this.hasUnsavedChanges = true;
       },
       submitPkg(data) {
         this.scriptContent += `[PKG: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.title}\n`;
         this.showPkgModal = false;
         this.hasUnsavedChanges = true;
       }
     }
     ```
3. **Test**:
   - Run `npm run serve` and navigate to `/content-editor/0228`.
   - Trigger `VO`, `NAT`, `PKG` modals, submit valid (e.g., slug: `test-vo`, text: `Test VO`, duration: `00:01:00`) and invalid (e.g., empty slug) data.
   - Verify API calls: `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/next-id` and `/preproc_vo`, `/preproc_nat`, `/preproc_pkg`.
   - Check script content updates in `ContentEditor.vue` (e.g., `[VO: test-vo | 00:01:00]`).
   - Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate syntax.

### 2. Verify/Implement Virtual Scrolling in `RundownManager.vue`
**Problem**: `update.py` claimed to add `<v-virtual-scroll>` to `RundownManager.vue`, but it’s unverified, risking performance with large rundowns.
**Fix**:
1. **Verify File**:
   - **Path**: `disaffected-ui/src/components/RundownManager.vue`
   - **Action**: Check for `<v-virtual-scroll>` with `item-height="42"` and `height="600"`. If missing, replace the `rundown-list` div with:
     ```vue
     <v-virtual-scroll :items="safeRundownItems" :item-height="42" height="600">
       <template v-slot:default="{ item, index }">
         <v-card
           :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
           @click="$emit('select-item', index)"
           @dblclick="$emit('edit-item', index)"
           style="cursor: pointer;"
           draggable="true"
           @dragstart="$emit('drag-start', index)"
           @dragover.prevent="$emit('drag-over', index)"
           @drop.prevent="$emit('drag-drop', index)"
         >
           <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
             <div class="index-number">{{ (index + 1) * 10 }}</div>
             <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
             <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
             <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
           </div>
         </v-card>
       </template>
     </v-virtual-scroll>
     ```
2. **Test**:
   - Run `npm run serve` and load `/rundown/0228` with mock data (>100 items, e.g., via `/api/episodes/0228`).
   - Verify smooth scrolling in DevTools (Performance tab).
   - Test drag-and-drop reordering.
   - Run `npm test` to ensure `RundownManager.spec.js` passes.

### 3. Verify/Complete Asset/Template Management
**Problem**: `AssetsView.vue` and `TemplatesView.vue` were created by `update.py`, but CRUD functionality and API integration need verification.
**Fix**:
1. **Verify AssetsView.vue**:
   - **Path**: `disaffected-ui/src/views/AssetsView.vue`
   - **Action**: Confirm file matches:
     ```vue
     <template>
       <v-container fluid>
         <v-row>
           <v-col>
             <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
             <v-file-input label="Upload Asset" accept="image/*,video/*,audio/*" @change="uploadAsset"></v-file-input>
             <v-data-table
               :headers="[{ title: 'File', key: 'filename' }, { title: 'Type', key: 'type' }, { title: 'Actions', key: 'actions' }]"
               :items="assets"
               :loading="loading"
             >
               <template v-slot:item.actions="{ item }">
                 <v-btn icon="mdi-delete" size="small" color="error" @click="deleteAsset(item)"></v-btn>
               </template>
             </v-data-table>
           </v-col>
         </v-row>
       </v-container>
     </template>
     <script>
     export default {
       name: 'AssetsView',
       data() { return { assets: [], loading: false }; },
       methods: {
         async uploadAsset(file) {
           if (!file) return;
           this.loading = true;
           try {
             const formData = new FormData();
             formData.append('file', file);
             const response = await this.$axios.post('/api/assets', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.assets.push(response.data);
             this.$toast.success('Asset uploaded successfully');
           } catch (error) { this.$toast.error('Failed to upload asset'); }
           this.loading = false;
         },
         async deleteAsset(item) {
           try {
             await this.$axios.delete(`/api/assets/${item.id}`, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.assets = this.assets.filter(a => a.id !== item.id);
             this.$toast.success('Asset deleted successfully');
           } catch (error) { this.$toast.error('Failed to delete asset'); }
         },
         async loadAssets() {
           this.loading = true;
           try {
             const response = await this.$axios.get('/api/assets', {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.assets = response.data;
           } catch (error) { this.$toast.error('Failed to load assets'); }
           this.loading = false;
         }
       },
       mounted() { this.loadAssets(); }
     }
     </script>
     ```
2. **Verify TemplatesView.vue**:
   - **Path**: `disaffected-ui/src/views/TemplatesView.vue`
   - **Action**: Confirm file matches:
     ```vue
     <template>
       <v-container fluid class="pa-0">
         <v-row class="header-row ma-0">
           <v-col cols="6" class="pa-4">
             <h2 class="text-h4 font-weight-bold">Templates</h2>
           </v-col>
           <v-col cols="6" class="d-flex align-center justify-end pe-4">
             <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">New Template</v-btn>
           </v-col>
         </v-row>
         <v-row class="ma-0">
           <v-col cols="12" class="pa-4">
             <v-card>
               <v-data-table
                 :headers="headers"
                 :items="templates"
                 :loading="loading"
                 density="comfortable"
               >
                 <template v-slot:item.actions="{ item }">
                   <v-btn icon="mdi-pencil" size="small" variant="text" @click="editTemplate(item)"></v-btn>
                   <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteTemplate(item)"></v-btn>
                 </template>
               </v-data-table>
             </v-col>
         </v-row>
         <v-dialog v-model="showCreateDialog" max-width="500">
           <v-card>
             <v-card-title>Create Template</v-card-title>
             <v-card-text>
               <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
               <v-select v-model="newTemplate.type" :items="['segment', 'ad', 'promo', 'cta', 'trans']" label="Type" required></v-select>
               <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
               <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </v-container>
     </template>
     <script>
     export default {
       name: 'TemplatesView',
       data() { return {
         loading: false,
         showCreateDialog: false,
         newTemplate: { name: '', type: '', content: '' },
         headers: [
           { title: 'Name', key: 'name', sortable: true },
           { title: 'Type', key: 'type', sortable: true },
           { title: 'Last Modified', key: 'modified', sortable: true },
           { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
         ],
         templates: []
       }},
       methods: {
         async createTemplate() {
           this.loading = true;
           try {
             await this.$axios.post('/api/templates', this.newTemplate, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.loadTemplates();
             this.showCreateDialog = false;
             this.newTemplate = { name: '', type: '', content: '' };
             this.$toast.success('Template created successfully');
           } catch (error) { this.$toast.error('Failed to create template'); }
           this.loading = false;
         },
         async editTemplate(item) {
           this.loading = true;
           try {
             await this.$axios.put(`/api/templates/${item.id}`, item, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.loadTemplates();
             this.$toast.success('Template updated successfully');
           } catch (error) { this.$toast.error('Failed to update template'); }
           this.loading = false;
         },
         async deleteTemplate(item) {
           this.loading = true;
           try {
             await this.$axios.delete(`/api/templates/${item.id}`, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.templates = this.templates.filter(t => t.id !== item.id);
             this.$toast.success('Template deleted successfully');
           } catch (error) { this.$toast.error('Failed to delete template'); }
           this.loading = false;
         },
         async loadTemplates() {
           this.loading = true;
           try {
             const response = await this.$axios.get('/api/templates', {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.templates = response.data;
           } catch (error) { this.$toast.error('Failed to load templates'); }
           this.loading = false;
         }
       },
       mounted() { this.loadTemplates(); }
     }
     </script>
     <style scoped>.header-row { background: rgba(0, 0, 0, 0.03); border-bottom: 1px solid rgba(0, 0, 0, 0.05); }</style>
     ```
3. **Test**:
   - Run `npm run serve` and navigate to `/assets` and `/templates`.
   - Test upload, create, edit, delete operations.
   - Verify API calls: `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/assets` and `/api/templates`.
   - Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate syntax.

### 4. Verify/Standardize Modal Naming in `ContentEditor.vue` and `EditorPanel.vue`
**Problem**: `update.py` updated modal naming, but consistency (e.g., `showGraphicModal` vs. `showGfxModal`) is unverified.
**Fix**:
1. **Verify ContentEditor.vue**:
   - **Path**: `disaffected-ui/src/components/ContentEditor.vue`
   - **Action**: Confirm the following in the `<template>` section:
     ```vue
     <EditorPanel
       @show-asset-modal="showAssetModal = true"
       @show-template-modal="showTemplateModal = true"
       @show-gfx-modal="showGfxModal = true"
       @show-fsq-modal="showFsqModal = true"
       @show-sot-modal="showSotModal = true"
       @show-vo-modal="showVoModal = true"
       @show-nat-modal="showNatModal = true"
       @show-pkg-modal="showPkgModal = true"
       <!-- ... other props -->
     />
     <AssetModal
       :visible="showAssetModal"
       @update:visible="showAssetModal = $event"
       @asset-selected="insertAssetReference"
     />
     <TemplateModal
       :visible="showTemplateModal"
       @update:visible="showTemplateModal = $event"
       @template-selected="insertTemplateReference"
     />
     <GfxModal v-model:show="showGfxModal" @submit="submitGfx" />
     <FsqModal v-model:show="showFsqModal" @submit="submitFsq" />
     <SotModal v-model:show="showSotModal" @submit="submitSot" />
     <VoModal v-model:show="showVoModal" @submit="submitVo" />
     <NatModal v-model:show="showNatModal" @submit="submitNat" />
     <PkgModal v-model:show="showPkgModal" @submit="submitPkg" />
     ```
   - Confirm `data()` includes:
     ```javascript
     data() {
       return {
         showAssetModal: false,
         showTemplateModal: false,
         showGfxModal: false,
         showFsqModal: false,
         showSotModal: false,
         showVoModal: false,
         showNatModal: false,
         showPkgModal: false,
         // ... other data
       };
     }
     ```
   - If incorrect, replace `showAssetBrowserModal` → `showAssetModal`, `showTemplateManagerModal` → `showTemplateModal`, `showGraphicModal` → `showGfxModal`.
2. **Verify EditorPanel.vue**:
   - **Path**: `disaffected-ui/src/components/EditorPanel.vue`
   - **Action**: Confirm the `<template>` section matches:
     ```vue
     <template>
       <div class="editor-panel">
         <v-toolbar dense flat class="editor-toolbar">
           <v-btn icon @click="$emit('toggle-rundown-panel')">
             <v-icon>{{ showRundownPanel ? 'mdi-chevron-left' : 'mdi-chevron-right' }}</v-icon>
           </v-btn>
           <v-btn text @click="save">Save</v-btn>
           <v-btn text @click="$emit('show-asset-modal')">Add Asset</v-btn>
           <v-btn text @click="$emit('show-template-modal')">Add Template</v-btn>
           <v-btn text @click="$emit('show-gfx-modal')">Add GFX</v-btn>
           <v-btn text @click="$emit('show-fsq-modal')">Add FSQ</v-btn>
           <v-btn text @click="$emit('show-sot-modal')">Add SOT</v-btn>
           <v-btn text @click="$emit('show-vo-modal')">Add VO</v-btn>
           <v-btn text @click="$emit('show-nat-modal')">Add NAT</v-btn>
           <v-btn text @click="$emit('show-pkg-modal')">Add PKG</v-btn>
           <v-select
             v-model="editorMode"
             :items="['script', 'scratch', 'metadata', 'code']"
             label="Mode"
             dense
           ></v-select>
         </v-toolbar>
         <v-textarea
           v-model="scriptContent"
           @input="$emit('content-change', $event)"
           :placeholder="editorMode === 'script' ? scriptPlaceholder : scratchPlaceholder"
           rows="20"
         ></v-textarea>
       </div>
     </template>
     ```
3. **Test**:
   - Run `npm run serve` and navigate to `/content-editor/0228`.
   - Trigger each modal and verify correct display and functionality.
   - Run `npm test` to ensure `ContentEditor.spec.js` passes.

### 5. Future-Proof Cue Types and Delete `main.js`
**Problem**: The system lacks support for new cue types (`VOX`, `MUS`, `LIVE`), limiting scalability, and `main.js` is no longer relevant.
**Fix**:
1. **Create Placeholder Modals**:
   - **Paths**:
     - `disaffected-ui/src/components/modals/VoxModal.vue`
     - `disaffected-ui/src/components/modals/MusModal.vue`
     - `disaffected-ui/src/components/modals/LiveModal.vue`
   - **Action**: Create or update:
     - **VoxModal.vue**:
       ```vue
       <template>
         <v-dialog v-model="show" max-width="500">
           <v-card>
             <v-card-title>Add Vox Pop (VOX) Cue</v-card-title>
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
         name: 'VoxModal',
         props: { show: Boolean, episode: String, duplicateSlugs: Array },
         data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
         methods: {
           async submit() {
             const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
             try {
               const formData = new FormData();
               formData.append('type', 'vox');
               formData.append('slug', normalizedSlug);
               const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               const assetID = response.data.id;
               let mediaURL = '';
               if (this.file) {
                 const uploadForm = new FormData();
                 uploadForm.append('type', 'vox');
                 uploadForm.append('episode', this.episode);
                 uploadForm.append('asset_id', assetID);
                 uploadForm.append('file', this.file);
                 uploadForm.append('slug', normalizedSlug);
                 uploadForm.append('duration', this.duration);
                 uploadForm.append('timestamp', this.timestamp || '00:00:00');
                 await axios.post('http://192.168.51.210:8888/preproc_vox', uploadForm, {
                   headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
                 });
                 mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
               }
               this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
               this.$toast.success('VOX cue added');
               this.reset();
             } catch (error) { this.$toast.error('Failed to add VOX cue'); }
           },
           reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
         },
         watch: { show(val) { if (!val) this.reset(); } }
       }
       </script>
       <style scoped>.v-card { padding: 16px; }</style>
       ```
     - **MusModal.vue**:
       ```vue
       <template>
         <v-dialog v-model="show" max-width="500">
           <v-card>
             <v-card-title>Add Music (MUS) Cue</v-card-title>
             <v-card-text>
               <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
               <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
               <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="show = false">Cancel</v-btn>
               <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </template>
       <script>
       import axios from 'axios';
       export default {
         name: 'MusModal',
         props: { show: Boolean, episode: String, duplicateSlugs: Array },
         data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
         methods: {
           async submit() {
             const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
             try {
               const formData = new FormData();
               formData.append('type', 'mus');
               formData.append('slug', normalizedSlug);
               const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               const assetID = response.data.id;
               let mediaURL = '';
               if (this.file) {
                 const uploadForm = new FormData();
                 uploadForm.append('type', 'mus');
                 uploadForm.append('episode', this.episode);
                 uploadForm.append('asset_id', assetID);
                 uploadForm.append('file', this.file);
                 uploadForm.append('slug', normalizedSlug);
                 uploadForm.append('duration', this.duration);
                 uploadForm.append('timestamp', this.timestamp || '00:00:00');
                 await axios.post('http://192.168.51.210:8888/preproc_mus', uploadForm, {
                   headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
                 });
                 mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
               }
               this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
               this.$toast.success('MUS cue added');
               this.reset();
             } catch (error) { this.$toast.error('Failed to add MUS cue'); }
           },
           reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
         },
         watch: { show(val) { if (!val) this.reset(); } }
       }
       </script>
       <style scoped>.v-card { padding: 16px; }</style>
       ```
     - **LiveModal.vue**:
       ```vue
       <template>
         <v-dialog v-model="show" max-width="500">
           <v-card>
             <v-card-title>Add Live (LIVE) Cue</v-card-title>
             <v-card-text>
               <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
               <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
               <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="show = false">Cancel</v-btn>
               <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </template>
       <script>
       import axios from 'axios';
       export default {
         name: 'LiveModal',
         props: { show: Boolean, episode: String, duplicateSlugs: Array },
         data() { return { slug: '', title: '', duration: '', timestamp: '' }; },
         methods: {
           async submit() {
             const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
             try {
               const formData = new FormData();
               formData.append('type', 'live');
               formData.append('slug', normalizedSlug);
               const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               const assetID = response.data.id;
               this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID });
               this.$toast.success('LIVE cue added');
               this.reset();
             } catch (error) { this.$toast.error('Failed to add LIVE cue'); }
           },
           reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.show = false; }
         },
         watch: { show(val) { if (!val) this.reset(); } }
       }
       </script>
       <style scoped>.v-card { padding: 16px; }</style>
       ```
2. **Update ContentEditor.vue**:
   - **Path**: `disaffected-ui/src/components/ContentEditor.vue`
   - **Action**: Add support for new modals:
     ```vue
     <!-- Add to <template> -->
     <VoxModal v-model:show="showVoxModal" @submit="submitVox" />
     <MusModal v-model:show="showMusModal" @submit="submitMus" />
     <LiveModal v-model:show="showLiveModal" @submit="submitLive" />
     ```
     ```javascript
     // Add to data()
     showVoxModal: false,
     showMusModal: false,
     showLiveModal: false,
     ```
     ```javascript
     // Add to methods
     submitVox(data) {
       this.scriptContent += `[VOX: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.text}\n`;
       this.showVoxModal = false;
       this.hasUnsavedChanges = true;
     },
     submitMus(data) {
       this.scriptContent += `[MUS: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.title}\n`;
       this.showMusModal = false;
       this.hasUnsavedChanges = true;
     },
     submitLive(data) {
       this.scriptContent += `[LIVE: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\n${data.title}\n`;
       this.showLiveModal = false;
       this.hasUnsavedChanges = true;
     }
     ```
3. **Update EditorPanel.vue**:
   - **Path**: `disaffected-ui/src/components/EditorPanel.vue`
   - **Action**: Add buttons for new modals:
     ```vue
     <v-btn text @click="$emit('show-vox-modal')">Add VOX</v-btn>
     <v-btn text @click="$emit('show-mus-modal')">Add MUS</v-btn>
     <v-btn text @click="$emit('show-live-modal')">Add LIVE</v-btn>
     ```
4. **Delete main.js**:
   - **Path**: `disaffected-ui/src/main.js`
   - **Action**: Delete the file if it exists.
5. **Test**:
   - Run `npm run serve` and navigate to `/content-editor/0228`.
   - Trigger `VOX`, `MUS`, `LIVE` modals, verify placeholders work (submit disabled if backend endpoints `/preproc_vox`, `/preproc_mus`, `/preproc_live` are unavailable).
   - Verify `main.js` is deleted: `ls disaffected-ui/src/main.js` should return no file.
   - Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate syntax.

### Validation Instructions
- **DeepSeek V3**: Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate all code changes.
- **Unit Tests**: Run `npm test` to verify `ContentEditor.spec.js` and `RundownManager.spec.js`.
- **Manual Tests**:
  - Frontend: `curl http://192.168.51.210:8080/`
  - Backend: `curl http://192.168.51.210:8888/health`
  - Modals: Navigate to `/content-editor/0228`, trigger `VO`, `NAT`, `PKG`, `VOX`, `MUS`, `LIVE` modals, verify script updates.
  - Performance: Load `/rundown/0228` with >100 items, check scrolling in DevTools (Performance tab).
  - Assets/Templates: Test CRUD at `/assets` and `/templates`.
- **API Tests**:
  - `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/assets`
  - `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/templates`
  - `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/episodes/0228/cues`

*Last Updated: July 9, 2025*