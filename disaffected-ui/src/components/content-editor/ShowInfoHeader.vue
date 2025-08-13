<template>
  <v-card class="show-info-header full-width-bg" flat>
    <v-card-text class="pa-3">
      <div v-if="loadingRundown" style="margin-bottom: 8px;">
        <v-progress-linear indeterminate color="primary" height="4" rounded></v-progress-linear>
      </div>
      <div class="header-container">
        <div class="show-title-area">
          <h2 class="show-title-fit text-h5 mb-1">{{ title || 'Disaffected' }}</h2>
          <p class="text-caption text-medium-emphasis mb-0">{{ episodeInfo || 'Episode Production Workspace' }}</p>
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
        </div>
      </div>
    </v-card-text>
    
    <!-- Status indicator bar at bottom of header -->
    <div class="status-indicator-bar" :style="statusFieldStyle">
      <div class="status-indicator">
        {{ productionStatus ? productionStatus.toUpperCase() : 'DRAFT' }}
      </div>
    </div>
  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap';

export default {
  name: 'ShowInfoHeader',
  emits: ['update:episodeNumber', 'update:airDate', 'update:productionStatus', 'episode-changed'],
  props: {
    title: {
      type: String,
      default: 'Disaffected'
    },
    episodeInfo: {
      type: String,
      default: 'Episode Production Workspace'
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
    }
  },
  computed: {
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

/* Status indicator bar at bottom of header */
.status-indicator-bar {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  padding: 0 16px 8px 0;
}

.status-indicator {
  width: 200px; /* Same width as text fields */
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
</style>
