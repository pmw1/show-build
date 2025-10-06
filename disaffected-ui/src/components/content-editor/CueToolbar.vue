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
        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'img')"
            color="indigo-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-image-outline</v-icon>
          </v-btn>
          <div class="cue-label indigo-darken-4">IMG</div>
        </div>

        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'gfx')"
            color="blue-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-image</v-icon>
          </v-btn>
          <div class="cue-label blue-darken-4">GFX</div>
        </div>

        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'fsq')"
            color="green-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-format-quote-close</v-icon>
          </v-btn>
          <div class="cue-label green-darken-4">FSQ</div>
        </div>

        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'sot')"
            color="purple-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-play</v-icon>
          </v-btn>
          <div class="cue-label purple-darken-4">SOT</div>
        </div>

        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'vo')"
            color="deep-orange-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-microphone</v-icon>
          </v-btn>
          <div class="cue-label deep-orange-darken-4">VO</div>
        </div>

        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'nat')"
            color="teal-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-volume-high</v-icon>
          </v-btn>
          <div class="cue-label teal-darken-4">NAT</div>
        </div>

        <div class="cue-btn-wrapper">
          <v-btn
            @click="$emit('show-modal', 'pkg')"
            color="red-darken-3"
            variant="elevated"
            class="cue-btn"
          >
            <v-icon size="small">mdi-package-variant</v-icon>
          </v-btn>
          <div class="cue-label red-darken-4">PKG</div>
        </div>
      </div>

      <!-- Second Row of Hotkeys Below Cue Buttons -->
      <div v-if="editorMode === 'script'" class="cue-second-row">
        <div class="cue-shortcut indigo-darken-4">Alt+I</div>
        <div class="cue-shortcut blue-darken-4">Alt+G</div>
        <div class="cue-shortcut green-darken-4">Alt+Q</div>
        <div class="cue-shortcut purple-darken-4">Alt+S</div>
        <div class="cue-shortcut deep-orange-darken-4">Alt+V</div>
        <div class="cue-shortcut teal-darken-4">Alt+N</div>
        <div class="cue-shortcut red-darken-4">Alt+P</div>
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
  gap: 8px; /* Spacing between button groups */
}

.cue-btn-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cue-btn {
  min-width: 60px;
  height: calc(56px - 16px) !important; /* Reduced height to make room for shortcut */
  border-radius: 0 !important; /* Remove rounded edges */
}

.cue-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-align: center;
  margin-top: 2px;
  min-width: 100%;
}

.cue-shortcut {
  font-size: 0.6rem;
  font-weight: 500;
  text-align: center;
  padding: 1px 4px;
  margin-top: 1px;
  min-width: 60px; /* Match button width */
  background: transparent;
  color: black !important; /* Override color classes for white background */
}

/* Color classes for labels and shortcuts - darker text colors matching button hues */
.cue-label.indigo-darken-4,
.cue-shortcut.indigo-darken-4 {
  color: rgb(var(--v-theme-indigo-darken-4)) !important;
}

.cue-label.blue-darken-4,
.cue-shortcut.blue-darken-4 {
  color: rgb(var(--v-theme-blue-darken-4)) !important;
}

.cue-label.green-darken-4,
.cue-shortcut.green-darken-4 {
  color: rgb(var(--v-theme-green-darken-4)) !important;
}

.cue-label.purple-darken-4,
.cue-shortcut.purple-darken-4 {
  color: rgb(var(--v-theme-purple-darken-4)) !important;
}

.cue-label.deep-orange-darken-4,
.cue-shortcut.deep-orange-darken-4 {
  color: rgb(var(--v-theme-deep-orange-darken-4)) !important;
}

.cue-label.teal-darken-4,
.cue-shortcut.teal-darken-4 {
  color: rgb(var(--v-theme-teal-darken-4)) !important;
}

.cue-label.red-darken-4,
.cue-shortcut.red-darken-4 {
  color: rgb(var(--v-theme-red-darken-4)) !important;
}

/* Second row styling */
.cue-second-row {
  display: flex;
  gap: 8px; /* Same gap as cue buttons */
  margin-top: 4px;
  background-color: white;
  padding: 2px 0;
}

.cue-area-placeholder {
  min-width: 60px; /* Same width as cue buttons */
  height: 1em;
  padding: 0;
  background-color: rgba(0, 0, 0, 0.1);
  border: 1px dashed rgba(0, 0, 0, 0.3);
  border-radius: 2px;
}
</style>
