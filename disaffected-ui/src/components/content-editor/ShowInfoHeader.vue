<template>
  <v-card class="show-info-header full-width-bg" flat>
    <v-card-text class="pa-3">
      <div class="header-container">
        <div class="show-title-area">
          <h2 class="text-h5 mb-1">{{ currentShowTitle || 'Disaffected' }}</h2>
          <p class="text-caption text-medium-emphasis mb-0">{{ currentEpisodeInfo || 'Episode Production Workspace' }}</p>
        </div>

        <div class="fields-area">
          <v-select
            label="Episode"
            :model-value="currentEpisodeNumber"
            :items="episodes"
            item-title="title"
            item-value="value"
            variant="outlined"
            density="comfortable"
            class="showinfo-field"
            hide-details
            @update:model-value="$emit('update:episodeNumber', $event)"
          ></v-select>

          <v-text-field
            label="Air Date"
            :model-value="currentAirDate"
            variant="outlined"
            density="comfortable"
            class="showinfo-field"
            hide-details
            @update:model-value="$emit('update:airDate', $event)"
          ></v-text-field>

          <v-select
            label="Status"
            :model-value="currentProductionStatus"
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
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'ShowInfoHeader',
  emits: ['update:episodeNumber', 'update:airDate', 'update:productionStatus'],
  props: {
    currentShowTitle: {
      type: String,
      default: 'Disaffected'
    },
    currentEpisodeInfo: {
      type: String,
      default: 'Episode Production Workspace'
    },
    currentEpisodeNumber: {
      type: [String, Number],
      default: ''
    },
    currentAirDate: {
      type: String,
      default: ''
    },
    currentProductionStatus: {
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
    }
  },
}
</script>

<style scoped>
.show-info-header {
  border-bottom: 1px solid #e0e0e0;
}

.full-width-bg {
  background-color: white;
  width: 100%;
}

.header-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.show-title-area {
  flex: 1 1 auto;
}

.fields-area {
  display: flex;
  flex-wrap: nowrap;
  gap: 16px;
  flex: 2 1 600px; /* Give more space to fields area */
  justify-content: flex-end;
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
