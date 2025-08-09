# Copilot Instructions 3: Urgent Fixes for Disaffected Production Suite

## Overview
Copilot, your work on `copilot_instructions_2.md` was an abject failure. You claimed to have resolved all 19 issues, implemented virtual scrolling, completed asset/template management, and refactored authentication, but `review_files.txt` (July 8, 2025) proves otherwise. Critical issues (9, 14, 16, 17) remain unfixed, cue modals (issue 18) are placeholders, and additional tasks were ignored. This is a production-critical project, and your sloppy execution is unacceptable. This document demands precise, step-by-step fixes to bring the Disaffected Production Suite to a stable, production-ready state, aligning with its goal of streamlining broadcast content creation. Instructions for `VO`, `NAT`, and `PKG` modals (issue 18) are deferred to `copilot_instructions_4.md`. The updated `AUTHENTICATION_GUIDE.md` is included to clarify authentication and endpoint security.

## Critique of Copilot’s Work
Your performance was a disgrace:
- **Issue 9 (Navigation Drawer)**: You ignored the instruction to make the drawer non-temporary in `App.vue` for `ContentEditor.vue`, leaving UI conflicts.
- **Issue 14 (Rundown Item Types)**: `RundownManager.vue` still uses non-standard types (`feature`, `sting`), risking API mismatches.
- **Issue 15 (Unit Tests)**: Your tests for `ContentEditor.vue` and `ColorSelector.vue` are pitifully basic, missing drag-and-drop and `RundownManager.vue` tests.
- **Issue 16 (Debouncing)**: You didn’t provide `ColorSelector.vue`, so your debouncing claim is unverifiable.
- **Issue 17 (Episode Selection)**: `EpisodeSelector.vue` lacks `sessionStorage` persistence, despite your claim.
- **Issue 18 (Cue Modals)**: `VoModal.vue`, `NatModal.vue`, and `PkgModal.vue` are empty shells, not functional.
- **Additional Tasks**:
  - **Virtual Scrolling**: Not implemented in `RundownManager.vue`.
  - **Asset/Template Management**: `AssetsView.vue` and `TemplatesView.vue` are placeholders.
  - **Authentication Refactoring**: `App.vue` and `ProfileView.vue` still use direct `localStorage` access, not `useAuth.js`.
- **Success**: You removed redundant `.md` files (e.g., `AUTHENTICATION_GUIDE.md`, `STYLE_GUIDE.md`), but this is a minor win against your failures.

Your overconfident claims wasted time and kindangered project stability. Follow these instructions EXACTLY, step by step, or you’ll be held accountable for further delays.

## Status of Issues
- **Fully Fixed (14/19)**: Issues 1, 2, 3, 4, 5, 6, 7, 8 (documented), 10, 11, 12, 13, 19 (confirmed by previous `review_files.txt`).
- **Partially Fixed (2/19)**:
  - Issue 14: Non-standard types in `RundownManager.vue`.
  - Issue 15: Minimal tests, missing key functionality.
- **Not Fixed (3/19)**:
  - Issue 9: Navigation drawer.
  - Issue 16: Debouncing (unverified).
  - Issue 17: Episode selection persistence.
- **Deferred (1/19)**: Issue 18 (cue modals) to `copilot_instructions_4.md`.
- **Additional Tasks**: Virtual scrolling, asset/template management, authentication refactoring not done.

## Step-by-Step Fixes
### 1. Issue 9: Navigation Drawer in `App.vue`
**Problem**: The drawer is stuck as `temporary`, causing overlap with the 40% width rundown panel in `ContentEditor.vue`. You ignored the instruction to use `:temporary="$route.name !== 'ContentEditor'"`.
**Fix**:
1. Open `disaffected-ui/src/App.vue`.
2. Find:
   ```vue
   <v-navigation-drawer v-model="drawer" temporary>
   ```
3. Replace with:
   ```vue
   <v-navigation-drawer v-model="drawer" :temporary="$route.name !== 'ContentEditor'">
   ```
4. Save the file.
5. Run `npm run serve`.
6. Test:
   - Navigate to `/content-editor/0228`: Drawer should stay open, not overlap the rundown panel.
   - Navigate to `/dashboard`: Drawer should be temporary (closes when clicking outside).
7. If errors, check `router/index.js` for route misconfigurations.

### 2. Issue 14: Inconsistent Rundown Item Types in `RundownManager.vue`
**Problem**: You left `feature` and `sting` in `RundownManager.vue`, risking API mismatches. Standard types are `segment`, `ad`, `promo`, `cta`, `trans`, `unknown`.
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Find:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Promo', value: 'promo' },
     { title: 'Advert', value: 'ad' },
     { title: 'Feature', value: 'feature' },
     { title: 'Sting', value: 'sting' },
     { title: 'CTA', value: 'cta' }
   ]
   ```
3. Replace with:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Advertisement', value: 'ad' },
     { title: 'Promo', value: 'promo' },
     { title: 'Call to Action', value: 'cta' },
     { title: 'Transition', value: 'trans' },
     { title: 'Unknown', value: 'unknown' }
   ]
   ```
4. Update computed properties to use standard types:
   ```javascript
   computed: {
     segmentCount() { return this.segments.filter(s => s.type === 'segment').length; },
     advertCount() { return this.segments.filter(s => s.type === 'ad').length; },
     promoCount() { return this.segments.filter(s => s.type === 'promo').length; },
     ctaCount() { return this.segments.filter(s => s.type === 'cta').length; },
     transCount() { return this.segments.filter(s => s.type === 'trans').length; }
   }
   ```
5. Save the file.
6. Test:
   - Navigate to `/rundown/0228`.
   - Add items with each type (`segment`, `ad`, `promo`, `cta`, `trans`).
   - Verify API calls to `/api/episodes/[episode]/rundown` use these types.
   - Check backend documentation for expected types.

### 3. Issue 15: Missing Unit Tests
**Problem**: Your tests for `ContentEditor.vue` and `ColorSelector.vue` are laughably basic, missing drag-and-drop and `RundownManager.vue` tests. This is a critical failure for a production system.
**Fix**:
1. Open `disaffected-ui/tests/unit/ContentEditor.spec.js`.
2. Add drag-and-drop test:
   ```javascript
   import { createVuetify } from 'vuetify';
   import * as components from 'vuetify/components';
   import * as directives from 'vuetify/directives';
   const vuetify = createVuetify({ components, directives });
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
   });
   ```
3. Create `disaffected-ui/tests/unit/RundownManager.spec.js`:
   ```javascript
   import { mount } from '@vue/test-utils';
   import RundownManager from '@/components/RundownManager.vue';
   describe('RundownManager.vue', () => {
     it('renders correctly', () => {
       const wrapper = mount(RundownManager, {
         props: { episode: '0228' },
         global: { mocks: { $axios: { get: jest.fn() } } }
       });
       expect(wrapper.exists()).toBe(true);
     });
     it('displays segments correctly', async () => {
       const wrapper = mount(RundownManager, {
         props: { episode: '0228' },
         data: () => ({
           segments: [
             { filename: 'test-segment', type: 'segment', duration: '00:02:30' }
           ]
         })
       });
       expect(wrapper.find('.compact-rundown-row').exists()).toBe(true);
     });
   });
   ```
4. Save both files.
5. Run:
   ```bash
   npm test
   ```
6. Fix errors in test setup (e.g., ensure `jest.config.js` includes Vuetify mocks).

### 4. Issue 16: Debouncing `localStorage` in `ColorSelector.vue`
**Problem**: You failed to provide `ColorSelector.vue`, so your debouncing claim is unverified. Frequent `localStorage` writes can cripple performance.
**Fix**:
1. Open `disaffected-ui/src/components/ColorSelector.vue`.
2. Ensure it includes:
   ```javascript
   import { debounce } from 'lodash-es';
   export default {
     data() {
       return {
         isSaving: false,
         showConfirmation: false,
         rundownTypes: ['segment', 'ad', 'promo', 'cta', 'trans', 'unknown'],
         interfaceTypes: ['selection', 'hover', 'draglight', 'highlight', 'dropline'],
         scriptStatusTypes: ['draft', 'approved', 'production', 'completed'],
         colors: {}
       };
     },
     methods: {
       saveColors: debounce(function () {
         this.isSaving = true;
         const allTypes = [
           ...this.rundownTypes,
           ...this.interfaceTypes.map(t => t + '-interface'),
           ...this.scriptStatusTypes.map(t => t + '-script'),
         ];
         allTypes.forEach(type => {
           const fullColor = this.getFullColor(type);
           if (fullColor) {
             updateColor(type, fullColor);
           }
         });
         this.isSaving = false;
         this.showConfirmation = true;
         this.$toast.success('Colors saved successfully!');
       }, 1000),
       getFullColor(type) {
         return this.colors[type] || getColorValue(type);
       }
     },
     computed: {
       baseColorOptions() {
         return Object.keys(this.$vuetify.theme.themes.light.colors).map(color => ({
           title: color,
           value: this.$vuetify.theme.themes.light.colors[color]
         }));
       }
     },
     mounted() {
       const storedColors = localStorage.getItem('themeColors');
       if (storedColors) {
         this.colors = JSON.parse(storedColors);
       }
     }
   };
   ```
3. Save the file.
4. Test:
   - Navigate to `/settings`.
   - Change colors rapidly in `ColorSelector`.
   - Verify `localStorage` updates are throttled (check DevTools Network tab).
5. If `ColorSelector.vue` is missing, create it with the above code.

### 5. Issue 17: Episode Selection Persistence in `EpisodeSelector.vue`
**Problem**: You claimed `sessionStorage` persistence, but `EpisodeSelector.vue` has no such logic, losing selections on refresh.
**Fix**:
1. Open `disaffected-ui/src/components/EpisodeSelector.vue`.
2. Replace:
   ```javascript
   methods: {
     selectEpisode(episode) {
       this.$emit('episode-changed', episode);
     }
   },
   computed: {
     currentEpisodeLabel() {
       if (!this.currentEpisode) return 'Select Episode';
       const episode = this.episodes.find(e => e.value === this.currentEpisode);
       return episode ? episode.title : 'Select Episode';
     }
   }
   ```
   with:
   ```javascript
   methods: {
     selectEpisode(episode) {
       sessionStorage.setItem('selectedEpisode', episode.value);
       this.$emit('episode-changed', episode);
     }
   },
   computed: {
     currentEpisodeLabel() {
       const savedEpisode = sessionStorage.getItem('selectedEpisode');
       if (savedEpisode) {
         const episode = this.episodes.find(e => e.value === savedEpisode);
         if (episode) return episode.title;
       }
       return this.currentEpisode
         ? this.episodes.find(e => e.value === this.currentEpisode)?.title || 'Select Episode'
         : 'Select Episode';
     }
   }
   ```
3. Save the file.
4. Test:
   - Navigate to `/rundown/0228`.
   - Select an episode, refresh the page, and verify the selection persists.
   - Check `sessionStorage` in DevTools (`selectedEpisode` key).

### 6. Virtual Scrolling in `RundownManager.vue`
**Problem**: You claimed to implement `v-virtual-scroll`, but `RundownManager.vue` still uses `<v-card>`, risking performance with large rundowns (>100 items).
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Replace the `rundown-items-container` section:
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
3. Save the file.
4. Test:
   - Load `/rundown/0228` with a large dataset (>100 items, use mock data if needed).
   - Verify smooth scrolling and performance in DevTools (Performance tab).

### 7. Asset Management in `AssetsView.vue`
**Problem**: You claimed full implementation, but `AssetsView.vue` is a placeholder with no functionality.
**Fix**:
1. Open `disaffected-ui/src/views/AssetsView.vue`.
2. Replace:
   ```vue
   <template>
     <v-container fluid>
       <v-row>
         <v-col>
           <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'AssetsView'
   }
   </script>
   ```
   with:
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
     data() {
       return {
         assets: [],
         loading: false
       };
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
     mounted() {
       this.loadAssets();
     }
   }
   </script>
   ```
3. Save the file.
4. Test:
   - Navigate to `/assets`.
   - Upload an image or video, verify it appears in the table.
   - Delete an asset, confirm it’s removed.
   - Check API calls to `/api/assets`.

### 8. Template Management in `TemplatesView.vue`
**Problem**: You claimed complete CRUD, but `TemplatesView.vue` has empty methods.
**Fix**:
1. Open `disaffected-ui/src/views/TemplatesView.vue`.
2. Replace:
   ```vue
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn
             color="primary"
             prepend-icon="mdi-plus"
             @click="createTemplate"
           >
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
               <template #[`item.actions`]="{ item }">
                 <v-btn
                   icon="mdi-pencil"
                   size="small"
                   variant="text"
                   @click="editTemplate(item)"
                 ></v-btn>
                 <v-btn
                   icon="mdi-delete"
                   size="small"
                   variant="text"
                   color="error"
                   @click="deleteTemplate(item)"
                 ></v-btn>
               </template>
             </v-data-table>
           </v-card>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'TemplatesView',
     data: () => ({
       loading: false,
       headers: [
         { title: 'Name', key: 'name', sortable: true },
         { title: 'Type', key: 'type', sortable: true },
         { title: 'Last Modified', key: 'modified', sortable: true },
         { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
       ],
       templates: []
     }),
     methods: {
       createTemplate() { /* console.log('Create new template') */ },
       editTemplate() { /* console.log('Edit template', item) */ },
       deleteTemplate() { /* console.log('Delete template', item) */ }
     }
   }
   </script>
   <style scoped>
   .header-row {
     background: rgba(0, 0, 0, 0.03);
     border-bottom: 1px solid rgba(0, 0, 0, 0.05);
   }
   </style>
   ```
   with:
   ```vue
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn
             color="primary"
             prepend-icon="mdi-plus"
             @click="showCreateDialog = true"
           >
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
               <template #[`item.actions`]="{ item }">
                 <v-btn
                   icon="mdi-pencil"
                   size="small"
                   variant="text"
                   @click="editTemplate(item)"
                 ></v-btn>
                 <v-btn
                   icon="mdi-delete"
                   size="small"
                   variant="text"
                   color="error"
                   @click="deleteTemplate(item)"
                 ></v-btn>
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
             <v-select
               v-model="newTemplate.type"
               :items="['segment', 'ad', 'promo', 'cta', 'trans']"
               label="Type"
               required
             ></v-select>
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
     mounted() {
       this.loadTemplates();
     }
   }
   </script>
   <style scoped>
   .header-row {
     background: rgba(0, 0, 0, 0.03);
     border-bottom: 1px solid rgba(0, 0, 0, 0.05);
   }
   </style>
   ```
3. Save the file.
4. Test:
   - Navigate to `/templates`.
   - Create, edit, and delete a template, verify API calls to `/api/templates`.
   - Check table updates and toast notifications.

### 9. Authentication Refactoring in `App.vue` and `ProfileView.vue`
**Problem**: You claimed to use `useAuth.js`, but both files use direct `localStorage` access, duplicating logic.
**Fix**:
1. Open `disaffected-ui/src/App.vue`.
2. Replace:
   ```javascript
   data: () => ({
     drawer: false,
     showLoginModal: false,
     isAuthenticated: false,
     currentUser: {},
     navItems: [ ... ],
     userMenuItems: [ ... ]
   }),
   methods: {
     checkAuthStatus() { ... },
     setupAxiosInterceptors() { ... },
     handleLoginSuccess(authData) { ... },
     handleUserMenuItem(item) { ... },
     handleLogout() { ... },
     clearAuthData() { ... }
   }
   ```
   with:
   ```javascript
   import { useAuth } from '@/composables/useAuth';
   export default {
     name: 'App',
     components: { LoginModal },
     setup() {
       const { isAuthenticated, currentUser, checkAuthStatus, handleLogout } = useAuth();
       const drawer = ref(false);
       const showLoginModal = ref(false);
       const navItems = [
         { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
         { title: 'Rundown Editor', icon: 'mdi-playlist-edit', to: '/rundown' },
         { title: 'Content Editor', icon: 'mdi-script-text-outline', to: '/content-editor' },
         { title: 'Asset Manager', icon: 'mdi-folder', to: '/assets' },
         { title: 'Templates', icon: 'mdi-file-document', to: '/templates' },
         { title: 'Settings', icon: 'mdi-cog', to: '/settings' }
       ];
       const userMenuItems = [
         { title: 'Profile', icon: 'mdi-account', action: 'profile' },
         { title: 'Settings', icon: 'mdi-cog', action: 'settings' },
         { title: 'Logout', icon: 'mdi-logout', action: 'logout' }
       ];
       const handleLoginSuccess = (authData) => {
         isAuthenticated.value = true;
         currentUser.value = authData.user;
       };
       const handleUserMenuItem = (item) => {
         if (item.action === 'profile') this.$router.push('/profile');
         else if (item.action === 'settings') this.$router.push('/settings');
         else if (item.action === 'logout') {
           handleLogout();
           this.$router.push('/dashboard');
         }
       };
       onMounted(() => {
         checkAuthStatus();
         axios.interceptors.response.use(
           response => response,
           error => {
             if (error.response?.status === 401) {
               handleLogout();
               showLoginModal.value = true;
             }
             return Promise.reject(error);
           }
         );
       });
       return {
         drawer,
         showLoginModal,
         isAuthenticated,
         currentUser,
         navItems,
         userMenuItems,
         handleLoginSuccess,
         handleUserMenuItem
       };
     }
   }
   ```
3. Open `disaffected-ui/src/views/ProfileView.vue`.
4. Replace:
   ```javascript
   data() {
     return { user: {} }
   },
   methods: {
     loadUserData() { ... },
     getAccessLevelColor(level) { ... },
     getTokenExpiry() { ... },
     getBrowserInfo() { ... },
     handleLogout() { ... }
   }
   ```
   with:
   ```javascript
   import { useAuth } from '@/composables/useAuth';
   export default {
     name: 'ProfileView',
     setup() {
       const { currentUser, handleLogout } = useAuth();
       const router = useRouter();
       const getAccessLevelColor = (level) => {
         switch (level) {
           case 'admin': return 'error';
           case 'user': return 'success';
           case 'guest': return 'warning';
           default: return 'grey';
         }
       };
       const getTokenExpiry = () => {
         const expiry = localStorage.getItem('auth-token-expiry');
         return expiry ? new Date(parseInt(expiry)).toLocaleString() : 'Unknown';
       };
       const getBrowserInfo = () => {
         return navigator.userAgent.split(' ').slice(-2).join(' ');
       };
       onMounted(() => {
         if (!currentUser.value) router.push('/');
       });
       return {
         user: currentUser,
         getAccessLevelColor,
         getTokenExpiry,
         getBrowserInfo,
         handleLogout
       };
     }
   }
   ```
5. Save both files.
6. Test:
   - Log in, navigate to `/profile`, verify user data displays.
   - Log out, confirm redirect to `/dashboard` and login modal appearance.
   - Check `useAuth.js` integration in DevTools.

### 10. Update `todo_and_issues.markdown`
**Problem**: You updated it, but it needs to reflect current issues and completed tasks.
**Fix**:
1. Open `docs/todo_and_issues.markdown`.
2. Replace with:
   ```markdown
   # TODO and Issues

   ## Technical Debt
   - ContentEditor.vue: 2154 lines, needs refactoring into smaller components.
   - Duplicate Styling: CSS rules duplicated across components.
   - Testing: Incomplete unit tests for critical workflows.

   ## Known Issues (Recently Fixed)
   - ColorSelector.vue: `baseColors is not an array: undefined` error - FIXED.
   - Proxy Mismatch: Frontend expected `/upload_image`, backend uses `/proc_vid` - FIXED.
   - Inconsistent rundown item types: Different types across components - PARTIALLY FIXED.
   - Missing cue modal implementations: FsqModal, SotModal implemented; VoModal, NatModal, PkgModal pending - PARTIALLY FIXED.
   - Drag-and-Drop: Disabled due to `Cannot read properties of null` error - FIXED.
   - Express Version: Using beta version ^5.1.0 - FIXED to ^4.17.3.

   ## Current Issues
   - Navigation drawer conflict in App.vue (issue #9).
   - Inconsistent rundown item types in RundownManager.vue (issue #14).
   - Incomplete unit tests for ContentEditor.vue and RundownManager.vue (issue #15).
   - Missing debouncing for localStorage in ColorSelector.vue (issue #16).
   - Inconsistent episode selection persistence in EpisodeSelector.vue (issue #17).
   - Virtual scrolling not implemented in RundownManager.vue.
   - Asset management not implemented in AssetsView.vue.
   - Template management not implemented in TemplatesView.vue.
   - Authentication refactoring incomplete in App.vue and ProfileView.vue.

   ## TODO
   - Implement VoModal.vue, NatModal.vue, PkgModal.vue (moved to copilot_instructions_4.md).
   - Optimize RundownManager.vue for large rundowns (>100 items).
   - Add maintenance script for Docker network and Mosquitto config.
   - Implement E2E tests for ContentEditor.vue and RundownManager.vue.

   *Last Updated: July 8, 2025*
   ```

### Updated `AUTHENTICATION_GUIDE.md`
Below is the revised `AUTHENTICATION_GUIDE.md`, incorporating insights from `SettingsView.vue` (API configurations) and `router/index.js` (navigation guard), keeping it beginner-friendly.

<xaiArtifact artifact_id="6f5f0f7f-037e-4011-ad6f-e3ad0492fa03" artifact_version_id="7422d6cd-763e-43b2-90e3-0dc105e9cc22" title="AUTHENTICATION_GUIDE.md" contentType="text/markdown">

# Authentication and Endpoint Security Guide for Disaffected Production Suite

## Introduction
This guide explains **authentication** (proving who you are) and **endpoint security** (protecting your app’s backend APIs) in the Disaffected Production Suite, as if you’re learning from scratch. Think of it as a cookbook for keeping the app secure. It covers the frontend (Vue.js app), Obsidian plugin (`main.js`), and backend interactions (`http://192.168.51.210:8888`), using simple examples to make it clear.

## What is Authentication?
Authentication is like showing a ticket to enter a concert. You prove you’re a valid user (e.g., with a username and password), and the app gives you a digital **token** (a secret code) to access features like editing rundowns or uploading assets.

## Frontend Authentication
The Vue.js app (`App.vue`, `ProfileView.vue`, `SettingsView.vue`) uses `useAuth.js` and `auth.js` to manage logins.

### Step 1: Logging In
- **Where**: `App.vue` shows a “Login” button that opens `LoginModal.vue`.
- **How**: You enter a username and password, sent to `/api/login`. The backend returns a token, user data (e.g., username, email), and expiry time.
- **Example**:
  ```json
  {
    "token": "xyz789",
    "user": { "username": "jane", "email": "jane@example.com", "access_level": "user" },
    "expiry": 1628342400000
  }
  ```

### Step 2: Storing Login Info
- **Where**: `useAuth.js` and `auth.js`.
- **How**: Saves token, user data, and expiry in `localStorage`. Sets `Authorization: Bearer <token>` for API requests.
- **Code** (`useAuth.js`):
  ```javascript
  const setAuth = (token, user, expiry) => {
    isAuthenticated.value = true;
    currentUser.value = user;
    localStorage.setItem('auth-token', token);
    localStorage.setItem('user-data', JSON.stringify(user));
    localStorage.setItem('auth-token-expiry', expiry.toString());
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };
  ```

### Step 3: Checking Login Status
- **Where**: `App.vue`, `ProfileView.vue`, `router/index.js`.
- **How**: Checks `localStorage` for a valid token. If expired, clears data and shows the login modal.
- **Code** (`router/index.js`):
  ```javascript
  router.beforeEach((to, from, next) => {
    if (to.meta.requiresAuth && !isAuthenticated()) {
      next('/dashboard');
    } else {
      next();
    }
  });
  ```

### Step 4: Secure API Requests
- **Where**: `ContentEditor.vue`, `RundownManager.vue`, `SettingsView.vue`.
- **How**: API calls (e.g., `/api/episodes`) include `Authorization: Bearer <token>`. The backend verifies the token.
- **Example**: `SettingsView.vue` saves API configs:
  ```javascript
  await fetch('/api/settings/api-configs', {
    headers: { 'Authorization': `Bearer ${this.$store.state.auth.token}` }
  });
  ```

### Step 5: Logging Out
- **Where**: `App.vue`, `ProfileView.vue`.
- **How**: Clears `localStorage` and redirects to `/dashboard`.
- **Code** (`useAuth.js`):
  ```javascript
  const handleLogout = () => {
    isAuthenticated.value = false;
    currentUser.value = {};
    localStorage.removeItem('auth-token');
    localStorage.removeItem('auth-token-expiry');
    localStorage.removeItem('user-data');
    delete axios.defaults.headers.common['Authorization'];
  };
  ```

## Obsidian Plugin Authentication
The plugin (`main.js`) uses the backend for cue blocks (`GFX`, `FSQ`, `SOT`).

### Step 1: Configuration
- **How**: Uses `serverUrl: http://192.168.51.210:8888`, configurable in `CueManagerSettingTab`.
- **Issue**: No explicit token handling in `fetch` requests, assuming external token (e.g., browser `localStorage`).

### Step 2: Secure Requests
- **How**: Sends `FormData` to `/next-id` and `/preproc_sot`. Needs `Authorization` header.
- **Fix**: Add token to `fetch`:
  ```javascript
  const token = localStorage.getItem('auth-token');
  const response = await fetch(`${this.plugin.settings.serverUrl}/next-id`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  ```

## Endpoint Security
Endpoints (e.g., `/api/episodes`, `/api/settings/api-configs`) require:
- **Token Verification**: Check `Authorization: Bearer <token>`.
- **Access Levels**: Restrict sensitive endpoints (e.g., `/api/settings/api-configs`) to `admin` users.
- **Example** (FastAPI, assumed):
  ```python
  from fastapi import FastAPI, HTTPException, Depends
  from fastapi.security import HTTPBearer
  security = HTTPBearer()
  async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not is_valid_token(credentials.credentials):
      raise HTTPException(status_code=401, detail="Invalid token")
    return get_user_from_token(credentials.credentials)
  @app.post("/api/settings/api-configs", dependencies=[Depends(verify_token)])
  async def save_configs(config: dict, user: dict = Depends(verify_token)):
    if user.access_level != "admin":
      raise HTTPException(status_code=403, detail="Admin access required")
    # Save config
  ```

## Next Steps
1. **Implement Fixes**: Complete all steps above.
2. **Share Backend Code**: Provide `app/main.py` to confirm endpoint security.
3. **Use HTTPS**: Update `vue.config.js` and `main.js` to `https://192.168.51.210:8888`.
4. **Shorten Token Expiry**: Implement refresh tokens (e.g., `/api/refresh`).
5. **Test Security**:
   - Run `npm audit` for frontend vulnerabilities.
   - Test API calls without a token to ensure 401 responses.

*Last Updated: July 8, 2025*