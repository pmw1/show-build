import { ref, computed, watch } from 'vue'

export function useContentEditor() {
  // Editor state
  const editorMode = ref('script')
  const showRundownPanel = ref(true)
  const rundownPanelWidth = ref('wide')
  const hasUnsavedChanges = ref(false)
  
  // Content
  const scriptContent = ref('')
  const scratchContent = ref('')
  const currentItemMetadata = ref({
    title: '',
    type: '',
    slug: '',
    duration: '',
    description: '',
    tags: [],
    reporter: ''
  })
  
  // Rundown
  const rundownItems = ref([])
  const selectedItemIndex = ref(-1)
  const editingItemIndex = ref(-1)
  const loadingRundown = ref(false)
  
  // Show information
  const currentShowTitle = ref('Disaffected')
  const currentEpisodeInfo = ref('Episode Production Workspace')
  const currentEpisodeNumber = ref('')
  const currentAirDate = ref('')
  const currentProductionStatus = ref('draft')
  
  // Modal states
  const showGfxModal = ref(false)
  const showFsqModal = ref(false)
  const showSotModal = ref(false)
  const showVoModal = ref(false)
  const showNatModal = ref(false)
  const showPkgModal = ref(false)
  const showNewItemModal = ref(false)
  const showAssetBrowser = ref(false)
  const showRundownOptions = ref(false)
  
  // Computed properties
  const rundownPanelWidthValue = computed(() => {
    return rundownPanelWidth.value === 'narrow' ? '300px' : '520px'
  })
  
  const rundownHeaderWidth = computed(() => {
    return showRundownPanel.value ? rundownPanelWidthValue.value : '0px'
  })
  
  const cueToolbarWidth = computed(() => {
    return showRundownPanel.value ? `calc(100% - ${rundownPanelWidthValue.value})` : '100%'
  })
  
  const safeRundownItems = computed(() => {
    return rundownItems.value || []
  })
  
  const duration = computed(() => {
    return calculateDuration()
  })
  
  // Methods
  const calculateDuration = () => {
    if (!rundownItems.value || rundownItems.value.length === 0) {
      return '0:00'
    }
    
    let totalSeconds = 0
    rundownItems.value.forEach(item => {
      if (item?.duration) {
        const duration = item.duration.toString()
        if (duration.includes(':')) {
          const parts = duration.split(':')
          if (parts.length === 2) {
            totalSeconds += parseInt(parts[0]) * 60 + parseInt(parts[1])
          } else if (parts.length === 3) {
            totalSeconds += parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2])
          }
        } else {
          totalSeconds += parseInt(duration) || 0
        }
      }
    })
    
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }
  }
  
  const selectRundownItem = (index) => {
    selectedItemIndex.value = index
  }
  
  const startEditingItem = (index) => {
    editingItemIndex.value = index
    selectedItemIndex.value = index
  }
  
  const toggleRundownPanel = () => {
    showRundownPanel.value = !showRundownPanel.value
  }
  
  const toggleRundownWidth = () => {
    rundownPanelWidth.value = rundownPanelWidth.value === 'narrow' ? 'wide' : 'narrow'
  }
  
  const onContentChange = () => {
    hasUnsavedChanges.value = true
  }
  
  const saveContent = () => {
    // Implementation for saving content
    console.log('Saving content...')
    hasUnsavedChanges.value = false
  }
  
  const showModal = (modalType) => {
    switch (modalType) {
      case 'gfx':
        showGfxModal.value = true
        break
      case 'fsq':
        showFsqModal.value = true
        break
      case 'sot':
        showSotModal.value = true
        break
      case 'vo':
        showVoModal.value = true
        break
      case 'nat':
        showNatModal.value = true
        break
      case 'pkg':
        showPkgModal.value = true
        break
      default:
        console.warn('Unknown modal type:', modalType)
    }
  }
  
  const refreshRundown = () => {
    loadingRundown.value = true
    // Implementation for refreshing rundown
    setTimeout(() => {
      loadingRundown.value = false
    }, 1000)
  }
  
  const importRundown = () => {
    // Implementation for importing rundown
    console.log('Importing rundown...')
  }
  
  const exportRundown = () => {
    // Implementation for exporting rundown
    console.log('Exporting rundown...')
  }
  
  const sortRundown = () => {
    // Implementation for sorting rundown
    console.log('Sorting rundown...')
  }
  
  // Watch for changes
  watch([scriptContent, scratchContent], () => {
    onContentChange()
  })
  
  return {
    // State
    editorMode,
    showRundownPanel,
    rundownPanelWidth,
    hasUnsavedChanges,
    scriptContent,
    scratchContent,
    currentItemMetadata,
    rundownItems,
    selectedItemIndex,
    editingItemIndex,
    loadingRundown,
    currentShowTitle,
    currentEpisodeInfo,
    currentEpisodeNumber,
    currentAirDate,
    currentProductionStatus,
    
    // Modal states
    showGfxModal,
    showFsqModal,
    showSotModal,
    showVoModal,
    showNatModal,
    showPkgModal,
    showNewItemModal,
    showAssetBrowser,
    showRundownOptions,
    
    // Computed
    rundownPanelWidthValue,
    rundownHeaderWidth,
    cueToolbarWidth,
    safeRundownItems,
    duration,
    
    // Methods
    calculateDuration,
    selectRundownItem,
    startEditingItem,
    toggleRundownPanel,
    toggleRundownWidth,
    onContentChange,
    saveContent,
    showModal,
    refreshRundown,
    importRundown,
    exportRundown,
    sortRundown
  }
}
