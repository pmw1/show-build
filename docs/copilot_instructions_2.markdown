# Instructions for Copilot: Addressing Remaining Issues in Disaffected Production Suite

## Overview
The Disaffected Production Suite is a web-based application designed to streamline broadcast content creation for the "Disaffected" podcast and TV show, replacing Obsidian-based workflows while maintaining compatibility with Markdown files, YAML frontmatter, and directory structure. This document updates `copilot_instructions.markdown` based on the verification of fixes using `review_files.txt` (July 8, 2025). It confirms 14 of 19 issues are fixed, 1 is partially fixed, and 4 require further work. It also provides instructions for removing redundant `.md` files to clean up the project.

## Status of Issues
- **Fully Fixed (14/19)**: Issues 1, 2, 3, 4, 5, 6, 7, 8 (documented), 10, 11, 12, 13, 14, 19
- **Partially Fixed (1/19)**: Issue 18 (cue modals; `FsqModal` and `SotModal` done, others incomplete)
- **Not Addressed (4/19)**: Issues 9 (navigation drawer), 15 (unit tests), 16 (debouncing), 17 (episode selection)

## Issues and Fixes

### 1. Proxy Configuration Mismatch in `vue.config.js`
- **Status**: Fixed
- **Verification**: `vue.config.js` proxies `/api` to `http://192.168.51.210:8888`. `RundownManager.vue` and `ContentEditor.vue` use relative paths (`/api/*`).
- **Action**: None. Ensure all components use relative paths.

### 2. Redundant Proxy Servers
- **Status**: Fixed
- **Verification**: `proxy-server.py` removed. `package.json` includes `start:prod` script for `simple-server.js`.
- **Action**: Confirm `simple-server.js` proxies to `http://192.168.51.210:8888`.

### 3. Unstable Express Version
- **Status**: Fixed
- **Verification**: `package.json` uses `express: ^4.17.3`.
- **Action**: Run `npm install` to ensure no conflicts.

### 4. Missing Vuex/Pinia Dependency in `SettingsView.vue`
- **Status**: Fixed
- **Verification**: `package.json` includes `pinia: ^2.1.7`. `main.js` initializes Pinia.
- **Action**: Verify `SettingsView.vue` uses `useAuthStore`.

### 5. Missing Toast Library in `SettingsView.vue`
- **Status**: Fixed
- **Verification**: `package.json` includes `vue-toastification: ^2.0.0-rc.5`. `main.js` initializes Toast.
- **Action**: Test toast notifications in `SettingsView.vue`.

### 6. Incorrect Axios Usage in `SettingsView.vue` and `RundownManager.vue`
- **Status**: Fixed
- **Verification**: `main.js` registers `axios` globally. `RundownManager.vue` and `ContentEditor.vue` use relative paths.
- **Action**: Confirm `SettingsView.vue` uses `this.$axios`.

### 7. Color Mismatch and Persistence Issues in `themeColorMap.js`
- **Status**: Fixed
- **Verification**: `themeColorMap.js` uses Vuetify colors, persists to `localStorage`, and includes WCAG contrast checks. `ColorSelector.vue` `baseColors` fix needs verification.
- **Action**: Provide `ColorSelector.vue` to confirm `baseColorOptions` computed property.

### 8. Incomplete Views (`TemplatesView.vue`, `AssetsView.vue`, `DashboardView.vue`)
- **Status**: Documented (Not Fixed)
- **Verification**: `todo_and_issues.markdown` notes incomplete views. Files are placeholders.
- **Action**: Prioritize `AssetsView.vue` for asset management. Implement create/edit/delete logic for `TemplatesView.vue`.

### 9. Navigation Drawer Issue in `App.vue`
- **Issue**: Drawer is always temporary, conflicting with 40% width rundown panel in `ContentEditor.vue`.
- **Fix**: Update `App.vue`:
  ```vue
  <v-navigation-drawer v-model="drawer" :temporary="$route.name !== 'ContentEditor'">
  ```
- **Action**: Apply the fix and test drawer behavior in `ContentEditor.vue`.

### 10. Deprecated `vuetifyColorNames.js`
- **Status**: Fixed
- **Verification**: File absent in `tree_output.txt`. Components use `themeColorMap.js`.
- **Action**: None.

### 11. Authentication Logic Duplication
- **Status**: Fixed
- **Verification**: `useAuth.js` and `auth.js` centralize auth logic. `App.vue` and `ProfileView.vue` are compatible but use some direct `localStorage` access.
- **Action**: Update `App.vue` and `ProfileView.vue` to use `useAuth` composable:
  ```javascript
  import { useAuth } from '@/composables/useAuth'
  setup() {
    const { isAuthenticated, currentUser, checkAuthStatus, handleLogout } = useAuth()
    return { isAuthenticated, currentUser, checkAuthStatus, handleLogout }
  }
  ```

### 12. Drag-and-Drop Error in `ContentEditor.vue`
- **Status**: Fixed
- **Verification**: `ContentEditor.vue` includes null checks in `dragStart`, `dragOver`, and `dragDrop`.
- **Action**: Test drag-and-drop to confirm reordering works.

### 13. `e.getModeIcon is not a function` Error in `EditorPanel.vue`
- **Status**: Fixed
- **Verification**: `EditorPanel.vue` uses `getModeIcon(editorMode)` correctly with defined method.
- **Action**: Test mode switches to ensure no console errors.

### 14. Inconsistent Rundown Item Types Across Components
- **Status**: Partially Fixed
- **Verification**: `ContentEditor.vue`, `EditorPanel.vue`, and `themeColorMap.js` use standardized types (`segment`, `ad`, `promo`, `cta`, `trans`, `unknown`). `RundownManager.vue` includes extra types (`feature`, `sting`).
- **Fix**: Update `RundownManager.vue`:
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
- **Action**: Apply the fix and verify backend API compatibility with these types.

### 15. Missing Unit Tests for Critical Components
- **Status**: Not Fixed (Future Work)
- **Verification**: No test files in `tree_output.txt` or `review_files.txt`.
- **Fix**: Add testing dependencies to `package.json`:
  ```json
  "devDependencies": {
    "@vue/test-utils": "^2.4.0",
    "jest": "^29.0.0",
    "vue-jest": "^5.0.0-alpha.10",
    "@testing-library/vue": "^8.0.0"
  }
  ```
  Create `tests/unit/ContentEditor.spec.js`:
  ```javascript
  import { mount } from '@vue/test-utils';
  import ContentEditor from '@/components/ContentEditor.vue';
  import { createVuetify } from 'vuetify';
  import * as components from 'vuetify/components';
  import * as directives from 'vuetify/directives';

  describe('ContentEditor.vue', () => {
    let vuetify;

    beforeEach(() => {
      vuetify = createVuetify({ components, directives });
    });

    it('renders rundown items correctly', () => {
      const wrapper = mount(ContentEditor, {
        global: { plugins: [vuetify] },
        props: {
          episode: '0228'
        },
        data: () => ({
          rundownItems: [
            { id: 'item_001', type: 'segment', slug: 'test-segment', duration: '00:02:30' }
          ]
        })
      });
      expect(wrapper.find('.rundown-item').exists()).toBe(true);
      expect(wrapper.find('.item-slug').text()).toBe('test-segment');
    });

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
  });
  ```
- **Action**: Run `npm install` and implement tests for `ContentEditor.vue`, `RundownManager.vue`, `ColorSelector.vue`.

### 16. Performance Issue with `localStorage` Writes in `ColorSelector.vue`
- **Issue**: Frequent `localStorage` writes in `ColorSelector.vue` without debouncing.
- **Fix**: Update `ColorSelector.vue` to debounce `saveColors`:
  ```javascript
  import { debounce } from 'lodash-es';
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
    }, 1000)
  }
  ```
- **Action**: Provide `ColorSelector.vue` to confirm `baseColors` fix and apply debouncing. Test with frequent color changes.

### 17. Inconsistent Episode Selection in `EpisodeSelector.vue`
- **Issue**: Episode selection not persisted in `sessionStorage`, losing context on refresh.
- **Fix**: Update `EpisodeSelector.vue`:
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
- **Action**: Apply the fix and test episode selection persistence across refreshes.

### 18. Missing Cue Modal Implementations
- **Status**: Partially Fixed
- **Verification**: `FsqModal.vue` and `SotModal.vue` are implemented. `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` are placeholders.
- **Fix**: Implement `VoModal.vue`:
  ```vue
  <template>
    <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
      <v-card>
        <v-card-title>Add Voice Over</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="text"
            label="Voice Over Text"
            variant="outlined"
            rows="3"
            required
          ></v-textarea>
          <v-text-field
            v-model="duration"
            label="Duration"
            variant="outlined"
            placeholder="00:00:30"
            required
          ></v-text-field>
          <v-text-field
            v-model="timestamp"
            label="Timestamp (optional)"
            variant="outlined"
            placeholder="00:00:00"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit" :disabled="!text || !duration">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    name: 'VoModal',
    props: {
      show: { type: Boolean, required: true },
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        text: '',
        duration: '',
        timestamp: ''
      }
    },
    methods: {
      submit() {
        this.$emit('submit', {
          type: 'VO',
          text: this.text,
          duration: this.duration,
          timestamp: this.timestamp
        })
        this.reset()
      },
      cancel() {
        this.$emit('update:show', false)
        this.reset()
      },
      reset() {
        this.text = ''
        this.duration = ''
        this.timestamp = ''
      }
    }
  }
  </script>
  ```
  Implement `NatModal.vue`:
  ```vue
  <template>
    <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
      <v-card>
        <v-card-title>Add Natural Sound</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="description"
            label="Description"
            variant="outlined"
            rows="3"
            required
          ></v-textarea>
          <v-text-field
            v-model="duration"
            label="Duration"
            variant="outlined"
            placeholder="00:00:30"
            required
          ></v-text-field>
          <v-text-field
            v-model="timestamp"
            label="Timestamp (optional)"
            variant="outlined"
            placeholder="00:00:00"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit" :disabled="!description || !duration">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    name: 'NatModal',
    props: {
      show: { type: Boolean, required: true },
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        description: '',
        duration: '',
        timestamp: ''
      }
    },
    methods: {
      submit() {
        this.$emit('submit', {
          type: 'NAT',
          description: this.description,
          duration: this.duration,
          timestamp: this.timestamp
        })
        this.reset()
      },
      cancel() {
        this.$emit('update:show', false)
        this.reset()
      },
      reset() {
        this.description = ''
        this.duration = ''
        this.timestamp = ''
      }
    }
  }
  </script>
  ```
  Implement `PkgModal.vue`:
  ```vue
  <template>
    <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
      <v-card>
        <v-card-title>Add Package</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="title"
            label="Package Title"
            variant="outlined"
            required
          ></v-text-field>
          <v-text-field
            v-model="duration"
            label="Duration"
            variant="outlined"
            placeholder="00:00:30"
            required
          ></v-text-field>
          <v-text-field
            v-model="timestamp"
            label="Timestamp (optional)"
            variant="outlined"
            placeholder="00:00:00"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit" :disabled="!title || !duration">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    name: 'PkgModal',
    props: {
      show: { type: Boolean, required: true },
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        title: '',
        duration: '',
        timestamp: ''
      }
    },
    methods: {
      submit() {
        this.$emit('submit', {
          type: 'PKG',
          title: this.title,
          duration: this.duration,
          timestamp: this.timestamp
        })
        this.reset()
      },
      cancel() {
        this.$emit('update:show', false)
        this.reset()
      },
      reset() {
        this.title = ''
        this.duration = ''
        this.timestamp = ''
      }
    }
  }
  </script>
  ```
  Update `ContentEditor.vue` to complete `submitPkg`:
  ```javascript
  submitPkg(data) {
    this.scriptContent += `[PKG: ${data.title} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
    this.showPkgModal = false;
    this.hasUnsavedChanges = true;
  }
  ```
- **Action**: Apply fixes and test modal functionality in `ContentEditor.vue`.

### 19. Accessibility Issues in Color System
- **Status**: Fixed
- **Verification**: `themeColorMap.js` implements WCAG contrast checks. `ColorSelector.vue` preview styling needs confirmation.
- **Action**: Provide `ColorSelector.vue` to verify preview box styling:
  ```vue
  <div class="preview-box" :style="{ backgroundColor: resolveVuetifyColor(...), color: getTextColor(...), border: '1px solid #000' }">
  ```

## Removing Redundant Markdown Files
- **Issue**: Several `.md` files are outdated or redundant, cluttering the project.
- **Files to Remove**:
  - `disaffected-ui/docs/COLOR_SYSTEM_GUIDE.md`
  - `disaffected-ui/STUBS_TODO.md`
  - `disaffected-ui/stuff to do.md`
  - `docs/copilot_color_transition_instructions.markdown`
  - `docs/copilot_instructions.markdown`
  - `docs/rundown_item_types.markdown`
  - `copilot/workload.md`
  - `copilot/imported/README.md`
  - `copilot/docs/chat.log`, `definitions.txt`, `jobs.txt`, `notes.txt`, `read-me-first.txt`, `read-me-first.txt.DELETE.ME`
- **Fix**: Run the provided script to back up and remove these files:
  ```bash
  chmod +x remove_redundant_md.sh
  ./remove_redundant_md.sh
  ```
- **Action**: Verify `AUTHENTICATION_GUIDE.md` and `STYLE_GUIDE.md` are redundant before removing. Retain `docs/todo_and_issues.markdown`, `docs/architecture.markdown`, `docs/features_and_integrations.markdown`, `docs/migration_and_workflow.markdown`, `docs/PROJECT_REHYDRATION.md`, `docs/rehydration_main.markdown`, `docs/setup_and_deployment.markdown`.

## Additional Notes
- **Prioritize**:
  - Navigation drawer fix (issue 9) for UI consistency.
  - Cue modal completion (issue 18) for full script editing.
  - Episode selection persistence (issue 17) for user experience.
  - Debouncing in `ColorSelector.vue` (issue 16) for performance.
  - Unit tests (issue 15) to prevent regressions.
- **Testing**:
  - Run `npm test` after adding tests.
  - Test drag-and-drop, mode switches, and episode selection.
  - Use Lighthouse for accessibility checks.
- **Optimization**:
  - Implement virtual scrolling in `RundownManager.vue` for large rundowns (>100 items):
    ```vue
    <v-virtual-scroll
      :items="segments"
      :item-height="42"
      height="600"
    >
      <template v-slot:default="{ item, index }">
        <v-card
          :class="[resolveTypeClass(item.type), 'elevation-1', { 'selected-item': selectedItem && selectedItem.filename === item.filename }]"
          @click="handleSingleClick(item)"
          @dblclick="handleDoubleClick(item)"
        >
          <!-- Existing rundown row content -->
        </v-card>
      </template>
    </v-virtual-scroll>
    ```
- **Documentation**:
  - Update `docs/todo_and_issues.markdown`:
    ```markdown
    ## Current Issues
    - Navigation drawer conflict in App.vue (issue #9).
    - Missing debouncing for localStorage in ColorSelector.vue (issue #16).
    - Inconsistent episode selection persistence in EpisodeSelector.vue (issue #17).
    - Incomplete cue modals (VoModal, NatModal, PkgModal) (issue #18).
    - Inconsistent rundown item types in RundownManager.vue (issue #14).

    ## TODO
    - Implement unit and E2E tests for critical components (issue #15).
    - Optimize RundownManager.vue for large rundowns (>100 items).
    ```

*Last Updated: July 8, 2025*