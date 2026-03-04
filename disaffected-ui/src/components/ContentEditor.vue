<template>
  <div class="content-editor-wrapper">
    <!-- Scrollable Content Area (contains header + columns) -->
    <div class="scrollable-content-wrapper">
      <!-- Show Info Header (full width, scrolls off) -->
      <ShowInfoHeader
        :title="currentShowTitle"
        :episode-info="currentEpisodeInfoText"
        :episode-number="currentEpisodeNumber"
        :episode-asset-id="currentEpisodeAssetId"
        :slug="currentEpisodeSlug"
        :episode-title="currentEpisodeTitle"
        :subtitle="currentEpisodeSubtitle"
        :guest="currentEpisodeGuest"
        :description="currentEpisodeDescription"
        :is-dummy="currentEpisodeIsDummy"
        :air-date="currentAirDate"
        :air-time="currentAirTime"
        :air-timezone="currentAirTimezone"
        :show-timezone="currentShowTimezone"
        :production-status="currentProductionStatus"
        :duration="duration"
        :production-statuses="productionStatuses"
        :save-state="episodeSaveState"
        :show-metadata-panel="showMetadataPanel"
        :is-xtts-configured="isXttsConfigured"
        :is-reading-script="isReadingScript"
        :thumbnails="episodeThumbnails"
        :confirmed-thumbnail-url="confirmedThumbnailUrl"
        :taken-source-url="takenSourceUrl"
        @update:airDate="handleAirDateChange"
        @update:airTime="handleAirTimeChange"
        @update:airTimezone="handleAirTimezoneChange"
        @take-thumbnail="handleTakeThumbnail"
        @update:productionStatus="handleProductionStatusChange"
        @update:title="handleTitleChange"
        @update:slug="handleSlugChange"
        @update:episodeTitle="handleEpisodeTitleChange"
        @update:subtitle="handleSubtitleChange"
        @update:guest="handleGuestChange"
        @update:description="handleDescriptionChange"
        @save-all="saveEverything"
        @toggle-metadata-panel="showMetadataPanel = !showMetadataPanel"
        @toggle-script-reading="handleToggleScriptReading"
        @request-new-episode-assetid="handleRequestNewEpisodeAssetID"
        @show-assetid-info="handleShowAssetIDInfo"
        @generate-script="handleGenerateScript"
      />

      <!-- Main Content Area -->
      <div class="main-content-area">
      <!-- Rundown Panel -->
      <RundownPanel
        ref="rundownPanelRef"
        v-if="showRundownPanel"
        :episode="currentEpisode"
        :items="rundownItems"
        :selected-item-index="selectedItemIndex"
        :llm-state="llmState"
        :loading="loadingRundown"
        :panel-width="rundownPanelWidth"
        :panel-height="sidePanelHeight"
        :collapse-break-regions="interfaceSettings.collapseBreakRegions"
        :save-state="episodeSaveState"
        @select-item="selectRundownItem"
        @new-item="handleNewItemClick"
        @delete-selected="deleteSelectedItem"
        @delete-item="handleDeleteItem"
        @delete-region="handleDeleteRegion"
        @rundown-cleared="handleRundownCleared"
        @toggle-width="toggleRundownWidth"
        @close="showRundownPanel = false"
        @reorder-items="handleRundownReorder"
        @sync-order="syncRundownOrder"
        @create-region="handleCreateRegion"
        @select-region="handleRegionSelection"
        @save="saveEverything"
        @refresh-rundown="handleRefreshRundown"
        @restore-revision="handleRestoreRevision"
      />

      <!-- Reopen Rundown Button (when panel is closed) -->
      <div v-else class="rundown-tab-controls-closed">
        <v-btn
          icon
          size="small"
          @click="showRundownPanel = true"
          class="rundown-tab-btn"
        >
          <v-icon>mdi-arrow-expand-horizontal</v-icon>
          <v-tooltip activator="parent" location="right">
            Show Rundown Panel
          </v-tooltip>
        </v-btn>
      </div>

      <!-- Editor Panel (scrollable center column) -->
      <div class="editor-panel">
        <EditorPanel
          ref="editorPanel"
          :item="currentRundownItem"
          :current-item-metadata="currentItemMetadata"
          :current-episode="currentEpisodeNumber"
          :script-content="scriptContent"
          @update:script-content="updateScriptContent"
          v-model:scratch-content="scratchContent"
          v-model:editor-mode="editorMode"
          @update:editor-mode="editorMode = $event"
          :has-unsaved-changes="hasUnsavedChanges"
          :has-unsaved-rundown-changes="hasUnsavedRundownChanges"
          :save-state="episodeSaveState"
          :show-rundown-panel="showRundownPanel"
          :show-metadata-panel="showMetadataPanel"
          :is-segment-locked="segmentLockState?.isLocked?.value && !segmentLockState?.isMyLock?.value"
          :lock-info="segmentLockState?.lockInfo?.value || { lockedBy: '', lockedAt: null }"
          @save="() => saveCurrentItem(true)"
          @save-all="saveEverything"
          @save-current="() => saveCurrentItem(true)"
          @toggle-rundown-panel="showRundownPanel = !showRundownPanel"
          @toggle-metadata-panel="showMetadataPanel = !showMetadataPanel"
          @show-asset-browser-modal="showAssetBrowserModal = true"
          @show-template-manager-modal="showTemplateManagerModal = true"
          @show-img-modal="handleShowImgModal"
          @show-gfx-modal="handleShowGfxModal"
          @show-fsq-modal="handleShowFsqModal"
          @show-sot-modal="handleShowSotModal"
          @edit-sot-cue="handleShowSotModal"
          @reupload-sot-cue="handleReuploadSotCue"
          @sot-job-complete="handleSotJobComplete"
          @edit-fsq-cue="handleEditFsqCue"
          @edit-gfx-cue="handleEditGfxCue"
          @edit-img-cue="handleEditImgCue"
          @edit-dir-cue="handleEditDirCue"
          @show-vo-modal="handleShowVoModal"
          @show-nat-modal="handleShowNatModal"
          @show-rif-modal="handleShowRifModal"
          @show-pkg-modal="handleShowPkgModal"
          @show-dir-modal="handleShowDirModal"
          @show-bump-modal="handleShowBumpModal"
          @show-sting-modal="handleShowStingModal"
          @show-vox-modal="handleShowVoxModal"
          @show-mus-modal="handleShowMusModal"
          @show-live-modal="handleShowLiveModal"
          @metadata-change="onMetadataChange"
          @update:slug="handleSlugChangeFromEditor"
          @update:duration="handleDurationChangeFromEditor"
          @duration-calculated="handleDurationCalculated"
          @insert-cue="handleInsertCue"
        />
      </div>

      <!-- Metadata Panel -->
      <MetadataPanel
        v-if="showMetadataPanel"
        ref="metadataPanel"
        :item="currentRundownItem"
        :panel-width="metadataPanelWidth"
        :panel-height="sidePanelHeight"
        :item-types="rundownItemTypes"
        :episode-number="currentEpisodeNumber"
        :media-list-loading="generatingMediaList"
        :host-script-loading="generatingHostScript"
        :save-state="episodeSaveState"
        :version-history="versionHistory"
        :loading-versions="loadingVersions"
        @update-field="handleMetadataFieldUpdate"
        @toggle-width="toggleMetadataWidth"
        @close="showMetadataPanel = false"
        @reset-fields="resetMetadataFields"
        @open-wpm-tool="showWpmTool = true"
        @generate-script="handleGenerateScript"
        @generate-host-script="handleGenerateScript"
        @generate-media-list="handleGenerateMediaList"
        @generate-prompter-files="handleGeneratePrompterFiles"
        @restore-version="restoreToVersion"
      />
      
      <!-- Reopen Metadata Buttons (when panel is closed) - Tab style -->
      <div v-else-if="currentRundownItem" class="metadata-tab-controls-closed">
        <v-btn
          icon
          size="small"
          @click="showMetadataPanel = true"
          class="metadata-tab-btn"
        >
          <v-icon>mdi-arrow-expand-horizontal</v-icon>
          <v-tooltip activator="parent" location="left">
            Show Metadata Panel
          </v-tooltip>
        </v-btn>
      </div>
    </div>
    </div><!-- End scrollable-content-wrapper -->

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

    <FsqModal
      :show="showFsqModal"
      @update:show="handleFsqModalClose"
      :current-episode="currentEpisodeNumber"
      :speaker-wpm="currentSpeakerWpm"
      :edit-mode="!!editingFsqCueData"
      :initial-data="editingFsqCueData"
      @submit="submitFsq"
    />
    <SotModal
      v-model:show="showSotModal"
      :episode-number="currentEpisodeNumber"
      :segment-name="currentItemMetadata?.title || currentItemMetadata?.slug || 'Segment'"
      :edit-mode="!!editingSotCueData"
      :initial-data="editingSotCueData"
      @submit="submitSot"
      @submit-multiple="submitMultipleSots"
    />
    <VoModal
      v-model:show="showVoModal"
      :episode="currentEpisodeNumber"
      @submit="submitVo"
    />
    <NatModal v-model:show="showNatModal" @submit="submitNat" />
    <RifModal v-model:show="showRifModal" @submit="submitRif" />
    <PkgModal v-model:show="showPkgModal" @submit="submitPkg" />
    <DirModal v-model:show="showDirModal" :editing-cue-data="editingDirCueData" @submit="submitDir" />
    <BumpModal v-model:show="showBumpModal" @submit="submitBump" />
    <StingModal v-model:show="showStingModal" @submit="submitSting" />
    <VoxModal v-model:show="showVoxModal" @submit="submitVox" />
    <MusModal v-model:show="showMusModal" @submit="submitMus" />
    <LiveModal v-model:show="showLiveModal" @submit="submitLive" />

    <NewItemModal
      v-if="showNewItemModal"
      v-model:show="showNewItemModal"
      :loading="creatingNewItem"
      :rundownItemTypes="rundownItemTypes"
      @submit="createNewItem"
      @open-library-picker="handleOpenLibraryPicker"
    />

    <ContentLibraryPickerModal
      v-if="showLibraryPickerModal"
      v-model:show="showLibraryPickerModal"
      :item-type="libraryPickerItemType"
      :episode-number="paddedEpisodeNumber"
      @select="handleLibraryItemSelected"
      @create-new="handleCreateNewLibraryItem"
    />

    <NewGFXModal
      v-model:show="showNewGFXModal"
      @submit="createGFXItem"
    />
    
    <NewSOTModal
      v-model:show="showNewSOTModal"
      @submit="createSOTItem"
    />
    
    <DeleteCueModal
      v-model:show="showDeleteCueModal"
      :cue-data="selectedCueData"
      :start-line="selectedCueStartLine"
      :end-line="selectedCueEndLine"
      @delete="deleteCue"
      @cancel="cancelDeleteCue"
    />

    <ImgCueModal
      v-model:show="showImgCueModal"
      :current-episode="currentEpisodeNumber"
      @submit="handleImgCueSubmit"
    />

    <RequireEpisodeModal
      v-model:show="showEpisodeModal"
      :action-description="episodeModalAction"
      @episode-selected="handleEpisodeSelectedInContentEditor"
      @cancelled="handleModalCancelled"
    />

    <!-- WPM Measurement Tool -->
    <WPMMeasurementTool
      v-model="showWpmTool"
      @speaker-saved="handleSpeakerSaved"
      @show-message="showMessage"
    />

    <!-- Loading Overlay -->
    <v-overlay
      v-model="loadingRundown"
      persistent
      class="content-editor-loading-overlay"
      :scrim="false"
      :contained="false"
    >
      <div class="loading-content">
        <v-progress-circular
          indeterminate
          size="64"
          width="6"
          color="primary"
        ></v-progress-circular>
        <div class="loading-text" v-if="currentEpisodeNumber">Loading {{ currentEpisodeNumber }}</div>
        <div class="loading-subtitle" v-if="currentEpisodeTitle">{{ currentEpisodeTitle }}</div>
        <div class="loading-text" v-else>Loading Episode Content...</div>
      </div>
    </v-overlay>

    <!-- Script Generation Overlay -->
    <v-overlay
      v-model="generatingHostScript"
      persistent
      class="script-generation-overlay"
      :scrim="true"
      scrim-color="rgba(0,0,0,0.7)"
    >
      <div class="script-gen-content">
        <v-progress-circular
          indeterminate
          size="80"
          width="8"
          color="success"
        ></v-progress-circular>
        <div class="script-gen-title">🎬 Generating Host Script</div>
        <div class="script-gen-episode">Episode {{ currentEpisodeNumber }}</div>
        <div class="script-gen-status">{{ scriptGenStatus }}</div>
        <div class="script-gen-steps">
          <div
            v-for="(step, idx) in scriptGenSteps"
            :key="idx"
            class="script-gen-step"
            :class="{ 'step-active': idx === scriptGenCurrentStep, 'step-done': idx < scriptGenCurrentStep }"
          >
            <v-icon v-if="idx < scriptGenCurrentStep" color="success" size="small">mdi-check-circle</v-icon>
            <v-progress-circular v-else-if="idx === scriptGenCurrentStep" indeterminate size="16" width="2" color="success"></v-progress-circular>
            <v-icon v-else color="grey" size="small">mdi-circle-outline</v-icon>
            <span>{{ step }}</span>
          </div>
        </div>
      </div>
    </v-overlay>

    <!-- Media List Generation Overlay -->
    <v-overlay
      v-model="generatingMediaList"
      persistent
      class="script-generation-overlay"
      :scrim="true"
      scrim-color="rgba(0,0,0,0.7)"
    >
      <div class="script-gen-content media-list-theme">
        <v-progress-circular
          indeterminate
          size="80"
          width="8"
          color="primary"
        ></v-progress-circular>
        <div class="script-gen-title">📋 Generating Media List</div>
        <div class="script-gen-episode media-list-ep">Episode {{ currentEpisodeNumber }}</div>
        <div class="script-gen-status">{{ mediaListStatus }}</div>
        <div class="script-gen-steps">
          <div
            v-for="(step, idx) in mediaListSteps"
            :key="idx"
            class="script-gen-step"
            :class="{ 'step-active-blue': idx === mediaListCurrentStep, 'step-done-blue': idx < mediaListCurrentStep }"
          >
            <v-icon v-if="idx < mediaListCurrentStep" color="primary" size="small">mdi-check-circle</v-icon>
            <v-progress-circular v-else-if="idx === mediaListCurrentStep" indeterminate size="16" width="2" color="primary"></v-progress-circular>
            <v-icon v-else color="grey" size="small">mdi-circle-outline</v-icon>
            <span>{{ step }}</span>
          </div>
        </div>
      </div>
    </v-overlay>
  </div>
</template>

<script>
import axios from 'axios';
// import { API_BASE_URL } from '@/config.js'; // Temporarily remove to simplify
import EditorPanel from './content-editor/EditorPanel.vue';
import RundownPanel from './content-editor/RundownPanel.vue';
import MetadataPanel from './content-editor/MetadataPanel.vue';
import AssetBrowserModal from './modals/AssetBrowserModal.vue';
import TemplateManagerModal from './modals/TemplateManagerModal.vue';
import GfxModal from './modals/GfxModal.vue';
import FsqModal from './modals/FsqModal.vue';
import SotModal from './modals/SotModal.vue';
import VoModal from './modals/VoModal.vue';
import NatModal from './modals/NatModal.vue';
import RifModal from './modals/RifModal.vue';
import PkgModal from './modals/PkgModal.vue';
import DirModal from './modals/DirModal.vue';
import BumpModal from './modals/BumpModal.vue';
import StingModal from './modals/StingModal.vue';
import VoxModal from './modals/VoxModal.vue';
import MusModal from './modals/MusModal.vue';
import LiveModal from './modals/LiveModal.vue';
import NewItemModal from './modals/NewItemModal.vue';
import ContentLibraryPickerModal from './modals/ContentLibraryPickerModal.vue';
import NewGFXModal from './modals/NewGFXModal.vue';
import NewSOTModal from './modals/NewSOTModal.vue';
import DeleteCueModal from './content-editor/modals/DeleteCueModal.vue';
import ImgCueModal from './content-editor/modals/ImgCueModal.vue';
import RequireEpisodeModal from './modals/RequireEpisodeModal.vue';
import ShowInfoHeader from './content-editor/ShowInfoHeader.vue';
import WPMMeasurementTool from './tools/WPMMeasurementTool.vue';
import { getColorValue, resolveVuetifyColor, loadColorsFromDatabase } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';
import { getItemTypesForDropdown } from '../config/itemTypes';
import { notifyUserStandard, NOTIFICATION_COLORS } from '../composables/useStandardNotification';
import { useLLM } from '../composables/useLLM';
import { useLLMState } from '../composables/useLLMState';
import { useSOTProcessing } from '../composables/useSOTProcessing';
import { useRequireEpisode } from '../composables/useRequireEpisode';
import { useSegmentLock } from '../composables/useSegmentLock';

export default {
  name: 'ContentEditor',
  components: {
    EditorPanel,
    RundownPanel,
    // eslint-disable-next-line vue/no-unused-components
    MetadataPanel,
    AssetBrowserModal,
    TemplateManagerModal,
    GfxModal,
    FsqModal,
    SotModal,
    VoModal,
    NatModal,
    RifModal,
    DirModal,
    BumpModal,
    StingModal,
    LiveModal,
    MusModal,
    VoxModal,
    PkgModal,
    ShowInfoHeader,
    NewItemModal,
    ContentLibraryPickerModal,
    NewGFXModal,
    NewSOTModal,
    DeleteCueModal,
    ImgCueModal,
    RequireEpisodeModal,
    WPMMeasurementTool
  },

  setup() {
    // Episode requirement system
    const {
      showEpisodeModal,
      episodeModalAction,
      handleEpisodeSelected,
      handleModalCancelled
    } = useRequireEpisode();

    // Segment locking system
    const segmentLock = useSegmentLock();

    return {
      showEpisodeModal,
      episodeModalAction,
      handleEpisodeSelected,
      handleModalCancelled,
      // Segment lock state and methods
      segmentLockState: segmentLock
    };
  },

  async mounted() {
    console.log('ContentEditor mounted');
    
    // Load item types from single source of truth
    this.rundownItemTypes = getItemTypesForDropdown();
    console.log('Loaded item types from config:', this.rundownItemTypes.length, 'types');
    
    // Add keyboard event listener for delete functionality
    document.addEventListener('keydown', this.handleKeydown);
    
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

    // Load interface settings
    await this.loadInterfaceSettings();

    await this.fetchShowInfo();
    await this.fetchEpisodes();
    
    console.log('Episodes loaded:', this.episodes.length, 'episodes');
    console.log('Current episode from prop:', this.episode);
    console.log('Current episode from data:', this.currentEpisodeNumber);
    console.log('Mounted complete, episode loading handled by fetchEpisodes()');

    // Watch for episode changes from App.vue toolbar selector via sessionStorage
    this.checkEpisodeInterval = setInterval(() => {
      const currentEpisode = sessionStorage.getItem('currentEpisode');
      if (currentEpisode && currentEpisode !== this.currentEpisodeNumber) {
        console.log(`Episode changed from ${this.currentEpisodeNumber} to ${currentEpisode} - reloading...`);
        this.handleEpisodeChange(currentEpisode);
      }
    }, 500);

    // CRITICAL: Add beforeunload handler to catch browser refresh/close
    this.handleBeforeUnload = (e) => {
      // Flush any pending changes synchronously (best effort)
      if (this.$refs.editorPanel?.flushPendingChanges) {
        this.$refs.editorPanel.flushPendingChanges();
      }
      // Warn user if there are unsaved changes
      if (this.hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };
    window.addEventListener('beforeunload', this.handleBeforeUnload);

    // Side panel height: track available space below ShowInfoHeader
    this.$nextTick(() => {
      this._scrollWrapper = this.$el.querySelector('.scrollable-content-wrapper');
      this._headerEl = this.$el.querySelector('.show-info-header');
      if (this._scrollWrapper) {
        this._scrollWrapper.addEventListener('scroll', this.updateSidePanelHeight, { passive: true });
        window.addEventListener('resize', this.updateSidePanelHeight, { passive: true });
        this.updateSidePanelHeight();
      }
    });
  },

  beforeUnmount() {
    // CRITICAL: Flush any pending edits before component unmounts
    if (this.$refs.editorPanel?.flushPendingChanges) {
      console.log('💾 Flushing pending changes before unmount...');
      this.$refs.editorPanel.flushPendingChanges();
    }
    // Clean up beforeunload handler
    if (this.handleBeforeUnload) {
      window.removeEventListener('beforeunload', this.handleBeforeUnload);
    }
    // Clean up keyboard event listener
    document.removeEventListener('keydown', this.handleKeydown);
    // Clean up side panel height listeners
    if (this._scrollWrapper) {
      this._scrollWrapper.removeEventListener('scroll', this.updateSidePanelHeight);
      window.removeEventListener('resize', this.updateSidePanelHeight);
    }
    // Clean up episode check interval
    if (this.checkEpisodeInterval) {
      clearInterval(this.checkEpisodeInterval);
    }
    // Release any held segment locks
    if (this.segmentLockState) {
      this.segmentLockState.releaseLock();
    }
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
    // Real-time autosave with 500ms debounce (aggressive)
    // Wrapper to capture the paragraph being edited when debounce starts
    this.debouncedAutoSave = debounce(() => {
      // Use the captured paragraph index from when typing started
      this.saveCurrentItem(false, this.paragraphBeingEdited);
    }, 500);

    // Debounced capture for undo stack (300ms to group rapid typing)
    this.debouncedCaptureUndoState = debounce(() => {
      this.captureUndoState();
    }, 300);
  },

  watch: {
    // Real-time autosave on content changes
    rawMarkdownContent: {
      handler(newVal, oldVal) {
        if (newVal !== oldVal && this.selectedItemIndex >= 0) {
          // CRITICAL FIX: Skip autosave when loading item content from the database.
          // Without this guard, switching items triggers: loadItemContent -> rawMarkdownContent changes
          // -> watcher fires -> autosave queued -> saves loaded content back unnecessarily.
          // Combined with the (now removed) duplicate detection, this caused permanent data loss.
          if (this.isLoadingItemContent) {
            console.log('📝 Content changed during item load - skipping autosave');
            return;
          }
          console.log('📝 Content changed, triggering autosave...');
          this.hasUnsavedChanges = true;
          // Capture which paragraph is being edited NOW, before debounce delay
          const editorPanel = this.$refs.editorPanel;
          this.paragraphBeingEdited = editorPanel?.focusedParagraphIndex ?? editorPanel?.activelyEditingSegment ?? null;
          console.log('📝 Captured paragraph being edited:', this.paragraphBeingEdited);
          this.debouncedAutoSave();

          // Debounced capture for undo stack (groups rapid typing)
          this.debouncedCaptureUndoState();
        }
      }
    },

    scratchContent: {
      handler(newVal, oldVal) {
        if (newVal !== oldVal && this.selectedItemIndex >= 0) {
          console.log('📝 Scratch changed, triggering autosave...');
          this.hasUnsavedChanges = true;
          // Capture which paragraph is being edited NOW
          const editorPanel = this.$refs.editorPanel;
          this.paragraphBeingEdited = editorPanel?.focusedParagraphIndex ?? editorPanel?.activelyEditingSegment ?? null;
          this.debouncedAutoSave();

          // Debounced capture for undo stack (groups rapid typing)
          this.debouncedCaptureUndoState();
        }
      }
    },

    showNewItemModal: {
      handler(newVal, oldVal) {
        console.log('showNewItemModal changed from', oldVal, 'to', newVal);
        if (newVal) {
          console.log('Modal is opening, rundownItemTypes:', this.rundownItemTypes);
        }
      },
      immediate: true
    },
    
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

    // Clean up placeholder when SOT modal closes without submitting
    showSotModal(newVal, oldVal) {
      if (oldVal === true && newVal === false) {
        // Modal was closed
        console.log('🚪 SOT modal closed - checking for placeholder cleanup');
        // Clean up placeholder after a short delay to allow submitSot to finish if it was triggered
        setTimeout(() => {
          this.cleanupCuePlaceholder();
        }, 100);
      }
    }
    // Removed currentEpisodeNumber watcher to prevent race conditions
    // Episode changes should only be handled explicitly via handleEpisodeChange
  },
  props: {
    episode: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      // Universal LLM state management
      llmState: useLLMState(),

      // SOT processing tracking
      sotProcessing: useSOTProcessing(),

      // Layout state
      showRundownPanel: true,
      rundownPanelWidth: 'wide', // 'narrow' or 'wide'
      showMetadataPanel: true,
      metadataPanelWidth: 'wide', // 'narrow' or 'wide'
      sidePanelHeight: null, // Dynamic height for side panels (px), null = 100vh fallback

      // Interface settings - will be loaded from database
      interfaceSettings: {
        collapseBreakRegions: true  // Default to true, will be overridden by database settings
      },

      // Editor state
      editorMode: 'script', // 'script', 'scratch', or 'code'
      selectedItemIndex: -1, // Start with no selection
      selectedRegion: null, // Currently selected region for item placement
      editingItemIndex: -1, // Index of item being edited (grows by 2%)
      generatingItemIndex: -1, // DEPRECATED - Use llmState instead
      hasUnsavedChanges: false,
      paragraphBeingEdited: null, // Track which paragraph was being edited when autosave debounce started
      loadingRundown: true, // Start with loading overlay visible until episode loads
      loadingEpisode: false, // Prevent duplicate episode loading
      isLoadingItemContent: false, // Guard to prevent autosave during item content load
      rundownError: null,
      checkEpisodeInterval: null, // Interval for checking episode changes from toolbar
      
      // Show Information
      showInfo: {},
      currentEpisodeNumber: '', // This will be updated from session
      currentEpisodeSlug: '',
      currentEpisodeTitle: '',
      currentEpisodeSubtitle: '',
      currentEpisodeGuest: '',
      currentEpisodeDescription: '',
      currentEpisodeIsDummy: false,
      currentAirDate: '',
      currentAirTime: '',
      currentAirTimezone: 'America/New_York',
      currentShowTimezone: 'America/New_York', // Show-level timezone setting
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
      episodeThumbnails: [], // Available poster/thumbnail images for current episode
      confirmedThumbnailUrl: null, // Protected thumbnail URL from database
      takenSourceUrl: null, // Original source URL that was taken/confirmed
      loading: false,
      saving: false,
      generatingMediaList: false, // Loading state for media list generation
      generatingHostScript: false, // Loading state for host script generation

      // Script generation progress
      scriptGenStatus: 'Initializing...', // Current status message for script generation
      scriptGenCurrentStep: 0, // Current step index
      scriptGenSteps: [
        'Collecting rundown items',
        'Processing media assets',
        'Building HTML content',
        'Generating PDF',
        'Finalizing'
      ],

      // Media list generation progress
      mediaListStatus: 'Initializing...',
      mediaListCurrentStep: 0,
      mediaListSteps: [
        'Scanning rundown items',
        'Extracting media cues',
        'Checking media URLs',
        'Building media list',
        'Generating HTML'
      ],

      // Auto-save tracking
      itemContentBackup: {},
      autoSaveOnSwitch: true, // Auto-save when switching items instead of prompting
      autoSaveTimeout: null,
      hoveredItemIndex: -1, // Index of the item being hovered
      dragStartIndex: -1, // Index of the item being dragged
      hasUnsavedRundownChanges: false, // Track if any items in rundown need saving

      // Version History for Undo
      versionHistory: [],        // List of versions for current item
      loadingVersions: false,    // Loading state for version history

      // Undo/Redo Stack (in-memory, client-side)
      undoStack: [],             // Array of state snapshots for undo
      redoStack: [],             // Array of undone states for redo
      maxUndoHistory: 50,        // Limit memory usage (50 states max)
      isUndoingRedoing: false,   // Prevent recursive captures during undo/redo
      undoCaptureDebounceTimer: null, // Debounce timer for capturing undo states

      // Content
      scratchContent: '',
      rawMarkdownContent: '',
      
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
      
      // Metadata editing - comprehensive frontmatter structure
      currentItemMetadata: {
        // Core identification
        AssetID: '',
        title: '',
        type: 'segment',
        slug: '',
        subtitle: '',
        
        // Production details
        description: '',
        duration: '00:00:00:00',
        status: 'draft',
        order: 1,
        airdate: '',
        priority: '',
        
        // People and resources
        guests: '',
        resources: '',
        tags: '',
        
        // System information
        server_message: '',
        created_at: ''
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
      editingSotCueData: null,  // For editing existing SOT cues
      editingFsqCueData: null,  // For editing existing FSQ cues
      editingGfxCueData: null,  // For editing existing GFX cues
      editingImgCueData: null,  // For editing existing IMG cues
      editingDirCueData: null,  // For editing existing DIR cues
      showVoModal: false,
      showNatModal: false,
      showRifModal: false,
      showDirModal: false,
      showBumpModal: false,
      showStingModal: false,
      showPkgModal: false,
      showVoxModal: false,
      showMusModal: false,
      showLiveModal: false,

      // FSQ insertion snapshot (captured when hotkey pressed)
      fsqInsertionIndex: null,

      // GFX insertion snapshot (captured when modal opened)
      gfxInsertionIndex: null,

      // IMG insertion snapshot (captured when modal opened)
      imgInsertionIndex: null,

      // SOT insertion snapshot (captured when modal opened)
      sotInsertionIndex: null,
      cuePlaceholderId: null, // Placeholder div ID for precise cue insertion

      // Rundown management state
      showNewItemModal: false,
      showNewGFXModal: false,
      showNewSOTModal: false,
      showLibraryPickerModal: false,
      libraryPickerItemType: '',
      showRundownOptions: false,

      // Cue Modals
      showImgCueModal: false,

      // Delete Cue Modal
      showDeleteCueModal: false,

      // WPM Tool
      showWpmTool: false,
      selectedCueData: {},
      selectedCueStartLine: 0,
      selectedCueEndLine: 0,
      
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
      
      // Available rundown item types - imported from single source of truth
      rundownItemTypes: [],
      
      graphicDetails: {
        url: '',
        file: null
      },
      gfxSlug: '',
      gfxDescription: '',
      graphicPreview: null,
      graphicFile: null,
      
      // Duration for the episode
      duration: '00:00:00:00',

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

    currentEpisode() {
      return this.currentEpisodeNumber;
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

    currentEpisodeAssetId() {
      // Get asset ID from current episode info or first rundown item
      if (this.rundownItems && this.rundownItems.length > 0) {
        // Try to get from first rundown item
        const firstItem = this.rundownItems[0];
        if (firstItem && (firstItem.AssetID || firstItem.asset_id)) {
          // Extract show-level asset ID (remove item suffix if present)
          const assetId = firstItem.AssetID || firstItem.asset_id;
          // Show asset IDs typically look like "DIS-2024-0238" while items have "-001", "-002" etc.
          // Return the base show asset ID
          return assetId.includes('-') ? assetId.split('-').slice(0, 3).join('-') : assetId;
        }
      }
      
      // Fallback: generate from episode number if available
      if (this.currentEpisodeNumber) {
        const year = new Date().getFullYear();
        return `DIS-${year}-${this.currentEpisodeNumber}`;
      }
      
      return '';
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

    currentSpeakerWpm() {
      // Get speaker WPM from current rundown item's speaker data
      // Default to 150 if no speaker is set or WPM is not available
      if (this.currentRundownItem && this.currentRundownItem.speaker_wpm) {
        return this.currentRundownItem.speaker_wpm
      }
      return 150
    },

    // Form validation rules
    titleRules() {
      return [
        v => !!v || 'Title is required'
      ]
    },
    durationRules() {
      return [
        v => !v || /^\d{2}:\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS:FF format'
      ]
    },

    // Unified save state for both save buttons
    episodeSaveState() {
      // Ensure we have safe defaults during initialization
      const hasChanges = Boolean(this.hasUnsavedChanges || this.hasUnsavedRundownChanges)

      return {
        hasChanges,
        buttonText: hasChanges ? 'Save Episode' : 'Synchronized',
        buttonColor: hasChanges ? 'primary' : 'success',
        buttonIcon: hasChanges ? 'mdi-content-save' : 'mdi-check-circle',
        isDisabled: !hasChanges,
        tooltip: hasChanges
          ? 'Save Episode & Rundown (unsaved changes detected)'
          : 'Episode is synchronized - no changes to save'
      }
    },

    // Script content accessor - rawMarkdownContent is now pure content (no frontmatter)
    // Metadata comes from currentItemMetadata, not embedded in content
    parsedContent() {
      return {
        frontmatter: {}, // Frontmatter no longer embedded - use currentItemMetadata instead
        scriptContent: this.rawMarkdownContent || ''
      };
    },

    // Computed property for script mode (replaces scriptContent)
    scriptContent() {
      return this.parsedContent.scriptContent;
    },

    // Computed property for metadata - uses item metadata directly
    computedMetadata() {
      return {
        ...this.currentItemMetadata
      };
    },

    // Pass-through computed properties from EditorPanel
    isXttsConfigured() {
      return this.$refs.editorPanel?.isXttsConfigured || false;
    },

    isReadingScript() {
      return this.$refs.editorPanel?.isReadingScript || false;
    }
  },
  methods: {
    /**
     * Get authentication headers for API requests
     * Uses JWT token from localStorage
     * @returns {object} Headers object with Content-Type and Authorization
     */
    getAuthHeaders() {
      const token = localStorage.getItem('auth-token');
      return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      };
    },

    /**
     * Handle episode selection from RequireEpisodeModal
     * Updates local state and syncs with global episode selector
     * @param {string} selectedEpisode - The episode number selected by user
     */
    handleEpisodeSelectedInContentEditor(selectedEpisode) {
      console.log('📺 Episode selected from modal:', selectedEpisode);

      // Update local state
      this.currentEpisodeNumber = selectedEpisode;

      // Update sessionStorage for global consistency
      sessionStorage.setItem('currentEpisodeId', selectedEpisode);
      sessionStorage.setItem('selectedEpisode', selectedEpisode);
      sessionStorage.setItem('currentEpisode', selectedEpisode);

      // Load the episode
      this.handleEpisodeChange(selectedEpisode);

      // Call the composable handler to execute any pending callbacks
      this.handleEpisodeSelected(selectedEpisode);

      console.log('✅ Episode context updated globally');
    },

    // ===== LLM Generation State Management =====
    // Generic methods to indicate LLM work is being performed on a rundown item

    /**
     * Start LLM generation indicator for a specific rundown item
     * @param {number} itemIndex - Index of the item in rundownItems array (-1 to use selectedItemIndex)
     */
    startLLMGeneration(itemIndex = -1) {
      this.generatingItemIndex = itemIndex === -1 ? this.selectedItemIndex : itemIndex;
      console.log('🤖 LLM generation started for item:', this.generatingItemIndex);
    },

    /**
     * Stop LLM generation indicator
     */
    stopLLMGeneration() {
      console.log('✅ LLM generation completed for item:', this.generatingItemIndex);
      this.generatingItemIndex = -1;
    },

    /**
     * Wrapper for async LLM operations with automatic state management
     * @param {Function} llmOperation - Async function that performs LLM work
     * @param {number} itemIndex - Index of the item (-1 to use selectedItemIndex)
     * @returns {Promise} Result of the LLM operation
     */
    async withLLMGeneration(llmOperation, itemIndex = -1) {
      this.startLLMGeneration(itemIndex);
      try {
        return await llmOperation();
      } finally {
        this.stopLLMGeneration();
      }
    },

    // ===== Undo/Redo Stack Management =====

    /**
     * Capture current state for undo stack
     * Called on content changes (debounced) and before destructive operations
     */
    captureUndoState() {
      // Don't capture if we're in the middle of an undo/redo operation
      if (this.isUndoingRedoing) {
        console.log('⏮️ Skipping undo capture - currently undoing/redoing');
        return;
      }

      // Don't capture if no item is selected
      if (this.selectedItemIndex < 0) {
        return;
      }

      const snapshot = {
        scriptContent: this.rawMarkdownContent,
        scratchContent: this.scratchContent,
        cursorPosition: this.getCursorPosition(),
        timestamp: new Date(),
        selectedItemIndex: this.selectedItemIndex
      };

      // Check if snapshot is different from last one (avoid duplicates)
      const lastSnapshot = this.undoStack[this.undoStack.length - 1];
      if (lastSnapshot &&
          lastSnapshot.scriptContent === snapshot.scriptContent &&
          lastSnapshot.scratchContent === snapshot.scratchContent) {
        console.log('⏮️ Skipping duplicate undo capture');
        return;
      }

      this.undoStack.push(snapshot);
      this.redoStack = []; // Clear redo on new change

      // Limit stack size
      if (this.undoStack.length > this.maxUndoHistory) {
        this.undoStack.shift();
      }

      console.log(`⏮️ Captured undo state (${this.undoStack.length} states in stack)`);
    },

    /**
     * Get current cursor position from EditorPanel
     * @returns {object|null} Cursor position data
     */
    getCursorPosition() {
      const editorPanel = this.$refs.editorPanel;
      if (!editorPanel) return null;

      return {
        segmentIndex: editorPanel.focusedParagraphIndex ?? editorPanel.activelyEditingSegment,
        savedCursorState: editorPanel.savedCursorState
      };
    },

    /**
     * Restore cursor position in EditorPanel
     * @param {object} position - Cursor position data from snapshot
     */
    restoreCursorPosition(position) {
      if (!position) return;

      const editorPanel = this.$refs.editorPanel;
      if (!editorPanel) return;

      // Try to restore the segment focus
      if (position.segmentIndex !== null && position.segmentIndex !== undefined) {
        editorPanel.focusedParagraphIndex = position.segmentIndex;
        editorPanel.activelyEditingSegment = position.segmentIndex;

        // If we have saved cursor state, restore it
        if (position.savedCursorState) {
          editorPanel.savedCursorState = position.savedCursorState;
          this.$nextTick(() => {
            editorPanel.restoreCursorPosition?.();
          });
        }
      }
    },

    /**
     * Undo last change
     */
    undo() {
      if (this.undoStack.length === 0) {
        console.log('⏮️ Undo stack empty - nothing to undo');
        return;
      }

      // Save current state to redo stack before undoing
      const currentState = {
        scriptContent: this.rawMarkdownContent,
        scratchContent: this.scratchContent,
        cursorPosition: this.getCursorPosition(),
        timestamp: new Date(),
        selectedItemIndex: this.selectedItemIndex
      };
      this.redoStack.push(currentState);

      // Restore previous state
      this.isUndoingRedoing = true;
      const previous = this.undoStack.pop();

      // Only restore if same item is selected
      if (previous.selectedItemIndex === this.selectedItemIndex) {
        this.rawMarkdownContent = previous.scriptContent;
        this.scratchContent = previous.scratchContent;

        this.$nextTick(() => {
          this.restoreCursorPosition(previous.cursorPosition);
          this.isUndoingRedoing = false;
        });
      } else {
        // Different item - just restore the flag
        this.isUndoingRedoing = false;
        console.log('⏮️ Undo skipped - different item was selected');
      }

      console.log(`⏮️ Undo performed (${this.undoStack.length} states remaining)`);
    },

    /**
     * Redo last undone change
     */
    redo() {
      if (this.redoStack.length === 0) {
        console.log('⏭️ Redo stack empty - nothing to redo');
        return;
      }

      // Save current state to undo stack before redoing
      const currentState = {
        scriptContent: this.rawMarkdownContent,
        scratchContent: this.scratchContent,
        cursorPosition: this.getCursorPosition(),
        timestamp: new Date(),
        selectedItemIndex: this.selectedItemIndex
      };
      this.undoStack.push(currentState);

      // Restore redo state
      this.isUndoingRedoing = true;
      const next = this.redoStack.pop();

      // Only restore if same item is selected
      if (next.selectedItemIndex === this.selectedItemIndex) {
        this.rawMarkdownContent = next.scriptContent;
        this.scratchContent = next.scratchContent;

        this.$nextTick(() => {
          this.restoreCursorPosition(next.cursorPosition);
          this.isUndoingRedoing = false;
        });
      } else {
        // Different item - just restore the flag
        this.isUndoingRedoing = false;
        console.log('⏭️ Redo skipped - different item was selected');
      }

      console.log(`⏭️ Redo performed (${this.redoStack.length} states remaining)`);
    },

    /**
     * Clear undo/redo stacks (call when switching items)
     */
    clearUndoStacks() {
      this.undoStack = [];
      this.redoStack = [];
      console.log('⏮️ Undo/redo stacks cleared');
    },

    // Get color for segment type from theme settings
    getTypeColor(segmentType) {
      // Map segment types to color keys in themeColorMap
      return getColorValue(segmentType) || '#2196F3'; // Fallback to blue
    },

    /**
     * Validate that a rundown item is selected before opening cue modals
     * Prevents users from inserting cues that would be silently lost
     * @param {string} cueType - Type of cue being inserted (for error message)
     * @returns {boolean} - true if valid, false if no item selected
     */
    requireRundownItemSelected(cueType = 'cue') {
      if (this.selectedItemIndex < 0 || !this.currentRundownItem) {
        notifyUserStandard(
          `Select a rundown item first to insert ${cueType}`,
          NOTIFICATION_COLORS.WARNING,
          3000
        );
        console.warn(`⚠️ Cannot insert ${cueType} - no rundown item selected`);
        return false;
      }
      return true;
    },

    // Modal handlers to prevent infinite recursion with v-model
    async handleShowImgModal() {
      console.log('🖼️ handleShowImgModal called');
      console.log('🖼️ selectedItemIndex:', this.selectedItemIndex);
      console.log('🖼️ currentRundownItem:', this.currentRundownItem?.title);
      if (!this.requireRundownItemSelected('IMG cue')) {
        console.log('🖼️ BLOCKED - no rundown item selected');
        return;
      }
      // CRITICAL: Flush pending changes before opening modal
      if (this.$refs.editorPanel?.flushPendingChanges) {
        await this.$refs.editorPanel.flushPendingChanges();
      }
      if (!this.showImgCueModal) {
        // Capture cursor position BEFORE opening modal
        // Use focusedParagraphIndex if available, fall back to lastKnownParagraphIndex (survives blur)
        const editorPanel = this.$refs.editorPanel;
        this.imgInsertionIndex = editorPanel?.focusedParagraphIndex ?? editorPanel?.lastKnownParagraphIndex;
        console.log('🖼️ focusedParagraphIndex:', editorPanel?.focusedParagraphIndex);
        console.log('🖼️ lastKnownParagraphIndex:', editorPanel?.lastKnownParagraphIndex);
        console.log('🖼️ Captured cursor position (using fallback if needed):', this.imgInsertionIndex);

        console.log('🖼️ Opening IMG modal...');
        this.showImgCueModal = true;
      } else {
        console.log('🖼️ Modal already open, skipping');
      }
    },
    async handleShowGfxModal() {
      if (!this.requireRundownItemSelected('GFX cue')) return;
      // CRITICAL: Flush pending changes before opening modal
      if (this.$refs.editorPanel?.flushPendingChanges) {
        await this.$refs.editorPanel.flushPendingChanges();
      }
      console.log('🎨 handleShowGfxModal called, current state:', this.showGfxModal);
      if (!this.showGfxModal) {
        // Capture cursor position BEFORE opening modal
        // Use focusedParagraphIndex if available, fall back to lastKnownParagraphIndex (survives blur)
        const editorPanel = this.$refs.editorPanel;
        this.gfxInsertionIndex = editorPanel?.focusedParagraphIndex ?? editorPanel?.lastKnownParagraphIndex;
        console.log('🎨 Captured cursor position:', this.gfxInsertionIndex);
        console.log('🎨 focusedParagraphIndex:', editorPanel?.focusedParagraphIndex);
        console.log('🎨 lastKnownParagraphIndex:', editorPanel?.lastKnownParagraphIndex);

        this.showGfxModal = true;
        console.log('🎨 GFX modal opened');
      }
    },
    async handleShowFsqModal() {
      if (!this.requireRundownItemSelected('FSQ cue')) return;
      // CRITICAL: Flush pending changes before opening modal
      if (this.$refs.editorPanel?.flushPendingChanges) {
        await this.$refs.editorPanel.flushPendingChanges();
      }
      if (!this.showFsqModal) {
        // Capture the cursor position when FSQ hotkey is pressed
        // FSQ will insert AFTER this position, but at a safe point (not inside another cue)
        // Use focusedParagraphIndex if available, fall back to lastKnownParagraphIndex (survives blur)
        const editorPanel = this.$refs.editorPanel;
        this.fsqInsertionIndex = editorPanel?.focusedParagraphIndex ?? editorPanel?.lastKnownParagraphIndex;
        console.log('📍 FSQ hotkey pressed - captured cursor position:', this.fsqInsertionIndex);
        console.log('📍 focusedParagraphIndex:', editorPanel?.focusedParagraphIndex);
        console.log('📍 lastKnownParagraphIndex:', editorPanel?.lastKnownParagraphIndex);

        // If no paragraph is focused, will insert at end
        if (this.fsqInsertionIndex === null || this.fsqInsertionIndex === undefined) {
          console.log('📍 No focus detected, FSQ will insert at end of document');
        }

        this.showFsqModal = true;
      }
    },
    handleEditFsqCue(cueData) {
      console.log('📝 Editing FSQ cue:', cueData);
      // Store cue data for editing
      this.editingFsqCueData = cueData;
      this.showFsqModal = true;
    },
    handleEditGfxCue(cueData) {
      console.log('📝 Editing GFX cue:', cueData);
      // Store cue data for editing
      this.editingGfxCueData = cueData;
      this.showGfxModal = true;
    },
    handleEditImgCue(cueData) {
      console.log('📝 Editing IMG cue:', cueData);
      // Store cue data for editing
      this.editingImgCueData = cueData;
      this.showImgCueModal = true;
    },
    handleEditDirCue(cueData) {
      console.log('📝 Editing NOTE cue:', cueData);
      // Store cue data for editing
      this.editingDirCueData = cueData;
      this.showDirModal = true;
    },
    async handleShowSotModal(cueData = null) {
      console.error('🚨 Opening SotModal via handleShowSotModal', cueData ? '(Edit mode)' : '(New)');
      // Only require selection for NEW cues, not when editing existing ones
      if (!cueData && !this.requireRundownItemSelected('SOT cue')) return;
      // CRITICAL: Flush pending changes before opening modal
      if (this.$refs.editorPanel?.flushPendingChanges) {
        await this.$refs.editorPanel.flushPendingChanges();
      }
      if (!this.showSotModal) {
        // If editing, store cue data; otherwise clear it
        this.editingSotCueData = cueData;

        if (!cueData) {
          // Keep paragraph index as metadata (snapshotting now happens in EditorPanel.insertCue)
          this.sotInsertionIndex = this.$refs.editorPanel?.focusedParagraphIndex;
          console.log('📍 Fallback cursor position:', this.sotInsertionIndex);

          // If no paragraph is focused, use last segment as fallback
          if (this.sotInsertionIndex === null || this.sotInsertionIndex === undefined) {
            const segments = this.$refs.editorPanel?.scriptSegments || [];
            this.sotInsertionIndex = segments.length > 0 ? segments.length - 1 : null;
            console.log('📍 No focus detected, using last segment:', this.sotInsertionIndex);
          }
        } else {
          console.log('📝 Editing existing SOT cue:', cueData.slug);
        }

        this.showSotModal = true;
        console.error('✅ SotModal opened - showSotModal set to true');
      }
    },
    /**
     * Handle re-upload request for SOT cue
     * Opens SotModal with existing metadata but no mediaUrl (requires new video upload)
     * This will REPLACE the existing cue block in place (not insert a new one)
     */
    handleReuploadSotCue(reuploadData) {
      console.log('📤 Re-upload SOT cue:', reuploadData);
      if (!this.showSotModal) {
        // Store cue data for editing, but this is re-upload mode
        // The reuploadData doesn't include mediaUrl, so user must upload new video
        this.editingSotCueData = {
          ...reuploadData,
          // Mark as re-upload so submitSot knows to replace in place
          isReupload: true,
          // Store original assetId so we can find and replace the cue
          originalAssetId: reuploadData.assetId,
          // Ensure mediaUrl is not set so user has to upload a new file
          mediaUrl: null,
          thumbnailUrl: null,
          // Clear trim times since they apply to the old video
          trimStart: null,
          trimEnd: null
        };

        console.log('📤 Opening SotModal in re-upload mode:', this.editingSotCueData);
        console.log('📤 Original AssetID to replace:', reuploadData.assetId);
        this.showSotModal = true;
      }
    },

    /**
     * Handle SOT job completion - refresh the cue block content from database
     * This is triggered when a PlaceholderCueCard detects its job has completed
     */
    async handleSotJobComplete({ assetId }) {
      console.log('🔄 SOT job completed, refreshing content for AssetID:', assetId);

      try {
        // Get the current rundown item ID
        const currentItem = this.currentRundownItem;
        if (!currentItem || !currentItem.db_id) {
          console.warn('No current item to refresh (missing db_id)');
          return;
        }

        // Fetch the updated script_content from the database
        // Note: db_id is the database integer ID, not asset_id
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`/api/episodes/rundown-item-by-id/${currentItem.db_id}`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch updated item: ${response.status}`);
        }

        const updatedItem = await response.json();
        console.log('📥 Fetched updated item from database:', updatedItem.id);

        // Update the local rundown item's script field using Vue.set pattern for reactivity
        const itemIndex = this.rundownItems.findIndex(item => item.id === currentItem.id);
        if (itemIndex >= 0) {
          const newScript = updatedItem.script_content || updatedItem.script;
          // Replace the entire item to ensure Vue detects the change
          this.rundownItems.splice(itemIndex, 1, {
            ...this.rundownItems[itemIndex],
            script: newScript
          });
          console.log('✅ Updated rundownItems[', itemIndex, '] with new script content');

          // If this item is currently selected, refresh the editor content
          if (this.selectedItemIndex === itemIndex) {
            // Rebuild rawMarkdownContent from the updated item
            this.loadRawMarkdownContent(this.rundownItems[itemIndex]);
            console.log('✅ Refreshed rawMarkdownContent for current item');

            // CRITICAL: Force EditorPanel to invalidate its segment cache
            // This ensures the cue cards re-render with the new data from processing
            this.$nextTick(() => {
              if (this.$refs.editorPanel && this.$refs.editorPanel.forceRefreshSegments) {
                this.$refs.editorPanel.forceRefreshSegments();
                console.log('✅ Forced EditorPanel segment refresh');
              }
            });
          }
        }

      } catch (error) {
        console.error('Failed to refresh SOT content:', error);
      }
    },

    handleShowVoModal() {
      if (!this.requireRundownItemSelected('VO cue')) return;
      if (!this.showVoModal) {
        this.showVoModal = true;
      }
    },
    handleShowNatModal() {
      if (!this.requireRundownItemSelected('NAT cue')) return;
      if (!this.showNatModal) {
        this.showNatModal = true;
      }
    },
    handleShowRifModal() {
      if (!this.requireRundownItemSelected('RIF cue')) return;
      if (!this.showRifModal) {
        this.showRifModal = true;
      }
    },
    handleShowPkgModal() {
      if (!this.requireRundownItemSelected('PKG cue')) return;
      if (!this.showPkgModal) {
        this.showPkgModal = true;
      }
    },
    handleShowDirModal() {
      if (!this.requireRundownItemSelected('NOTE cue')) return;
      if (!this.showDirModal) {
        // Clear editing data when creating new NOTE
        this.editingDirCueData = null;
        this.showDirModal = true;
      }
    },
    handleShowBumpModal() {
      if (!this.requireRundownItemSelected('BUMP cue')) return;
      if (!this.showBumpModal) {
        this.showBumpModal = true;
      }
    },
    handleShowStingModal() {
      if (!this.requireRundownItemSelected('STING cue')) return;
      if (!this.showStingModal) {
        this.showStingModal = true;
      }
    },
    handleShowVoxModal() {
      if (!this.requireRundownItemSelected('VOX cue')) return;
      if (!this.showVoxModal) {
        this.showVoxModal = true;
      }
    },
    handleShowMusModal() {
      if (!this.requireRundownItemSelected('MUS cue')) return;
      if (!this.showMusModal) {
        this.showMusModal = true;
      }
    },
    handleShowLiveModal() {
      if (!this.requireRundownItemSelected('LIVE cue')) return;
      if (!this.showLiveModal) {
        this.showLiveModal = true;
      }
    },

    // SINGLE SOURCE HELPER: Update script content within rawMarkdownContent
    updateScriptContent(newScriptContent) {
      // Database-first: no frontmatter in script_content, just the body
      // NOTE: Removed '---' → '- - -' sanitizer that was corrupting content.
      // Frontmatter is stripped on load, so standalone '---' lines in body content
      // (e.g., markdown horizontal rules) should be preserved as-is.
      this.rawMarkdownContent = newScriptContent || '';

      // CRITICAL: Mark that we have unsaved changes when content is updated
      this.hasUnsavedChanges = true;
    },

    // SINGLE SOURCE HELPER: Append to script content
    // For cue insertions (FSQ, etc.), finds a safe insertion point between segments
    appendToScriptContent(textToAppend, insertAfterParagraph = null) {
      console.log('📥📥📥 ===============================================');
      console.log('📥 appendToScriptContent CALLED');
      console.log('📄 Text to append length:', textToAppend.length);
      console.log('📝 Text to append full content:\n', textToAppend);
      console.log('📍 Insert after paragraph:', insertAfterParagraph);
      console.log('📊 this.parsedContent exists:', !!this.parsedContent);
      console.log('📊 this.parsedContent.scriptContent exists:', !!this.parsedContent?.scriptContent);

      const currentScript = this.parsedContent.scriptContent || '';
      console.log('📊 Current script length:', currentScript.length);
      console.log('📊 Current script preview (first 200 chars):', currentScript.substring(0, 200));

      let newScript;
      let isAtEnd = false;
      const isInsertingCue = textToAppend.includes('<!-- Begin Cue -->');

      // If insertAfterParagraph is specified (and is a valid number), insert after that paragraph
      // Otherwise append to end of script
      if (insertAfterParagraph !== null && insertAfterParagraph !== undefined && typeof insertAfterParagraph === 'number' && this.$refs.editorPanel) {
        console.log('🔍 Insertion after specific paragraph requested');
        const segments = this.$refs.editorPanel.scriptSegments || [];
        console.log('📋 Total segments:', segments.length);

        // Find the insertion point by counting segments up to the specified index
        // For cue insertions, skip past any consecutive cue segments to find clean insertion point
        let insertionPoint = 0;
        let charCount = 0;
        let targetIndex = insertAfterParagraph;

        // If inserting a cue, find the next text segment boundary (skip past cues)
        if (isInsertingCue) {
          // Start from the requested position and skip any consecutive cues
          let i = insertAfterParagraph;
          while (i < segments.length && segments[i]?.type === 'cue') {
            console.log(`📍 Segment ${i} is a cue, skipping...`);
            i++;
          }
          // If we found a text segment, insert before it (after previous segment)
          // If we reached the end, insert at end
          targetIndex = i > 0 ? i - 1 : 0;
          if (i >= segments.length) {
            targetIndex = segments.length - 1;
            console.log('📍 Reached end of segments, will insert at end');
          } else {
            console.log(`📍 Found safe insertion point after segment ${targetIndex}`);
          }
        }

        // Calculate character position for the target segment
        for (let i = 0; i <= targetIndex && i < segments.length; i++) {
          const segment = segments[i];
          if (segment.type === 'text' && segment.content) {
            charCount += segment.content.length;
          } else if (segment.type === 'cue' && segment.raw) {
            charCount += segment.raw.length;
          }
          insertionPoint = charCount;
        }

        // For cue insertions, ensure we're inserting COMPLETELY OUTSIDE any elements
        // This includes: cue blocks, <p> tags, and any other HTML elements
        if (isInsertingCue && insertionPoint < currentScript.length) {
          const beforeInsert = currentScript.slice(0, insertionPoint);
          const afterInsert = currentScript.slice(insertionPoint);

          // Check if we're inside a cue block
          const lastBeginCue = beforeInsert.lastIndexOf('<!-- Begin Cue -->');
          const lastEndCue = beforeInsert.lastIndexOf('<!-- End Cue -->');

          if (lastBeginCue > lastEndCue) {
            // We're inside a cue block - find the end and insert after
            const endCuePos = afterInsert.indexOf('<!-- End Cue -->');
            if (endCuePos !== -1) {
              insertionPoint += endCuePos + '<!-- End Cue -->'.length;
              console.log('📍 Was inside cue block, moved to after <!-- End Cue -->');
            }
          }

          // Check if we're inside a <p> tag - count open vs close tags
          const openPTags = (beforeInsert.match(/<p\s/g) || []).length;
          const closePTags = (beforeInsert.match(/<\/p>/g) || []).length;

          if (openPTags > closePTags) {
            // We're inside a <p> tag - find the closing </p> and insert after
            const closePPos = afterInsert.indexOf('</p>');
            if (closePPos !== -1) {
              insertionPoint += closePPos + '</p>'.length;
              console.log('📍 Was inside <p> tag, moved to after </p>');
            }
          }

          // Check if we're inside any other HTML element by looking for unclosed tags
          // Find the last < that isn't followed by a matching >
          const lastOpenBracket = beforeInsert.lastIndexOf('<');
          if (lastOpenBracket !== -1) {
            const afterOpenBracket = beforeInsert.slice(lastOpenBracket);
            const hasClosingBracket = afterOpenBracket.includes('>');

            if (!hasClosingBracket) {
              // We're in the middle of an HTML tag - move past it
              const closeBracketPos = afterInsert.indexOf('>');
              if (closeBracketPos !== -1) {
                insertionPoint += closeBracketPos + 1;
                console.log('📍 Was inside HTML tag, moved past closing >');
              }
            }
          }

          // Final safety check: ensure we're not splitting an element
          // Move to after any closing tag that immediately follows
          const updatedAfter = currentScript.slice(insertionPoint);
          const immediateCloseMatch = updatedAfter.match(/^(\s*<\/[^>]+>)+/);
          if (immediateCloseMatch) {
            insertionPoint += immediateCloseMatch[0].length;
            console.log('📍 Moved past immediate closing tags:', immediateCloseMatch[0]);
          }
        }

        console.log('📍 Final insertion point:', insertionPoint);

        // Check if we're inserting at the end
        isAtEnd = (insertionPoint >= currentScript.length);
        console.log('📍 Is at end:', isAtEnd);

        // Insert at the calculated position
        newScript = currentScript.slice(0, insertionPoint) + textToAppend + currentScript.slice(insertionPoint);
        console.log('✅ Inserted after paragraph', insertAfterParagraph, '(adjusted to safe point)');
      } else {
        // Default behavior: append to end
        console.log('🔍 No specific insertion point - appending to end');
        newScript = currentScript + textToAppend;
        isAtEnd = true;
        console.log('✅ Appended to end (no insertion point specified)');
      }

      // If cue was inserted at the end of the script, add empty paragraph for writer to continue
      if (isAtEnd && isInsertingCue) {
        console.log('🎯 Cue inserted at end of script - adding empty paragraph for continuation');
        // Extract last speaker from script content
        const lastSpeaker = this.getLastSpeakerFromScript(newScript);
        console.log('📢 Last speaker detected:', lastSpeaker);
        newScript += `\n<p class="${lastSpeaker}"></p>\n`;
      }

      console.log('📊 New script length:', newScript.length);
      console.log('📊 New script preview (first 200 chars):', newScript.substring(0, 200));
      console.log('🔄 Calling updateScriptContent...');

      this.updateScriptContent(newScript);
      console.log('✅ appendToScriptContent complete');
      console.log('📥📥📥 ===============================================');
    },

    /**
     * Clean up any cue insertion placeholders
     */
    cleanupCuePlaceholder() {
      if (this.cuePlaceholderId) {
        const placeholder = document.getElementById(this.cuePlaceholderId);
        if (placeholder) {
          placeholder.remove();
          console.log('🧹 Removed cue placeholder:', this.cuePlaceholderId);
        }
        this.cuePlaceholderId = null;
      }
    },

    /**
     * Insert a placeholder div at the current cursor position for cue insertion
     * Handles stepping out of <p> tags and cue blocks to find the correct insertion point
     *
     * IMPORTANT: The placeholder must be inserted OUTSIDE of any:
     * - <p> tags (paragraph elements)
     * - .cue-segment elements (cue card wrappers)
     * - .cue-card elements (cue card components)
     * - .cue-block elements (raw cue block divs)
     * - Any element that is part of a cue structure
     */
    insertCuePlaceholder() {
      console.log('📍📍📍 ===============================================');
      console.log('📍 insertCuePlaceholder CALLED');

      try {
        // Get the editor panel's script container
        const editorPanel = this.$refs.editorPanel;
        if (!editorPanel || !editorPanel.$refs.scriptContainer) {
          console.warn('⚠️ No editor panel or script container found');
          return;
        }

        const scriptContainer = editorPanel.$refs.scriptContainer;
        const selection = window.getSelection();

        if (!selection || selection.rangeCount === 0) {
          console.warn('⚠️ No selection found');
          return;
        }

        const range = selection.getRangeAt(0);
        let currentNode = range.startContainer;

        console.log('📍 Current node:', currentNode.nodeName, currentNode.nodeType);
        console.log('📍 Current node parent:', currentNode.parentElement?.tagName);

        // If we're in a text node, get the parent element
        if (currentNode.nodeType === Node.TEXT_NODE) {
          currentNode = currentNode.parentElement;
        }

        console.log('📍 Working with element:', currentNode?.tagName, currentNode?.className);

        /**
         * Helper function to check if an element is a cue container or paragraph
         * These are elements we should NOT insert a cue INSIDE of
         */
        const isCueOrParagraphContainer = (element) => {
          if (!element || element === scriptContainer) return false;

          const tagName = element.tagName?.toLowerCase();
          const className = element.className || '';

          // Check for paragraph
          if (tagName === 'p') return true;

          // Check for cue-related classes
          if (className.includes('cue-segment')) return true;
          if (className.includes('cue-card')) return true;
          if (className.includes('cue-block')) return true;
          if (className.includes('placeholder-cue-card')) return true;
          if (className.includes('image-cue-card')) return true;

          // Check for v-card which wraps cue cards
          if (tagName === 'div' && className.includes('v-card')) return true;

          return false;
        };

        // Walk up the DOM tree to find the outermost cue/paragraph container
        // We want to insert AFTER this container, not inside it
        let outermostContainer = null;
        let walker = currentNode;

        while (walker && walker !== scriptContainer) {
          if (isCueOrParagraphContainer(walker)) {
            outermostContainer = walker;
            console.log('🔍 Found container:', walker.tagName, walker.className);
          }
          walker = walker.parentElement;
        }

        // Create the placeholder div with a unique ID
        const placeholderId = `cue-placeholder-${Date.now()}`;
        const placeholder = document.createElement('div');
        placeholder.id = placeholderId;
        placeholder.className = 'cue-insertion-placeholder';
        placeholder.style.cssText = 'height: 2px; background: #FF9800; margin: 5px 0; opacity: 0.5; position: relative;';
        placeholder.innerHTML = '<span style="position: absolute; top: -10px; left: 0; font-size: 10px; color: #FF9800; font-weight: bold;">▼ CUE WILL INSERT HERE</span>';

        console.log('📍 Placeholder ID:', placeholderId);

        // Insert the placeholder AFTER the outermost container
        if (outermostContainer) {
          console.log('📍 Outermost container found:', outermostContainer.tagName, outermostContainer.className);

          // Insert after the outermost container (before its next sibling)
          const parent = outermostContainer.parentElement;
          const nextSibling = outermostContainer.nextSibling;

          if (parent) {
            if (nextSibling) {
              parent.insertBefore(placeholder, nextSibling);
              console.log('✅ Inserted placeholder AFTER container (before next sibling)');
            } else {
              parent.appendChild(placeholder);
              console.log('✅ Appended placeholder after container (no next sibling)');
            }
          } else {
            // Fallback: append to script container
            scriptContainer.appendChild(placeholder);
            console.log('✅ Appended placeholder to script container (no parent found)');
          }
        } else {
          // No container found - cursor is at top level of script container
          // Insert at current cursor position
          console.log('📍 No container found - inserting at cursor position in script container');

          if (currentNode && currentNode.parentElement === scriptContainer) {
            // Current node is direct child of script container
            const nextSibling = currentNode.nextSibling;
            if (nextSibling) {
              scriptContainer.insertBefore(placeholder, nextSibling);
              console.log('✅ Inserted placeholder after current node');
            } else {
              scriptContainer.appendChild(placeholder);
              console.log('✅ Appended placeholder to script container');
            }
          } else {
            // Fallback: append to script container
            scriptContainer.appendChild(placeholder);
            console.log('✅ Appended placeholder to script container (fallback)');
          }
        }

        // Store the placeholder ID for later use
        this.cuePlaceholderId = placeholderId;
        console.log('✅ Stored placeholder ID:', this.cuePlaceholderId);

      } catch (error) {
        console.error('❌ Error inserting cue placeholder:', error);
        console.error('❌ Stack trace:', error.stack);
      }

      console.log('📍📍📍 ===============================================');
    },

    /**
     * Extract the last speaker class from script HTML content
     * @param {string} scriptHtml - The HTML script content
     * @returns {string} The last speaker class name (e.g., 'HOST', 'GUEST', 'JOSH')
     */
    getLastSpeakerFromScript(scriptHtml) {
      if (!scriptHtml) {
        return this.currentRundownItem?.speaker || this.currentItemMetadata?.speaker || 'HOST';
      }

      // Find all <p class="SPEAKER"> tags and extract the last one
      const paragraphRegex = /<p\s+class="([^"]+)"/g;
      let lastSpeaker = null;
      let match;

      while ((match = paragraphRegex.exec(scriptHtml)) !== null) {
        lastSpeaker = match[1];
      }

      // If we found a speaker, return it; otherwise use fallback
      if (lastSpeaker) {
        return lastSpeaker;
      }

      // Fallback to item metadata or default
      return this.currentRundownItem?.speaker || this.currentItemMetadata?.speaker || 'HOST';
    },

    // Load interface settings from database
    async loadInterfaceSettings() {
      try {
        const response = await fetch('/api/settings/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })

        if (response.ok) {
          const settings = await response.json()

          // Load interface settings
          if (settings.interface) {
            this.interfaceSettings = { ...this.interfaceSettings, ...settings.interface }
            // Also save to localStorage for EditorPanel to access
            localStorage.setItem('showbuild_interface_settings', JSON.stringify(this.interfaceSettings))
            console.log('Interface settings loaded:', this.interfaceSettings)
          }
        }
      } catch (error) {
        console.error('Failed to load interface settings:', error)
      }
    },

    async handleEpisodeChange(newEpisodeNumber) {
      console.log('Episode change requested to:', newEpisodeNumber);
      
      if (!newEpisodeNumber || newEpisodeNumber === this.currentEpisodeNumber) {
        console.log('No episode change needed');
        return;
      }

      // Confirm episode change if there are unsaved changes
      if (this.hasUnsavedChanges) {
        const confirmChange = confirm('You have unsaved changes. Are you sure you want to switch episodes? Unsaved changes will be lost.');
        if (!confirmChange) {
          return;
        }
      }

      // Load the new episode
      try {
        await this.loadEpisode(newEpisodeNumber);
        console.log('Episode successfully changed to:', newEpisodeNumber);
      } catch (error) {
        console.error('Failed to change episode:', error);
        alert('Failed to load the selected episode. Please try again.');
      }
    },

    async reloadFromDatabase() {
      console.log('Reloading all content from database...');

      // CRITICAL: Save any pending changes before reloading
      if (this.selectedItemIndex >= 0) {
        if (this.$refs.editorPanel?.flushPendingChanges) {
          console.log('💾 Flushing pending editor changes before reload...');
          this.$refs.editorPanel.flushPendingChanges();
          await this.$nextTick();
        }
        if (this.hasUnsavedChanges) {
          console.log('💾 Saving changes before reload...');
          try {
            await this.saveCurrentItem();
          } catch (error) {
            console.error('Failed to save before reload:', error);
          }
        }
      }

      try {
        // Show loading state
        this.loadingRundown = true;

        // Clear current state
        this.rundownItems = [];
        this.selectedItemIndex = -1;
        this.scratchContent = '';
        this.rawMarkdownContent = '';

        // Force EditorPanel to re-parse on reload
        if (this.$refs.editorPanel) {
          this.$refs.editorPanel.segmentReparseKey++;
          this.$refs.editorPanel.cachedScriptSegments = null;
          this.$refs.editorPanel.lastParsedContent = null;
          this.$refs.editorPanel.segmentEditBuffer = {};
        }

        // Reload episode data and rundown
        if (this.currentEpisodeNumber) {
          await this.loadEpisode(this.currentEpisodeNumber);
          console.log('Successfully reloaded all content from database');

          // Show success message
          this.$emit('show-snackbar', 'Content reloaded from database', 'success');
        } else {
          console.warn('No current episode to reload');
        }
      } catch (error) {
        console.error('Failed to reload from database:', error);
        this.$emit('show-snackbar', 'Failed to reload content from database', 'error');
      } finally {
        this.loadingRundown = false;
      }
    },

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
            style.color = '#ffffff'; // Always use white text for better contrast
          } else {
            // Fallback color
            style.backgroundColor = '#9E9E9E';
            style.color = '#ffffff';
          }
        } else {
          // Fallback for unknown types
          style.backgroundColor = '#9E9E9E';
          style.color = '#ffffff';
        }

        // Override for selected item - enhance the existing color instead of replacing it
        if (this.selectedItemIndex === index) {
          // Keep the item's type color but add visual emphasis
          style.border = '3px solid #ffffff';
          style.boxShadow = '0 0 8px rgba(255,255,255,0.8), inset 0 0 0 2px rgba(0,0,0,0.2)';
          style.transform = 'scale(1.02)';
          style.zIndex = '10';
          // Make the color slightly brighter for selection
          if (style.backgroundColor && style.backgroundColor !== '#9E9E9E') {
            // Keep the existing color but make it slightly brighter/more saturated
            style.filter = 'brightness(1.1) saturate(1.2)';
          }
        }
        // Override for hovered item (but not if it's the selected item)
        else if (this.hoveredItemIndex === index) {
           const hoverColorName = getColorValue('hover-interface') || getColorValue('hover') || 'blue-lighten-4';
           const hoverColor = resolveVuetifyColor(hoverColorName, this.$vuetify);
           if (hoverColor) {
             // Add a subtle border instead of changing the whole background
             style.boxShadow = `inset 4px 0 0 0 ${hoverColor}`;
           }
        }

        console.log(`Final style for ${itemType} at index ${index}:`, style);
        return style;
      } catch (error) {
        console.error('Error in resolveItemStyle:', error);
        return { backgroundColor: '#9E9E9E', color: '#ffffff' }; // Return fallback style on error
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
        
        // Load initial episode if needed
        let episodeToLoad = null;
        
        // Priority 1: Episode from props
        if (this.episode && this.episodes.some(e => e.value === this.episode.padStart(4, '0'))) {
          episodeToLoad = this.episode.padStart(4, '0');
        }
        // Priority 2: Current episode number if still valid
        else if (this.currentEpisodeNumber && this.episodes.some(e => e.value === this.currentEpisodeNumber)) {
          episodeToLoad = this.currentEpisodeNumber;
        }
        // Priority 3: Last selected episode from session storage
        else if (!this.episode) {
          const lastEpisode = sessionStorage.getItem('selectedEpisode');
          if (lastEpisode && this.episodes.some(e => e.value === lastEpisode)) {
            episodeToLoad = lastEpisode;
          } else if (this.episodes.length > 0) {
            // Default to the next upcoming episode (by air date)
            const now = new Date();
            const episodesWithDates = this.episodes
              .filter(e => e.air_date)
              .map(e => ({
                ...e,
                parsedDate: new Date(e.air_date)
              }));

            // Find upcoming episodes (air date in future or today)
            const upcomingEpisodes = episodesWithDates
              .filter(e => e.parsedDate >= now)
              .sort((a, b) => a.parsedDate - b.parsedDate);

            if (upcomingEpisodes.length > 0) {
              // Load the soonest upcoming episode
              episodeToLoad = upcomingEpisodes[0].value;
            } else {
              // No upcoming episodes, default to the latest episode number
              const sortedEpisodes = [...this.episodes].sort((a, b) => b.value - a.value);
              episodeToLoad = sortedEpisodes[0].value;
            }
          }
        }
        
        if (episodeToLoad) {
          console.log('Loading initial episode:', episodeToLoad);
          await this.loadEpisode(episodeToLoad, true);
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

    async loadEpisode(episodeNumber, skipSessionUpdate = false, forceReload = false) {
      const paddedNumber = this.padEpisodeNumber(episodeNumber);
      if (!paddedNumber) return;

      // Skip if already loaded with content (unless force reload is requested)
      if (!forceReload && this.currentEpisodeNumber === paddedNumber && this.rundownItems.length > 0) {
        console.log('Episode already loaded with items');
        return;
      }

      console.log('Starting episode load for:', paddedNumber);
      this.loadingEpisode = true;
      this.loadingRundown = true;

      try {
        // Set episode number
        this.currentEpisodeNumber = paddedNumber;
        if (!skipSessionUpdate) {
          sessionStorage.setItem('selectedEpisode', paddedNumber);
        }

        // Load episode info, rundown, and thumbnails in parallel
        const [infoResponse, rundownResponse, thumbnailsResponse] = await Promise.allSettled([
          axios.get(`/api/episodes/${paddedNumber}/info`),
          axios.get(`/api/episodes/${paddedNumber}/rundown`),
          axios.get(`/api/episodes/${paddedNumber}/thumbnails`)
        ]);

        // Handle episode info
        if (infoResponse.status === 'fulfilled') {
          const info = infoResponse.value.data.info || {};
          console.log('API Response - Episode Info:', info);
          this.currentAirDate = info.airdate || '';
          this.currentAirTime = info.airtime || '';
          this.currentAirTimezone = info.airtimezone || 'America/New_York';
          this.currentShowTimezone = info.show_timezone || 'America/New_York';
          this.currentProductionStatus = info.status || 'draft';
          this.duration = info.duration || '01:00:00';
          this.showTitle = info.title || 'Untitled';
          this.currentEpisodeSlug = info.slug || '';
          this.currentEpisodeTitle = info.title || '';
          this.currentEpisodeSubtitle = info.subtitle || '';
          this.currentEpisodeGuest = info.guest || '';
          this.currentEpisodeDescription = info.description || '';
          this.currentEpisodeIsDummy = info.is_dummy || false;
          console.log('After setting - Air Date:', this.currentAirDate, 'Status:', this.currentProductionStatus, 'Duration:', this.duration);
        }

        // Handle rundown
        if (rundownResponse.status === 'fulfilled') {
          const items = rundownResponse.value.data.items || [];
          this.rundownItems = items;

          // Restore selected item from sessionStorage or default to first item
          let restoredIndex = -1;
          if (items.length > 0) {
            const sessionKey = `selectedItem_${paddedNumber}`;
            const savedIndex = sessionStorage.getItem(sessionKey);

            if (savedIndex !== null) {
              const parsedIndex = parseInt(savedIndex);
              // Validate that the saved index is still valid
              if (parsedIndex >= 0 && parsedIndex < items.length) {
                restoredIndex = parsedIndex;
                console.log(`Restored selected item index ${restoredIndex} from session for episode ${paddedNumber}`);
              } else {
                console.log(`Saved index ${parsedIndex} is invalid for ${items.length} items, defaulting to first item`);
                restoredIndex = 0;
              }
            } else {
              // No saved selection, default to first item
              restoredIndex = 0;
              console.log('No saved selection found, defaulting to first item');
            }
          }

          this.selectedItemIndex = restoredIndex;
          if (this.selectedItemIndex !== -1 && items[this.selectedItemIndex]) {
            // Force EditorPanel to re-parse segments on episode load
            if (this.$refs.editorPanel) {
              this.$refs.editorPanel.segmentReparseKey++;
            }
            this.loadItemContent(items[this.selectedItemIndex]);
          }
          console.log('Loaded episode', paddedNumber, 'with', items.length, 'items, selected index:', this.selectedItemIndex);
        } else {
          console.error('Failed to load rundown:', rundownResponse.reason);
          this.rundownError = `Failed to load rundown for episode ${paddedNumber}`;
        }

        // Handle episode info errors
        if (infoResponse.status === 'rejected') {
          console.error('Failed to load episode info:', infoResponse.reason);
        }

        // Handle thumbnails
        if (thumbnailsResponse.status === 'fulfilled') {
          this.episodeThumbnails = thumbnailsResponse.value.data.thumbnails || [];
          console.log('Loaded', this.episodeThumbnails.length, 'thumbnail(s) for episode', paddedNumber);
        } else {
          console.warn('Failed to load thumbnails:', thumbnailsResponse.reason);
          this.episodeThumbnails = [];
        }

        // Fetch confirmed thumbnail from database
        try {
          const confirmedResponse = await axios.get(`/api/episodes/${paddedNumber}/thumbnail/confirmed`);
          if (confirmedResponse.data.confirmed && confirmedResponse.data.exists) {
            this.confirmedThumbnailUrl = confirmedResponse.data.url;
            this.takenSourceUrl = confirmedResponse.data.source_url || null;
            console.log('Confirmed thumbnail:', this.confirmedThumbnailUrl, 'Source:', this.takenSourceUrl);
          } else {
            this.confirmedThumbnailUrl = null;
            this.takenSourceUrl = null;
          }
        } catch (err) {
          console.warn('Failed to fetch confirmed thumbnail:', err);
          this.takenSourceUrl = null;
          this.confirmedThumbnailUrl = null;
        }

        // Start polling for SOT processing updates
        this.sotProcessing.startPolling(
          paddedNumber,
          (job) => {
            // On update: just log for now
            console.log(`🎬 SOT job update: ${job.slug} - ${job.current_phase}`)
          },
          async (job) => {
            // On complete: reload the current item if it contains this asset_id
            console.log(`✅ SOT job completed: ${job.slug}`)
            await this.reloadCurrentItemContent()
          }
        )

      } catch (error) {
        console.error('Failed to load episode:', error);
        this.rundownError = `Failed to load episode ${paddedNumber}`;
      } finally {
        console.log('Clearing loading flags for episode:', paddedNumber);
        this.loadingEpisode = false;
        this.loadingRundown = false;
      }
    },
    // Save just the current item (autosave - content only, no order changes)
    // isManualSave: true for manual saves (creates version history), false for autosave
    // paragraphToFlash: specific paragraph index to flash on success (captured when typing started)
    async saveCurrentItem(isManualSave = false, paragraphToFlash = null) {
      if (this.selectedItemIndex < 0 || !this.currentRundownItem) {
        console.log('Cannot save - no valid item selected');
        return;
      }

      this.saving = true;
      // CRITICAL FIX: Capture the item index NOW, not after async operations.
      // If selectedItemIndex changes during the await (e.g., user switches items),
      // the post-save mutation must still target the correct item.
      const saveTargetIndex = this.selectedItemIndex;
      try {
        const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
        const headers = this.getAuthHeaders();

        // Save only the current item's content without touching order
        // IMPORTANT: Spread rundownItems first, then override with current editor content
        const currentItem = {
          ...this.rundownItems[this.selectedItemIndex]
        };

        // Override with current editor content (must come after spread)
        // Use rawMarkdownContent if available (preserves frontmatter), otherwise use parsed script content
        // SAFETY: Only save if we have actual content to save
        const contentToSave = this.rawMarkdownContent || this.parsedContent.scriptContent || '';

        // CRITICAL: Prevent saving empty/minimal content that would destroy existing content
        // NOTE: API returns items with field "script" (not "script_content"), so check .script
        const existingScript = this.rundownItems[this.selectedItemIndex]?.script || '';
        if (contentToSave.length < 50 && existingScript.length > 100) {
          console.error('🚨 BLOCKED: Attempted to save minimal content over substantial existing content');
          console.error(`   New content: ${contentToSave.length} chars, Existing: ${existingScript.length} chars`);
          throw new Error('Blocked save: would destroy existing content');
        }

        currentItem.script = contentToSave;
        currentItem.scratch = this.scratchContent;
        currentItem.rawMarkdown = this.rawMarkdownContent;

        // Get the AssetID for this item
        const assetId = currentItem.asset_id || currentItem.AssetID || currentItem.id;

        // CRITICAL VALIDATION: Check for corruption before saving
        // Check rawMarkdownContent for multiple YAML frontmatter blocks (multiple segments)
        const rawToCheck = this.rawMarkdownContent || '';

        // More specific check: Look for multiple frontmatter blocks by detecting the pattern
        // "---" or "- - -" followed by YAML keys like "id:", "slug:", "type:" which indicate segment metadata
        const frontmatterBlockPattern = /^(?:---|(?:-\s){2}-)\s*\n\s*(id|slug|type|title):/gm;
        const frontmatterBlockMatches = rawToCheck.match(frontmatterBlockPattern);
        const frontmatterBlockCount = frontmatterBlockMatches ? frontmatterBlockMatches.length : 0;

        console.log('🔍 Corruption check:', {
          frontmatterBlockCount,
          rawLength: rawToCheck.length,
          matches: frontmatterBlockMatches,
          rawPreview: rawToCheck.substring(0, 500)
        });

        // Should have exactly 1 frontmatter block (the segment's metadata)
        // More than 1 means multiple segments were concatenated
        if (frontmatterBlockCount > 1) {
          console.error('🚨🚨🚨 SAVE BLOCKED: Raw content contains multiple segments!');
          console.error('Frontmatter block occurrences:', frontmatterBlockCount);
          console.error('Expected: 1 (single segment)');
          console.error('Raw content preview:', rawToCheck.substring(0, 500));
          console.error('All matches:', frontmatterBlockMatches);
          throw new Error('Cannot save: Multiple segments detected in script content. This would corrupt the database.');
        }

        console.log('💾 Autosaving current item:', {
          title: currentItem.title,
          assetId: assetId,
          selectedIndex: this.selectedItemIndex,
          scriptLength: this.parsedContent.scriptContent?.length || 0,
          scriptPreview: this.parsedContent.scriptContent?.substring(0, 50) || ''
        });

        // Use save-rundown endpoint in single-item mode
        const response = await axios.put(
          `/api/episodes/${paddedId}/save-rundown`,
          {
            item: currentItem,
            asset_id: assetId,
            save_type: isManualSave ? 'manual_save' : 'autosave'
          },
          { headers }
        );

        if (response.data) {
          // Check if backend blocked a destructive save
          if (response.data.blocked_saves && response.data.blocked_saves.length > 0) {
            console.error('🚨 Backend BLOCKED a destructive save:', response.data.blocked_saves);
            const editorPanel = this.$refs.editorPanel;
            if (editorPanel && editorPanel.flashParagraph && paragraphToFlash !== null) {
              editorPanel.flashParagraph(paragraphToFlash, 'error', 5);
            }
            if (window.flashUrgent) {
              window.flashUrgent('Save blocked: content too short to overwrite existing', window.FLASH_COLORS?.RED || '#f44336', 5000);
            }
            // Keep hasUnsavedChanges true so user knows save didn't fully succeed
            this.hasUnsavedChanges = true;
            return;
          }

          this.hasUnsavedChanges = false;
          console.log('✅ Current item autosaved successfully');

          // Flash the specific paragraph that was being edited (not necessarily the currently focused one)
          console.log('💾 Autosave complete, attempting to flash paragraph:', paragraphToFlash);
          const editorPanel = this.$refs.editorPanel;
          if (editorPanel && editorPanel.flashParagraph && paragraphToFlash !== null && paragraphToFlash !== undefined) {
            console.log('💾 Calling flashParagraph for index:', paragraphToFlash);
            editorPanel.flashParagraph(paragraphToFlash, 'success', 3);
          } else {
            console.log('💾 Skipping flash - no valid paragraph index or editorPanel not ready');
          }

          // Update local state with saved content IN-PLACE
          // CRITICAL: Use saveTargetIndex (captured at call time) instead of this.selectedItemIndex
          // which may have changed during the async axios call if the user switched items.
          // Using the live selectedItemIndex here was Bug #5 - it could write the wrong content
          // to the wrong item's local state during concurrent saves.
          const savedItem = this.rundownItems[saveTargetIndex];
          if (savedItem) {
            savedItem.script = contentToSave;
            savedItem.scratch = this.scratchContent;
            savedItem.rawMarkdown = null;  // Clear to prevent stale frontmatter-included content
          }
        }

      } catch (error) {
        console.error('❌ Autosave failed:', error);
        this.hasUnsavedChanges = true;
        throw error; // Re-throw so EditorPanel can show red flash
      } finally {
        this.saving = false;
      }
    },

    // Fetch version history for current rundown item
    async fetchVersionHistory() {
      if (!this.currentRundownItem) {
        this.versionHistory = [];
        return;
      }

      const assetId = this.currentRundownItem.asset_id || this.currentRundownItem.AssetID;
      if (!assetId) {
        this.versionHistory = [];
        return;
      }

      this.loadingVersions = true;
      try {
        const headers = this.getAuthHeaders();
        const response = await axios.get(`/api/episodes/rundown-item/${assetId}/versions`, { headers });

        if (response.data && response.data.versions) {
          this.versionHistory = response.data.versions;
          console.log(`📜 Loaded ${this.versionHistory.length} versions for ${assetId}`);
        } else {
          this.versionHistory = [];
        }
      } catch (error) {
        console.error('Failed to fetch version history:', error);
        this.versionHistory = [];
      } finally {
        this.loadingVersions = false;
      }
    },

    // Undo last change - restore to previous version
    async undoLastChange() {
      if (!this.currentRundownItem) {
        notifyUserStandard('No item selected', NOTIFICATION_COLORS.WARNING, 2000);
        return;
      }

      const assetId = this.currentRundownItem.asset_id || this.currentRundownItem.AssetID;
      if (!assetId) {
        notifyUserStandard('Cannot undo - item has no asset ID', NOTIFICATION_COLORS.WARNING, 2000);
        return;
      }

      // Refresh version history first
      await this.fetchVersionHistory();

      if (this.versionHistory.length < 2) {
        notifyUserStandard('No previous version to restore', NOTIFICATION_COLORS.INFO, 2000);
        return;
      }

      // Get the second-to-last version (current is the latest)
      const previousVersion = this.versionHistory[1];

      try {
        const headers = this.getAuthHeaders();
        const response = await axios.post(
          `/api/episodes/rundown-item/${assetId}/versions/${previousVersion.version_number}/restore`,
          {},
          { headers }
        );

        if (response.data && response.data.success) {
          notifyUserStandard(`Restored to version ${previousVersion.version_number}`, NOTIFICATION_COLORS.SUCCESS, 2000);

          // Reload the current item to reflect the restored content
          await this.loadEpisode(this.currentEpisodeNumber);

          // Re-select the same item
          const restoredItemIndex = this.rundownItems.findIndex(
            item => (item.asset_id || item.AssetID) === assetId
          );
          if (restoredItemIndex >= 0) {
            await this.selectItem(restoredItemIndex);
          }

          // Refresh version history
          await this.fetchVersionHistory();
        } else {
          notifyUserStandard('Failed to restore version', NOTIFICATION_COLORS.ERROR, 3000);
        }
      } catch (error) {
        console.error('Undo failed:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Undo failed: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
      }
    },

    // Restore to a specific version (used by MetadataPanel)
    async restoreToVersion(versionNumber) {
      if (!this.currentRundownItem) {
        notifyUserStandard('No item selected', NOTIFICATION_COLORS.WARNING, 2000);
        return;
      }

      const assetId = this.currentRundownItem.asset_id || this.currentRundownItem.AssetID;
      if (!assetId) {
        notifyUserStandard('Cannot restore - item has no asset ID', NOTIFICATION_COLORS.WARNING, 2000);
        return;
      }

      try {
        const headers = this.getAuthHeaders();
        const response = await axios.post(
          `/api/episodes/rundown-item/${assetId}/versions/${versionNumber}/restore`,
          {},
          { headers }
        );

        if (response.data && response.data.success) {
          notifyUserStandard(`Restored to version ${versionNumber}`, NOTIFICATION_COLORS.SUCCESS, 2000);

          // Reload the current item to reflect the restored content
          await this.loadEpisode(this.currentEpisodeNumber);

          // Re-select the same item
          const restoredItemIndex = this.rundownItems.findIndex(
            item => (item.asset_id || item.AssetID) === assetId
          );
          if (restoredItemIndex >= 0) {
            await this.selectItem(restoredItemIndex);
          }

          // Refresh version history
          await this.fetchVersionHistory();
        } else {
          notifyUserStandard('Failed to restore version', NOTIFICATION_COLORS.ERROR, 3000);
        }
      } catch (error) {
        console.error('Restore failed:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Restore failed: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
      }
    },

    // Sync rundown order - update order values to match current positions
    async syncRundownOrder() {
      if (!this.rundownItems || this.rundownItems.length === 0) {
        notifyUserStandard('No rundown items to sync', NOTIFICATION_COLORS.WARNING, 2000);
        return;
      }

      try {
        console.log('Starting rundown order sync...');
        
        // Check if any items need order updates
        let needsUpdate = false;
        this.rundownItems.forEach((item, index) => {
          const expectedOrder = (index + 1) * 10;
          if (item.order !== expectedOrder) {
            needsUpdate = true;
          }
        });

        if (!needsUpdate) {
          notifyUserStandard('Order already matches positions', NOTIFICATION_COLORS.INFO, 2000);
          return;
        }

        // Mark as having unsaved changes and save all content
        // The saveAllContent method will automatically update order values to match positions
        this.hasUnsavedChanges = true;
        
        await this.saveAllContent();
        
        notifyUserStandard('Rundown order synchronized!', NOTIFICATION_COLORS.SUCCESS, 2000);
        
      } catch (error) {
        console.error('Error syncing rundown order:', error);
        notifyUserStandard('Failed to sync rundown order', NOTIFICATION_COLORS.ERROR, 3000);
      }
    },

    // Save all rundown items - DATABASE FIRST approach
    async saveAllContent() {
      this.saving = true;
      try {
        const result = await this.saveRundownItems({
          showSuccessMessage: true,
          includCurrentEditorContent: true,
          customMessage: 'All rundown items saved successfully'
        });

        if (!result.success) {
          throw new Error(result.error);
        }

        console.log('✅ All content saved via centralized function');
      } catch (error) {
        console.error('❌ Save all content failed:', error);
        throw error;
      } finally {
        this.saving = false;
      }
    },

    // CENTRALIZED RUNDOWN SAVE FUNCTION - handles index to order synchronization
    async saveRundownItems(options = {}) {
      const {
        showSuccessMessage = true,
        includCurrentEditorContent = true,
        customMessage = null,
        recalculateOrder = false  // Only recalculate on drag-drop or new item creation
      } = options;

      const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
      if (!paddedId || !this.rundownItems || this.rundownItems.length === 0) {
        console.log('Cannot save rundown - no valid episode or rundown items');
        return { success: false, error: 'No valid episode or rundown items' };
      }

      try {
        console.log('🔄 CENTRALIZED RUNDOWN SAVE - Starting...');
        console.log(`Episode: ${paddedId}, Items: ${this.rundownItems.length}, Recalculate Order: ${recalculateOrder}`);

        // STEP 1: CONDITIONAL INDEX-TO-ORDER SYNCHRONIZATION
        const processedItems = this.rundownItems.map((item, index) => {
          const processedItem = { ...item };

          // Only recalculate order if explicitly requested (drag-drop or new item creation)
          if (recalculateOrder) {
            // 🔥 RECALCULATE: Override order field with current array index
            // 🚨 CRITICAL: Cold Open always gets index = 1, regardless of position
            if (item.type === 'coldopen') {
              processedItem.index = 1;
              processedItem.order = 1;
              console.log(`❄️ COLD OPEN Item ${index}: ${item.title} -> Index: 1, Order: 1 (FIXED)`);
            } else {
              processedItem.index = (index + 1) * 10;  // Frontend index (10, 20, 30, 40...)
              processedItem.order = processedItem.index;  // Database order field
              console.log(`🔢 RECALC Item ${index}: ${item.title} -> Index: ${processedItem.index}, Order: ${processedItem.order}`);
            }
          } else {
            // 🔒 PRESERVE: Keep existing order values from database
            // 🚨 CRITICAL: Cold Open always gets index = 1, even in preserve mode
            if (item.type === 'coldopen') {
              processedItem.index = 1;
              processedItem.order = 1;
              console.log(`❄️ COLD OPEN Item ${index}: ${item.title} -> Index: 1, Order: 1 (PRESERVED)`);
            } else {
              // Use !== undefined to handle 0 as valid value (0 is falsy but valid!)
              processedItem.index = (item.index !== undefined && item.index !== null) ? item.index :
                                    (item.order !== undefined && item.order !== null) ? item.order :
                                    (index + 1) * 10;
              processedItem.order = (item.order !== undefined && item.order !== null) ? item.order :
                                    (item.index !== undefined && item.index !== null) ? item.index :
                                    (index + 1) * 10;
              console.log(`🔒 PRESERVE Item ${index}: ${item.title} -> Index: ${processedItem.index}, Order: ${processedItem.order}`);
            }
          }

          // Include current editor content if this is the selected item
          if (includCurrentEditorContent && index === this.selectedItemIndex) {
            processedItem.script = this.parsedContent.scriptContent;
            processedItem.scratch = this.scratchContent;
            processedItem.rawMarkdown = this.rawMarkdownContent;
            console.log(`📝 Including editor content for selected item: ${item.title}`);
          }
          // Note: script preserved on local items for duration calculation

          return processedItem;
        });

        // STEP 2: Build payload - strip script from non-selected items to prevent stale overwrites
        const headers = this.getAuthHeaders();

        const payloadItems = processedItems.map((item, index) => {
          const payloadItem = { ...item };
          if (index !== this.selectedItemIndex) {
            delete payloadItem.script;
            delete payloadItem.scratch;
            delete payloadItem.rawMarkdown;
          }
          return payloadItem;
        });

        const rundownPayload = {
          items: payloadItems,
          episode_number: paddedId,
          save_type: 'manual_save'  // Always manual save for saveRundownItems (creates version history)
        };

        console.log('🚀 Sending to /save-rundown endpoint...');
        const response = await axios.put(`/api/episodes/${paddedId}/save-rundown`, rundownPayload, { headers });

        // STEP 3: Update local state with synchronized data (scripts preserved)
        this.rundownItems = processedItems;
        this.hasUnsavedChanges = false;
        this.hasUnsavedRundownChanges = false;

        // Update master duration from backend calculation
        if (response.data && response.data.total_duration) {
          this.duration = response.data.total_duration;
        }

        console.log('✅ Centralized rundown save completed:', response.data);

        if (showSuccessMessage) {
          const message = customMessage || `Saved ${processedItems.length} rundown items`;
          notifyUserStandard(message, NOTIFICATION_COLORS.SUCCESS, 2000);
        }

        return {
          success: true,
          data: response.data,
          itemsSaved: processedItems.length
        };

      } catch (error) {
        console.error('❌ Centralized rundown save failed:', error);

        if (showSuccessMessage) {
          notifyUserStandard('Failed to save rundown items', NOTIFICATION_COLORS.ERROR, 3000);
        }

        return {
          success: false,
          error: error.message,
          details: error
        };
      }
    },

    // SINGLE SAVE FUNCTION - saves both episode and rundown
    async saveEverything() {
      this.saving = true;
      try {
        console.log('🚀 SAVING EVERYTHING - Episode + Rundown');

        // 1. Save episode metadata first
        await this.saveEpisodeMetadata();
        console.log('✅ Episode metadata saved');

        // 2. Save rundown items with index→order sync
        const rundownResult = await this.saveRundownItems({
          showSuccessMessage: false, // We'll show our own message
          includCurrentEditorContent: true,
          customMessage: null
        });

        if (!rundownResult.success) {
          throw new Error(rundownResult.error);
        }

        console.log('✅ Rundown items saved');

        // Show single success message
        notifyUserStandard(`Episode and rundown saved successfully`, NOTIFICATION_COLORS.SUCCESS, 2000);

      } catch (error) {
        console.error('❌ Save everything failed:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Save failed: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 4000);
        throw error;
      } finally {
        this.saving = false;
      }
    },

    // Save episode metadata - DATABASE FIRST approach
    async saveEpisodeMetadata() {
      const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
      if (!paddedId) {
        console.log('Cannot save episode metadata - no valid episode');
        return;
      }

      try {
        const headers = this.getAuthHeaders();

        const episodeData = {
          title: this.currentEpisodeTitle,
          slug: this.currentEpisodeSlug,
          subtitle: this.currentEpisodeSubtitle,
          description: this.currentEpisodeDescription,
          air_date: this.currentAirDate,
          air_time: this.currentAirTime,
          air_timezone: this.currentAirTimezone,
          duration_formatted: this.duration,
          status: this.currentProductionStatus
        };

        console.log('💾 Saving episode metadata to database...', episodeData);

        const response = await axios.put(`/api/episodes/${paddedId}/save-episode`, episodeData, { headers });
        console.log('✅ Episode metadata saved:', response.data);

        notifyUserStandard('Episode metadata saved', NOTIFICATION_COLORS.SUCCESS, 1500);

      } catch (error) {
        console.error('❌ Episode metadata save failed:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Episode save failed: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
        throw error;
      }
    },

    // Check if any rundown items need saving
    checkForUnsavedRundownChanges() {
      // For now, we'll use simple heuristics to determine if there are unsaved changes
      // In a more sophisticated implementation, we'd track changes per item
      this.hasUnsavedRundownChanges = this.hasUnsavedChanges || this.rundownItems.some(item => {
        // Check if item has indicators of unsaved changes
        return !item.lastSaved || (item.modified && item.modified > item.lastSaved);
      });
    },
    getStatusLabel(status) {
      // TODO: Implement actual logic for status label
      return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
    },
    loadItemContent(item) {
      if (!item) {
        this.isLoadingItemContent = true;
        this.scratchContent = '';
        this.rawMarkdownContent = '';
        this.currentItemMetadata = {};
        this.isLoadingItemContent = false;
        return;
      }

      console.log('🔄 Loading content for item:', item.slug || item.title);
      console.log(`🔄 Item details - ID: ${item.id}, AssetID: ${item.asset_id}, Type: ${item.type}, Order: ${item.order}`);
      console.log('🔄 script length:', item.script?.length || 0);
      console.log('🔄 script preview:', item.script?.substring(0, 200) || '(empty)');

      // Set loading guard to prevent autosave watcher from firing during content load
      this.isLoadingItemContent = true;

      // Load scratch content
      this.scratchContent = item.scratch || '';

      // CRITICAL: Build rawMarkdownContent from item.script (body) + item metadata (frontmatter)
      // Do NOT use item.rawMarkdown - it may contain stale/corrupted frontmatter
      // The loadRawMarkdownContent function rebuilds the complete markdown from clean sources
      this.loadRawMarkdownContent(item);

      console.log('✅ Built rawMarkdownContent, length:', this.rawMarkdownContent?.length || 0);
      
      // Load all frontmatter metadata from the item
      this.currentItemMetadata = {
        // Standard fields
        AssetID: item.AssetID || item.asset_id || '',
        title: item.title || '',
        type: item.type || 'segment',
        slug: item.slug || '',
        subtitle: item.subtitle || '',
        description: item.description || '',
        duration: item.duration || '00:00:00',
        status: item.status || 'draft',
        order: item.order || 1,
        airdate: item.airdate || '',
        priority: item.priority || '',
        guests: item.guests || '',
        resources: item.resources || '',
        tags: item.tags || '',
        server_message: item.server_message || '',
        created_at: item.created_at || '',
        
        // Include any additional custom fields from the item
        ...Object.keys(item).reduce((acc, key) => {
          // Skip standard fields and system fields
          const standardFields = [
            'AssetID', 'asset_id', 'title', 'type', 'slug', 'subtitle', 'description',
            'duration', 'status', 'order', 'airdate', 'priority', 'guests', 'resources', 
            'tags', 'server_message', 'created_at', 'script', 'scratch', 'filename', 'id'
          ];
          
          if (!standardFields.includes(key) && item[key] !== null && item[key] !== undefined) {
            acc[key] = item[key];
          }
          return acc;
        }, {})
      };
      
      console.log('✅ Loaded metadata - AssetID:', this.currentItemMetadata.AssetID, 'Title:', this.currentItemMetadata.title, 'Order:', this.currentItemMetadata.order);
      console.log('Loaded raw content length:', this.rawMarkdownContent.length);

      // Clear loading guard - content is fully loaded, future changes are user edits
      this.$nextTick(() => {
        this.isLoadingItemContent = false;
        this.hasUnsavedChanges = false;
        console.log('🔓 Content load complete - autosave re-enabled');
      });
    },

    async reloadCurrentItemContent() {
      // Reload the currently selected item from the server (for processing updates)
      if (this.selectedItemIndex < 0 || !this.currentEpisodeNumber) {
        console.log('Cannot reload - no valid item selected')
        return
      }

      try {
        console.log('🔄 Reloading current item content from server...')
        const response = await axios.get(`/api/episodes/${this.currentEpisodeNumber}/rundown`)
        const items = response.data.items || []

        if (this.selectedItemIndex < items.length) {
          const updatedItem = items[this.selectedItemIndex]

          // Update in rundownItems array
          this.rundownItems[this.selectedItemIndex] = updatedItem

          // Force EditorPanel to re-parse segments for updated content
          if (this.$refs.editorPanel) {
            this.$refs.editorPanel.segmentReparseKey++
          }

          // Reload into editor
          this.loadItemContent(updatedItem)

          console.log('✅ Current item content reloaded')
        }
      } catch (error) {
        console.error('Failed to reload current item:', error)
      }
    },

    loadRawMarkdownContent(item) {
      // Load script content directly - NO frontmatter injection
      // Metadata is available via item object, no need to embed in content
      try {
        // Get script content and strip any legacy frontmatter if present
        let scriptContent = item.script || '';
        let strippingIterations = 0;
        const maxIterations = 5; // Safety limit to prevent infinite loops

        // Strip any existing frontmatter (legacy/corrupted data cleanup)
        // Detect both '---' and '- - -' (sanitized) frontmatter delimiters
        const isFrontmatterDelimiter = (line) => {
          const t = line.trim();
          return t === '---' || t === '- - -';
        };
        while ((scriptContent.trim().startsWith('---') || scriptContent.trim().startsWith('- - -')) && strippingIterations < maxIterations) {
          strippingIterations++;
          console.warn(`🧹 Stripping legacy frontmatter (iteration ${strippingIterations})`);

          const lines = scriptContent.split('\n');
          let frontmatterEndIndex = -1;
          let dashCount = 0;

          for (let i = 0; i < lines.length; i++) {
            if (isFrontmatterDelimiter(lines[i])) {
              dashCount++;
              if (dashCount === 2) {
                frontmatterEndIndex = i;
                break;
              }
            }
          }

          if (frontmatterEndIndex > -1) {
            scriptContent = lines.slice(frontmatterEndIndex + 1).join('\n').trim();
          } else {
            break;
          }
        }

        if (strippingIterations > 0) {
          console.log(`✅ Cleaned ${strippingIterations} frontmatter block(s) from content`);
        }

        // REMOVED: Duplicate content detection was causing false positives
        // and permanently truncating legitimate content (refrains, repeated intros).
        // The autosave watcher would then save the truncated version back to the DB.
        // If duplicate content is a problem, it should be handled as a UI warning,
        // NOT by silently modifying the content on load.

        // Set content directly - no frontmatter wrapper
        this.rawMarkdownContent = scriptContent;

      } catch (error) {
        console.error('Error loading raw markdown content:', error);
        this.rawMarkdownContent = item.script || '';
      }
    },
    
    async saveRundownOrder() {
      const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
      if (!paddedId) return;
      
      try {
        // Prepare the reorder request with updated order fields
        const segments = this.rundownItems.map((item, index) => ({
          filename: item.filename, // Use the actual filename from the rundown item
          order: (index + 1) * 10
        }));
        
        const payload = { segments };

        // Call the reorder endpoint with authentication
        const reorderHeaders = this.getAuthHeaders();

        await axios.post(`/rundown/${paddedId}/reorder`, payload, { headers: reorderHeaders });
        console.log('Rundown order saved successfully');
        this.hasUnsavedChanges = false;
        notifyUserStandard("Rundown order saved", NOTIFICATION_COLORS.SUCCESS, 1500);
      } catch (error) {
        console.error('Failed to save rundown order:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Save Failed: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
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
    
    async handleRundownReorder(reorderData) {
      // CRITICAL: Flush any pending edits before reordering to prevent data loss
      if (this.$refs.editorPanel?.flushPendingChanges) {
        console.log('💾 Flushing pending changes before reorder...');
        await this.$refs.editorPanel.flushPendingChanges();
        await this.$nextTick();
      }

      // Handle both formats: object {oldIndex, newIndex, items} or simple array
      let oldIndex, newIndex, items;

      if (Array.isArray(reorderData)) {
        // Simple array format from cross-region moves
        items = reorderData;
        oldIndex = undefined;
        newIndex = undefined;
        console.log(`Reordering: updating ${items.length} items from cross-region drag`);
      } else {
        // Object format from within-region moves
        ({ oldIndex, newIndex, items } = reorderData);
        console.log(`Reordering: moving item from index ${oldIndex} to ${newIndex}`);
      }

      // Safety check: ensure items is valid before updating
      if (!items || !Array.isArray(items)) {
        console.error('❌ Invalid items data in handleRundownReorder:', items);
        return;
      }

      // 🔥 CRITICAL FIX: Do NOT replace rundownItems with stale data from RundownPanel!
      // RundownPanel's items don't have the latest content edits.
      // Instead, reorder our existing items based on the new positions.
      console.log('🔄 Reordering items while preserving content...');

      // Create a map of asset_id -> current item (with fresh content)
      const currentItemsMap = new Map();
      for (const item of this.rundownItems) {
        const id = item.asset_id || item.AssetID || item.id;
        if (id) {
          currentItemsMap.set(id, item);
        }
      }

      // Reorder using the new positions but preserve content from current items
      const reorderedItems = items.map((newItem, newIndex) => {
        const id = newItem.asset_id || newItem.AssetID || newItem.id;
        const existingItem = currentItemsMap.get(id);

        if (existingItem) {
          // Use existing item (has current content) but update position fields
          return {
            ...existingItem,
            index: (newIndex + 1) * 10,
            order: (newIndex + 1) * 10,
            order_in_rundown: (newIndex + 1) * 10,
            regionId: newItem.regionId  // Preserve region assignment from drag
          };
        } else {
          // Fallback: use the new item if we can't find existing (shouldn't happen)
          console.warn(`⚠️ Could not find existing item for ${id}, using RundownPanel data`);
          return {
            ...newItem,
            index: (newIndex + 1) * 10,
            order: (newIndex + 1) * 10,
            order_in_rundown: (newIndex + 1) * 10
          };
        }
      });

      this.rundownItems = reorderedItems;
      console.log(`✅ Reordered ${reorderedItems.length} items while preserving content`);

      // Mark as having unsaved changes
      this.hasUnsavedChanges = true;
      
      // Save the new order to the backend
      try {
        await this.saveRundownItems({
          showSuccessMessage: true,
          includCurrentEditorContent: false,
          customMessage: 'Rundown reorder saved successfully',
          recalculateOrder: true  // Recalculate order after drag-drop
        });
        console.log('Rundown reorder saved successfully');
        
        // Update selected item index if necessary (only for within-region moves)
        if (oldIndex !== undefined && newIndex !== undefined) {
          if (this.selectedItemIndex === oldIndex) {
            this.selectedItemIndex = newIndex;
          } else if (this.selectedItemIndex > oldIndex && this.selectedItemIndex <= newIndex) {
            this.selectedItemIndex--;
          } else if (this.selectedItemIndex < oldIndex && this.selectedItemIndex >= newIndex) {
            this.selectedItemIndex++;
          }
        }
        
        // Show success feedback attached to rundown panel
        const panelElement = this.$refs.rundownPanelRef?.$el;
        notifyUserStandard("Rundown order updated", NOTIFICATION_COLORS.SUCCESS, 1500, panelElement, true);
        
      } catch (error) {
        console.error('Failed to save rundown reorder:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        const panelElement = this.$refs.rundownPanelRef?.$el;
        notifyUserStandard(`Failed to save reorder: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000, panelElement, true);
        
        // Optionally revert the local changes
        // this.fetchRundownItems();
      }
    },
    
    async selectRundownItem(index) {
      console.log('🎯 Selecting rundown item at index:', index);
      console.log('Current selectedItemIndex before update:', this.selectedItemIndex);
      console.log('Total rundown items:', this.rundownItems.length);

      // CRITICAL: Save current item before switching to prevent data loss
      if (this.selectedItemIndex >= 0 && this.selectedItemIndex !== index) {
        // STEP 1: Flush any pending edits from EditorPanel's debounce buffer
        // This ensures typed content that hasn't been emitted yet is captured
        if (this.$refs.editorPanel?.flushPendingChanges) {
          console.log('💾 Flushing pending editor changes before switch...');
          // CRITICAL: Must await the flush to ensure emit is processed before checking hasUnsavedChanges
          await this.$refs.editorPanel.flushPendingChanges();
          // Extra tick to ensure parent's updateScriptContent has processed the emit
          await this.$nextTick();
          console.log('💾 Flush complete, hasUnsavedChanges:', this.hasUnsavedChanges);
        }

        // STEP 2: Now save if there are unsaved changes (including freshly flushed ones)
        if (this.hasUnsavedChanges) {
          console.log('💾 Saving current item before switching...');
          try {
            await this.saveCurrentItem();
            console.log('✅ Successfully saved before switching');
          } catch (error) {
            console.error('❌ Failed to save before switching:', error);
            // Continue with switch even if save fails - user will see unsaved changes warning
          }
        }
      }

      // Clear undo/redo stacks when switching items (undo is item-specific)
      if (this.selectedItemIndex !== index) {
        this.clearUndoStacks();
      }

      // Unregister previous active edit and release lock
      if (this.selectedItemIndex >= 0 && this.rundownItems[this.selectedItemIndex]) {
        const prevAssetId = this.rundownItems[this.selectedItemIndex].asset_id;
        if (prevAssetId) {
          // Release segment lock first
          if (this.segmentLockState && this.segmentLockState.currentAssetId.value === prevAssetId) {
            try {
              await this.segmentLockState.releaseLock();
              console.log('🔓 Released segment lock for', prevAssetId);
            } catch (err) {
              console.warn('Failed to release segment lock:', err);
            }
          }
          // Unregister active edit
          try {
            await axios.post('/api/housekeeping/active-edit/unregister',
              { asset_id: prevAssetId },
              { headers: this.getAuthHeaders() }
            );
          } catch (err) {
            console.warn('Failed to unregister active edit:', err);
          }
        }
      }

      // CRITICAL FIX: Force-clear EditorPanel's editing flags before switching items.
      // If isActivelyEditing is still true (e.g., blur didn't fire before click on touch devices),
      // the scriptContent watcher in EditorPanel would be bypassed, leaving stale cached segments
      // from the previous item. This caused cross-item content contamination (Bug #4).
      const editorPanelRef = this.$refs.editorPanel;
      if (editorPanelRef) {
        editorPanelRef.isActivelyEditing = false;
        editorPanelRef.isRestoringCursor = false;
        editorPanelRef.activelyEditingSegment = null;
        editorPanelRef.cachedScriptSegments = null;
        editorPanelRef.lastParsedContent = null;
        editorPanelRef.segmentEditBuffer = {};
        // CRITICAL: Increment reparseKey to guarantee scriptSegments re-evaluates.
        // The manual cache in scriptSegments can get stale due to side-effect-based caching
        // interacting with Vue's async reactivity batching. This counter creates an explicit
        // dependency that forces fresh parsing regardless of cache state.
        editorPanelRef.segmentReparseKey++;
        console.log('🧹 Cleared EditorPanel editing flags and segment cache for clean item switch (reparseKey:', editorPanelRef.segmentReparseKey, ')');
      }

      this.selectedItemIndex = index;
      console.log('Updated selectedItemIndex to:', this.selectedItemIndex);

      // Save selected item index to sessionStorage for persistence
      if (index >= 0) {
        const sessionKey = `selectedItem_${this.currentEpisodeNumber}`;
        sessionStorage.setItem(sessionKey, index.toString());
        console.log(`Saved selected item index ${index} to session for episode ${this.currentEpisodeNumber}`);
      } else {
        // Clear selection from session if index is -1
        const sessionKey = `selectedItem_${this.currentEpisodeNumber}`;
        sessionStorage.removeItem(sessionKey);
      }

      // Load content for the newly selected item
      if (index >= 0 && index < this.rundownItems.length) {
        const itemToLoad = this.rundownItems[index];
        console.log('🔍 Loading item at index', index, ':', itemToLoad?.title || itemToLoad?.slug);
        this.loadItemContent(itemToLoad);

        // Reset scroll position to top when switching items
        this.$nextTick(() => {
          const scrollWrapper = document.querySelector('.scrollable-content-wrapper');
          if (scrollWrapper) {
            scrollWrapper.scrollTop = 0;
            console.log('📜 Reset scroll to top for new item');
          }
        });

        // Fetch version history for undo functionality
        this.fetchVersionHistory();

        // Register new active edit
        const newAssetId = itemToLoad.asset_id;
        if (newAssetId) {
          try {
            await axios.post('/api/housekeeping/active-edit/register',
              { asset_id: newAssetId },
              { headers: this.getAuthHeaders() }
            );
            console.log('✅ Registered active edit for', newAssetId);
          } catch (err) {
            console.warn('Failed to register active edit:', err);
          }

          // Try to acquire segment lock
          if (this.segmentLockState) {
            const lockResult = await this.segmentLockState.acquireLock(newAssetId);
            if (lockResult.success) {
              console.log('🔒 Acquired segment lock for', newAssetId);
            } else if (lockResult.locked) {
              console.log('🔒 Segment locked by:', lockResult.lockedBy);
              // Lock info is automatically updated in segmentLockState
            }
          }
        }
      } else {
        this.loadItemContent(null);
      }
    },

    // Navigate to next rundown item (arrow down)
    selectNextRundownItem() {
      if (this.rundownItems.length === 0) return;

      const nextIndex = this.selectedItemIndex === -1
        ? 0  // If nothing selected, select first item
        : Math.min(this.selectedItemIndex + 1, this.rundownItems.length - 1);

      if (nextIndex !== this.selectedItemIndex) {
        this.selectRundownItem(nextIndex);
      }
    },

    // Navigate to previous rundown item (arrow up)
    selectPreviousRundownItem() {
      if (this.rundownItems.length === 0) return;

      const prevIndex = this.selectedItemIndex === -1
        ? 0  // If nothing selected, select first item
        : Math.max(this.selectedItemIndex - 1, 0);

      if (prevIndex !== this.selectedItemIndex) {
        this.selectRundownItem(prevIndex);
      }
    },

    // Focus on the first editable element of current item (Enter key)
    focusCurrentItem() {
      if (this.selectedItemIndex === -1 || !this.currentRundownItem) {
        return;
      }

      this.$nextTick(() => {
        // Get the EditorPanel component reference and its DOM element
        const editorPanelComponent = this.$refs.editorPanel;
        const editorPanelElement = editorPanelComponent?.$el || document.querySelector('.editor-panel');

        if (!editorPanelElement || typeof editorPanelElement.querySelector !== 'function') {
          // Fallback: search entire document for textarea
          const textarea = document.querySelector('.editor-panel textarea');
          if (textarea) {
            textarea.focus();
          }
          return;
        }

        // Look for textareas in priority order
        const scriptTextarea = editorPanelElement.querySelector('.code-textarea textarea') ||
                              editorPanelElement.querySelector('.speaker-textarea') ||
                              editorPanelElement.querySelector('textarea');

        if (scriptTextarea) {
          scriptTextarea.focus();
        }
      });
    },

    toggleRundownWidth() {
      this.rundownPanelWidth = this.rundownPanelWidth === 'narrow' ? 'wide' : 'narrow';
      console.log('Rundown panel width toggled to:', this.rundownPanelWidth);
    },

    toggleMetadataWidth() {
      this.metadataPanelWidth = this.metadataPanelWidth === 'narrow' ? 'wide' : 'narrow';
      console.log('Metadata panel width toggled to:', this.metadataPanelWidth);
    },

    // Calculate available height for side panels based on how much header is visible
    updateSidePanelHeight() {
      const wrapper = this._scrollWrapper;
      const header = this._headerEl;
      if (!wrapper) return;
      const viewportHeight = wrapper.clientHeight;
      const headerHeight = header ? header.offsetHeight : 0;
      const scrollTop = wrapper.scrollTop;
      // How much of the header is still visible in the scroll viewport
      const headerVisible = Math.max(0, headerHeight - scrollTop);
      this.sidePanelHeight = viewportHeight - headerVisible;
    },

    handleMetadataFieldUpdate({ field, value }) {
      if (this.currentRundownItem) {
        console.log(`Updating field ${field} to:`, value);
        this.currentRundownItem[field] = value;
        this.hasUnsavedChanges = true;
        
        // Update the rundown item in the array as well
        if (this.selectedItemIndex >= 0 && this.rundownItems[this.selectedItemIndex]) {
          this.rundownItems[this.selectedItemIndex][field] = value;
        }
      }
    },

    resetMetadataFields() {
      // Reload the current item from the server or reset to last saved state
      if (this.selectedItemIndex >= 0) {
        this.selectRundownItem(this.selectedItemIndex);
        notifyUserStandard('Metadata fields reset', NOTIFICATION_COLORS.INFO, 1500);
      }
    },
    
    handleKeydown(event) {
      // Allow space key to pass through to contenteditable elements
      if ((event.key === ' ' || event.code === 'Space') && event.target.isContentEditable) {
        return;
      }

      // Check if user is in editing mode (focused on input/textarea/contenteditable)
      const isInTextField = ['INPUT', 'TEXTAREA'].includes(event.target.tagName) ||
                            event.target.isContentEditable;

      // Check if any modal is open
      const hasModalOpen = this.showImgCueModal || this.showGfxModal || this.showFsqModal ||
                           this.showSotModal || this.showVoModal || this.showNatModal ||
                           this.showPkgModal || this.showVoxModal || this.showMusModal ||
                           this.showLiveModal || this.showNewItemModal || this.showNewGFXModal ||
                           this.showNewSOTModal || this.showDeleteCueModal ||
                           this.showAssetBrowserModal || this.showTemplateManagerModal ||
                           this.showBumpModal || this.showStingModal || this.showDirModal ||
                           this.showRifModal;

      // UNDO (Ctrl+Z / Cmd+Z) - Works in all modes, including text fields
      if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        event.stopPropagation();
        this.undo();
        return;
      }

      // REDO (Ctrl+Y / Cmd+Y or Ctrl+Shift+Z / Cmd+Shift+Z)
      if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.key === 'z' && event.shiftKey) || (event.key === 'Z' && event.shiftKey))) {
        event.preventDefault();
        event.stopPropagation();
        this.redo();
        return;
      }

      // ESCAPE KEY - Close modal if one is open, otherwise exit editing mode
      if (event.key === 'Escape') {
        if (hasModalOpen) {
          event.preventDefault();
          event.stopPropagation();
          event.stopImmediatePropagation();  // Prevent other handlers from also processing ESC
          console.log('🚨 ESC pressed with modal open - closing modal only (not leaving segment)');

          // Close whichever modal is open
          this.showImgCueModal = false;
          this.showGfxModal = false;
          this.showFsqModal = false;
          this.showSotModal = false;
          this.showVoModal = false;
          this.showNatModal = false;
          this.showPkgModal = false;
          this.showVoxModal = false;
          this.showMusModal = false;
          this.showLiveModal = false;
          this.showNewItemModal = false;
          this.showNewGFXModal = false;
          this.showNewSOTModal = false;
          this.showDeleteCueModal = false;
          this.showAssetBrowserModal = false;
          this.showTemplateManagerModal = false;
          this.showBumpModal = false;
          this.showStingModal = false;
          this.showDirModal = false;
          this.showRifModal = false;

          return;
        }

        // No modal open - handle normal escape behavior
        if (isInTextField) {
          event.preventDefault();
          event.target.blur(); // Remove focus from editor
          console.log('🚪 Exited editing mode - returned to rundown navigation');

          // CRITICAL: Flush and save any pending changes when user presses ESC
          // This provides an explicit "I'm done editing" checkpoint
          if (this.$refs.editorPanel?.flushPendingChanges) {
            this.$refs.editorPanel.flushPendingChanges();
          }
          // Save after flush (async, don't await - let it happen in background)
          this.$nextTick(() => {
            if (this.hasUnsavedChanges) {
              this.saveCurrentItem().then(() => {
                console.log('💾 Auto-saved on ESC');
              }).catch(err => {
                console.error('Failed to auto-save on ESC:', err);
              });
            }
          });
          return;
        }
        // If not in text field, allow other Escape handlers (like multi-select cancel)
      }

      // ARROW DOWN - Navigate to next rundown item (navigation mode only)
      if (event.key === 'ArrowDown' && !isInTextField && !hasModalOpen) {
        event.preventDefault();
        this.selectNextRundownItem();
        return;
      }

      // ARROW UP - Navigate to previous rundown item (navigation mode only)
      if (event.key === 'ArrowUp' && !isInTextField && !hasModalOpen) {
        event.preventDefault();
        this.selectPreviousRundownItem();
        return;
      }

      // ENTER KEY - Enter editing mode for selected item (navigation mode only)
      if (event.key === 'Enter' && !isInTextField && !hasModalOpen) {
        event.preventDefault();
        this.focusCurrentItem();
        return;
      }

      // Handle Ctrl+Shift+S for saving everything
      if (event.ctrlKey && event.shiftKey && event.key === 'S' && !event.altKey && !event.metaKey) {
        event.preventDefault();
        this.saveEverything();
        return;
      }

      // Handle Ctrl+Z for undo (restore to previous version)
      if (event.ctrlKey && !event.shiftKey && event.key === 'z' && !event.altKey && !event.metaKey) {
        // Only intercept Ctrl+Z when NOT in a text field (allow browser undo in text fields)
        if (!isInTextField) {
          event.preventDefault();
          this.undoLastChange();
          return;
        }
      }

      // Handle Ctrl+Shift+R for reloading rundown from database
      if (event.ctrlKey && event.shiftKey && event.key === 'R' && !event.altKey && !event.metaKey) {
        event.preventDefault();
        console.log('🔄 Ctrl+Shift+R: Reloading rundown from database...');
        this.reloadFromDatabase();
        return;
      }
      // Handle Ctrl+Shift+I for new item
      if (event.ctrlKey && event.shiftKey && event.key === 'I' && !event.altKey && !event.metaKey) {
        event.preventDefault();
        this.handleNewItemClick();
        return;
      }
      // Handle Shift+Delete for deleting cue at cursor (changed from Alt+D to free up Alt+D for DIR cue)
      if (event.shiftKey && event.key === 'Delete' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        // Only trigger if in a textarea (text editor)
        if (event.target.tagName === 'TEXTAREA') {
          event.preventDefault();
          this.deleteCueAtCursor(event.target);
        }
      }
      // Handle Alt+D for NOTE cue
      else if (event.altKey && event.key === 'd' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showDirModal = true;
      }
      // Handle Alt+B for BUMP (Bumper) cue
      else if (event.altKey && event.key === 'b' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showBumpModal = true;
      }
      // Handle Alt+R for STING (Stinger) cue
      else if (event.altKey && event.key === 'r' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showStingModal = true;
      }
      // Handle Alt+G for GFX cue modal
      else if (event.altKey && event.key === 'g' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showGfxModal = true;
      }
      // Handle Alt+S for SOT cue - works globally, even in text fields
      else if (event.altKey && event.key === 's' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        event.stopPropagation();
        this.handleShowSotModal();
      }
      // Handle Alt+Q for creating FSQ (Full Screen Quote) cue
      // NOTE: ALT+Q is now handled by EditorPanel.vue with placement overlay workflow
      // Removed duplicate handler to prevent conflicts
      // Handle Alt+I for IMG cue
      else if (event.altKey && event.key === 'i' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showImgCueModal = true;
      }
      // Handle Alt+V for VO (Voice Over) cue
      else if (event.altKey && event.key === 'v' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showVoModal = true;
      }
      // Handle Alt+N for NAT (Natural Sound) cue
      else if (event.altKey && event.key === 'n' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showNatModal = true;
      }
      // Handle Alt+P for PKG (Package) cue
      else if (event.altKey && event.key === 'p' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        this.showPkgModal = true;
      }
      // Handle Ctrl+Alt+Shift+Number for test segment generation (developer tool)
      else if (event.ctrlKey && event.altKey && event.shiftKey && /^Digit[1-9]$/.test(event.code)) {
        event.preventDefault();
        const paragraphCount = parseInt(event.code.replace('Digit', ''));
        console.log('🧪 Generating test segment with', paragraphCount, 'paragraphs');
        this.generateTestSegment(paragraphCount);
      }
      // Handle Delete key for deleting selected rundown item
      else if (event.key === 'Delete' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        // Only trigger if NOT in any editable field (INPUT, TEXTAREA, or contenteditable)
        // CRITICAL: Must check isInTextField to avoid deleting segment when user is editing text
        // CRITICAL: Must also check hasModalOpen to prevent accidental deletion when modal is open
        // (e.g., if user accidentally presses Delete while focused on video player in SotModal)
        if (!isInTextField && !hasModalOpen) {
          event.preventDefault();
          this.deleteSelectedItem();
        }
      }
    },
    
    async deleteSelectedItem(itemToDelete = null) {
      // CRITICAL: Capture undo state before destructive operation
      this.captureUndoState();

      console.log('=== DELETE BY ASSET_ID START ===');
      console.log('selectedItemIndex:', this.selectedItemIndex);
      console.log('rundownItems length:', this.rundownItems.length);
      console.log('itemToDelete parameter:', itemToDelete);

      // Use passed item or fall back to current selection
      const item = itemToDelete || this.currentRundownItem;

      if (!item) {
        console.log('No item to delete (no parameter and no selection)');
        return;
      }

      // Find the index of the item to delete in rundownItems
      const itemIndex = this.rundownItems.findIndex(i =>
        (i.id && i.id === item.id) ||
        (i.slug && i.slug === item.slug) ||
        (i.asset_id && i.asset_id === item.asset_id)
      );

      if (itemIndex === -1) {
        console.error('Item not found in rundownItems array:', item);
        return;
      }

      // Get asset_id - this is the reliable unique identifier
      const assetId = item.asset_id || item.id;
      if (!assetId) {
        console.error('No asset_id found for item:', item);
        alert('Cannot delete item: missing asset_id');
        return;
      }

      const episodeNumber = this.padEpisodeNumber(this.currentEpisodeNumber);

      console.log('Deleting item by asset_id:', {
        assetId,
        slug: item.slug,
        title: item.title,
        index: itemIndex
      });

      // Confirmation already handled by RundownPanel modal

      try {
        // Get authentication headers using existing helper
        const headers = this.getAuthHeaders();

        // DELETE BY ASSET_ID - Database-first approach (more robust)
        const response = await fetch(`/api/episodes/${episodeNumber}/rundown/by-asset-id/${assetId}`, {
          method: 'DELETE',
          headers
        });

        if (response.ok) {
          const result = await response.json();
          console.log('Delete response:', result);

          const deletedIndex = itemIndex;

          // Remove from local rundownItems array
          this.rundownItems.splice(itemIndex, 1);

          // Smart selection after deletion (only if deleting current selection)
          if (itemToDelete === null || itemIndex === this.selectedItemIndex) {
            if (this.rundownItems.length === 0) {
              // No items left
              this.selectedItemIndex = -1;
              this.scratchContent = '';
              this.rawMarkdownContent = '';
            } else {
              // Select the next logical item
              if (deletedIndex >= this.rundownItems.length) {
                // Deleted the last item, select the new last item
                this.selectedItemIndex = this.rundownItems.length - 1;
              } else {
                // Select the item that moved into the deleted position
                this.selectedItemIndex = deletedIndex;
              }

              // Load content for the newly selected item
              if (this.selectedItemIndex >= 0 && this.rundownItems[this.selectedItemIndex]) {
                this.loadItemContent(this.rundownItems[this.selectedItemIndex]);
              }
            }
          } else {
            // Deleting a different item, adjust selectedItemIndex if needed
            if (this.selectedItemIndex > itemIndex) {
              this.selectedItemIndex--;
            }
          }

          console.log(`✅ Deleted item: ${item.slug || item.title} (asset_id: ${assetId})`);

          // Recalculate order for remaining items after deletion
          await this.saveRundownItems({
            showSuccessMessage: false,
            includCurrentEditorContent: false,
            recalculateOrder: true  // Recalculate order after deletion
          });
          console.log('✅ Rundown order recalculated after deletion');
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
          console.error('Failed to delete item:', errorData);
          alert(`Failed to delete item: ${errorData.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error deleting item:', error);
        alert('An error occurred while deleting the item.');
      }
    },

    // Handle individual item deletion from RundownPanel
    async handleDeleteItem(data) {
      console.log('Delete item event received:', data);

      // Data can be either an item object (from multi-select) or structured data with itemIndex
      if (data.itemIndex !== undefined && data.itemIndex >= 0) {
        // Old format: structured data with itemIndex
        this.selectedItemIndex = data.itemIndex;
        await this.deleteSelectedItem();
      } else {
        // New format: item object directly (from multi-select deletion)
        await this.deleteSelectedItem(data);
      }
    },

    // Handle region deletion from RundownPanel
    async handleDeleteRegion(data) {
      console.log('Delete region event received:', data);

      if (!data.items || !Array.isArray(data.items)) {
        console.error('Invalid region data for deletion');
        return;
      }

      // Confirmation already handled by RundownPanel modal

      try {
        // Delete items in reverse order to maintain proper indices
        for (let i = data.items.length - 1; i >= 0; i--) {
          const item = data.items[i];
          this.selectedItemIndex = item.index || i;
          await this.deleteSelectedItem();
        }

        notifyUserStandard(`Deleted region "${data.regionName}" with ${data.items.length} items`, NOTIFICATION_COLORS.SUCCESS, 3000);
      } catch (error) {
        console.error('Error deleting region:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Failed to delete region: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
      }
    },

    // Handle rundown cleared event from RundownPanel
    async handleRundownCleared() {
      console.log('Rundown cleared event received');

      try {
        // Reload the episode data to reflect the cleared rundown
        await this.loadEpisodeData();

        // Clear any selected items
        this.selectedItemIndex = null;

        // Show success message
        notifyUserStandard('Entire rundown cleared successfully', NOTIFICATION_COLORS.SUCCESS, 3000);

      } catch (error) {
        console.error('Error reloading episode after rundown clear:', error);
        notifyUserStandard('Rundown cleared but failed to reload data', NOTIFICATION_COLORS.WARNING, 3000);
      }
    },

    // Delete cue at cursor position (Alt+D)
    deleteCueAtCursor(textarea) {
      const cursorPos = textarea.selectionStart;
      const text = textarea.value;
      const lines = text.split('\n');
      
      // Find the line where the cursor is
      let currentLine = 0;
      let charCount = 0;
      
      for (let i = 0; i < lines.length; i++) {
        if (charCount + lines[i].length >= cursorPos) {
          currentLine = i;
          break;
        }
        charCount += lines[i].length + 1; // +1 for newline character
      }
      
      console.log('Cursor at line:', currentLine, 'Line content:', lines[currentLine]);
      
      // Find cue boundaries from current line
      const cueInfo = this.findCueBlockBoundaries(lines, currentLine);
      if (!cueInfo) {
        alert('No cue block found at cursor position');
        return;
      }
      
      console.log('Found cue block:', cueInfo);
      
      // Extract cue data for the confirmation modal
      const cueData = this.parseCueData(lines, cueInfo.startLine, cueInfo.endLine);
      
      // Show confirmation modal
      this.selectedCueData = cueData;
      this.selectedCueStartLine = cueInfo.startLine;
      this.selectedCueEndLine = cueInfo.endLine;
      this.showDeleteCueModal = true;
    },

    // Find cue block boundaries starting from current line
    findCueBlockBoundaries(lines, currentLine) {
      let startLine = -1;
      let endLine = -1;
      
      // Search upward from current line to find "<!-- Begin Cue -->"
      for (let i = currentLine; i >= 0; i--) {
        const line = lines[i].trim();
        if (line === '<!-- Begin Cue -->') {
          startLine = i;
          break;
        }
        // If we hit "<!-- End Cue -->" first, we weren't in a cue block
        if (line === '<!-- End Cue -->') {
          console.log('Found End Cue before Begin Cue - cursor not in cue block');
          return null;
        }
      }
      
      if (startLine === -1) {
        console.log('No Begin Cue found - cursor not in cue block');
        return null;
      }
      
      // Search downward from start line to find "<!-- End Cue -->"
      for (let i = startLine + 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line === '<!-- End Cue -->') {
          endLine = i;
          break;
        }
      }
      
      if (endLine === -1) {
        console.log('No End Cue found - malformed cue block');
        return null;
      }
      
      return { startLine, endLine };
    },

    // Parse cue data from lines between start and end
    parseCueData(lines, startLine, endLine) {
      const cueData = {
        type: '',
        assetId: '',
        slug: '',
        description: '',
        mediaUrl: '',
        credit: '',
        caption: ''
      };
      
      // Parse each line for cue properties
      for (let i = startLine + 1; i < endLine; i++) {
        const line = lines[i].trim();
        
        // Match pattern [Property: Value]
        const match = line.match(/^\[([^:]+):\s*(.+)\]$/);
        if (match) {
          const property = match[1].toLowerCase();
          const value = match[2];
          
          switch (property) {
            case 'type':
              cueData.type = value;
              break;
            case 'assetid':
              cueData.assetId = value;
              break;
            case 'slug':
              cueData.slug = value;
              break;
            case 'description':
              cueData.description = value;
              break;
            case 'mediaurl':
              cueData.mediaUrl = value;
              break;
            case 'credit':
              cueData.credit = value;
              break;
            case 'caption':
              cueData.caption = value;
              break;
          }
        }
      }
      
      return cueData;
    },

    // Delete the confirmed cue block
    deleteCue(deleteInfo) {
      // CRITICAL: Capture undo state before destructive operation
      this.captureUndoState();

      console.log('Deleting cue:', deleteInfo);

      // Find the textarea that was active
      const textareas = document.querySelectorAll('textarea');
      let activeTextarea = null;
      
      for (const textarea of textareas) {
        if (document.activeElement === textarea || textarea.matches(':focus')) {
          activeTextarea = textarea;
          break;
        }
      }
      
      if (!activeTextarea) {
        // If no active textarea, try to find the script or scratch textarea
        const scriptTextarea = document.querySelector('.script-textarea textarea');
        const scratchTextarea = document.querySelector('.scratch-mode textarea');
        const codeTextarea = document.querySelector('.code-textarea textarea');
        activeTextarea = scriptTextarea || scratchTextarea || codeTextarea;
      }
      
      if (!activeTextarea) {
        console.error('No textarea found for deletion');
        return;
      }
      
      const text = activeTextarea.value;
      const lines = text.split('\n');
      
      // Remove lines from startLine to endLine (inclusive)
      lines.splice(deleteInfo.startLine, deleteInfo.endLine - deleteInfo.startLine + 1);
      
      // Update the textarea content
      activeTextarea.value = lines.join('\n');
      
      // Trigger change event to update the component's data
      const event = new Event('input', { bubbles: true });
      activeTextarea.dispatchEvent(event);
      
      // Mark as having unsaved changes
      this.hasUnsavedChanges = true;
      
      console.log('Cue block deleted successfully');
    },

    // Cancel delete cue modal
    cancelDeleteCue() {
      this.showDeleteCueModal = false;
      this.selectedCueData = {};
      this.selectedCueStartLine = 0;
      this.selectedCueEndLine = 0;
    },

    // Vue.Draggable event handlers for drag and drop
    onDragStart(event) {
      console.log('Drag started:', event.oldIndex);
      this.dragStartIndex = event.oldIndex;
    },

    async onDragEnd(event) {
      console.log('Drag ended:', event.oldIndex, '->', event.newIndex);

      // Only process if the position actually changed
      if (event.oldIndex !== event.newIndex) {
        console.log('Position changed, saving rundown order');

        // Update selected index if necessary
        if (this.selectedItemIndex === event.oldIndex) {
          this.selectedItemIndex = event.newIndex;
        } else if (this.selectedItemIndex > event.oldIndex && this.selectedItemIndex <= event.newIndex) {
          this.selectedItemIndex--;
        } else if (this.selectedItemIndex < event.oldIndex && this.selectedItemIndex >= event.newIndex) {
          this.selectedItemIndex++;
        }

        // 🔥 CRITICAL FIX: Await save and provide user feedback
        const result = await this.saveRundownItems({
          showSuccessMessage: false,
          includCurrentEditorContent: false,
          customMessage: null,
          recalculateOrder: true  // Recalculate order after drag-drop
        });

        if (result.success) {
          this.hasUnsavedChanges = false;
          // Show notification attached to rundown panel
          const panelElement = this.$refs.rundownPanelRef?.$el;
          notifyUserStandard("Rundown reordered", NOTIFICATION_COLORS.SUCCESS, 1500, panelElement, true);
        } else {
          const errorMsg = result.error || 'Unknown error';
          const panelElement = this.$refs.rundownPanelRef?.$el;
          notifyUserStandard(`Failed to save reorder: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000, panelElement, true);
          console.error('❌ Drag-and-drop save failed:', result);
        }
      }

      this.dragStartIndex = -1;
    },
    
    
    onRawMarkdownChange(content) {
      this.rawMarkdownContent = content;
      this.hasUnsavedChanges = true;
      this.checkForUnsavedRundownChanges();
      
      // Optional: Parse the raw markdown to update other content fields
      try {
        if (content.includes('---')) {
          const parts = content.split('---');
          if (parts.length >= 3) {
            // Extract frontmatter and script content
            // const frontmatterYaml = parts[1].trim(); // TODO: Parse this for metadata sync
            // const scriptContent = parts.slice(2).join('---').trim(); // No longer needed

            // Script content is now handled by the computed property parsedContent.scriptContent
            // No need to manually sync since it parses from rawMarkdownContent
            
            // Optionally parse frontmatter to update metadata
            // (Could be enhanced to sync metadata form with raw edits)
          }
        }
      } catch (error) {
        console.warn('Could not parse raw markdown:', error);
      }
    },
    
    onMetadataChange(changeData) {
      console.log('Metadata change received:', changeData);
      const { field, value } = changeData;
      
      // Update the metadata in the current item metadata
      if (this.currentItemMetadata) {
        this.currentItemMetadata[field] = value;
        console.log(`Updated ${field} to:`, value);
      }
      
      // Also update the rundown item directly if we have a selected item
      if (this.selectedItemIndex >= 0 && this.selectedItemIndex < this.rundownItems.length) {
        const currentItem = this.rundownItems[this.selectedItemIndex];
        if (currentItem) {
          currentItem[field] = value;
          console.log(`Also updated field ${field} in rundown item:`, currentItem.slug || currentItem.title);
        }
      }
      
      this.hasUnsavedChanges = true;
      this.checkForUnsavedRundownChanges();
    },

    // Handle cue insertion from EditorPanel or floating panel
    handleInsertCue(cueTypeOrEvent) {
      console.log('🎯 handleInsertCue called with:', typeof cueTypeOrEvent === 'string' ? cueTypeOrEvent : cueTypeOrEvent.cueType);

      // Handle direct cue type string (from floating panel)
      if (typeof cueTypeOrEvent === 'string') {
        const cueType = cueTypeOrEvent;
        console.log('📌 String mode - cueType:', cueType);

        // Validate rundown item is selected before inserting any cue
        if (!this.requireRundownItemSelected(`${cueType} cue`)) return;

        // Handle cues that require modals
        if (cueType === 'IMG') {
          this.showImgCueModal = true;
          return;
        }

        if (cueType === 'SOT') {
          this.showSotModal = true;
          return;
        }

        // Handle other cue types with simple templates
        const cueTemplates = {
          'GFX': '[GFX: graphic-name]',
          'FSQ': '[FSQ: "Quote text here" - Source Name]',
        };

        const cueText = cueTemplates[cueType] || `[${cueType}]`;

        // Insert into current editor mode
        if (this.editorMode === 'script') {
          this.appendToScriptContent(`\n${cueText}\n`);
        } else if (this.editorMode === 'scratch') {
          this.scratchContent += `\n${cueText}\n`;
        } else if (this.editorMode === 'code') {
          this.rawMarkdownContent += `\n${cueText}\n`;
        }

        this.hasUnsavedChanges = true;
        return;
      }

      // Handle event object format (from modals)
      const { cueType, cueText, editorMode } = cueTypeOrEvent;
      console.log(`🔧 Object mode - Inserting ${cueType} cue in ${editorMode} mode`);
      console.log('📝 Cue text preview:', cueText.substring(0, 100));
      console.log('📊 Current scriptContent length BEFORE:', this.scriptContent?.length || 0);

      // Get the currently focused paragraph index from EditorPanel
      const focusedIndex = this.$refs.editorPanel?.focusedParagraphIndex;
      console.log('📍 Currently focused paragraph index:', focusedIndex);

      // Insert cue text into the appropriate content field based on editor mode
      if (editorMode === 'script') {
        console.log('✅ Calling appendToScriptContent...');
        this.appendToScriptContent(`\n${cueText}\n`, focusedIndex);
        console.log('✅ appendToScriptContent returned');
      } else if (editorMode === 'scratch') {
        this.scratchContent += `\n${cueText}\n`;
      } else if (editorMode === 'code') {
        this.rawMarkdownContent += `\n${cueText}\n`;
      }

      console.log('📊 Current scriptContent length AFTER:', this.scriptContent?.length || 0);

      this.hasUnsavedChanges = true;
      this.checkForUnsavedRundownChanges();
      console.log('✅ handleInsertCue complete');
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
    
    async submitGraphic(gfxCueData) {
      console.log('🎨 GFX cue submitted:', gfxCueData);

      // Verify editorPanel ref exists
      if (!this.$refs.editorPanel) {
        console.error('❌ EditorPanel ref not found');
        alert('Error: Editor panel not ready. Please try again.');
        return;
      }

      // Format the GFX cue block with all metadata
      let gfxCueBlock = `<!-- Begin Cue -->\n`;
      gfxCueBlock += `[Type: GFX]\n`;
      gfxCueBlock += `[AssetID: ${gfxCueData.assetId}]\n`;
      gfxCueBlock += `[Slug: ${gfxCueData.slug}]\n`;
      gfxCueBlock += `[GfxType: ${gfxCueData.gfxType || 'fullscreen-text'}]\n`;

      if (gfxCueData.title) {
        gfxCueBlock += `[Title: ${gfxCueData.title}]\n`;
      }
      if (gfxCueData.body) {
        // Escape newlines in body for single-line storage
        const escapedBody = gfxCueData.body.replace(/\n/g, '\\n');
        gfxCueBlock += `[Body: ${escapedBody}]\n`;
      }
      if (gfxCueData.style) {
        gfxCueBlock += `[FontSize: ${gfxCueData.style.fontSize}px]\n`;
        gfxCueBlock += `[FontFamily: ${gfxCueData.style.fontFamily}]\n`;
        gfxCueBlock += `[TextAlign: ${gfxCueData.style.textAlign}]\n`;
      }
      if (gfxCueData.renderMode) {
        gfxCueBlock += `[RenderMode: ${gfxCueData.renderMode}]\n`;
      }
      if (gfxCueData.assetUrl) {
        gfxCueBlock += `[AssetURL: ${gfxCueData.assetUrl}]\n`;
      }
      if (gfxCueData.status) {
        gfxCueBlock += `[Status: ${gfxCueData.status}]\n`;
      }
      gfxCueBlock += `<!-- End Cue -->`;

      console.log('📝 GFX cue block:', gfxCueBlock);

      // Use EditorPanel's handleSotCueSubmit which properly uses selectedSegmentIndex
      // This is the same method SOT uses and it works correctly
      console.log('🎨 Inserting GFX cue via EditorPanel method (same as SOT)');

      if (this.$refs.editorPanel && this.$refs.editorPanel.handleSotCueSubmit) {
        await this.$refs.editorPanel.handleSotCueSubmit(gfxCueBlock);
        console.log('✅ GFX cue inserted via EditorPanel.handleSotCueSubmit');
      } else {
        // Fallback: append at end
        console.warn('⚠️ EditorPanel.handleSotCueSubmit not available, appending at end');
        this.appendToScriptContent(`\n${gfxCueBlock}\n`);
      }

      // Clear the snapshot for next time
      this.gfxInsertionIndex = null;
      console.log('🧹 Cleared gfxInsertionIndex snapshot');

      // Close the modal
      this.showGfxModal = false;

      this.hasUnsavedChanges = true;
      this.checkForUnsavedRundownChanges();

      this.$toast?.success('GFX cue inserted successfully!');
      console.log('✅ GFX cue inserted');
    },
    
    submitFsq(fsqCueData) {
      console.log('🎬 FSQ cue submitted:', fsqCueData);

      // Verify editorPanel ref exists
      if (!this.$refs.editorPanel) {
        console.error('❌ EditorPanel ref not found');
        alert('Error: Editor panel not ready. Please try again.');
        return;
      }

      // Format the FSQ cue block with all metadata
      let fsqCueBlock = `<!-- Begin Cue -->\n`;
      fsqCueBlock += `[Type: FSQ]\n`;
      fsqCueBlock += `[AssetID: ${fsqCueData.assetId}]\n`;
      fsqCueBlock += `[Slug: ${fsqCueData.slug}]\n`;
      fsqCueBlock += `[Quote: "${fsqCueData.quote}"]\n`;
      if (fsqCueData.source) {
        fsqCueBlock += `[Attribution: ${fsqCueData.source}]\n`;
      }
      fsqCueBlock += `[Style: ${fsqCueData.style}]\n`;
      if (fsqCueData.fontFamily) {
        fsqCueBlock += `[FontFamily: ${fsqCueData.fontFamily}]\n`;
      }
      if (fsqCueData.fontSize) {
        fsqCueBlock += `[FontSize: ${fsqCueData.fontSize}px]\n`;
      }
      fsqCueBlock += `[Duration: ${fsqCueData.duration}]\n`;
      if (fsqCueData.wordCount) {
        fsqCueBlock += `[WordCount: ${fsqCueData.wordCount}]\n`;
      }
      if (fsqCueData.part) {
        fsqCueBlock += `[Part: ${fsqCueData.part}]\n`;
      }
      if (fsqCueData.mediaUrl) {
        fsqCueBlock += `[MediaURL: ${fsqCueData.mediaUrl}]\n`;
      }
      if (fsqCueData.renderMode) {
        fsqCueBlock += `[RenderMode: ${fsqCueData.renderMode}]\n`;
      }
      fsqCueBlock += `<!-- End Cue -->`;

      // ── EDIT MODE: Replace existing cue in-place ──
      if (this.editingFsqCueData) {
        const editAssetId = this.editingFsqCueData.assetId || this.editingFsqCueData.rawData?.assetId;
        console.log(`📝 EDIT MODE: Replacing FSQ cue with assetId ${editAssetId}`);

        const segments = this.$refs.editorPanel.scriptSegments;
        const segmentIndex = segments.findIndex(seg =>
          seg.type === 'cue' &&
          (seg.data?.assetId === editAssetId || seg.data?.rawData?.assetId === editAssetId)
        );

        if (segmentIndex !== -1) {
          // Build updated data object matching the segment structure
          const oldSegment = segments[segmentIndex];
          const updatedRawData = {
            ...oldSegment.data?.rawData,
            type: 'FSQ',
            assetId: fsqCueData.assetId,
            slug: fsqCueData.slug,
            quote: fsqCueData.quote,
            attribution: fsqCueData.source || fsqCueData.attribution || '',
            style: fsqCueData.style,
            fontFamily: fsqCueData.fontFamily,
            fontSize: fsqCueData.fontSize ? `${fsqCueData.fontSize}px` : undefined,
            duration: fsqCueData.duration,
            wordCount: fsqCueData.wordCount,
            part: fsqCueData.part,
            mediaUrl: fsqCueData.mediaUrl || oldSegment.data?.mediaUrl,
            renderMode: fsqCueData.renderMode
          };

          const updatedData = {
            ...oldSegment.data,
            ...updatedRawData,
            rawData: updatedRawData
          };

          // Replace the segment in-place
          segments.splice(segmentIndex, 1, {
            ...oldSegment,
            data: updatedData,
            rawContent: fsqCueBlock
          });

          // Reconstruct and update script content
          const newRawContent = this.$refs.editorPanel.reconstructRawContent(segments);
          this.updateScriptContent(newRawContent);

          console.log(`✅ FSQ cue replaced in-place at segment index ${segmentIndex}`);
        } else {
          console.warn('⚠️ Could not find existing cue to replace, inserting as new');
          // Fall through to insert logic below
          this.editingFsqCueData = null;
          this.submitFsq(fsqCueData);
          return;
        }

        // Close modal and clean up edit state
        this.showFsqModal = false;
        this.editingFsqCueData = null;
        this.hasUnsavedChanges = true;
        this.checkForUnsavedRundownChanges();

        // Trigger PNG regeneration
        this.triggerFsqGeneration([fsqCueData]);
        return;
      }

      // ── NEW MODE: Insert new cue(s) ──

      // Initialize pending cues arrays if this is the first part
      if (!this.$refs.editorPanel.pendingCueDataArray) {
        this.$refs.editorPanel.pendingCueDataArray = [];
      }
      if (!this.$refs.editorPanel.pendingFsqDataArray) {
        this.$refs.editorPanel.pendingFsqDataArray = [];
      }

      // Add this cue text block and original data to the arrays
      this.$refs.editorPanel.pendingCueDataArray.push(fsqCueBlock);
      this.$refs.editorPanel.pendingFsqDataArray.push(fsqCueData);
      console.log(`📦 Collected FSQ part ${this.$refs.editorPanel.pendingCueDataArray.length} (Part: ${fsqCueData.part})`);

      // Check if this is a multipart quote and if we're on the last part
      const partMatch = fsqCueData.part?.match(/(\d+)x(\d+)/);
      const currentPart = partMatch ? parseInt(partMatch[1]) : 1;
      const totalParts = partMatch ? parseInt(partMatch[2]) : 1;
      const isLastPart = currentPart === totalParts;

      console.log(`🔢 Multipart check: ${currentPart}/${totalParts}, isLastPart: ${isLastPart}`);

      // Only insert when we have ALL parts
      if (isLastPart) {
        console.log(`✅ All ${totalParts} FSQ parts collected, inserting at cursor position`);

        // Close the modal
        this.showFsqModal = false;

        // Insert all parts at the captured cursor position (or end if null/undefined)
        const allCues = this.$refs.editorPanel.pendingCueDataArray.join('\n\n');
        const insertionPosition = this.fsqInsertionIndex;

        // Determine if we have a valid insertion position
        const hasValidPosition = insertionPosition !== null &&
                                 insertionPosition !== undefined &&
                                 typeof insertionPosition === 'number';

        if (hasValidPosition) {
          console.log(`📝 Inserting ${totalParts} FSQ cue(s) after paragraph index ${insertionPosition}`);
        } else {
          console.log(`📝 Inserting ${totalParts} FSQ cue(s) at BOTTOM of script (no valid cursor position: ${insertionPosition})`);
        }

        // Use EditorPanel's snapshotted position for precise insertion
        if (this.$refs.editorPanel?.insertCueAtSnapshotPosition) {
          this.$refs.editorPanel.insertCueAtSnapshotPosition(allCues);
          console.log('✅ FSQ cue(s) inserted via EditorPanel.insertCueAtSnapshotPosition');
        } else {
          this.appendToScriptContent(`\n${allCues}\n`, insertionPosition);
        }

        // Clear the snapshot for next time
        this.fsqInsertionIndex = null;

        this.hasUnsavedChanges = true;
        this.checkForUnsavedRundownChanges();

        // Trigger automatic PNG generation for each FSQ
        const fsqDataToGenerate = [...this.$refs.editorPanel.pendingFsqDataArray];
        this.triggerFsqGeneration(fsqDataToGenerate);

        // Clear the arrays for next time
        this.$refs.editorPanel.pendingCueDataArray = [];
        this.$refs.editorPanel.pendingFsqDataArray = [];
      } else {
        console.log(`⏳ Waiting for remaining parts (${currentPart}/${totalParts})...`);
      }
    },

    /**
     * Trigger automatic PNG generation for FSQ cues
     * Calls the async generation endpoint for each FSQ in the background
     */
    async triggerFsqGeneration(fsqDataArray) {
      if (!fsqDataArray || fsqDataArray.length === 0) return;

      const episode = this.$route?.params?.episode || this.currentEpisode;
      if (!episode) {
        console.warn('⚠️ Cannot trigger FSQ generation: no episode ID');
        return;
      }

      console.log(`🎨 Triggering automatic PNG generation for ${fsqDataArray.length} FSQ(s)...`);

      // Show notification that generation is starting
      if (this.$root && this.$root.$emit) {
        this.$root.$emit('show-notification', {
          type: 'info',
          title: 'FSQ Generation Started',
          message: `Generating ${fsqDataArray.length} quote graphic(s) in background...`,
          timeout: 3000
        });
      }

      const token = localStorage.getItem('auth-token');
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Fire off generation requests for each FSQ (don't wait for completion)
      for (const fsqData of fsqDataArray) {
        try {
          // Map frontend style names to backend alignment
          const alignmentMap = {
            'centered': 'center',
            'left': 'left',
            'right': 'right',
            'large': 'center',
            'elegant': 'center'
          };

          const requestBody = {
            episode_id: episode,
            quote: fsqData.quote,
            attribution: fsqData.source || '',
            slug: fsqData.slug,
            asset_id: fsqData.assetId,
            alignment: alignmentMap[fsqData.style] || 'center',
            font_family: fsqData.fontFamily || 'sans-serif',
            box_height: 80,
            box_opacity: 75,
            line_spacing: 30,
            duration: fsqData.duration || '00:00:05:00',
            enumerator: null,  // Can add rundown position later
            priority: 'high'   // User-initiated = high priority
          };

          console.log(`🎨 Queuing FSQ generation: ${fsqData.slug}`);

          // Fire and forget - don't await
          fetch('/api/fsq/generate-async', {
            method: 'POST',
            headers,
            body: JSON.stringify(requestBody)
          }).then(response => {
            if (response.ok) {
              return response.json();
            }
            throw new Error(`HTTP ${response.status}`);
          }).then(result => {
            console.log(`✅ FSQ generation queued: ${fsqData.slug} (task: ${result.task_id})`);
          }).catch(err => {
            console.error(`❌ FSQ generation failed for ${fsqData.slug}:`, err);
          });

        } catch (err) {
          console.error(`❌ Error queuing FSQ generation for ${fsqData.slug}:`, err);
        }
      }

      console.log(`🎨 All ${fsqDataArray.length} FSQ generation requests queued`);
    },

    // Handle FSQ modal close (including cancel/ESC)
    handleFsqModalClose(isVisible) {
      // Update modal visibility
      this.showFsqModal = isVisible;

      // When modal is closed (isVisible becomes false)
      if (!isVisible) {
        // Clear edit mode state
        this.editingFsqCueData = null;

        // Only clear placement if there's NO pending cue waiting to be placed
        // (if user submitted, placement overlay should remain active)
        if (this.$refs.editorPanel && !this.$refs.editorPanel.pendingCueData) {
          console.log('🎬🔥 FSQ modal closed - no pending cue, clearing placement highlighting');
          this.$refs.editorPanel.showCuePlacement = false;
          this.$refs.editorPanel.pendingCueType = null;
          this.$refs.editorPanel.pendingPlacement = null;
        } else if (this.$refs.editorPanel && this.$refs.editorPanel.pendingCueData) {
          console.log('🎬✅ FSQ modal closed - pending cue active, keeping placement overlay');
        }
      }
    },
    
    async submitSot(data) {
      try {
        console.log('🎬🎬🎬 ===============================================');
        console.log('🎬 submitSot CALLED - Starting SOT cue handling');
        console.log('🎬 AssetID:', data.assetId);
        console.log('📋 Full SOT data received:', JSON.stringify(data, null, 2));

        // Check if this is a re-upload (replacing existing cue in place)
        const isReupload = this.editingSotCueData?.isReupload;
        const originalAssetId = this.editingSotCueData?.originalAssetId;

        if (isReupload) {
          console.log('📤 RE-UPLOAD MODE - Will replace existing cue in place');
          console.log('📤 Original AssetID to find:', originalAssetId);
          console.log('📤 New AssetID:', data.assetId);
        }

        // Build the SOT cue block
        let sotCue = `<!-- Begin Cue -->
[Type: SOT]
[AssetID: ${data.assetId}]
[Slug: ${data.slug}]
[Description: ${data.description}]
[MediaURL: ${data.mediaUrl}]
[Duration: ${data.duration}]
[TrimStart: ${data.trimStart}]
[TrimEnd: ${data.trimEnd}]`;

        // Add clipping info if present
        if (data.clippingMethod && data.clippingMethod !== 'none') {
          sotCue += `\n[ClippingMethod: ${data.clippingMethod}]`;
        }
        if (data.clips && data.clips.length > 0) {
          sotCue += `\n[Clips: ${JSON.stringify(data.clips)}]`;
        }

        sotCue += `
[Transcription: ${data.transcription}]
[ThumbnailURL: ${data.thumbnailUrl}]
[Credits: ${data.credits}]
<!-- End Cue -->

`;

        console.log('📝 Built SOT cue block (length:', sotCue.length, 'chars)');
        console.log('📝 Cue block content:\n', sotCue);

        // Close modal first
        this.showSotModal = false;
        console.log('🚪 SOT modal closed');

        // RE-UPLOAD: Replace existing cue in place instead of inserting new one
        if (isReupload && originalAssetId) {
          console.log('📤 Replacing existing cue block in script content...');

          // Find and replace the existing cue block by its AssetID
          // The cue block format is: <!-- Begin Cue --> ... [AssetID: xxx] ... <!-- End Cue -->
          const scriptContent = this.rawMarkdownContent || '';

          // Build regex to find the entire cue block containing the original AssetID
          // This regex matches from <!-- Begin Cue --> to <!-- End Cue --> that contains the specific AssetID
          // Note: The field name in cue blocks is "Assetid" (lowercase 'id'), case-insensitive match
          const escapedAssetId = originalAssetId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

          console.log('📤 Script content length:', scriptContent.length);
          console.log('📤 Looking for AssetID:', originalAssetId);
          console.log('📤 Escaped AssetID:', escapedAssetId);

          // First try to find just the assetid line to verify it exists
          const assetIdLineRegex = new RegExp(`\\[Assetid:\\s*${escapedAssetId}\\]`, 'i');
          const assetIdMatch = scriptContent.match(assetIdLineRegex);
          console.log('📤 AssetID line found:', !!assetIdMatch, assetIdMatch ? assetIdMatch[0] : 'NOT_FOUND');

          // Full cue block regex - matches from <!-- Begin Cue --> to <!-- End Cue --> containing the AssetID
          const cueBlockRegex = new RegExp(
            `<!--\\s*Begin Cue\\s*-->[\\s\\S]*?\\[Assetid:\\s*${escapedAssetId}\\][\\s\\S]*?<!--\\s*End Cue\\s*-->\\s*\\n?`,
            'i'
          );

          const match = scriptContent.match(cueBlockRegex);

          if (match) {
            console.log('✅ Found existing cue block to replace');
            console.log('📍 Match position:', match.index, 'length:', match[0].length);

            // Replace the old cue block with the new one
            const updatedContent = scriptContent.replace(cueBlockRegex, sotCue);

            // Update the script content via the rawMarkdownContent property
            // This is reactive and will propagate to EditorPanel via the scriptContent prop
            this.rawMarkdownContent = updatedContent;

            console.log('✅ Cue block replaced successfully in place');
          } else {
            console.warn('⚠️ Could not find existing cue block with AssetID:', originalAssetId);
            console.warn('⚠️ Will insert as new cue instead');
            // Fall through to normal insertion below
          }

          // Clear the re-upload state
          this.editingSotCueData = null;

          // Skip normal insertion if we successfully replaced
          if (match) {
            this.hasUnsavedChanges = true;
            this.checkForUnsavedRundownChanges();

            console.log('💾 Saving script content to database before processing...');
            await this.saveCurrentItem();
            console.log('💾 Save complete - updated cue block is now in database');

            console.log('🔄 About to trigger SOT processing...');
            await this.triggerSOTProcessing(data);
            console.log('🎬🎬🎬 submitSot (RE-UPLOAD) COMPLETED');
            console.log('🎬🎬🎬 ===============================================');
            return;
          }
        }

        // Delegate to EditorPanel (uses pendingCueInsertionIndex snapshotted at button-press time)
        if (this.$refs.editorPanel?.insertCueAtSnapshotPosition) {
          this.$refs.editorPanel.insertCueAtSnapshotPosition(sotCue);
          console.log('✅ SOT cue inserted via EditorPanel.insertCueAtSnapshotPosition');
        } else {
          console.warn('⚠️ EditorPanel not available, appending to end');
          this.appendToScriptContent(`\n${sotCue}\n`, null);
        }

        this.hasUnsavedChanges = true;
        this.checkForUnsavedRundownChanges();

        console.log(`✅ SOT cue inserted successfully`);

        // CRITICAL: Save to database BEFORE triggering processing
        // The worker needs to find the cue block in the database
        console.log('💾 Saving script content to database before processing...');
        await this.saveCurrentItem();
        console.log('💾 Save complete - cue block is now in database');

        // Trigger processing NOW that cue is in database
        console.log('🔄 About to trigger SOT processing...');
        await this.triggerSOTProcessing(data);
        console.log('🎬🎬🎬 submitSot COMPLETED');
        console.log('🎬🎬🎬 ===============================================');

      } catch (error) {
        console.error('❌❌❌ Error in submitSot:', error);
        console.error('❌ Stack trace:', error.stack);
        if (this.$toast) {
          this.$toast.error(`Failed to insert SOT cue: ${error.message}`);
        }
      }
    },

    /**
     * Handle multiple SOT submissions from Individual Clips mode
     * Each clip becomes an independent SOT cue processed via single_trim workflow
     * @param {Array} sotsArray - Array of SOT data objects, each with its own AssetID
     */
    async submitMultipleSots(sotsArray) {
      console.log('🎬🎬🎬 ===============================================');
      console.log(`🎬 submitMultipleSots CALLED - ${sotsArray.length} independent SOT cues`);
      console.log('📋 SOTs to insert:', sotsArray.map(s => `${s.slug} (${s.assetId})`));

      // Close modal first
      this.showSotModal = false;
      console.log('🚪 SOT modal closed');

      try {
        // Process each SOT sequentially to maintain order
        for (let i = 0; i < sotsArray.length; i++) {
          const data = sotsArray[i];
          console.log(`\n📍 Processing SOT ${i + 1}/${sotsArray.length}: ${data.slug}`);

          // Build the SOT cue block with source reference metadata for re-trimming
          const sotCue = `<!-- Begin Cue -->
[Type: SOT]
[AssetID: ${data.assetId}]
[Slug: ${data.slug}]
[Description: ${data.description || ''}]
[MediaURL: Processing...]
[Duration: Calculating...]
[TrimStart: ${data.trimStart}]
[TrimEnd: ${data.trimEnd}]
[SourceJobId: ${data.sourceJobId || data.tempJobId}]
[OriginalTrimStart: ${data.originalTrimStart || data.trimStart}]
[OriginalTrimEnd: ${data.originalTrimEnd || data.trimEnd}]
[Transcription: Processing...]
[ThumbnailURL: ]
[Credits: ${data.credits || '{}'}]
[ProcessingStatus: Queued]
<!-- End Cue -->

`;

          console.log(`📝 Built SOT cue block for ${data.slug} (length: ${sotCue.length} chars)`);

          // Insert cue using EditorPanel's method (proper paragraph boundary detection)
          if (this.$refs.editorPanel && this.$refs.editorPanel.handleSotCueSubmit) {
            await this.$refs.editorPanel.handleSotCueSubmit(sotCue);
            console.log(`✅ Cue ${i + 1} inserted via EditorPanel.handleSotCueSubmit`);
          } else {
            // Fallback - append to end
            console.warn('⚠️ EditorPanel not available, appending to end');
            this.appendToScriptContent(`\n${sotCue}\n`, null);
          }
        }

        // Mark changes and save
        this.hasUnsavedChanges = true;
        this.checkForUnsavedRundownChanges();

        // CRITICAL: Save to database BEFORE triggering processing
        console.log('💾 Saving script content with all cue blocks to database...');
        await this.saveCurrentItem();
        console.log('💾 Save complete - all cue blocks are now in database');

        // Trigger processing for each SOT (can run in parallel)
        console.log(`🔄 Triggering ${sotsArray.length} processing jobs...`);
        const processingPromises = sotsArray.map((data, i) => {
          console.log(`🎬 Starting processing for ${data.slug} (${i + 1}/${sotsArray.length})`);
          return this.triggerSOTProcessing(data);
        });

        // Wait for all processing to start (not complete, just dispatched)
        await Promise.all(processingPromises);

        console.log(`✅ All ${sotsArray.length} processing jobs dispatched`);
        console.log('🎬🎬🎬 submitMultipleSots COMPLETED');
        console.log('🎬🎬🎬 ===============================================');

        // Notify user
        notifyUserStandard(
          `🎬 ${sotsArray.length} clips inserted and processing started`,
          NOTIFICATION_COLORS.SUCCESS,
          5000
        );

      } catch (error) {
        console.error('❌❌❌ Error in submitMultipleSots:', error);
        console.error('❌ Stack trace:', error.stack);
        if (this.$toast) {
          this.$toast.error(`Failed to insert multiple SOT cues: ${error.message}`);
        }
      }
    },

    async triggerSOTProcessing(data) {
      // Only trigger if we have a background upload ready
      if (!data.tempJobId) {
        console.log('ℹ️ No tempJobId - skipping processing');
        return;
      }

      try {
        console.log('🎬 Triggering SOT processing for:', data.tempJobId);

        const axios = (await import('axios')).default;
        const response = await axios.post('/api/sot/process/multi-phase', {
          temp_job_id: data.tempJobId,
          episode: this.currentEpisodeNumber,
          slug: data.slug,
          asset_id: data.assetId,
          trim_start: data.trimStart,
          trim_end: data.trimEnd,
          job_type: data.jobType || 'full_process',
          clips: data.clips ? JSON.parse(data.clips) : null
        });

        console.log('✅ Processing started:', response.data);

        // Use slide-in notification instead of toast
        notifyUserStandard(
          `🎬 ${data.slug}: Processing started`,
          NOTIFICATION_COLORS.SUCCESS,
          4000
        );

      } catch (error) {
        console.error('❌ Failed to start SOT processing:', error);

        // Use slide-in notification for errors
        notifyUserStandard(
          `❌ ${data.slug}: Processing failed - ${error.message}`,
          NOTIFICATION_COLORS.ERROR,
          5000
        );
      }
    },

    async submitVo(data) {
      try {
        console.log('🎬 VO Modal Submit');
        console.log('📋 VO data received:', JSON.stringify(data, null, 2));

        // Build the VO cue block (similar to SOT but without transcription/credits)
        let voCue = `<!-- Begin Cue -->
[Type: VO]
[AssetID: ${data.assetID || data.assetId || ''}]
[Slug: ${data.slug || ''}]
[MediaURL: ${data.mediaURL || data.mediaUrl || ''}]
[Duration: ${data.duration || ''}]
[TrimStart: ${data.trimStart || '00:00:00'}]
[TrimEnd: ${data.trimEnd || '00:00:00'}]
[ProcessingStatus: ${data.taskId ? 'Processing' : 'Pending'}]
<!-- End Cue -->

`;

        console.log('📝 Built VO cue block (length:', voCue.length, 'chars)');
        console.log('📝 Cue block content:\n', voCue);

        // Close modal first
        this.showVoModal = false;
        console.log('🚪 VO modal closed');

        // Send cue data to EditorPanel for placement-based insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handleVoCueSubmit(voCue);
          console.log('✅ VO cue data sent to EditorPanel - placement overlay now active');
          console.log('📍 Waiting for user to click drop zone to insert VO...');
        }

        // NOTE: Database save will happen automatically after user clicks placement
        // via the normal auto-save mechanism when scriptContent is updated

      } catch (error) {
        console.error('❌ Error in submitVo:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert VO cue: ${error.message}`);
        }
      }
    },
    
    async submitNat(data) {
      try {
        console.log('🎬 NAT Modal Submit');
        console.log('📋 NAT data received:', data);

        // Build the NAT cue
        const natCue = `[NAT: ${data.description}${data.duration ? ' | ' + data.duration : ''}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;

        console.log('📝 Built NAT cue, sending to EditorPanel for placement insertion');

        // Close modal first
        this.showNatModal = false;

        // Send cue data to EditorPanel for placement-based insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handleNatCueSubmit(natCue);
          console.log('✅ NAT cue data sent to EditorPanel - placement overlay now active');
          console.log('📍 Waiting for user to click drop zone to insert NAT...');
        }

      } catch (error) {
        console.error('❌ Error in submitNat:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert NAT cue: ${error.message}`);
        }
      }
    },

    async submitRif(data) {
      try {
        console.log('🎬 RIF Modal Submit');
        console.log('📋 RIF data received:', data);

        // Build the RIF cue in standard format
        const rifCue = `<!-- Begin Cue -->
[Assetid: ${data.assetID}]
[Type: RIF]
[Slug: ${data.slug}]
[Duration: ${data.duration}]
<!-- End Cue -->
`;

        console.log('📝 Built RIF cue, sending to EditorPanel for cursor insertion');

        // Close modal first
        this.showRifModal = false;

        // Send cue data to EditorPanel for cursor insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handleRifCueSubmit(rifCue);
          console.log('✅ RIF cue inserted at cursor position');
        }

      } catch (error) {
        console.error('❌ Error in submitRif:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert RIF cue: ${error.message}`);
        }
      }
    },

    async submitPkg(data) {
      try {
        console.log('🎬 PKG Modal Submit');
        console.log('📋 PKG data received:', data);

        // Build the PKG cue
        const pkgCue = `[PKG: ${data.title} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;

        console.log('📝 Built PKG cue, sending to EditorPanel for placement insertion');

        // Close modal first
        this.showPkgModal = false;

        // Send cue data to EditorPanel for placement-based insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handlePkgCueSubmit(pkgCue);
          console.log('✅ PKG cue data sent to EditorPanel - placement overlay now active');
          console.log('📍 Waiting for user to click drop zone to insert PKG...');
        }

      } catch (error) {
        console.error('❌ Error in submitPkg:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert PKG cue: ${error.message}`);
        }
      }
    },

    async submitDir(data) {
      try {
        console.log('🎬 NOTE Modal Submit');
        console.log('📋 NOTE data received:', data);

        // Close modal first
        this.showDirModal = false;

        // Send cue data to EditorPanel for placement-based insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handleDirCueSubmit(data);
          console.log('✅ NOTE cue data sent to EditorPanel');
        }

      } catch (error) {
        console.error('❌ Error in submitDir:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert NOTE cue: ${error.message}`);
        }
      }
    },

    async submitBump(data) {
      try {
        console.log('🎬 BUMP Modal Submit');
        console.log('📋 BUMP data received:', data);

        // Close modal first
        this.showBumpModal = false;

        // Send cue data to EditorPanel for placement-based insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handleBumpCueSubmit(data);
          console.log('✅ BUMP cue data sent to EditorPanel - placement overlay now active');
          console.log('📍 Waiting for user to click drop zone to insert BUMP...');
        }

      } catch (error) {
        console.error('❌ Error in submitBump:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert BUMP cue: ${error.message}`);
        }
      }
    },

    async submitSting(data) {
      try {
        console.log('🎬 STING Modal Submit');
        console.log('📋 STING data received:', data);

        // Close modal first
        this.showStingModal = false;

        // Send cue data to EditorPanel for placement-based insertion
        if (this.$refs.editorPanel) {
          await this.$refs.editorPanel.handleStingCueSubmit(data);
          console.log('✅ STING cue data sent to EditorPanel - placement overlay now active');
          console.log('📍 Waiting for user to click drop zone to insert STING...');
        }

      } catch (error) {
        console.error('❌ Error in submitSting:', error);
        if (this.$toast) {
          this.$toast.error(`Failed to insert STING cue: ${error.message}`);
        }
      }
    },

    submitVox(data) {
      const voxCue = `[VOX: ${data.slug} | ${data.description} | ${data.duration}]\n`;

      if (this.$refs.editorPanel?.insertCueAtSnapshotPosition) {
        this.$refs.editorPanel.insertCueAtSnapshotPosition(voxCue);
      } else {
        this.handleInsertCue({ cueType: 'VOX', cueText: voxCue, editorMode: this.editorMode });
      }

      this.showVoxModal = false;
      this.$toast.success('VOX cue inserted successfully!');
      console.log('✅ VOX cue inserted');
    },

    submitMus(data) {
      const musCue = `[MUS: ${data.slug} | ${data.description} | ${data.duration}]\n`;

      if (this.$refs.editorPanel?.insertCueAtSnapshotPosition) {
        this.$refs.editorPanel.insertCueAtSnapshotPosition(musCue);
      } else {
        this.handleInsertCue({ cueType: 'MUS', cueText: musCue, editorMode: this.editorMode });
      }

      this.showMusModal = false;
      this.$toast.success('MUS cue inserted successfully!');
      console.log('✅ MUS cue inserted');
    },

    submitLive(data) {
      const liveCue = `[LIVE: ${data.slug} | ${data.description} | ${data.duration}]\n`;

      if (this.$refs.editorPanel?.insertCueAtSnapshotPosition) {
        this.$refs.editorPanel.insertCueAtSnapshotPosition(liveCue);
      } else {
        this.handleInsertCue({ cueType: 'LIVE', cueText: liveCue, editorMode: this.editorMode });
      }

      this.showLiveModal = false;
      this.$toast.success('LIVE cue inserted successfully!');
      console.log('✅ LIVE cue inserted');
    },

    async createNewItem(itemData) {
      try {
        this.creatingNewItem = true;
        
        console.log('Creating new rundown item:', itemData);
        
        // Calculate index based on business rules
        let calculatedIndex = this.calculateNewItemIndex(itemData.type);
        
        // Add the calculated index to itemData
        const itemDataWithIndex = {
          ...itemData,
          index: calculatedIndex
        };
        
        console.log('Item data with calculated index:', itemDataWithIndex);
        console.log('Calculated index value:', calculatedIndex);
        console.log('Index field in request data:', itemDataWithIndex.index);
        
        // Get authentication credentials (using same approach as delete function)
        console.log('All localStorage keys:', Object.keys(localStorage));
        console.log('localStorage contents:', {
          api_key: localStorage.getItem('api_key'),
          auth_token: localStorage.getItem('auth_token'), 
          token: localStorage.getItem('token'),
          'auth-token': localStorage.getItem('auth-token'),
          jwt: localStorage.getItem('jwt'),
          authToken: localStorage.getItem('authToken'),
          access_token: localStorage.getItem('access_token')
        });
        
        let token = null;
        let apiKey = localStorage.getItem('api_key');
        
        // Try multiple localStorage keys for token
        token = localStorage.getItem('auth_token') || 
                 localStorage.getItem('token') || 
                 localStorage.getItem('auth-token') || 
                 localStorage.getItem('jwt') || 
                 localStorage.getItem('authToken') ||
                 localStorage.getItem('access_token');
        
        console.log('Token found:', token ? 'YES' : 'NO');
        console.log('API Key found:', apiKey ? 'YES' : 'NO');
        
        // Build authentication headers (but don't require them initially)
        const authHeaders = {};
        if (token) {
          authHeaders['Authorization'] = `Bearer ${token}`;
          console.log('Will use JWT token for authentication');
        } else if (apiKey) {
          authHeaders['X-API-Key'] = apiKey;
          console.log('Will use API key for authentication');
        } else {
          console.log('No authentication credentials found - will try API call without auth first');
        }
        
        // Create the rundown item using the correct API endpoint
        console.log('Making API request to create rundown item...');
        const paddedEpisodeNumber = this.padEpisodeNumber(this.currentEpisodeNumber);
        
        const response = await axios.post(
          `/api/episodes/${paddedEpisodeNumber}/rundown/item`,
          itemDataWithIndex,
          { headers: { 'Content-Type': 'application/json', ...authHeaders } }
        );
        
        console.log('API response received:', response);
        console.log('Full response data:', response.data);
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (response.data && response.data.success) {
          // Close modal
          this.showNewItemModal = false;
          
          // Instead of manually adding to array, reload rundown from database
          // This ensures we get the fresh state without duplicates
          await this.reloadFromDatabase();

          // Find and select the newly created item by AssetID
          console.log('Looking for newly created item...');
          console.log('Response asset_id:', response.data.asset_id);
          console.log('ItemData asset_id:', itemDataWithIndex.asset_id);
          console.log('Current rundown items:', this.rundownItems.map(item => ({
            asset_id: item.asset_id,
            slug: item.slug,
            title: item.title
          })));

          const searchId = response.data.asset_id;
          const newItemIndex = this.rundownItems.findIndex(item =>
            item.asset_id === searchId
          );

          console.log('Searching for asset_id:', searchId);
          console.log('Found item at index:', newItemIndex);

          if (newItemIndex !== -1) {
            // Show urgent flash message first
            const typeDisplayName = itemData.type.charAt(0).toUpperCase() + itemData.type.slice(1);
            notifyUserStandard(`New ${typeDisplayName}`, NOTIFICATION_COLORS.SUCCESS, 2000);

            // Small delay to let the message show, then flash the item
            await new Promise(resolve => setTimeout(resolve, 300));
            await this.flashNewlyCreatedItem(newItemIndex);
            this.selectedItemIndex = newItemIndex;
            this.selectRundownItem(newItemIndex);
            console.log('Successfully flashed and selected newly created item at index:', newItemIndex);

            // Focus slug field for new items
            this.$nextTick(() => {
              const editorPanel = this.$refs.editorPanelRef
              if (editorPanel && editorPanel.focusSlugField) {
                editorPanel.focusSlugField()
              }
            });
          } else {
            console.warn('Could not find newly created item in rundown. Trying alternative search methods...');

            // Try finding by slug as fallback
            const slugIndex = this.rundownItems.findIndex(item =>
              item.slug === itemData.slug
            );

            if (slugIndex !== -1) {
              // Show urgent flash message first
              const typeDisplayName = itemData.type.charAt(0).toUpperCase() + itemData.type.slice(1);
              notifyUserStandard(`New ${typeDisplayName}`, NOTIFICATION_COLORS.SUCCESS, 2000);

              // Small delay to let the message show, then flash the item
              await new Promise(resolve => setTimeout(resolve, 300));
              await this.flashNewlyCreatedItem(slugIndex);
              this.selectedItemIndex = slugIndex;
              this.selectRundownItem(slugIndex);
              console.log('Found by slug, flashed and selected item at index:', slugIndex);

              // Focus slug field for new items
              this.$nextTick(() => {
                const editorPanel = this.$refs.editorPanelRef
                if (editorPanel && editorPanel.focusSlugField) {
                  editorPanel.focusSlugField()
                }
              });
            } else {
              console.error('Could not locate newly created item by asset_id or slug');
              // Still show success message even if we can't locate the item
              const typeDisplayName = itemData.type.charAt(0).toUpperCase() + itemData.type.slice(1);
              notifyUserStandard(`New ${typeDisplayName}`, NOTIFICATION_COLORS.SUCCESS, 2000);
            }
          }
        } else {
          throw new Error(response.data?.message || 'API request did not return success');
        }
      } catch (error) {
        console.error('Error creating rundown item:', error);
        let errorMessage = 'Failed to create rundown item';
        
        // Safely extract error message
        if (error.response && error.response.data) {
          if (error.response.data.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.response.data.message) {
            errorMessage = error.response.data.message;
          } else if (typeof error.response.data === 'string') {
            errorMessage = error.response.data;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        // Show error message
        notifyUserStandard(errorMessage, NOTIFICATION_COLORS.ERROR, 4000);
      } finally {
        this.creatingNewItem = false;
      }
    },
    
    handleNewItemClick() {
      console.log('New Item button clicked!');
      console.log('Current rundownItemTypes:', this.rundownItemTypes);
      console.log('Setting showNewItemModal to true...');
      this.showNewItemModal = true;
      console.log('showNewItemModal is now:', this.showNewItemModal);
    },

    // Handle opening library picker when a reusable type is selected
    handleOpenLibraryPicker(data) {
      console.log('Opening library picker for:', data);
      this.libraryPickerItemType = data.itemType;
      this.showLibraryPickerModal = true;
    },

    // Handle library item selection
    async handleLibraryItemSelected(data) {
      console.log('Library item selected:', data);

      try {
        const paddedEpisodeNumber = this.padEpisodeNumber(this.currentEpisodeNumber);
        const calculatedIndex = this.calculateNewItemIndex(data.libraryItem.item_type);
        const headers = this.getAuthHeaders();

        // Place the library content in the rundown via API
        const response = await axios.post(
          `/api/content-library/place/${paddedEpisodeNumber}`,
          {
            library_asset_id: data.libraryItem.asset_id,
            order_in_rundown: calculatedIndex
          },
          { headers }
        );

        if (response.data && response.data.success) {
          console.log('Library content placed successfully:', response.data);

          // Reload rundown to show the new placement
          await this.reloadFromDatabase();

          // Show success notification
          const message = `Added "${data.libraryItem.title}" to rundown`;
          notifyUserStandard(message, NOTIFICATION_COLORS.SUCCESS, 2000);
        } else {
          throw new Error(response.data?.message || 'Failed to place content');
        }
      } catch (error) {
        console.error('Error placing library content:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Failed to add content: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
      }
    },

    // Handle request to create new library item
    handleCreateNewLibraryItem(data) {
      console.log('Create new library item requested:', data);
      // For now, fall back to regular item creation
      // Later this could open a dedicated library item creation modal
      const itemData = {
        type: data.itemType,
        title: '',
        subtitle: '',
        slug: '',
        duration: '00:00:30:00',
        description: '',
        status: 'draft'
      };
      this.createNewItem(itemData);
    },

    // Handle region selection from RundownPanel
    async handleRegionSelection(region) {
      console.log('Region selection changed:', region);
      this.selectedRegion = region;

      // Clear item selection when selecting a region (region selection takes precedence)
      if (region && this.selectedItemIndex >= 0) {
        // CRITICAL: Save any pending changes before clearing selection
        if (this.$refs.editorPanel?.flushPendingChanges) {
          this.$refs.editorPanel.flushPendingChanges();
          await this.$nextTick();
        }
        if (this.hasUnsavedChanges) {
          try {
            await this.saveCurrentItem();
          } catch (error) {
            console.error('Failed to save before region selection:', error);
          }
        }
        this.selectedItemIndex = -1;
      }
    },

    // Handle refresh rundown from Options menu
    async handleRefreshRundown() {
      console.log('🔄 Refresh rundown requested from Options menu');
      await this.reloadFromDatabase();
    },

    // Handle restore revision from Options menu
    async handleRestoreRevision() {
      if (this.selectedItemIndex < 0 || !this.currentRundownItem) {
        notifyUserStandard('Please select an item first', NOTIFICATION_COLORS.WARNING, 2000);
        return;
      }

      console.log('📜 Restore revision requested for:', this.currentRundownItem.title);

      // Open the metadata panel which has version history
      this.showMetadataPanel = true;

      // Notify user where to find version history
      notifyUserStandard('Version history is in the Metadata panel on the right', NOTIFICATION_COLORS.INFO, 3000);
    },

    async handleCreateRegion(regionData) {
      console.log('Create Region requested:', regionData);

      try {
        // Create a placeholder item to make the new region immediately visible
        const placeholderItem = this.createRegionPlaceholderItem(regionData);

        // Add the placeholder item to the end of the rundown
        this.rundownItems.push(placeholderItem);

        // Update the local UI immediately
        this.forceRundownUpdate();

        const message = `Created new ${regionData.type} region: ${regionData.name}`;
        console.log(message);

        // Use the flash message system
        notifyUserStandard(message, NOTIFICATION_COLORS.SUCCESS, 2000);

        // TODO: Later implement actual region creation API call
        // await this.createRegionInDatabase(regionData, placeholderItem);

      } catch (error) {
        console.error('Error creating region:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        notifyUserStandard(`Failed to create region: ${errorMsg}`, NOTIFICATION_COLORS.ERROR, 3000);
      }
    },

    createRegionPlaceholderItem(regionData) {
      // Create a placeholder item that will force the region to appear
      const maxOrder = Math.max(...(this.rundownItems.map(item => item.order || 0)), 0);
      const nextOrder = Math.ceil((maxOrder + 10) / 10) * 10; // Round up to next multiple of 10

      // Determine the appropriate item type for the region
      const itemType = regionData.type === 'break' ? 'ad' : 'segment';

      const placeholderItem = {
        id: `placeholder_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        slug: `new-${regionData.type}-placeholder`,
        title: `New ${regionData.name} (Click to edit)`,
        type: itemType,
        order: nextOrder,
        index: nextOrder,
        duration: '00:01:00',
        status: 'draft',
        content: `# New ${regionData.name}\n\nThis is a placeholder item. Edit this content to start building your ${regionData.type} region.`,
        isPlaceholder: true, // Flag to identify placeholder items
        regionType: regionData.type // Store the intended region type
      };

      return placeholderItem;
    },

    forceRundownUpdate() {
      // Force Vue to update the rundown display
      this.$nextTick(() => {
        // Trigger reactivity update
        this.$forceUpdate();
      });
    },
    
    cancelNewItem() {
      this.showNewItemModal = false;
    },
    
    calculateNewItemIndex(itemType) {
      console.log('=== CALCULATE NEW ITEM INDEX ===');
      console.log('Item type:', itemType);
      console.log('Selected item index:', this.selectedItemIndex);
      console.log('Rundown items count:', this.rundownItems?.length || 0);

      // Rule 1: Cold Open always gets index = 1
      if (itemType === 'coldopen') {
        console.log('Cold open type - assigning index 1');
        return 1;
      }

      // Get current order values from rundown items (they come sorted from backend)
      const existingOrders = this.rundownItems
        .map(item => item.order_in_rundown || item.order || item.index || 0)
        .filter(order => order !== null && order !== undefined);

      console.log('Existing orders:', existingOrders);

      let targetIndex;

      // Rule 2: If an item is selected, insert directly below it
      if (this.selectedItemIndex >= 0 && this.rundownItems[this.selectedItemIndex]) {
        const selectedItem = this.rundownItems[this.selectedItemIndex];
        const selectedOrder = selectedItem.order_in_rundown || selectedItem.order || selectedItem.index || 0;

        console.log('Selected item order:', selectedOrder);

        // Check if there's an item immediately after the selected one
        const nextItemIndex = this.selectedItemIndex + 1;
        if (nextItemIndex < this.rundownItems.length) {
          const nextItem = this.rundownItems[nextItemIndex];
          const nextOrder = nextItem.order_in_rundown || nextItem.order || nextItem.index || 0;

          // Place between selected and next item
          targetIndex = Math.floor((selectedOrder + nextOrder) / 2);

          // If they're too close (difference of 1), place right after selected
          if (targetIndex <= selectedOrder) {
            targetIndex = selectedOrder + 1;
          }

          console.log(`Inserting between ${selectedOrder} and ${nextOrder}, using ${targetIndex}`);
        } else {
          // Selected item is last, place after it
          targetIndex = selectedOrder + 10;
          console.log(`Selected item is last, placing at ${targetIndex}`);
        }
      } else {
        // Rule 3: No selection - place at the bottom
        const maxOrder = existingOrders.length > 0 ? Math.max(...existingOrders) : 0;
        targetIndex = maxOrder + 10;
        console.log(`No selection - placing at bottom: ${targetIndex}`);
      }

      console.log('=== FINAL RESULT ===');
      console.log('Final calculated index:', targetIndex);
      console.log('================');
      return targetIndex;
    },
    
    // IMG Cue Modal Methods
    async handleImgCueSubmit(imgCueData) {
      console.log('🖼️ IMG cue submitted:', imgCueData);
      console.log('🖼️ Current editorMode:', this.editorMode);
      console.log('🖼️ Selected item index:', this.selectedItemIndex);
      console.log('🖼️ Current rundown item:', this.currentRundownItem?.title);

      // Validate we have a rundown item selected
      if (this.selectedItemIndex < 0 || !this.currentRundownItem) {
        console.error('❌ No rundown item selected for IMG cue insertion');
        this.$toast?.error('Select a rundown item first to insert IMG cue');
        this.showImgCueModal = false;
        return;
      }

      // Validate editorMode
      if (!this.editorMode || !['script', 'scratch', 'code'].includes(this.editorMode)) {
        console.error('❌ Invalid editorMode:', this.editorMode);
        // Default to script mode if not set
        console.log('⚠️ Defaulting to script mode for insertion');
      }

      try {
        // Generate AssetID for the image (must use FormData, not JSON)
        const formData = new FormData();
        formData.append('type', 'img');
        formData.append('slug', imgCueData.slug);

        const assetIdResponse = await axios.post('/assetid/generate-legacy', formData, {
          headers: {
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        });

        const assetId = assetIdResponse.data.id;
        console.log('🆔 Generated AssetID:', assetId);

        // Format the IMG cue block with all metadata
        let imgCueBlock = `<!-- Begin Cue -->\n`;
        imgCueBlock += `[Type: IMG]\n`;
        imgCueBlock += `[AssetID: ${assetId}]\n`;
        imgCueBlock += `[Slug: ${imgCueData.slug}]\n`;
        if (imgCueData.description) {
          imgCueBlock += `[Description: ${imgCueData.description}]\n`;
        }
        if (imgCueData.credit) {
          imgCueBlock += `[Credit: ${imgCueData.credit}]\n`;
        }
        if (imgCueData.caption) {
          imgCueBlock += `[Caption: ${imgCueData.caption}]\n`;
        }
        if (imgCueData.filepath) {
          imgCueBlock += `[MediaURL: ${imgCueData.filepath}]\n`;
        }
        imgCueBlock += `<!-- End Cue -->`;

        console.log('📝 Generated IMG cue block:', imgCueBlock);

        // Use the effective editor mode (default to 'script' if invalid)
        const effectiveMode = ['script', 'scratch', 'code'].includes(this.editorMode) ? this.editorMode : 'script';
        console.log('📝 Using editor mode:', effectiveMode);

        // Delegate to EditorPanel (uses pendingCueInsertionIndex snapshotted at button-press time)
        if (this.$refs.editorPanel?.insertCueAtSnapshotPosition) {
          this.$refs.editorPanel.insertCueAtSnapshotPosition(imgCueBlock);
          console.log('✅ IMG cue inserted via EditorPanel.insertCueAtSnapshotPosition');
        } else {
          console.warn('⚠️ EditorPanel not available, appending at end');
          this.appendToScriptContent(`\n${imgCueBlock}\n`);
        }

        this.hasUnsavedChanges = true;
        this.$toast?.success('IMG cue inserted successfully!');
        console.log('✅ IMG cue inserted');

      } catch (error) {
        console.error('❌ Error creating IMG cue:', error);
        this.$toast?.error('Failed to insert IMG cue');
      }

      // Close the modal
      this.showImgCueModal = false;
    },

    // WPM Tool Methods
    handleSpeakerSaved(speakerData) {
      console.log('Speaker profile saved:', speakerData);
      // Refresh the metadata panel's speaker list
      if (this.$refs.metadataPanel) {
        this.$refs.metadataPanel.loadSpeakers();
      }
    },

    showMessage(message) {
      // Display flash message using snackbar or similar
      console.log('Message:', message.text, 'Type:', message.type);
      // You can add a v-snackbar to show these messages if desired
    },

    // GFX Modal Methods
    openNewGFXModal() {
      console.log('Opening New GFX Modal (Alt+G pressed)');
      this.showNewGFXModal = true;
    },
    
    async createGFXItem(gfxData) {
      console.log('Creating GFX item:', gfxData);
      
      try {
        this.creatingNewItem = true;
        
        // Handle image upload first if there's an image
        let imagePath = '';
        if (gfxData.imageBlob && gfxData.imageExtension) {
          // Create form data for image upload
          const formData = new FormData();
          formData.append('image', gfxData.imageBlob, `${gfxData.slug}.${gfxData.imageExtension}`);
          formData.append('type', 'gfx');
          formData.append('slug', gfxData.slug);
          
          // Upload image to assets directory
          const uploadResponse = await this.$http.post('/api/assets/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
          
          if (uploadResponse.data && uploadResponse.data.path) {
            imagePath = uploadResponse.data.path;
            console.log('Image uploaded to:', imagePath);
          }
        }
        
        // Calculate index for proper placement
        const calculatedIndex = this.calculateNewItemIndex('gfx');

        // Prepare GFX item data (similar to tease but for graphics)
        const newItem = {
          type: 'gfx',
          title: gfxData.title || '',
          subtitle: gfxData.subtitle || '',
          slug: gfxData.slug,
          duration: gfxData.duration || '00:00:00:00',
          description: gfxData.description || '',
          airdate: gfxData.airdate || '',
          priority: gfxData.priority || '',
          guests: gfxData.guests || '',
          tags: gfxData.tags || '',
          server_message: gfxData.server_message || '',
          status: gfxData.status || 'draft',
          image_path: imagePath, // Store the uploaded image path
          customer: gfxData.customer || '',
          link: gfxData.link || '',
          index: calculatedIndex // Required for proper rundown placement
        };
        
        console.log('Submitting GFX item to API:', newItem);

        // Create the new GFX rundown item
        const paddedId = String(this.currentEpisodeNumber).padStart(4, '0');
        const response = await this.$http.post(`/api/episodes/${paddedId}/rundown/item`, newItem);
        
        if (response.data && response.data.success) {
          console.log('GFX item created successfully:', response.data);

          // Close the modal
          this.showNewGFXModal = false;

          // Reload episode rundown to show new item
          await this.loadEpisode(this.currentEpisodeNumber, false, true);

          // Find and flash the newly created item
          const newItemIndex = this.rundownItems.findIndex(item =>
            item.asset_id === response.data.asset_id
          );

          if (newItemIndex !== -1) {
            await this.flashNewlyCreatedItem(newItemIndex);
            this.selectedItemIndex = newItemIndex;
            this.selectRundownItem(newItemIndex);
          }

          // Show success message for cue creation
          this.$toast.success(`GFX cue "${gfxData.slug}" created successfully!`);
        } else {
          throw new Error(response.data?.error || 'Failed to create GFX item');
        }
      } catch (error) {
        console.error('Error creating GFX item:', error);
        this.$toast.error(`Failed to create GFX item: ${error.response?.data?.error || error.message}`);
      } finally {
        this.creatingNewItem = false;
      }
    },
    
    // SOT Modal Methods
    openNewSOTModal() {
      console.log('Opening New SOT Modal (Alt+S pressed)');
      this.showNewSOTModal = true;
    },
    
    async createSOTItem(sotData) {
      console.log('Creating SOT item:', sotData);
      
      try {
        this.creatingNewItem = true;
        
        // Handle video upload first if there's a video
        let videoPath = '';
        let thumbnailPath = '';
        
        if (sotData.videoBlob && sotData.videoFileName) {
          // Create form data for video upload
          const formData = new FormData();
          formData.append('video', sotData.videoBlob, sotData.videoFileName);
          formData.append('type', 'sot');
          formData.append('slug', sotData.slug);
          
          // Upload video to assets directory
          const uploadResponse = await this.$http.post('/api/assets/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
          
          if (uploadResponse.data && uploadResponse.data.path) {
            videoPath = uploadResponse.data.path;
            console.log('Video uploaded to:', videoPath);
            
            // TODO: Generate thumbnail from video if needed
            // thumbnailPath = uploadResponse.data.thumbnailPath;
          }
        }
        
        // Calculate index for proper placement
        const calculatedIndex = this.calculateNewItemIndex('sot');

        // Prepare SOT item data with comprehensive structure
        const newItem = {
          type: 'sot',
          title: sotData.title || '',
          subtitle: sotData.subtitle || '',
          slug: sotData.slug,
          duration: sotData.duration || '00:00:00:00',
          description: sotData.description || '',
          transcription: sotData.transcription || '',
          airdate: sotData.airdate || '',
          priority: sotData.priority || '',
          guests: sotData.guests || '',
          tags: sotData.tags || '',
          server_message: sotData.server_message || '',
          status: sotData.status || 'draft',

          // SOT-specific fields
          video_path: videoPath,
          thumbnail_path: thumbnailPath,
          video_specs: JSON.stringify(sotData.videoSpecs || {}),
          cuts: JSON.stringify(sotData.cuts || {}), // Dictionary of cut information
          credits: JSON.stringify(sotData.credits || {}), // Dictionary of credits/lower thirds

          // Standard fields
          customer: sotData.customer || '',
          link: sotData.link || '',
          index: calculatedIndex // Required for proper rundown placement
        };
        
        console.log('Submitting SOT item to API:', newItem);
        console.log('Cut information:', sotData.cuts);
        console.log('Credits information:', sotData.credits);

        // Create the new SOT rundown item
        const paddedId = String(this.currentEpisodeNumber).padStart(4, '0');
        const response = await this.$http.post(`/api/episodes/${paddedId}/rundown/item`, newItem);
        
        if (response.data && response.data.success) {
          console.log('SOT item created successfully:', response.data);

          // Close the modal
          this.showNewSOTModal = false;

          // Reload episode rundown to show new item
          await this.loadEpisode(this.currentEpisodeNumber, false, true);

          // Find and flash the newly created item
          const newItemIndex = this.rundownItems.findIndex(item =>
            item.asset_id === response.data.asset_id
          );

          if (newItemIndex !== -1) {
            await this.flashNewlyCreatedItem(newItemIndex);
            this.selectedItemIndex = newItemIndex;
            this.selectRundownItem(newItemIndex);
          }

          // Show success message for cue creation
          this.$toast.success(`SOT cue "${sotData.slug}" created successfully!`);
        } else {
          throw new Error(response.data?.error || 'Failed to create SOT item');
        }
      } catch (error) {
        console.error('Error creating SOT item:', error);
        this.$toast.error(`Failed to create SOT item: ${error.response?.data?.error || error.message}`);
      } finally {
        this.creatingNewItem = false;
      }
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
    },

    // Handle slug changes from ShowInfoHeader
    handleSlugChange(newSlug) {
      console.log('Slug change from header:', newSlug);
      if (this.currentRundownItem) {
        this.currentRundownItem.slug = newSlug;
        this.onMetadataChange({ field: 'slug', value: newSlug });
      }
    },

    // Handle slug changes from EditorPanel slug field
    handleSlugChangeFromEditor(newSlug) {
      console.log('Slug change from editor:', newSlug);
      if (this.currentRundownItem) {
        this.currentRundownItem.slug = newSlug;
        this.onMetadataChange({ field: 'slug', value: newSlug });
      }
    },

    // Handle duration changes from EditorPanel duration field
    handleDurationChangeFromEditor(newDuration) {
      console.log('Duration change from editor:', newDuration);
      if (this.currentRundownItem) {
        this.currentRundownItem.duration = newDuration;
        this.onMetadataChange({ field: 'duration', value: newDuration });
      }
    },

    // Handle calculated duration from EditorPanel (auto-calculated based on content)
    // NOTE: Does NOT auto-save to prevent data loss. Duration saved with manual save only.
    handleDurationCalculated(calculatedDuration) {
      console.log('⏱️ Auto-calculated duration from content:', calculatedDuration);
      if (this.currentRundownItem) {
        this.currentRundownItem.duration = calculatedDuration;
        this.currentItemMetadata.duration = calculatedDuration;
        // Mark as having unsaved changes but do NOT trigger auto-save
        // Duration will be saved when user explicitly saves
        this.hasUnsavedChanges = true;
      }
    },

    // Handle other header field changes
    handleTitleChange(newTitle) {
      console.log('Title change from header:', newTitle);
      if (this.currentRundownItem) {
        this.currentRundownItem.title = newTitle;
        this.onMetadataChange({ field: 'title', value: newTitle });
      }
    },

    handleSubtitleChange(newSubtitle) {
      console.log('Subtitle change from header:', newSubtitle);
      if (this.currentRundownItem) {
        this.currentRundownItem.subtitle = newSubtitle;
        this.onMetadataChange({ field: 'subtitle', value: newSubtitle });
      }
    },

    handleDescriptionChange(newDescription) {
      console.log('Episode description change from header:', newDescription);
      this.currentEpisodeDescription = newDescription;
      this.hasUnsavedChanges = true;
    },

    handleEpisodeTitleChange(newEpisodeTitle) {
      console.log('Episode title change from header:', newEpisodeTitle);
      this.currentEpisodeTitle = newEpisodeTitle;
      this.hasUnsavedChanges = true;
    },

    handleGuestChange(newGuest) {
      console.log('Guest change from header:', newGuest);
      this.currentEpisodeGuest = newGuest;
      // You can add additional logic here to save to episode metadata
    },

    handleAirDateChange(newAirDate) {
      console.log('Air date change from header:', newAirDate);
      this.currentAirDate = newAirDate;
      this.hasUnsavedChanges = true;
    },

    handleAirTimeChange(newAirTime) {
      console.log('Air time change from header:', newAirTime);
      this.currentAirTime = newAirTime;
      this.hasUnsavedChanges = true;
    },

    handleAirTimezoneChange(newTimezone) {
      console.log('Air timezone change from header:', newTimezone);
      this.currentAirTimezone = newTimezone;
      this.hasUnsavedChanges = true;
    },

    handleProductionStatusChange(newStatus) {
      console.log('Production status change from header:', newStatus);
      this.currentProductionStatus = newStatus;
      this.hasUnsavedChanges = true;
    },

    async handleTakeThumbnail({ url }) {
      console.log('Taking thumbnail:', url);
      try {
        const response = await axios.post(`/api/episodes/${this.currentEpisodeNumber}/thumbnail/take`, {
          source_url: url
        });

        if (response.data.success) {
          this.confirmedThumbnailUrl = response.data.protected_url;
          this.takenSourceUrl = response.data.original_url; // Store the original source URL
          console.log('Thumbnail confirmed and protected:', response.data.protected_url);
          // Show success message
          this.$emit('show-snackbar', 'Thumbnail confirmed and protected', 'success');
        }
      } catch (error) {
        console.error('Failed to take thumbnail:', error);
        this.$emit('show-snackbar', 'Failed to confirm thumbnail', 'error');
      }
    },

    // Handler methods for ShowInfoHeader button actions
    handleToggleScriptReading() {
      // Delegate to EditorPanel
      if (this.$refs.editorPanel) {
        this.$refs.editorPanel.toggleScriptReading();
      }
    },

    handleRequestNewEpisodeAssetID() {
      // Delegate to EditorPanel
      if (this.$refs.editorPanel) {
        this.$refs.editorPanel.requestNewEpisodeAssetID();
      }
    },

    handleShowAssetIDInfo() {
      // Delegate to EditorPanel
      if (this.$refs.editorPanel) {
        this.$refs.editorPanel.showAssetIDInfo();
      }
    },

    // Generate script for current episode with specified preset
    async handleGenerateScript(preset = 'host_full') {
      console.log('🎬 handleGenerateScript called with preset:', preset);
      console.log('🎬 currentEpisodeNumber:', this.currentEpisodeNumber);

      if (!this.currentEpisodeNumber) {
        this.$toast.warning('No episode loaded');
        return;
      }

      // Reset progress state
      this.scriptGenCurrentStep = 0;
      this.scriptGenStatus = 'Starting script generation...';
      this.generatingHostScript = true;

      // Preset display names
      const presetNames = {
        'host_full': 'Host Script (Full)',
        'host_clean': 'Host Script (Clean)',
        'production': 'Production Rundown'
      };
      const presetName = presetNames[preset] || preset;

      // Animate through steps (simulated progress since API is single call)
      const animateProgress = () => {
        const statusMessages = [
          'Collecting rundown items...',
          'Processing media assets...',
          'Building HTML content...',
          'Generating PDF...',
          'Finalizing...'
        ];

        let step = 0;
        const interval = setInterval(() => {
          if (step < 4 && this.generatingHostScript) {
            step++;
            this.scriptGenCurrentStep = step;
            this.scriptGenStatus = statusMessages[step];
          } else {
            clearInterval(interval);
          }
        }, 800); // Advance every 800ms

        return interval;
      };

      const progressInterval = animateProgress();

      try {
        console.log(`🎬 Generating ${presetName} for episode:`, this.currentEpisodeNumber);

        const response = await this.$axios.post(`/scripts/generate/${this.currentEpisodeNumber}?preset=${preset}`);
        console.log('🎬 Script generation response:', response.data);

        // Complete progress animation
        clearInterval(progressInterval);
        this.scriptGenCurrentStep = 5;
        this.scriptGenStatus = 'Complete!';

        if (response.data.success) {
          const revision = response.data.revision || 1;
          const revisionText = revision > 1 ? ` (Revision ${revision})` : '';
          const filename = response.data.pdf_path ? response.data.pdf_path.split('/').pop() : '';

          // Brief delay to show completion
          await new Promise(resolve => setTimeout(resolve, 500));

          this.$toast.success(`✅ ${presetName} generated${revisionText}!\n${filename}`, { timeout: 5000 });

          // Refresh the generated scripts list in MetadataPanel
          if (this.$refs.metadataPanel && this.$refs.metadataPanel.loadGeneratedDocuments) {
            this.$refs.metadataPanel.loadGeneratedDocuments();
          }
        } else {
          this.scriptGenStatus = 'Error!';
          this.$toast.error(`❌ Error generating script: ${response.data.error}`, { timeout: 8000 });
        }
      } catch (error) {
        clearInterval(progressInterval);
        this.scriptGenStatus = 'Error!';
        console.error('🎬 Script generation failed:', error);
        console.error('🎬 Error response:', error.response);
        const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message;
        this.$toast.error(`❌ Failed to generate script: ${errorMsg}`, { timeout: 8000 });
      } finally {
        // Reset after a brief delay so user sees completion state
        setTimeout(() => {
          this.generatingHostScript = false;
          this.scriptGenCurrentStep = 0;
          this.scriptGenStatus = 'Initializing...';
        }, 300);
      }
    },

    // Generate media list for current episode
    // Uses backend GET endpoint which reads directly from database
    async handleGenerateMediaList() {
      if (!this.currentEpisodeNumber) {
        this.$toast.warning('No episode loaded');
        return;
      }

      // Reset progress state
      this.mediaListCurrentStep = 0;
      this.mediaListStatus = 'Starting media list generation...';
      this.generatingMediaList = true;

      // Animate progress while waiting for backend
      const animateProgress = () => {
        const statusMessages = [
          'Scanning rundown items...',
          'Extracting media cues...',
          'Checking media URLs...',
          'Building media list...',
          'Generating HTML...'
        ];

        let step = 0;
        const interval = setInterval(() => {
          if (step < 4 && this.generatingMediaList) {
            step++;
            this.mediaListCurrentStep = step;
            this.mediaListStatus = statusMessages[step];
          } else {
            clearInterval(interval);
          }
        }, 600);

        return interval;
      };

      const progressInterval = animateProgress();

      try {
        console.log('📋 Generating media list for episode:', this.currentEpisodeNumber);

        // Use GET endpoint - backend reads directly from database
        const response = await this.$axios.get(`/scripts/media-list/${this.currentEpisodeNumber}`);
        console.log('📋 Media list response:', response.data);

        // Complete progress animation
        clearInterval(progressInterval);
        this.mediaListCurrentStep = 5;
        this.mediaListStatus = 'Complete!';

        if (response.data.success) {
          const itemCount = response.data.item_count || 0;

          // Brief delay to show completion
          await new Promise(resolve => setTimeout(resolve, 500));

          this.$toast.success(`📋 Media list generated! ${itemCount} items`, { timeout: 5000 });

          // Refresh the generated scripts list in MetadataPanel
          if (this.$refs.metadataPanel && this.$refs.metadataPanel.loadGeneratedDocuments) {
            this.$refs.metadataPanel.loadGeneratedDocuments();
          }
        } else {
          this.mediaListStatus = 'Error!';
          this.$toast.error(`❌ Error: ${response.data.error}`, { timeout: 8000 });
        }
      } catch (error) {
        clearInterval(progressInterval);
        this.mediaListStatus = 'Error!';
        console.error('📋 Media list generation failed:', error);
        this.$toast.error(`❌ Failed to generate media list: ${error.response?.data?.detail || error.message}`, { timeout: 8000 });
      } finally {
        // Reset after a brief delay
        setTimeout(() => {
          this.generatingMediaList = false;
          this.mediaListCurrentStep = 0;
          this.mediaListStatus = 'Initializing...';
        }, 300);
      }
    },

    // Generate prompter files for current episode (STUB)
    handleGeneratePrompterFiles() {
      this.$toast.info('Prompter file generation coming soon!');
      console.log('📜 Prompter file generation requested for episode:', this.currentEpisodeNumber);
      // TODO: Implement prompter file generation
      // This will generate teleprompter-friendly text files with:
      // - Large text formatting
      // - Segment markers
      // - Timing cues
      // - Speaker attribution
    },

    // Flash newly created rundown item with locator flash color
    async flashNewlyCreatedItem(itemIndex) {
      console.log('Starting locator flash for item at index:', itemIndex);

      // Get the locator flash color from theme
      const flashColor = getColorValue('locatorflash') || getColorValue('locatorflash-interface') || 'deep-orange-accent-2';
      const resolvedFlashColor = resolveVuetifyColor(flashColor, this.$vuetify);

      // Ensure we have a valid hex color for DOM styling
      let hexFlashColor = resolvedFlashColor;
      if (!hexFlashColor || hexFlashColor === flashColor) {
        // If resolveVuetifyColor didn't convert properly, try manual conversion
        const vuetifyTheme = this.$vuetify?.theme?.current?.colors;
        if (vuetifyTheme) {
          // Try to get the color from the current theme
          const colorKey = flashColor.replace(/-/g, '');
          hexFlashColor = vuetifyTheme[colorKey] || vuetifyTheme[flashColor] || '#FF5722'; // Deep orange fallback
        } else {
          hexFlashColor = '#FF5722'; // Deep orange fallback
        }
      }

      console.log('Flash color config:', flashColor);
      console.log('Resolved flash color:', resolvedFlashColor);
      console.log('Final hex color:', hexFlashColor);

      // Wait a moment for DOM to update after item creation
      await new Promise(resolve => setTimeout(resolve, 100));

      // Find the rundown item card by looking for all rundown-item-card elements
      // and matching by the selectedItemIndex (which should match our target index)
      const rundownCards = document.querySelectorAll('.rundown-item-card');
      let rundownItemElement = null;

      // Try multiple approaches to find the correct element
      if (rundownCards.length > itemIndex) {
        rundownItemElement = rundownCards[itemIndex];
      }

      // Fallback: look for the selected item if it matches our target
      if (!rundownItemElement && this.selectedItemIndex === itemIndex) {
        rundownItemElement = document.querySelector('.rundown-item-card.selected-item');
      }

      // Another fallback: find by scanning all cards and checking their content
      if (!rundownItemElement && this.rundownItems && this.rundownItems[itemIndex]) {
        const indexNumber = (itemIndex + 1) * 10;

        for (const card of rundownCards) {
          const indexElement = card.querySelector('.index-number');
          if (indexElement && indexElement.textContent.trim() === String(indexNumber)) {
            rundownItemElement = card;
            break;
          }
        }
      }

      if (!rundownItemElement) {
        console.warn('Could not find rundown item element for flashing at index:', itemIndex);
        console.log('Available rundown cards:', rundownCards.length);
        console.log('Target index:', itemIndex);
        console.log('Selected index:', this.selectedItemIndex);
        return;
      }

      console.log('Found element to flash:', rundownItemElement);
      console.log('Using flash color:', resolvedFlashColor);

      // Store original styles
      const originalBackground = rundownItemElement.style.backgroundColor || '';
      const originalTransition = rundownItemElement.style.transition || '';
      const originalImportant = rundownItemElement.style.getPropertyPriority('background-color');

      // Add transition for smooth flashing (double speed)
      rundownItemElement.style.transition = 'background-color 100ms ease-in-out';

      try {
        // Flash 10 times: 100ms on, 100ms off (double speed, double count, same total duration)
        for (let i = 0; i < 10; i++) {
          // Flash ON (100ms) - use !important to override Vue computed styles
          rundownItemElement.style.setProperty('background-color', hexFlashColor, 'important');
          console.log(`Flash ${i + 1} ON - Color: ${hexFlashColor}`);
          await new Promise(resolve => setTimeout(resolve, 100));

          // Flash OFF (100ms) - restore original
          if (originalBackground) {
            rundownItemElement.style.setProperty('background-color', originalBackground, originalImportant);
          } else {
            rundownItemElement.style.removeProperty('background-color');
          }
          console.log(`Flash ${i + 1} OFF`);
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      } finally {
        // Restore original styles completely
        if (originalBackground) {
          rundownItemElement.style.setProperty('background-color', originalBackground, originalImportant);
        } else {
          rundownItemElement.style.removeProperty('background-color');
        }
        rundownItemElement.style.transition = originalTransition;
        console.log('Locator flash complete, styles restored');
      }

      // Scroll item into view if needed
      rundownItemElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    },

    /**
     * Generate test podcast segment using LLM (Developer Tool)
     * Triggered by Ctrl+Alt+Shift+[1-9]
     * @param {number} paragraphCount - Number of paragraphs to generate (1-9)
     */
    async generateTestSegment(paragraphCount) {
      console.log(`🧪 Generating test segment with ${paragraphCount} paragraphs...`);

      // ⚠️ CAPTURE TARGET ITEM IMMEDIATELY - Lock in the item at keypress time
      // This prevents race condition where user switches items during generation
      const targetItem = this.currentRundownItem;
      const targetItemId = targetItem?.id;

      if (!targetItem) {
        notifyUserStandard('No rundown item selected', NOTIFICATION_COLORS.ERROR, 3000);
        return;
      }

      // Get target item's duration or use default
      const duration = targetItem.duration || '3';
      const segmentType = targetItem.type || 'segment';

      // Get upcoming segments if this is a tease
      let upcomingSegments = '';
      if (segmentType === 'tease') {
        const currentIndex = this.rundownItems.findIndex(item => item.id === targetItemId);
        if (currentIndex >= 0) {
          // Get next few segments (skip other teases/ads)
          const upcoming = this.rundownItems
            .slice(currentIndex + 1)
            .filter(item => ['segment', 'coldopen'].includes(item.type))
            .slice(0, 3) // Get up to 3 upcoming segments
            .map(item => item.title || 'Untitled')
            .filter(title => title !== 'Untitled');

          if (upcoming.length > 0) {
            upcomingSegments = `\n\nUpcoming segments to tease:\n${upcoming.map(t => `- ${t}`).join('\n')}`;
          }
        }
      }

      // Show loading notification with LLM generating color
      notifyUserStandard(`Generating ${paragraphCount}-paragraph ${segmentType}...`, NOTIFICATION_COLORS.GENERATING);

      try {
        // Check if user is authenticated
        const token = localStorage.getItem('auth-token');
        if (!token) {
          notifyUserStandard('Please login to use LLM features', NOTIFICATION_COLORS.ERROR, 3000);
          return;
        }

        const { smartCall } = useLLM();

        // Target item already captured at function start (lines 4212-4213)

        // Fetch prompt template from settings based on segment type
        let promptName;
        if (segmentType === 'tease') {
          promptName = 'Segment Generator (Tease)';
        } else if (segmentType === 'coldopen') {
          promptName = 'Segment Generator (Cold Open)';
        } else {
          promptName = 'Segment Generator (Standard)';
        }

        // Get LLM routing settings from database
        let template = null;
        try {
          const response = await this.$axios.get('/settings/llm_routing');
          const prompts = response.data?.value?.prompts || [];
          const promptConfig = prompts.find(p => p.name === promptName && p.enabled);

          if (promptConfig) {
            template = promptConfig.template;
            console.log(`📋 Using prompt template: ${promptName}`);
          }
        } catch (error) {
          console.warn('Failed to load prompt from settings, using fallback:', error);
        }

        // Fallback to basic template if not found in settings
        if (!template) {
          console.warn(`⚠️ Prompt "${promptName}" not found in settings, using fallback template`);
          template = 'Write a {duration}-minute podcast {segmentType} with {paragraphs} paragraphs. DO NOT include any introductory text - start immediately with the content.';
        }

        const prompt = template
          .replace('{duration}', duration)
          .replace('{paragraphs}', paragraphCount)
          .replace('{upcomingSegments}', upcomingSegments)
          .replace('{segmentType}', segmentType);

        console.log('🎯 Calling smartCall with taskType: content-expansion');

        // Use Universal LLM Framework for visual feedback on rundown item
        const generatedText = await this.llmState.withLLM(
          'item',
          targetItemId,
          'generating',
          async () => {
            return await smartCall(prompt, {
              taskType: 'content-expansion',
              temperature: 0.8,
              max_tokens: 2000
            });
          },
          {
            notify: false, // Already showing toast notification
            metadata: {
              component: 'Content Editor',
              location: 'Test Segment Generator',
              operation: `${paragraphCount}-paragraph ${segmentType}`
            }
          }
        );

        // ⚠️ INSERT INTO TARGET ITEM - Not currently displayed item
        // Get target item's current script content (might be different from displayed scriptContent)
        const targetScript = targetItem?.script_content || '';

        console.log('📝 Generated text length:', generatedText?.length, 'chars');
        console.log('📝 Generated text preview:', generatedText?.substring(0, 100));
        console.log('🎯 Target item ID:', targetItemId, 'Title:', targetItem?.title);

        // Wrap each paragraph in <p class="josh"> tags for script mode parsing
        const paragraphs = generatedText.split(/\n\s*\n/).filter(p => p.trim());
        const wrappedParagraphs = paragraphs.map(p => `<p class="josh">${p.trim()}</p>`).join('\n\n');

        // Append generated segment with spacing
        const newScript = targetScript + (targetScript ? '\n\n' : '') + wrappedParagraphs;

        console.log('📝 New script length:', newScript.length, 'chars');

        // Update target item directly via API (not currently displayed item)
        try {
          await this.$axios.patch(`/episodes/${this.padEpisodeNumber(this.currentEpisodeNumber)}/item/${targetItemId}`, {
            script_content: newScript
          });

          // Update the target item in rundownItems array
          const itemIndex = this.rundownItems.findIndex(item => item.id === targetItemId);
          if (itemIndex !== -1) {
            this.rundownItems[itemIndex].script_content = newScript;
          }

          // If target item is currently displayed, update the editor
          if (this.currentRundownItem?.id === targetItemId) {
            this.updateScriptContent(newScript);

            // Force Vue to re-render in case reactivity doesn't trigger
            this.$nextTick(() => {
              console.log('🔄 After nextTick, scriptContent:', this.scriptContent?.substring(0, 100));
              // Force editor refresh if needed
              if (this.$refs.editorPanel && this.$refs.editorPanel.$forceUpdate) {
                this.$refs.editorPanel.$forceUpdate();
              }
            });
          }

          notifyUserStandard(`Test segment generated into "${targetItem?.title || 'item'}"!`, NOTIFICATION_COLORS.SUCCESS, 3000);
          console.log('✅ Test segment generated and inserted into target item');
        } catch (updateError) {
          console.error('❌ Failed to update target item:', updateError);
          notifyUserStandard('Failed to save generated content', NOTIFICATION_COLORS.ERROR, 3000);
        }

      } catch (error) {
        console.error('❌ Test segment generation failed:', error);
        notifyUserStandard(`Generation failed: ${error.message}`, NOTIFICATION_COLORS.ERROR, 5000);
      }
    }
  }
}
</script>

<style scoped>
.content-editor-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

/* Content Editor Loading Overlay */
.content-editor-loading-overlay :deep(.v-overlay__scrim) {
  opacity: 0 !important;
}

.content-editor-loading-overlay {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  pointer-events: none !important; /* Allow scrolling through the overlay */
}

.content-editor-loading-overlay :deep(.v-overlay__content) {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  pointer-events: all !important; /* Allow interaction with loading spinner */
  transform: translate(-50%, -50%) !important;
  width: auto !important;
  height: auto !important;
}

.content-editor-loading-overlay .loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.content-editor-loading-overlay .loading-text {
  font-size: 1.25rem;
  font-weight: 500;
  color: #333;
  text-align: center;
}

.content-editor-loading-overlay .loading-subtitle {
  font-size: 1rem;
  font-weight: 400;
  color: #666;
  text-align: center;
  margin-top: -10px;
}

/* Script Generation Overlay */
.script-generation-overlay {
  z-index: 10000 !important;
}

.script-generation-overlay :deep(.v-overlay__content) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.script-gen-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px 60px;
  background: rgba(30, 30, 30, 0.95);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  min-width: 320px;
}

.script-gen-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin-top: 8px;
}

.script-gen-episode {
  font-size: 1.1rem;
  color: #4caf50;
  font-weight: 500;
}

.script-gen-status {
  font-size: 0.95rem;
  color: #aaa;
  min-height: 24px;
}

.script-gen-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  width: 100%;
}

.script-gen-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #888;
  transition: all 0.3s ease;
}

.script-gen-step.step-active {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
  font-weight: 500;
}

.script-gen-step.step-done {
  color: #4caf50;
}

.script-gen-step.step-done span {
  text-decoration: line-through;
  opacity: 0.7;
}

/* Media List Theme (Blue) */
.media-list-theme {
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.media-list-ep {
  color: #2196f3 !important;
}

.script-gen-step.step-active-blue {
  background: rgba(33, 150, 243, 0.15);
  color: #2196f3;
  font-weight: 500;
}

.script-gen-step.step-done-blue {
  color: #2196f3;
}

.script-gen-step.step-done-blue span {
  text-decoration: line-through;
  opacity: 0.7;
}

.rundown-panel {
  width: 40%;
  max-height: 100vh; /* Limit to viewport height */
  overflow-y: auto; /* Internal scroll for rundown items */
  /* Remove static border-right so only dynamic border shows */
  /* border-right: 1px solid var(--v-divider-color, #E0E0E0); */
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  border: none; /* Remove all borders */
  border-radius: 0 !important;
  box-sizing: border-box;
  position: sticky; /* Stick to top when scrolling */
  top: 0; /* Stick at the top of the scroll container */
  z-index: 10; /* Appear above editor panel */
  align-self: flex-start; /* Required for sticky to work in flex container */
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
  overflow-x: hidden;
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
  opacity: 0.5;
  background: #e3f2fd;
  transform: scale(0.98);
}

/* SortableJS classes for drag feedback */
.rundown-item.chosen-class {
  opacity: 0.8;
  background: #fff3cd;
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.rundown-item.drag-class {
  opacity: 0.7;
  background: #d1ecf1;
  transform: rotate(2deg);
  box-shadow: 0 6px 16px rgba(0,0,0,0.3);
  z-index: 2000;
}

.rundown-item.dragging {
  opacity: 0.8;
  transform: translateZ(0);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
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
  height: auto; /* Grow with content */
  overflow-y: visible; /* No internal scroll - scrolls with page */
  overflow-x: visible; /* Allow flag note panels to overflow into sidebar area */
  position: relative;
  z-index: auto; /* Don't create stacking context - allows flag note panels to appear above sidebar */
  padding-bottom: 50vh; /* Add whitespace equal to 50% of viewport height */
}

/* Scrollable wrapper containing header + columns */
.scrollable-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* Main scroll - controls everything until header scrolls off */
  overflow-x: hidden;
  min-height: 0;
}

.main-content-area {
  display: flex;
  min-height: 0;
  height: auto; /* Allow to grow with content */
  overflow: visible;
  flex-shrink: 0; /* Don't shrink */
}

/* ShowInfoHeader - full width, scrolls off naturally */
.show-info-header {
  width: 100%;
  flex-shrink: 0; /* Don't compress the header */
  position: relative !important; /* NOT sticky - scrolls off */
  z-index: 1; /* Keep it above content but below modals */
  border-bottom: 1px solid var(--v-divider-color, #E0E0E0);
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

/* Removed duplicate .dragging rule - conflicts with .rundown-item.dragging */

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
/* Removed problematic transform rule that caused items to jump */



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

/* Vue.Draggable CSS classes for visual feedback */
/* Placeholder shown in drop position */
.rundown-item.ghost-class {
  opacity: 0.5;
  background: #e3f2fd !important;
  transform: scale(0.98);
  border: 2px dashed #2196F3 !important;
}

/* Applied when item is selected for dragging */
.rundown-item.chosen-class {
  opacity: 0.8;
  background: #fff3cd !important;
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  border: 2px solid #ffc107 !important;
}

/* Applied to the item being dragged */
.rundown-item.drag-class {
  opacity: 0.7;
  background: #d1ecf1 !important;
  transform: rotate(2deg) scale(1.05);
  box-shadow: 0 6px 16px rgba(0,0,0,0.3);
  z-index: 2000;
  border: 2px solid #17a2b8 !important;
}

/* Rundown Panel Reopen Button */
/* Rundown tab controls when panel is closed - positioned on left side */
.rundown-tab-controls-closed {
  position: fixed;
  left: 0;
  top: 50vh;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 100;
}

.rundown-tab-btn {
  border-radius: 0 8px 8px 0 !important;
  background-color: rgba(25, 118, 210, 0.9) !important;
  color: white !important;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3) !important;
  transition: all 0.2s ease !important;
  width: 32px !important;
  height: 40px !important;
}

.rundown-tab-btn:hover {
  background-color: rgba(25, 118, 210, 1) !important;
  transform: translateX(4px) !important;
  box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4) !important;
}

.rundown-tab-btn .v-icon {
  color: white !important;
}

/* Metadata Panel Reopen Button */
/* Metadata tab controls when panel is closed - positioned on right side */
.metadata-tab-controls-closed {
  position: fixed;
  right: 0;
  top: 50vh;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 100;
}

.metadata-tab-btn {
  border-radius: 8px 0 0 8px !important;
  background-color: rgba(25, 118, 210, 0.9) !important;
  color: white !important;
  box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.3) !important;
  transition: all 0.2s ease !important;
  width: 32px !important;
  height: 40px !important;
}

.metadata-tab-btn:hover {
  background-color: rgba(25, 118, 210, 1) !important;
  transform: translateX(-4px) !important;
  box-shadow: -4px 4px 12px rgba(0, 0, 0, 0.4) !important;
}

.metadata-tab-btn .v-icon {
  color: white !important;
}

</style>

