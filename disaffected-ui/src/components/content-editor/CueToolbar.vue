<template>
  <v-toolbar 
    density="comfortable" 
    color="surface-variant" 
    class="px-2 py-1 cue-toolbar" 
    style="min-height: 56px;"
  >
    <v-btn
      icon
      size="small"
      @click="$emit('toggle-rundown')"
      v-if="!showRundownPanel"
    >
      <v-icon>mdi-menu</v-icon>
    </v-btn>

    <div class="d-flex align-center">
      <span class="text-overline mr-4 cue-toolbar-label">Insert Element Cues</span>
      <!-- Cue Insertion Buttons with proper spacing -->
      <div v-if="editorMode === 'script'" class="cue-buttons-container">
        <v-btn 
          @click="$emit('show-modal', 'gfx')" 
          color="blue-darken-3" 
          variant="elevated" 
          class="cue-btn"
        >
          <v-icon size="small">mdi-image</v-icon>
          GFX
          <v-tooltip activator="parent" location="bottom">Alt+G</v-tooltip>
        </v-btn>
        
        <v-btn 
          @click="$emit('show-modal', 'fsq')" 
          color="green-darken-3" 
          variant="elevated" 
          class="cue-btn"
        >
          <v-icon size="small">mdi-format-quote-close</v-icon>
          FSQ
          <v-tooltip activator="parent" location="bottom">Alt+Q</v-tooltip>
        </v-btn>
        
        <v-btn 
          @click="$emit('show-modal', 'sot')" 
          color="purple-darken-3" 
          variant="elevated" 
          class="cue-btn"
        >
          <v-icon size="small">mdi-play</v-icon>
          SOT
          <v-tooltip activator="parent" location="bottom">Alt+S</v-tooltip>
        </v-btn>
        
        <v-btn 
          @click="$emit('show-modal', 'vo')" 
          color="deep-orange-darken-3" 
          variant="elevated" 
          class="cue-btn"
        >
          <v-icon size="small">mdi-microphone</v-icon>
          VO
          <v-tooltip activator="parent" location="bottom">Alt+V</v-tooltip>
        </v-btn>
        
        <v-btn 
          @click="$emit('show-modal', 'nat')" 
          color="teal-darken-3" 
          variant="elevated" 
          class="cue-btn"
        >
          <v-icon size="small">mdi-volume-high</v-icon>
          NAT
          <v-tooltip activator="parent" location="bottom">Alt+N</v-tooltip>
        </v-btn>
        
        <v-btn 
          @click="$emit('show-modal', 'pkg')" 
          color="red-darken-3" 
          variant="elevated" 
          class="cue-btn"
        >
          <v-icon size="small">mdi-package-variant</v-icon>
          PKG
          <v-tooltip activator="parent" location="bottom">Alt+P</v-tooltip>
        </v-btn>
      </div>
    </div>

    <v-spacer></v-spacer>

    <!-- Mode Label -->
    <v-chip size="small" variant="text" class="mr-2">
      <v-icon left>{{ modeIcon }}</v-icon>
      {{ editorMode.toUpperCase() }} MODE
    </v-chip>
  </v-toolbar>
</template>

<script>
export default {
  name: 'CueToolbar',
  emits: ['toggle-rundown', 'show-modal'],
  props: {
    showRundownPanel: {
      type: Boolean,
      default: false
    },
    editorMode: {
      type: String,
      default: 'script',
      validator: (value) => ['script', 'scratch', 'metadata'].includes(value)
    }
  },
  computed: {
    modeIcon() {
      const icons = {
        script: 'mdi-script-text',
        scratch: 'mdi-pencil',
        metadata: 'mdi-cog'
      }
      return icons[this.editorMode] || 'mdi-script-text'
    }
  }
}
</script>

<style scoped>
.cue-toolbar {
  border-bottom: 1px solid rgba(0,0,0,0.12);
}

.cue-toolbar-label {
  color: rgba(0, 0, 0, 0.6);
}

.cue-buttons-container {
  display: flex;
  gap: 8px; /* Spacing between buttons */
}

.cue-btn {
  min-width: 60px;
  height: calc(56px - 8px) !important; /* Fill available height minus toolbar padding */
  border-radius: 0 !important; /* Remove rounded edges */
}
</style>
