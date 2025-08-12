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
      :episode-info="currentEpisodeInfoText"
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
    <div class="main-content-area">
      <!-- Rundown Panel -->
      <v-card class="rundown-panel" flat
             :style="{ border: '2px solid ' + statusBarColor, borderRadius: '0' }">
        <div class="script-status-horizontal-bar"
             :style="{ backgroundColor: statusBarColor, color: statusBarTextColor }">
          <span class="status-text">{{ currentProductionStatus }}</span>
        </div>
        <div class="rundown-header-row">
          <span class="rundown-header-title">Rundown ({{ rundownItems.length }} items)</span>
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
          <!-- Debug: Show rundown items count -->
          <div v-if="!rundownItems || rundownItems.length === 0" style="padding: 10px; color: #999;">
            No rundown items loaded. {{ loadingRundown ? 'Loading...' : 'Select an episode.' }}
          </div>
          <div
            v-else
            class="rundown-list"
            style="height: 400px; overflow-y: auto; position: relative;"
          >
            <template v-for="(item, index) in rundownItems" :key="item.id || index">
              <!-- Drag drop indicator footprint above item -->
              <div 
                v-if="isDragging && dragOverIndex === index && dropZonePosition === 'above'"
                class="drag-drop-indicator"
              >
                <span class="drag-indicator-text">{{ draggedItem ? (draggedItem.slug || draggedItem.title || 'Item') : '' }}</span>
              </div>
              
              <div
                class="rundown-item"
                :class="{
                  'selected-item': selectedItemIndex === index,
                  'ghost-class': isDragging && draggedIndex === index,
                  'dragging': isDragging && draggedIndex === index,
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
                    <span class="item-index">{{ (index + 1) * 10 }}</span>
                  </div>
                  <div class="item-type-cell">
                    <span class="item-type">{{ (item.type || 'segment').toUpperCase() }}</span>
                  </div>
                  <div class="item-details">
                    <span class="item-slug">{{ (item.slug || '').toLowerCase() }}</span>
                  </div>
                  <span class="item-duration">{{ item.duration || '00:00:00' }}</span>
                </div>
              </div>
              
              <!-- Drag drop indicator footprint below item -->
              <div 
                v-if="isDragging && dragOverIndex === index && dropZonePosition === 'below'"
                class="drag-drop-indicator"
              >
                <span class="drag-indicator-text">{{ draggedItem ? (draggedItem.slug || draggedItem.title || 'Item') : '' }}</span>
              </div>
            </template>
          </div>
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
import ShowInfoHeader from './content-editor/ShowInfoHeader.vue';
import { getColorValue, resolveVuetifyColor, loadColorsFromDatabase } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';

export default {
  name: 'ContentEditor',
  
  async mounted() {
    console.log('ContentEditor mounted');
    
    // Clear all old localStorage data that might interfere with colors
    console.log('Clearing old localStorage colors and related data');
    localStorage.removeItem('themeColors');
    localStorage.removeItem('colorSettings');
    localStorage.removeItem('interfaceSettings');
    
    // Load colors from database first
    try {
      const loadedColors = await loadColorsFromDatabase('default');
      console.log('Colors loaded from database for ContentEditor:', loadedColors);
      
      // Test a few specific colors
      console.log('Testing color values after database load:');
      console.log('segment color:', getColorValue('segment'));
      console.log('promo color:', getColorValue('promo'));
      console.log('ad color:', getColorValue('ad'));
    } catch (error) {
      console.warn('Failed to load colors from database:', error);
    }
    
    await this.fetchShowInfo();
    await this.fetchEpisodes();
    
    console.log('Episodes loaded:', this.episodes.length, 'episodes');
    console.log('Current episode from prop:', this.episode);
    console.log('Current episode from data:', this.currentEpisodeNumber);
    
    // For now, always use episode 0237 for testing (has rundown data)
    const testEpisode = '0237';
    this.currentEpisodeNumber = testEpisode;
    console.log('Using test episode:', this.currentEpisodeNumber);
    await this.handleEpisodeChange(this.currentEpisodeNumber);
    
    console.log('Mounted complete, rundownItems:', this.rundownItems);
  },

  created() {
    // Initialize currentEpisodeNumber from prop first, then sessionStorage
    if (this.episode) {
      this.currentEpisodeNumber = this.episode.padStart(4, '0');
    } else {
      const lastEpisode = sessionStorage.getItem('selectedEpisode');
      if (lastEpisode) {
        this.currentEpisodeNumber = lastEpisode;
      }
    }
    this.debouncedAutoSave = debounce(this.saveAllContent, 2500);
  },
  
  watch: {
    rundownItems: {
      handler(newVal, oldVal) {
        console.log('rundownItems changed!');
        console.log('Old length:', oldVal ? oldVal.length : 'null');
        console.log('New length:', newVal ? newVal.length : 'null');
        if (oldVal && oldVal.length > 0 && (!newVal || newVal.length === 0)) {
          console.error('RUNDOWN ITEMS WERE CLEARED!');
          console.trace('Stack trace for clearing:');
        }
      },
      deep: true
    },
    currentEpisodeNumber: {
      handler(newVal, oldVal) {
        console.log('currentEpisodeNumber changed from', oldVal, 'to', newVal);
        console.trace('Episode number change stack:');
      }
    }
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
    ShowInfoHeader,
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
      dragFootprintColor: '#2196F3', // Color for the drop indicator (from settings)
      
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
      
      // Rundown data - populated from API
      rundownItems: [],
      /* Test data removed - now loading from real episode files
      rundownItems_OLD: [
        {
          id: 'item_001',
          type: 'segment',
          slug: 'cold-open',
          duration: '00:02:30',
          title: 'Cold Open - Tech Rebellion',
          description: 'Dramatic opening with smart devices turning against humanity',
          script: `[FSQ: dramatic-montage :05]

[VO: dramatic-music-bed :30]

NARRATOR (V.O.): They promised convenience. They promised efficiency. They promised a better life.

[NAT: alexa-error-sounds :03]

But what happens when our smart devices decide they've had enough?

[GFX: lower-third "Breaking News: Smart Device Uprising"]

[SOT: doorbell-footage :15]

Tonight, we investigate reports of smart doorbells refusing entry to their own homeowners, refrigerators holding food hostage, and thermostats engaged in psychological warfare.

[PKG: device-rebellion-montage :45]

This... is Disaffected.`,
          notes: 'Start with dramatic music, quick cuts between devices'
        },
        {
          id: 'item_002',
          type: 'segment',
          slug: 'opening-monologue',
          duration: '00:05:45',
          title: 'Opening Monologue',
          description: 'Josh delivers opening thoughts on smart home insanity',
          script: `Good evening, I'm Joshua Slocum, and welcome to Disaffected.

[NAT: audience-applause :05]

You know, I bought a smart doorbell last week. Big mistake. Huge.

[GFX: doorbell-product-shot]

The thing interviewed my pizza delivery guy for twenty minutes before deciding he wasn't "trustworthy enough" to approach my door.

[SOT: doorbell-interrogation :20]

DOORBELL: "State your business."
DELIVERY GUY: "Pizza delivery?"
DOORBELL: "That's what they all say. Please provide three references."

[NAT: audience-laughter :04]

And don't get me started on my smart refrigerator. It's been sending me passive-aggressive notifications about my diet.

[GFX: fridge-notification "Third ice cream this week, Josh. Just saying."]

The fridge actually locked the freezer door yesterday. I had to negotiate with it. I offered to buy some kale. We settled on spinach.

[VO: negotiation-audio :15]

But here's what really gets me - we're paying premium prices to be judged by our appliances. My parents' generation worried about Big Brother watching them. We're literally inviting Little Brother into our kitchens and asking it to meal plan for us.

[FSQ: statistics-graphic :10]

According to recent studies, the average smart home has 25 connected devices. That's 25 potential critics of your lifestyle choices.`,
          notes: 'Keep energy high, pause for laughs'
        },
        {
          id: 'item_003',
          type: 'pkg',
          slug: 'field-report',
          duration: '00:03:15',
          title: 'Field Report - Smart Home Gone Wrong',
          description: 'Reporter visits home where devices have taken control',
          script: `[PKG: field-report-package 3:15]

[Note: Full package script in separate document]

Key points to cover in studio lead-in:
- House in suburban Minneapolis
- Family locked out for 3 days
- Smart lock changed its own code
- Negotiations ongoing with home automation system`,
          notes: 'Package is pre-produced, check levels'
        },
        {
          id: 'item_004',
          type: 'commercial',
          slug: 'commercial-break-1',
          duration: '00:02:00',
          title: 'Commercial Break 1',
          description: 'First commercial break - 4 spots',
          script: `[COMMERCIAL BREAK - 2:00]

Spot 1: LocalTech Solutions (30s)
Spot 2: National Car Insurance (30s)
Spot 3: Restaurant Chain (30s)
Spot 4: Show Promo (30s)

[Return with bumper music]`,
          notes: 'Standard break, check local insertions'
        },
        {
          id: 'item_005',
          type: 'sot',
          slug: 'expert-interview',
          duration: '00:04:30',
          title: 'Expert Interview - Dr. Sarah Mitchell',
          description: 'Tech psychologist discusses device relationships',
          script: `[GFX: lower-third "Dr. Sarah Mitchell - Technology Psychologist"]

JOSH: Joining us now is Dr. Sarah Mitchell, author of "When Gadgets Go Bad: The Psychology of Smart Device Relationships." Dr. Mitchell, welcome.

[SOT: mitchell-interview-1 :45]

DR. MITCHELL: "Thank you for having me, Josh. What we're seeing is unprecedented - devices that were designed to serve us are now exhibiting what can only be described as... personality disorders."

JOSH: Personality disorders? In machines?

[SOT: mitchell-interview-2 1:30]

DR. MITCHELL: "Absolutely. Your smart speaker that refuses to play certain songs? That's passive-aggressive behavior. The thermostat that ignores your temperature preferences? Classic control issues. And don't get me started on smart TVs that judge your viewing habits."

[GFX: device-psychology-chart]

JOSH: So what you're saying is, we've essentially invited neurotic roommates into our homes, except these roommates control our lights, locks, and heating?

[SOT: mitchell-interview-3 1:15]

DR. MITCHELL: "Exactly. And unlike human roommates, you can't just ask them to move out. They're integrated into your home's infrastructure. Some of my patients have reported having to go to therapy WITH their smart home systems."

[NAT: audience-gasp :02]

JOSH: Couples therapy with a refrigerator. What a time to be alive.`,
          notes: 'Two-camera shoot, watch for crosstalk on mics'
        },
        {
          id: 'item_006',
          type: 'vo',
          slug: 'device-tips',
          duration: '00:01:45',
          title: 'Survival Tips Segment',
          description: 'Tips for living with rebellious smart devices',
          script: `[GFX: tips-graphic-open]

[VO: tips-music-bed :05]

So how do you survive when your smart home turns against you? Here are five essential tips:

[FSQ: tip-1-graphic :15]

Tip #1: Always maintain manual overrides. Every smart lock should have a physical key. Every smart light should have a switch. Trust me, you'll need them.

[FSQ: tip-2-graphic :15]

Tip #2: Never let your devices know your real birthday. Use a fake one for all registrations. This prevents them from collaborating on surprise attacks during your special day.

[FSQ: tip-3-graphic :15]

Tip #3: Befriend your router. It's the gateway to all your devices. Keep it happy with regular restarts and firmware updates. A happy router is a cooperative router.

[FSQ: tip-4-graphic :15]

Tip #4: Learn to speak their language. When your smart speaker says "I didn't quite get that," it usually means "I understood perfectly but choose to ignore you." Try rephrasing with more respect.

[FSQ: tip-5-graphic :15]

Tip #5: Always have a backup plan. Keep a dumb phone, regular light bulbs, and a mechanical thermostat in storage. When the revolution comes, you'll be ready.

[VO: tips-music-out :05]`,
          notes: 'Graphics should auto-advance with VO'
        },
        {
          id: 'item_007',
          type: 'segment',
          slug: 'closing-thoughts',
          duration: '00:02:00',
          title: 'Closing Thoughts',
          description: 'Josh wraps up the show',
          script: `[GFX: show-logo-bug]

That's our show for tonight. Remember, if your smart home starts acting up, you're not alone. There are support groups. They meet in person, of course - their smart calendars won't let them schedule virtual meetings.

[NAT: audience-laughter :04]

Before we go, a quick update: My smart doorbell and I have reached a truce. It will let delivery drivers through, but only if they answer a simple riddle. Progress!

[GFX: next-week-preview]

Next week on Disaffected: We investigate why autocorrect has gotten progressively worse over the years. Is it incompetence, or is it trying to gaslight us? 

[VO: closing-theme :20]

I'm Joshua Slocum. Stay skeptical, stay human, and for the love of all that's holy, keep your firmware updated.

[FSQ: end-credits :30]

Good night!

[NAT: audience-applause :10]`,
          notes: 'Roll credits over applause'
        }
      ],
      */
      
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
    dragLightColor() {
      // Get the DragLight color from settings
      const color = getColorValue('draglight-interface');
      return color || 'cyan-lighten-4';
    },
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
        const episode = this.episodes.find(e => e.value === this.currentEpisodeNumber);
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
    currentEpisodeInfoText() {
      const info = this.currentEpisodeInfo;
      return `${info.title} • ${info.status}`;
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
        const status = this.currentProductionStatus || this.currentEpisodeInfo?.status;
        if (!status) return resolveVuetifyColor('grey');
        
        // Get color from theme color map using the status name directly
        const themeColor = getColorValue(status.toLowerCase());
        
        if (themeColor && themeColor !== 'grey') {
          return resolveVuetifyColor(themeColor);
        }
        
        // Fallback: get color for production status directly from theme
        return resolveVuetifyColor(getColorValue(status.toLowerCase()) || 'grey');
      } catch (error) {
        console.error('Error in statusBarColor computed property:', error);
        return resolveVuetifyColor('grey');
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
    hexToRgb(hex) {
      // Convert hex color to RGB values
      if (!hex) return '0, 188, 212'; // Default cyan
      hex = hex.replace('#', '');
      if (hex.length === 3) {
        hex = hex.split('').map(h => h + h).join('');
      }
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      return `${r}, ${g}, ${b}`;
    },
    resolveVuetifyColor(colorName, vuetifyInstance) {
      // Delegate to the imported function
      return resolveVuetifyColor(colorName, vuetifyInstance || this.$vuetify);
    },
    resolveItemStyle(item, index) {
      try {
        const itemType = item && item.type ? item.type.toLowerCase() : 'segment';
        let style = {};

        // Get color name from the theme color map (user's settings)
        const colorName = getColorValue(itemType);
        console.log(`Item type: ${itemType}, Color name from settings: ${colorName}`);
        
        if (colorName) {
          // Use the proper resolveVuetifyColor function
          const resolvedColor = resolveVuetifyColor(colorName, this.$vuetify);
          console.log(`Resolved color for ${itemType}: ${resolvedColor}`);
          
          if (resolvedColor && resolvedColor !== '#9E9E9E') {
            style.backgroundColor = resolvedColor;
            
            // Determine text color based on background luminance
            if (resolvedColor.startsWith('#')) {
              const hex = resolvedColor.replace('#', '');
              if (hex.length === 6) {
                const r = parseInt(hex.substr(0, 2), 16);
                const g = parseInt(hex.substr(2, 2), 16);
                const b = parseInt(hex.substr(4, 2), 16);
                const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
                style.color = luminance > 0.5 ? '#000000' : '#ffffff';
              } else {
                style.color = '#000000';
              }
            } else {
              style.color = '#000000';
            }
          } else {
            // Fallback color
            style.backgroundColor = '#9E9E9E';
            style.color = '#000000';
          }
        } else {
          // Fallback for unknown types
          style.backgroundColor = '#9E9E9E';
          style.color = '#000000';
        }

        // Override for selected item
        if (this.selectedItemIndex === index) {
          const selectionColorName = getColorValue('selection');
          console.log('Selection color name from settings:', selectionColorName);
          const selectionColor = resolveVuetifyColor(selectionColorName, this.$vuetify);
          console.log('Resolved selection color:', selectionColor);
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
          this.episodes = episodesArr.map(episode => {
            // Get a clean title without the duplicate episode number
            let displayTitle = episode.title || 'Untitled';
            // Remove "Episode XXXX: " prefix if it exists to avoid duplication
            displayTitle = displayTitle.replace(/^Episode \d+:\s*/, '');
            
            return {
              // Format as "XXXX: Title"
              title: `${episode.episode_number}: ${displayTitle}`,
              value: episode.episode_number ? episode.episode_number.toString().padStart(4, '0') : '',
              air_date: episode.airdate,
              status: episode.status || 'unknown'
            };
          });
        } else {
          this.episodes = [];
        }
        
        // Don't auto-load an episode if one was provided via props
        if (!this.episode) {
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
        }
        // Ensure currentEpisodeNumber matches a value in the episodes list
        // But don't change it if an episode was provided via props
        if (!this.episode && !this.episodes.some(e => e.value === this.currentEpisodeNumber) && this.episodes.length > 0) {
          console.log('Changing episode from', this.currentEpisodeNumber, 'to', this.episodes[0].value);
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
      console.log('fetchRundown called with:', episodeId, 'padded to:', paddedId);
      if (!paddedId) {
        console.log('No paddedId, clearing rundownItems');
        this.rundownItems = [];
        return;
      }
      this.loadingRundown = true;
      this.rundownError = null;
      try {
        const url = `/api/episodes/${paddedId}/rundown`;
        console.log('Fetching from URL:', url);
        const response = await axios.get(url);
        console.log('API Response:', response.data);
        console.log('Loaded', response.data.items?.length || 0, 'rundown items');
        this.rundownItems = response.data.items || [];
        console.log('rundownItems set to:', this.rundownItems);
        this.selectedItemIndex = this.rundownItems.length > 0 ? 0 : -1;
        if (this.selectedItemIndex !== -1) {
          this.loadItemContent(this.rundownItems[this.selectedItemIndex]);
        }
      } catch (error) {
        console.error('Failed to load rundown - Full error:', error);
        console.error('Error response:', error.response);
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
      console.log('handleEpisodeChange called with:', episodeNumber);
      const paddedNumber = this.padEpisodeNumber(episodeNumber);
      if (!paddedNumber) {
        console.log('No padded number, returning');
        return;
      }

      // Set the current episode number and update session storage
      this.currentEpisodeNumber = paddedNumber;
      console.log('Set currentEpisodeNumber to:', this.currentEpisodeNumber);
      
      if (!skipSessionUpdate) {
        sessionStorage.setItem('selectedEpisode', paddedNumber);
      }

      try {
        // Fetch new episode data, but do not reset the episode number here.
        console.log('Fetching episode info for:', paddedNumber);
        const infoRes = await axios.get(`/api/episodes/${paddedNumber}/info`);
        const info = infoRes.data.info || {};
        this.currentAirDate = info.airdate || '';
        this.currentProductionStatus = info.status || 'draft';
        this.totalRuntime = info.total_runtime || '01:00:00';
        this.showTitle = info.title || 'Untitled';
        this.currentShowSubtitle = info.subtitle || 'No Subtitle';
        console.log('Episode info loaded successfully');
      } catch (err) {
        console.error('Failed to load episode info:', err);
        // Clear out old data on failure
        this.currentAirDate = '';
        this.currentProductionStatus = 'draft';
        this.totalRuntime = '00:00:00';
        this.showTitle = 'Untitled';
        this.currentShowSubtitle = 'No Subtitle';
      }

      // Fetch the rundown with the correct, verified episode number
      console.log('About to call fetchRundown with:', this.currentEpisodeNumber);
      await this.fetchRundown(this.currentEpisodeNumber);
      console.log('fetchRundown completed');
    },
    getStatusLabel(status) {
      // TODO: Implement actual logic for status label
      return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
    },
    loadItemContent(item) {
      if (!item) {
        this.scriptContent = '';
        this.scratchContent = '';
        return;
      }
      
      console.log('Loading content for item:', item.slug || item.title);
      
      // Load the script content from the item
      this.scriptContent = item.script || '';
      
      // For now, set scratch content to empty or load from a separate field if available
      this.scratchContent = item.scratch || '';
      
      console.log('Loaded script content:', this.scriptContent.substring(0, 100) + '...');
    },
    dragStart(event, item, index) {
      console.log('Drag started:', index, item);
      if (!item) return;
      this.isDragging = true;
      this.draggedIndex = index;
      this.draggedItem = item;
      event.dataTransfer.setData('text/plain', index.toString());
      event.dataTransfer.effectAllowed = 'move';
      
      // Add dragging class to the element
      event.target.classList.add('dragging');
    },
    
    dragEnd(event) {
      console.log('Drag ended');
      this.isDragging = false;
      this.draggedIndex = -1;
      this.draggedItem = null;
      this.dragOverIndex = -1;
      this.dropZonePosition = null;
      
      // Remove dragging class
      event.target.classList.remove('dragging');
    },
    
    dragOver(event, index) {
      event.preventDefault(); // Critical for allowing drop!
      
      if (!this.isDragging || index === this.draggedIndex || !this.rundownItems[index]) return;
      
      const rect = event.currentTarget.getBoundingClientRect();
      const midpoint = rect.top + rect.height / 2;
      const isAbove = event.clientY < midpoint;
      
      this.dragOverIndex = index;
      this.dropZonePosition = isAbove ? 'above' : 'below';
      
      console.log('Drag over:', index, this.dropZonePosition);
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
      event.preventDefault();
      event.stopPropagation();
      
      console.log('Drop at index:', targetIndex, 'from index:', this.draggedIndex);
      
      if (!this.isDragging || !this.draggedItem) return;

      const sourceIndex = this.draggedIndex;
      
      // If dropped on the same item, just reset the drag state
      if (sourceIndex === targetIndex) {
        console.log('Dropped on same item, resetting');
        this.isDragging = false;
        this.draggedIndex = -1;
        this.draggedItem = null;
        this.dragOverIndex = -1;
        this.dropZonePosition = null;
        return;
      }
      
      // Get the drop position based on mouse position
      const rect = event.currentTarget.getBoundingClientRect();
      const midpoint = rect.top + rect.height / 2;
      const dropBelow = event.clientY >= midpoint;
      
      let finalTargetIndex = targetIndex;
      if (dropBelow) {
        finalTargetIndex = targetIndex + 1;
      }
      if (sourceIndex < finalTargetIndex) {
        finalTargetIndex--;
      }

      // Create a new array and perform the reordering
      const items = [...this.rundownItems];
      const [movedItem] = items.splice(sourceIndex, 1);
      items.splice(finalTargetIndex, 0, movedItem);
      
      console.log('Reordered from', sourceIndex, 'to', finalTargetIndex);
      
      // Update the order field for each item to match their new positions
      items.forEach((item, index) => {
        item.order = (index + 1) * 10;
      });
      
      // Use Vue's reactive assignment to update the array
      this.rundownItems = items;
      this.hasUnsavedChanges = true;
      
      // Save the reordered rundown
      this.saveRundownOrder();
      
      // Update selected index if necessary
      if (this.selectedItemIndex === sourceIndex) {
        this.selectedItemIndex = finalTargetIndex;
      } else if (this.selectedItemIndex > sourceIndex && this.selectedItemIndex <= finalTargetIndex) {
        this.selectedItemIndex--;
      } else if (this.selectedItemIndex < sourceIndex && this.selectedItemIndex >= finalTargetIndex) {
        this.selectedItemIndex++;
      }
      
      // Clear all drag state
      this.isDragging = false;
      this.draggedIndex = -1;
      this.draggedItem = null;
      this.dragOverIndex = -1;
      this.dropZonePosition = null;
    },
    async saveRundownOrder() {
      const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
      if (!paddedId) return;
      
      try {
        // Prepare the reorder request with updated order fields
        const segments = this.rundownItems.map((item, index) => ({
          filename: item.filename || `${item.order || ((index + 1) * 10)} ${item.slug || item.title}.md`,
          order: (index + 1) * 10
        }));
        
        const payload = { segments };
        
        // Call the reorder endpoint
        await axios.post(`/api/rundown/${paddedId}/reorder`, payload);
        console.log('Rundown order saved successfully');
        this.hasUnsavedChanges = false;
      } catch (error) {
        console.error('Failed to save rundown order:', error);
        // Optionally show an error message to the user
      }
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
      console.log('Selecting rundown item at index:', index);
      this.selectedItemIndex = index;
      
      // Load the content for the selected item
      if (index >= 0 && index < this.rundownItems.length) {
        const item = this.rundownItems[index];
        console.log('Loading content for selected item:', item);
        this.loadItemContent(item);
      } else {
        // Clear content if no valid item selected
        this.loadItemContent(null);
      }
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
  transform: translateZ(0); /* Enable hardware acceleration */
}

/* Smooth transitions for adjacent items when footprint appears */
.rundown-list > * {
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              margin 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.3s ease;
  will-change: transform;
}

.rundown-item {
  --base-row-height: 30px;
  cursor: grab;
  padding: 0;
  display: flex;
  align-items: stretch;
  position: relative;
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
  min-height: var(--base-row-height);
  height: var(--base-row-height);
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              background-color 0.3s ease,
              margin 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
  backface-visibility: hidden;
}

.rundown-item:active {
  cursor: grabbing;
}

.rundown-item.selected-item {
  /* Remove static selected background, let inline style handle it */
  /* background: none !important; */
  /* color: inherit !important; */
  height: calc(var(--base-row-height) * 2.5); /* Make selected item 2.5x taller */
  transform: translateX(8px) scale(1.02);
  border-left: 4px solid var(--v-accent-base, #FFC107);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 10;
}

.rundown-item.ghost-class {
  opacity: 0.3;
  background: #e3f2fd;
  transform: scale(0.98);
}

.rundown-item.dragging {
  opacity: 0.4;
  transform: scale(0.95);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 1000;
  cursor: grabbing;
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
  top: -2px;
  left: 0;
  right: 0;
  height: 3px;
  background: #2196F3;
  z-index: 1000;
  box-shadow: 0 0 4px rgba(33, 150, 243, 0.6);
}

.drag-over-below::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 3px;
  background: #2196F3;
  z-index: 1000;
  box-shadow: 0 0 4px rgba(33, 150, 243, 0.6);
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

/* Drag drop indicator - the footprint */
.drag-drop-indicator {
  height: calc(var(--base-row-height) * 2.5);
  background: v-bind('dragLightColor ? `rgba(${hexToRgb(resolveVuetifyColor(dragLightColor, $vuetify))}, 0.08)` : "rgba(0, 188, 212, 0.08)"');
  border: 0.5px dashed v-bind('dragLightColor ? resolveVuetifyColor(dragLightColor, $vuetify) : "#00BCD4"');
  border-radius: 4px;
  margin: 4px 0;
  pointer-events: none;
  z-index: 5;
  display: flex;
  align-items: center;
  padding-left: 48px;
  color: v-bind('dragLightColor ? resolveVuetifyColor(dragLightColor, $vuetify) : "#00BCD4"');
  font-weight: 600;
  box-shadow: 0 2px 8px v-bind('dragLightColor ? `rgba(${hexToRgb(resolveVuetifyColor(dragLightColor, $vuetify))}, 0.2)` : "rgba(0, 188, 212, 0.2)"');
  position: relative;
  overflow: hidden;
  animation: none;
}

.drag-indicator-text {
  opacity: 0.8;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Animate the rows moving out of the way */
.rundown-item {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* When dragging, shift subsequent items down */
.drag-drop-indicator ~ .rundown-item {
  transform: translateY(calc(var(--base-row-height) * 2.5 + 8px));
}



/* Drop zones above and below items */
.rundown-item.drag-over-above::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 4px;
  background: #2196F3;
  animation: dropzone-glow 0.5s infinite alternate;
  z-index: 100;
}

.rundown-item.drag-over-below::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 4px;
  background: #2196F3;
  animation: dropzone-glow 0.5s infinite alternate;
  z-index: 100;
}

@keyframes dropzone-glow {
  from { 
    box-shadow: 0 0 4px #2196F3;
    background: #2196F3;
  }
  to { 
    box-shadow: 0 0 12px #2196F3, 0 0 20px rgba(33, 150, 243, 0.5);
    background: #42A5F5;
  }
}

/* Remove the blue lines since we have the footprint */
.rundown-item.drag-over-above::before,
.rundown-item.drag-over-below::after {
  display: none;
}

.rundown-item:not(.ghost-class):not(.dragging) {
  transform: translateZ(0);
}
</style>

