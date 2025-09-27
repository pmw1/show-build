<template>
  <div :class="['editor-panel', !showRundownPanel ? 'full-width' : '']">
    <v-card class="fill-height editor-card" flat>
      <!-- Editor Mode and Controls Toolbar -->
      <v-toolbar density="comfortable" color="grey-lighten-4" class="px-2 py-1 editor-toolbar-sticky" style="min-height: 48px;">
        <v-btn
          icon
          size="small"
          @click="$emit('toggle-rundown')"
          v-if="!showRundownPanel"
          rounded="0"
        >
          <v-icon>mdi-menu</v-icon>
        </v-btn>

        <v-btn-toggle
          :model-value="editorMode"
          @update:model-value="$emit('update:editorMode', $event)"
          mandatory
          class="mx-2 editor-mode-toggle"
        >
          <v-btn value="script" size="small" class="mode-btn" rounded="0">
            <v-icon left size="small">mdi-script-text</v-icon>
            Script
          </v-btn>
          <v-divider vertical class="mode-separator"></v-divider>
          <v-btn value="scratch" size="small" class="mode-btn" rounded="0">
            <v-icon left size="small">mdi-pencil</v-icon>
            Scratch
          </v-btn>
          <v-divider vertical class="mode-separator"></v-divider>
          <v-btn value="code" size="small" class="mode-btn" rounded="0">
            <v-icon left size="small">mdi-code-braces</v-icon>
            Code
          </v-btn>
        </v-btn-toggle>

        <v-spacer></v-spacer>

        <!-- Asset Management Buttons -->
        <v-btn size="small" @click="$emit('show-asset-browser')" v-if="editorMode === 'scratch'" rounded="0">
          <v-icon left>mdi-paperclip</v-icon>
          Assets
        </v-btn>

        <v-divider vertical class="mx-2"></v-divider>

        <!-- Autosave Status and Save Buttons -->
        <div class="save-controls d-flex align-center gap-2">
          <!-- Autosave Status with Save Button Below -->
          <div class="autosave-section d-flex flex-column align-center">
            <div class="autosave-status text-caption text-medium-emphasis">
              <div class="text-center">
                <span>Autosave</span>
                <div class="text-xs opacity-75">{{ formatTimestamp(new Date()) }}</div>
              </div>
            </div>
            
          </div>

          <!-- Horizontal Divider -->
          <v-divider vertical class="mx-2"></v-divider>

          <!-- Save All Button -->
          <v-btn
            size="small"
            :color="saveState?.buttonColor || 'success'"
            variant="elevated"
            @click="$emit('save-all')"
            :disabled="saveState?.isDisabled ?? true"
            class="save-all-btn px-4"
            rounded="0"
          >
            <v-icon size="small" class="mr-1">{{ saveState?.buttonIcon || 'mdi-check-circle' }}</v-icon>
            {{ saveState?.buttonText || 'Synchronized' }}
            <v-tooltip activator="parent" location="bottom">{{ saveState?.tooltip || 'Episode is synchronized - no changes to save' }}</v-tooltip>
          </v-btn>

          <!-- Horizontal Divider -->
          <v-divider vertical class="mx-2"></v-divider>

          <!-- Metadata Panel Toggle -->
          <v-btn 
            size="small"
            :color="showMetadataPanel ? 'secondary' : 'grey'"
            :variant="showMetadataPanel ? 'elevated' : 'outlined'"
            @click="$emit('toggle-metadata-panel')"
            class="metadata-toggle-btn px-3"
            rounded="0"
          >
            <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
            Metadata
            <v-tooltip activator="parent" location="bottom">{{ showMetadataPanel ? 'Hide Metadata Panel' : 'Show Metadata Panel' }}</v-tooltip>
          </v-btn>
        </div>
      </v-toolbar>

      <!-- Editor Content Area -->
      <v-card-text class="pa-0 editor-content">

        <!-- Script Mode - Markdown Editor -->
        <div v-if="editorMode === 'script'" class="fill-height d-flex flex-column">

          <!-- Insert Cues Toolbar (inside script mode only) -->
          <div v-if="showCuesToolbar" class="editor-cues-toolbar cues-toolbar-sticky">
            <div class="cue-buttons-flex-container">

              <v-btn
                variant="flat"
                class="cue-btn-flex img-btn"
                :style="getCueButtonStyle('IMG')"
                @click="insertCue('IMG')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-image</v-icon>
                  <span class="cue-label">IMG</span>
                  <span class="hotkey-display">[ALT+I]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Image/Photo</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex gfx-btn"
                :style="getCueButtonStyle('GFX')"
                @click="insertCue('GFX')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-image-outline</v-icon>
                  <span class="cue-label">GFX</span>
                  <span class="hotkey-display">[ALT+G]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Graphics & Lower Thirds</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex fsq-btn"
                :style="getCueButtonStyle('FSQ')"
                @click="insertCue('FSQ')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-format-quote-close</v-icon>
                  <span class="cue-label">FSQ</span>
                  <span class="hotkey-display">[ALT+Q]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Full Screen Quote</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex sot-btn"
                :style="getCueButtonStyle('SOT')"
                @click="insertCue('SOT')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-play-circle-outline</v-icon>
                  <span class="cue-label">SOT</span>
                  <span class="hotkey-display">[ALT+S]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Sound on Tape</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex vo-btn"
                :style="getCueButtonStyle('VO')"
                @click="insertCue('VO')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-microphone</v-icon>
                  <span class="cue-label">VO</span>
                  <span class="hotkey-display">[ALT+V]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Voice Over</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex nat-btn"
                :style="getCueButtonStyle('NAT')"
                @click="insertCue('NAT')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-volume-high</v-icon>
                  <span class="cue-label">NAT</span>
                  <span class="hotkey-display">[ALT+N]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Natural Sound</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex pkg-btn"
                :style="getCueButtonStyle('PKG')"
                @click="insertCue('PKG')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-package-variant</v-icon>
                  <span class="cue-label">PKG</span>
                  <span class="hotkey-display">[ALT+P]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Package</v-tooltip>
              </v-btn>
            </div>
          </div>

          <!-- Text formatting shortcuts box below cue toolbar -->
          <div class="text-formatting-box text-formatting-sticky d-flex align-center justify-center">
            <span class="formatting-hotkey"><strong>CTRL+B</strong> Bold</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+I</strong> Italic</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+U</strong> Underline</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+S</strong> Save</span>
          </div>

          <!-- Script Content Area with embedded fields -->
          <div class="script-content-container flex-grow-1">
            <!-- Slug and Duration Fields at Top of Script -->
            <div class="script-header-fields">
              <v-text-field
                :model-value="item?.slug || ''"
                @update:model-value="$emit('update:slug', $event)"
                placeholder="segment-slug"
                variant="plain"
                hide-details
                class="script-slug-field-inline"
                :disabled="hasNoItem"
              ></v-text-field>
              <v-text-field
                :model-value="item?.duration || ''"
                @update:model-value="$emit('update:duration', $event)"
                placeholder="00:05:00"
                variant="plain"
                hide-details
                class="script-duration-field-inline"
                :disabled="hasNoItem"
              ></v-text-field>
              <v-btn
                :color="hasUnsavedRundownChanges ? 'primary' : 'success'"
                variant="elevated"
                class="script-save-button"
                :disabled="hasNoItem"
                @click="$emit('save-all')"
              >
                <v-icon size="small" class="mr-2">
                  {{ hasUnsavedRundownChanges ? 'mdi-content-save' : 'mdi-check-circle' }}
                </v-icon>
                {{ hasUnsavedRundownChanges ? 'Save Rundown' : 'Synchronized' }}
              </v-btn>
            </div>

            <v-textarea
              :model-value="hasNoItem ? '' : scriptContent"
              @update:model-value="hasNoItem ? null : $emit('update:scriptContent', $event)"
              :placeholder="hasNoItem ? noItemPlaceholder : scriptPlaceholder"
              :disabled="hasNoItem"
              variant="plain"
              hide-details
              class="editor-textarea script-textarea script-textarea-with-header"
              :class="{ 'ghost-text': hasNoItem }"
              @input="hasNoItem ? null : $emit('content-change')"
              no-resize
            ></v-textarea>
          </div>
        </div>

        <!-- Scratch Mode - Brainstorming Editor -->
        <div v-else-if="editorMode === 'scratch'" class="fill-height d-flex flex-column">
          <!-- Insert Cues Toolbar (inside scratch mode) -->
          <div v-if="showCuesToolbar" class="editor-cues-toolbar cues-toolbar-sticky">
            <div class="cue-buttons-flex-container">

              <v-btn
                variant="flat"
                class="cue-btn-flex img-btn"
                :style="getCueButtonStyle('IMG')"
                @click="insertCue('IMG')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-image</v-icon>
                  <span class="cue-label">IMG</span>
                  <span class="hotkey-display">[ALT+I]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Image/Photo</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex gfx-btn"
                :style="getCueButtonStyle('GFX')"
                @click="insertCue('GFX')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-image-outline</v-icon>
                  <span class="cue-label">GFX</span>
                  <span class="hotkey-display">[ALT+G]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Graphics & Lower Thirds</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex fsq-btn"
                :style="getCueButtonStyle('FSQ')"
                @click="insertCue('FSQ')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-format-quote-close</v-icon>
                  <span class="cue-label">FSQ</span>
                  <span class="hotkey-display">[ALT+Q]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Full Screen Quote</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex sot-btn"
                :style="getCueButtonStyle('SOT')"
                @click="insertCue('SOT')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-play-circle-outline</v-icon>
                  <span class="cue-label">SOT</span>
                  <span class="hotkey-display">[ALT+S]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Sound on Tape</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex vo-btn"
                :style="getCueButtonStyle('VO')"
                @click="insertCue('VO')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-microphone</v-icon>
                  <span class="cue-label">VO</span>
                  <span class="hotkey-display">[ALT+V]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Voice Over</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex nat-btn"
                :style="getCueButtonStyle('NAT')"
                @click="insertCue('NAT')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-volume-high</v-icon>
                  <span class="cue-label">NAT</span>
                  <span class="hotkey-display">[ALT+N]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Natural Sound</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex pkg-btn"
                :style="getCueButtonStyle('PKG')"
                @click="insertCue('PKG')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-package-variant</v-icon>
                  <span class="cue-label">PKG</span>
                  <span class="hotkey-display">[ALT+P]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Package</v-tooltip>
              </v-btn>
            </div>
          </div>

          <!-- Text formatting shortcuts box below cue toolbar -->
          <div class="text-formatting-box text-formatting-sticky d-flex align-center justify-center">
            <span class="formatting-hotkey"><strong>CTRL+B</strong> Bold</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+I</strong> Italic</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+U</strong> Underline</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+S</strong> Save</span>
          </div>

          <v-textarea
            :model-value="scratchContent"
            @update:model-value="$emit('update:scratchContent', $event)"
            :placeholder="scratchPlaceholder"
            variant="plain"
            hide-details
            class="editor-textarea scratch-mode flex-grow-1"
            @input="$emit('content-change')"
            @drop="$emit('asset-drop', $event)"
            @dragover.prevent
            no-resize
          ></v-textarea>
        </div>

        <!-- Metadata Mode - Comprehensive Frontmatter Editor -->
        <div v-else-if="editorMode === 'metadata'" class="fill-height metadata-editor-container">
          <div class="metadata-editor pa-4">
            <!-- Enhanced debug info -->
            <div v-if="!currentItemMetadata || meaningfulFieldCount === 0" class="mb-4">
              <v-alert type="warning" variant="outlined">
                <div class="text-body-1 mb-2">
                  <strong>No meaningful metadata available.</strong> Fields with actual data: {{ meaningfulFieldCount }}
                </div>
                <details class="mt-2">
                  <summary class="cursor-pointer text-subtitle-2">Show raw metadata debug info</summary>
                  <pre class="mt-2 pa-2 bg-grey-lighten-4 text-caption">{{ JSON.stringify(currentItemMetadata, null, 2) }}</pre>
                </details>
                <div class="mt-2 text-caption">
                  <strong>Tip:</strong> Try creating a new rundown item to see if metadata fields populate correctly.
                </div>
              </v-alert>
            </div>
            <!-- Header with AssetID and Creation Info -->
            <v-card class="mb-4" variant="tonal" :color="currentItemMetadata.AssetID ? 'primary' : 'warning'">
              <v-card-text class="pb-2">
                <v-row no-gutters>
                  <v-col cols="12" md="6">
                    <div class="text-subtitle-2 mb-1">AssetID</div>
                    <div class="text-body-1 font-weight-medium">
                      <span v-if="currentItemMetadata.AssetID">
                        {{ currentItemMetadata.AssetID }}
                      </span>
                      <span v-else class="text-warning font-weight-bold">
                        <v-icon size="small" class="mr-1">mdi-alert</v-icon>
                        Not assigned (null)
                      </span>
                    </div>
                  </v-col>
                  <v-col cols="12" md="6">
                    <div class="text-subtitle-2 mb-1">Created</div>
                    <div class="text-body-2">
                      <span v-if="currentItemMetadata.created_at">
                        {{ formatDateTime(currentItemMetadata.created_at) }}
                      </span>
                      <span v-else class="text-warning">
                        <v-icon size="small" class="mr-1">mdi-alert</v-icon>
                        Unknown (null)
                      </span>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Basic Information Section -->
            <v-card class="mb-4" variant="outlined">
              <v-card-title class="text-h6 py-3">
                <v-icon class="mr-2">mdi-information</v-icon>
                Basic Information
              </v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="currentItemMetadata.title"
                      @update:model-value="updateMetadata('title', $event)"
                      label="Title"
                      variant="outlined"
                      density="comfortable"
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
                      density="comfortable"
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
                      density="comfortable"
                      :rules="slugRules"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="currentItemMetadata.subtitle"
                      @update:model-value="updateMetadata('subtitle', $event)"
                      label="Subtitle"
                      variant="outlined"
                      density="comfortable"
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
                      density="comfortable"
                      rows="3"
                      auto-grow
                    ></v-textarea>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Production Details Section -->
            <v-card class="mb-4" variant="outlined">
              <v-card-title class="text-h6 py-3">
                <v-icon class="mr-2">mdi-play-box-outline</v-icon>
                Production Details
              </v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="currentItemMetadata.duration"
                      @update:model-value="updateMetadata('duration', $event)"
                      label="Duration"
                      variant="outlined"
                      density="comfortable"
                      placeholder="00:00:00"
                      hint="Format: HH:MM:SS or MM:SS"
                      persistent-hint
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      :model-value="currentItemMetadata.status"
                      @update:model-value="updateMetadata('status', $event)"
                      :items="statusOptions"
                      label="Status"
                      variant="outlined"
                      density="comfortable"
                    ></v-select>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12" md="4">
                    <v-text-field
                      :model-value="currentItemMetadata.order"
                      @update:model-value="updateMetadata('order', $event)"
                      label="Order"
                      variant="outlined"
                      density="comfortable"
                      type="number"
                      min="1"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-select
                      :model-value="currentItemMetadata.priority"
                      @update:model-value="updateMetadata('priority', $event)"
                      :items="priorityOptions"
                      label="Priority"
                      variant="outlined"
                      density="comfortable"
                      clearable
                    ></v-select>
                  </v-col>
                  <v-col cols="12" md="4">
                    <v-text-field
                      :model-value="currentItemMetadata.airdate"
                      @update:model-value="updateMetadata('airdate', $event)"
                      label="Air Date"
                      variant="outlined"
                      density="comfortable"
                      type="date"
                    ></v-text-field>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- People & Resources Section -->
            <v-card class="mb-4" variant="outlined">
              <v-card-title class="text-h6 py-3">
                <v-icon class="mr-2">mdi-account-group</v-icon>
                People & Resources
              </v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="currentItemMetadata.guests"
                      @update:model-value="updateMetadata('guests', $event)"
                      label="Guests"
                      variant="outlined"
                      density="comfortable"
                      hint="Comma-separated list of guest names"
                      persistent-hint
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="currentItemMetadata.resources"
                      @update:model-value="updateMetadata('resources', $event)"
                      label="Resources"
                      variant="outlined"
                      density="comfortable"
                      hint="Links, files, or reference materials"
                      persistent-hint
                    ></v-text-field>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12">
                    <v-combobox
                      :model-value="parseTagsForDisplay(currentItemMetadata.tags)"
                      @update:model-value="updateTagsFromCombobox"
                      label="Tags"
                      variant="outlined"
                      density="comfortable"
                      chips
                      multiple
                      clearable
                      hint="Press Enter to add a new tag"
                      persistent-hint
                    ></v-combobox>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- System Information Section -->
            <v-card class="mb-4" variant="outlined">
              <v-card-title class="text-h6 py-3">
                <v-icon class="mr-2">mdi-server</v-icon>
                System Information
              </v-card-title>
              <v-card-text>
                <v-row>
                  <v-col cols="12">
                    <v-textarea
                      :model-value="currentItemMetadata.server_message"
                      @update:model-value="updateMetadata('server_message', $event)"
                      label="Server Message"
                      variant="outlined"
                      density="comfortable"
                      rows="2"
                      auto-grow
                      readonly
                      hint="System-generated audit trail (read-only)"
                      persistent-hint
                    ></v-textarea>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Dynamic/Custom Fields Section -->
            <v-card v-if="hasCustomFields" class="mb-4" variant="outlined">
              <v-card-title class="text-h6 py-3">
                <v-icon class="mr-2">mdi-code-braces</v-icon>
                Custom Fields
              </v-card-title>
              <v-card-text>
                <div v-for="(value, key) in customFields" :key="key" class="mb-3">
                  <v-text-field
                    :model-value="value"
                    @update:model-value="updateMetadata(key, $event)"
                    :label="formatFieldLabel(key)"
                    variant="outlined"
                    density="comfortable"
                    :hint="`Custom field: ${key}`"
                    persistent-hint
                  ></v-text-field>
                </div>
              </v-card-text>
            </v-card>

          </div>
        </div>

        <!-- Code Mode - Raw Markdown/Code Editor -->
        <div v-else-if="editorMode === 'code'" class="fill-height d-flex flex-column">
          <!-- Insert Cues Toolbar (inside code mode) -->
          <div v-if="showCuesToolbar" class="editor-cues-toolbar cues-toolbar-sticky">
            <div class="cue-buttons-flex-container">

              <v-btn
                variant="flat"
                class="cue-btn-flex img-btn"
                :style="getCueButtonStyle('IMG')"
                @click="insertCue('IMG')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-image</v-icon>
                  <span class="cue-label">IMG</span>
                  <span class="hotkey-display">[ALT+I]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Image/Photo</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex gfx-btn"
                :style="getCueButtonStyle('GFX')"
                @click="insertCue('GFX')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-image-outline</v-icon>
                  <span class="cue-label">GFX</span>
                  <span class="hotkey-display">[ALT+G]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Graphics & Lower Thirds</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex fsq-btn"
                :style="getCueButtonStyle('FSQ')"
                @click="insertCue('FSQ')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-format-quote-close</v-icon>
                  <span class="cue-label">FSQ</span>
                  <span class="hotkey-display">[ALT+Q]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Full Screen Quote</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex sot-btn"
                :style="getCueButtonStyle('SOT')"
                @click="insertCue('SOT')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-play-circle-outline</v-icon>
                  <span class="cue-label">SOT</span>
                  <span class="hotkey-display">[ALT+S]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Sound on Tape</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex vo-btn"
                :style="getCueButtonStyle('VO')"
                @click="insertCue('VO')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-microphone</v-icon>
                  <span class="cue-label">VO</span>
                  <span class="hotkey-display">[ALT+V]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Voice Over</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex nat-btn"
                :style="getCueButtonStyle('NAT')"
                @click="insertCue('NAT')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-volume-high</v-icon>
                  <span class="cue-label">NAT</span>
                  <span class="hotkey-display">[ALT+N]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Natural Sound</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex pkg-btn"
                :style="getCueButtonStyle('PKG')"
                @click="insertCue('PKG')"
              >
                <div class="cue-btn-content-flex">
                  <v-icon size="small" class="mb-1">mdi-package-variant</v-icon>
                  <span class="cue-label">PKG</span>
                  <span class="hotkey-display">[ALT+P]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Package</v-tooltip>
              </v-btn>
            </div>
          </div>

          <!-- Text formatting shortcuts box below cue toolbar -->
          <div class="text-formatting-box text-formatting-sticky d-flex align-center justify-center">
            <span class="formatting-hotkey"><strong>CTRL+B</strong> Bold</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+I</strong> Italic</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+U</strong> Underline</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+S</strong> Save</span>
          </div>

          <v-textarea
            :model-value="hasNoItem ? '' : rawMarkdownContent"
            @update:model-value="hasNoItem ? null : $emit('update:rawMarkdownContent', $event)"
            :placeholder="hasNoItem ? noItemPlaceholder : 'Edit the raw markdown content including frontmatter and body content...'"
            :disabled="hasNoItem"
            variant="plain"
            hide-details
            class="code-textarea flex-grow-1"
            :class="{ 'ghost-text': hasNoItem }"
            style="font-family: 'Roboto Mono', monospace;"
            no-resize
            @input="hasNoItem ? null : $emit('content-change')"
          ></v-textarea>
        </div>
      </v-card-text>
    </v-card>
  </div>

  <!-- IMG Cue Modal -->
  <ImgCueModal 
    v-model:show="showImgModal"
    @submit="handleImgCueSubmit"
  />
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap.js';
import ImgCueModal from './modals/ImgCueModal.vue';

export default {
  name: 'EditorPanel',
  components: {
    ImgCueModal
  },
  data() {
    return {
      showImgModal: false
    }
  },
  mounted() {
    console.log('EditorPanel mounted with metadata:', this.currentItemMetadata);
  },
  watch: {
    currentItemMetadata: {
      handler(newVal) {
        console.log('EditorPanel currentItemMetadata changed:', newVal);
      },
      deep: true,
      immediate: true
    }
  },
  emits: [
    'toggle-rundown',
    'toggle-metadata-panel',
    'update:editorMode',
    'show-asset-browser',
    'save',
    'save-all',
    'content-change',
    'update:scriptContent',
    'update:scratchContent',
    'update:rawMarkdownContent',
    'update:slug',
    'asset-drop',
    'metadata-change',
    'insert-cue',
    'show-img-modal',
    'show-gfx-modal',
    'show-fsq-modal',
    'show-sot-modal',
    'show-vo-modal',
    'show-nat-modal',
    'show-pkg-modal',
    'show-vox-modal',
    'show-mus-modal',
    'show-live-modal'
  ],
  props: {
    showRundownPanel: {
      type: Boolean,
      default: false
    },
    showMetadataPanel: {
      type: Boolean,
      default: false
    },
    editorMode: {
      type: String,
      default: 'script',
      validator: (value) => ['script', 'scratch', 'code'].includes(value)
    },
    hasUnsavedChanges: {
      type: Boolean,
      default: false
    },
    hasUnsavedRundownChanges: {
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
    rawMarkdownContent: {
      type: String,
      default: ''
    },
    item: {
      type: Object,
      default: null
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
        'segment',
        'coldopen',
        'ad',
        'promo',
        'cta',
        'trans',
        'interview',
        'package',
        'tease',
        'reader',
        'story',
        'commercial',
        'weather',
        'sports',
        'feature',
        'breaking',
        'live',
        'vo',
        'vosot',
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
    },
    saveState: {
      type: Object,
      default: () => ({
        hasChanges: false,
        buttonText: 'Synchronized',
        buttonColor: 'success',
        buttonIcon: 'mdi-check-circle',
        isDisabled: true,
        tooltip: 'Episode is synchronized - no changes to save'
      })
    }
  },
  computed: {
    // Enhanced options for select fields
    statusOptions() {
      return [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'In Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ]
    },
    
    priorityOptions() {
      return [
        { title: 'Low', value: 'low' },
        { title: 'Normal', value: 'normal' },
        { title: 'High', value: 'high' },
        { title: 'Urgent', value: 'urgent' }
      ]
    },

    // Detect custom fields that aren't part of the standard schema
    customFields() {
      if (!this.currentItemMetadata) return {}
      
      const standardFields = [
        'AssetID', 'title', 'type', 'slug', 'subtitle', 'description', 
        'duration', 'status', 'order', 'airdate', 'priority', 'guests', 
        'resources', 'tags', 'server_message', 'created_at'
      ]
      
      const custom = {}
      Object.keys(this.currentItemMetadata).forEach(key => {
        if (!standardFields.includes(key) && this.currentItemMetadata[key] !== null && this.currentItemMetadata[key] !== '') {
          custom[key] = this.currentItemMetadata[key]
        }
      })
      
      return custom
    },

    // Check if there are any custom fields to display
    hasCustomFields() {
      return Object.keys(this.customFields).length > 0
    },

    // Count fields with meaningful (non-null, non-empty) data
    meaningfulFieldCount() {
      if (!this.currentItemMetadata) return 0
      return Object.keys(this.currentItemMetadata).filter(key => {
        const value = this.currentItemMetadata[key]
        return value !== null && value !== undefined && value !== ''
      }).length
    },

    // Show cues toolbar for Script, Scratch, and Code modes (not Metadata)
    showCuesToolbar() {
      return ['script', 'scratch', 'code'].includes(this.editorMode)
    },

    // Detect when no rundown item is selected
    hasNoItem() {
      return !this.item || this.item === null
    },

    // Ghost text for when no item is selected
    noItemPlaceholder() {
      return 'To begin editing your show content, add an item to your rundown.'
    }
  },
  methods: {
    updateMetadata(field, value) {
      this.$emit('metadata-change', { field, value })
    },

    // Format datetime for display
    formatDateTime(dateString) {
      if (!dateString) return null
      try {
        const date = new Date(dateString)
        return date.toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (e) {
        return dateString
      }
    },

    // Format field labels for custom fields (convert snake_case to Title Case)
    formatFieldLabel(fieldName) {
      return fieldName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },

    // Parse tags for display in combobox
    parseTagsForDisplay(tags) {
      if (!tags) return []
      if (Array.isArray(tags)) return tags
      if (typeof tags === 'string') {
        // Handle comma-separated string or YAML array-like format
        return tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
      }
      return []
    },

    // Update tags from combobox back to appropriate format
    updateTagsFromCombobox(tags) {
      // Convert array back to comma-separated string for consistency
      const tagString = Array.isArray(tags) ? tags.join(', ') : tags
      this.updateMetadata('tags', tagString)
    },

    // Format timestamp for autosave display
    formatTimestamp(date) {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },

    // Insert broadcast cue at cursor position
    insertCue(cueType) {
      // All cue buttons should trigger their respective modals (same as hotkeys)
      if (cueType === 'IMG') {
        this.$emit('show-img-modal')
        return
      }
      
      if (cueType === 'GFX') {
        this.$emit('show-gfx-modal')
        return
      }
      
      if (cueType === 'FSQ') {
        this.$emit('show-fsq-modal')
        return
      }
      
      if (cueType === 'SOT') {
        this.$emit('show-sot-modal')
        return
      }
      
      if (cueType === 'VO') {
        this.$emit('show-vo-modal')
        return
      }
      
      if (cueType === 'NAT') {
        this.$emit('show-nat-modal')
        return
      }
      
      if (cueType === 'PKG') {
        this.$emit('show-pkg-modal')
        return
      }

      // Fallback for any other cue types
      const cueText = `**[${cueType}: ]**`
      this.$emit('insert-cue', { cueType, cueText, editorMode: this.editorMode })
    },

    // Get theme color for cue type
    getCueColor(cueType) {
      const colorName = getColorValue(cueType.toLowerCase())
      return resolveVuetifyColor(colorName)
    },

    // Get cue button style object
    getCueButtonStyle(cueType) {
      const backgroundColor = this.getCueColor(cueType)
      return {
        backgroundColor: backgroundColor,
        borderColor: backgroundColor
      }
    },

    // Normalize slug for filename
    normalizeSlug(slug) {
      return slug
        .toLowerCase() // Convert to lowercase
        .replace(/[^\w\s-]/g, '') // Remove punctuation except spaces and hyphens
        .replace(/\s+/g, '-') // Convert spaces to hyphens
        .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
        .replace(/^-|-$/g, '') // Remove leading/trailing hyphens
    },

    // Handle IMG cue submission from modal
    async handleImgCueSubmit(imgCueData) {
      try {
        // Normalize the slug for filename
        const normalizedSlug = this.normalizeSlug(imgCueData.slug)
        const fileExtension = imgCueData.imageFile.type.split('/')[1] || 'png'
        const filename = `${normalizedSlug}.${fileExtension}`
        
        // Upload image file to server
        const formData = new FormData()
        formData.append('file', imgCueData.imageFile)
        formData.append('filename', filename)
        
        const uploadResponse = await fetch('/api/upload/image', {
          method: 'POST',
          body: formData
        })
        
        if (!uploadResponse.ok) {
          throw new Error('Failed to upload image')
        }
        
        await uploadResponse.json() // Process response but don't store unused result
        const mediaUrl = `../assets/images/${filename}`
        
        // Generate the IMG cue block based on the examples you provided
        const imgCueBlock = `<!-- Begin Cue -->
[Type: IMG]
[AssetID: ${imgCueData.assetId}]
[Slug: ${normalizedSlug}]
[Description: ${imgCueData.description || ''}]
[Credit: ${imgCueData.credit || ''}]
[Caption: ${imgCueData.caption || ''}]
[MediaURL: ${mediaUrl}]
<!-- End Cue -->`

        // Emit the cue for insertion
        this.$emit('insert-cue', { 
          cueType: 'IMG', 
          cueText: imgCueBlock, 
          editorMode: this.editorMode,
          imageFile: imgCueData.imageFile,
          filename: filename
        })

        console.log('IMG cue created:', imgCueData)
      } catch (error) {
        console.error('Error handling IMG cue submission:', error)
        // TODO: Show error message to user
      }
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

/* Ensure v-card uses flex layout properly */
.editor-card {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  /* Remove overflow: hidden to allow proper scrolling */
}

.editor-textarea {
  font-family: 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  padding: 16px 32px !important;
  margin: 0 16px !important;
  min-height: calc(100vh - 200px) !important;
  overflow-y: auto !important;
  text-indent: 8px !important;
}

.editor-textarea.scratch-mode {
  font-family: 'Roboto', sans-serif !important;
  color: var(--v-medium-emphasis-opacity);
}

/* Script Mode Header Fields */
.script-content-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.script-header-fields {
  display: flex;
  gap: 16px;
  padding: 16px 32px 8px 32px;
  margin: 0 16px;
  background-color: transparent;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  align-items: stretch;
}

.script-slug-field-inline,
.script-duration-field-inline {
  background-color: #f8f8f8 !important;
  border-radius: 0 !important;
  border: none !important;
}

.script-slug-field-inline {
  flex: 2;
}

.script-duration-field-inline {
  flex: 1;
  min-width: 120px;
}

.script-save-button {
  flex: 0 0 auto;
  min-width: 140px;
  height: auto !important;
  align-self: stretch;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 0 !important;
  padding: 0 16px !important;
}

.script-save-button :deep(.v-btn__content) {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.script-slug-field-inline :deep(.v-field__input),
.script-duration-field-inline :deep(.v-field__input) {
  font-size: 200% !important;
  color: #555555 !important;
  font-weight: 500 !important;
  padding: 12px 16px !important;
  background-color: #f8f8f8 !important;
  border-radius: 0 !important;
}

.script-slug-field-inline :deep(.v-field__field),
.script-duration-field-inline :deep(.v-field__field) {
  background-color: #f8f8f8 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
}

.script-slug-field-inline :deep(.v-field__outline),
.script-duration-field-inline :deep(.v-field__outline) {
  display: none !important;
}

.script-textarea-with-header {
  padding-top: 0 !important;
}

.metadata-editor-container {
  min-height: calc(100vh - 200px);
  overflow-y: auto;
}

.metadata-editor {
  max-width: 800px;
  margin: 0 auto;
}

/* Code editor specific styling - now extends to bottom of page */
.code-editor-container {
  min-height: calc(100vh - 200px); /* Account for header, toolbars, and cue bar */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background-color: #fafafa; /* Slightly off-white background */
  margin: 0 !important;
  padding: 0 !important;
}

.code-editor {
  height: 100%;
  margin: 0 !important;
  padding: 16px !important; /* Override pa-4 with consistent padding */
  display: flex;
  flex-direction: column;
}

.code-textarea {
  font-family: 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  padding: 16px !important;
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
  margin: 0 !important;
  background-color: white; /* Keep textarea background white for contrast */
}

.code-textarea :deep(.v-field) {
  height: 100% !important;
  flex: 1 !important;
}

.code-textarea :deep(.v-field__input) {
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
}

.code-textarea :deep(textarea) {
  font-family: 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  padding: 16px !important;
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
  resize: none !important;
  box-sizing: border-box !important;
}

/* Script textarea specific styling */
.script-textarea {
  white-space: pre-wrap !important;
  word-wrap: break-word !important;
  height: 100% !important;
  flex: 1 !important;
}

.script-textarea :deep(.v-field) {
  height: 100% !important;
  flex: 1 !important;
}

.script-textarea :deep(.v-field__input) {
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
}

.script-textarea :deep(textarea) {
  white-space: pre-wrap !important;
  word-wrap: break-word !important;
  line-height: 1.6 !important;
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
  resize: none !important;
  box-sizing: border-box !important;
  padding: 16px !important;
}

/* Scratch mode styling - same as script */
.scratch-mode {
  height: 100% !important;
  flex: 1 !important;
}

.scratch-mode :deep(.v-field) {
  height: 100% !important;
  flex: 1 !important;
}

.scratch-mode :deep(.v-field__input) {
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
}

.scratch-mode :deep(textarea) {
  height: 100% !important;
  flex: 1 !important;
  overflow-y: auto !important;
  resize: none !important;
  box-sizing: border-box !important;
  padding: 16px !important;
  line-height: 1.6 !important;
}

/* Ensure proper spacing in all editor modes */
.editor-textarea :deep(.v-field__input) {
  padding-top: 16px !important;
}

.editor-textarea :deep(textarea) {
  padding-top: 16px !important;
}

/* Sticky Toolbar Styling */
.editor-toolbar-sticky {
  position: sticky !important;
  top: 0 !important;
  z-index: 10 !important;
  background-color: #f5f5f5 !important;
  border-bottom: 1px solid #e0e0e0 !important;
}

/* Sticky Cues Toolbar */
.cues-toolbar-sticky {
  position: sticky !important;
  top: 48px !important; /* Position below the main toolbar */
  z-index: 9 !important;
  background-color: white !important;
  border-bottom: 1px solid #e0e0e0 !important;
}

/* Sticky Text Formatting Box */
.text-formatting-sticky {
  position: sticky !important;
  top: 108px !important; /* Position below main toolbar + cues toolbar */
  z-index: 8 !important;
  background-color: #fafafa !important;
  border-bottom: 1px solid #e0e0e0 !important;
}

/* Toolbar Mode Button Styling */
.editor-mode-toggle {
  background: transparent !important;
  border: none !important;
}

.mode-btn {
  background-color: rgb(var(--v-theme-surface-variant)) !important;
  color: rgb(var(--v-theme-on-surface-variant)) !important;
  border: 1px solid rgba(var(--v-theme-outline), 0.2) !important;
}

.mode-btn.v-btn--active {
  background-color: rgb(var(--v-theme-surface)) !important;
  color: rgb(var(--v-theme-primary)) !important;
  border: 1px solid rgb(var(--v-theme-primary)) !important;
}

.mode-separator {
  height: 24px !important;
  opacity: 0.3 !important;
  margin: 0 2px !important;
}

/* Save Controls Styling */
.save-controls {
  min-width: 180px;
}

.autosave-section {
  min-width: 80px;
}

.autosave-status {
  text-align: center;
  line-height: 1.1;
  min-width: 60px;
}

.save-divider {
  height: 28px !important;
  opacity: 0.4 !important;
}

.save-btn {
  font-size: 11px !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;
}

.save-btn:disabled {
  background-color: rgb(var(--v-theme-success)) !important;
  color: white !important;
  opacity: 0.8 !important;
}

.save-all-btn {
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  height: 36px !important;
  min-height: 36px !important;
}

.save-all-btn:disabled {
  background-color: rgb(var(--v-theme-success)) !important;
  color: white !important;
  opacity: 1 !important;
}

/* Cues Toolbar Styling */
.cues-toolbar {
  border-top: 1px solid rgba(var(--v-theme-outline), 0.1) !important;
  border-bottom: 2px solid #ccc !important;
  min-height: 60px !important;
}

.cue-btn {
  margin: 0 2px !important;
  min-height: 52px !important;
  min-width: 95px !important;
  padding: 6px 8px !important;
  text-transform: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.cue-btn-content {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
}

.cue-label {
  font-size: 14px !important;
  font-weight: 700 !important;
  letter-spacing: 0.5px !important;
}

.hotkey-display {
  font-size: 9.5px !important;
  font-weight: 500 !important;
  opacity: 1 !important;
  line-height: 1 !important;
  margin-top: 1px !important;
  text-align: center !important;
  color: rgba(0, 0, 0, 0.9) !important;
}

.hotkey-display strong {
  font-weight: 700 !important;
  color: rgba(0, 0, 0, 1) !important;
}

.cue-btn .v-icon {
  margin-right: 3px !important;
}

.gap-1 {
  gap: 4px;
}

/* Insert Cue Label Styling */
.insert-cue-label {
  font-size: 13px !important;
  font-weight: 700 !important;
  color: rgba(0, 0, 0, 0.7) !important;
  line-height: 0.9 !important;
  text-align: right !important;
}

/* Lesser Hotkeys List Styling */
.lesser-hotkeys {
  gap: 2px;
}

.hotkey-item {
  font-size: 10px !important;
  font-weight: 400 !important;
  color: rgba(0, 0, 0, 0.6) !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
}

/* Ghost text styling for disabled editors */
.ghost-text :deep(textarea) {
  color: rgba(0, 0, 0, 0.55) !important;
  font-style: italic !important;
  background-color: rgba(0, 0, 0, 0.02) !important;
}

.ghost-text :deep(.v-field__input) {
  color: rgba(0, 0, 0, 0.55) !important;
  font-style: italic !important;
}

/* Text formatting hotkeys box styling */
.text-formatting-box {
  position: relative;
  background-color: rgba(245, 245, 245, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 4px 12px;
  margin: 2px auto;
  width: fit-content;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.formatting-hotkey {
  font-family: 'Helvetica', 'Arial', sans-serif !important;
  font-size: 9px !important;
  font-weight: 500 !important;
  color: rgba(80, 80, 80, 0.9) !important;
  white-space: nowrap !important;
}

.formatting-hotkey strong {
  font-weight: 700 !important;
  color: rgba(60, 60, 60, 1) !important;
}

.hotkey-divider {
  height: 12px !important;
  opacity: 0.3 !important;
}

/* Auto-sizing Cue Toolbar inside Editor Content */
.editor-cues-toolbar {
  position: sticky !important;
  top: 48px !important; /* Position below main toolbar */
  z-index: 9 !important;
  width: 100% !important;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  padding: 6px 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cue-buttons-flex-container {
  display: flex;
  align-items: stretch;
  gap: 4px;
  width: 100%;
}

.insert-cue-label {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--v-theme-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-right: 8px;
  white-space: nowrap;
  min-width: fit-content;
}

.cue-btn-flex {
  flex: 1 !important; /* Auto-size to fit available space */
  min-width: 0 !important; /* Allow buttons to shrink */
  height: 48px !important;
  padding: 2px 4px !important;
  border-radius: 0 !important;
  color: white !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.2s ease !important;
}

.cue-btn-flex:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
}

.cue-btn-content-flex {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 1px;
}

.cue-btn-content-flex .cue-label {
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.3px !important;
  line-height: 1 !important;
}

.cue-btn-content-flex .hotkey-display {
  font-size: 0.6rem !important;
  opacity: 0.9 !important;
  line-height: 1 !important;
  font-weight: 500 !important;
}

.cue-btn-content-flex .v-icon {
  font-size: 16px !important;
}

/* Script Slug Field Styling */
.script-slug-container {
  border-bottom: 1px solid #e0e0e0;
  background-color: #fafafa;
}

.script-slug-field {
  max-width: 400px;
}

.script-slug-field :deep(.v-field__input) {
  font-family: 'Roboto Mono', monospace;
  font-size: 14px;
  font-weight: 500;
}

.script-slug-field :deep(.v-label) {
  font-weight: 600;
  color: var(--v-theme-primary);
}
</style>
