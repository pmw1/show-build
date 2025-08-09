# Copilot Instructions 6: Finalize Disaffected Production Suite for Production-Ready Status

## Overview
Copilot, your repeated failures across `copilot_instructions_2.md` to `copilot_instructions_5.md` have delayed the Disaffected Production Suite, a critical web-based application for streamlining broadcast content creation for the "Disaffected" podcast and TV show. As of July 9, 2025 (12:37 AM EDT), `review_files.txt` and prior instructions confirm 18/19 issues are resolved, but Issue 18 (cue modals), virtual scrolling, asset/template management, modal naming, and Obsidian plugin alignment remain incomplete. This document sets definitive milestones to achieve all green checkmarks, ensuring a production-ready system with full Obsidian compatibility. Follow these explicit, numbered steps exactly, using Claude Sonnet 4, with DeepSeek V3 (local, 128k tokens) for validation. No excuses—execute or face accountability.

## Critique of Copilot’s Work
- **Successes**: 18/19 issues fixed (1–7, 9–13, 15–17, 19), including navigation drawer, rundown item types, unit tests, debouncing, episode selection, and authentication.
- **Failures**:
  - **Issue 18**: `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` are placeholders, blocking script editing.
  - **Virtual Scrolling**: Missing in `RundownManager.vue`, risking performance.
  - **Asset/Template Management**: `AssetsView.vue`, `TemplatesView.vue` unimplemented.
  - **Modal Naming**: Inconsistent (`showAssetBrowser`, `showGfxModal`) in `ContentEditor.vue`.
  - **Obsidian Plugin**: `main.js` lacks `VO`, `NAT`, `PKG` support.
- **Impact**: These gaps prevent production readiness and workflow efficiency.

## Status
- **Fully Fixed (18/19)**: Issues 1–7, 9–13, 15–17, 19.
- **Not Fixed (1/19)**: Issue 18 (cue modals).
- **Additional Tasks**: Virtual scrolling, asset/template management, modal naming, plugin alignment, future-proofing for new cue types (`VOX`, `MUS`, `LIVE`).

## Milestones for Full Resolution
1. **Complete Issue 18: Implement `VO`, `NAT`, `PKG` Modals** (Critical)
2. **Implement Virtual Scrolling in `RundownManager.vue`** (Performance)
3. **Complete Asset/Template Management in `AssetsView.vue`, `TemplatesView.vue`** (Workflow)
4. **Standardize Modal Naming in `ContentEditor.vue`** (Maintainability)
5. **Align Obsidian Plugin (`main.js`) with Frontend** (Compatibility)
6. **Update Documentation** (Clarity)
7. **Future-Proof for New Cue Types** (Scalability)

## Step-by-Step Fixes
### 1. Issue 18: Implement `VO`, `NAT`, `PKG` Modals
**Problem**: Placeholders lack fields and backend integration, blocking script editing.
**Fix**:
1. Replace `disaffected-ui/src/components/modals/VoModal.vue` with:
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
2. Replace `disaffected-ui/src/components/modals/NatModal.vue` with:
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
3. Replace `disaffected-ui/src/components/modals/PkgModal.vue` with:
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
4. Test:
   - Navigate to `/content-editor/0228`.
   - Open each modal, submit with valid/invalid data, verify API calls (`/next-id`, `/preproc_*`).
   - Check script content updates in `ContentEditor.vue`.
   - Run: `npm run serve` and `curl http://192.168.51.210:8888/health`.

### 2. Virtual Scrolling in `RundownManager.vue`
**Problem**: Missing `<v-virtual-scroll>`, risking performance with large rundowns.
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Replace `rundown-items-container` with:
   ```vue
   <v-virtual-scroll :items="safeRundownItems" :item-height="42" height="600">
     <template v-slot:default="{ item, index }">
       <v-card
         :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
         @click="$emit('select-item', index)"
         @dblclick="$emit('edit-item', index)"
         style="cursor: pointer;"
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
3. Test:
   - Load `/rundown/0228` with mock data (>100 items).
   - Verify smooth scrolling in DevTools (Performance tab).
   - Run: `npm run serve`.

### 3. Asset/Template Management
**Problem**: `AssetsView.vue`, `TemplatesView.vue` are placeholders, blocking asset and template workflows.
**Fix**:
1. Create `disaffected-ui/src/views/AssetsView.vue`:
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
2. Create `disaffected-ui/src/views/TemplatesView.vue`:
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
           </v-card>
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
     data: () => ({
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
     }),
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
3. Test:
   - Navigate to `/assets` and `/templates`.
   - Verify upload, CRUD operations, and API calls (`/api/assets`, `/api/templates`).
   - Run: `npm run serve` and `curl http://192.168.51.210:8888/health`.

### 4. Standardize Modal Naming in `ContentEditor.vue`
**Problem**: Inconsistent naming (`showAssetBrowser`, `showGfxModal`, `showGraphicModal`).
**Fix**:
1. Open `disaffected-ui/src/components/ContentEditor.vue`.
2. Replace modal data properties and event handlers:
   ```javascript
   data() {
     return {
       // ... other data
       showAssetBrowserModal: false,
       showTemplateManagerModal: false,
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
3. Update template:
   ```vue
   <EditorPanel
     @show-asset-browser-modal="showAssetBrowserModal = true"
     @show-template-manager-modal="showTemplateManagerModal = true"
     @show-gfx-modal="showGfxModal = true"
     @show-fsq-modal="showFsqModal = true"
     @show-sot-modal="showSotModal = true"
     @show-vo-modal="showVoModal = true"
     @show-nat-modal="showNatModal = true"
     @show-pkg-modal="showPkgModal = true"
     <!-- ... other props -->
   />
   ```
4. Test:
   - Navigate to `/content-editor/0228`.
   - Trigger each modal,