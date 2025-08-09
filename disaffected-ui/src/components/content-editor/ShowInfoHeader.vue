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
            density="comfortable"
            class="showinfo-field"
            hide-details
            @update:model-value="$emit('update:episodeNumber', $event)"
            :item-props="episode => ({
              title: (typeof episode.title === 'string')
                ? episode.title.split(':')[0] + (episode.title.includes(':') ? ':' : '') + ' ' + (episode.title.split(':')[1] ? episode.title.split(':')[1].trim() : '')
                : ''
            })"
          ></v-select>

          <v-text-field
            label="Air Date"
            :model-value="airDate"
            variant="outlined"
            density="comfortable"
            class="showinfo-field"
            hide-details
            @update:model-value="$emit('update:airDate', $event)"
          ></v-text-field>

          <v-select
            label="Status"
            :model-value="productionStatus"
            :items="productionStatuses"
            variant="outlined"
            density="comfortable"
            class="showinfo-field"
            hide-details
            @update:model-value="$emit('update:productionStatus', $event)"
          ></v-select>

          <v-text-field
            label="Total Runtime"
            :model-value="totalRuntime"
            variant="outlined"
            density="comfortable"
            class="showinfo-field"
            hide-details
            readonly
          ></v-text-field>

          <div class="status-indicator" :style="{ backgroundColor: statusColor, color: '#fff', borderRadius: '4px', padding: '4px 12px', display: 'inline-block', marginBottom: '8px', fontWeight: 600, letterSpacing: '1px' }">
            {{ productionStatus }}
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { getColorValue } from '../../utils/themeColorMap';

export default {
  name: 'ShowInfoHeader',
  emits: ['update:episodeNumber', 'update:airDate', 'update:productionStatus'],
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
      default: 'Pre-Production'
    },
    totalRuntime: {
      type: String,
      default: '00:00:00'
    },
    episodes: {
      type: Array,
      default: () => []
    },
    productionStatuses: {
      type: Array,
      default: () => ['Draft', 'Approved', 'Production', 'Completed']
    },
    loadingRundown: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    statusColor() {
      // Use getColorValue to get the color for the current status
      return getColorValue((this.productionStatus || '').toLowerCase());
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
  font-size: clamp(1.1rem, 2.5vw, 2rem);
}

.fields-area {
  display: flex;
  flex-wrap: nowrap;
  gap: 16px;
  flex: 2 1 600px;
  justify-content: flex-end;
  align-items: flex-start;
  align-self: flex-start;
}

.showinfo-field {
  min-width: 150px; /* Reduced min-width for more flexibility */
  flex: 1 1 0;
}


/* Deep selectors for Vuetify component styling */
:deep(.v-select .v-field__input),
:deep(.v-text-field .v-field__input) {
  padding-top: 4px !important;
  padding-bottom: 4px !important;
  min-height: 40px !important;
}

:deep(.v-field__field) {
  height: 40px !important;
}
</style>
