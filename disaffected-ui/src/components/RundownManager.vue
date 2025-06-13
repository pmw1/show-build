<template>
  <v-container>
    <!-- Header row with episode selector and save button -->
    <v-row class="align-center justify-space-between mb-4">
      <v-col cols="6">
        <h2>Rundown Editor</h2>
      </v-col>
      <v-col cols="6" class="text-right">
        <v-select
          v-model="selectedEpisode"
          :items="episodes"
          label="Select Episode"
          @change="loadEpisode"
          :disabled="loading"
        />
        <v-btn color="primary" class="ml-2" @click="saveChanges" :disabled="loading || segments.length === 0">
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
          v-if="!loading && segments.length > 0"
          v-model="segments" 
          :item-key="getItemKey"
          @start="dragStart"
          @end="dragEnd"
          @change="handleDragChange"
          :class="{ dragging: isDragging }"
        >
          <template #item="{ element, index }">
            <v-expand-transition>
              <v-card
                outlined
                :class="[
                  resolveTypeClass(element.type),
                  'elevation-1'
                ]"
              >
                <v-row no-gutters class="rundown-row">
                  <!-- Index + Type column -->
                  <v-col class="type-col">
                    <div class="type-cell">
                      <div class="type-label">{{ (element.type || 'UNKNOWN').toUpperCase() }}</div>
                      <div class="index-number">{{ (index + 1) * 10 }}</div>
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
  </v-container>
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
      selectedEpisode: "0225",
      episodes: ["0225", "0226", "0227"], // Can be made dynamic
      loading: false,
      isDragging: false,
      dragError: null
    };
  },
  methods: {
    getItemKey(item) {
      return item.asset_id || item.filename || item.order || Math.random().toString();
    },
    async loadEpisode() {
      this.loading = true;
      try {
        const response = await axios.get(`http://192.168.51.210:8888/rundown/${this.selectedEpisode}`);
        
        // Log full entry for item #20 (index 1)
        console.log("[DEBUG] Full Entry #20:", {
          raw: response.data[1],
          metadata: response.data[1].metadata,
          filename: response.data[1].filename
        });

        // Log advertisement entries
        const adverts = response.data.filter(entry => entry.metadata.type === 'advert');
        console.log("[DEBUG] Advertisement Entries:", adverts);

        this.segments = response.data.map(entry => {
          const processed = {
            ...entry.metadata,      // Spread metadata first
            filename: entry.filename,
            type: entry.metadata.type || 'unknown',
            slug: entry.metadata.slug || '',
            id: entry.metadata.id || 'No ID',
            duration: entry.metadata.duration || 'N/A',
            title: entry.metadata.title || '',
            description: entry.metadata.description || ''
          };
          
          // Debug each processed entry
          console.log("[DEBUG] Processed Entry:", {
            original: entry,
            processed: processed,
            fields: {
              slug: processed.slug,
              id: processed.id,
              duration: processed.duration,
              type: processed.type
            }
          });
          
          return processed;
        });

      } catch (err) {
        console.error("[ERROR] Failed to load rundown:", err);
        this.segments = [];
        alert(`Failed to load rundown for episode ${this.selectedEpisode}: ${err.message}`);
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
    },
    dragEnd() {
      this.isDragging = false;
    },
    handleDragChange(evt) {
      console.log("[DEBUG] Drag operation:", evt)
      // Validate new order if needed
    }
  },
  created() {
    const highlightColor = getColorValue('highlight');
    // Set initial highlight color with RGB values
    document.documentElement.style.setProperty('--highlight-color', `rgb(var(--v-theme-${highlightColor}))`);
  },
  mounted() {
    this.loadEpisode();
  },
};
</script>

<style scoped>
/* Force square corners everywhere */
.v-card,
.v-card.elevation-1,
:deep(.v-card),
:deep(.v-card__text) {
  border-radius: 0 !important;
}

/* Adjust layout sizes */
.rundown-row {
  min-height: 52px !important;  /* Increased for more content */
  max-height: 52px !important;
}

.type-col {
  width: 90px !important;     /* Widened for index number */
  min-width: 90px !important;
  max-width: 90px !important;
}

.type-cell {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.05);
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  padding: 4px;
}

.index-number {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 2px;
  font-family: monospace;  /* For better number alignment */
}

.type-label {
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 2px;
}

.content-cell {
  padding: 0;  /* Remove padding from content cell */
  height: 100%;
  display: flex;
  align-items: stretch;  /* Changed to stretch for full height */
  justify-content: space-between;
}

.slug-text {
  font-size: 0.95rem;
  font-weight: 400;
  flex-grow: 1;
  padding: 0 12px;  /* Move padding to slug-text */
  display: flex;
  align-items: center;
}

/* New duration box styling */
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

/* Clean up hover state */
.v-card.elevation-1:hover:not(.dragging):not(.sortable-chosen) {
  background: var(--highlight-color) !important;
  cursor: grab;
  transform: translateZ(0);
}

/* Dragged item animation - smooth left shift and improved contrast */
.dragging .v-card.sortable-chosen {
  background: var(--draglight-color) !important;
  cursor: grabbing !important;
  z-index: 100;
  transform: translateX(-45px) translateZ(20px) !important;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  color: rgba(0, 0, 0, 0.87) !important;
  animation: slide-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Replace rotation with subtle spacing animation */
.dragging .v-card:not(.sortable-chosen):not(.sortable-ghost) {
  transform: translateY(0);
  margin-bottom: 5px !important;
  opacity: 0.95;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Update ghost indicator */
.sortable-ghost {
  opacity: 0.7;
  background: var(--dropline-color) !important;
  border: 2px solid var(--dropline-color) !important;
  margin-bottom: 5px !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Add slide-left animation for dragged item */
@keyframes slide-left {
  from {
    transform: translateX(0) translateZ(20px);
  }
  to {
    transform: translateX(-45px) translateZ(20px);
  }
}
</style>
