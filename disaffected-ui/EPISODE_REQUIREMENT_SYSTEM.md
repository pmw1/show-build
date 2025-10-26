# Episode Requirement System

## Overview

The Episode Requirement System ensures that actions requiring an episode context (uploads, saves, etc.) always have a valid episode selected. If no episode is selected, a modal automatically prompts the user to select one.

## Architecture

### Components

1. **`RequireEpisodeModal.vue`** - Modal that prompts user to select an episode
2. **`useRequireEpisode.js`** - Composable providing the guard logic
3. **Integration Pattern** - How to use in your components

## Usage

### Basic Pattern (Synchronous)

```vue
<script>
import { useRequireEpisode } from '@/composables/useRequireEpisode'

export default {
  setup() {
    const { requireEpisode } = useRequireEpisode()
    return { requireEpisode }
  },
  methods: {
    async uploadImage() {
      // Check if episode is selected
      const episode = this.requireEpisode(
        this.currentEpisode,
        'Upload Image'
      )

      if (!episode) {
        // Modal will be shown automatically
        return
      }

      // Continue with action using episode
      await axios.post('/api/upload', {
        episode: episode,
        // ... other data
      })
    }
  }
}
</script>
```

### Advanced Pattern (With Callback)

```vue
<script>
import { useRequireEpisode } from '@/composables/useRequireEpisode'

export default {
  setup() {
    const { requireEpisode } = useRequireEpisode()
    return { requireEpisode }
  },
  methods: {
    initiateUpload() {
      // Check episode and provide callback
      const episode = this.requireEpisode(
        this.currentEpisode,
        'Upload Image',
        (selectedEpisode) => {
          // This callback executes after user selects episode
          this.performUpload(selectedEpisode)
        }
      )

      if (episode) {
        // Episode already selected, proceed immediately
        this.performUpload(episode)
      }
      // Otherwise callback will be called after modal selection
    },

    async performUpload(episode) {
      // Upload logic using episode
    }
  }
}
</script>
```

### Adding Modal to Root Component

Add the modal to your root component (e.g., `App.vue` or `ContentEditor.vue`):

```vue
<template>
  <RequireEpisodeModal
    v-model:show="showEpisodeModal"
    :action-description="episodeModalAction"
    @episode-selected="handleEpisodeSelected"
    @cancelled="handleModalCancelled"
  />
</template>

<script>
import RequireEpisodeModal from '@/components/modals/RequireEpisodeModal.vue'
import { useRequireEpisode } from '@/composables/useRequireEpisode'

export default {
  components: {
    RequireEpisodeModal
  },
  setup() {
    const {
      showEpisodeModal,
      episodeModalAction,
      handleEpisodeSelected,
      handleModalCancelled
    } = useRequireEpisode()

    return {
      showEpisodeModal,
      episodeModalAction,
      handleEpisodeSelected,
      handleModalCancelled
    }
  },
  methods: {
    handleEpisodeSelected(episode) {
      // Update your global episode selector
      this.currentEpisodeNumber = episode

      // Call the composable handler to execute pending callback
      this.$options.setup().handleEpisodeSelected(episode)
    }
  }
}
</script>
```

## Migration Guide

### Replace Hardcoded Fallbacks

**Before:**
```javascript
getCurrentEpisode() {
  if (this.currentEpisode) {
    return this.currentEpisode
  }
  return '0239' // ❌ Hardcoded fallback
}
```

**After:**
```javascript
import { useRequireEpisode } from '@/composables/useRequireEpisode'

setup() {
  const { requireEpisode } = useRequireEpisode()
  return { requireEpisode }
},

getCurrentEpisode() {
  return this.requireEpisode(
    this.currentEpisode,
    'This Action'
  )
}
```

### Replace sessionStorage Fallbacks

**Before:**
```javascript
const episode = this.currentEpisode ||
                sessionStorage.getItem('currentEpisodeId') ||
                '0239'
```

**After:**
```javascript
const episode = this.requireEpisode(
  this.currentEpisode,
  'Perform Action'
)
if (!episode) return // Modal shown
```

## Benefits

1. **Single Source of Truth** - Episode selector at top dictates all actions
2. **Defensive UX** - Prevents actions without episode context
3. **User-Friendly** - Clear modal prompt instead of silent failures
4. **Consistent** - Same pattern across all episode-requiring actions
5. **Maintains State** - Updates both local and global episode selection

## Components to Migrate

Priority components that need this pattern:

- ✅ `ImgCueModal.vue` - Fixed getCurrentEpisode()
- ⏳ `GfxModal.vue`
- ⏳ `FsqModal.vue`
- ⏳ `SotModal.vue`
- ⏳ `VoModal.vue`
- ⏳ `NatModal.vue`
- ⏳ `RifModal.vue`
- ⏳ `PkgModal.vue`
- ⏳ Any other components with hardcoded episode fallbacks

## Testing

Test scenarios:

1. **Happy Path**: Episode selected → Action proceeds
2. **No Episode**: No episode → Modal shows → Select → Action proceeds
3. **Cancel**: No episode → Modal shows → Cancel → Action aborted
4. **Stale Session**: Old sessionStorage → Warns but uses → Should update to current

## Future Enhancements

1. Auto-sync with top episode selector on modal selection
2. Remember last used episode per action type
3. Quick-create new episode from modal
4. Episode validation (check if episode exists before proceeding)
