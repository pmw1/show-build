# Vue.Draggable Implementation Guide

This document describes the implementation of drag-and-drop functionality in the Show-Build project using Vue.Draggable and SortableJS.

## Overview

The drag-and-drop functionality is implemented in the ContentEditor component's rundown list. This replaces the previous HTML5 drag API implementation with a more robust solution using `vue-draggable-next` and SortableJS.

## Dependencies

```bash
npm install vue-draggable-next --legacy-peer-deps
```

## Implementation Details

### Import and Registration

```javascript
import { VueDraggableNext as draggable } from 'vue-draggable-next';

export default {
  components: {
    draggable,
    // ... other components
  }
}
```

### Template Usage

```vue
<draggable
  v-model="rundownItems"
  tag="div"
  :item-key="item => item.id || item.slug || Math.random()"
  handle=".rundown-item"
  ghost-class="ghost-class"
  chosen-class="chosen-class"
  drag-class="drag-class"
  @start="onDragStart"
  @end="onDragEnd"
>
  <template #item="{element: item, index}">
    <div class="rundown-item">
      <!-- Item content -->
    </div>
  </template>
</draggable>
```

### Configuration Properties

- `v-model="rundownItems"`: Two-way binding to the array of items
- `tag="div"`: HTML element wrapper for the draggable container  
- `item-key`: Function to generate unique keys for each item
- `handle=".rundown-item"`: CSS selector for drag handle (entire item)
- `ghost-class="ghost-class"`: CSS class applied to the placeholder during drag
- `chosen-class="chosen-class"`: CSS class applied when item is selected for drag
- `drag-class="drag-class"`: CSS class applied to the item being dragged

### Event Handlers

```javascript
// SortableJS event handlers for drag and drop
onDragStart(event) {
  console.log('Drag started:', event.oldIndex);
  this.dragStartIndex = event.oldIndex;
},

onDragEnd(event) {
  console.log('Drag ended:', event.oldIndex, '->', event.newIndex);
  
  // Only process if the position actually changed
  if (event.oldIndex !== event.newIndex) {
    console.log('Position changed, saving rundown order');
    this.hasUnsavedChanges = true;
    this.saveRundownOrder();
    
    // Update selected index if necessary
    if (this.selectedItemIndex === event.oldIndex) {
      this.selectedItemIndex = event.newIndex;
    } else if (this.selectedItemIndex > event.oldIndex && this.selectedItemIndex <= event.newIndex) {
      this.selectedItemIndex--;
    } else if (this.selectedItemIndex < event.oldIndex && this.selectedItemIndex >= event.newIndex) {
      this.selectedItemIndex++;
    }
  }
  
  this.dragStartIndex = -1;
},
```

### CSS Classes for Visual Feedback

```css
/* Placeholder shown in drop position */
.rundown-item.ghost-class {
  opacity: 0.5;
  background: #e3f2fd;
  transform: scale(0.98);
}

/* Applied when item is selected for dragging */
.rundown-item.chosen-class {
  opacity: 0.8;
  background: #fff3cd;
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Applied to the item being dragged */
.rundown-item.drag-class {
  opacity: 0.7;
  background: #d1ecf1;
  transform: rotate(2deg);
  box-shadow: 0 6px 16px rgba(0,0,0,0.3);
  z-index: 2000;
}
```

## Data Management

### Simplified State

The new implementation requires minimal state management:

```javascript
data() {
  return {
    // Drag state (simplified for SortableJS)
    dragStartIndex: -1,
    // ... other data
  }
}
```

### Automatic Array Updates

Vue.Draggable automatically handles the array reordering through the `v-model` binding. No manual array manipulation is required.

### Backend Synchronization

The `saveRundownOrder()` method is called when items are reordered:

```javascript
async saveRundownOrder() {
  const paddedId = this.padEpisodeNumber(this.currentEpisodeNumber);
  if (!paddedId) return;
  
  try {
    const segments = this.rundownItems.map((item, index) => ({
      filename: item.filename || `${item.order || ((index + 1) * 10)} ${item.slug || item.title}.md`,
      order: (index + 1) * 10
    }));
    
    const payload = { segments };
    await axios.post(`/api/rundown/${paddedId}/reorder`, payload);
    console.log('Rundown order saved successfully');
    this.hasUnsavedChanges = false;
  } catch (error) {
    console.error('Failed to save rundown order:', error);
  }
},
```

## Benefits Over HTML5 Drag API

1. **Automatic Array Management**: Vue.Draggable handles array reordering automatically
2. **Better Mobile Support**: SortableJS provides touch/mobile compatibility  
3. **Consistent Visual Feedback**: Standardized CSS classes for drag states
4. **Simpler Implementation**: Fewer custom event handlers and state management
5. **Better Performance**: Optimized for Vue.js reactivity system
6. **Cross-Browser Compatibility**: Works consistently across all modern browsers

## Integration Points

### File Locations
- **Implementation**: `/disaffected-ui/src/components/ContentEditor.vue`
- **Documentation**: `/docs/VUE_DRAGGABLE_IMPLEMENTATION.md`

### Backend Endpoints
- **Reorder API**: `POST /api/rundown/{episode_id}/reorder`
- **Payload Format**: `{ segments: [{ filename, order }] }`

### Component Dependencies
- Vue 3 Composition API
- Vuetify 3 for styling
- Axios for HTTP requests
- vue-draggable-next package

## Migration Notes

The following HTML5 drag API methods were removed:
- `dragStart()`, `dragEnd()`, `dragOver()`, `dragDrop()`, `dragLeave()`
- `resetDragState()` method  
- Complex drag state properties (`isDragging`, `draggedIndex`, etc.)

The new implementation is much simpler and more reliable for production use.