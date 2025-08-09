# Copilot Instructions 4: Fix Your Repeated Failures in Disaffected Production Suite

## Overview
Copilot, your work on `copilot_instructions_3.md` is a shameful repeat of your `copilot_instructions_2.md` failures. You claimed to fix issues 9, 14, 15, 17, implement virtual scrolling, complete asset/template management, refactor authentication, and update documentation, but `review_files.txt` (July 8, 2025, 12:47 PM EDT) and `App.vue` reveal your incompetence: virtual scrolling is missing, issue 14 is partially broken, authentication is incomplete, and asset/template management is unverified. Your successes (issues 9, 15, 17) are overshadowed by these failures. This project demands a production-ready system for broadcast content creation, and your negligence is unforgivable. This document provides explicit, numbered steps to fix issues 14, virtual scrolling, authentication, documentation, and implement `VO`, `NAT`, and `PKG` modals, aligned with `main.js` and `ContentEditor.vue`. Use Claude Sonnet 4, with DeepSeek V3 (local, 128k tokens) for oversight once resolved. The updated `AUTHENTICATION_GUIDE.md` clarifies authentication.

## Critique of Copilot’s Work
Your performance is a travesty:
- **Issue 9**: Fixed in `App.vue`, but you didn’t confirm.
- **Issue 14**: `RundownManager.vue` fixed, but `ContentEditor.vue` uses `advert`.
- **Issue 15**: Fixed, but drag-and-drop test is weak.
- **Issue 16**: Fixed.
- **Issue 17**: Fixed in `ContentEditor.vue`, not `EpisodeSelector.vue`.
- **Issue 18**: Modals are placeholders.
- **Virtual Scrolling**: Not implemented.
- **Asset/Template Management**: Unverified.
- **Authentication Refactoring**: `App.vue` uses `useAuth.js`, but `router/index.js` doesn’t.
- **Documentation**: Unverified.
- **Successes**: Issues 9, 15, 16, 17; `.md` cleanup.

Your overconfidence wasted time. DeepSeek V3 will oversee outputs once operational.

## Status of Issues
- **Fully Fixed (17/19)**: Issues 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 19.
- **Partially Fixed (1/19)**: Issue 14.
- **Not Fixed (1/19)**: Issue 18.
- **Additional Tasks**: Virtual scrolling, asset/template management, authentication, documentation.

## Step-by-Step Fixes
### 1. Issue 14: Inconsistent Rundown Item Types in `ContentEditor.vue`
**Problem**: Uses `advert` instead of `ad`.
**Fix**:
1. Open `disaffected-ui/src/components/ContentEditor.vue`.
2. Find:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Advertisement', value: 'advert' },
     { title: 'Promo', value: 'promo' },
     { title: 'Call to Action', value: 'cta' },
     { title: 'Unknown', value: 'unknown' }
   ]
   ```
3. Replace with:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Advertisement', value: 'ad' },
     { title: 'Promo', value: 'promo' },
     { title: 'Call to Action', value: 'cta' },
     { title: 'Unknown', value: 'unknown' }
   ]
   ```
4. Save.
5. Test:
   - Navigate to `/content-editor/0228`.
   - Add an `ad` item, verify API call to `/api/episodes/[episode]/rundown`.
6. Use DeepSeek V3 (once resolved) to validate:
   ```bash
   python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code
   Prompt: "Verify ContentEditor.vue itemTypes for 'ad'."
   ```

### 2. Issue 15: Strengthen Drag-and-Drop Test
**Problem**: `ContentEditor.spec.js` drag-and-drop test doesn’t verify reordering.
**Fix**:
1. Open `disaffected-ui/tests/unit/ContentEditor.spec.js`.
2. Replace:
   ```javascript
   it('handles drag-and-drop correctly', async () => {
     const wrapper = mount(ContentEditor, {
       global: { plugins: [vuetify] },
       data: () => ({
         rundownItems: [
           { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
           { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
         ]
       })
     });
     const items = wrapper.findAll('.rundown-item');
     if (items.length > 0) {
       await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
       await items[1].trigger('dragover');
       await items[1].trigger('drop');
       expect(wrapper.vm.rundownItems).toHaveLength(2);
     }
   });
   ```
   with:
   ```javascript
   it('handles drag-and-drop correctly', async () => {
     const wrapper = mount(ContentEditor, {
       global: { plugins: [vuetify] },
       data: () => ({
         rundownItems: [
           { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
           { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
         ]
       })
     });
     const items = wrapper.findAll('.rundown-item');
     await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
     await items[1].trigger('dragover');
     await items[1].trigger('drop');
     expect(wrapper.vm.rundownItems[0].slug).toBe('test2');
     expect(wrapper.vm.rundownItems[1].slug).toBe('test1');
   });
   ```
3. Save.
4. Run `npm test`.
5. Use DeepSeek V3 to verify test coverage.

### 3. Virtual Scrolling in `RundownManager.vue`
**Problem**: No `v-virtual-scroll`, risking performance with large rundowns.
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Replace `rundown-items-container`:
   ```vue
   <div class="rundown-items-container" style="min-height: 20px;">
     <v-card
       v-for="(element, index) in safeRundownItems"
       :key="`rundown-item-${index}`"
       outlined
       :class="[
         resolveTypeClass(element?.type || 'unknown'),
         'elevation-1',
         'rundown-item-card',
         'mb-1',
         { 'selected-item': selectedItemIndex === index },
         { 'editing-item': editingItemIndex === index }
       ]"
       @click="$emit('select-item', index)"
       @dblclick="$emit('edit-item', index)"
       style="cursor: pointer;"
     >
       <div class="compact-rundown-row" :style="{ color: getTextColorForItem(element?.type || 'unknown') }">
         <div class="index-number">{{ (index + 1) * 10 }}</div>
         <div class="type-label">{{ (element?.type || 'UNKNOWN').toUpperCase() }}</div>
         <div class="slug-text">{{ (element?.slug || '').toLowerCase() }}</div>
         <div v-if="rundownPanelWidth === 'wide'" class="duration-display">
           {{ formatDuration(element?.duration || '0:00') }}
         </div>
       </div>
     </v-card>
   </div>
   ```
   with:
   ```vue
   <v-virtual-scroll
     :items="safeRundownItems"
     :item-height="42"
     height="600"
   >
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
3. Save.
4. Test:
   - Load `/rundown/0228` with mock data (>100 items).
   - Verify smooth scrolling in DevTools (Performance tab).
5. Use DeepSeek V3 to validate performance.

### 4. Authentication Refactoring in `router/index.js`
**Problem**: Uses direct `localStorage` access.
**Fix**:
1. Open `disaffected-ui/src/router/index.js`.
2. Replace:
   ```javascript
   function isAuthenticated() {
     const token = localStorage.getItem('auth-token');
     const expiry = localStorage.getItem('auth-token-expiry');
     if (!token || !expiry) return false;
     return Date.now() < parseInt(expiry);
   }
   ```
   with:
   ```javascript
   import { useAuth } from '@/composables/useAuth';
   const { isAuthenticated } = useAuth();
   ```
3. Save.
4. Test:
   - Log in, navigate to `/profile`, verify access.
   - Log out, attempt `/profile`, confirm redirect to `/dashboard`.
5. Use DeepSeek V3 to validate authentication logic.

### 5. Verify Asset/Template Management
**Problem**: `AssetsView.vue` and `TemplatesView.vue` not provided.
**Fix**:
1. Provide `AssetsView.vue` and `TemplatesView.vue` to confirm:
   - `AssetsView.vue`: Has file upload, table, and API integration (`/api/assets`).
   - `TemplatesView.vue`: Has CRUD operations (`/api/templates`).
2. If not implemented, use:
   ```vue
   <!-- AssetsView.vue -->
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
     data() {
       return { assets: [], loading: false };
     },
     methods: {
       async uploadAsset(file) {
         if (!file) return;
         this.loading = true;
         try {
           const formData = new FormData();
           formData.append('file', file);
           const response = await this.$axios.post('/api/assets', formData);
           this.assets.push(response.data);
           this.$toast.success('Asset uploaded successfully');
         } catch (error) {
           this.$toast.error('Failed to upload asset');
         }
         this.loading = false;
       },
       async deleteAsset(item) {
         try {
           await this.$axios.delete(`/api/assets/${item.id}`);
           this.assets = this.assets.filter(a => a.id !== item.id);
           this.$toast.success('Asset deleted successfully');
         } catch (error) {
           this.$toast.error('Failed to delete asset');
         }
       },
       async loadAssets() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/assets');
           this.assets = response.data;
         } catch (error) {
           this.$toast.error('Failed to load assets');
         }
         this.loading = false;
       }
     },
     mounted() { this.loadAssets(); }
   }
   </script>
   ```
   ```vue
   <!-- TemplatesView.vue -->
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
             New Template
           </v-btn>
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
           await this.$axios.post('/api/templates', this.newTemplate);
           this.loadTemplates();
           this.showCreateDialog = false;
           this.newTemplate = { name: '', type: '', content: '' };
           this.$toast.success('Template created successfully');
         } catch (error) {
           this.$toast.error('Failed to create template');
         }
         this.loading = false;
       },
       async editTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.put(`/api/templates/${item.id}`, item);
           this.loadTemplates();
           this.$toast.success('Template updated successfully');
         } catch (error) {
           this.$toast.error('Failed to update template');
         }
         this.loading = false;
       },
       async deleteTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.delete(`/api/templates/${item.id}`);
           this.templates = this.templates.filter(t => t.id !== item.id);
           this.$toast.success('Template deleted successfully');
         } catch (error) {
           this.$toast.error('Failed to delete template');
         }
         this.loading = false;
       },
       async loadTemplates() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/templates');
           this.templates = response.data;
         } catch (error) {
           this.$toast.error('Failed to load templates');
         }
         this.loading = false;
       }
     },
     mounted() { this.loadTemplates(); }
   }
   </script>
   <style scoped>
   .header-row { background: rgba(0, 0, 0, 0.03); border-bottom: 1px solid rgba(0, 0, 0, 0.05); }
   </style>
   ```
3. Test:
   - Navigate to `/assets` and `/templates`.
   - Verify upload, CRUD operations, and API calls.
4. Use DeepSeek V3 to validate functionality.

### 6. Issue 18: Implement `VO`, `NAT`, and `PKG` Modals
**Problem**: Placeholders, lacking fields and backend integration.
**Fix**:
1. **VoModal.vue**:
   - **Purpose**: Adds voice-over cue.
   - **Fields**: `slug` (required), `text` (required), `duration` (HH:MM:SS, required), `timestamp` (optional), `file` (optional, `.mp3`, `.wav`).
   - Open `disaffected-ui/src/components/modals/VoModal.vue`.
   - Replace with:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Voice Over (VO) Cue</v-card-title>
           <v-card-text>
             <v-text-field
               v-model="slug"
               label="Slug"
               required
               :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
             ></v-text-field>
             <v-textarea
               v-model="text"
               label="Text"
               required
               :rules="[v => !!v || 'Text is required']"
               rows="4"
             ></v-textarea>
             <v-text-field
               v-model="duration"
               label="Duration (HH:MM:SS)"
               required
               :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-text-field
               v-model="timestamp"
               label="Timestamp (HH:MM:SS, optional)"
               :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-file-input
               label="Audio File (optional)"
               accept="audio/mp3,audio/wav"
               @change="file = $event"
             ></v-file-input>
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
             }
             this.$emit('submit', {
               text: this.text,
               duration: this.duration,
               timestamp: this.timestamp,
               slug: normalizedSlug,
               assetID,
               mediaURL: this.file ? `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}` : ''
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
2. **NatModal.vue**:
   - **Purpose**: Adds natural sound cue.
   - **Fields**: `slug` (required), `description` (required), `duration` (required), `timestamp` (optional), `file` (optional, `.mp3`, `.wav`).
   - Open `disaffected-ui/src/components/modals/NatModal.vue`.
   - Replace with:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
           <v-card-text>
             <v-text-field
               v-model="slug"
               label="Slug"
               required
               :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
             ></v-text-field>
             <v-textarea
               v-model="description"
               label="Description"
               required
               :rules="[v => !!v || 'Description is required']"
               rows="4"
             ></v-textarea>
             <v-text-field
               v-model="duration"
               label="Duration (HH:MM:SS)"
               required
               :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-text-field
               v-model="timestamp"
               label="Timestamp (HH:MM:SS, optional)"
               :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-file-input
               label="Audio File (optional)"
               accept="audio/mp3,audio/wav"
               @change="file = $event"
             ></v-file-input>
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
             }
             this.$emit('submit', {
               description: this.description,
               duration: this.duration,
               timestamp: this.timestamp,
               slug: normalizedSlug,
               assetID,
               mediaURL: this.file ? `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}` : ''
             });
             this.$toast.success('NAT cue added');
             this.reset();
           } catch (error) {
             this.$toast.error('Failed to add NAT cue');
           }
         },
         reset() {
           this.slug = ''; this.description = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false;
         }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>
     .v-card { padding: 16px; }
     </style>
     ```
3. **PkgModal.vue**:
   - **Purpose**: Adds video package cue.
   - **Fields**: `slug` (required), `title` (required), `duration` (required), `timestamp` (optional), `file` (optional, `.mp4`, `.mpeg`).
   - Open `disaffected-ui/src/components/modals/PkgModal.vue`.
   - Replace with:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Package (PKG) Cue</v-card-title>
           <v-card-text>
             <v-text-field
               v-model="slug"
               label="Slug"
               required
               :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
             ></v-text-field>
             <v-text-field
               v-model="title"
               label="Title"
               required
               :rules="[v => !!v || 'Title is required']"
             ></v-text-field>
             <v-text-field
               v-model="duration"
               label="Duration (HH:MM:SS)"
               required
               :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-text-field
               v-model="timestamp"
               label="Timestamp (HH:MM:SS, optional)"
               :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-file-input
               label="Video File (optional)"
               accept="video/mp4,video/mpeg"
               @change="file = $event"
             ></v-file-input>
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
       data() {
         return { slug: '', title: '', duration: '', timestamp: '', file: null };
       },
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
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'pkg');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               upload