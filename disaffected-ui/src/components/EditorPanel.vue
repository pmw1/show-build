<template>
  <div :class="['editor-panel', !showRundownPanel ? 'full-width' : '']">
    <v-card class="fill-height" flat>
      <!-- Editor Mode and Controls Toolbar (mode buttons left, mode display chip and status right) -->
      <v-toolbar density="comfortable" color="surface" class="px-2 py-1" style="min-height: 48px;">
        <v-btn
          icon
          size="small"
          @click="$emit('toggle-rundown-panel')"
          v-if="!showRundownPanel"
        >
          <v-icon>mdi-menu</v-icon>
        </v-btn>

        <!-- Mode Buttons Left -->
        <v-btn-toggle
          :model-value="editorMode"
          @update:model-value="$emit('update:editorMode', $event)"
          variant="outlined"
          divided
          dense
        >
          <v-btn value="script">
            <v-icon>mdi-script-text-outline</v-icon>
          </v-btn>
          <v-btn value="scratch">
            <v-icon>mdi-notebook-edit-outline</v-icon>
          </v-btn>
          <v-btn value="metadata">
            <v-icon>mdi-database-edit-outline</v-icon>
          </v-btn>
          <v-btn value="code">
            <v-icon>mdi-code-braces</v-icon>
          </v-btn>
        </v-btn-toggle>

        <v-spacer></v-spacer>

        <!-- Right side: Mode Display Chip, Asset Button, Save Status -->
        <div class="d-flex align-center">
          <!-- Script Mode Display Chip -->
          <v-chip size="small" variant="text" class="mr-2 d-flex align-center" style="padding: 0 12px; min-width: 110px;">
            <v-icon left>{{ getModeIcon(editorMode) }}</v-icon>
            {{ editorMode.toUpperCase() }} MODE
          </v-chip>

          <!-- Asset Management Buttons -->
          <v-btn size="small" @click="$emit('show-asset-browser-modal')" v-if="editorMode === 'scratch'">
            <v-icon left>mdi-paperclip</v-icon>
            Assets
          </v-btn>

          <v-divider vertical class="mx-2"></v-divider>

          <!-- Save Indicator -->
          <v-chip
            :color="hasUnsavedChanges ? 'warning' : 'success'"
            size="small"
            variant="flat"
          >
            <v-icon left>{{ hasUnsavedChanges ? 'mdi-content-save-alert' : 'mdi-content-save' }}</v-icon>
            {{ hasUnsavedChanges ? 'Unsaved' : 'Saved' }}
          </v-chip>

          <v-btn icon size="small" @click="$emit('save')" :disabled="!hasUnsavedChanges">
            <v-icon>mdi-content-save</v-icon>
            <v-tooltip activator="parent" location="bottom">Save Current Item (Ctrl+S)</v-tooltip>
          </v-btn>
        </div>
      </v-toolbar>

      <!-- Cue Insertion Buttons Toolbar: now inside EditorPanel, above the text area -->
      <v-toolbar v-if="editorMode === 'script'" density="comfortable" class="cue-buttons-toolbar px-2 py-1" style="border-bottom: 1px solid var(--v-theme-outline); min-height: 48px; background: rgba(0,0,0,0.05);">
        <span class="text-overline mr-4">Insert Element Cues</span>
        <v-spacer></v-spacer>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-gfx-modal')" color="blue-darken-3" variant="elevated">
          <v-icon size="20">mdi-image</v-icon>
          GFX
          <v-tooltip activator="parent" location="bottom">Alt+G</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-fsq-modal')" color="green-darken-3" variant="elevated">
          <v-icon size="20">mdi-format-quote-close</v-icon>
          FSQ
          <v-tooltip activator="parent" location="bottom">Alt+Q</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-sot-modal')" color="purple-darken-3" variant="elevated">
          <v-icon size="20">mdi-play</v-icon>
          SOT
          <v-tooltip activator="parent" location="bottom">Alt+S</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-vo-modal')" color="deep-orange-darken-3" variant="elevated">
          <v-icon size="20">mdi-microphone</v-icon>
          VO
          <v-tooltip activator="parent" location="bottom">Alt+V</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-nat-modal')" color="teal-darken-3" variant="elevated">
          <v-icon size="20">mdi-volume-high</v-icon>
          NAT
          <v-tooltip activator="parent" location="bottom">Alt+N</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-pkg-modal')" color="red-darken-3" variant="elevated">
          <v-icon size="20">mdi-package-variant</v-icon>
          PKG
          <v-tooltip activator="parent" location="bottom">Alt+P</v-tooltip>
        </v-btn>
        <v-divider vertical class="mx-2"></v-divider>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-vox-modal')" color="cyan-darken-3" variant="elevated">
          <v-icon size="20">mdi-account-voice</v-icon>
          VOX
          <v-tooltip activator="parent" location="bottom">Alt+X</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-mus-modal')" color="orange-darken-3" variant="elevated">
          <v-icon size="20">mdi-music</v-icon>
          MUS
          <v-tooltip activator="parent" location="bottom">Alt+M</v-tooltip>
        </v-btn>
        <v-btn size="small" class="mx-1 cue-btn" @click="$emit('show-live-modal')" color="pink-darken-3" variant="elevated">
          <v-icon size="20">mdi-access-point</v-icon>
          LIVE
          <v-tooltip activator="parent" location="bottom">Alt+L</v-tooltip>
        </v-btn>
      </v-toolbar>

      <!-- Editor Content Area -->
      <v-card-text class="pa-0 editor-content">
        <!-- Script Mode - Markdown Editor -->
        <div v-if="editorMode === 'script'" class="fill-height">
          <v-textarea
            :model-value="scriptContent"
            @update:model-value="onContentInput('script', $event)"
            :placeholder="scriptPlaceholder"
            variant="plain"
            hide-details
            class="editor-textarea"
            style="height: 100%;"
            rows="30"
            auto-grow
          ></v-textarea>
        </div>

        <!-- Scratch Mode - Brainstorming Editor -->
        <div v-else-if="editorMode === 'scratch'" class="fill-height">
          <v-textarea
            :model-value="scratchContent"
            @update:model-value="onContentInput('scratch', $event)"
            :placeholder="scratchPlaceholder"
            variant="plain"
            hide-details
            class="editor-textarea scratch-mode"
            style="height: 100%;"
            @drop="handleAssetDrop"
            @dragover.prevent
            rows="30"
            auto-grow
          ></v-textarea>
        </div>

        <!-- Metadata Mode - Frontmatter Editor -->
        <div v-else-if="editorMode === 'metadata'" class="fill-height metadata-editor-container">
          <div class="metadata-editor pa-4" v-if="internalMetadata">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="internalMetadata.title"
                  label="Title"
                  variant="outlined"
                  density="compact"
                  @input="onMetadataInput"
                  :rules="titleRules"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="internalMetadata.type"
                  :items="itemTypes"
                  label="Type"
                  variant="outlined"
                  density="compact"
                  @update:modelValue="onMetadataInput"
                ></v-select>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="internalMetadata.slug"
                  label="Slug"
                  variant="outlined"
                  density="compact"
                  @input="onMetadataInput"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="internalMetadata.duration"
                  label="Duration"
                  placeholder="00:05:30"
                  variant="outlined"
                  density="compact"
                  @input="onMetadataInput"
                  :rules="durationRules"
                ></v-text-field>
              </v-col>
            </v-row>
            <!-- ... more metadata fields ... -->
          </div>
        </div>

        <!-- Code Mode - Raw Markdown/Cue View -->
        <div v-else-if="editorMode === 'code'" class="fill-height">
          <v-textarea
            :model-value="scriptContent"
            variant="plain"
            hide-details
            readonly
            class="editor-textarea code-mode"
            style="height: 100%; font-family: monospace;"
            rows="30"
            auto-grow
          ></v-textarea>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>

export default {
  name: 'EditorPanel',
  props: {
    item: {
      type: Object,
      default: () => ({})
    },
    editorMode: {
      type: String,
      default: 'script'
    },
    scriptContent: {
      type: String,
      default: ''
    },
    scratchContent: {
      type: String,
      default: ''
    },
    hasUnsavedChanges: {
      type: Boolean,
      default: false
    },
    showRundownPanel: {
      type: Boolean,
      default: true
    }
  },
  emits: [
    'update:scriptContent',
    'update:scratchContent',
    'update:editorMode',
    'metadata-change',
    'content-change',
    'save',
    'show-asset-browser-modal',
    'show-template-manager-modal',
    'show-gfx-modal',
    'show-fsq-modal',
    'show-sot-modal',
    'show-vo-modal',
    'show-nat-modal',
    'show-pkg-modal',
    'show-vox-modal',
    'show-mus-modal',
    'show-live-modal',
    'toggle-rundown-panel'
  ],
  data() {
    return {
      internalMetadata: null,
      // Validation rules
      titleRules: [v => !!v || 'Title is required'],
      durationRules: [
        v => !!v || 'Duration is required',
        v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS'
      ],
      itemTypes: [
        { title: 'Segment', value: 'segment' },
        { title: 'Advertisement', value: 'ad' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Transition', value: 'trans' }
      ]
    };
  },
  computed: {
    scriptPlaceholder() {
      return this.item ? `Enter script for ${this.item.slug}...` : 'Select an item to start editing.';
    },
    scratchPlaceholder() {
      return this.item ? `Scratchpad for ${this.item.slug}...` : 'Select an item to use the scratchpad.';
    }
  },
  watch: {
    item: {
      handler(newItem) {
        if (newItem && newItem.metadata) {
          this.internalMetadata = { ...newItem.metadata };
        } else {
          this.internalMetadata = null;
        }
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    getModeIcon(mode) {
      const icons = {
        script: 'mdi-script-text',
        scratch: 'mdi-pencil',
        metadata: 'mdi-cog',
        code: 'mdi-code-braces'
      };
      return icons[mode] || 'mdi-help-circle';
    },
    onContentInput(mode, value) {
      if (mode === 'script') {
        this.$emit('update:scriptContent', value);
      } else if (mode === 'scratch') {
        this.$emit('update:scratchContent', value);
      }
      this.$emit('content-change');
    },
    onMetadataInput() {
      this.$emit('metadata-change', this.internalMetadata);
    },
    handleAssetDrop(event) {
      event.preventDefault();
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        // Handle file drop, e.g., emit an event
      }
    }
  }
};
</script>

<style scoped>
.editor-panel {
  flex-grow: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.editor-panel.full-width {
  width: 100%;
}
.editor-content {
  height: calc(100vh - 224px); /* Adjust based on toolbar heights */
  overflow-y: auto;
}
.editor-textarea {
  width: 100%;
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
}
.scratch-mode {
  background-color: #fdf5e6; /* A light, distinct color for the scratchpad */
  color: #333;
}
.code-mode {
  background-color: #2d2d2d;
  color: #f8f8f2;
}
.metadata-editor-container {
  overflow-y: auto;
  height: 100%;
}
.cue-buttons-toolbar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}
.cue-btn {
  font-weight: 500;
}
</style>
