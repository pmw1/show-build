<template>
  <div 
    :class="['rundown-panel', panelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ width: panelWidthValue }"
  >
    <v-card class="fill-height" flat>
      <!-- Rundown Header -->
      <v-card-title class="d-flex align-center pa-2 rundown-title">
        <span class="text-h6">Rundown</span>
        <v-spacer></v-spacer>
        <v-btn
          icon
          size="small"
          @click="$emit('toggle-width')"
        >
          <v-icon>{{ panelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
        </v-btn>
        <v-btn icon size="small" @click="$emit('close')">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <!-- Rundown Toolbar -->
      <v-toolbar density="compact" color="surface" class="rundown-toolbar" flat>
        <v-btn
          size="small"
          color="primary"
          variant="elevated"
          @click="$emit('new-item')"
          prepend-icon="mdi-plus"
        >
          New Item
          <v-tooltip activator="parent" location="bottom">
            Add New Rundown Item (Ctrl+Shift+N)
          </v-tooltip>
        </v-btn>
        
        <v-btn
          size="small"
          color="secondary"
          variant="outlined"
          @click="$emit('import')"
          prepend-icon="mdi-import"
          class="ml-1"
        >
          Import
        </v-btn>
        
        <v-spacer></v-spacer>
        
        <v-btn
          icon
          size="small"
          @click="$emit('export')"
        >
          <v-icon>mdi-export</v-icon>
          <v-tooltip activator="parent" location="bottom">Export Rundown (Ctrl+Shift+E)</v-tooltip>
        </v-btn>
        
        <v-btn
          icon
          size="small"
          @click="$emit('sort')"
        >
          <v-icon>mdi-sort</v-icon>
          <v-tooltip activator="parent" location="bottom">Sort Items</v-tooltip>
        </v-btn>
        
        <v-btn
          icon
          size="small"
          @click="$emit('refresh')"
          :loading="loading"
        >
          <v-icon>mdi-refresh</v-icon>
          <v-tooltip activator="parent" location="bottom">Refresh Rundown (Ctrl+Shift+R)</v-tooltip>
        </v-btn>
        
        <v-btn
          icon
          size="small"
          @click="$emit('toggle-options')"
        >
          <v-icon>mdi-dots-vertical</v-icon>
          <v-tooltip activator="parent" location="bottom">Rundown Options</v-tooltip>
        </v-btn>
      </v-toolbar>
      
      <v-card-text class="pa-1 rundown-content">
        <!-- Column Headers -->
        <div class="rundown-headers" v-if="items && items.length > 0">
          <div class="header-index">#</div>
          <div class="header-type">Type</div>
          <div class="header-slug">Slug</div>
          <div v-if="panelWidth === 'wide'" class="header-duration">Duration</div>
        </div>

        <!-- Rundown Items List -->
        <div class="rundown-items-container" style="min-height: 20px;">
          <v-card
            v-for="(element, index) in safeItems" 
            :key="`rundown-item-${index}`"
            outlined
            :class="[
              resolveTypeClass(element?.type || 'unknown'),
              'elevation-1',
              'rundown-item-card',
              'mb-1',
              { 'selected-item': selectedItemIndex === index },
              { 'editing-item': editingItemIndex === index }
            ]"
            @click="$emit('select-item', index)"
            @dblclick="$emit('edit-item', index)"
            style="cursor: pointer;"
          >
            <div class="compact-rundown-row" :style="{ color: getTextColorForItem(element?.type || 'unknown') }">
              <!-- Index Number -->
              <div class="index-number">{{ (index + 1) * 10 }}</div>
              
              <!-- Type -->
              <div class="type-label">{{ (element?.type || 'UNKNOWN').toUpperCase() }}</div>
              
              <!-- Slug (Bold) -->
              <div class="slug-text">{{ (element?.slug || '').toLowerCase() }}</div>
              
              <!-- Duration (Right side) -->
              <div v-if="panelWidth === 'wide'" class="duration-display">
                {{ formatDuration(element?.duration || '0:00') }}
              </div>
            </div>
          </v-card>
        </div>
        
        <!-- Empty state -->
        <div v-if="!items || items.length === 0" class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-playlist-remove</v-icon>
          <p class="text-h6 text-grey-lighten-1">No rundown items found</p>
          <p class="text-caption text-grey">Switch to Rundown Manager to add items</p>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { themeColorMap } from '@/utils/themeColorMap'

export default {
  name: 'RundownPanel',
  emits: [
    'close', 
    'toggle-width', 
    'new-item', 
    'import', 
    'export', 
    'sort', 
    'refresh', 
    'toggle-options',
    'select-item',
    'edit-item'
  ],
  props: {
    panelWidth: {
      type: String,
      default: 'wide',
      validator: (value) => ['narrow', 'wide'].includes(value)
    },
    items: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    selectedItemIndex: {
      type: Number,
      default: -1
    },
    editingItemIndex: {
      type: Number,
      default: -1
    }
  },
  computed: {
    panelWidthValue() {
      return this.panelWidth === 'narrow' ? '200px' : '350px'
    },
    safeItems() {
      return this.items || []
    }
  },
  methods: {
    resolveTypeClass(type) {
      const colorMapping = themeColorMap[type] || themeColorMap.unknown
      return `type-${type.toLowerCase()}-bg`
    },
    getTextColorForItem(type) {
      const colorMapping = themeColorMap[type] || themeColorMap.unknown
      return colorMapping.textColor || 'inherit'
    },
    formatDuration(duration) {
      if (!duration) return '0:00'
      if (typeof duration === 'string' && duration.includes(':')) {
        return duration
      }
      // Handle numeric duration (assuming seconds)
      if (typeof duration === 'number') {
        const minutes = Math.floor(duration / 60)
        const seconds = duration % 60
        return `${minutes}:${seconds.toString().padStart(2, '0')}`
      }
      return duration.toString()
    }
  }
}
</script>

<style scoped>
.rundown-panel {
  height: 100%;
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.rundown-title {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  min-height: 56px;
}

.rundown-toolbar {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.rundown-content {
  overflow-y: auto;
  height: calc(100vh - 250px);
}

.rundown-headers {
  display: grid;
  grid-template-columns: 40px 60px 1fr 80px;
  gap: 8px;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--v-medium-emphasis-opacity);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.rundown-panel.narrow .rundown-headers {
  grid-template-columns: 40px 60px 1fr;
}

.compact-rundown-row {
  display: grid;
  grid-template-columns: 40px 60px 1fr 80px;
  gap: 8px;
  padding: 8px 12px;
  align-items: center;
  font-size: 13px;
}

.rundown-panel.narrow .compact-rundown-row {
  grid-template-columns: 40px 60px 1fr;
}

.index-number {
  font-weight: 500;
  text-align: center;
  font-size: 11px;
}

.type-label {
  font-weight: 600;
  font-size: 10px;
  text-align: center;
}

.slug-text {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.duration-display {
  text-align: right;
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
}

.rundown-item-card {
  border-radius: 4px !important;
  transition: all 0.2s ease;
}

.rundown-item-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

.selected-item {
  border: 2px solid var(--v-primary-base) !important;
}

.editing-item {
  border: 2px solid var(--v-warning-base) !important;
}

.rundown-items-container {
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}
</style>
