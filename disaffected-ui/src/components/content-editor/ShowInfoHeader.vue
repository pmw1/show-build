<template>
  <v-card class="show-info-header full-width-bg" flat>
    <v-card-text class="pa-1">
      <div v-if="loadingRundown" style="margin-bottom: 8px;">
        <v-progress-linear indeterminate color="primary" height="4" rounded></v-progress-linear>
      </div>
      <div class="header-container">
        <div class="show-title-area">
          <!-- Editable Show Title -->
          <div class="show-title-container">
            <v-text-field
              :model-value="title || 'Disaffected'"
              @update:model-value="$emit('update:title', $event)"
              variant="plain"
              density="compact"
              class="show-title-input"
              hide-details
              single-line
              @blur="saveShowTitle"
              placeholder="Show Title"
            />
            <span v-if="isDummy" class="dummy-indicator"> (DUMMY)</span>
          </div>

          <p class="text-caption text-medium-emphasis mb-0">{{ displayEpisodeInfo }}</p>
          <p v-if="episodeAssetId" class="text-caption text-medium-emphasis mb-0 asset-id-display">{{ episodeAssetId }}</p>
        </div>

        <!-- Action Buttons (right side) -->
        <div class="action-buttons-area d-flex align-center gap-2">
          <!-- Metadata Panel Toggle -->
          <v-btn
            size="small"
            :color="showMetadataPanel ? 'secondary' : 'grey'"
            :variant="showMetadataPanel ? 'elevated' : 'outlined'"
            @click="$emit('toggle-metadata-panel')"
            class="metadata-toggle-btn px-3"
            rounded="0"
          >
            <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
            Metadata
            <v-tooltip activator="parent" location="bottom">{{ showMetadataPanel ? 'Hide Metadata Panel' : 'Show Metadata Panel' }}</v-tooltip>
          </v-btn>

          <!-- Vertical Divider -->
          <v-divider vertical class="mx-1"></v-divider>

          <!-- More Options Dropdown -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                size="small"
                color="grey"
                variant="outlined"
                class="more-options-btn px-3"
                rounded="0"
                v-bind="props"
              >
                <v-icon size="small" class="mr-1">mdi-dots-horizontal</v-icon>
                More Options
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="$emit('toggle-script-reading')" :disabled="!isXttsConfigured">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2" :color="isReadingScript ? 'error' : 'primary'">{{ isReadingScript ? 'mdi-stop' : 'mdi-volume-high' }}</v-icon>
                  {{ isReadingScript ? 'Stop Reading' : 'Read Script Aloud' }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ isXttsConfigured ? 'Read with XTTS' : 'XTTS not configured' }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="$emit('request-new-episode-assetid')">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2">mdi-refresh</v-icon>
                  Request New Episode AssetID
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('show-assetid-info')">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2">mdi-identifier</v-icon>
                  Show AssetID Info
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <!-- Vertical Divider -->
          <v-divider vertical class="mx-1"></v-divider>

          <!-- Save All Button (rightmost) -->
          <v-btn
            size="small"
            :color="saveState?.buttonColor || 'success'"
            variant="elevated"
            @click="$emit('save-all')"
            :disabled="saveState?.isDisabled ?? true"
            class="save-all-btn"
            rounded="0"
          >
            <v-icon size="small" class="mr-1">{{ saveState?.buttonIcon || 'mdi-check-circle' }}</v-icon>
            Save All
            <v-tooltip activator="parent" location="bottom">{{ saveState?.tooltip || 'Episode is synchronized - no changes to save' }}</v-tooltip>
          </v-btn>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap';

export default {
  name: 'ShowInfoHeader',
  emits: ['update:airDate', 'update:productionStatus', 'update:title', 'update:slug', 'update:episodeTitle', 'update:subtitle', 'update:guest', 'update:description', 'save-all', 'toggle-metadata-panel', 'toggle-script-reading', 'request-new-episode-assetid', 'show-assetid-info'],
  props: {
    title: {
      type: String,
      default: 'Disaffected'
    },
    episodeInfo: {
      type: String,
      default: 'Episode Production Workspace'
    },
    episodeAssetId: {
      type: String,
      default: ''
    },
    slug: {
      type: String,
      default: ''
    },
    episodeTitle: {
      type: String,
      default: ''
    },
    subtitle: {
      type: String,
      default: ''
    },
    guest: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    },
    airDate: {
      type: String,
      default: ''
    },
    productionStatus: {
      type: String,
      default: 'draft'
    },
    duration: {
      type: String,
      default: '00:00:00'
    },
    productionStatuses: {
      type: Array,
      default: () => [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ]
    },
    loadingRundown: {
      type: Boolean,
      default: false
    },
    isDummy: {
      type: Boolean,
      default: false
    },
    saveState: {
      type: Object,
      default: () => ({
        hasChanges: false,
        buttonText: 'Synchronized',
        buttonColor: 'success',
        buttonIcon: 'mdi-check-circle',
        isDisabled: true,
        tooltip: 'Episode is synchronized - no changes to save'
      })
    },
    showMetadataPanel: {
      type: Boolean,
      default: false
    },
    isXttsConfigured: {
      type: Boolean,
      default: false
    },
    isReadingScript: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    displayEpisodeInfo() {
      // Show episode title if available, otherwise fall back to episodeInfo prop
      if (this.episodeTitle && this.episodeTitle.trim()) {
        return this.episodeTitle;
      } else {
        return this.episodeInfo || 'Episode Production Workspace';
      }
    },
    statusColor() {
      // Status values now directly match color keys ('draft', 'approved', 'production', 'completed')
      const status = (this.productionStatus || '').toLowerCase();
      const colorName = getColorValue(status);
      const resolvedColor = resolveVuetifyColor(colorName);
      return resolvedColor || '#ccc'; // fallback to grey
    },
    statusFieldStyle() {
      if (!this.productionStatus) return {};
      
      // Status values now directly match color keys
      const status = this.productionStatus.toLowerCase();
      const colorName = getColorValue(status);
      const baseColor = resolveVuetifyColor(colorName);
      if (!baseColor) return {};
      
      // Create darker variant by reducing lightness
      const darkerTextColor = this.darkenColor(baseColor, 0.4); // 40% darker
      const darkerLabelColor = this.darkenColor(baseColor, 0.5); // 50% darker for labels
      
      // Create themed variations
      const bgColor = baseColor + '15'; // 15% opacity for subtle background
      const borderColor = baseColor + '80'; // 80% opacity for border
      
      return {
        '--status-bg-color': bgColor,
        '--status-border-color': borderColor,
        '--status-text-color': darkerTextColor,
        '--status-label-color': darkerLabelColor,
        '--status-base-color': baseColor
      };
    }
  },
  methods: {
    getStatusBackgroundColor(status) {
      if (!status || typeof status !== 'string') return 'transparent';
      try {
        const colorValue = getColorValue(status.toLowerCase());
        if (!colorValue) return 'transparent';
        // Add some transparency to make text readable
        return colorValue + '20'; // Add 20% opacity
      } catch (error) {
        console.warn('Error getting status color:', error);
        return 'transparent';
      }
    },
    saveShowTitle() {
      // Emit save event or handle save logic
      console.log('Saving show title');
    },
    saveSlug() {
      console.log('Saving slug');
    },
    saveEpisodeTitle() {
      console.log('Saving episode title');
    },
    saveSubtitle() {
      console.log('Saving subtitle');
    },
    saveGuest() {
      console.log('Saving guest');
    },
    saveDescription() {
      console.log('Saving description');
    },
    darkenColor(hexColor, factor) {
      // Remove # if present
      const hex = hexColor.replace('#', '');
      
      // Parse RGB components
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      
      // Darken by reducing each component
      const newR = Math.round(r * (1 - factor));
      const newG = Math.round(g * (1 - factor));
      const newB = Math.round(b * (1 - factor));
      
      // Convert back to hex
      const toHex = (c) => {
        const hex = c.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      };
      
      return '#' + toHex(newR) + toHex(newG) + toHex(newB);
    }
  }
};
</script>

<style scoped>
.show-info-header {
  border-bottom: 1px solid #e0e0e0;
  min-height: 0;
  height: auto;
  max-height: none;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  background-color: white;
  transition: height 0.2s;
  padding-top: 0;
  position: relative !important; /* Override any Vuetify position: sticky */
}

.full-width-bg {
  background-color: white;
  width: 100%;
}

.header-container {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 100%;
}

.show-title-area {
  min-width: 200px;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
}

.show-title-fit {
  width: 100%;
  display: block;
  white-space: normal;
  word-wrap: break-word;
  font-size: clamp(0.7rem, 1.4vw, 1.1rem) !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
}

.fields-area {
  display: grid;
  grid-template-columns: 200px;
  grid-gap: 0;
  row-gap: 0;
  flex: 2 1 600px;
  justify-content: flex-end;
  align-self: flex-start;
  justify-items: end;
}

.fields-area > * {
  grid-column: 1;
}

.showinfo-field {
  width: 200px !important; /* Fixed width for all fields */
  min-width: 200px !important;
  max-width: 200px !important;
  font-size: 0.8rem !important; /* 20% smaller font */
}

/* Clean Vuetify component styling with consistent dimensions */
:deep(.showinfo-field .v-field__input) {
  padding: 4px 8px !important; /* Reduced internal padding */
  min-height: 24px !important; /* Reduced height */
  font-size: 0.75rem !important; /* Smaller font */
  line-height: 1.2 !important;
}

:deep(.showinfo-field .v-field__field) {
  height: 24px !important; /* Reduced height */
  min-height: 24px !important;
}

:deep(.showinfo-field .v-field__outline) {
  --v-field-border-width: 2px !important; /* Slightly thicker border for theming */
}

/* Consistent select dropdown styling */
:deep(.showinfo-field .v-select__selection) {
  font-size: 0.8rem !important;
  line-height: 1.2 !important;
}

/* Status-themed field coloring using database colors */
:deep(.status-field .v-field),
:deep(.airdate-field .v-field),
:deep(.duration-field .v-field) {
  background-color: var(--status-bg-color, transparent) !important;
}

:deep(.status-field .v-field__outline),
:deep(.airdate-field .v-field__outline),
:deep(.duration-field .v-field__outline) {
  border-color: var(--status-border-color, currentColor) !important;
}

/* Status-themed text coloring - darker variants for all field values */
:deep(.status-field .v-field__input input),
:deep(.airdate-field .v-field__input input),
:deep(.duration-field .v-field__input input),
:deep(.status-field .v-select__selection) {
  color: var(--status-text-color, currentColor) !important;
  font-weight: 500 !important;
}

/* Status-themed labels - much darker variants */
:deep(.status-field .v-field-label),
:deep(.airdate-field .v-field-label),
:deep(.duration-field .v-field-label) {
  color: var(--status-label-color, currentColor) !important;
  opacity: 1 !important;
  font-weight: 500 !important;
}

/* Status indicator directly below duration field */
.status-indicator {
  width: 200px !important; /* Same width as text fields */
  height: 32px;
  background-color: var(--status-base-color, #ccc);
  color: #ffffff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  margin-top: 4px; /* Small gap between duration field and status */
  grid-column: 2; /* Place in same column as other fields */
}

:deep(.v-label) {
  top: 50% !important;
  transform: translateY(-50%) !important;
}

:deep(.v-field--focused .v-label),
:deep(.v-field--dirty .v-label) {
  top: 0 !important;
  transform: translateY(-50%) scale(0.75) !important;
}

.asset-id-display {
  font-family: 'Courier New', monospace !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  margin-top: 2px !important;
}

.show-title-container {
  display: flex;
  align-items: center;
  width: 100%;
  line-height: 1;
}

.dummy-indicator {
  color: #ff0000 !important;
  font-weight: bold !important;
  font-size: clamp(0.7rem, 1.4vw, 1.1rem) !important;
  text-transform: uppercase !important;
  margin-left: 4px;
  align-self: center;
  line-height: 1;
}

/* Editable field styling */
.show-title-input {
  width: 100% !important;
  margin-bottom: 2px !important;
}

.show-title-input :deep(.v-field__input) {
  font-size: clamp(0.7rem, 1.4vw, 1.1rem) !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
  padding: 0 !important;
  min-height: auto !important;
  width: 100% !important;
  line-height: 1 !important;
  display: flex !important;
  align-items: center !important;
}

.show-title-input :deep(.v-field__field) {
  padding: 0 !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  min-height: auto !important;
}

.slug-input,
.episode-title-input,
.subtitle-input,
.guest-input,
.description-input {
  width: 100% !important;
  margin-bottom: 4px !important;
}

.slug-input :deep(.v-field__input),
.episode-title-input :deep(.v-field__input),
.subtitle-input :deep(.v-field__input),
.guest-input :deep(.v-field__input) {
  font-size: 0.75rem !important;
  padding: 1px 0 !important;
  min-height: auto !important;
  width: 100% !important;
}

.description-input :deep(.v-field__input) {
  font-size: 0.75rem !important;
  padding: 1px 0 !important;
  min-height: auto !important;
  width: 100% !important;
}

.slug-input :deep(.v-field__field),
.episode-title-input :deep(.v-field__field),
.subtitle-input :deep(.v-field__field),
.guest-input :deep(.v-field__field),
.description-input :deep(.v-field__field) {
  width: 100% !important;
}

.show-title-input :deep(.v-field__outline),
.slug-input :deep(.v-field__outline),
.episode-title-input :deep(.v-field__outline),
.subtitle-input :deep(.v-field__outline),
.guest-input :deep(.v-field__outline),
.description-input :deep(.v-field__outline) {
  display: none !important;
}

/* Show subtle underline on hover/focus */
.show-title-input:hover :deep(.v-field__field),
.slug-input:hover :deep(.v-field__field),
.episode-title-input:hover :deep(.v-field__field),
.subtitle-input:hover :deep(.v-field__field),
.guest-input:hover :deep(.v-field__field),
.description-input:hover :deep(.v-field__field) {
  border-bottom: 1px solid rgba(0,0,0,0.2) !important;
}

.show-title-input:focus-within :deep(.v-field__field),
.slug-input:focus-within :deep(.v-field__field),
.episode-title-input:focus-within :deep(.v-field__field),
.subtitle-input:focus-within :deep(.v-field__field),
.guest-input:focus-within :deep(.v-field__field),
.description-input:focus-within :deep(.v-field__field) {
  border-bottom: 2px solid var(--v-theme-primary) !important;
}

/* Icon styling for all editable fields with icons */
.slug-input :deep(.v-field__prepend-inner),
.episode-title-input :deep(.v-field__prepend-inner),
.subtitle-input :deep(.v-field__prepend-inner),
.guest-input :deep(.v-field__prepend-inner),
.description-input :deep(.v-field__prepend-inner) {
  padding-right: 4px !important;
  opacity: 0.6;
}

.slug-input :deep(.v-field__prepend-inner .v-icon),
.episode-title-input :deep(.v-field__prepend-inner .v-icon),
.subtitle-input :deep(.v-field__prepend-inner .v-icon),
.guest-input :deep(.v-field__prepend-inner .v-icon),
.description-input :deep(.v-field__prepend-inner .v-icon) {
  font-size: 14px !important;
}

/* Action Buttons Area */
.action-buttons-area {
  flex-shrink: 0;
  min-width: fit-content;
}

/* Button Styles - Match EditorPanel toolbar buttons */
.save-all-btn {
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  height: 48px !important;
  min-height: 48px !important;
}

.save-all-btn:disabled {
  background-color: rgb(var(--v-theme-success)) !important;
  color: white !important;
  opacity: 1 !important;
}

.metadata-toggle-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.more-options-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}
</style>
