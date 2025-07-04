<template>
  <div :class="['editor-panel', !showRundownPanel ? 'full-width' : '']">
    <v-card class="fill-height" flat>
      <!-- Editor Mode and Controls Toolbar -->
      <v-toolbar density="comfortable" color="surface" class="px-2 py-1" style="min-height: 48px;">
        <v-btn
          icon
          size="small"
          @click="$emit('toggle-rundown')"
          v-if="!showRundownPanel"
        >
          <v-icon>mdi-menu</v-icon>
        </v-btn>

        <v-btn-toggle
          :model-value="editorMode"
          @update:model-value="$emit('update:editorMode', $event)"
          mandatory
          class="mx-2"
        >
          <v-btn value="script" size="small">
            <v-icon left>mdi-script-text</v-icon>
            Script
          </v-btn>
          <v-btn value="scratch" size="small">
            <v-icon left>mdi-pencil</v-icon>
            Scratch
          </v-btn>
          <v-btn value="metadata" size="small">
            <v-icon left>mdi-cog</v-icon>
            Metadata
          </v-btn>
        </v-btn-toggle>

        <v-spacer></v-spacer>

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
      </v-toolbar>

      <!-- Editor Content Area -->
      <v-card-text class="pa-0 editor-content">
        <!-- Script Mode - Markdown Editor -->
        <div v-if="editorMode === 'script'" class="fill-height">
          <v-textarea
            :model-value="scriptContent"
            @update:model-value="$emit('update:scriptContent', $event)"
            :placeholder="scriptPlaceholder"
            variant="plain"
            hide-details
            class="editor-textarea"
            style="height: 100%;"
            @input="$emit('content-change')"
            rows="30"
            auto-grow
          ></v-textarea>
        </div>

        <!-- Scratch Mode - Brainstorming Editor -->
        <div v-else-if="editorMode === 'scratch'" class="fill-height">
          <v-textarea
            :model-value="scratchContent"
            @update:model-value="$emit('update:scratchContent', $event)"
            :placeholder="scratchPlaceholder"
            variant="plain"
            hide-details
            class="editor-textarea scratch-mode"
            style="height: 100%;"
            @input="$emit('content-change')"
            @drop="$emit('asset-drop', $event)"
            @dragover.prevent
            rows="30"
            auto-grow
          ></v-textarea>
        </div>

        <!-- Metadata Mode - Frontmatter Editor -->
        <div v-else-if="editorMode === 'metadata'" class="fill-height metadata-editor-container">
          <div class="metadata-editor pa-4">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  :model-value="currentItemMetadata.title"
                  @update:model-value="updateMetadata('title', $event)"
                  label="Title"
                  variant="outlined"
                  density="compact"
                  :rules="titleRules"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  :model-value="currentItemMetadata.type"
                  @update:model-value="updateMetadata('type', $event)"
                  :items="itemTypes"
                  label="Type"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  :model-value="currentItemMetadata.slug"
                  @update:model-value="updateMetadata('slug', $event)"
                  label="Slug"
                  variant="outlined"
                  density="compact"
                  :rules="slugRules"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  :model-value="currentItemMetadata.duration"
                  @update:model-value="updateMetadata('duration', $event)"
                  label="Duration"
                  variant="outlined"
                  density="compact"
                  placeholder="0:00"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12">
                <v-textarea
                  :model-value="currentItemMetadata.description"
                  @update:model-value="updateMetadata('description', $event)"
                  label="Description"
                  variant="outlined"
                  density="compact"
                  rows="3"
                ></v-textarea>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-combobox
                  :model-value="currentItemMetadata.tags"
                  @update:model-value="updateMetadata('tags', $event)"
                  label="Tags"
                  variant="outlined"
                  density="compact"
                  chips
                  multiple
                  clearable
                ></v-combobox>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  :model-value="currentItemMetadata.reporter"
                  @update:model-value="updateMetadata('reporter', $event)"
                  label="Reporter"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
            </v-row>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'EditorPanel',
  emits: [
    'toggle-rundown', 
    'update:editorMode', 
    'show-asset-browser', 
    'save', 
    'content-change',
    'update:scriptContent',
    'update:scratchContent',
    'asset-drop',
    'metadata-change'
  ],
  props: {
    showRundownPanel: {
      type: Boolean,
      default: false
    },
    editorMode: {
      type: String,
      default: 'script',
      validator: (value) => ['script', 'scratch', 'metadata'].includes(value)
    },
    hasUnsavedChanges: {
      type: Boolean,
      default: false
    },
    scriptContent: {
      type: String,
      default: ''
    },
    scratchContent: {
      type: String,
      default: ''
    },
    currentItemMetadata: {
      type: Object,
      default: () => ({})
    },
    scriptPlaceholder: {
      type: String,
      default: 'Start writing your script here...\n\nUse the cue buttons above to insert broadcast elements:\n• GFX - Graphics and lower thirds\n• FSQ - Full screen quotes\n• SOT - Sound on tape/video clips\n• VO - Voice over segments\n• NAT - Natural sound\n• PKG - Pre-produced packages'
    },
    scratchPlaceholder: {
      type: String,
      default: 'Use this space for brainstorming, notes, and rough drafts...\n\n• Drag and drop assets here\n• Experiment with ideas\n• Keep track of research\n• Draft story outlines'
    },
    itemTypes: {
      type: Array,
      default: () => [
        'story',
        'commercial',
        'weather',
        'sports',
        'feature',
        'breaking',
        'live',
        'package',
        'vo',
        'vosot',
        'reader',
        'tease',
        'tag'
      ]
    },
    titleRules: {
      type: Array,
      default: () => [
        v => !!v || 'Title is required',
        v => (v && v.length >= 3) || 'Title must be at least 3 characters'
      ]
    },
    slugRules: {
      type: Array,
      default: () => [
        v => !!v || 'Slug is required',
        v => (v && v.length >= 3) || 'Slug must be at least 3 characters',
        v => /^[a-z0-9-_]+$/.test(v) || 'Slug must be lowercase with only letters, numbers, hyphens, and underscores'
      ]
    }
  },
  methods: {
    updateMetadata(field, value) {
      this.$emit('metadata-change', { field, value })
    }
  }
}
</script>

<style scoped>
.editor-panel {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-panel.full-width {
  width: 100%;
}

.editor-content {
  flex: 1;
  overflow: hidden;
}

.editor-textarea {
  font-family: 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  padding: 16px !important;
  height: calc(100vh - 200px) !important;
  overflow-y: auto !important;
}

.editor-textarea.scratch-mode {
  font-family: 'Roboto', sans-serif !important;
  color: var(--v-medium-emphasis-opacity);
}

.metadata-editor-container {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.metadata-editor {
  max-width: 800px;
  margin: 0 auto;
}

/* Ensure proper spacing in the editor */
.editor-textarea :deep(.v-field__input) {
  padding-top: 16px !important;
}

.editor-textarea :deep(textarea) {
  padding-top: 16px !important;
  min-height: calc(100vh - 250px) !important;
}
</style>
