import { ref } from 'vue'
import { getColorValue } from '../utils/themeColorMap'

export function useRegions() {
  // For now, we'll define regions as logical groupings of rundown items
  // Later this will be backed by database models

  const regionTypes = ref([
    {
      id: 'break',
      name: 'Break',
      type: 'break',
      description: 'Commercial breaks, station IDs, technical breaks',
      defaultDuration: '00:02:30',
      allowedItemTypes: ['ad', 'promo', 'cta'],
      isCollapsible: true
    },
    {
      id: 'block',
      name: 'Content Block',
      type: 'block',
      description: 'Main content segments and interviews',
      defaultDuration: '00:15:00',
      allowedItemTypes: ['coldopen', 'segment', 'interview', 'live', 'pkg', 'vo', 'sot', 'trans', 'tease'],
      isCollapsible: true
    }
  ])

  // Group rundown items into regions based on rules
  const groupItemsIntoRegions = (rundownItems) => {
    if (!rundownItems || rundownItems.length === 0) {
      return []
    }

    const regions = []
    let currentRegion = null
    let regionCounter = { break: 1, block: 1 }

    // Sort items by order to ensure correct grouping
    const sortedItems = [...rundownItems].sort((a, b) => (a.order || 0) - (b.order || 0))

    sortedItems.forEach((item, index) => {
      const itemType = item.type || item.item_type || 'segment'
      console.log(`🔍 Processing item ${index}: ${item.title || item.slug || 'Unnamed'} (type: ${itemType}, order: ${item.order})`)

      // Determine which region type this item belongs to
      let targetRegionType = null

      // First check if this is a placeholder item with explicit region type
      if (item.isPlaceholder && item.regionType) {
        targetRegionType = item.regionType
      } else {
        // Special handling for 'break' items - they force creation of break regions
        if (itemType === 'break') {
          targetRegionType = 'break'
        } else {
          // Check if item type matches any region's allowed types
          for (const regionType of regionTypes.value) {
            if (regionType.allowedItemTypes.includes(itemType)) {
              targetRegionType = regionType.type
              break
            }
          }

          // Default to 'block' if no specific region found
          if (!targetRegionType) {
            targetRegionType = 'block'
          }
        }
      }

      // Special logic: force new block after break regions
      const forceNewBlock = (
        currentRegion?.type === 'break' &&
        targetRegionType === 'block'
      )

      // Check if current region is compatible with target type
      const isCurrentRegionCompatible = currentRegion && (
        currentRegion.type === targetRegionType ||
        (currentRegion.type.startsWith('block-') && targetRegionType === 'block') ||
        (currentRegion.type === 'break' && targetRegionType === 'break')
      )

      // Create new region if needed
      console.log(`🏗️ Region check: currentRegion=${currentRegion?.name} (type: ${currentRegion?.type}), targetType=${targetRegionType}, compatible=${isCurrentRegionCompatible}`)
      if (!currentRegion || !isCurrentRegionCompatible || forceNewBlock) {
        if (forceNewBlock) {
          console.log(`✨ Creating new block region after break (forced separation)`);
        } else {
          console.log(`✨ Creating new region for ${targetRegionType}`);
        }
        // For block subtypes (block-a, block-b, etc.), use the base 'block' config
        const lookupType = targetRegionType.startsWith('block-') ? 'block' : targetRegionType
        const regionTypeConfig = regionTypes.value.find(rt => rt.type === lookupType)

        // Debug logging for troubleshooting
        if (!regionTypeConfig) {
          console.warn(`⚠️ Region type config not found for '${targetRegionType}' (lookup: '${lookupType}')`)
          console.log('Available region types:', regionTypes.value.map(rt => rt.type))
        }

        // Generate appropriate name and type based on region type
        let regionName
        let actualRegionType = targetRegionType

        if (targetRegionType === 'block') {
          // Convert number to letter: 1->A, 2->B, 3->C, etc.
          const letter = String.fromCharCode(64 + regionCounter[targetRegionType]) // 65 is 'A'
          regionName = `Block ${letter}`
          // Use specific block type for color assignment (block-a, block-b, etc.)
          actualRegionType = `block-${letter.toLowerCase()}`
        } else {
          // Fallback if regionTypeConfig is not found
          const configName = regionTypeConfig?.name || targetRegionType || 'Unknown'
          regionName = `${configName} ${regionCounter[targetRegionType]}`
        }

        currentRegion = {
          id: `${targetRegionType}_${regionCounter[targetRegionType]}`,
          type: actualRegionType, // Use the specific block type for color lookup
          name: regionName,
          color: regionTypeConfig.color,
          description: regionTypeConfig.description,
          isCollapsible: regionTypeConfig.isCollapsible,
          isCollapsed: false,
          items: [],
          estimatedDuration: regionTypeConfig.defaultDuration,
          allowReorder: true
        }

        regions.push(currentRegion)
        regionCounter[targetRegionType]++
      }

      // Add item to current region
      console.log(`➕ Adding item "${item.title || item.slug || 'Unnamed'}" to region "${currentRegion.name}" (type: ${currentRegion.type})`)
      currentRegion.items.push({
        ...item,
        regionId: currentRegion.id
      })
    })

    return regions
  }

  // Calculate total duration for a region
  const calculateRegionDuration = (region) => {
    if (!region.items || region.items.length === 0) {
      return region.estimatedDuration || '00:00:00'
    }

    let totalSeconds = 0
    region.items.forEach(item => {
      if (item.duration) {
        const [hours, minutes, seconds] = item.duration.split(':').map(Number)
        totalSeconds += hours * 3600 + minutes * 60 + seconds
      }
    })

    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }

  // Get region color theme - use dynamic color configuration
  const getRegionColor = (regionType) => {
    // Use the color configuration system to get the assigned color
    return getColorValue(regionType) || 'grey'
  }

  // Check if item type is allowed in region
  const isItemAllowedInRegion = (itemType, regionType) => {
    // Allow all items between different block regions (block-a, block-b, etc.)
    const isBlockRegion = regionType.startsWith('block')
    const targetBlockType = isBlockRegion ? 'block' : regionType

    // Find the base region type for validation
    const validationRegionType = regionTypes.value.find(rt => rt.type === targetBlockType)

    return validationRegionType ? validationRegionType.allowedItemTypes.includes(itemType) : true
  }

  // Move item between regions (for drag-and-drop)
  const moveItemToRegion = (item, fromRegionId, toRegionId, regions) => {
    const fromRegion = regions.find(r => r.id === fromRegionId)
    const toRegion = regions.find(r => r.id === toRegionId)

    if (!fromRegion || !toRegion) return false

    // Check if item type is allowed in target region
    const itemType = item.type || item.item_type
    if (!isItemAllowedInRegion(itemType, toRegion.type)) {
      return false
    }

    // Remove from source region
    const itemIndex = fromRegion.items.findIndex(i => i.id === item.id)
    if (itemIndex === -1) return false

    const [movedItem] = fromRegion.items.splice(itemIndex, 1)

    // Add to target region
    movedItem.regionId = toRegionId
    toRegion.items.push(movedItem)

    return true
  }

  return {
    regionTypes,
    groupItemsIntoRegions,
    calculateRegionDuration,
    getRegionColor,
    isItemAllowedInRegion,
    moveItemToRegion
  }
}