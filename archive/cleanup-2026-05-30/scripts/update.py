#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import shutil

# Define project root and paths
PROJECT_ROOT = "/mnt/process/show-build"
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backup_md_20250709")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
CHANGELOG_PATH = os.path.join(DOCS_DIR, "20_changelog.markdown")
CONTENT_EDITOR_PATH = "disaffected-ui/src/components/ContentEditor.vue"

# Updated ContentEditor.vue template to fix ColorSelector overlap
CONTENT_EDITOR_TEMPLATE = """<template>
  <div class="content-editor-wrapper">
    <!-- Main Toolbar -->
    <v-toolbar dense flat class="main-toolbar" style="height: 128px; min-height: 128px; max-height: 128px; align-items: flex-start;">
      <v-spacer></v-spacer>
      <v-toolbar-items>
        <v-btn text @click="saveAllContent">Save</v-btn>
        <v-btn text>Publish</v-btn>
      </v-toolbar-items>
    </v-toolbar>

    <!-- Show Info Header -->
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

    <!-- Main Content Area -->
    <div class="main-content-area" style="position: relative; z-index: 1;">
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

    <!-- Color Configuration Panel -->
    <v-card class="color-selector-panel" flat style="position: sticky; top: 128px; z-index: 0;">
      <ColorSelector />
    </v-card>

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
  data() {
    return {
      showRundownPanel: true,
      rundownPanelWidth: 'wide',
      editorMode: 'script',
      selectedItemIndex: -1,
      editingItemIndex: -1,
      hasUnsavedChanges: false,
      loadingRundown: true,
      rundownError: null,
      showInfo: {},
      currentEpisodeNumber: '',
      currentAirDate: '',
      currentProductionStatus: 'draft',
      productionStatuses: [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ],
      selectedEpisode: null,
      episodes: [],
      loading: false,
      saving: false,
      isDragging: false,
      draggedIndex: -1,
      draggedItem: null,
      dragOverIndex: -1,
      dropZonePosition: null,
      itemContentBackup: {},
      autoSaveOnSwitch: true,
      autoSaveTimeout: null,
      hoveredItemIndex: -1,
      scriptContent: '',
      scratchContent: '',
      showAssetBrowserModal: false,
      showTemplateManagerModal: false,
      selectedFiles: [],
      availableAssets: [
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
      rundownItems: [
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
      showGfxModal: false,
      showFsqModal: false,
      showSotModal: false,
      showVoModal: false,
      showNatModal: false,
      showPkgModal: false,
      showVoxModal: false,
      showMusModal: false,
      showLiveModal: false,
      showNewItemModal: false,
      showRundownOptions: false,
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
      totalRuntime: '00:00:00',
      showTitle: 'Disaffected',
    }
  },
  computed: {
    styleCache() {
      const theme = this.$vuetify.theme;
      if (!theme) return {};
      const cache = {};
      const currentTheme = theme.dark ? 'dark' : 'light';
      const themeColors = theme.themes[currentTheme];
      const itemTypes = this.rundownItemTypes.map(t => t.value ? t.value.toLowerCase() : '');
      const states = ['selection', 'hover', 'draglight', 'highlight', 'dropline'];
      const allColorSources = [...new Set([...states, ...itemTypes, 'unknown'])];
      for (const source of allColorSources) {
        const colorName = getColorValue(source);
        const colorValue = themeColors[colorName];
        if (colorValue) {
          cache[source] = { backgroundColor: colorValue };
        }
      }
      return cache;
    },
    currentShowTitle() {
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
        return { title: 'Error', status: 'error' };
      }
    },
    rundownPanelWidthValue() {
      return this.rundownPanelWidth === 'narrow' ? '25%' : '40%';
    },
    rundownHeaderWidth() {
      return this.rundownPanelWidth === 'narrow' ? '25%' : '40%';
    },
    cueToolbarWidth() {
      if (!this.showRundownPanel) return '100%';
      return this.rundownPanelWidth === 'narrow' ? '75%' : '60%';
    },
    statusBarColor() {
      try {
        const status = this.currentEpisodeInfo.status;
        const color = this.themeColorMap.status[status];
        return color || 'grey';
      } catch (error) {
        return 'grey';
      }
    },
    statusBarTextColor() {
      try {
        const color = this.statusBarColor;
        return this.isDarkColor(color) ? 'white' : 'black';
      } catch (error) {
        return 'black';
      }
    },
    scriptPlaceholder() {
      return `# ${this.currentRundownItem?.slug || 'Script Content'}\n\nWrite your script content here using Markdown...\n\nUse the toolbar buttons above to insert:\n- **GFX** cues for graphics\n- **FSQ** cues for full-screen quotes  \n- **SOT** cues for video content\n\nExample:\n[GFX: opening_title.png]\nWelcome to today's show...\n\n[SOT: interview_clip.mp4 | 0:30-2:15]\nHere's what our guest had to say...`;
    },
    scratchPlaceholder() {
      return `# Brainstorming & Notes\n\nUse this space for:\n• Research notes and ideas\n• Asset planning and references  \n• Interview questions\n• Production notes\n\n💡 **Smart Features:**\n- Drag & drop assets from your file system\n- Paste URLs for automatic link cards\n- @ mentions for collaboration\n- # tags for organization\n\nTry dropping an image or video file here!`;
    },
    currentRundownItem() {
      return (this.rundownItems && this.rundownItems[this.selectedItemIndex]) || null;
    },
    titleRules() {
      return [ v => !!v || 'Title is required' ];
    },
    durationRules() {
      return [ v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS format' ];
    }
  },
  methods: {
    resolveItemStyle(item, index) {
      try {
        const itemType = item && item.type ? item.type.toLowerCase() : 'unknown';
        let style = {};
        const colorName = getColorValue(itemType);
        const resolvedColor = resolveVuetifyColor(colorName, this.$vuetify);
        if (resolvedColor) {
          style.backgroundColor = resolvedColor;
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
          style.backgroundColor = '#E0E0E0';
          style.color = '#000000';
        }
        if (this.selectedItemIndex === index) {
          const selectionColorName = getColorValue('selection');
          const selectionColor = resolveVuetifyColor(selectionColorName, this.$vuetify);
          if (selectionColor) {
            style.backgroundColor = selectionColor;
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
        } else if (this.hoveredItemIndex === index) {
           const hoverColorName = getColorValue('hover');
           const hoverColor = resolveVuetifyColor(hoverColorName, this.$vuetify);
           if (hoverColor) {
             style.boxShadow = `inset 4px 0 0 0 ${hoverColor}`;
           }
        }
        return style;
      } catch (error) {
        return {};
      }
    },
    async fetchShowInfo() {
      this.loading = true;
      try {
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
     
