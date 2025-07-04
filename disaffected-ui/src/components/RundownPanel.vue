<template>
  <div
    :class="['rundown-panel', rundownPanelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ width: rundownPanelWidthValue }"
  >
    <v-card class="fill-height" flat>
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
          :loading="loadingRundown"
        >
          <v-icon>mdi-refresh</v-icon>
          <v-tooltip activator="parent" location="bottom">Refresh Rundown (Ctrl+Shift+R)</v-tooltip>
        </v-btn>
        
        <v-btn
          icon
          size="small"
          @click="showRundownOptions = !showRundownOptions"
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
          <div v-if="rundownPanelWidth === 'wide'" class="header-duration">Duration</div>
        </div>

        <!-- Rundown Items List -->
        <div class="rundown-items-container" style="min-height: 20px;">
          <v-card
            v-for="(element, index) in safeRundownItems" 
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
              <div class="index-number">{{ (index + 1) * 10 }}</div>
              <div class="type-label">{{ (element?.type || 'UNKNOWN').toUpperCase() }}</div>
              <div class="slug-text">{{ (element?.slug || '').toLowerCase() }}</div>
              <div v-if="rundownPanelWidth === 'wide'" class="duration-display">
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
import { getColorValue } from '../utils/themeColorMap';

export default {
  name: 'RundownPanel',
  props: {
    items: {
      type: Array,
      default: () => []
    },
    rundownPanelWidth: {
      type: String,
      default: 'wide'
    },
    selectedItemIndex: {
      type: Number,
      default: -1
    },
    editingItemIndex: {
      type: Number,
      default: -1
    },
    loadingRundown: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select-item', 'edit-item', 'new-item', 'import', 'export', 'sort', 'refresh'],
  data() {
    return {
      showRundownOptions: false,
    };
  },
  computed: {
    rundownPanelWidthValue() {
      return this.rundownPanelWidth === 'narrow' ? '25%' : '40%';
    },
    safeRundownItems() {
      if (!this.items || !Array.isArray(this.items)) {
        return [];
      }
      return this.items.filter(item => item != null);
    }
  },
  methods: {
    formatDuration(duration) {
      if (!duration) return '00:00:00';
      if (/^\d{2}:\d{2}:\d{2}$/.test(duration)) return duration;
      if (/^\d{1,2}:\d{2}$/.test(duration)) return `00:${duration.padStart(5, '0')}`;
      if (/^\d:\d{2}$/.test(duration)) return `00:0${duration}`;
      if (/^\d+$/.test(duration)) {
        const totalSeconds = parseInt(duration);
        const h = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
        const m = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
        const s = (totalSeconds % 60).toString().padStart(2, '0');
        return `${h}:${m}:${s}`;
      }
      if (duration.includes(':')) {
        const parts = duration.split(':');
        if (parts.length === 2) {
          const m = (parseInt(parts[0]) || 0).toString().padStart(2, '0');
          const s = (parseInt(parts[1]) || 0).toString().padStart(2, '0');
          return `00:${m}:${s}`;
        }
      }
      return '00:00:00';
    },
    resolveTypeClass(type) {
      if (!type || type === 'unknown') return 'bg-grey-light';
      const color = getColorValue(type.toLowerCase());
      return `bg-${color}`;
    },
    getTextColorForItem(type) {
      if (!type || typeof type !== 'string') return '#333333';
      const bgColor = getColorValue(type.toLowerCase());
      const darkBackgrounds = ['blue', 'purple', 'indigo', 'red', 'green'];
      return darkBackgrounds.some(color => bgColor.includes(color)) ? '#ffffff' : '#333333';
    }
  }
};
</script>

<style scoped>
.rundown-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid #ccc;
  background-color: var(--v-theme-surface);
}

.rundown-toolbar {
  border-bottom: 1px solid rgba(0,0,0,0.12);
}

.rundown-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 4px;
}

.rundown-headers {
  display: flex;
  font-weight: bold;
  padding: 4px 8px;
  font-size: 0.75rem;
  color: grey;
  border-bottom: 1px solid #ccc;
  position: sticky;
  top: 0;
  background-color: var(--v-theme-surface);
  z-index: 1;
}

.header-index { width: 30px; }
.header-type { width: 60px; }
.header-slug { flex-grow: 1; }
.header-duration { width: 60px; text-align: right; }

.rundown-item-card {
  transition: background-color 0.2s ease-in-out;
}

.rundown-item-card:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

.selected-item {
  border-left: 4px solid rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.editing-item {
   border-left: 4px solid rgb(var(--v-theme-secondary));
   background-color: rgba(var(--v-theme-secondary), 0.1);
}

.compact-rundown-row {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  font-size: 0.8rem;
}

.index-number {
  width: 30px;
  font-weight: bold;
  color: grey;
  font-size: 0.7rem;
}

.type-label {
  width: 60px;
  font-weight: bold;
  font-size: 0.7rem;
}

.slug-text {
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.duration-display {
  width: 60px;
  text-align: right;
  font-family: monospace;
  font-size: 0.8rem;
}
</style>
