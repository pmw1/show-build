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
          mandatory
          class="ml-2"
          style="display: flex; align-items: center;"
        >
          <v-btn value="script" size="small" variant="elevated" color="primary">
            <v-icon>mdi-script-text</v-icon>
            Script
          </v-btn>
          <v-btn value="scratch" size="small" variant="elevated" color="secondary">
            <v-icon>mdi-pencil</v-icon>
            Scratch
          </v-btn>
          <v-btn value="metadata" size="small" variant="elevated" color="info">
            <v-icon>mdi-cog</v-icon>
            Metadata
          </v-btn>
        </v-btn-toggle>

        <v-spacer></v-spacer>

        <!-- Right side: Mode Display Chip, Asset Button, Save Status -->
        <div class="d-flex align-center">
          <!-- Script Mode Display Chip -->
          <v-chip size="small" variant="text" class="mr-2 d-flex align-center" style="padding: 0 12px; min-width: 110px;">
            <v-icon left>{{ getModeIcon() }}</v-icon>
            {{ editorMode.toUpperCase() }} MODE
          </v-chip>

          <!-- Asset Management Buttons -->
          <v-btn size="small" @click="$emit('show-asset-browser')" v-if="editorMode === 'scratch'">
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
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import yaml from 'js-yaml';

export default {
  name: 'EditorPanel',
  props: {
    editorMode: { type: String, required: true },
    scriptContent: { type: String, default: '' },
    scratchContent: { type: String, default: '' },
    metadata: { type: Object, default: () => ({}) },
    hasUnsavedChanges: { type: Boolean, default: false },
    showRundownPanel: { type: Boolean, default: true },
    // Pass down validation rules and options from parent
    itemTypes: { type: Array, default: () => [] },
    titleRules: { type: Array, default: () => [] },
    durationRules: { type: Array, default: () => [] },
  },
  emits: [
    'update:editorMode',
    'update:scriptContent',
    'update:scratchContent',
    'update:metadata',
    'save',
    'show-asset-browser',
    'toggle-rundown-panel',
    'asset-drop',
  ],
  data() {
    return {
      internalMetadata: null,
      customMetadataYaml: '',
    };
  },
  computed: {
    scriptPlaceholder() {
      return this.metadata?.title ? `Script for ${this.metadata.title}...` : 'Select an item to start writing...';
    },
    scratchPlaceholder() {
      return this.metadata?.title ? `Scratchpad for ${this.metadata.title}...` : 'Select an item to start brainstorming...';
    },
  },
  watch: {
    metadata: {
      handler(newVal) {
        this.internalMetadata = newVal ? JSON.parse(JSON.stringify(newVal)) : null;
        if (this.internalMetadata?.custom) {
          this.customMetadataYaml = yaml.dump(this.internalMetadata.custom);
        } else {
          this.customMetadataYaml = '';
        }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    onContentInput(contentType, value) {
      if (contentType === 'script') {
        this.$emit('update:scriptContent', value);
      } else if (contentType === 'scratch') {
        this.$emit('update:scratchContent', value);
      }
    },
    onMetadataInput() {
      this.$emit('update:metadata', this.internalMetadata);
    },
    onCustomMetadataChange() {
      try {
        const customData = yaml.load(this.customMetadataYaml);
        this.internalMetadata.custom = customData;
        this.onMetadataInput();
      } catch (e) {
        console.warn("Invalid YAML in custom metadata:", e.message);
      }
    },
    handleAssetDrop(event) {
      this.$emit('asset-drop', event);
    },
  },
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
  flex-grow: 1;
  overflow-y: auto;
}
.editor-textarea {
  width: 100%;
  height: 100%;
  padding: 16px;
  font-family: 'Roboto Mono', monospace;
}
.metadata-editor-container {
  height: 100%;
  overflow-y: auto;
}
.metadata-editor {
  max-width: 960px;
  margin: 0 auto;
}
.cue-buttons-toolbar {
  background: rgba(0,0,0,0.05) !important;
  border-bottom: 1px solid var(--v-theme-outline);
  box-shadow: none !important;
  position: relative;
  z-index: 1;
}
.cue-buttons-toolbar::before {
  content: none;
}
.cue-buttons-toolbar > * {
  position: relative;
  z-index: 3;
}
.cue-btn {
  min-width: 64px;
}
</style>
