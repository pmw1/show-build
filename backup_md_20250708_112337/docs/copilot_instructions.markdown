# Instructions for Copilot: Addressing Issues in Disaffected Production Suite

## Overview
The Disaffected Production Suite is a web-based application designed to streamline broadcast content creation for the "Disaffected" podcast and TV show, replacing Obsidian-based workflows while maintaining compatibility with Markdown files, YAML frontmatter, and directory structure. The suite aims to unify pre-production, production, and promotion workflows using Vue.js, FastAPI, and MQTT, with a focus on reliability, performance, and user satisfaction. This document updates and extends the existing instructions for Copilot to address critical issues identified in the provided files, focusing on frontend components (`ContentEditor.vue`, `RundownManager.vue`, `ColorSelector.vue`, `EditorPanel.vue`, `RundownPanel.vue`, `EpisodeSelector.vue`) and ensuring alignment with project goals.

## Issues and Fixes

### 1. Proxy Configuration Mismatch in `vue.config.js`
- **Issue**: `vue.config.js` proxies `/api` to `http://192.168.51.210:8888`, but some components (e.g., `RundownManager.vue`) use `http://127.0.0.1:8000`, causing inconsistent API requests and failures.
- **Fix**:
  Standardize proxy configuration in `vue.config.js`:
  ```javascript
  module.exports = {
    transpileDependencies: true,
    devServer: {
      host: '0.0.0.0',
      port: 8080,
      allowedHosts: 'all',
      proxy: {
        '/api': {
          target: 'http://192.168.51.210:8888',
          changeOrigin: true,
          secure: false,
          pathRewrite: { '^/api': '' }
        }
      }
    }
  }
  ```
  Update `RundownManager.vue` to use relative paths (e.g., `/api/episodes` instead of `http://127.0.0.1:8000/api/episodes`).

### 2. Redundant Proxy Servers
- **Issue**: `simple-server.js` and `proxy-server.py` both serve as proxies on port `8080`, risking conflicts. `vue.config.js` should handle development proxying.
- **Fix**:
  Remove `proxy-server.py`. Use `simple-server.js` for production and `vue.config.js` for development. Update `package.json` scripts:
  ```json
  "scripts": {
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint",
    "start:prod": "node simple-server.js"
  }
  ```
  Ensure `simple-server.js` proxies to `http://192.168.51.210:8888`.

### 3. Unstable Express Version
- **Issue**: `package.json` uses `express: ^5.1.0` (beta), risking instability.
- **Fix**:
  Update `package.json` to use stable Express:
  ```json
  "dependencies": {
    "express": "^4.17.3"
  }
  ```
  Run `npm install`.

### 4. Missing Vuex/Pinia Dependency in `SettingsView.vue`
- **Issue**: `SettingsView.vue` uses `this.$store.state.auth.token`, but no state management library is included.
- **Fix**:
  Add Pinia to `package.json`:
  ```json
  "dependencies": {
    "pinia": "^2.1.7"
  }
  ```
  Initialize in `main.js`:
  ```javascript
  import { createPinia } from 'pinia';
  app.use(createPinia());
  ```
  Create `src/stores/auth.js`:
  ```javascript
  import { defineStore } from 'pinia';
  export const useAuthStore = defineStore('auth', {
    state: () => ({
      token: localStorage.getItem('auth-token') || null
    })
  });
  ```

### 5. Missing Toast Library in `SettingsView.vue`
- **Issue**: `this.$toast` is used without a toast library.
- **Fix**:
  Add `vue-toastification` to `package.json`:
  ```json
  "dependencies": {
    "vue-toastification": "^2.0.0"
  }
  ```
  Initialize in `main.js`:
  ```javascript
  import Toast from 'vue-toastification';
  import 'vue-toastification/dist/index.css';
  app.use(Toast);
  ```

### 6. Incorrect Axios Usage in `SettingsView.vue` and `RundownManager.vue`
- **Issue**: `this.$axios` is undefined in `SettingsView.vue`; `RundownManager.vue` uses absolute URLs (`http://127.0.0.1:8000`).
- **Fix**:
  Register axios globally in `main.js`:
  ```javascript
  import axios from 'axios';
  app.config.globalProperties.$axios = axios;
  ```
  Update `RundownManager.vue` to use relative paths (e.g., `/api/episodes`).

### 7. Color Mismatch and Persistence Issues in `themeColorMap.js`
- **Issue**: `themeColorMap.js` uses outdated Material Design colors (e.g., `cyan`, `yellow-accent`) instead of Vuetify theme colors (`primary`, `accent`). `updateColor` lacks `localStorage` and backend persistence, and `ColorSelector.vue` causes `[ColorSelector] baseColors is not an array: undefined` error due to uninitialized `baseColors`.
- **Fix**:
  Update `themeColorMap.js` to use Vuetify colors and add persistence:
  ```javascript
  const defaultColors = {
    'segment': 'info',         // #2196F3
    'ad': 'primary',           // #1976D2
    'promo': 'success',        // #4CAF50
    'cta': 'accent',           // #82B1FF
    'trans': 'secondary',      // #424242
    'unknown': 'grey',         // #9E9E9E
    'selection': 'warning',    // #FB8C00
    'hover': 'blue-lighten-4', // #BBDEFB
    'draglight': 'cyan-lighten-4', // #B2EBF2
    'highlight': 'yellow-lighten-3', // #FFF9C4
    'dropline': 'green-lighten-4', // #C8E6C9
    'draft': 'grey-darken-2',  // #616161
    'approved': 'green-accent', // #69F0AE
    'production': 'blue-accent', // #448AFF
    'completed': 'yellow-accent' // #FFD740
  };
  let currentColors = { ...defaultColors };

  export const getColorValue = (type) => {
    return currentColors[type.toLowerCase()] || defaultColors[type.toLowerCase()] || 'grey';
  };

  export const updateColor = (type, newColor) => {
    try {
      const updatedColors = { ...currentColors, [type.toLowerCase()]: newColor };
      currentColors = updatedColors;
      localStorage.setItem('themeColors', JSON.stringify(updatedColors));
      fetch('/api/settings/colors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ colors: updatedColors })
      });
      return true;
    } catch (err) {
      console.error('Failed to update color:', err);
      return false;
    }
  };

  export const resolveVuetifyColor = (colorName, vuetifyInstance, textColor = '#FFFFFF') => {
    if (!colorName) return '#000000';
    if (!vuetifyInstance?.theme?.themes) return '#000000';
    const theme = vuetifyInstance.theme.themes[vuetifyInstance.theme.dark ? 'dark' : 'light'].colors;
    const color = theme[colorName] || '#000000';
    const contrastRatio = getContrastRatio(color, textColor);
    if (contrastRatio < 4.5) {
      console.warn(`Low contrast for ${colorName}: ${color} (ratio: ${contrastRatio})`);
      return '#000000';
    }
    return color;
  };

  const getContrastRatio = (color1, color2) => {
    const luminance = (hex) => {
      const rgb = parseInt(hex.replace('#', ''), 16);
      const r = (rgb >> 16) & 0xff;
      const g = (rgb >> 8) & 0xff;
      const b = rgb & 0xff;
      return 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);
    };
    const lum1 = luminance(color1);
    const lum2 = luminance(color2);
    return (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
  };
  ```
  Update `ColorSelector.vue` to initialize `baseColors`:
  ```javascript
  computed: {
    baseColorOptions() {
      const theme = this.$vuetify?.theme?.themes?.light?.colors || {};
      return Object.entries(theme).map(([key, value]) => ({
        title: key.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value: key,
      }));
    }
  },
  ```

### 8. Incomplete Views (`TemplatesView.vue`, `AssetsView.vue`, `DashboardView.vue`)
- **Issue**: These views lack core functionality, contradicting `features_and_integrations.md`.
- **Fix**:
  Update `todo_and_issues.md` to document incomplete views:
  ```markdown
  ## Incomplete Views
  - TemplatesView.vue: Missing create/edit/delete logic for templates.
  - AssetsView.vue: Placeholder; no asset management functionality.
  - DashboardView.vue: Placeholder; lacks stats and interactivity.
  ```

### 9. Navigation Drawer Issue in `App.vue`
- **Issue**: Temporary drawer conflicts with `style_guide.md`’s 40% width rundown panel in `ContentEditor.vue`.
- **Fix**:
  Update `App.vue`:
  ```vue
  <v-navigation-drawer v-model="drawer" :temporary="$route.name !== 'ContentEditor'">
    <!-- Drawer content -->
  </v-navigation-drawer>
  ```

### 10. Deprecated `vuetifyColorNames.js`
- **Issue**: Deprecated file may cause confusion as `themeColorMap.js` handles color logic.
- **Fix**:
  Delete `vuetifyColorNames.js`. Ensure all components reference `themeColorMap.js`.

### 11. Authentication Logic Duplication
- **Issue**: `App.vue` and `ProfileView.vue` duplicate auth logic, risking inconsistent state.
- **Fix**:
  Create `src/composables/useAuth.js`:
  ```javascript
  import { ref } from 'vue';
  import axios from 'axios';
  export function useAuth() {
    const isAuthenticated = ref(false);
    const currentUser = ref({});
    const checkAuthStatus = () => {
      const token = localStorage.getItem('auth-token');
      const expiry = localStorage.getItem('auth-token-expiry');
      const userData = localStorage.getItem('user-data');
      if (token && expiry && userData) {
        const currentTime = Date.now();
        const expiryTime = parseInt(expiry);
        if (currentTime < expiryTime) {
          isAuthenticated.value = true;
          currentUser.value = JSON.parse(userData);
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        } else {
          clearAuthData();
        }
      }
    };
    const handleLogout = () => {
      isAuthenticated.value = false;
      currentUser.value = {};
      localStorage.removeItem('auth-token');
      localStorage.removeItem('auth-token-expiry');
      localStorage.removeItem('user-data');
      delete axios.defaults.headers.common['Authorization'];
    };
    const clearAuthData = () => {
      isAuthenticated.value = false;
      currentUser.value = {};
      localStorage.removeItem('auth-token');
      localStorage.removeItem('auth-token-expiry');
      localStorage.removeItem('user-data');
      delete axios.defaults.headers.common['Authorization'];
    };
    return { isAuthenticated, currentUser, checkAuthStatus, handleLogout };
  }
  ```
  Update `App.vue` and `ProfileView.vue` to use `useAuth`.

### 12. Drag-and-Drop Error in `ContentEditor.vue`
- **Issue**: Drag-and-drop in `ContentEditor.vue` causes `Cannot read properties of null` error, disabling functionality (`todo_and_issues.md`).
- **Fix**:
  Update `ContentEditor.vue` drag methods to handle null cases:
  ```javascript
  methods: {
    dragStart(event, item, index) {
      if (!item) return;
      this.isDragging = true;
      this.draggedIndex = index;
      this.draggedItem = item;
      event.dataTransfer.setData('text/plain', index.toString());
      event.dataTransfer.effectAllowed = 'move';
    },
    dragOver(event, index) {
      if (!this.isDragging || index === this.draggedIndex || !this.rundownItems[index]) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const midpoint = rect.top + rect.height / 2;
      this.dragOverIndex = index;
      this.dropZonePosition = event.clientY < midpoint ? 'above' : 'below';
    },
    dragDrop(event, targetIndex) {
      if (!this.isDragging || !this.draggedItem || !this.rundownItems[targetIndex]) return;
      this.dragOverIndex = -1;
      this.dropZonePosition = null;
      const sourceIndex = this.draggedIndex;
      if (sourceIndex === targetIndex) {
        this.isDragging = false;
        this.draggedIndex = -1;
        this.draggedItem = null;
        return;
      }
      let finalTargetIndex = targetIndex;
      if (this.dropZonePosition === 'below') {
        finalTargetIndex = targetIndex + 1;
      }
      if (sourceIndex < finalTargetIndex) {
        finalTargetIndex--;
      }
      const newItems = [...this.rundownItems];
      const [draggedItem] = newItems.splice(sourceIndex, 1);
      newItems.splice(finalTargetIndex, 0, draggedItem);
      this.rundownItems = newItems;
      this.hasUnsavedChanges = true;
      if (this.selectedItemIndex === sourceIndex) {
        this.selectedItemIndex = finalTargetIndex;
      }
      this.isDragging = false;
      this.draggedIndex = -1;
      this.draggedItem = null;
    }
  }
  ```

### 13. `e.getModeIcon is not a function` Error in `EditorPanel.vue`
- **Issue**: `EditorPanel.vue` throws `e.getModeIcon is not a function` due to incorrect v-icon binding.
- **Fix**:
  Update `EditorPanel.vue` template to use `getModeIcon` method directly:
  ```vue
  <v-chip size="small" variant="text" class="mr-2 d-flex align-center" style="padding: 0 12px; min-width: 110px;">
    <v-icon left>{{ getModeIcon(editorMode) }}</v-icon>
    {{ editorMode.toUpperCase() }} MODE
  </v-chip>
  ```

### 14. Inconsistent Rundown Item Types Across Components
- **Issue**: Rundown item types differ across components:
  - `ContentEditor.vue`: `segment`, `advert`, `promo`, `cta`, `unknown`
  - `RundownManager.vue`: `segment`, `promo`, `advert`, `feature`, `sting`, `cta`
  - `RundownPanel.vue`: `segment`, `ad`, `promo`, `cta`, `trans`
  - `ColorSelector.vue`: `Advert`, `CTA`, `Promo`, `Segment`, `Trans`
  This causes rendering inconsistencies and potential API mismatches.
- **Fix**:
  Standardize item types in `themeColorMap.js` and update components:
  ```javascript
  const defaultColors = {
    'segment': 'info',
    'ad': 'primary',
    'promo': 'success',
    'cta': 'accent',
    'trans': 'secondary',
    'unknown': 'grey',
    'selection': 'warning',
    'hover': 'blue-lighten-4',
    'draglight': 'cyan-lighten-4',
    'highlight': 'yellow-lighten-3',
    'dropline': 'green-lighten-4',
    'draft': 'grey-darken-2',
    'approved': 'green-accent',
    'production': 'blue-accent',
    'completed': 'yellow-accent'
  };
  ```
  Update `ContentEditor.vue`, `RundownManager.vue`, `RundownPanel.vue`, and `ColorSelector.vue` to use:
  - `segment`, `ad`, `promo`, `cta`, `trans`, `unknown`
  Example for `RundownManager.vue`:
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

### 15. Missing Unit Tests for Critical Components
- **Issue**: No unit or E2E tests for `ContentEditor.vue`, `RundownManager.vue`, `ColorSelector.vue`, `EditorPanel.vue`, `RundownPanel.vue`, and `themeColorMap.js`, risking regressions.
- **Fix**:
  Add testing dependencies to `package.json`:
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

### 16. Performance Issue with `localStorage` Writes in `ColorSelector.vue`
- **Issue**: Frequent `localStorage` writes in `saveColors` without debouncing can degrade performance for large rundowns.
- **Fix**:
  Update `ColorSelector.vue` to debounce `saveColors`:
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

### 17. Inconsistent Episode Selection in `EpisodeSelector.vue`
- **Issue**: `EpisodeSelector.vue` does not persist selected episode to `sessionStorage`, causing loss of context on refresh.
- **Fix**:
  Update `EpisodeSelector.vue`:
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

### 18. Missing Cue Modal Implementations
- **Issue**: `ContentEditor.vue` references modals (`FsqModal`, `SotModal`, `VoModal`, `NatModal`, `PkgModal`) without full implementations, breaking cue insertion (`todo_and_issues.md`).
- **Fix**:
  Create `src/components/modals/FsqModal.vue` (and similarly for others):
  ```vue
  <template>
    <v-dialog v-model="show" max-width="500">
      <v-card>
        <v-card-title>Add Full-Screen Quote</v-card-title>
        <v-card-text>
          <v-text-field v-model="quote" label="Quote Text" variant="outlined"></v-text-field>
          <v-text-field v-model="source" label="Source" variant="outlined"></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    props: {
      show: { type: Boolean, default: false }
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        quote: '',
        source: ''
      };
    },
    methods: {
      submit() {
        this.$emit('submit', { type: 'FSQ', quote: this.quote, source: this.source });
        this.reset();
      },
      cancel() {
        this.$emit('update:show', false);
        this.reset();
      },
      reset() {
        this.quote = '';
        this.source = '';
      }
    }
  };
  </script>
  ```
  Update `ContentEditor.vue` to handle modal submissions:
  ```javascript
  methods: {
    submitFsq(data) {
      this.scriptContent += `[FSQ: ${data.quote} | ${data.source}]\n`;
      this.showFsqModal = false;
      this.hasUnsavedChanges = true;
    },
    // Add similar methods for other modals
  }
  ```

### 19. Accessibility Issues in Color System
- **Issue**: Colors in `ColorSelector.vue` and `themeColorMap.js` may not meet WCAG 2.1 AA contrast requirements, especially for light colors (e.g., `yellow-lighten-3`).
- **Fix**:
  Ensure `resolveVuetifyColor` in `themeColorMap.js` enforces contrast (already included above). Update `ColorSelector.vue` preview styles:
  ```vue
  <div 
    class="preview-box" 
    :style="{
      backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(getFullColor(type)), $vuetify),
      color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey(getFullColor(type)), $vuetify)),
      width: '60px',
      height: '28px',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 500,
      border: '1px solid #000' // Add border for low-contrast cases
    }"
  >
    {{ type }}
  </div>
  ```

## Additional Notes
- **Prioritize**: Proxy fix (#1), drag-and-drop fix (#12), color system updates (#7, #19), and cue modal implementations (#18) for immediate stability and usability.
- **Alignment with Purpose**: Fixes ensure reliable content creation, consistent styling, and accessibility, aligning with the goal of streamlining broadcast workflows and maintaining Obsidian compatibility.
- **Documentation**: Update `todo_and_issues.md` with:
  ```markdown
  ## Known Issues
  - Inconsistent rundown item types across components (fixed in #14).
  - Missing cue modal implementations (fixed in #18).
  - Accessibility issues in color system (fixed in #19).

  ## TODO
  - Implement E2E tests for `ContentEditor.vue` and `RundownManager.vue`.
  - Optimize `RundownManager.vue` for large rundowns (>100 items).
  ```
- **Testing**: Run `npm test` after adding unit tests to verify fixes.

*Last Updated: July 8, 2025*