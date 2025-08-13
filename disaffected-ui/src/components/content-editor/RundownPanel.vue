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
        <!-- New Item Button - Icon only in narrow mode -->
        <v-btn
          v-if="panelWidth === 'wide'"
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
          v-else
          icon
          size="small"
          color="primary"
          variant="elevated"
          @click="$emit('new-item')"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="bottom">
            Add New Rundown Item (Ctrl+Shift+N)
          </v-tooltip>
        </v-btn>
        
        <v-spacer></v-spacer>
        
        <!-- Export Button - Hidden in narrow mode -->
        <v-btn
          v-if="panelWidth === 'wide'"
          icon
          size="small"
          @click="$emit('export')"
        >
          <v-icon>mdi-export</v-icon>
          <v-tooltip activator="parent" location="bottom">Export Rundown (Ctrl+Shift+E)</v-tooltip>
        </v-btn>
        
        <!-- Refresh Button - Always visible -->
        <v-btn
          icon
          size="small"
          @click="$emit('refresh')"
          :loading="loading"
        >
          <v-icon>mdi-refresh</v-icon>
          <v-tooltip activator="parent" location="bottom">Refresh Rundown (Ctrl+Shift+R)</v-tooltip>
        </v-btn>
        
        <!-- Options Button - Hidden in narrow mode -->
        <v-btn
          v-if="panelWidth === 'wide'"
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

        <!-- Rundown Items List with Vue Draggable -->
        <div class="rundown-items-container" style="min-height: 20px;">
          <draggable
            v-model="localItems"
            item-key="id"
            @choose="handleChoose"
            @start="handleDragStart"
            @end="handleDragEnd"
            ghost-class="ghost-item"
            chosen-class="chosen-item"
            drag-class="drag-item"
            :animation="0"
            :force-fallback="false"
          >
            <template #item="{ element, index }">
              <v-card
                outlined
                :class="[
                  'elevation-1',
                  'rundown-item-card',
                  'mb-1',
                  { 'selected-item': !isDragging && selectedItemIndex === index },
                  { 'editing-item': editingItemIndex === index }
                ]"
                :style="{ 
                  backgroundColor: selectedItemIndex === index ? getSelectionColor() : getBackgroundColorForItem(element?.type || 'unknown'),
                  color: selectedItemIndex === index ? getSelectionTextColor() : getTextColorForItem(element?.type || 'unknown')
                }"
                @click="$emit('select-item', index)"
                @dblclick="$emit('edit-item', index)"
              >
                <div class="compact-rundown-row">
                  <!-- Index Number Cell -->
                  <div class="index-number-cell">
                    <div class="index-number">{{ (index + 1) * 10 }}</div>
                  </div>
                  
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
            </template>
          </draggable>
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
import { themeColorMap, getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'
import draggable from 'vuedraggable'

export default {
  name: 'RundownPanel',
  components: {
    draggable
  },
  emits: [
    'close', 
    'toggle-width', 
    'new-item', 
    'export', 
    'refresh', 
    'toggle-options',
    'select-item',
    'edit-item',
    'reorder-items'
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
  data() {
    return {
      isDragging: false,
      originalTransforms: new Map() // Store original transforms
    }
  },
  computed: {
    panelWidthValue() {
      return this.panelWidth === 'narrow' ? '300px' : '520px'
    },
    safeItems() {
      return this.items || []
    },
    localItems: {
      get() {
        return this.safeItems
      },
      set(/* newValue */) {
        // This will be called when vue.draggable reorders items
        // We don't need to do anything here as the parent manages the data
      }
    }
  },
  methods: {
    getTextColorForItem(type) {
      const colorMapping = themeColorMap[type] || themeColorMap.unknown
      // The themeColorMap now calculates text color dynamically based on contrast
      return colorMapping.textColor || '#ffffff'
    },
    
    getBackgroundColorForItem(type) {
      const colorValue = getColorValue(type.toLowerCase()) || 'grey'
      const resolvedColor = resolveVuetifyColor(colorValue)
      return resolvedColor
    },
    
    getSelectionColor() {
      const selectionValue = getColorValue('selection') || 'warning'
      return resolveVuetifyColor(selectionValue)
    },

    getSelectionTextColor() {
      // Use the theme system's contrast logic for selection background
      const colorMapping = themeColorMap['selection'] || themeColorMap.unknown
      return colorMapping.textColor || '#ffffff'
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
    },

    // Dropline color methods for ghost item styling
    getDroplineColor() {
      const droplineValue = getColorValue('dropline') || 'green-lighten-4'
      return resolveVuetifyColor(droplineValue)
    },

    getDroplineBackground() {
      const droplineValue = getColorValue('dropline') || 'green-lighten-4'
      const baseColor = resolveVuetifyColor(droplineValue)
      // Convert to rgba with low opacity for background
      const rgb = baseColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
      return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.2)` : 'rgba(200, 230, 201, 0.2)'
    },

    getDroplineTextColor() {
      const droplineValue = getColorValue('dropline') || 'green-lighten-4'
      const baseColor = resolveVuetifyColor(droplineValue)
      // Use slightly more opaque version for text
      const rgb = baseColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
      return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.8)` : 'rgba(200, 230, 201, 0.8)'
    },
    
    // Drag handlers for vue.draggable.next - implementing SortableJS transform workaround
    handleChoose(/* event */) {
      // Capture all transforms before SortableJS destroys them
      this.originalTransforms.clear()
      const container = this.$el.querySelector('.rundown-items-container')
      const cards = container.querySelectorAll('.rundown-item-card')
      
      cards.forEach((card, index) => {
        const computedStyle = window.getComputedStyle(card)
        this.originalTransforms.set(index, computedStyle.transform)
      })
    },

    handleDragStart(/* event */) {
      this.isDragging = true
    },
    
    handleDragEnd(event) {
      this.isDragging = false
      
      // Restore transforms after SortableJS finishes (workaround from GitHub issue #2423)
      setTimeout(() => {
        const container = this.$el.querySelector('.rundown-items-container')
        const cards = container.querySelectorAll('.rundown-item-card')
        
        cards.forEach((card, index) => {
          const originalTransform = this.originalTransforms.get(index)
          if (originalTransform && originalTransform !== 'none') {
            card.style.transform = originalTransform
          }
        })
        
        this.originalTransforms.clear()
      }, 50) // Short delay to let SortableJS finish
      
      // Create properly reordered array
      const newItems = [...this.safeItems]
      const [draggedItem] = newItems.splice(event.oldIndex, 1)
      newItems.splice(event.newIndex, 0, draggedItem)
      
      this.$emit('reorder-items', {
        oldIndex: event.oldIndex,
        newIndex: event.newIndex,
        items: newItems
      })
    }
  }
}
</script>

<style scoped>
.rundown-panel {
  height: 100vh; /* Full viewport height */
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden; /* Prevent any overflow issues */
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
  height: calc(100vh - 140px); /* Extend to fill more of the screen */
  overflow-x: hidden; /* Prevent horizontal scrolling during drag */
}

.rundown-headers {
  display: grid;
  grid-template-columns: 50px 60px 1fr;
  gap: 8px;
  padding: 8px 12px 8px 12px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--v-medium-emphasis-opacity);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  position: relative;
}

/* Position duration header absolutely too */
.rundown-headers .header-duration {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.rundown-panel.narrow .rundown-headers {
  grid-template-columns: 40px 50px 1fr;
  padding: 6px 8px;
  font-size: 11px;
  gap: 6px;
}

.compact-rundown-row {
  display: grid;
  grid-template-columns: 50px 60px 1fr;
  gap: 0px 8px;
  padding: 0px 90px 0px 0px; /* Right padding to make room for absolute duration */
  align-items: center;
  font-size: 13px;
  height: 100%;
  min-height: 2.5em;
}

.rundown-panel.narrow .compact-rundown-row {
  grid-template-columns: 40px 50px 1fr;
  padding: 0px 70px 0px 0px; /* Right padding for absolute duration in narrow mode */
  font-size: 12px;
  gap: 0px 6px;
  height: 100%;
  min-height: 2.5em;
  align-items: center;
}

/* Index Number Cell with semi-transparent white background */
.index-number-cell {
  background-color: rgba(255, 255, 255, 0.10);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  height: 100%;
  border-left: none;
  border-top: none;
  border-bottom: none;
  min-width: 50px; /* Ensure consistent width for largest possible numbers */
}

.rundown-panel.narrow .index-number-cell {
  min-width: 40px; /* Slightly smaller for narrow mode */
}

.index-number {
  font-weight: 500;
  text-align: center;
  font-size: calc(11px + 0.2em); /* Increased by 0.2em */
  color: inherit;
  line-height: 1;
}

.type-label {
  font-weight: 600;
  font-size: 10px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.slug-text {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  height: 100%;
}

.duration-display {
  position: absolute;
  right: calc(12px + 25px); /* Account for indentation */
  top: 50%;
  transform: translateY(-50%);
  font-family: 'Roboto Mono', monospace;
  font-size: calc(11px + 0.2em);
  color: inherit;
  white-space: nowrap;
  transition: right 0.3s ease;
}

/* Duration positioning for selected (non-indented) items */
.selected-item .duration-display {
  right: 12px;
}

/* During drag, all durations align with indented position */
.rundown-items-container:has(.chosen-item) .duration-display {
  right: calc(12px + 25px) !important;
}

/* Ensure the row container can contain absolute positioned duration */
.rundown-item-card {
  position: relative;
  border-radius: 0 !important;
  transition: background-color 0.3s ease;
  transform: translateX(25px); /* Restore indentation */
  min-height: 2.5em;
  display: flex;
  align-items: center;
}

/* Force no indentation during any drag operation */
.rundown-items-container:has(.chosen-item) .rundown-item-card {
  transform: translateX(25px) !important; /* Force all items to stay indented during drag */
}

.rundown-item-card:hover:not(.selected-item) {
  transform: translateX(0) translateY(-1px); /* No indentation on hover */
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
  transition: box-shadow 0.2s ease;
}

.selected-item {
  border: 2px solid var(--v-primary-base) !important;
  transform: translateX(0) !important; /* No indent when selected */
  height: 60px;
  transition: 
    background-color 0.3s ease,
    height 0.3s ease 0.1s,
    margin 0.3s ease 0.1s;
  z-index: 10;
  margin: 4px 0;
  display: flex;
  align-items: center;
}

/* Override: Force selected items to stay indented during drag */
.rundown-items-container:has(.chosen-item) .selected-item {
  transform: translateX(25px) !important;
}

.editing-item {
  border: 2px solid var(--v-warning-base) !important;
}

.rundown-items-container {
  height: calc(100vh - 200px); /* Fixed height instead of max-height */
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scrolling */
}

/* Enhanced narrow mode styling */
.rundown-panel.narrow .rundown-title {
  min-height: 48px;
}

.rundown-panel.narrow .rundown-toolbar {
  padding: 4px;
}

.rundown-panel.narrow .index-number {
  font-size: 10px;
}

.rundown-panel.narrow .type-label {
  font-size: 9px;
}

.rundown-panel.narrow .slug-text {
  font-size: 12px;
  font-weight: 500;
}

.rundown-panel.narrow .rundown-item-card {
  margin-bottom: 2px !important;
  transform: translateX(15px); /* Restore narrow mode indentation */
  transition: background-color 0.3s ease;
}

.rundown-panel.narrow .rundown-item-card:hover {
  transform: translateX(15px) translateY(-0.5px);
  transition: box-shadow 0.2s ease;
}

/* Narrow mode drag override */
.rundown-panel.narrow .rundown-items-container:has(.chosen-item) .rundown-item-card {
  transform: translateX(15px) !important;
}

.rundown-panel.narrow .rundown-items-container:has(.chosen-item) .selected-item {
  transform: translateX(15px) !important;
}

/* Narrow mode duration positioning */
.rundown-panel.narrow .duration-display {
  right: calc(12px + 15px);
}

.rundown-panel.narrow .selected-item .duration-display {
  right: 12px;
}

.rundown-panel.narrow .rundown-items-container:has(.chosen-item) .duration-display {
  right: calc(12px + 15px) !important;
}

/* Vue Draggable Styling */

/* Ghost item - shown while dragging */
.ghost-item {
  opacity: 0.8;
  background: v-bind('getDroplineBackground()') !important;
  border: 2px dashed v-bind('getDroplineColor()') !important;
  color: v-bind('getDroplineTextColor()') !important;
  transform: rotate(2deg); /* Just rotation, no indent */
  transition: all 0.2s ease;
}

/* Chosen item - item being dragged */
.chosen-item {
  opacity: 0.8;
  transform: scale(1.02); /* Just scale, no indent */
  box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
  z-index: 1000;
  cursor: grabbing !important;
}

/* Drag item - visual feedback during drag */
.drag-item {
  transform: rotate(3deg) scale(1.05); /* Just effects, no indent */
  opacity: 0.9;
}

/* Draggable items have grab cursor */
.rundown-item-card {
  cursor: grab;
  transition: all 0.2s ease;
}

/* Disable transitions during drag operations to prevent jumping */
.sortable-drag * {
  transition: none !important;
}

/* Alternative: disable transitions when any draggable operation is happening */
.rundown-items-container:has(.chosen-item) .rundown-item-card:not(.chosen-item) {
  transition: none !important;
}

.rundown-item-card:hover {
  cursor: grab;
}

.rundown-item-card:active {
  cursor: grabbing;
}
</style>
