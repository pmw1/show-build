<template>
  <div class="content-editor-container">
    <!-- Show Information Header -->
    <div class="show-info-header-fixed">
      <ShowInfoHeader
        :current-show-title="currentShowTitle"
        :current-episode-info="currentEpisodeInfo"
        :current-episode-number="currentEpisodeNumber"
        :current-air-date="currentAirDate"
        :current-production-status="currentProductionStatus"
        :total-runtime="totalRuntime"
        :total-runtime-label="'Total Running Time'"
        :production-statuses="productionStatuses"
        :episodes="episodes"
        @update:episode-number="currentEpisodeNumber = $event"
        @update:air-date="currentAirDate = $event"
        @update:production-status="currentProductionStatus = $event"
      />
    </div>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Cue Insertion Toolbar - Full Width, Flush with Headers -->
      <div class="cue-toolbar-container">
        <div class="cue-toolbar-row">
          <!-- Rundown Header Section (Left) -->
          <div v-if="showRundownPanel" class="rundown-header-section" :style="{ width: rundownHeaderWidth }">
            <v-card-title class="d-flex align-center pa-2 rundown-title">
              <span class="text-h6">Rundown</span>
              <v-spacer></v-spacer>
              <v-btn icon size="small" @click="rundownPanelWidth = rundownPanelWidth === 'narrow' ? 'wide' : 'narrow'">
                <v-icon>{{ rundownPanelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
              </v-btn>
              <v-btn icon size="small" @click="showRundownPanel = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
          </div>
          <!-- Removed duplicate script mode display and collapsed the space -->
        </div>
      </div>

      <div class="content-row">
        <!-- Left Panel - Rundown Manager -->
        <RundownPanel
          v-if="showRundownPanel"
          :items="rundownItems"
          :rundown-panel-width="rundownPanelWidth"
          :selected-item-index="selectedItemIndex"
          :editing-item-index="editingItemIndex"
          :loading-rundown="loadingRundown"
          @select-item="selectRundownItem"
          @edit-item="startEditingItem"
          @new-item="showNewItemModal = true"
          @import="importRundown"
          @export="exportRundown"
          @sort="sortRundown"
          @refresh="refreshRundown"
        />

        <!-- Main Editor Panel -->
        <EditorPanel
          v-model:editorMode="editorMode"
          v-model:scriptContent="scriptContent"
          v-model:scratchContent="scratchContent"
          v-model:metadata="currentItemMetadata"
          :has-unsaved-changes="hasUnsavedChanges"
          :show-rundown-panel="showRundownPanel"
          :item-types="itemTypes"
          :title-rules="titleRules"
          :duration-rules="durationRules"
          @save="saveContent"
          @show-asset-browser="showAssetBrowser = true"
          @toggle-rundown-panel="showRundownPanel = !showRundownPanel"
          @asset-drop="handleAssetDrop"
          @show-gfx-modal="showGfxModal = true"
          @show-fsq-modal="showFsqModal = true"
          @show-sot-modal="showSotModal = true"
          @show-vo-modal="showVoModal = true"
          @show-nat-modal="showNatModal = true"
          @show-pkg-modal="showPkgModal = true"
        />
      </div>
    </div>

    <!-- Modals -->
    <AssetBrowserModal
      v-model:show="showAssetBrowser"
      v-model:selected-files="selectedFiles"
      :available-assets="availableAssets"
      @upload="uploadAssets"
      @insert-asset="insertAssetReference"
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

    <NewItemModal
      v-model:show="showNewItemModal"
      v-model:valid="newItemFormValid"
      v-model:type="newItemType"
      v-model:slug="newItemSlug"
      v-model:duration="newItemDuration"
      v-model:owner="newItemOwner"
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
import ShowInfoHeader from './content-editor/ShowInfoHeader.vue';
import RundownPanel from './RundownPanel.vue';
import EditorPanel from './EditorPanel.vue';
import AssetBrowserModal from './modals/AssetBrowserModal.vue';
import GfxModal from './modals/GfxModal.vue';
import FsqModal from './modals/FsqModal.vue';
import SotModal from './modals/SotModal.vue';
import VoModal from './modals/VoModal';
import NatModal from './modals/NatModal.vue';
import PkgModal from './modals/PkgModal.vue';
import NewItemModal from './modals/NewItemModal.vue';
import { getColorValue } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';
import yaml from 'js-yaml';

// Error handling utility
const handleError = (context, error, fallback = null) => {
  console.warn(`[ContentEditor:${context}]`, error);
  return fallback;
};

export default {
  name: 'ContentEditor',
  
  // Add error capture for better debugging
  errorCaptured(err, instance, info) {
    console.error('[ContentEditor] Error captured:', {
      error: err,
      instance: instance?.$options.name || 'Unknown',
      info
    });
    
    // Return false to stop the error from propagating further
    return false;
  },

  created() {
    this.debouncedAutoSave = debounce(this.saveAllContent, 2500);
  },

  components: {
    ShowInfoHeader,
    RundownPanel,
    EditorPanel,
    AssetBrowserModal,
    GfxModal,
    FsqModal,
    SotModal,
    VoModal,
    NatModal,
    PkgModal,
    NewItemModal,
  },
  props: {
    episode: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      // Layout state
      showRundownPanel: true,
      rundownPanelWidth: 'wide', // 'narrow' or 'wide'
      
      // Editor state
      editorMode: 'script', // 'script' or 'scratch'
      selectedItemIndex: -1, // Start with no selection
      editingItemIndex: -1, // Index of item being edited (grows by 2%)
      hasUnsavedChanges: false,
      
      // Show Information
      currentShowTitle: 'Disaffected',
      currentEpisodeNumber: 'EP001',
      currentAirDate: '2025-07-15',
      currentProductionStatus: 'draft',
      productionStatuses: [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ],
      
      // Episode management - will be moved to App.vue
      selectedEpisode: 'EP001',
      episodes: [
        { title: 'EP001 - Pilot Episode', value: 'EP001' },
        { title: 'EP002 - Getting Started', value: 'EP002' },
        { title: 'EP003 - Deep Dive', value: 'EP003' }
      ],
      loading: false,
      saving: false,
      
      // Drag state
      isDragging: false,
      draggedIndex: -1,
      draggedItem: null,
      
      // Auto-save tracking
      itemContentBackup: {},
      autoSaveOnSwitch: true, // Auto-save when switching items instead of prompting
      autoSaveTimeout: null,
      
      // Content
      scriptContent: '',
      scratchContent: '',
      
      // Asset management
      showAssetBrowser: false,
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
      
      // Mock rundown data - will be replaced with props/API
      rundownItems: [
        {
          slug: 'cold open graphics',
          type: 'segment',
          duration: '0:30',
          content: '# Cold Open\n\nWelcome to the show...'
        },
        {
          slug: 'sponsor message',
          type: 'advert',
          duration: '1:00',
          content: '# Sponsor Message\n\nToday we have...'
        },
        {
          slug: 'main interview segment',
          type: 'segment',
          duration: '15:00',
          content: '# Main Interview\n\n[SOT: interview_segment.mp4]'
        },
        {
          slug: 'promo for next episode',
          type: 'promo',
          duration: '0:30',
          content: '# Next Episode Promo\n\nNext week we will...'
        },
        {
          slug: 'call to action',
          type: 'cta',
          duration: '0:45',
          content: '# Closing CTA\n\nThanks for watching...'
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
        { title: 'Advertisement', value: 'advert' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Unknown', value: 'unknown' }
      ],
      
      // Graphic attachment state
      showGraphicModal: false,
      showGfxModal: false,
      showFsqModal: false,
      showSotModal: false,
      showVoModal: false,
      showNatModal: false,
      showPkgModal: false,
      
      // Rundown management state
      showNewItemModal: false,
      showRundownOptions: false,
      loadingRundown: false,
      
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
      totalRuntime: '00:00:00'
    }
  },
   computed: {
    safeRundownItems() {
      try {
        if (!this.rundownItems) {
          return [];
        }
        
        if (!Array.isArray(this.rundownItems)) {
          console.warn('rundownItems is not an array:', this.rundownItems);
          return [];
        }
        
        return this.rundownItems.filter(item => item != null);
      } catch (error) {
        return handleError('safeRundownItems', error, []);
      }
    },

    currentContent() {
      try {
        return this.editorMode === 'script' ? this.scriptContent : this.scratchContent;
      } catch (error) {
        return handleError('currentContent', error, '');
      }
    },

    currentEpisodeInfo() {
      try {
        return `${this.currentEpisodeNumber} • ${this.currentAirDate} • ${this.getStatusLabel()}`;
      } catch (error) {
        return handleError('currentEpisodeInfo', error, 'Episode Info Unavailable');
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
    
    scriptPlaceholder() {
      return `# ${this.currentRundownItem?.slug || 'Script Content'}

Write your script content here using Markdown...

Use the toolbar buttons above to insert:
- **GFX** cues for graphics
- **FSQ** cues for full-screen quotes  
- **SOT** cues for video content

Example:
[GFX: opening_title.png]
Welcome to today's show...

[SOT: interview_clip.mp4 | 0:30-2:15]
Here's what our guest had to say...`
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
        v => !!v || 'Title is required',
        v => v.length >= 3 || 'Title must be at least 3 characters',
        v => v.length <= 100 || 'Title must be less than 100 characters'
      ];
    },
    
    durationRules() {
      return [
        v => !v || /^(\d{1,2}:)?[0-5]?\d:[0-5]\d$/.test(v) || 'Duration must be in MM:SS or HH:MM:SS format'
      ];
    },
    
    linkRules() {
      return [
        v => !v || /^https?:\/\/.+/.test(v) || 'Link must start with http:// or https://'
      ];
    },
  },
  
  watch: {
    selectedItemIndex: {
      handler(newIndex) {
        // Only load content if rundownItems is ready
        if (this.rundownItems && Array.isArray(this.rundownItems)) {
          this.loadItemContent(newIndex)
        }
      },
      immediate: true
    },
    
    editorMode() {
      this.hasUnsavedChanges = false
    }
  },
  
  mounted() {
    // Add keyboard event listeners
    document.addEventListener('keydown', this.handleKeyDown);
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', this.handleKeyboardShortcuts);
    
    // Initialize metadata for the first item after the component is mounted
    this.$nextTick(() => {
      if (this.rundownItems && this.rundownItems.length > 0) {
        this.selectedItemIndex = 0;
        this.loadCurrentItemMetadata();
      }
    });
  },

  beforeUnmount() {
    // Clean up event listeners
    document.removeEventListener('keydown', this.handleKeyDown);
    
    // Remove keyboard shortcuts
    document.removeEventListener('keydown', this.handleKeyboardShortcuts);
  },
  
  methods: {
    saveContent() {
      this.saveAllContent();
    },

    // Show Information Methods
    getStatusLabel() {
      const status = this.productionStatuses.find(s => s.value === this.currentProductionStatus);
      return status ? status.title : 'Unknown';
    },
    
    calculateTotalRuntime() {
      if (!this.rundownItems || this.rundownItems.length === 0) {
        return '00:00:00';
      }
      
      let totalSeconds = 0;
      this.rundownItems.forEach(item => {
        if (item.duration) {
          const formatted = this.formatDuration(item.duration);
          const parts = formatted.split(':');
          if (parts.length === 3) {
            totalSeconds += parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
          }
        }
      });
      
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    },
    
    getModeIcon() {
      switch (this.editorMode) {
        case 'script': return 'mdi-script-text';
        case 'scratch': return 'mdi-pencil';
        case 'metadata': return 'mdi-cog';
        default: return 'mdi-text';
      }
    },
    
    formatDuration(duration) {
      // Convert various duration formats to HH:MM:SS
      if (!duration) return '00:00:00';
      
      // If already in HH:MM:SS format, return as is
      if (/^\d{2}:\d{2}:\d{2}$/.test(duration)) {
        return duration;
      }
      
      // If in MM:SS format, add hours
      if (/^\d{1,2}:\d{2}$/.test(duration)) {
        return `00:${duration.padStart(5, '0')}`;
      }
      
      // If in M:SS format, pad and add hours
      if (/^\d:\d{2}$/.test(duration)) {
        return `00:0${duration}`;
      }
      
      // If just seconds (like "30"), convert to HH:MM:SS
      if (/^\d+$/.test(duration)) {
        const totalSeconds = parseInt(duration);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      }
      
      // Try to parse decimal formats like "0:30" or "1:00"
      if (duration.includes(':')) {
        const parts = duration.split(':');
        if (parts.length === 2) {
          const minutes = parseInt(parts[0]) || 0;
          const seconds = parseInt(parts[1]) || 0;
          return `00:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
      }
      
      // Default fallback
      return '00:00:00';
    },
    
    handleKeyDown(event) {
      // Handle Alt+G for GFX modal
      if (event.altKey && event.key.toLowerCase() === 'g') {
        event.preventDefault();
        this.showGfxModal = true;
      }
      // Handle Alt+Q for FSQ modal
      else if (event.altKey && event.key.toLowerCase() === 'q') {
        event.preventDefault();
        this.showFsqModal = true;
      }
      // Handle Alt+S for SOT modal
      else if (event.altKey && event.key.toLowerCase() === 's') {
        event.preventDefault();
        this.showSotModal = true;
      }
      // Handle Alt+V for VO modal
      else if (event.altKey && event.key.toLowerCase() === 'v') {
        event.preventDefault();
        this.showVoModal = true;
      }
      // Handle Alt+N for NAT modal
      else if (event.altKey && event.key.toLowerCase() === 'n') {
        event.preventDefault();
        this.showNatModal = true;
      }
      // Handle Alt+P for PKG modal
      else if (event.altKey && event.key.toLowerCase() === 'p') {
        event.preventDefault();
        this.showPkgModal = true;
      }
      // Handle Ctrl+S for save
      else if (event.ctrlKey && event.key.toLowerCase() === 's') {
        event.preventDefault();
        this.saveAllContent();
      }
    },
    
    // Keyboard shortcuts handler
    handleKeyboardShortcuts(event) {
      // Ctrl+Shift+N: New rundown item
      if (event.ctrlKey && event.shiftKey && event.key === 'N') {
        event.preventDefault();
        this.showNewItemModal = true;
      }
      
      // Ctrl+Shift+R: Refresh rundown
      if (event.ctrlKey && event.shiftKey && event.key === 'R') {
        event.preventDefault();
        this.refreshRundown();
      }
      
      // Ctrl+Shift+E: Export rundown
      if (event.ctrlKey && event.shiftKey && event.key === 'E') {
        event.preventDefault();
        this.exportRundown();
      }
    },
    
    selectRundownItem(index) {
      // Safety check for valid index
      if (!this.rundownItems || !Array.isArray(this.rundownItems) || index < 0 || index >= this.rundownItems.length) {
        console.warn('Invalid rundown item index:', index);
        return;
      }
      
      if (this.hasUnsavedChanges) {
        // Auto-save or prompt user
        const shouldSave = this.autoSaveOnSwitch || confirm('You have unsaved changes. Save before switching items?');
        if (shouldSave) {
          this.saveContent()
        } else {
          // Discard changes by reloading content
          this.hasUnsavedChanges = false
        }
      }
      this.selectedItemIndex = index
      // Clear editing state when selecting different item
      if (this.editingItemIndex !== index) {
        this.editingItemIndex = -1
      }
      
      // Load metadata for the selected item
      this.loadCurrentItemMetadata();
    },
    
    startEditingItem(index) {
      this.selectedItemIndex = index
      this.editingItemIndex = index
      // Set selection highlight color
      const selectionColor = getColorValue('selection');
      document.documentElement.style.setProperty('--selection-color', `rgb(var(--v-theme-${selectionColor}))`);
    },
    
    // Native HTML5 drag-and-drop handlers (temporarily disabled to fix parentNode errors)
    /*
    handleDragStart(index, event) {
      try {
        this.isDragging = true;
        this.draggedIndex = index;
        this.draggedItem = this.rundownItems[index];
        
        // Set drag effect
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', index.toString());
        
        // Add visual feedback
        const dragLightColor = getColorValue('draglight');
        const highlightColor = getColorValue('highlight');
        const droplineColor = getColorValue('dropline');

        document.documentElement.style.setProperty('--highlight-color', `rgb(var(--v-theme-${highlightColor}))`);
        document.documentElement.style.setProperty('--draglight-color', `rgb(var(--v-theme-${dragLightColor}))`);
        document.documentElement.style.setProperty('--dropline-color', `rgb(var(--v-theme-${droplineColor}))`);
      } catch (error) {
        console.warn('Error in handleDragStart:', error);
        this.isDragging = false;
      }
    },
    
    handleDragEnd() {
      try {
        this.isDragging = false;
        this.draggedIndex = -1;
        this.draggedItem = null;
        
        // Clear drag colors
        document.documentElement.style.removeProperty('--highlight-color');
        document.documentElement.style.removeProperty('--draglight-color');
        document.documentElement.style.removeProperty('--dropline-color');
      } catch (error) {
        console.warn('Error in handleDragEnd:', error);
      }
    },
    
    handleDragOver(index, event) {
      if (this.isDragging && this.draggedIndex !== index) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
      }
    },
    
    handleDrop(dropIndex, event) {
      try {
        event.preventDefault();
        
        if (!this.isDragging || this.draggedIndex === -1 || this.draggedIndex === dropIndex) {
          return;
        }
        
        // Reorder the items array
        const draggedItem = this.rundownItems.splice(this.draggedIndex, 1)[0];
        this.rundownItems.splice(dropIndex, 0, draggedItem);
        
        // Update selection if needed
        if (this.selectedItemIndex === this.draggedIndex) {
          this.selectedItemIndex = dropIndex;
        } else if (this.selectedItemIndex > this.draggedIndex && this.selectedItemIndex <= dropIndex) {
          this.selectedItemIndex--;
        } else if (this.selectedItemIndex < this.draggedIndex && this.selectedItemIndex >= dropIndex) {
          this.selectedItemIndex++;
        }
        
        // Mark as having unsaved changes
        this.hasUnsavedChanges = true;
        
        console.log('Drag reorder:', { from: this.draggedIndex, to: dropIndex });
      } catch (error) {
        console.warn('Error in handleDrop:', error);
      }
    },
    */
    
    // Transition group animation handlers (temporarily disabled to fix parentNode errors)
    /*
    beforeEnter(el) {
      el.style.opacity = 0;
      el.style.transform = 'translateX(-30px)';
    },
    
    enter(el, done) {
      el.style.transition = 'all 0.3s ease';
      setTimeout(() => {
        el.style.opacity = 1;
        el.style.transform = 'translateX(0)';
      }, 10);
      setTimeout(done, 300);
    },
    
    leave(el, done) {
      el.style.transition = 'all 0.3s ease';
      el.style.opacity = 0;
      el.style.transform = 'translateX(30px)';
      setTimeout(done, 300);
    },
    */
    
    // Legacy drag methods for compatibility (can be removed later)
    dragStart() {
      console.warn('Legacy dragStart called - using new HTML5 drag implementation');
    },
    
    dragEnd() {
      console.warn('Legacy dragEnd called - using new HTML5 drag implementation');
    },
    
    handleDragChange(event) {
      console.warn('Legacy handleDragChange called - using new HTML5 drag implementation', event);
    },
    
    handleEpisodeChange(newEpisode) {
      console.log('Episode changed to:', newEpisode);
      // Here you would load rundown items for the selected episode
      this.loadEpisodeRundown(newEpisode);
    },
    
    loadEpisodeRundown(episode) {
      this.loading = true;
      // Mock loading - replace with real API call
      setTimeout(() => {
        console.log('Loading rundown for episode:', episode);
        this.loading = false;
      }, 500);
    },
    
    saveAllContent() {
      this.saving = true;
      // Mock save - replace with real API call
      setTimeout(() => {
        console.log('Saving all content for episode:', this.selectedEpisode);
        this.hasUnsavedChanges = false;
        this.saving = false;
      }, 1000);
    },
    
    loadItemContent(index) {
      if (!this.rundownItems || !Array.isArray(this.rundownItems) || index < 0 || index >= this.rundownItems.length) {
        this.scriptContent = ''
        this.scratchContent = ''
        this.hasUnsavedChanges = false
        return
      }
      
      const item = this.rundownItems[index]
      if (item) {
        this.scriptContent = item.content || ''
        this.scratchContent = item.scratchContent || ''
        this.hasUnsavedChanges = false
      }
    },
    
    onContentChange() {
      this.debouncedAutoSave();
    },

    loadCurrentItemMetadata() {
      try {
        const item = this.currentRundownItem;
        if (!item) {
          // Reset or set to default if no item is selected
          this.currentItemMetadata = {
            title: '',
            type: 'segment',
            slug: '',
            duration: '00:00:00',
            description: '',
            guests: '',
            tags: '',
            sponsor: '',
            campaign: '',
            segment_number: 0,
            live_status: 'off-air'
          };
          this.customMetadataYaml = '';
          return;
        }

        // Map rundown item data to metadata object
        this.currentItemMetadata = {
          title: item.slug || '', // Assuming slug is the primary title for now
          type: item.type || 'unknown',
          slug: item.slug || '',
          duration: this.formatDuration(item.duration || '0'),
          description: item.description || '', // Assuming description exists
          guests: item.guests || '',
          tags: Array.isArray(item.tags) ? item.tags.join(', ') : (item.tags || ''),
          sponsor: item.sponsor || '',
          campaign: item.campaign || '',
          segment_number: this.selectedItemIndex + 1,
          live_status: item.live_status || 'off-air'
        };

        // Handle custom metadata if it exists
        if (item.metadata_yaml) {
          this.customMetadataYaml = item.metadata_yaml;
          // Optionally, merge YAML into the main metadata object
          try {
            const customMeta = yaml.load(item.metadata_yaml);
            Object.assign(this.currentItemMetadata, customMeta);
          } catch (e) {
            console.warn('[ContentEditor] Failed to parse custom metadata YAML:', e);
          }
        } else {
          this.customMetadataYaml = '';
        }
      } catch (error) {
        handleError('loadCurrentItemMetadata', error);
      }
    },

    onMetadataChange() {
      // Mark as having unsaved changes when metadata is modified
      this.hasUnsavedChanges = true;
      this.debouncedAutoSave();
      
      // Update the rundown item with new metadata
      if (this.selectedItemIndex >= 0 && this.rundownItems[this.selectedItemIndex]) {
        // Update item content
        this.rundownItems[this.selectedItemIndex].content = this.currentContent;
      }
    },

    onCustomMetadataChange() {
      try {
        this.currentItemMetadata.custom = yaml.load(this.customMetadataYaml);
        this.onMetadataChange();
      } catch (e) {
        console.warn("Invalid YAML in custom metadata:", e.message);
        // Optionally, provide user feedback about the invalid YAML
      }
    },
  }
};
</script>

<style scoped>
.content-editor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden; /* Prevent full-page scrollbars */
}

/* Fix ShowInfoHeader height to prevent layout bounce */
.show-info-header-fixed {
  min-height: 64px; /* Reduced height for more compact header */
  padding-top: 8px;
  padding-bottom: 8px;
  width: 100%;
  /* Adjust 80px as needed to match your header's normal height */
  overflow: hidden;
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

/* Use :deep() to ensure padding overrides apply to Vuetify v-text-field and v-select internals */
:deep(.show-info-header-fixed .v-input input),
:deep(.show-info-header-fixed .v-input textarea),
:deep(.show-info-header-fixed .v-field__input),
:deep(.show-info-header-fixed .v-field__slot),
:deep(.show-info-header-fixed .v-field__overlay),
:deep(.show-info-header-fixed .v-field__field),
:deep(.show-info-header-fixed input),
:deep(.show-info-header-fixed textarea) {
  padding-left: 12px !important;
  padding-right: 12px !important;
  padding-top: 4px !important;
  padding-bottom: 4px !important;
  font-size: 0.95rem !important;
  color: rgb(var(--v-theme-on-surface), 1) !important;
  background: transparent !important;
  height: auto !important;
  min-height: 32px !important;
  line-height: 1.3 !important;
  box-sizing: border-box;
}

.show-info-header-fixed .v-label {
  font-size: 0.80rem !important; /* Smaller label font */
}

/* Reduce width and spacing for compact look */
.show-info-header-fixed .v-input,
.show-info-header-fixed .v-field {
  min-width: 260px !important;
  max-width: 700px !important;
  margin-left: 4px !important;
  margin-right: 4px !important;
  width: 100% !important;
}

:deep(.show-info-header-fixed .showinfo-field) {
  width: 100% !important;
}

:deep(.show-info-header-fixed .v-col) {
  flex: 1 1 0 !important;
  min-width: 260px !important;
  max-width: 700px !important;
}

/* Reduce select dropdown font/height */
.show-info-header-fixed .v-select__selection {
  font-size: 0.85rem !important;
  min-height: 24px !important;
}

.main-content {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  overflow: hidden;
}

.content-row {
  display: flex;
  flex-direction: row;
  flex-grow: 1;
  overflow: hidden; /* Each panel will have its own scrollbar */
}

/* --- Lighter Toolbar Background Override --- */
.lighter-toolbar-bg {
  background: #f5f5f5 !important;
  /* fallback for light mode */
  background-color: rgba(255,255,255,0.85) !important;
  /* for extra lightness and transparency */
  box-shadow: none !important;
}

/* Editor Textarea Styles - Fix fade/gradient issues */
.editor-textarea textarea,
.editor-textarea .v-field__input,
.editor-textarea .v-input__control {
  opacity: 1 !important;
  background: transparent !important;
  background-image: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  padding-top: 20px !important; /* Add padding to prevent text from being hidden behind headers */
}

.editor-textarea .v-field {
  background: transparent !important;
  background-image: none !important;
}

.editor-textarea .v-field__field {
  opacity: 1 !important;
  background: transparent !important;
  padding-top: 20px !important; /* Ensure the field has proper padding */
}

/* Remove any gradient overlays from Vuetify */
.editor-textarea .v-field__overlay,
.editor-textarea .v-field__loader {
  display: none !important;
}

/* Ensure text is always fully visible */
.editor-textarea textarea {
  color: rgb(var(--v-theme-on-surface)) !important;
  opacity: 1 !important;
  padding-top: 20px !important; /* Critical: Add top padding to prevent text clipping */
  box-sizing: border-box !important;
}

/* Fix any potential clipping or overflow issues */
.editor-content {
  overflow: visible !important;
  padding-top: 10px; /* Add some breathing room */
}

.editor-content .fill-height {
  height: 100% !important;
  min-height: 400px;
}

/* Ensure the main editor panel has proper spacing */
.editor-panel .v-card-text {
  padding-top: 15px !important;
  padding-left: 15px !important;
  padding-right: 15px !important;
}

/* Fix text visibility issues specifically for the main textarea */
.editor-panel .v-textarea .v-field__input {
  padding-top: 25px !important;
  line-height: 1.5 !important;
}

/* Ensure proper scrolling without content being hidden */
.editor-panel .v-card-text .fill-height {
  overflow-y: auto;
  max-height: calc(100vh - 200px); /* Account for headers */
}

/* Add more styling here as needed */
</style>

