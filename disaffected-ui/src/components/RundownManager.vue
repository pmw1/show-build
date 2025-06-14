<template>
  <v-container fluid class="pa-0">
    <v-row class="header-row ma-0">
      <v-col cols="6" class="pa-4">
        <h2 class="text-h4 font-weight-bold">Rundown Editor</h2>
      </v-col>
      <v-col cols="6" class="d-flex align-center justify-end">
        <!-- Move status table here -->
        <v-table density="compact" class="status-table">
          <tbody>
            <tr>
              <td class="text-caption font-weight-medium">Duration:</td>
              <td class="text-caption">00:28:30</td>
            </tr>
            <tr>
              <td class="text-caption font-weight-medium">Segments:</td>
              <td class="text-caption">{{ segmentCount }}</td>
            </tr>
            <tr>
              <td class="text-caption font-weight-medium">Features:</td>
              <td class="text-caption">{{ featureCount }}</td>
            </tr>
            <tr>
              <td class="text-caption font-weight-medium">Promos:</td>
              <td class="text-caption">{{ promoCount }}</td>
            </tr>
            <tr>
              <td class="text-caption font-weight-medium">Adverts:</td>
              <td class="text-caption">{{ advertCount }}</td>
            </tr>
            <tr>
              <td class="text-caption font-weight-medium">CTAs:</td>
              <td class="text-caption">{{ stingCount }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-col>
    </v-row>

    <!-- Controls row - with episode selector in its own cell -->
    <v-row class="controls-row mb-4">
      <v-col cols="3" class="d-flex align-center">
        <!-- Episode selector cell -->
        <v-select
          v-model="selectedEpisode"
          :items="episodes"
          label="Episode Selector"
          :loading="loading"
          :disabled="loading"
          variant="outlined"
          density="compact"
          hide-details
          class="episode-select"
          style="width: 75px"
          :menu-props="{ 
            contentClass: 'episode-select-menu',
            transition: 'fade-transition',    // Try different transition
            origin: 'top',                    // Align with input
            offsetY: true,                    // Offset from input
            closeOnContentClick: true         // Close on selection
          }"
          @update:model-value="handleEpisodeChange"
        ></v-select>
      </v-col>
      
      <v-col cols="3">
        <!-- Empty spacer cell -->
      </v-col>
      
      <!-- Button column -->
      <v-col cols="6" class="d-flex align-end justify-end gap-2">
        <!-- Action buttons only -->
        <v-btn 
          color="error" 
          variant="outlined" 
          @click="revertChanges" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-undo</v-icon>
          Revert
        </v-btn>

        <v-btn 
          color="primary" 
          variant="outlined" 
          class="ml-2" 
          @click="compileRundown" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-cog</v-icon>
          Compile
        </v-btn>

        <v-btn 
          color="secondary" 
          variant="outlined" 
          class="ml-2" 
          @click="printRundown" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-printer</v-icon>
          Print
        </v-btn>

        <v-btn 
          color="success" 
          class="ml-2" 
          @click="saveChanges" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-content-save</v-icon>
          Save & Commit
        </v-btn>
      </v-col>
    </v-row>
    <!-- Rundown list -->
    <v-card-text>
      <div>
        <v-fade-transition>
          <div v-if="loading" class="text-center">
            <v-progress-circular 
              indeterminate 
              color="primary"
              size="64"
            />
            <p class="mt-2">Loading rundown...</p>
          </div>
        </v-fade-transition>

        <v-alert
          v-if="!loading && segments.length === 0"
          type="warning"
          outlined
          class="text-center"
        >
          No segments found for episode {{ selectedEpisode }}. 
          Check /mnt/sync/disaffected/episodes/{{ selectedEpisode }}/rundown/ for .md files.
        </v-alert>

        <draggable 
          v-model="segments" 
          :item-key="getItemKey"
          @start="dragStart"
          @end="dragEnd"
          @change="handleDragChange"
          :animation="150"
          :ghost-class="'sortable-ghost'"
          :chosen-class="'sortable-chosen'"
          :drag-class="'sortable-drag'"
        >
          <template #item="{ element, index }">
            <v-expand-transition>
              <v-card
                outlined
                :class="[
                  resolveTypeClass(element.type),
                  'elevation-1',
                  { 'single-click-effect': singleClickActive },
                  { 'double-click-effect': doubleClickActive }
                ]"
                @click="handleSingleClick(element)"
                @dblclick="handleDoubleClick(element)"
              >
                <v-row no-gutters class="rundown-row">
                  <!-- Index + Type column -->
                  <v-col class="type-col">
                    <div class="type-cell">
                      <div class="index-number">{{ (index + 1) * 10 }}</div>
                      <div class="type-label">{{ (element.type || 'UNKNOWN').toUpperCase() }}</div>
                    </div>
                  </v-col>

                  <!-- Content column -->
                  <v-col>
                    <div class="content-cell">
                      <div class="slug-text">{{ element.slug }}</div>
                      <div class="duration-box">{{ element.duration }}</div>
                    </div>
                  </v-col>
                </v-row>
              </v-card>
            </v-expand-transition>
          </template>
        </draggable>
      </div>
    </v-card-text>

    <!-- Add dialogs after v-container -->
    <v-dialog v-model="showUnavailableDialog" max-width="400">
      <v-card>
        <v-card-title>Unavailable</v-card-title>
        <v-card-text>
          This feature is not yet available. Talk to Kevin about when it will be ready.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showUnavailableDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showCompileDialog" max-width="400">
      <v-card>
        <v-card-title>Compile Script</v-card-title>
        <v-card-text>
          <v-radio-group v-model="compileTarget">
            <v-radio label="Director" value="director"></v-radio>
            <v-radio label="Host" value="host"></v-radio>
            <v-radio label="Prompter Operator" value="prompter"></v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="showCompileDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="handleCompile">Compile</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showPrintDialog" max-width="400">
      <v-card>
        <v-card-title>Print for</v-card-title>
        <v-card-text>
          <v-radio-group v-model="printTarget">
            <v-radio label="Director" value="director"></v-radio>
            <v-radio label="Host" value="host"></v-radio>
            <v-radio label="Prompter Operator" value="prompter"></v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="showPrintDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="handlePrint">Print</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>

  <!-- Add this right after your v-container closing tag -->
  <div 
    v-if="showClickOverlay" 
    class="click-overlay"
    :class="{ 'single': clickType === 'single', 'double': clickType === 'double' }"
  >
    {{ clickType === 'single' ? 'SINGLE CLICK' : 'DOUBLE CLICK' }}
  </div>
</template>

<script>
import draggable from "vuedraggable"
import axios from "axios"
import { getColorValue, defaultColors } from '../utils/themeColorMap'

export default {
  name: "RundownManager",
  components: { draggable },
  data() {
    return {
      segments: [],
      selectedEpisode: null,  // Remove hardcoded "0225"
      episodes: [],          // Will be populated from API
      loading: false,
      isDragging: false,
      dragError: null,
      showUnavailableDialog: false,
      showCompileDialog: false,
      showPrintDialog: false,
      compileTarget: 'director',
      printTarget: 'director',
      singleClickActive: false,
      doubleClickActive: false,
      clickTimer: null,
      showClickOverlay: false,
      clickType: ''
    };
  },
  computed: {
    segmentCount() {
      return this.segments.filter(item => item.type === 'segment').length;
    },
    promoCount() {
      return this.segments.filter(item => item.type === 'promo').length;
    },
    advertCount() {
      return this.segments.filter(item => item.type === 'advert').length;
    },
    featureCount() {
      return this.segments.filter(item => item.type === 'feature').length;
    },
    stingCount() {
      return this.segments.filter(item => item.type === 'sting').length;
    },
    ctaCount() {
      return this.segments.filter(item => item.type === 'cta').length;
    }
  },
  methods: {
    getItemKey(item) {
      return item.asset_id || item.filename || item.order || Math.random().toString();
    },
    async handleEpisodeChange(newValue) {
      console.log('[DEBUG] Episode changed to:', newValue);
      if (newValue) {
        await this.loadEpisode(newValue);
      }
    },
    async fetchEpisodes() {
      this.loading = true;
      try {
        const response = await axios.get('http://192.168.51.210:8888/episodes');
        this.episodes = response.data;
        
        // Set initial episode if none selected
        if (!this.selectedEpisode && this.episodes.length) {
          this.selectedEpisode = this.episodes[0];
          await this.loadEpisode();
        }
      } catch (err) {
        console.error('[ERROR] Failed to fetch episodes:', err);
      } finally {
        this.loading = false;
      }
    },
    async loadEpisode(episodeId) {
      if (!episodeId) return;
      
      this.loading = true;
      try {
        const response = await axios.get(
          `http://192.168.51.210:8888/rundown/${episodeId}`
        );
        this.segments = response.data.map(entry => ({
          ...entry.metadata,
          filename: entry.filename,
          type: entry.metadata.type || 'unknown',
          slug: entry.metadata.slug || '',
          id: entry.metadata.id || 'No ID',
          duration: entry.metadata.duration || 'N/A'
        }));
      } catch (err) {
        console.error('[ERROR] Failed to load rundown:', err);
        this.segments = [];
      } finally {
        this.loading = false;
      }
    },
    async saveChanges() {
      try {
        const payload = { segments: this.segments.map(segment => ({ filename: segment.filename })) };
        const response = await axios.post(
          `http://192.168.51.210:8888/rundown/${this.selectedEpisode}/reorder`,
          payload
        );
        console.log("[DEBUG] Rundown saved:", response.data);
        alert("Rundown reordered successfully!");
      } catch (err) {
        console.error("[ERROR] Failed to save rundown:", err);
        alert("Failed to save rundown: " + err.message);
      }
    },
    revertChanges() {
      this.showUnavailableDialog = true;
    },
    compileRundown() {
      this.showCompileDialog = true;
    },
    handleCompile() {
      console.log(`Compiling for ${this.compileTarget}`);
      this.showCompileDialog = false;
      // Implement actual compilation
    },
    printRundown() {
      this.showPrintDialog = true;
    },
    handlePrint() {
      console.log(`Printing for ${this.printTarget}`);
      this.showPrintDialog = false;
      // Implement actual printing
    },
    resolveTypeClass(type) {
      if (!type || type === 'unknown') {
        console.log("[DEBUG] Resolving unknown type:", type);
        return 'bg-grey-light';
      }
      
      const normalizedType = type.toLowerCase();
      console.log("[DEBUG] Type before color lookup:", {
        original: type,
        normalized: normalizedType
      });
      
      const color = getColorValue(normalizedType);
      const cssClass = `bg-${color}`;
      
      console.log("[DEBUG] Final color resolution:", {
        type: normalizedType,
        color: color,
        cssClass: cssClass,
        availableColors: defaultColors
      });
      
      return cssClass;
    },
    dragStart() {
      this.isDragging = true;
      const dragLightColor = getColorValue('draglight');
      const highlightColor = getColorValue('highlight');
      const droplineColor = getColorValue('dropline');  // Add dropline color
    
      // DEBUG: Log all color values
      console.log("[DEBUG] Raw color values:", {
        dragLight: dragLightColor,
        highlight: highlightColor,
        dropline: droplineColor
      });
    
      // Set all CSS custom properties
      document.documentElement.style.setProperty('--highlight-color', `rgb(var(--v-theme-${highlightColor}))`);
      document.documentElement.style.setProperty('--draglight-color', `rgb(var(--v-theme-${dragLightColor}))`);
      document.documentElement.style.setProperty('--dropline-color', `rgb(var(--v-theme-${droplineColor}))`);

      // Force a reflow to ensure animation triggers consistently
      requestAnimationFrame(() => {
        document.body.offsetHeight;
      });
    },
    dragEnd() {
      this.isDragging = false;

      // Force animation reset
      requestAnimationFrame(() => {
        document.body.offsetHeight;
      });
    },
    handleDragChange(evt) {
      console.log("[DEBUG] Drag operation:", evt)
      // Validate new order if needed
    },
    handleSingleClick(item) {
      clearTimeout(this.clickTimer);
      this.clickTimer = setTimeout(() => {
        if (!this.doubleClickActive) {
          console.log('Single click on:', item);
          this.singleClickActive = true;
          // Show overlay
          this.clickType = 'single';
          this.showClickOverlay = true;
          setTimeout(() => {
            this.singleClickActive = false;
            this.showClickOverlay = false;
          }, 500);
        }
      }, 200);
    },
    handleDoubleClick(item) {
      clearTimeout(this.clickTimer);
      this.doubleClickActive = true;
      console.log('Double click on:', item);
      // Show overlay
      this.clickType = 'double';
      this.showClickOverlay = true;
      setTimeout(() => {
        this.doubleClickActive = false;
        this.showClickOverlay = false;
      }, 500);
    }
  },
  watch: {
    // Watch for route changes
    '$route.params.episode': {
      handler(newEpisode) {
        if (newEpisode && newEpisode !== this.selectedEpisode) {
          this.selectedEpisode = newEpisode;
          this.loadEpisode(newEpisode);
        }
      },
      immediate: true
    },
    
    // Watch for episode selection changes
    selectedEpisode(newEpisode) {
      if (newEpisode && newEpisode !== this.$route.params.episode) {
        this.$router.push({
          name: 'rundown',
          params: { episode: newEpisode }
        });
      }
    }
  },
  created() {
    const highlightColor = getColorValue('highlight');
    // Set initial highlight color with RGB values
    document.documentElement.style.setProperty('--highlight-color', `rgb(var(--v-theme-${highlightColor}))`);
  },
  mounted() {
    this.fetchEpisodes();  // Get episode list first
    if (this.selectedEpisode) {
      this.loadEpisode();        // Then load selected episode
    }
  },
};
</script>

<style scoped>
/*============================================================
  🛡️ PROTECTED: CORE RUNDOWN STYLES - DO NOT MODIFY 
============================================================*/

/* Force square corners */
.v-card,
.v-card.elevation-1,
:deep(.v-card),
:deep(.v-card__text) {
  border-radius: 0 !important;
}

/* Core layout structure */
.rundown-row {
  min-height: 42px !important;
  max-height: 42px !important;
  width: 100%;
  margin: 0;
}

.type-col {
  width: 120px !important;
  min-width: 120px !important;
  max-width: 120px !important;
}

/* Cell styling */
.type-cell {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
  padding: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.1);
}

.index-number {
  font-size: 0.85rem;
  font-weight: 700;
  opacity: 0.9;
  font-family: monospace;
  min-width: 35px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  color: rgba(255, 255, 255, 0.95);
  z-index: 1;
}

/* Drag and drop states */
.sortable-chosen {
  background: var(--draglight-color) !important;
  cursor: grabbing !important;
  transform: translateX(-35px) !important;
  z-index: 100;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  color: rgba(0, 0, 0, 0.87) !important;  /* Add high contrast for dragged item */
}

.sortable-chosen .index-number {
  color: rgba(255, 255, 255, 0.95) !important;  /* Keep index number white */
}

.sortable-chosen .type-label,
.sortable-chosen .slug-text,
.sortable-chosen .duration-box {
  color: rgba(0, 0, 0, 0.87) !important;  /* Ensure text is dark for contrast */
}

.sortable-ghost {
  opacity: 0.5;
  background: var(--highlight-color) !important;
  border: 2px dashed var(--dropline-color) !important;
}

.sortable-drag {
  opacity: 0.3;
}

/* Hover states */
.v-card.elevation-1:hover:not(.dragging):not(.sortable-chosen) {
  background: var(--highlight-color) !important;
  cursor: grab;
  color: rgba(0, 0, 0, 0.87) !important;
}

/*============================================================
  🛡️ END PROTECTED CORE STYLES
============================================================*/

/* Safe to modify styles below this line */

/* Adjust container padding */
:deep(.v-container) {
  padding: 0 !important;
}

/* Remove card text padding */
:deep(.v-card-text) {
  padding: 0 !important;
}

/* Update header row and controls row to match */
.header-row,
.controls-row {
  background: rgba(0, 0, 0, 0.03);
  padding: 8px 16px;  /* Consistent padding */
  margin: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  width: 100%;
}

/* Update controls row styling */
.controls-row {
  margin: 0;
  padding: 0 !important;
  width: 100%;
  background: transparent;
  border: none;
}

/* Update button styling in the scoped styles section */
.controls-row .v-btn {
  --v-btn-height: 40px !important;  /* Increased from 28px to match v-select */
  font-size: 0.875rem !important;   /* Slightly larger font */
  letter-spacing: 0.25px !important;
  padding: 0 16px !important;       /* Increased padding */
}

.controls-row .v-btn .v-icon {
  font-size: 18px !important;       /* Slightly larger icons */
  margin-right: 4px !important;     /* Space between icon and text */
}

/* Update episode select to ensure consistent height */
:deep(.episode-select .v-field) {
  background: white !important;
  border: 2px solid rgb(var(--v-theme-primary)) !important;
  border-radius: 4px !important;
  height: 40px !important;
  min-height: 40px !important;
}

:deep(.episode-select .v-field__input) {
  min-height: 40px !important;  /* Removed the extra '0' */
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  font-size: 1.25rem !important;
  font-weight: 500 !important;
  color: rgb(var(--v-theme-primary)) !important;  /* Blue text */
}

:deep(.episode-select .v-field__field .v-label) {
  position: absolute !important;
  top: -32px !important;
  left: 0 !important;
  transform: none !important;
  font-size: 0.75rem !important;
  color: rgb(var(--v-theme-primary)) !important;  /* Blue label */
  background: transparent !important;
  z-index: 1 !important;
  margin: 0 !important;
  padding: 0 !important;
  transition: none !important;
}

/* Update dropdown icon color */
:deep(.episode-select .v-field__append-inner) {
  color: rgb(var(--v-theme-primary)) !important;  /* Blue dropdown arrow */
}

/* Update just the status table styling */
.status-table {
  background: transparent !important;
  margin: 0 !important;
  padding: 0 !important;
  min-width: 180px !important;
}

.status-table :deep(td) {
  height: 16px !important;
  padding: 0 !important;
  border: none !important;
  white-space: nowrap !important;
  text-align: left !important;
}

/* Minimal spacing between value and label */
.status-table :deep(td:last-child) {
  padding-left: 4px !important;
}

/* Header styling */
.status-table :deep(th) {
  padding: 0 0 2px 0 !important;
}

/* Make rows full width */
.rundown-row {
  min-height: 42px !important;
  max-height: 42px !important;
  width: 100%;
  margin: 0;
}

/* Adjust layout sizes */
.rundown-row {
  min-height: 42px !important;  /* Reduced from 52px */
  max-height: 42px !important;
}

.type-col {
  width: 120px !important;     /* Adjusted for horizontal layout */
  min-width: 120px !important;
  max-width: 120px !important;
}

/* Update type cell and index number styling */
.type-cell {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;                /* Remove gap between index and type */
  padding: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.1);
}

.index-number {
  font-size: 0.85rem;
  font-weight: 700;            /* Increased to 700 for bolder index numbers */
  opacity: 0.9;
  font-family: monospace;
  min-width: 35px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0;
  color: rgba(255, 255, 255, 0.95);
  z-index: 1;
}

/* Type label specific styling */
.type-label {
  font-size: 0.75rem !important;  /* Smaller size */
  font-weight: 400 !important;    /* Normal weight */
  flex-grow: 1 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 !important;
  height: 100% !important;
}

/* Slug text specific styling */
.slug-text {
  font-size: 1.05rem !important;  /* Larger size */
  font-weight: 700 !important;    /* Bold weight */
  flex-grow: 1 !important;
  padding: 0 12px !important;
  display: flex !important;
  align-items: center !important;
}

.content-cell {
  padding: 0;  /* Remove padding from content cell */
  height: 100%;
  display: flex;
  align-items: stretch;  /* Changed to stretch for full height */
  justify-content: space-between;
}

.duration-box {
  font-size: 0.8rem;
  font-family: monospace;
  background: rgba(0, 0, 0, 0.1);
  padding: 0 12px;
  white-space: nowrap;
  width: 100px;  /* Set fixed width instead of min-width */
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid rgba(0, 0, 0, 0.05);  /* Optional subtle separator */
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Enhanced transition effects */
.v-scale-transition-enter-active,
.v-scale-transition-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.v-scale-transition-enter-from,
.v-scale-transition-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Clean up hover state and improve text contrast */
.v-card.elevation-1:hover:not(.dragging):not(.sortable-chosen) {
  background: var(--highlight-color) !important;
  cursor: grab;
  transform: translateZ(0);
  color: rgba(0, 0, 0, 0.87) !important;  /* Add high contrast text */
}

/* Add specific contrast for light/dark backgrounds on hover */
.v-card.elevation-1:hover[class*="bg-light"]:not(.dragging):not(.sortable-chosen) {
  color: rgba(0, 0, 0, 0.87) !important;
}

.v-card.elevation-1:hover[class*="bg-dark"]:not(.dragging):not(.sortable-chosen),
.v-card.elevation-1:hover.bg-blue-accent:not(.dragging):not(.sortable-chosen),
.v-card.elevation-1:hover.bg-purple-accent:not(.dragging):not(.sortable-chosen),
.v-card.elevation-1:hover.bg-indigo-accent:not(.dragging):not(.sortable-chosen) {
  color: rgba(255, 255, 255, 0.95) !important;
}

/* Base card state */
.v-card {
  transform: translateX(0);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.4, 1);
  will-change: transform;
}

/* Dragged item */
.sortable-chosen {
  background: var(--draglight-color) !important;
  cursor: grabbing !important;
  transform: translateX(-35px) !important;
  z-index: 100;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  color: rgba(0, 0, 0, 0.87) !important;  /* Add high contrast for dragged item */
}

.sortable-chosen .index-number {
  color: rgba(255, 255, 255, 0.95) !important;  /* Keep index number white */
}

.sortable-chosen .type-label,
.sortable-chosen .slug-text,
.sortable-chosen .duration-box {
  color: rgba(0, 0, 0, 0.87) !important;  /* Ensure text is dark for contrast */
}

/* Ghost placeholder */
.sortable-ghost {
  opacity: 0.5;
  background: var(--highlight-color) !important;
  border: 2px dashed var(--dropline-color) !important;
}

/* Hide drag clone */
.sortable-drag {
  opacity: 0.3;
}

/* Update modal and overlay styling */
:deep(.v-dialog) {
  border: 20px solid rgba(0, 0, 0, 0.95) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
  animation: modal-enter 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: visible !important;
  margin: 24px !important;
}

:deep(.v-dialog .v-card) {
  padding: 24px !important;
  margin: 0 !important;
  border-radius: 0 !important;
  background: white !important;
  box-shadow: none !important;
}

/* Update modal content spacing */
:deep(.v-dialog .v-card-title) {
  font-size: 1.5rem !important;
  padding: 0 0 20px 0 !important;
  margin: 0 !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
}

:deep(.v-dialog .v-card-text) {
  padding: 24px 0 !important;
  margin: 0 !important;
}

:deep(.v-dialog .v-card-actions) {
  padding: 20px 0 0 0 !important;
  margin: 0 !important;
  border-top: 1px solid rgba(0, 0, 0, 0.1) !important;
}

/* Update radio group spacing */
:deep(.v-dialog .v-radio-group) {
  padding: 8px 0 !important;
}

/* Enhanced blur effect for overlay */
:deep(.v-overlay__scrim) {
  backdrop-filter: blur(3px) !important;
  background: rgba(0, 0, 0, 0.4) !important;
}

/* Click effect animations */
@keyframes singleClickPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}

@keyframes doubleClickShake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
  100% { transform: translateX(0); }
}

.single-click-effect {
  animation: singleClickPulse 0.5s ease-out;
}

.double-click-effect {
  animation: doubleClickShake 0.5s ease-in-out;
  background: var(--highlight-color) !important;
}

/* Update the episode selector styles */
:deep(.episode-select) {
  margin-top: 16px !important;
  position: relative !important;
  z-index: 2 !important;
}

:deep(.episode-select .v-label) {
  position: absolute !important;
  top: -22px !important;              /* Changed from -20px to -22px */
  left: -4px !important;
  transform: none !important;
  font-size: 0.75rem !important;
  color: rgb(var(--v-theme-primary)) !important;
  background-color: white !important;
  padding: 0 4px !important;
  margin: 0 !important;
  z-index: 3 !important;
  white-space: nowrap !important;
  width: auto !important;
  min-width: max-content !important;
  pointer-events: none !important;
}
</style>

<style>
/* Global styles - no scoping */
/* Modal styles stay the same */
.v-overlay__content:where(.v-dialog) {
  border: 10px solid black !important;
  border-radius: 0 !important;
  overflow: hidden !important;
}

/* Episode selector dropdown menu styling */
.episode-select-menu {
  margin-top: 4px !important;
  border: none !important;
  border-radius: 4px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  background: rgb(var(--v-theme-primary)) !important;
  overflow: hidden !important;
}

.episode-select-menu .v-list {
  background: rgb(var(--v-theme-primary)) !important;
  padding: 4px !important;
  min-width: 75px !important;
}

.episode-select-menu .v-list-item {
  min-height: 36px !important;
  font-size: 1.1rem !important;
  padding: 0 12px !important;
  color: white !important;
  text-align: left !important;     /* Changed from center to left */
  display: flex !important;
  align-items: center !important;
}

/* Custom scrollbar styling */
.episode-select-menu ::-webkit-scrollbar {
  width: 8px !important;
}

.episode-select-menu ::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1) !important;
}

.episode-select-menu ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3) !important;
  border-radius: 4px !important;
}

.episode-select-menu ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5) !important;
}
</style>
