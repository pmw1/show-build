<template>
  <v-card class="show-info-header full-width-bg" flat>
    <v-card-text class="pa-3">
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
          
          <!-- Editable Slug -->
          <v-text-field
            :model-value="slug"
            @update:model-value="$emit('update:slug', $event)"
            variant="plain"
            density="compact"
            class="slug-input"
            hide-details
            single-line
            @blur="saveSlug"
            placeholder="episode-slug"
            prepend-inner-icon="mdi-link-variant"
          />
          
          <!-- Editable Episode Title -->
          <v-text-field
            :model-value="episodeTitle"
            @update:model-value="$emit('update:episodeTitle', $event)"
            variant="plain"
            density="compact"
            class="episode-title-input"
            hide-details
            single-line
            @blur="saveEpisodeTitle"
            placeholder="Episode title"
            prepend-inner-icon="mdi-television-classic"
          />

          <!-- Editable Subtitle -->
          <v-text-field
            :model-value="subtitle"
            @update:model-value="$emit('update:subtitle', $event)"
            variant="plain"
            density="compact"
            class="subtitle-input"
            hide-details
            single-line
            @blur="saveSubtitle"
            placeholder="Episode subtitle"
            prepend-inner-icon="mdi-text"
          />

          <!-- Editable Guest(s) -->
          <v-text-field
            :model-value="guest"
            @update:model-value="$emit('update:guest', $event)"
            variant="plain"
            density="compact"
            class="guest-input"
            hide-details
            single-line
            @blur="saveGuest"
            placeholder="Guest(s)"
            prepend-inner-icon="mdi-account-multiple"
          />

          <!-- Editable Description -->
          <v-textarea
            :model-value="description"
            @update:model-value="$emit('update:description', $event)"
            variant="plain"
            density="compact"
            class="description-input"
            hide-details
            rows="2"
            auto-grow
            @blur="saveDescription"
            placeholder="Episode description"
            prepend-inner-icon="mdi-text-long"
          />
        </div>

        <div class="fields-area">
          <v-select
            label="Episode"
            :model-value="episodeNumber"
            :items="episodes"
            item-title="title"
            item-value="value"
            variant="outlined"
            density="compact"
            class="showinfo-field episode-field"
            :style="statusFieldStyle"
            hide-details
            @update:model-value="(newEpisode) => $emit('episode-changed', newEpisode)"
            :item-props="episode => ({
              title: (typeof episode.title === 'string')
                ? episode.title.split(':')[0] + (episode.title.includes(':') ? ':' : '') + ' ' + (episode.title.split(':')[1] ? episode.title.split(':')[1].trim() : '')
                : ''
            })"
          ></v-select>

          <v-select
            label="Status"
            :model-value="productionStatus"
            :items="productionStatuses"
            item-title="title"
            item-value="value"
            variant="outlined"
            density="compact"
            class="showinfo-field status-field"
            :style="statusFieldStyle"
            hide-details
            @update:model-value="$emit('update:productionStatus', $event)"
          ></v-select>

          <v-text-field
            label="Air Date"
            :model-value="airDate"
            variant="outlined"
            density="compact"
            class="showinfo-field airdate-field"
            :style="statusFieldStyle"
            hide-details
            @update:model-value="$emit('update:airDate', $event)"
          ></v-text-field>

          <v-text-field
            label="Duration"
            :model-value="duration"
            variant="outlined"
            density="compact"
            class="showinfo-field duration-field"
            :style="statusFieldStyle"
            hide-details
            readonly
          ></v-text-field>
          
          <!-- Status indicator directly below duration field -->
          <div class="status-indicator" :style="statusFieldStyle">
            {{ productionStatus ? productionStatus.toUpperCase() : 'DRAFT' }}
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap';

export default {
  name: 'ShowInfoHeader',
  emits: ['update:episodeNumber', 'update:airDate', 'update:productionStatus', 'episode-changed', 'update:title', 'update:slug', 'update:episodeTitle', 'update:subtitle', 'update:guest', 'update:description'],
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
    episodeNumber: {
      type: [String, Number],
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
    episodes: {
      type: Array,
      default: () => []
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
    }
  },
  computed: {
    displayEpisodeInfo() {
      // Show episode title if available, otherwise fall back to episode number info
      if (this.episodeTitle && this.episodeTitle.trim()) {
        return this.episodeTitle;
      } else if (this.episodeNumber) {
        return `Episode ${String(this.episodeNumber).padStart(4, '0')}`;
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
  position: relative;
  transition: height 0.2s;
  padding-top: 0;
}

.full-width-bg {
  background-color: white;
  width: 100%;
}

.header-container {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 16px;
  align-content: flex-start;
  height: 100%;
}

.show-title-area {
  width: 320px;
  min-width: 200px;
  max-width: 400px;
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
}

.show-title-fit {
  width: 100%;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: clamp(0.94rem, 2.1vw, 1.7rem) !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
}

.fields-area {
  display: grid;
  grid-template-columns: 0 200px 0;
  grid-gap: 0;
  row-gap: 0;
  flex: 2 1 600px;
  justify-content: flex-end;
  align-self: flex-start;
  justify-items: end;
}

.fields-area > * {
  grid-column: 2;
}

.showinfo-field {
  width: 200px !important; /* Fixed width for all fields */
  min-width: 200px !important;
  max-width: 200px !important;
  font-size: 0.8rem !important; /* 20% smaller font */
}

/* Clean Vuetify component styling with consistent dimensions */
:deep(.showinfo-field .v-field__input) {
  padding: 10px 12px !important; /* Consistent internal padding */
  min-height: 36px !important; /* Consistent height */
  font-size: 0.8rem !important; /* 20% smaller font */
  line-height: 1.2 !important;
}

:deep(.showinfo-field .v-field__field) {
  height: 36px !important; /* Consistent height */
  min-height: 36px !important;
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
:deep(.episode-field .v-field),
:deep(.airdate-field .v-field),
:deep(.duration-field .v-field) {
  background-color: var(--status-bg-color, transparent) !important;
}

:deep(.status-field .v-field__outline),
:deep(.episode-field .v-field__outline),
:deep(.airdate-field .v-field__outline),
:deep(.duration-field .v-field__outline) {
  border-color: var(--status-border-color, currentColor) !important;
}

/* Status-themed text coloring - darker variants for all field values */
:deep(.status-field .v-field__input input),
:deep(.episode-field .v-field__input input),
:deep(.airdate-field .v-field__input input),
:deep(.duration-field .v-field__input input),
:deep(.status-field .v-select__selection),
:deep(.episode-field .v-select__selection) {
  color: var(--status-text-color, currentColor) !important;
  font-weight: 500 !important;
}

/* Status-themed labels - much darker variants */
:deep(.status-field .v-field-label),
:deep(.episode-field .v-field-label),
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
  font-size: clamp(0.94rem, 2.1vw, 1.7rem) !important;
  text-transform: uppercase !important;
  margin-left: 4px;
  align-self: center;
  line-height: 1;
}

/* Editable field styling */
.show-title-input {
  width: 100% !important;
  margin-bottom: 4px !important;
}

.show-title-input :deep(.v-field__input) {
  font-size: clamp(0.94rem, 2.1vw, 1.7rem) !important;
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
  font-size: 0.875rem !important;
  padding: 2px 0 !important;
  min-height: auto !important;
  width: 100% !important;
}

.description-input :deep(.v-field__input) {
  font-size: 0.875rem !important;
  padding: 2px 0 !important;
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
</style>
