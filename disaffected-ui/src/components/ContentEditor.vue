<template>
  <div class="content-editor-wrapper">
    <!-- Main Toolbar -->
    <v-toolbar dense flat class="main-toolbar" style="height: 128px; min-height: 128px; max-height: 128px; align-items: flex-start;">
      <v-spacer></v-spacer>
      <v-toolbar-items>
        <v-btn text @click="saveAllContent">Save</v-btn>
        <v-btn text>Publish</v-btn>
      </v-toolbar-items>
    </v-toolbar>

    <!-- Show Info Header (restored) -->
    <ShowInfoHeader
      :title="currentShowTitle"
      :episode-info="currentEpisodeInfo"
      :episode-number="currentEpisodeNumber"
      :air-date="currentAirDate"
      :production-status="currentProductionStatus"
      :total-runtime="totalRuntime"
      :episodes="episodes"
      :production-statuses="productionStatuses"
      @update:episodeNumber="handleEpisodeChange"
      @update:airDate="val => currentAirDate = val"
      @update:productionStatus="val => currentProductionStatus = val"
    />

    <!-- Color Configuration Panel -->
    <ColorSelector />

    <!-- Main Content Area (restored) -->
    <div class="main-content-area">
      <!-- Rundown Panel -->
      <v-card class="rundown-panel" flat
             :style="{ border: '2px solid ' + statusBarColor, borderRadius: '0' }">
        <div class="script-status-horizontal-bar"
             :style="{ backgroundColor: statusBarColor, color: statusBarTextColor }">
          <span class="status-text">{{ currentProductionStatus }}</span>
        </div>
        <div class="rundown-header-row">
          <span class="rundown-header-title">Rundown</span>
          <div style="flex:1"></div>
          <v-btn icon x-small class="rundown-header-btn" @click="showNewItemModal = true"><v-icon size="18">mdi-plus</v-icon></v-btn>
          <v-btn icon x-small class="rundown-header-btn"><v-icon size="18">mdi-dots-vertical</v-icon></v-btn>
        </div>
        <div>
          <div class="rundown-table-header">
            <div class="index-container">Index</div>
            <div class="item-type-cell">Type</div>
            <div class="item-details">Slug</div>
            <div class="item-duration">Duration</div>
          </div>
          <v-virtual-scroll
            :items="rundownItems"
            :item-height="26"
            class="rundown-list"
            bench="10"
          >
            <template v-slot:default="{ item, index }">
              <div
                class="rundown-item"
                :class="{
                  'selected-item': selectedItemIndex === index,
                  'ghost-class': isDragging && draggedIndex === index,
                  'drag-over-above': dragOverIndex === index && dropZonePosition === 'above',
                  'drag-over-below': dragOverIndex === index && dropZonePosition === 'below'
                }"
                :style="resolveItemStyle(item, index)"
                draggable="true"
                @click="selectRundownItem(index)"
                @dragstart="dragStart($event, item, index)"
                @dragend="dragEnd($event, item, index)"
                @dragover.prevent="dragOver($event, index)"
                @drop.prevent="dragDrop($event, index)"
              >
                <div class="item-content">
                  <div class="index-container">
                    <span class="item-index">{{ index + 1 }}</span>
                  </div>
                  <div class="item-type-cell">
                    <span class="item-type">{{ item.type.toUpperCase() }}</span>
                  </div>
                  <div class="item-details">
                    <span class="item-slug">{{ item.slug.toLowerCase() }}</span>
                  </div>
                  <span class="item-duration">{{ item.duration }}</span>
                </div>
              </div>
            </template>
          </v-virtual-scroll>
        </div>
      </v-card>

      <!-- Editor Panel -->
      <div class="editor-panel">
        <EditorPanel
          :item="currentRundownItem"
          v-model:script-content="scriptContent"
          v-model:scratch-content="scratchContent"
          v-model:editor-mode="editorMode"
          @update:editor-mode="editorMode = $event"
          :has-unsaved-changes="hasUnsavedChanges"
          :show-rundown-panel="showRundownPanel"
          @save="saveAllContent"
          @toggle-rundown-panel="showRundownPanel = !showRundownPanel"
          @show-asset-browser-modal="showAssetBrowserModal = true"
          @show-template-manager-modal="showTemplateManagerModal = true"
          @show-gfx-modal="showGfxModal = true"
          @show-fsq-modal="showFsqModal = true"
          @show-sot-modal="showSotModal = true"
          @show-vo-modal="showVoModal = true"
          @show-nat-modal="showNatModal = true"
          @show-pkg-modal="showPkgModal = true"
          @show-vox-modal="showVoxModal = true"
          @show-mus-modal="showMusModal = true"
          @show-live-modal="showLiveModal = true"
          @content-change="onContentChange"
          @metadata-change="onMetadataChange"
        />
      </div>
    </div>

    <!-- Modals -->
    <AssetBrowserModal
      :visible="showAssetBrowserModal"
      @update:visible="showAssetBrowserModal = $event"
      @asset-selected="insertAssetReference"
    />

    <TemplateManagerModal
      :visible="showTemplateManagerModal"
      @update:visible="showTemplateManagerModal = $event"
      @template-selected="insertTemplateReference"
    />

    <GfxModal
      v-model:show="showGfxModal"
      v-model:slug="gfxSlug"
      v-model:description="gfxDescription"
      :graphic-preview="graphicPreview"
      @paste-from-clipboard="pasteFromClipboard"
      @select-file="selectFile"
      @paste-url="pasteUrl"
      @submit="submitGraphic"
    />

    <FsqModal v-model:show="showFsqModal" @submit="submitFsq" />
    <SotModal v-model:show="showSotModal" @submit="submitSot" />
    <VoModal v-model:show="showVoModal" @submit="submitVo" />
    <NatModal v-model:show="showNatModal" @submit="submitNat" />
    <PkgModal v-model:show="showPkgModal" @submit="submitPkg" />
    <VoxModal v-model:show="showVoxModal" @submit="submitVox" />
    <MusModal v-model:show="showMusModal" @submit="submitMus" />
    <LiveModal v-model:show="showLiveModal" @submit="submitLive" />

    <NewItemModal
      v-model:show="showNewItemModal"
      v-model:valid="newItemFormValid"
      v-model:type="newItemType"
      v-model:slug="newItemSlug"
      v-model:duration="newItemDuration"
      v-model:description="newItemDescription"
      :loading="creatingNewItem"
      :item-types="rundownItemTypes"
      :duration-rules="durationRules"
      @create="createNewItem"
      @cancel="cancelNewItem"
    />
  </div>
</template>

<script>
import axios from 'axios';
// import { API_BASE_URL } from '@/config.js'; // Temporarily remove to simplify
import EditorPanel from './EditorPanel.vue';
import AssetBrowserModal from './modals/AssetBrowserModal.vue';
import TemplateManagerModal from './modals/TemplateManagerModal.vue';
import GfxModal from './modals/GfxModal.vue';
import FsqModal from './modals/FsqModal.vue';
import SotModal from './modals/SotModal.vue';
import VoModal from './modals/VoModal.vue';
import NatModal from './modals/NatModal.vue';
import PkgModal from './modals/PkgModal.vue';
import VoxModal from './modals/VoxModal.vue';
import MusModal from './modals/MusModal.vue';
import LiveModal from './modals/LiveModal.vue';
import NewItemModal from './modals/NewItemModal.vue';
import ColorSelector from './ColorSelector.vue';
import ShowInfoHeader from './content-editor/ShowInfoHeader.vue';
import { getColorValue, resolveVuetifyColor } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';

export default {
  name: 'ContentEditor',
  
  async mounted() {
    await this.fetchShowInfo();
    await this.fetchEpisodes();
  },

  created() {
    // Initialize currentEpisodeNumber from sessionStorage if available
    const lastEpisode = sessionStorage.getItem('selectedEpisode');
    if (lastEpisode) {
      this.currentEpisodeNumber = lastEpisode;
    }
    this.debouncedAutoSave = debounce(this.saveAllContent, 2500);
  },

  components: {
    EditorPanel,
    AssetBrowserModal,
    TemplateManagerModal,
    GfxModal,
    FsqModal,
    SotModal,
    VoModal,
    NatModal,
    PkgModal,
    VoxModal,
    MusModal,
    LiveModal,
    NewItemModal,
    ColorSelector,
    ShowInfoHeader,
  },
  props: {
    // episode: {
    //   type: String,
    //   default: null
    // }
  },
  data() {
    return {
      // Layout state
      showRundownPanel: true,
      rundownPanelWidth: 'wide', // 'narrow' or 'wide'
      
      // Editor state
      editorMode: 'script', // 'script', 'scratch', 'metadata', or 'code'
      selectedItemIndex: -1, // Start with no selection
      editingItemIndex: -1, // Index of item being edited (grows by 2%)
      hasUnsavedChanges: false,
      loadingRundown: true, // Start in loading state
      rundownError: null,
      
      // Show Information
      showInfo: {},
      currentEpisodeNumber: '', // This will be updated from session
      currentAirDate: '',
      currentProductionStatus: 'draft',
      productionStatuses: [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ],
      
      // Episode management
      selectedEpisode: null,
      episodes: [],
      loading: false,
      saving: false,
      
      // Drag state
      isDragging: false,
      draggedIndex: -1,
      draggedItem: null,
      dragOverIndex: -1, // Index of the item being dragged over
      dropZonePosition: null, // 'above' or 'below'
      
      // Auto-save tracking
      itemContentBackup: {},
      autoSaveOnSwitch: true, // Auto-save when switching items instead of prompting
      autoSaveTimeout: null,
      hoveredItemIndex: -1, // Index of the item being hovered
      
      // Content
      scriptContent: '',
      scratchContent: '',
      
      // Asset management
      showAssetBrowserModal: false, // Standardized name
      showTemplateManagerModal: false, // Standardized name
      selectedFiles: [],
      availableAssets: [
        // Mock data - will be replaced with API calls
        {
          id: 'asset_001',
          filename: 'opening_graphics.png',
          type: 'image',
          url: '/assets/opening_graphics.png',
          thumbnail: '/assets/thumbs/opening_graphics.png'
        },
        {
          id: 'asset_002',
          filename: 'interview_segment.mp4',
          type: 'video',
          url: '/assets/interview_segment.mp4'
        }
      ],
      
      // Mock rundown data - TODO: Replace with props/API when backend is ready
      rundownItems: [
        // Mock data for testing drag and drop - remove when API is integrated
        {
          id: 'item_001',
          type: 'segment',
          slug: 'opening-segment',
          duration: '00:02:30',
          description: 'Opening segment with intro graphics'
        },
        {
          id: 'item_002',
          type: 'sot',
          slug: 'interview-smith',
          duration: '00:05:45',
          description: 'Interview with John Smith'
        },
        {
          id: 'item_003',
          type: 'pkg',
          slug: 'climate-report',
          duration: '00:03:15',
          description: 'Climate change report package'
        },
        {
          id: 'item_004',
          type: 'commercial',
          slug: 'commercial-break-1',
          duration: '00:02:00',
          description: 'First commercial break'
        },
        {
          id: 'item_005',
          type: 'vo',
          slug: 'sports-highlights',
          duration: '00:01:45',
          description: 'Sports highlights voiceover'
        }
      ],
      
      // Metadata editing
      currentItemMetadata: {
        title: '',
        type: 'segment',
        slug: '',
        duration: '00:05:30',
        description: '',
        guests: '',
        tags: '',
        sponsor: '',
        campaign: '',
        segment_number: 1,
        live_status: 'live'
      },
      customMetadataYaml: '',
      itemTypes: [
        { title: 'Segment', value: 'segment' },
        { title: 'Advertisement', value: 'ad' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Unknown', value: 'unknown' }
      ],
      
      // Graphic attachment state
      showGfxModal: false,
      showFsqModal: false,
      showSotModal: false,
      showVoModal: false,
      showNatModal: false,
      showPkgModal: false,
      showVoxModal: false,
      showMusModal: false,
      showLiveModal: false,
      
      // Rundown management state
      showNewItemModal: false,
      showRundownOptions: false,
      
      // New item form state
      newItemFormValid: false,
      newItemType: '',
      newItemTitle: '',
      newItemSlug: '',
      newItemDuration: '',
      newItemDescription: '',
      newItemGuests: '',
      newItemCustomer: '',
      newItemLink: '',
      creatingNewItem: false,
      
      // Available rundown item types
      rundownItemTypes: [
        { title: 'Segment', value: 'segment' },
        { title: 'Advertisement', value: 'ad' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Transition', value: 'trans' }
      ],
      
      graphicDetails: {
        url: '',
        file: null
      },
      gfxSlug: '',
      gfxDescription: '',
      graphicPreview: null,
      graphicFile: null,
      
      // Total runtime for the episode
      totalRuntime: '00:00:00',

      // Show title for the current episode
      showTitle: 'Disaffected',
    }
  },
   computed: {
    styleCache() {
      // This computed property acts as a reactive cache for our item styles.
      // It depends on the Vuetify theme object, so it will automatically
      // re-calculate if the user changes the application's theme colors.
      const theme = this.$vuetify.theme;
      if (!theme) return {};

      const cache = {};
      const currentTheme = theme.dark ? 'dark' : 'light';
      const themeColors = theme.themes[currentTheme];

      // Define all possible sources for colors.
      const itemTypes = this.rundownItemTypes.map(t => t.value ? t.value.toLowerCase() : '');
      const states = ['selection', 'hover', 'draglight', 'highlight', 'dropline'];
      const allColorSources = [...new Set([...states, ...itemTypes, 'unknown'])];

      for (const source of allColorSources) {
        const colorName = getColorValue(source);
        const colorValue = themeColors[colorName]; // e.g., themeColors['primary']
        if (colorValue) {
          cache[source] = { backgroundColor: colorValue };
        }
      }

      return cache;
    },

    currentShowTitle() {
      // Use the title from showTitle data property if available, otherwise fallback
      return this.showTitle || (this.showInfo && this.showInfo.title) || 'Disaffected';
    },

    currentEpisodeInfo() {
      try {
        const episode = this.episodes.find(e => e.id === this.selectedEpisodeId);
        if (!episode) {
          return { title: 'No episode selected', status: 'unknown' };
        }
        return {
          title: episode.title,
          status: episode.status || 'unknown'
        };
      } catch (error) {
        // console.error('Error in currentEpisodeInfo:', error);
        return { title: 'Error', status: 'error' };
      }
    },
    
    // Layout width calculations for consistent sizing
    rundownPanelWidthValue() {
      return this.rundownPanelWidth === 'narrow' ? '25%' : '40%'
    },
    
    rundownHeaderWidth() {
      return this.rundownPanelWidth === 'narrow' ? '25%' : '40%'
    },
    
    cueToolbarWidth() {
      if (!this.showRundownPanel) return '100%'
      return this.rundownPanelWidth === 'narrow' ? '75%' : '60%'
    },
    
    statusBarColor() {
      try {
        const status = this.currentEpisodeInfo.status;
        const color = this.themeColorMap.status[status];
        return color || 'grey';
      } catch (error) {
        // console.error('Error in statusBarColor computed property:', error);
        return 'grey';
      }
    },
    statusBarTextColor() {
      try {
        const color = this.statusBarColor;
        return this.isDarkColor(color) ? 'white' : 'black';
      } catch (error) {
        // console.error('Error in statusBarTextColor computed property:', error);
        return 'black';
      }
    },
    
    scriptPlaceholder() {
      return `# ${this.currentRundownItem?.slug || 'Script Content'}\n\nWrite your script content here using Markdown...\n\nUse the toolbar buttons above to insert:\n- **GFX** cues for graphics\n- **FSQ** cues for full-screen quotes  \n- **SOT** cues for video content\n\nExample:\n[GFX: opening_title.png]\nWelcome to today's show...\n\n[SOT: interview_clip.mp4 | 0:30-2:15]\nHere's what our guest had to say...`
    },
    
    scratchPlaceholder() {
      return `# Brainstorming & Notes

Use this space for:
• Research notes and ideas
• Asset planning and references  
• Interview questions
• Production notes

💡 **Smart Features:**
- Drag & drop assets from your file system
- Paste URLs for automatic link cards
- @ mentions for collaboration
- # tags for organization

Try dropping an image or video file here!`
    },
    
    currentRundownItem() {
      return (this.rundownItems && this.rundownItems[this.selectedItemIndex]) || null
    },
    
    // Form validation rules
    titleRules() {
      return [
        v => !!v || 'Title is required'
      ]
    },
    durationRules() {
      return [
        v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS format'
      ]
    }
  },
  methods: {
    resolveItemStyle(item, index) {
      try {
        const itemType = item && item.type ? item.type.toLowerCase() : 'unknown';
        let style = {};

        // Base style from the theme color map
        const colorName = getColorValue(itemType);
        const resolvedColor = resolveVuetifyColor(colorName, this.$vuetify);

        if (resolvedColor) {
          style.backgroundColor = resolvedColor;
          // Simple luminance check for text color
          if (resolvedColor.startsWith('#')) {
            const hex = resolvedColor.replace('#', '');
            if (hex.length === 6) {
              const r = parseInt(hex.substr(0,2), 16);
              const g = parseInt(hex.substr(2,2), 16);
              const b = parseInt(hex.substr(4,2), 16);
              style.color = (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5 ? '#FFFFFF' : '#000000';
            } else {
              style.color = '#000000';
            }
          } else {
            style.color = '#000000';
          }
        } else {
          style.backgroundColor = '#E0E0E0'; // Fallback grey
          style.color = '#000000';
        }

        // Override for selected item
        if (this.selectedItemIndex === index) {
          const selectionColorName = getColorValue('selection');
          const selectionColor = resolveVuetifyColor(selectionColorName, this.$vuetify);
          if (selectionColor) {
            style.backgroundColor = selectionColor;
            // Simple luminance check for text color
            if (selectionColor.startsWith('#')) {
              const hex = selectionColor.replace('#', '');
              if (hex.length === 6) {
                const r = parseInt(hex.substr(0,2), 16);
                const g = parseInt(hex.substr(2,2), 16);
                const b = parseInt(hex.substr(4,2), 16);
                style.color = (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5 ? '#FFFFFF' : '#000000';
              } else {
                style.color = '#000000';
              }
            } else {
              style.color = '#000000';
            }
          }
        }
        // Override for hovered item (but not if it's the selected item)
        else if (this.hoveredItemIndex === index) {
           const hoverColorName = getColorValue('hover');
           const hoverColor = resolveVuetifyColor(hoverColorName, this.$vuetify);
           if (hoverColor) {
             // Add a subtle border instead of changing the whole background
             style.boxShadow = `inset 4px 0 0 0 ${hoverColor}`;
           }
        }

        return style;
      } catch (error) {
        // console.error('Error in resolveItemStyle:', error);
        return {}; // Return empty object on error
      }
    },

    async fetchShowInfo() {
      this.loading = true;
      try {
        // Use a relative path that the proxy will catch
        const response = await axios.get('/api/show-info');
        this.showInfo = response.data;
        this.showTitle = response.data.title || 'Disaffected';
      } catch (error) {
        this.rundownError = 'Failed to load show information. Please check backend connection.';
        this.showTitle = 'Disaffected';
      } finally {
        this.loading = false;
      }
    },

    async fetchEpisodes() {
      this.loading = true;
      this.rundownError = null;
      try {
        // Use a relative path that the proxy will catch
        const response = await axios.get('/api/episodes');
        const episodesArr = response.data.episodes || [];
        if (Array.isArray(episodesArr)) {
          this.episodes = episodesArr.map(episode => ({
            // Always use zero-padded string for value
            title: `${episode.id || episode.episode_number}: ${episode.title || 'Untitled'}`,
            value: episode.id ? episode.id.toString().padStart(4, '0') : (episode.episode_number ? episode.episode_number.toString().padStart(4, '0') : ''),
            air_date: episode.airdate,
            status: episode.status || 'unknown'
          }));
        } else {
          this.episodes = [];
        }
        
        // Restore last selected episode from session storage
        const lastEpisode = sessionStorage.getItem('selectedEpisode');
        let episodeToLoad = null;

        if (lastEpisode && this.episodes.some(e => e.value == lastEpisode)) {
          episodeToLoad = lastEpisode;
        } else if (this.episodes.length > 0) {
          // Default to the latest episode (assuming they are sorted by episode_number)
          const sortedEpisodes = [...this.episodes].sort((a, b) => b.value - a.value);
          episodeToLoad = sortedEpisodes[0].value;
        }
        
        if (episodeToLoad) {
          this.handleEpisodeChange(episodeToLoad, true);
        }
        // Ensure currentEpisodeNumber matches a value in the episodes list
        if (!this.episodes.some(e => e.value === this.currentEpisodeNumber) && this.episodes.length > 0) {
          this.currentEpisodeNumber = this.episodes[0].value;
        }
        
      } catch (error) {
        this.rundownError = `Failed to load episodes. ${error.message}. Check console for details.`;
        this.rundownError = 'Failed to load episodes. No data available.';
        this.episodes = [];
      } finally {
        this.loading = false;
      }
    },

    padEpisodeNumber(num) {
      // Always returns a string padded to 4 digits
      if (typeof num === 'number') num = String(num);
      return num ? num.padStart(4, '0') : '';
    },
    async fetchRundown(episodeId) {
      const paddedId = this.padEpisodeNumber(episodeId);
      if (!paddedId) {
        this.rundownItems = [];
        return;
      }
      this.loadingRundown = true;
      this.rundownError = null;
      try {
        const response = await axios.get(`/api/episodes/${paddedId}/rundown`);
        this.rundownItems = response.data.items;
        this.selectedItemIndex = this.rundownItems.length > 0 ? 0 : -1;
        if (this.selectedItemIndex !== -1) {
          this.loadItemContent(this.rundownItems[this.selectedItemIndex]);
        }
      } catch (error) {
        this.rundownError = `Failed to load rundown for episode ${paddedId}.`;
        this.rundownItems = [];
      } finally {
        this.loadingRundown = false;
      }
    },
    async saveAllContent() {
      const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
      this.hasUnsavedChanges = false;
      this.saving = true;
      try {
        const payload = {
          // ... construct payload
        };
        await axios.post(`/api/episodes/${paddedId}/rundown`, payload);
        this.hasUnsavedChanges = false;
      } catch (error) {
        // Handle save error
      } finally {
        this.saving = false;
      }
    },
    async handleEpisodeChange(episodeNumber, skipSessionUpdate = false) {
      const paddedNumber = this.padEpisodeNumber(episodeNumber);
      if (!paddedNumber) return;

      // Set the current episode number and update session storage
      this.currentEpisodeNumber = paddedNumber;
      if (!skipSessionUpdate) {
        sessionStorage.setItem('selectedEpisode', paddedNumber);
      }

      try {
        // Fetch new episode data, but do not reset the episode number here.
        const infoRes = await axios.get(`/api/episodes/${paddedNumber}/info`);
        const info = infoRes.data.info || {};
        this.currentAirDate = info.airdate || '';
        this.currentProductionStatus = info.status || 'draft';
        this.totalRuntime = info.total_runtime || '01:00:00';
        this.showTitle = info.title || 'Untitled';
        this.currentShowSubtitle = info.subtitle || 'No Subtitle';
      } catch (err) {
        // Clear out old data on failure
        this.currentAirDate = '';
        this.currentProductionStatus = 'draft';
        this.totalRuntime = '00:00:00';
        this.showTitle = 'Untitled';
        this.currentShowSubtitle = 'No Subtitle';
      }

      // Fetch the rundown with the correct, verified episode number
      this.fetchRundown(this.currentEpisodeNumber);
    },
    getStatusLabel(status) {
      // TODO: Implement actual logic for status label
      return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
    },
    loadItemContent(/* item */) {
      // TODO: Implement actual logic to load item content
      // For now, just log the item
    },
    dragStart(event, item, index) {
      if (!item) return;
      this.isDragging = true;
      this.draggedIndex = index;
      this.draggedItem = item;
      event.dataTransfer.setData('text/plain', index.toString());
      event.dataTransfer.effectAllowed = 'move';
    },
    
    dragEnd() {
      this.isDragging = false;
      this.draggedIndex = -1;
      this.draggedItem = null;
      this.dragOverIndex = -1;
      this.dropZonePosition = null;
    },
    
    dragOver(event, index) {
      if (!this.isDragging || index === this.draggedIndex || !this.rundownItems[index]) return;
      
      const rect = event.currentTarget.getBoundingClientRect();
      const midpoint = rect.top + rect.height / 2;
      const isAbove = event.clientY < midpoint;
      
      this.dragOverIndex = index;
      this.dropZonePosition = isAbove ? 'above' : 'below';
    },
    
    dragEnter(event, index) {
      event.preventDefault();
      event.stopPropagation();
      
      if (!this.isDragging) return;
      
      // Don't update if we're dragging over the same item
      if (index === this.draggedIndex) {
        return;
      }
      
      // Determine drop zone position
      const rect = event.currentTarget.getBoundingClientRect();
      const midpoint = rect.top + rect.height / 2;
      const isAbove = event.clientY < midpoint;
      
      this.dragOverIndex = index;
      this.dropZonePosition = isAbove ? 'above' : 'below';
    },
    
    dragLeave(event) {
      // Only clear drag state if leaving the entire rundown area
      const rundownList = document.querySelector('.rundown-list');
      if (rundownList && event.relatedTarget && !rundownList.contains(event.relatedTarget)) {
        this.dragOverIndex = -1;
        this.dropZonePosition = null;
      }
    },
    
    dragDrop(event, targetIndex) {
      if (!this.isDragging || !this.draggedItem || !this.rundownItems[targetIndex]) return;

      // Immediately clear visual drop indicators to prevent render errors
      this.dragOverIndex = -1;
      this.dropZonePosition = null;

      const sourceIndex = this.draggedIndex;
      
      // If dropped on the same item, just reset the drag state
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
    },
    getNextEpisodeNumber() {
      // Find the highest episode number in this.episodes and increment
      let maxNum = 0;
      this.episodes.forEach(e => {
        const num = parseInt(e.value, 10);
        if (!isNaN(num) && num > maxNum) maxNum = num;
      });
      return String(maxNum + 1).padStart(4, '0');
    },
    selectRundownItem(index) {
      this.selectedItemIndex = index;
    },
    
    // Missing stub methods to prevent Vue warnings
    onContentChange(/* content */) {
      this.hasUnsavedChanges = true;
    },
    
    onMetadataChange(/* metadata */) {
      this.hasUnsavedChanges = true;
    },
    
    insertAssetReference(/* assetData */) {
      // Stub implementation - could be enhanced to actually insert asset reference
      this.hasUnsavedChanges = true;
    },

    insertTemplateReference(/* templateData */) {
      // Stub implementation
      this.hasUnsavedChanges = true;
    },

    // Missing modal and action methods
    pasteFromClipboard() {
    },
    
    selectFile() {
    },
    
    pasteUrl() {
    },
    
    submitGraphic() {
    },
    
    submitFsq(data) {
      this.scriptContent += `[FSQ: ${data.quote} | ${data.source}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
      this.showFsqModal = false;
      this.hasUnsavedChanges = true;
    },
    
    submitSot(data) {
      this.scriptContent += `[SOT: ${data.filename} | ${data.duration}${data.description ? ' | ' + data.description : ''}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
      this.showSotModal = false;
      this.hasUnsavedChanges = true;
    },
    
    submitVo(data) {
      this.scriptContent += `[VO: ${data.text}${data.duration ? ' | ' + data.duration : ''}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
      this.showVoModal = false;
      this.hasUnsavedChanges = true;
    },
    
    submitNat(data) {
      this.scriptContent += `[NAT: ${data.description}${data.duration ? ' | ' + data.duration : ''}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
      this.showNatModal = false;
      this.hasUnsavedChanges = true;
    },
    
    submitPkg(data) {
      this.scriptContent += `[PKG: ${data.title} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
      this.showPkgModal = false;
      this.hasUnsavedChanges = true;
    },
    
    submitVox(data) {
      this.scriptContent += `[VOX: ${data.slug} | ${data.description} | ${data.duration}]\n`;
      this.showVoxModal = false;
      this.hasUnsavedChanges = true;
    },

    submitMus(data) {
      this.scriptContent += `[MUS: ${data.slug} | ${data.description} | ${data.duration}]\n`;
      this.showMusModal = false;
      this.hasUnsavedChanges = true;
    },

    submitLive(data) {
      this.scriptContent += `[LIVE: ${data.slug} | ${data.description} | ${data.duration}]\n`;
      this.showLiveModal = false;
      this.hasUnsavedChanges = true;
    },

    createNewItem() {
    },
    
    cancelNewItem() {
    },
    
    // Color utility methods
    hexToRgb(hex) {
      // Remove # if present
      hex = hex.replace('#', '');
      
      // Convert hex to RGB
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      
      return { r, g, b };
    },
    
    isColorDark(rgbString) {
      // If rgbString is an object with r, g, b properties
      if (typeof rgbString === 'object' && rgbString.r !== undefined) {
        const { r, g, b } = rgbString;
        // Calculate luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance < 0.5;
      }
      
      // If rgbString is a string like "rgb(r, g, b)"
      if (typeof rgbString === 'string' && rgbString.startsWith('rgb')) {
        const matches = rgbString.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (matches) {
          const r = parseInt(matches[1]);
          const g = parseInt(matches[2]);
          const b = parseInt(matches[3]);
          const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
          return luminance < 0.5;
        }
      }
      
      // Default to false if we can't parse the color
      return false;
    }
  }
}
</script>

<style scoped>
.content-editor-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.main-toolbar {
  background-color: var(--v-toolbar-bg, #FFFFFF);
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
}

.rundown-panel {
  position: relative;
  width: 40%;
  /* Remove static border-right so only dynamic border shows */
  /* border-right: 1px solid var(--v-divider-color, #E0E0E0); */
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  border: 2px solid transparent; /* fallback for dynamic border */
  border-radius: 0 !important;
  box-sizing: border-box;
  min-height: 0; /* Allow flexbox to shrink */
  overflow: hidden; /* Prevent content overflow */
}

.script-status-horizontal-bar {
  width: 100%;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: 1px;
  margin: 0;
  padding: 0;
  border-radius: 0 !important;
  border: none;
}
.status-text {
  width: 100%;
  text-align: center;
}

.rundown-header-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  background-color: var(--v-toolbar-bg, #F5F5F5);
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
  padding: 0 16px;
  height: 48px;
}

.rundown-header-title {
  font-weight: 500;
  color: var(--v-primary-text-color, #000000);
  font-size: 1.2rem;
  margin-left: 12px;
}

.status-box {
  border-radius: 4px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  font-weight: 600;
  height: 36px;
  min-width: 90px;
  justify-content: center;
  background: #888;
  color: #fff;
}

.panel-toolbar {
  display: flex;
  flex-direction: row;
  align-items: center;
  background-color: var(--v-toolbar-bg, #F5F5F5);
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
}

.toolbar-title {
  font-weight: 500;
  color: var(--v-primary-text-color, #000000);
}

.rundown-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  margin: 0;
  min-height: 0; /* Allow flexbox to shrink */
  height: auto; /* Remove any fixed height constraints */
}

.rundown-item {
  --base-row-height: 26px;
  cursor: grab;
  padding: 0;
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
  min-height: var(--base-row-height);
  height: var(--base-row-height);
  position: relative;
}

.rundown-item:active {
  cursor: grabbing;
}

.rundown-item.selected-item {
  /* Remove static selected background, let inline style handle it */
  /* background: none !important; */
  /* color: inherit !important; */
  height: calc(var(--base-row-height) * 2); /* Dynamically double the base height */
  transform: translateX(8px);
  border-left: 4px solid var(--v-accent-base, #FFC107);
}

.rundown-item.ghost-class {
  opacity: 0.5;
  background: #c8ebfb;
}

.rundown-item.dragging {
  opacity: 0.7;
  transform: rotate(2deg);
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.rundown-item:hover {
  background-color: rgba(0,0,0,0.02);
}

.rundown-item.no-hover:hover {
  background-color: unset;
}

.item-content {
  flex: 1;
  display: flex;
  align-items: stretch; /* Make children fill height */
  width: 100%;
}

.index-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px; /* Reduced from 12px to 6px (50% reduction) */
  background-color: rgba(0,0,0,0.5);
  color: white;
  flex-shrink: 0;
  min-width: 48px; /* Ensures all index cells are at least this wide */
  width: 48px;     /* Fixed width for all index cells */
  box-sizing: border-box;
}

.rundown-item.selected-item .index-container {
  background-color: rgba(0,0,0,0.65);
  color: white;
}

.rundown-item.selected-item .item-type-cell {
  background-color: rgba(255,255,255,0.25);
}

.item-index {
  font-weight: 500;
  font-size: 12px; /* Reduced by 2 points from typical 14px */
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  cursor: grab;
  flex-shrink: 0;
}

.item-type-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 65px;
  width: 65px;
  max-width: 65px;
  box-sizing: border-box;
  background-color: rgba(255,255,255,0.15);
}

.item-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center; /* Vertical centering */
  padding: 2px 6px; /* Reduced from 4px 12px to 2px 6px (50% reduction) */
  overflow: hidden;
  white-space: nowrap;
}

.item-type {
  font-size: 9px;
  font-weight: 400;
  text-transform: uppercase;
  line-height: 1.2;
  /* Remove vertical-align, use flex centering */
}

.item-slug {
  font-size: 14px;
  font-weight: 300;
  text-overflow: ellipsis;
  overflow: hidden;
  text-transform: lowercase;
}

.item-duration {
  font-size: 12px;
  font-weight: 400;
  display: flex;
  align-items: center;
  padding: 0 8px; /* Reduced from 16px to 8px (50% reduction) */
  flex-shrink: 0;
}

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0; /* Allow flexbox to shrink properly */
}

.rundown-table-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  width: 100%;
  background: rgba(0,0,0,0.08);
  font-size: 13px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
}
.rundown-table-header > div {
  text-align: center;
  padding: 8px 0;
}
.rundown-table-header .index-container {
  min-width: 48px;
  width: 48px;
  max-width: 48px;
}
.rundown-table-header .item-type-cell {
  min-width: 65px;
  width: 65px;
  max-width: 65px;
}
.rundown-table-header .item-details {
  flex: 1;
  text-align: left;
  padding-left: 12px;
}
.rundown-table-header .item-duration {
  min-width: 60px;
  width: 60px;
  max-width: 60px;
  text-align: right;
  padding-right: 16px;
}

.rundown-header-btn {
  padding: 0 2px !important;
  margin-left: 4px;
  height: 28px !important;
  width: 28px !important;
 
  opacity: 0.5;
  transform: rotate(1deg);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  background: rgba(255, 193, 7, 0.1) !important;
}

.dragging {
  opacity: 0.8;
  transform: rotate(1deg);
  z-index: 1000;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.drag-over-above::before {
  content: '';
  position: absolute;
  top: -12px;
  left: 0;
  right: 0;
  height: 12px;
  background: #FFC107;
  z-index: 1000;
}

.drag-over-below::after {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 0;
  right: 0;
  height: 12px;
  background: #FFC107;
  z-index: 1000;
}

@keyframes pulse-yellow {
  0% {
    background: rgba(255, 193, 7, 0.8);
    border-color: rgba(255, 193, 7, 0.9);
    box-shadow: 0 4px 12px rgba(255, 193, 7, 0.4);
    transform: scale(1);
  }
  100% {
    background: rgba(255, 193, 7, 1);
    border-color: rgba(255, 193, 7, 1);
    box-shadow: 0 6px 16px rgba(255, 193, 7, 0.7);
    transform: scale(1.02);
  }
}

.rundown-item {
  transition: all 0.2s ease;
}

.rundown-item:not(.ghost-class):not(.dragging) {
  transform: translateZ(0);
}
</style>

