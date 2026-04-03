import { ref } from 'vue'

/**
 * Determine which region type an item belongs to based on its type.
 * Pure function — no component dependencies.
 */
export function determineRegionType(item) {
  if (item.regionType) return item.regionType

  const itemType = item.type || item.item_type || 'segment'

  const regionTypes = [
    {
      type: 'break',
      allowedItemTypes: ['ad', 'promo', 'cta', 'trans', 'break', 'bump']
    },
    {
      type: 'block',
      allowedItemTypes: ['segment', 'interview', 'live', 'pkg', 'vo', 'sot']
    }
  ]

  for (const regionType of regionTypes) {
    if (regionType.allowedItemTypes.includes(itemType)) {
      return regionType.type
    }
  }

  return 'block' // Default
}

/**
 * Composable for drag-and-drop logic in RundownPanel.
 *
 * Owns its own reactive state (isDragging, region-drag tracking).
 * Methods that need component-level data (regions, flatItemsFromRegions, emit)
 * receive them via a `ctx` object parameter.
 *
 * Usage in Options API setup():
 *   const dragDrop = useRundownDragDrop()
 *   return { ...dragDrop }
 *
 * Then in methods, call e.g.:
 *   this.handleRegionDragStart(evt)
 *   this.handleRegionDragEnd(evt, { regions: this.regions, flatItemsFromRegions: this.flatItemsFromRegions, emit: this.$emit })
 */
export function useRundownDragDrop() {
  // --- Reactive state ---
  const isDragging = ref(false)
  const isDraggingRegion = ref(false)
  const draggedRegionType = ref(null)
  const draggedRegionId = ref(null)
  const hoveredRegionId = ref(null)

  // --- Hierarchical drag handlers ---

  function handleRegionDragStart(evt) {
    console.log('Region drag started', evt)
    isDragging.value = true

    if (evt.item) {
      evt.item.classList.add('currently-dragging-region')
    }
  }

  /**
   * @param {Event} evt
   * @param {Object} ctx - { regions, flatItemsFromRegions, emit }
   */
  function handleRegionDragEnd(evt, ctx) {
    try {
      console.log('Region drag ended', evt)
      console.log('Old index:', evt.oldIndex, 'New index:', evt.newIndex)
      isDragging.value = false

      if (evt.item) {
        evt.item.classList.remove('currently-dragging-region')
      }

      if (evt.oldIndex !== evt.newIndex) {
        console.log('Region order changed - emitting updates')

        if (ctx.flatItemsFromRegions) {
          ctx.emit('reorder-items', ctx.flatItemsFromRegions)
        }
        if (ctx.regions) {
          ctx.emit('regions-updated', ctx.regions)
        }

        ctx.emit('save')
      }
    } catch (error) {
      console.error('Error in handleRegionDragEnd:', error)
      isDragging.value = false
    }
  }

  function handleItemDragStart(evt) {
    console.log('Item drag started', evt)
    isDragging.value = true

    if (evt.item) {
      evt.item.classList.add('currently-dragging')
    }
  }

  /**
   * @param {Event} evt
   * @param {Object} ctx - { regions, flatItemsFromRegions, emit }
   */
  function handleItemDragEnd(evt, ctx) {
    try {
      console.log('Item drag ended', evt)
      isDragging.value = false

      if (evt.item) {
        evt.item.classList.remove('currently-dragging')
      }

      if (ctx.flatItemsFromRegions) {
        ctx.emit('reorder-items', ctx.flatItemsFromRegions)
      }
      if (ctx.regions) {
        ctx.emit('regions-updated', ctx.regions)
      }

      ctx.emit('save')
    } catch (error) {
      console.error('Error in handleItemDragEnd:', error)
      isDragging.value = false
    }
  }

  /**
   * Validate whether a drag move should be allowed.
   */
  function allowMove(evt) {
    console.log('Drag Move Validation:', {
      draggedElement: evt.draggedElement,
      draggedData: evt.draggedElement?.__draggable_context?.element,
      itemType: evt.draggedElement?.__draggable_context?.element?.type,
      related: evt.related,
      targetRegion: evt.to?.closest('.region-container'),
      willAccept: evt.willAccept
    })

    return true // Allow all moves
  }

  /**
   * Handle cross-region item moves triggered by vue-draggable change events.
   * @param {Object} evt - The draggable change event
   * @param {Object} ctx - { regions, flatItemsFromRegions, emit }
   */
  function handleItemChange(evt, ctx) {
    try {
      console.log('Item change event', evt)

      if (evt.added) {
        console.log('Item added to region:', evt.added)
        const addedItem = evt.added.element
        if (addedItem && ctx.regions) {
          const targetRegion = ctx.regions.find(r =>
            r.items && r.items.some(item => item.id === addedItem.id)
          )
          if (targetRegion) {
            addedItem.regionId = targetRegion.id
            console.log(`Updated item ${addedItem.id} to region ${targetRegion.id}`)
          }
        }
      }

      if (evt.removed) {
        console.log('Item removed from region:', evt.removed)
      }

      if (evt.moved) {
        console.log('Item moved within region:', evt.moved)
      }

      console.log('Emitting updated items after cross-region change')
      if (ctx.flatItemsFromRegions) {
        ctx.emit('reorder-items', ctx.flatItemsFromRegions)
      }
      if (ctx.regions) {
        ctx.emit('regions-updated', ctx.regions)
      }

      ctx.emit('save')
    } catch (error) {
      console.error('Error in handleItemChange:', error)
    }
  }

  return {
    // Reactive state
    isDragging,
    isDraggingRegion,
    draggedRegionType,
    draggedRegionId,
    hoveredRegionId,

    // Pure utility (also exported as named export for direct import)
    determineRegionType,

    // Hierarchical drag handlers
    handleRegionDragStart,
    handleRegionDragEnd,
    handleItemDragStart,
    handleItemDragEnd,
    allowMove,
    handleItemChange
  }
}
