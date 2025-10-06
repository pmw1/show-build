<template>
  <div :class="['editor-panel', !showRundownPanel ? 'full-width' : '']">
    <!-- Flash Message for Cue Insertion -->
    <v-snackbar
      v-model="flashMessage.show"
      :timeout="500"
      location="center"
      :color="flashMessage.color"
      variant="elevated"
      class="cue-flash-message"
    >
      <div class="d-flex align-center">
        <v-icon class="mr-2">mdi-plus-circle</v-icon>
        <span class="font-weight-bold">{{ flashMessage.text }}</span>
      </div>
    </v-snackbar>

    <!-- Thick Cursor for Precise Insertion Point -->
    <div
      v-if="thickCursor.show"
      class="thick-cursor"
      :style="thickCursor.style"
    ></div>

    <v-card class="editor-card" flat>
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

          <!-- Autoformat Status -->
          <div class="autoformat-section d-flex flex-column align-center">
            <div class="autoformat-status text-caption text-medium-emphasis">
              <div class="text-center">
                <span>Autoformat</span>
                <div class="text-xs opacity-75">
                  {{ lastAutoformatTime ? formatTimestamp(lastAutoformatTime) : 'Not run' }}
                </div>
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
            class="save-all-btn"
            rounded="0"
            style="margin-top: -2px;"
          >
            <v-icon size="small" class="mr-1">{{ saveState?.buttonIcon || 'mdi-check-circle' }}</v-icon>
            Save All
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
            style="margin-top: -2px;"
          >
            <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
            Metadata
            <v-tooltip activator="parent" location="bottom">{{ showMetadataPanel ? 'Hide Metadata Panel' : 'Show Metadata Panel' }}</v-tooltip>
          </v-btn>

          <!-- Horizontal Divider -->
          <v-divider vertical class="mx-2"></v-divider>

          <!-- More Options Dropdown -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                size="small"
                color="grey"
                variant="outlined"
                class="more-options-btn px-3"
                rounded="0"
                style="margin-top: -2px;"
                v-bind="props"
              >
                <v-icon size="small" class="mr-1">mdi-dots-horizontal</v-icon>
                More Options
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="toggleScriptReading" :disabled="!isXttsConfigured">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2" :color="isReadingScript ? 'error' : 'primary'">{{ isReadingScript ? 'mdi-stop' : 'mdi-volume-high' }}</v-icon>
                  {{ isReadingScript ? 'Stop Reading' : 'Read Script Aloud' }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ isXttsConfigured ? 'Read with XTTS' : 'XTTS not configured' }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="requestNewEpisodeAssetID">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2">mdi-refresh</v-icon>
                  Request New Episode AssetID
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="showAssetIDInfo">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2">mdi-identifier</v-icon>
                  Show AssetID Info
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </v-toolbar>

      <!-- Editor Content Area -->
      <v-card-text class="pa-0 editor-content">

        <!-- Script Mode - Enhanced Visual Editor with Cue Cards -->
        <div v-if="editorMode === 'script'" class="d-flex flex-column script-mode-container">

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
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regenerate Cue AssetID</span>
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
            </div>

            <!-- Multi-Selection Actions -->
            <div v-if="multiSelectedSegments.size > 0" class="multi-selection-toolbar">
              <div class="selection-info">
                {{ multiSelectedSegments.size }} paragraph{{ multiSelectedSegments.size > 1 ? 's' : '' }} selected
              </div>
              <v-btn
                color="primary"
                variant="contained"
                size="small"
                @click="swapSelectedParagraphs"
                prepend-icon="mdi-swap-vertical"
              >
                Swap
              </v-btn>
              <v-btn
                color="error"
                variant="contained"
                size="small"
                @click="deleteMultipleSegments"
                prepend-icon="mdi-delete"
              >
                Delete Selected
              </v-btn>
              <v-btn
                variant="outlined"
                size="small"
                @click="clearMultiSelection"
              >
                Clear Selection
              </v-btn>
            </div>

            <!-- Enhanced Script Content with Visual Cue Cards -->
            <div v-if="useVisualScriptMode && !hasNoItem" class="visual-script-container">
              <div v-for="(segment, index) in scriptSegments" :key="`segment-${index}`" class="content-segment">
                <!-- Speaker Paragraph Segment -->
                <div v-if="segment.type === 'text'" class="text-segment">
                  <div
                    v-if="segment.needsParagraphTags"
                    class="speaker-paragraph"
                    :class="{
                      'selected': selectedSegmentIndex === index,
                      'multi-selected': multiSelectedSegments.has(index),
                      'blinking-swap': blinkingParagraphs.has(index)
                    }"
                    :style="multiSelectedSegments.has(index) ? {
                      'background-color': selectionBackgroundColor,
                      'border-left': `6px solid ${selectionColor}`,
                      'box-shadow': `0 0 0 2px ${selectionShadowColor}`
                    } : {}"
                    @click="handleParagraphClick(index, $event)"
                  >
                    <!-- Speaker Header -->
                    <div v-if="shouldShowSpeakerHeader(index, segment.speaker)" class="speaker-header" :style="getSpeakerHeaderStyle(segment.speaker)">
                      <div class="speaker-info">
                        <v-icon size="small" class="speaker-icon">mdi-account-voice</v-icon>
                        <span class="speaker-name">{{ getSpeakerDisplayName(segment.speaker) }}</span>
                      </div>
                      <div class="paragraph-actions">
                        <v-btn
                          size="small"
                          variant="text"
                          @click.stop="openSpeakerSelector(index)"
                          class="action-btn"
                        >
                          <v-icon size="small">mdi-account-switch</v-icon>
                          Change
                        </v-btn>
                        <v-btn
                          size="small"
                          variant="text"
                          @click.stop="deleteSegment(index)"
                          class="action-btn delete-btn"
                        >
                          <v-icon size="small">mdi-delete</v-icon>
                          Delete
                        </v-btn>
                      </div>
                    </div>

                    <!-- Paragraph Content -->
                    <div
                      class="paragraph-content"
                      :class="[
                        `seg-${index}`,
                        `speaker-bg-${segment.speaker}`,
                        {
                          'paragraph-focused': focusedParagraphIndex === index,
                          'paragraph-saved': savedParagraphIndex === index
                        }
                      ]"
                      @mouseenter="hoveredParagraphIndex = index"
                      @mouseleave="hoveredParagraphIndex = null"
                    >
                      <!-- Line Numbers Column -->
                      <div class="line-numbers-column" :ref="`lineNumbers-${index}`">
                        <div
                          v-for="lineNum in getLineCount(index)"
                          :key="lineNum"
                          class="line-number"
                        >
                          {{ getAbsoluteLineNumber(index, lineNum) }}
                        </div>
                      </div>

                      <v-textarea
                        :ref="`textareaRef-${index}`"
                        :model-value="getSegmentContent(index)"
                        @update:model-value="handleTextareaInput(index, $event)"
                        @keydown="handleTextareaKeydown(index, $event)"
                        @focus="handleParagraphFocus(index)"
                        @blur="handleParagraphBlur(index)"
                        variant="plain"
                        hide-details
                        class="speaker-textarea"
                        :class="`speaker-${segment.speaker}`"
                        :placeholder="`Enter ${getSpeakerDisplayName(segment.speaker)}'s dialogue here...`"
                        no-resize
                      ></v-textarea>

                      <!-- Delete Button (right middle) -->
                      <v-btn
                        v-if="hoveredParagraphIndex === index"
                        icon
                        size="small"
                        class="paragraph-delete-btn"
                        @click.stop="deleteSegment(index)"
                      >
                        <v-icon size="medium">mdi-close</v-icon>
                      </v-btn>

                      <!-- Add Paragraph Button (bottom center) -->
                      <v-btn
                        v-if="hoveredParagraphIndex === index"
                        icon
                        size="small"
                        class="paragraph-add-btn"
                        @click.stop="createNewParagraphAfter(index)"
                      >
                        <v-icon size="medium">mdi-plus</v-icon>
                      </v-btn>
                    </div>
                  </div>
                  <!-- Fallback for non-paragraph content -->
                  <v-textarea
                    v-else
                    :ref="`textarea-${index}`"
                    :model-value="getSegmentContent(index)"
                    @update:model-value="updateTextSegment(index, $event)"
                    @keydown="handleTextareaKeydown(index, $event)"
                    variant="plain"
                    hide-details
                    auto-grow
                    class="segment-textarea"
                            no-resize
                  ></v-textarea>
                </div>

                <!-- Cue Card Segment -->
                <div v-else-if="segment.type === 'cue'" class="cue-segment">
                  <ImageCueCard
                    v-if="segment.data.isImageType"
                    :cue-data="segment.data"
                    :selected="selectedCueIndex === index"
                    :order-number="extractOrderFromSlug(segment.data.slug)"
                    @select="selectCue(index)"
                    @edit="editCue(index, segment.data)"
                    @delete="deleteCue(index)"
                    @update-meta="handleMetaUpdate"
                  />
                  <PlaceholderCueCard
                    v-else
                    :cue-data="segment.data"
                    :selected="selectedCueIndex === index"
                    :order-number="extractOrderFromSlug(segment.data.slug)"
                    @select="selectCue(index)"
                    @edit="editCue(index, segment.data)"
                    @delete="deleteCue(index)"
                  />
                </div>
              </div>

            </div>

            <!-- Fluid typing area at bottom of visual content -->
            <div v-if="useVisualScriptMode && !hasNoItem" class="fluid-typing-area">
              <div class="typing-area" @click="focusTypingInput">
                <v-textarea
                  ref="typingInputRef"
                  v-model="typingBuffer"
                  @input="handleTypingInput"
                  @keydown="handleTypingKeydown"
                  variant="plain"
                  hide-details
                  auto-grow
                  class="typing-textarea"
                  placeholder="Continue writing..."
                  no-resize
                ></v-textarea>
              </div>
            </div>

            <!-- Fallback: Traditional Textarea -->
            <div v-else class="traditional-script-container">
              <v-textarea
                :model-value="hasNoItem ? '' : stripYamlFrontmatter(scriptContent)"
                @update:model-value="hasNoItem ? null : handleTraditionalScriptUpdate($event)"
                :placeholder="hasNoItem ? noItemPlaceholder : scriptPlaceholder"
                :disabled="hasNoItem"
                variant="plain"
                hide-details
                class="editor-textarea script-textarea script-textarea-with-header"
                :class="{ 'ghost-text': hasNoItem }"
                no-resize
              ></v-textarea>
            </div>
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
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regenerate Cue AssetID</span>
          </div>

          <v-textarea
            :model-value="scratchContent"
            @update:model-value="$emit('update:scratchContent', $event)"
            :placeholder="scratchPlaceholder"
            variant="plain"
            hide-details
            class="editor-textarea scratch-mode flex-grow-1"
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
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regenerate Cue AssetID</span>
          </div>

          <v-textarea
            v-model="rawScriptContent"
            :placeholder="hasNoItem ? noItemPlaceholder : 'Edit the script content in markdown format...'"
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
    :current-episode="currentEpisode"
    :edit-data="editingCueData"
    @submit="handleImgCueSubmit"
    @update:show="handleImgModalClose"
  />

  <!-- Delete IMG Cue Confirmation Modal -->
  <DeleteImgCueModal
    v-model:show="showDeleteImgModal"
    :cue-slug="deletingCueData?.slug || ''"
    :image-path="deletingCueData?.rawData?.mediaurl || ''"
    @delete-with-assets="handleDeleteWithAssets"
    @delete-preserve-assets="handleDeletePreserveAssets"
  />

  <!-- Speaker Selector Modal -->
  <SpeakerSelectorModal
    v-model:show="showSpeakerSelector"
    :current-speaker="currentSegmentSpeaker"
    @speaker-selected="handleSpeakerChange"
  />

  <!-- Swap Error Dialog -->
  <v-dialog v-model="showSwapErrorDialog" max-width="400">
    <v-card>
      <v-card-title class="text-h5 bg-error text-white">
        Swap Error
      </v-card-title>
      <v-card-text class="pt-4">
        {{ swapErrorMessage }}
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="text" @click="showSwapErrorDialog = false">
          OK
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Cue Placement Overlay -->
  <CuePlacementOverlay
    v-model:show="showCuePlacement"
    :cue-type="pendingCueType"
    @place-cue="handleCuePlacement"
    @cancel="cancelCuePlacement"
  />
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap.js';
import ImgCueModal from './modals/ImgCueModal.vue';
import DeleteImgCueModal from './modals/DeleteImgCueModal.vue';
import ImageCueCard from './cards/ImageCueCard.vue';
import PlaceholderCueCard from './cards/PlaceholderCueCard.vue';
import SpeakerSelectorModal from './modals/SpeakerSelectorModal.vue';
import CuePlacementOverlay from './CuePlacementOverlay.vue';
import CueParser from '../../utils/cueParser.js';
import { useXtts } from '../../composables/useXtts.js';

export default {
  name: 'EditorPanel',
  components: {
    ImgCueModal,
    DeleteImgCueModal,
    ImageCueCard,
    PlaceholderCueCard,
    SpeakerSelectorModal,
    CuePlacementOverlay
  },
  data() {
    return {
      showImgModal: false,
      showDeleteImgModal: false,
      editingCueData: null,
      deletingCueData: null,
      deletingCueIndex: null,
      selectedCueIndex: null,
      selectedSegmentIndex: null,
      multiSelectedSegments: new Set(),
      showSpeakerSelector: false,
      currentSegmentSpeaker: 'josh',
      editingSpeakerSegmentIndex: null,
      showCuePlacement: false,
      showSwapErrorDialog: false,
      swapErrorMessage: '',
      blinkingParagraphs: new Set(), // Track paragraphs that are blinking after swap
      pendingCueType: null,
      pendingPlacement: null,
      pendingCueData: null, // Store IMG cue data for post-modal placement
      useVisualScriptMode: true, // Toggle for visual cue cards vs traditional text - RE-ENABLED, fixing visibility issue
      hoveredParagraphIndex: null, // Track which paragraph is being hovered
      focusedParagraphIndex: null, // Track which paragraph has focus
      savedParagraphIndex: null, // Track paragraph that just saved (for blue flash)
      errorParagraphIndex: null, // Track paragraph with save error (for red flash)
      paragraphEditStates: {}, // Track if paragraph has been edited before (for re-edit detection)
      hasLocalUnsavedChanges: false, // Track if script content has unsaved changes
      typingBuffer: '', // Buffer for auto-expanding text input
      autoformatTimer: null, // Timer for periodic autoformat
      autoformatDebounceTimer: null, // Debounce timer for content changes
      segmentUpdateTimer: null, // Timer for debouncing segment updates
      lastAutoformatTime: null, // Timestamp of last autoformat run
      altKeyPressed: false, // Manual ALT key tracking for better browser compatibility
      isActivelyTyping: false, // Flag to prevent autoformat during typing
      lastEnterState: {}, // Track Enter key state per segment for double Enter detection
      segmentEditBuffer: {}, // Buffer for segment edits to prevent reactivity race conditions
      updateDebounceTimers: {}, // Debounce timers for each segment to prevent rapid updates
      // Universal cue insertion workflow
      pendingInsertionPoint: null, // Store cursor position for insertion (script mode)
      pendingCursorPosition: null, // Store cursor position for insertion (code mode)
      flashMessage: {
        show: false,
        text: '',
        color: ''
      },
      thickCursor: {
        show: false,
        style: {}
      },
      cursorPositionHighlight: null, // Reference to cursor position highlight element
      cursorPositionTimeout: null, // Timeout reference for cursor position highlight
      highlightedElement: null, // Currently highlighted element for insertion preview
      // XTTS reading state
      isReadingScript: false, // Whether script is currently being read
      currentReadingIndex: 0, // Current paragraph index being read
      audioElement: null, // Audio element for playback
      xttsInstance: null, // XTTS composable instance
      segmentLineCounts: {} // Cache of line counts per segment for reactivity
    }
  },
  mounted() {
    console.log('EditorPanel mounted with metadata:', this.currentItemMetadata);

    // Auto-resize all textareas on mount if scriptSegments exist
    // Use multiple attempts with delays to ensure content is fully rendered
    this.$nextTick(() => {
      if (this.scriptSegments && this.scriptSegments.length > 0) {
        // First attempt immediately
        this.scriptSegments.forEach((segment, index) => {
          if (segment.type === 'text' && segment.needsParagraphTags) {
            this.autoResizeTextarea(index);
          }
        });

        // Second attempt after 100ms to catch late renders
        setTimeout(() => {
          this.scriptSegments.forEach((segment, index) => {
            if (segment.type === 'text' && segment.needsParagraphTags) {
              this.autoResizeTextarea(index);
            }
          });
        }, 100);

        // Third attempt after 300ms to ensure everything is settled
        setTimeout(() => {
          this.scriptSegments.forEach((segment, index) => {
            if (segment.type === 'text' && segment.needsParagraphTags) {
              this.autoResizeTextarea(index);
            }
          });
        }, 300);
      }
    });

    // Initialize XTTS
    try {
      this.xttsInstance = useXtts();
      if (this.xttsInstance && !this.xttsInstance.xttsConfig?.value?.enabled) {
        this.xttsInstance.loadXttsConfig().catch(err => {
          console.error('Failed to load XTTS config:', err);
        });
      }
    } catch (error) {
      console.error('Failed to initialize XTTS:', error);
    }

    // Start periodic autoformat (every 30 seconds)
    this.startAutoformatTimer();

    // Add global hotkey listeners
    console.log('🎪 Adding global hotkey listeners');
    document.addEventListener('keydown', this.handleGlobalKeydown);
    document.addEventListener('keyup', this.handleGlobalKeyup);

    // Add keyboard listener for cursor character cleanup
    document.addEventListener('keydown', this.handleCursorCharacterKeydown);
  },
  unmounted() {
    // Clean up event listeners
    document.removeEventListener('keydown', this.handleGlobalKeydown);
    document.removeEventListener('keyup', this.handleGlobalKeyup);
    document.removeEventListener('keydown', this.handleCursorCharacterKeydown);
    if (this.autoformatTimer) {
      clearInterval(this.autoformatTimer);
    }

    // Clean up audio element
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.removeEventListener('ended', this.handleAudioEnd);
      this.audioElement.removeEventListener('error', this.handleAudioError);
      if (this.audioElement.src) {
        URL.revokeObjectURL(this.audioElement.src);
      }
      this.audioElement = null;
    }
  },

  beforeUnmount() {
    // Clean up timers
    this.stopAutoformatTimer();
    this.clearAutoformatDebounce();
  },
  watch: {
    currentItemMetadata: {
      handler(newVal) {
        console.log('EditorPanel currentItemMetadata changed:', newVal);
      },
      deep: true,
      immediate: true
    },

    // Watch for empty content in Script Mode and initialize with first paragraph
    scriptContent: {
      handler(newVal, oldVal) {
        console.log('🔔 scriptContent watcher fired:', {
          newLength: newVal?.length,
          oldLength: oldVal?.length,
          editorMode: this.editorMode,
          useVisualScriptMode: this.useVisualScriptMode
        });

        if (this.editorMode === 'script' && this.useVisualScriptMode) {
          const contentWithoutFrontmatter = this.stripYamlFrontmatter(newVal || '');

          // Check if content has no actual script content (only markdown headings or empty)
          const hasNoScriptContent = !contentWithoutFrontmatter ||
                                     contentWithoutFrontmatter.trim() === '' ||
                                     !contentWithoutFrontmatter.includes('<p');

          console.log('  hasNoScriptContent:', hasNoScriptContent);

          if (hasNoScriptContent) {
            this.$nextTick(() => {
              this.createInitialParagraph();
            });
          }
        }
      },
      immediate: true
    },

    // Watch scriptSegments to focus textarea after initial paragraph is rendered
    scriptSegments: {
      handler(newSegments, oldSegments) {
        console.log('📊 scriptSegments watcher fired:', {
          oldLength: oldSegments?.length,
          newLength: newSegments?.length,
          newSegments
        });

        // Auto-resize all textareas when segments change
        this.$nextTick(() => {
          if (newSegments && newSegments.length > 0) {
            newSegments.forEach((segment, index) => {
              if (segment.type === 'text' && segment.needsParagraphTags) {
                this.autoResizeTextarea(index);
              }
            });
          }
        });

        // REMOVED: Auto-focus behavior
        // Navigation mode now requires explicit Enter key to focus
        // User can navigate with arrow keys without being pulled into editing mode

        // Auto-resize all textareas after segments change
        this.$nextTick(() => {
          if (newSegments && newSegments.length > 0) {
            newSegments.forEach((segment, index) => {
              if (segment.type === 'text') {
                this.autoResizeTextarea(index);

                // Mark paragraphs with content as "already edited" so they show yellow highlight on first click
                if (segment.content && segment.content.trim() !== '') {
                  this.paragraphEditStates[index] = true;
                }
              }
            });
          }
        });
      }
    }
  },
  emits: [
    'toggle-rundown',
    'toggle-metadata-panel',
    'update:editorMode',
    'show-asset-browser',
    'save',
    'save-all',
    'update:scriptContent',
    'update:scratchContent',
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
    'show-live-modal',
    'toggleRundownPanel',
    'showAssetBrowserModal',
    'showTemplateManagerModal',
    'update:item'
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
    item: {
      type: Object,
      default: null
    },
    currentItemMetadata: {
      type: Object,
      default: () => ({})
    },
    currentEpisode: {
      type: String,
      default: ''
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
    // Single source of truth - raw script content
    rawScriptContent: {
      get() {
        return this.scriptContent || '';
      },
      set(value) {
        this.$emit('update:scriptContent', value);
      }
    },

    // Parse content into segments ONLY for Script mode display (no reactive loops)
    scriptSegments() {
      console.log('🔄 scriptSegments computed property called');
      console.log('  rawScriptContent length:', this.rawScriptContent?.length);
      console.log('  editorMode:', this.editorMode);
      console.log('  useVisualScriptMode:', this.useVisualScriptMode);

      if (!this.rawScriptContent || this.editorMode !== 'script' || !this.useVisualScriptMode) {
        console.log('  → Returning empty array (early exit)');
        return [];
      }

      try {
        // Strip YAML frontmatter for parsing
        const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);
        console.log('  contentWithoutFrontmatter:', contentWithoutFrontmatter?.substring(0, 100));

        // If content is empty or only whitespace, return empty paragraph segment
        // (initialization will be handled by mounted/watch)
        if (!contentWithoutFrontmatter || contentWithoutFrontmatter.trim() === '') {
          console.log('  → Returning single empty text segment');
          return [{
            type: 'text',
            content: '',
            speaker: 'josh',
            needsParagraphTags: true,
            segmentIndex: 0
          }];
        }

        const segments = CueParser.parseContent(contentWithoutFrontmatter);

        return segments.map((segment, index) => {
          if (segment.type === 'cue') {
            // Format cue data for card display
            const formattedCueData = CueParser.formatForCard(segment.data);
            return {
              type: 'cue',
              data: formattedCueData,
              segmentIndex: index
            };
          }
          return {
            ...segment,
            segmentIndex: index
          };
        });
      } catch (error) {
        console.error('Error parsing script segments:', error);
        // Fallback: treat as single text segment
        const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);
        return [{
          type: 'text',
          content: contentWithoutFrontmatter,
          speaker: 'josh',
          needsParagraphTags: true,
          segmentIndex: 0
        }];
      }
    },

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
    },

    // Get the selection color from theme configuration
    selectionColor() {
      const colorName = getColorValue('selection');
      return resolveVuetifyColor(colorName);
    },

    // Get selection color with opacity for background
    selectionBackgroundColor() {
      const hexColor = this.selectionColor;
      // Convert hex to RGB and add 25% opacity
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, 0.25)`;
    },

    // Get selection color with opacity for shadow
    selectionShadowColor() {
      const hexColor = this.selectionColor;
      // Convert hex to RGB and add 20% opacity
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, 0.2)`;
    },

    // Check if XTTS is properly configured
    isXttsConfigured() {
      return this.xttsInstance?.isXttsAvailable() || false;
    },

    // Get text-only paragraphs for reading
    readableParagraphs() {
      if (!this.scriptSegments || this.scriptSegments.length === 0) return [];
      return this.scriptSegments
        .filter(segment => segment.type === 'text' && segment.content && segment.content.trim() !== '')
        .map(segment => ({
          index: segment.segmentIndex,
          content: segment.content,
          speaker: segment.speaker
        }));
    },

  },
  methods: {
    // Handle textarea input - update content and auto-resize
    handleTextareaInput(index, value) {
      console.log(`✏️ handleTextareaInput called for index ${index}, value length: ${value?.length}`);
      this.updateTextSegment(index, value);
      this.autoResizeTextarea(index);
    },

    // Custom auto-resize for textareas (Vuetify auto-grow is broken)
    autoResizeTextarea(index) {
      console.log(`📏 autoResizeTextarea called for index ${index}`);
      this.$nextTick(() => {
        const textareaRefArray = this.$refs[`textareaRef-${index}`];
        console.log(`📏 textareaRef for ${index}:`, textareaRefArray);

        // Template refs in v-for return arrays, so get the first element
        const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;
        console.log(`📏 textareaRef component for ${index}:`, textareaRef);

        if (textareaRef && textareaRef.$el) {
          // Get the actual textarea element (Vuetify wraps it)
          const textarea = textareaRef.$el.querySelector('textarea');
          console.log(`📏 textarea element for ${index}:`, textarea);

          if (textarea) {
            const oldHeight = textarea.style.height;

            // Force overflow hidden and remove any height constraints
            textarea.style.overflow = 'hidden';
            textarea.style.minHeight = '0';
            textarea.style.maxHeight = 'none';

            // Reset to 1px to force recalculation (auto doesn't always work)
            textarea.style.height = '1px';

            // Calculate the new height based on scrollHeight
            const scrollHeight = textarea.scrollHeight;
            const newHeight = scrollHeight + 'px';

            // Apply the new height directly
            textarea.style.height = newHeight;

            console.log(`📏 Auto-resized textarea ${index} from ${oldHeight} to ${newHeight} (scrollHeight: ${scrollHeight}px)`);

            // Update line count after resize
            this.$nextTick(() => {
              this.updateLineCount(index);
            });
          } else {
            console.warn(`📏 No textarea element found for index ${index}`);
          }
        } else {
          console.warn(`📏 No textareaRef component found for index ${index}`);
        }
      });
    },

    // Calculate number of VISUAL lines in a textarea (based on rendered height)
    getLineCount(index) {
      // Return cached value if available
      if (this.segmentLineCounts[index]) {
        return this.segmentLineCounts[index];
      }

      const content = this.getSegmentContent(index);
      if (!content || content.trim() === '') return 1;

      // Fallback: count newlines
      const newlineCount = (content.match(/\n/g) || []).length;
      return newlineCount + 1;
    },

    // Update line count for a segment (called after resize)
    updateLineCount(index) {
      const textareaRefArray = this.$refs[`textareaRef-${index}`];
      const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;

      if (textareaRef && textareaRef.$el) {
        const textarea = textareaRef.$el.querySelector('textarea');
        if (textarea) {
          // Calculate line count based on actual height
          const lineHeight = 24; // 16px font * 1.5 line-height
          const totalHeight = textarea.scrollHeight;
          const lineCount = Math.max(1, Math.round(totalHeight / lineHeight));

          // Update reactive cache (Vue 3 way - direct assignment)
          this.segmentLineCounts[index] = lineCount;
        }
      }
    },

    // Calculate absolute line number across all paragraphs
    getAbsoluteLineNumber(segmentIndex, relativeLineNum) {
      let absoluteLine = 0;

      // Sum up all lines from previous segments
      for (let i = 0; i < segmentIndex; i++) {
        if (this.scriptSegments[i] && this.scriptSegments[i].type === 'text' && this.scriptSegments[i].needsParagraphTags) {
          absoluteLine += this.getLineCount(i);
        }
      }

      // Add the current relative line number
      return absoluteLine + relativeLineNum;
    },

    // Strip YAML frontmatter from content for visual display
    stripYamlFrontmatter(content) {
      if (!content) return '';

      // Check if content starts with YAML frontmatter (---)
      if (content.trim().startsWith('---')) {
        const lines = content.split('\n');
        let frontmatterEnd = -1;
        let bodyStart = -1;

        // Find the closing --- (skip the first line which is the opening ---)
        for (let i = 1; i < lines.length; i++) {
          if (lines[i].trim() === '---') {
            frontmatterEnd = i;
            bodyStart = i + 1;
            break;
          }
        }

        // If we found the closing ---, look for actual body content
        if (frontmatterEnd > 0 && bodyStart < lines.length) {
          // Skip empty lines and find the first real content
          for (let i = bodyStart; i < lines.length; i++) {
            const line = lines[i].trim();
            // If this line looks like YAML (key: value), skip it - it's malformed frontmatter
            if (line && line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
              console.warn(`🔧 Stripping malformed YAML line: "${line}"`);
              continue;
            }
            // If this line doesn't look like YAML, this is where body content starts
            if (line && !line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
              return lines.slice(i).join('\n').trim();
            }
            // If it's an empty line, include it but keep looking
            if (!line) {
              bodyStart = i;
            }
          }

          // If we didn't find any body content, return empty string
          return '';
        }
      }

      // If no frontmatter found, return original content
      return content;
    },

    // Extract YAML frontmatter from content
    extractYamlFrontmatter(content) {
      if (!content) return '';

      if (content.trim().startsWith('---')) {
        const lines = content.split('\n');
        let frontmatterEnd = -1;

        // Find the closing --- (skip the first line which is the opening ---)
        for (let i = 1; i < lines.length; i++) {
          if (lines[i].trim() === '---') {
            frontmatterEnd = i;
            break;
          }
        }

        // If we found the closing ---, return the frontmatter including delimiters
        if (frontmatterEnd > 0) {
          return lines.slice(0, frontmatterEnd + 1).join('\n');
        }
      }

      return '';
    },

    // Generate current frontmatter from metadata
    generateCurrentFrontmatter() {
      if (!this.currentItemMetadata) return '';

      const metadata = this.currentItemMetadata;

      // DEBUGGING: Log metadata to identify corruption
      console.warn('🔍 DEBUGGING generateCurrentFrontmatter metadata:', JSON.stringify(metadata, null, 2));

      let frontmatter = '---\n';

      // Add all available metadata fields with proper formatting
      if (metadata.AssetID) frontmatter += `id: '${metadata.AssetID}'\n`;
      if (metadata.slug) frontmatter += `slug: "${metadata.slug}"\n`;  // FIXED: Added quotes
      if (metadata.type) frontmatter += `type: ${metadata.type}\n`;
      if (metadata.order !== undefined) frontmatter += `order: ${metadata.order}\n`;
      if (metadata.index !== undefined) frontmatter += `index: ${metadata.index}\n`;
      if (metadata.duration) frontmatter += `duration: "${metadata.duration}"\n`;
      if (metadata.status) frontmatter += `status: ${metadata.status}\n`;
      if (metadata.title) frontmatter += `title: "${metadata.title}"\n`;

      frontmatter += '---';

      console.warn('🔍 Generated frontmatter:', frontmatter);
      return frontmatter;
    },

    // Reconstruct script content while preserving and updating frontmatter
    reconstructScriptContentWithFrontmatter(segments) {
      const bodyContent = CueParser.reconstructContent(segments);
      const currentFrontmatter = this.generateCurrentFrontmatter();

      if (currentFrontmatter) {
        return currentFrontmatter + '\n' + bodyContent;
      }

      return bodyContent;
    },

    // Comprehensive YAML frontmatter validation and synchronization
    validateAndSyncYamlFrontmatter() {
      if (!this.scriptContent || !this.currentItemMetadata) {
        return false; // No content or metadata to validate
      }

      try {
        // DEBUGGING: Log metadata to detect contamination
        if (this.currentItemMetadata.AssetID) {
          console.log(`🔍 YAML Validation - Current AssetID: ${this.currentItemMetadata.AssetID}, Title: ${this.currentItemMetadata.title}, Type: ${this.currentItemMetadata.type}, Order: ${this.currentItemMetadata.order}`);
        }

        // Check for multiple frontmatter blocks or malformed YAML first
        const multipleBlocksInfo = this.detectMultipleFrontmatterBlocks(this.scriptContent);
        if (multipleBlocksInfo.isMalformed) {
          if (multipleBlocksInfo.hasMultiple) {
            console.warn(`🚨 MULTIPLE FRONTMATTER BLOCKS DETECTED: ${multipleBlocksInfo.blockCount} blocks found`);
          }
          if (multipleBlocksInfo.hasYamlAfterClosing) {
            console.warn('🚨 MALFORMED YAML: Found YAML content after frontmatter closing ---');
          }
          console.warn('This indicates data contamination - will clean up automatically');

          // Force update to clean up malformed YAML
          const bodyContent = this.stripYamlFrontmatter(this.scriptContent);
          const correctFrontmatter = this.generateCurrentFrontmatter();
          const correctedContent = correctFrontmatter + '\n' + bodyContent;

          console.log('🧹 Cleaning up malformed YAML frontmatter');
          this.$emit('update:scriptContent', correctedContent);
          return true; // Content was updated
        }

        // Extract current frontmatter from script content
        const existingFrontmatter = this.extractYamlFrontmatter(this.scriptContent);
        const bodyContent = this.stripYamlFrontmatter(this.scriptContent);

        // Generate what the frontmatter should be based on current metadata
        const correctFrontmatter = this.generateCurrentFrontmatter();

        // Check if frontmatter needs to be added or updated
        let needsUpdate = false;
        let updateReason = '';

        if (!existingFrontmatter && correctFrontmatter) {
          // Missing frontmatter entirely
          needsUpdate = true;
          updateReason = 'Missing YAML frontmatter';
        } else if (existingFrontmatter !== correctFrontmatter) {
          // Existing frontmatter doesn't match current metadata
          needsUpdate = true;
          updateReason = 'YAML frontmatter out of sync with metadata';

          // Additional validation: check if existing YAML is malformed
          if (existingFrontmatter && !this.isValidYaml(existingFrontmatter)) {
            updateReason = 'Invalid YAML frontmatter detected';
          }
        }

        if (needsUpdate) {
          console.log(`🔧 Autoformat: ${updateReason}`);

          // Reconstruct content with correct frontmatter
          const correctedContent = correctFrontmatter + '\n' + bodyContent;

          // Update the script content
          this.$emit('update:scriptContent', correctedContent);

          return true; // Indicate that content was updated
        }

        return false; // No updates needed

      } catch (error) {
        console.error('Error validating YAML frontmatter:', error);
        return false;
      }
    },

    // Enhanced YAML validation - detects multiple frontmatter blocks
    isValidYaml(yamlString) {
      try {
        if (!yamlString.includes('---')) return false;

        const lines = yamlString.split('\n');
        if (lines[0].trim() !== '---') return false;

        let foundClosing = false;
        let frontmatterBlocks = 0;

        for (let i = 0; i < lines.length; i++) {
          if (lines[i].trim() === '---') {
            frontmatterBlocks++;

            // If we find more than 2 --- markers, we have multiple frontmatter blocks
            if (frontmatterBlocks > 2) {
              console.warn('🚨 Multiple frontmatter blocks detected - this indicates data contamination');
              return false; // Invalid due to multiple blocks
            }

            if (frontmatterBlocks === 2) {
              foundClosing = true;
              break;
            }
          } else if (frontmatterBlocks === 1) {
            // We're inside the frontmatter block
            const line = lines[i].trim();
            if (line && !line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
              return false; // Invalid YAML syntax
            }
          }
        }

        return foundClosing && frontmatterBlocks === 2;
      } catch (error) {
        return false;
      }
    },

    // Detect and clean multiple frontmatter blocks or malformed YAML
    detectMultipleFrontmatterBlocks(content) {
      if (!content) return { hasMultiple: false, blockCount: 0, isMalformed: false };

      const lines = content.split('\n');
      let dashCount = 0;
      const blockStarts = [];
      let hasYamlAfterClosing = false;

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].trim() === '---') {
          dashCount++;
          if (dashCount % 2 === 1) { // Odd count = start of block
            blockStarts.push(i);
          }
        } else if (dashCount >= 2) {
          // We're after a completed frontmatter block - check for more YAML
          const line = lines[i].trim();
          if (line && line.match(/^[a-zA-Z_][a-zA-Z0-9_]*:\s*.+$/)) {
            hasYamlAfterClosing = true;
            console.warn(`🚨 MALFORMED YAML: Found YAML after closing --- on line ${i + 1}: "${line}"`);
            break;
          }
        }
      }

      const frontmatterBlocks = Math.floor(dashCount / 2);
      const isMalformed = hasYamlAfterClosing || frontmatterBlocks > 1;

      return {
        hasMultiple: frontmatterBlocks > 1,
        blockCount: frontmatterBlocks,
        blockStarts: blockStarts,
        isMalformed: isMalformed,
        hasYamlAfterClosing: hasYamlAfterClosing
      };
    },

    updateMetadata(field, value) {
      this.$emit('metadata-change', { field, value })
    },

    // Determine if speaker header should be shown
    shouldShowSpeakerHeader(index, speaker) {
      // Only show header if:
      // 1.) It is the first paragraph of a segment, OR
      // 2.) The speaker changes with this <p>

      // Show header if it's the first segment
      if (index === 0) {
        return true;
      }

      // Show header if previous segment has different speaker
      const previousSegment = this.scriptSegments[index - 1];

      // If previous segment is a cue, this is first paragraph after cue (condition 1)
      if (previousSegment && previousSegment.type === 'cue') {
        return true;
      }

      // If previous segment is text with different speaker (condition 2)
      if (previousSegment && previousSegment.type === 'text' && previousSegment.speaker !== speaker) {
        return true;
      }

      return false;
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
    async insertCue(cueType) {
      console.log('🎬 insertCue called with:', cueType);
      console.log('🎬 Current editorMode:', this.editorMode);

      // CODE MODE: Simpler workflow - insert at cursor position
      if (this.editorMode === 'code') {
        console.log('📝 Code mode detected - using cursor-based insertion');

        // Store cursor position from code textarea
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Stored cursor position:', this.pendingCursorPosition);
        }

        this.pendingCueType = cueType;

        // Show modal immediately for code mode
        if (cueType === 'IMG') {
          this.showImgModal = true;
          return;
        }

        if (cueType === 'GFX') {
          this.$emit('show-gfx-modal');
          return;
        }

        if (cueType === 'FSQ') {
          this.$emit('show-fsq-modal');
          return;
        }

        if (cueType === 'SOT') {
          this.$emit('show-sot-modal');
          return;
        }

        if (cueType === 'VO') {
          this.$emit('show-vo-modal');
          return;
        }

        if (cueType === 'NAT') {
          this.$emit('show-nat-modal');
          return;
        }

        if (cueType === 'PKG') {
          this.$emit('show-pkg-modal');
          return;
        }

        // Fallback for other cue types
        const cueText = `**[${cueType}: ]**`;
        this.insertCueAtCursor(cueText);
        return;
      }

      // SCRIPT MODE: Full workflow with placement overlay
      console.log('📄 Script mode detected - using placement overlay workflow');

      // Special handling for SOT - skip pre-modal highlighting, show modal immediately
      if (cueType === 'SOT') {
        console.log('🎯 SOT detected - opening modal immediately (placement overlay will activate AFTER modal closes)');
        this.pendingCueType = cueType;
        this.$emit('show-sot-modal');
        console.log('🎬 SOT modal opened - placement overlay will activate when modal closes');
        return;
      }

      // For other cue types: Show placement overlay with flash animation before modal
      // Step 1: Detect segment ID
      console.log('🎯 Step 1: Detecting segment ID...');
      const insertionPoint = this.detectAndHighlightCursorPosition(cueType);
      console.log('🎯 Segment detected:', insertionPoint?.segmentId);

      // Step 2: Show placement overlay with flash animation (preview of planned insertion)
      console.log('🎯 Step 2: Showing placement overlay preview with flash animation');
      this.pendingCueType = cueType;
      this.pendingInsertionPoint = insertionPoint;
      this.showCuePlacement = true;

      // Wait for flash animation to complete (5 flashes * 100ms * 2 = 1000ms)
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Hide placement overlay after preview (for non-SOT cues)
      this.showCuePlacement = false;
      console.log('🎯 Placement overlay preview complete');

      // Step 3: Show flash message "Insert {CUE_TYPE} CUE" for 500ms
      console.log('🎯 Step 3: Showing flash message');
      this.showFlashMessage(cueType);

      // Wait for flash message to complete (800ms total duration)
      await new Promise(resolve => setTimeout(resolve, 800));
      console.log('🎯 Flash message complete');

      // Step 4: Open modal
      console.log('🎯 Step 4: Opening modal');
      if (cueType === 'IMG') {
        this.showImgModal = true;
        console.log('🎬 IMG modal opened');
        return;
      }

      if (cueType === 'FSQ') {
        // Set pending cue type for placement workflow
        this.pendingCueType = 'FSQ';
        this.$emit('show-fsq-modal');
        console.log('🎬 FSQ modal opened');
        console.log('📄 Set pendingCueType to FSQ for placement overlay');
        return;
      }

      if (cueType === 'GFX') {
        this.$emit('show-gfx-modal');
        console.log('🎬 GFX modal opened');
        return;
      }

      if (cueType === 'VO') {
        this.$emit('show-vo-modal');
        console.log('🎬 VO modal opened');
        return;
      }

      if (cueType === 'NAT') {
        this.$emit('show-nat-modal');
        console.log('🎬 NAT modal opened');
        return;
      }

      if (cueType === 'PKG') {
        this.$emit('show-pkg-modal');
        console.log('🎬 PKG modal opened');
        return;
      }

      // For other cue types, show placement overlay for final selection
      this.showCuePlacement = true;
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

    // Enhanced slug normalization for media filenames
    normalizeSlugForMedia(slug) {
      return slug
        .toLowerCase() // 1. Convert to lowercase
        .replace(/[^\w\s-]/g, '') // 2. Remove all punctuation except spaces and hyphens
        .replace(/\s+/g, '-') // 3. Replace spaces with dashes
        .replace(/-+/g, '-') // Replace multiple dashes with single dash
        .replace(/^-|-$/g, '') // Remove leading/trailing dashes
    },

    // Check if slug already exists in current episode's cues
    isSlugDuplicate(slug) {
      if (!this.scriptContent) return false;

      // Extract all existing slugs from cue blocks
      const slugPattern = /\[Slug:\s*([^\]]+)\]/gi;
      const matches = this.scriptContent.matchAll(slugPattern);

      const existingSlugs = [];
      for (const match of matches) {
        existingSlugs.push(match[1].trim().toLowerCase());
      }

      console.log('🔍 Existing slugs in episode:', existingSlugs);
      console.log('🔍 Checking slug:', slug.toLowerCase());

      return existingSlugs.includes(slug.toLowerCase());
    },

    // Get file extension from file object
    getFileExtension(file) {
      if (file.name) {
        const lastDot = file.name.lastIndexOf('.');
        return lastDot !== -1 ? file.name.slice(lastDot + 1).toLowerCase() : 'jpg';
      }
      // Fallback to MIME type
      const mimeType = file.type || 'image/jpeg';
      return mimeType.split('/')[1] || 'jpg';
    },

    // Handle IMG cue submission from modal
    async handleImgCueSubmit(imgCueData) {
      console.error('🚨🚨🚨 handleImgCueSubmit CALLED!!! 🚨🚨🚨');
      console.error('imgCueData:', imgCueData);
      try {
        console.log('🎬 Starting IMG cue submission workflow');
        console.log('🔍 Current item metadata:', this.currentItemMetadata);
        console.log('🔍 Current item AssetID:', this.currentItemMetadata?.AssetID);

        // Get parent AssetID from current rundown item
        let parentAssetId = this.currentItemMetadata?.AssetID;

        if (!parentAssetId) {
          console.warn('⚠️ No AssetID in currentItemMetadata, checking rundown items...');
          // Try to get from the current episode's rundown items
          if (this.currentItemId && this.rundownItems) {
            const currentItem = this.rundownItems.find(item => item.id === this.currentItemId);
            parentAssetId = currentItem?.AssetID || currentItem?.asset_id;
            console.log('🔍 Found AssetID from rundown item:', parentAssetId);
          }
        }

        if (!parentAssetId) {
          throw new Error('Cannot create IMG cue: No parent rundown item AssetID available. Please select a rundown item first.');
        }

        console.log('✅ Using parent AssetID:', parentAssetId);

        // Request AssetID from server using correct endpoint
        const assetIdResponse = await fetch('/newAssetID', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          },
          body: JSON.stringify({
            asset_type: 'cue',
            cue_type: 'IMG',
            slug: imgCueData.slug,
            parent_asset_id: parentAssetId
          })
        });

        if (!assetIdResponse.ok) {
          throw new Error(`Failed to generate AssetID: ${assetIdResponse.status} ${assetIdResponse.statusText}`);
        }

        const assetIdData = await assetIdResponse.json();
        const assetId = assetIdData.asset_id;
        console.log('🎬 AssetID generation SUCCESS:', assetId);

        // Enhanced image file processing with episode-specific path
        // Slug for cue block: lowercase + remove punctuation, keep spaces
        const cueBlockSlug = imgCueData.slug
          .toLowerCase()
          .replace(/[^a-z0-9\s]/g, '')
          .trim();

        // Check for duplicate slugs in current episode
        if (this.isSlugDuplicate(cueBlockSlug)) {
          throw new Error(`Slug "${cueBlockSlug}" already exists in this episode. Please use a unique slug.`);
        }

        // Slug for filename: lowercase + hyphens for spaces
        const filenameSlug = this.normalizeSlugForMedia(imgCueData.slug);
        const fileExtension = this.getFileExtension(imgCueData.imageFile);
        const newFilename = `${filenameSlug}.${fileExtension}`;

        // Upload and relocate image to episode-specific location
        const formData = new FormData();
        formData.append('file', imgCueData.imageFile);
        formData.append('episode', this.currentEpisode || '0243');
        formData.append('filename', newFilename);

        const uploadResponse = await fetch('/api/upload/image', {
          method: 'POST',
          body: formData
        });

        if (!uploadResponse.ok) {
          throw new Error('Failed to upload and relocate image');
        }

        await uploadResponse.json();
        // Episode-specific MediaURL path
        const episodeSpecificMediaUrl = `episodes/${this.currentEpisode || '0243'}/assets/images/${newFilename}`;

        // Generate the IMG cue block with episode-specific MediaURL
        const imgCueBlock = `<!-- Begin Cue -->
[Type: IMG]
[AssetID: ${assetId}]
[Slug: ${cueBlockSlug}]
[Description: ${imgCueData.description || ''}]
[Credit: ${imgCueData.credit || ''}]
[Caption: ${imgCueData.caption || ''}]
[Duration: ]
[MediaURL: ${episodeSpecificMediaUrl}]
<!-- End Cue -->`

        // Store the completed cue data
        this.pendingCueData = imgCueBlock;

        // Step 6: Handle insertion based on editor mode
        console.log('🎯 Step 6: Handling cue insertion for mode:', this.editorMode);
        console.log('🎯 editorMode type:', typeof this.editorMode);
        console.log('🎯 editorMode === "code":', this.editorMode === 'code');
        console.log('🎯 editorMode === "script":', this.editorMode === 'script');

        // CODE MODE: Insert directly at cursor position
        if (this.editorMode === 'code') {
          // Close the modal first for code mode
          this.showImgModal = false;
          console.log('📝 Code mode: Inserting at cursor position:', this.pendingCursorPosition);
          this.insertCueAtCursor(imgCueBlock);
          this.pendingCueData = null;
          this.pendingCursorPosition = null;
          this.pendingCueType = null;
          console.log('✅ IMG cue inserted in code mode');
          return;
        }

        // SCRIPT MODE: Insert at end of script content
        console.log('📄 Script mode: Inserting at end of script content');

        // Close the modal
        this.showImgModal = false;

        // Simply append to the end of script content
        const currentContent = this.scriptContent || '';
        const newContent = currentContent + '\n\n' + imgCueBlock + '\n\n';
        this.$emit('update:scriptContent', newContent);
        console.log('✅ IMG cue inserted at end of script');

        // Clear pending data
        this.pendingCueData = null;
        this.pendingCueType = null;

        console.log('IMG cue created:', imgCueData)
      } catch (error) {
        console.error('Error handling IMG cue submission:', error)
        // TODO: Show error message to user
      }
    },

    // Handle modal close events (including ESC key abort)
    handleImgModalClose(isVisible) {
      // When modal is closed (isVisible becomes false)
      if (!isVisible) {
        console.log('🎬🔥 IMG modal closed - EMERGENCY clearing ALL highlighting');

        // Force immediate cleanup of cursor position highlight
        console.log('🎯🔥 Force clearing cursor position highlight before anything else');
        this.clearCursorPositionHighlight();

        // Then clear insertion highlight (which should also call clearCursorPositionHighlight again)
        this.clearInsertionHighlight();

        // Also manually remove any leftover elements by class name
        const orphanedElements = document.querySelectorAll('.cursor-position-highlight');
        console.log('🧹 Found', orphanedElements.length, 'potentially orphaned cursor highlights');
        orphanedElements.forEach((element, index) => {
          try {
            element.remove();
            console.log('🧹 Removed orphaned element', index + 1);
          } catch (error) {
            console.error('🧹 Failed to remove orphaned element', index + 1, error);
          }
        });

        // CRITICAL: Clean up any leftover cursor characters in textarea
        this.cleanupCursorCharacters();
        // Clear pending data
        this.pendingCueType = null;
        this.pendingInsertionPoint = null;
        this.pendingCueData = null;
        this.editingCueData = null;

        console.log('🎬✅ Modal close cleanup COMPLETE');
      }
    },

    // Visual Script Mode Methods
    // Single Source of Truth Editing Methods
    getSegmentContent(segmentIndex) {
      // Return buffered content if it exists (user is actively editing)
      if (this.segmentEditBuffer && this.segmentEditBuffer[segmentIndex] !== undefined) {
        console.log('📝 getSegmentContent: returning BUFFERED content for segment', segmentIndex);
        return this.segmentEditBuffer[segmentIndex];
      }

      // Otherwise return parsed content from single source of truth
      const segment = this.scriptSegments[segmentIndex];
      return segment ? segment.content : '';
    },

    updateTextSegment(segmentIndex, newContent) {
      console.log('📝 updateTextSegment called - Index:', segmentIndex, 'New content length:', newContent.length);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      // Initialize edit buffer if needed
      if (!this.segmentEditBuffer) {
        this.segmentEditBuffer = {};
      }
      if (!this.updateDebounceTimers) {
        this.updateDebounceTimers = {};
      }

      // Store the new content in buffer immediately (trim to prevent whitespace issues)
      this.segmentEditBuffer[segmentIndex] = newContent;
      console.log('📝 Buffered content for segment', segmentIndex, '- Content:', newContent.substring(0, 50));

      // Clear existing timer for this segment
      if (this.updateDebounceTimers[segmentIndex]) {
        clearTimeout(this.updateDebounceTimers[segmentIndex]);
      }

      // Debounce the actual update to prevent race conditions during typing
      this.updateDebounceTimers[segmentIndex] = setTimeout(async () => {
        console.log('📝 Debounced update executing for segment', segmentIndex);

        // Get current segments from parsed content
        const segments = [...this.scriptSegments];

        if (!segments[segmentIndex] || segments[segmentIndex].type !== 'text') {
          console.error('Cannot update non-text segment or invalid index:', segmentIndex);
          return;
        }

        console.log('📝 Old content:', JSON.stringify(segments[segmentIndex].content));

        // Update this specific segment with buffered content
        segments[segmentIndex].content = this.segmentEditBuffer[segmentIndex];

        console.log('📝 Updated segment content:', JSON.stringify(segments[segmentIndex].content));

        // Reconstruct raw markdown content
        const newRawContent = this.reconstructRawContent(segments);

        console.log('📝 Reconstructed raw content length:', newRawContent.length);

        // Update single source of truth
        this.rawScriptContent = newRawContent;

        // Clear buffer and timer
        delete this.segmentEditBuffer[segmentIndex];
        delete this.updateDebounceTimers[segmentIndex];

        // Persist to database and show visual feedback
        await this.persistCurrentItemToDatabase(segmentIndex);
      }, 2000); // 2 second debounce - persist after user stops typing
    },

    // Handle keyboard events for Script mode behaviors that affect Code mode
    handleTextareaKeydown(segmentIndex, event) {
      console.log('🎹 Key pressed:', event.key, 'in segment', segmentIndex);

      if (event.key === 'Enter' && !event.shiftKey) {
        const textarea = event.target;
        const currentContent = textarea.value;
        const cursorPos = textarea.selectionStart;

        // Check if we're at the end and if content already ends with newline
        const atEnd = cursorPos === currentContent.length;
        const contentEndsWithNewline = currentContent.endsWith('\n');

        // If at end AND content already ends with \n, this is the SECOND Enter
        if (atEnd && contentEndsWithNewline) {
          event.preventDefault();

          // Remove the trailing newline from current segment
          const cleanedContent = currentContent.replace(/\n$/, '');
          this.updateTextSegment(segmentIndex, cleanedContent);

          // Create new paragraph
          this.createNewParagraphAfter(segmentIndex);
        }
        // Otherwise let the first Enter add a newline normally
      }

      // Script Mode Behavior: Backspace at beginning merges with previous paragraph
      if (event.key === 'Backspace') {
        const textarea = event.target;
        const cursorPos = textarea.selectionStart;

        // If at beginning of any paragraph, merge with previous
        if (cursorPos === 0) {
          event.preventDefault();
          this.mergeParagraphWithPrevious(segmentIndex);
        }
      }

      // Script Mode Behavior: Delete key at end of paragraph merges with next
      if (event.key === 'Delete') {
        const textarea = event.target;
        const content = textarea.value;
        const cursorPos = textarea.selectionStart;

        // If at end of paragraph, merge with next paragraph
        if (cursorPos === content.length) {
          setTimeout(() => {
            this.mergeParagraphWithNext(segmentIndex);
          }, 0);
        }
      }
    },

    // Script Mode Behavior: Create new <p> tag in Code mode
    createNewParagraphAfter(segmentIndex) {
      console.log('📝 Creating new paragraph after segment', segmentIndex);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      const segments = [...this.scriptSegments];
      const currentSegment = segments[segmentIndex];

      if (!currentSegment) return;

      // Create new empty text segment that will become a new <p> tag
      const newSegment = {
        type: 'text',
        content: '', // Empty content for new paragraph
        speaker: currentSegment.speaker || 'josh', // Inherit speaker from current paragraph
        needsParagraphTags: true // This ensures it becomes <p class="speaker">content</p>
      };

      // Insert after current segment
      segments.splice(segmentIndex + 1, 0, newSegment);

      // Reconstruct raw content - this will create the new <p> tag in Code mode
      const newRawContent = this.reconstructRawContent(segments);
      this.rawScriptContent = newRawContent;

      // Focus the new empty paragraph for immediate typing
      this.$nextTick(() => {
        // Try multiple times to ensure the new textarea is rendered
        const tryFocus = (attempts = 0) => {
          if (attempts > 5) {
            console.log('❌ Failed to focus new paragraph after 5 attempts');
            return;
          }

          const textareaRef = this.$refs[`textareaRef-${segmentIndex + 1}`];
          const textarea = textareaRef?.[0]?.$el?.querySelector('textarea');

          console.log(`🎯 Focus attempt ${attempts + 1}:`, {
            ref: textareaRef,
            textarea: textarea
          });

          if (textarea) {
            textarea.focus();
            console.log('✅ Focused new paragraph');
          } else {
            // Try again after a short delay
            setTimeout(() => tryFocus(attempts + 1), 50);
          }
        };

        tryFocus();
      });
    },

    // Create initial paragraph for empty content
    createInitialParagraph() {
      console.log('🔧 createInitialParagraph called');

      // Check if content already has <p> tags
      const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);
      if (contentWithoutFrontmatter && contentWithoutFrontmatter.includes('<p')) {
        console.log('❌ Content already has <p> tags, skipping');
        return; // Already has paragraph tags
      }

      console.log('✅ Creating initial paragraph');

      // Extract existing frontmatter (if any)
      const frontmatterMatch = this.rawScriptContent.match(/^(---\n[\s\S]*?\n---\n)/);
      const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';

      // Preserve any existing content after frontmatter (like ## Notes, ## Description, ## Script)
      const existingContent = contentWithoutFrontmatter || '';

      // Create initial empty paragraph after existing content
      const initialContent = frontmatter + existingContent + '\n<p class="josh"></p>\n';

      console.log('📝 Setting rawScriptContent with initial paragraph (triggers setter emit)');
      this.rawScriptContent = initialContent;

      // Note: Focus happens in scriptSegments watcher after content is rendered
    },

    // Script Mode Behavior: Merge paragraph with previous (Backspace at start)
    mergeParagraphWithPrevious(segmentIndex) {
      if (segmentIndex === 0) return; // Can't merge first paragraph

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      const segments = [...this.scriptSegments];
      const currentSegment = segments[segmentIndex];
      const previousSegment = segments[segmentIndex - 1];

      // Only merge text segments
      if (currentSegment?.type !== 'text' || previousSegment?.type !== 'text') return;

      // Remember cursor position (end of previous content)
      const cursorPosition = previousSegment.content.length;

      // Merge current content into previous segment
      previousSegment.content = previousSegment.content + currentSegment.content;

      // Remove current segment
      segments.splice(segmentIndex, 1);

      // Reconstruct and update Code mode
      const newRawContent = this.reconstructRawContent(segments);
      this.rawScriptContent = newRawContent;

      // Focus previous paragraph at merge point
      this.$nextTick(() => {
        const textareaRef = this.$refs[`textareaRef-${segmentIndex - 1}`];
        const textarea = textareaRef?.[0]?.$el?.querySelector('textarea');
        if (textarea) {
          textarea.focus();
          textarea.setSelectionRange(cursorPosition, cursorPosition);
        }
      });
    },

    // Script Mode Behavior: Merge with next paragraph (Delete at end)
    mergeParagraphWithNext(segmentIndex) {
      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      const segments = [...this.scriptSegments];
      if (segmentIndex >= segments.length - 1) return; // Can't merge last paragraph

      const currentSegment = segments[segmentIndex];
      const nextSegment = segments[segmentIndex + 1];

      // Only merge text segments
      if (currentSegment?.type !== 'text' || nextSegment?.type !== 'text') return;

      // Merge content if next segment has content
      if (nextSegment.content.trim()) {
        currentSegment.content = currentSegment.content + ' ' + nextSegment.content;
      }

      // Remove next segment
      segments.splice(segmentIndex + 1, 1);

      // Reconstruct and update Code mode
      const newRawContent = this.reconstructRawContent(segments);
      this.rawScriptContent = newRawContent;
    },

    // Reconstruct raw markdown from segments
    reconstructRawContent(segments) {
      // Get existing YAML frontmatter (only the FIRST block)
      const frontmatterMatch = this.rawScriptContent.match(/^(---\n[\s\S]*?\n---\n)/);
      const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';

      // Reconstruct content body using CueParser
      const contentBody = CueParser.reconstructContent(segments);

      // CRITICAL: Ensure content body doesn't start with frontmatter
      // This prevents duplicate frontmatter blocks
      const cleanContentBody = this.stripYamlFrontmatter(contentBody);

      return frontmatter + cleanContentBody;
    },

    reconstructScriptContent(segments) {
      return CueParser.reconstructContent(segments);
    },

    formatCueToMarkdown(cueData) {
      if (!cueData) return '';

      let cueBlock = '<!-- Begin Cue -->\n';

      // Add all fields from the original cue data
      Object.keys(cueData).forEach(key => {
        if (key !== 'imageTag' && key !== 'imageSrc' && cueData[key]) {
          const displayKey = this.formatFieldForDisplay(key);
          cueBlock += `[${displayKey}: ${cueData[key]}]\n`;
        }
      });

      // Add image tag if it exists
      if (cueData.imageTag) {
        cueBlock += `${cueData.imageTag}\n`;
      }

      cueBlock += '<!-- End Cue -->';
      return cueBlock;
    },

    formatFieldForDisplay(camelCaseField) {
      // Convert camelCase back to Title Case for display
      return camelCaseField
        .replace(/([A-Z])/g, ' $1')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    },

    selectCue(index) {
      this.selectedCueIndex = index;
    },

    editCue(index, cueData) {
      console.log('Edit cue at index:', index, cueData);
      // Open appropriate modal based on cue type
      if (cueData.type === 'IMG') {
        this.editingCueData = cueData;
        this.showImgModal = true;
      }
      // Add other cue type modals as needed
    },

    handleMetaUpdate({ cueData, metadata }) {
      console.log('Meta update received:', metadata);

      // Find the cue segment in scriptSegments
      const segmentIndex = this.scriptSegments.findIndex(segment =>
        segment.type === 'cue' && segment.data === cueData
      );

      if (segmentIndex === -1) {
        console.error('Could not find cue segment to update');
        return;
      }

      // Update the cue data with new metadata
      const updatedCueData = {
        ...cueData,
        rawData: {
          ...cueData.rawData,
          description: metadata.description,
          credit: metadata.credit,
          caption: metadata.caption,
          duration: metadata.duration
        }
      };

      // Rebuild the cue line with updated metadata
      const cueParser = new CueParser();
      const updatedCueLine = cueParser.buildCueLine(updatedCueData);

      // Update the segment
      this.scriptSegments[segmentIndex].data = updatedCueData;
      this.scriptSegments[segmentIndex].rawContent = updatedCueLine;

      // Reconstruct raw content
      const newRawContent = this.reconstructRawContent(this.scriptSegments);
      this.rawScriptContent = newRawContent;

      console.log('Meta updated successfully');
    },

    deleteCue(index) {
      const segment = this.scriptSegments[index];

      // If it's an IMG cue, show confirmation modal
      if (segment?.type === 'cue' && segment.data?.type === 'IMG') {
        this.deletingCueData = segment.data;
        this.deletingCueIndex = index;
        this.showDeleteImgModal = true;
        return;
      }

      // For other cue types, delete directly
      this.performCueDeletion(index, false);
    },

    performCueDeletion(index, deleteAssets = false) {
      // Remove the cue segment and update script content
      const updatedSegments = this.scriptSegments.filter((_, i) => i !== index);
      const newRawContent = this.reconstructRawContent(updatedSegments);
      this.rawScriptContent = newRawContent;

      // Clear selection if the deleted cue was selected
      if (this.selectedCueIndex === index) {
        this.selectedCueIndex = null;
      }

      // TODO: If deleteAssets is true, also delete the media file via API
      if (deleteAssets && this.deletingCueData?.rawData?.mediaurl) {
        console.log('Would delete media file:', this.deletingCueData.rawData.mediaurl);
        // Implement API call to delete media file
      }
    },

    handleDeleteWithAssets() {
      if (this.deletingCueIndex !== null) {
        this.performCueDeletion(this.deletingCueIndex, true);
        this.deletingCueData = null;
        this.deletingCueIndex = null;
      }
    },

    handleDeletePreserveAssets() {
      if (this.deletingCueIndex !== null) {
        this.performCueDeletion(this.deletingCueIndex, false);
        this.deletingCueData = null;
        this.deletingCueIndex = null;
      }
    },


    extractOrderFromSlug(slug) {
      if (!slug) return null;

      // Extract number from slug like "20 kam-kam-harris" -> "20"
      const match = slug.match(/^(\d+)\s/);
      return match ? match[1] : null;
    },

    // Speaker-related methods
    selectSegment(index) {
      this.selectedSegmentIndex = index;
      this.selectedCueIndex = null; // Clear cue selection
    },

    deleteSegment(index) {
      console.log('🗑️ Delete segment called with index:', index);
      console.log('🗑️ Total segments before:', this.scriptSegments.length);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      // Remove the segment and update script content
      const updatedSegments = this.scriptSegments.filter((_, i) => i !== index);
      console.log('🗑️ Total segments after filter:', updatedSegments.length);
      const newScriptContent = this.reconstructScriptContentWithFrontmatter(updatedSegments);
      console.log('🗑️ New script content length:', newScriptContent.length);
      this.$emit('update:scriptContent', newScriptContent);
      console.log('🗑️ Emitted update:scriptContent');

      // Clear selection if the deleted segment was selected
      if (this.selectedSegmentIndex === index) {
        this.selectedSegmentIndex = null;
      }
      // Remove from multi-selection if it was selected
      this.multiSelectedSegments.delete(index);
    },

    openSpeakerSelector(segmentIndex) {
      this.editingSpeakerSegmentIndex = segmentIndex;
      const segment = this.scriptSegments[segmentIndex];
      this.currentSegmentSpeaker = segment.speaker || 'josh';
      this.showSpeakerSelector = true;
    },

    toggleMultiSelection(index) {
      console.log('Toggle multi-selection for index:', index);
      if (this.multiSelectedSegments.has(index)) {
        this.multiSelectedSegments.delete(index);
      } else {
        this.multiSelectedSegments.add(index);
      }
      console.log('Multi-selected segments:', Array.from(this.multiSelectedSegments));
    },

    deleteMultipleSegments() {
      console.log('🗑️ Bulk delete called for segments:', Array.from(this.multiSelectedSegments));
      // Sort indices in descending order to delete from end to start (preserves indices)
      const sortedIndices = Array.from(this.multiSelectedSegments).sort((a, b) => b - a);
      console.log('🗑️ Deleting in order:', sortedIndices);

      let updatedSegments = [...this.scriptSegments];

      // Remove segments from end to start
      sortedIndices.forEach(index => {
        updatedSegments.splice(index, 1);
      });

      console.log('🗑️ Segments remaining after bulk delete:', updatedSegments.length);
      const newRawContent = this.reconstructRawContent(updatedSegments);
      this.rawScriptContent = newRawContent;

      // Clear all selections
      this.clearMultiSelection();
      this.selectedSegmentIndex = null;
    },

    swapSelectedParagraphs() {
      console.log('🔄 Swap called for segments:', Array.from(this.multiSelectedSegments));

      // Check if exactly 2 segments are selected
      if (this.multiSelectedSegments.size !== 2) {
        this.swapErrorMessage = `Swap requires exactly 2 selected paragraphs. Currently ${this.multiSelectedSegments.size} selected.`;
        this.showSwapErrorDialog = true;
        return;
      }

      // Get the two indices and sort them
      const indices = Array.from(this.multiSelectedSegments).sort((a, b) => a - b);
      const [index1, index2] = indices;

      console.log(`🔄 Swapping segments at indices ${index1} and ${index2}`);

      let updatedSegments = [...this.scriptSegments];

      // Swap the segments
      [updatedSegments[index1], updatedSegments[index2]] = [updatedSegments[index2], updatedSegments[index1]];

      console.log('🔄 Segments swapped, reconstructing content');

      // Update content
      const newRawContent = this.reconstructRawContent(updatedSegments);
      this.rawScriptContent = newRawContent;

      // Clear selection
      this.clearMultiSelection();

      // Add blink effect to the swapped paragraphs
      this.$nextTick(() => {
        this.blinkingParagraphs.add(index1);
        this.blinkingParagraphs.add(index2);

        // Remove blink effect after animation completes (5 blinks at 0.3s each = 1.5s)
        setTimeout(() => {
          this.blinkingParagraphs.delete(index1);
          this.blinkingParagraphs.delete(index2);
        }, 1500);
      });
    },

    clearMultiSelection() {
      console.log('🔄 Clearing multi-selection');
      this.multiSelectedSegments.clear();
    },

    handleCuePlacement(placement) {
      console.log('📍 Cue placement selected:', placement);
      console.log('📍 placement.cueType:', placement.cueType);
      console.log('📍 this.pendingCueData exists:', !!this.pendingCueData);
      console.log('📍 this.pendingCueType:', this.pendingCueType);

      this.pendingPlacement = placement;
      this.showCuePlacement = false;

      // Handle different cue types that come from modals with pre-generated data
      if (placement.cueType === 'IMG' || placement.cueType === 'FSQ' || placement.cueType === 'SOT') {
        console.log(`📍 ${placement.cueType} cue type detected`);
        if (this.pendingCueData) {
          console.log(`✅ Using pendingCueData for ${placement.cueType} insertion`);
          console.log('📍 pendingCueData preview:', this.pendingCueData.substring(0, 200));
          // We already have cue data from modal, insert it
          this.insertCueAtPlacement(placement, this.pendingCueData);
          this.pendingCueData = null;
          this.pendingPlacement = null;
          this.pendingCueType = null;
        } else {
          console.warn(`⚠️ No pendingCueData found - opening ${placement.cueType} modal`);
          // No cue data yet, show modal first
          if (placement.cueType === 'IMG') {
            this.showImgModal = true;
          } else if (placement.cueType === 'FSQ') {
            this.$emit('show-fsq-modal');
          } else if (placement.cueType === 'SOT') {
            this.$emit('show-sot-modal');
          }
        }
      } else {
        console.log('📍 Non-IMG/FSQ/SOT cue type, generating cue block');
        // For other cue types, generate standard cue block and insert directly
        const cueContent = this.generateCueBlock(placement.cueType);
        this.insertCueAtPlacement(placement, cueContent);

        // Clear pending data
        this.pendingPlacement = null;
        this.pendingCueType = null;
      }
    },

    cancelCuePlacement() {
      console.log('❌ Cue placement cancelled - clearing all pending data');
      this.showCuePlacement = false;
      this.pendingCueType = null;
      this.pendingPlacement = null;
      this.pendingCueData = null;
      this.pendingInsertionPoint = null;
      this.pendingCursorPosition = null;
      console.log('✅ Drop locator terminated for this rundown/user');
    },

    async handleSotCueSubmit(sotCueText) {
      console.log('🎬 SOT cue submitted to EditorPanel for placement-based insertion');

      // Store the cue data for later insertion
      this.pendingCueData = sotCueText;
      this.pendingCueType = 'SOT';

      // CODE MODE: Insert directly at cursor position
      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting SOT at cursor position');
        this.insertCueAtCursor(sotCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ SOT cue inserted in code mode');
        return;
      }

      // SCRIPT MODE: Activate placement overlay for user to choose insertion point
      console.log('📄 Script mode: Activating placement overlay for SOT insertion');
      console.log('✅ Pending cue data stored, showing placement overlay');

      // Activate placement overlay - user will click to choose where to insert
      this.showCuePlacement = true;

      console.log('📍 Placement overlay activated - waiting for user to click drop zone');
      // User clicks a drop zone -> handleCuePlacement is called -> cue is inserted
    },

    generateCueBlock(cueType) {
      console.log('🏗️ Generating cue block for type:', cueType);

      // Generate unique asset ID for cues that need it
      const assetId = this.generateAssetId();

      switch (cueType) {
        case 'IMG':
          // This should NOT be called for IMG - IMG cues go through handleImgCueSubmit
          console.error('⚠️ generateCueBlock called for IMG - this should use handleImgCueSubmit instead');
          return `<!-- Begin Cue -->
[Type: IMG]
[AssetID: ${assetId}]
[Slug: img-${Date.now()}]
[Description: ]
[Credit: ]
[Caption: ]
[Duration: ]
[MediaURL: ]
<!-- End Cue -->`;

        case 'GFX':
          return `<!-- Begin Cue -->
[Type: GFX]
[AssetID: ${assetId}]
[Slug: gfx-${Date.now()}]
[Title: Graphics Title]
[Description: Lower third or graphic description]
[Duration: 00:00:05]
<!-- End Cue -->`;

        case 'FSQ':
          return `<!-- Begin Cue -->
[Type: FSQ]
[AssetID: ${assetId}]
[Slug: quote-${Date.now()}]
[Quote: "Your quote text here"]
[Attribution: Speaker Name, Title]
[Duration: 00:00:08]
<!-- End Cue -->`;

        case 'SOT':
          return `<!-- Begin Cue -->
[Type: SOT]
[AssetID: ${assetId}]
[Slug: sot-${Date.now()}]
[Title: Sound on Tape]
[Description: Audio description]
[Duration: 00:00:30]
[MediaURL: ../assets/audio/]
<!-- End Cue -->`;

        case 'VO':
          return `<!-- Begin Cue -->
[Type: VO]
[AssetID: ${assetId}]
[Slug: vo-${Date.now()}]
[Title: Voice Over]
[Script: Your voice over script here]
[Duration: 00:00:15]
<!-- End Cue -->`;

        case 'NAT':
          return `<!-- Begin Cue -->
[Type: NAT]
[AssetID: ${assetId}]
[Slug: nat-${Date.now()}]
[Title: Natural Sound]
[Description: Natural sound description]
[Duration: 00:00:10]
[MediaURL: ../assets/audio/]
<!-- End Cue -->`;

        case 'PKG':
          return `<!-- Begin Cue -->
[Type: PKG]
[AssetID: ${assetId}]
[Slug: pkg-${Date.now()}]
[Title: Package Title]
[Description: Package description]
[Duration: 00:02:00]
[MediaURL: ../assets/video/]
<!-- End Cue -->`;

        default: {
          const safeType = cueType || 'CUE';
          return `<!-- Begin Cue -->
[Type: ${safeType}]
[AssetID: ${assetId}]
[Slug: ${safeType.toLowerCase()}-${Date.now()}]
[Title: ${safeType} Title]
[Description: ${safeType} description]
[Duration: 00:00:05]
<!-- End Cue -->`;
        }
      }
    },

    generateAssetId() {
      // Simple asset ID generation - could be enhanced with proper ID generation logic
      return 'AST' + Date.now().toString().slice(-8) + Math.floor(Math.random() * 100).toString().padStart(2, '0');
    },

    insertCueAtPlacement(placement, cueContent = null) {
      console.log('🎯 Step 7: Inserting cue at placement:', placement);

      // Clear any highlighting
      this.clearInsertionHighlight();

      if (placement.type === 'between') {
        // Insert between paragraphs - straightforward
        this.insertCueBetweenParagraphsInRawScript(placement, cueContent);
      } else if (placement.type === 'paragraph') {
        // Insert within paragraph - requires splitting
        this.insertCueWithinParagraphInRawScript(placement, cueContent);
      }

      // Clean up pending state
      this.pendingCueData = null;
      this.pendingPlacement = null;
      this.pendingCueType = null;
      this.pendingInsertionPoint = null;

      console.log('✅ Cue insertion complete - should render in script mode');
    },

    insertCueBetweenParagraphs(placement, cueContent) {
      const insertIndex = placement.index + 1; // Insert after the specified paragraph

      if (cueContent) {
        // Add the cue content to script content
        const segments = [...this.scriptSegments];

        // Create cue segment
        const cueSegment = {
          type: 'cue',
          content: cueContent,
          cueType: placement.cueType
        };

        segments.splice(insertIndex, 0, cueSegment);

        const newScriptContent = this.reconstructScriptContentWithFrontmatter(segments);
        this.$emit('update:scriptContent', newScriptContent);
      }
    },

    insertCueWithinParagraph(placement, cueContent) {
      if (!cueContent) return;

      const paragraphIndex = placement.index;
      const characterPosition = placement.characterPosition || 0;

      const segments = [...this.scriptSegments];
      const targetSegment = segments[paragraphIndex];

      if (targetSegment && targetSegment.type === 'text') {
        const originalContent = targetSegment.content;

        // Split the paragraph content at character position
        const beforeText = originalContent.substring(0, characterPosition);
        const afterText = originalContent.substring(characterPosition);

        // Create three new segments: before, cue, after
        const beforeSegment = {
          ...targetSegment,
          content: beforeText.trim()
        };

        const cueSegment = {
          type: 'cue',
          content: cueContent,
          cueType: placement.cueType
        };

        const afterSegment = {
          ...targetSegment,
          content: afterText.trim()
        };

        // Replace the original segment with the three new ones
        const newSegments = [
          ...segments.slice(0, paragraphIndex),
          ...(beforeText.trim() ? [beforeSegment] : []),
          cueSegment,
          ...(afterText.trim() ? [afterSegment] : []),
          ...segments.slice(paragraphIndex + 1)
        ];

        const newScriptContent = this.reconstructScriptContentWithFrontmatter(newSegments);
        this.$emit('update:scriptContent', newScriptContent);
      }
    },

    // Code Mode: Insert cue at cursor position in raw textarea
    insertCueAtCursor(cueContent) {
      console.log('📝 Inserting cue at cursor position in code mode');

      if (!cueContent) {
        console.error('❌ No cue content provided for insertion');
        return;
      }

      // Get current script content
      let currentScript = this.scriptContent || '';

      // Use stored cursor position (or fallback to end)
      const cursorPosition = this.pendingCursorPosition !== null
        ? this.pendingCursorPosition
        : currentScript.length;

      console.log('📝 Inserting at position:', cursorPosition);

      // Insert cue block at cursor position with proper spacing
      const beforeCursor = currentScript.slice(0, cursorPosition);
      const afterCursor = currentScript.slice(cursorPosition);

      // Add newlines around cue block for proper formatting
      const newScript = beforeCursor + '\n\n' + cueContent + '\n\n' + afterCursor;

      console.log('📝 New script length:', newScript.length);

      // Update script content
      this.$emit('update:scriptContent', newScript);

      // Clear cursor position
      this.pendingCursorPosition = null;

      console.log('✅ Cue inserted at cursor position');
    },

    // Raw Script Insertion Methods (Direct to Database)
    insertCueBetweenParagraphsInRawScript(placement, cueContent) {
      console.log('🎯 Inserting cue between paragraphs in raw script');
      console.log('🎯 Placement index:', placement.index);

      // Get current script content
      let currentScript = this.scriptContent || '';

      // Find all paragraph elements to determine insertion point
      const paragraphMatches = [...currentScript.matchAll(/<p[^>]*class="[^"]*"[^>]*>.*?<\/p>/gs)];

      if (paragraphMatches.length === 0) {
        // No paragraphs found, append at end
        const newScript = currentScript + '\n\n' + cueContent + '\n\n';
        this.$emit('update:scriptContent', newScript);
        return;
      }

      // Between-zone index mapping:
      // index 0 = before first paragraph
      // index 1 = after paragraph 0
      // index 2 = after paragraph 1
      // etc.
      const betweenZoneIndex = placement.index;

      if (betweenZoneIndex === 0) {
        // Insert before first paragraph
        const firstParagraph = paragraphMatches[0];
        const insertPosition = firstParagraph.index;

        const beforeCue = currentScript.slice(0, insertPosition);
        const afterCue = currentScript.slice(insertPosition);

        const newScript = beforeCue + cueContent + '\n\n' + afterCue;
        this.$emit('update:scriptContent', newScript);
        console.log('🎯 Inserted before first paragraph');
      } else if (betweenZoneIndex > paragraphMatches.length) {
        // Insert at end
        const newScript = currentScript + '\n\n' + cueContent + '\n\n';
        this.$emit('update:scriptContent', newScript);
        console.log('🎯 Inserted at end');
      } else {
        // Insert after paragraph[betweenZoneIndex - 1]
        const paragraphIndex = betweenZoneIndex - 1;
        const paragraphMatch = paragraphMatches[paragraphIndex];
        const insertPosition = paragraphMatch.index + paragraphMatch[0].length;

        const beforeCue = currentScript.slice(0, insertPosition);
        const afterCue = currentScript.slice(insertPosition);

        const newScript = beforeCue + '\n\n' + cueContent + '\n\n' + afterCue;
        this.$emit('update:scriptContent', newScript);
        console.log(`🎯 Inserted after paragraph ${paragraphIndex}`);
      }
    },

    insertCueWithinParagraphInRawScript(placement, cueContent) {
      console.log('🎯 Inserting cue within paragraph in raw script');

      // Get current script content
      let currentScript = this.scriptContent || '';

      // Find all paragraph elements
      const paragraphMatches = [...currentScript.matchAll(/<p[^>]*class="[^"]*"[^>]*>(.*?)<\/p>/gs)];

      if (paragraphMatches.length === 0 || !paragraphMatches[placement.index]) {
        // Fallback to between paragraphs
        this.insertCueBetweenParagraphsInRawScript(placement, cueContent);
        return;
      }

      const paragraphMatch = paragraphMatches[placement.index];
      const paragraphContent = paragraphMatch[1];
      const paragraphStart = paragraphMatch.index;
      const paragraphEnd = paragraphMatch.index + paragraphMatch[0].length;

      // Split paragraph at character position
      const characterOffset = placement.characterOffset || 0;
      const beforeText = paragraphContent.slice(0, characterOffset);
      const afterText = paragraphContent.slice(characterOffset);

      // Get paragraph class and speaker
      const classMatch = paragraphMatch[0].match(/class="([^"]*)"/);
      const paragraphClass = classMatch ? classMatch[1] : 'josh';

      // Create new content with split paragraphs and cue
      let newParagraphContent = '';

      if (beforeText.trim()) {
        newParagraphContent += `<p class="${paragraphClass}">${beforeText.trim()}</p>\n\n`;
      }

      newParagraphContent += cueContent + '\n\n';

      if (afterText.trim()) {
        newParagraphContent += `<p class="${paragraphClass}">${afterText.trim()}</p>`;
      }

      // Replace the original paragraph with the new content
      const beforeParagraph = currentScript.slice(0, paragraphStart);
      const afterParagraph = currentScript.slice(paragraphEnd);

      const newScript = beforeParagraph + newParagraphContent + afterParagraph;
      this.$emit('update:scriptContent', newScript);
    },

    handleSpeakerChange(newSpeaker) {
      if (this.editingSpeakerSegmentIndex !== null) {
        // Update the segment's speaker
        const updatedSegments = [...this.scriptSegments];
        updatedSegments[this.editingSpeakerSegmentIndex].speaker = newSpeaker;

        // Reconstruct and emit updated content
        const newScriptContent = this.reconstructScriptContentWithFrontmatter(updatedSegments);
        this.$emit('update:scriptContent', newScriptContent);

        // Clear editing state
        this.editingSpeakerSegmentIndex = null;
      }
    },

    focusTypingInput() {
      // Focus the typing input when the typing area is clicked
      this.$nextTick(() => {
        if (this.$refs.typingInputRef) {
          this.$refs.typingInputRef.focus();
        }
      });
    },

    handleTypingInput() {
      // Auto-create paragraphs as user types
      if (this.typingBuffer.trim()) {
        // User is typing, keep the content in buffer
        // We'll convert to paragraph when they finish (on Enter or blur)
      }
    },

    handleTypingKeydown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        // Check if this is a double Enter (empty line followed by Enter)
        const currentValue = this.typingBuffer;
        const endsWithNewline = currentValue.endsWith('\n');

        if (endsWithNewline && currentValue.trim() !== '') {
          // Double Enter - create paragraph and start new one
          event.preventDefault();
          this.createParagraphFromCurrentLine();
        } else {
          // Single Enter - allow normal line break behavior
          // Don't prevent default, let the textarea handle it
        }
      }
    },

    handleGlobalKeydown(event) {
      // Handle Ctrl+Shift+X for XTTS reading
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'x') {
        console.log('✅ CTRL+SHIFT+X triggered - toggling XTTS reading');
        event.preventDefault();
        this.toggleContextualReading();
        return;
      }

      // Track ALT key state manually
      if (event.key === 'Alt') {
        this.altKeyPressed = true;
        return;
      }

      // Handle Alt+Shift+A for AssetID regeneration (special case)
      if (this.altKeyPressed && event.shiftKey && event.key.toLowerCase() === 'a') {
        console.log('✅ ALT+SHIFT+A triggered - calling regenerateCurrentCueAssetID');
        event.preventDefault();
        this.regenerateCurrentCueAssetID();
        return;
      }

      // Use manual ALT tracking instead of event.altKey for better browser compatibility
      if (!this.altKeyPressed || event.ctrlKey || event.shiftKey) {
        return;
      }

      // Don't trigger hotkeys when typing in input fields (except our own speaker textareas)
      const target = event.target;

      // Allow hotkeys in speaker textareas by checking if textarea is inside a speaker-paragraph
      const isInSpeakerParagraph = target.closest && target.closest('.speaker-paragraph');

      if (target.tagName === 'INPUT' ||
          (target.tagName === 'TEXTAREA' && !isInSpeakerParagraph)) {
        return;
      }

      // Handle ENTER key for placement acceptance (no ALT needed)
      // BUT skip if we're typing in Code Mode or Script Mode textareas
      if (event.key === 'Enter' && this.showCuePlacement) {
        const target = event.target;
        const isCodeModeTextarea = target.classList.contains('code-textarea') ||
                                 target.closest('.code-textarea');
        const isScriptModeTextarea = target.classList.contains('speaker-textarea') ||
                                   target.closest('.speaker-paragraph');

        if (!isCodeModeTextarea && !isScriptModeTextarea) {
          this.handleEnterKeyForPlacement(event);
          return;
        }
      }

      // Handle cue hotkeys
      console.log('🔑 Processing hotkey:', event.key.toLowerCase(), 'with manual ALT tracking');
      switch (event.key.toLowerCase()) {
        case 'i':
          console.log('✅ ALT+I triggered - calling insertCue(IMG)');
          event.preventDefault();
          this.insertCue('IMG');
          break;
        case 'g':
          event.preventDefault();
          this.insertCue('GFX');
          break;
        case 'q':
          event.preventDefault();
          this.insertCue('FSQ');
          break;
        case 's':
          event.preventDefault();
          this.insertCue('SOT');
          break;
        case 'v':
          event.preventDefault();
          this.insertCue('VO');
          break;
        case 'n':
          event.preventDefault();
          this.insertCue('NAT');
          break;
        case 'p':
          event.preventDefault();
          this.insertCue('PKG');
          break;
        default:
          console.log('❓ Unhandled hotkey:', event.key);
          break;
      }
    },

    // Handle ENTER key to accept current highlighted location
    handleEnterKeyForPlacement(event) {
      if (this.showCuePlacement && this.pendingInsertionPoint && this.pendingCueData) {
        console.log('⏎ ENTER pressed - accepting current highlighted location');
        event.preventDefault();

        // Create placement object from our stored insertion point
        const placement = {
          type: this.pendingInsertionPoint.type,
          index: this.getElementIndex(this.pendingInsertionPoint.element),
          cueType: this.pendingCueType,
          characterOffset: this.pendingInsertionPoint.characterOffset || 0
        };

        // Insert at current location
        this.insertCueAtPlacement(placement, this.pendingCueData);
        this.showCuePlacement = false;
      }
    },

    // Get the index of an element among its siblings
    getElementIndex(element) {
      const paragraphs = document.querySelectorAll('.speaker-paragraph');
      return Array.from(paragraphs).indexOf(element);
    },

    handleGlobalKeyup(event) {
      // Reset ALT key state on keyup
      if (event.key === 'Alt') {
        this.altKeyPressed = false;
        console.log('🔑 ALT key released - setting altKeyPressed = false');
      }
    },

    createParagraphFromCurrentLine() {
      if (this.typingBuffer.trim()) {
        // Create a new paragraph from the current buffer
        const newParagraph = `<p class="josh">${this.typingBuffer.trim()}</p>`;
        const newScriptContent = this.scriptContent
          ? this.scriptContent + '\n\n' + newParagraph + '\n\n'
          : newParagraph + '\n\n';
        this.$emit('update:scriptContent', newScriptContent);

        // Clear the buffer for the next paragraph
        this.typingBuffer = '';

        // Keep focus on the input for continuous typing
        this.$nextTick(() => {
          if (this.$refs.typingInputRef) {
            this.$refs.typingInputRef.focus();
          }
        });
      }
    },

    // Handle traditional script textarea updates while preserving frontmatter
    handleTraditionalScriptUpdate(newContent) {
      // Get existing frontmatter
      const existingFrontmatter = this.extractYamlFrontmatter(this.scriptContent);

      // Combine frontmatter with new content
      const fullContent = existingFrontmatter
        ? existingFrontmatter + '\n' + newContent
        : newContent;

      this.$emit('update:scriptContent', fullContent);
    },

    // Handle paragraph click for selection
    handleParagraphClick(index, event) {
      if (event.ctrlKey || event.metaKey) {
        // Ctrl+click for multi-selection
        this.toggleMultiSelection(index);
      } else {
        // Regular click for single selection
        this.selectSegment(index);
      }
    },

    // Get speaker display name
    getSpeakerDisplayName(speaker) {
      const options = CueParser.getSpeakerOptions();
      const option = options.find(opt => opt.value === speaker);
      return option ? option.label : speaker.charAt(0).toUpperCase() + speaker.slice(1);
    },

    // Get light background style for speaker
    getLightBackgroundStyle(speaker) {
      const speakerColor = speaker === 'josh' ? '#1565C0' : CueParser.getSpeakerColor(speaker);
      return {
        backgroundColor: this.hexToRgba(speakerColor, 0.05)
      };
    },

    // Get paragraph background style (with focus states)
    getParagraphBackgroundStyle(speaker, index) {
      console.log(`🎨 getParagraphBackgroundStyle called for index ${index}:`, {
        savedParagraphIndex: this.savedParagraphIndex,
        errorParagraphIndex: this.errorParagraphIndex,
        focusedParagraphIndex: this.focusedParagraphIndex,
        paragraphEditStates: this.paragraphEditStates
      });

      // If error (red flash), override with red
      if (this.errorParagraphIndex === index) {
        console.log(`🔴 Paragraph ${index} has ERROR - showing red`);
        return {
          backgroundColor: '#ffcdd2', // Light red
          transition: 'background-color 0.25s ease'
        };
      }

      // If saved (blue flash), override with blue
      if (this.savedParagraphIndex === index) {
        console.log(`🔵 Paragraph ${index} is SAVED - showing blue`);
        return {
          backgroundColor: '#bbdefb', // Light blue
          transition: 'background-color 0.25s ease'
        };
      }

      // If focused, use very light yellow
      if (this.focusedParagraphIndex === index) {
        console.log(`🟡 Paragraph ${index} is FOCUSED - showing yellow`);
        return {
          backgroundColor: '#fffef0', // Very light yellow
          transition: 'background-color 0.2s ease'
        };
      }

      // Default speaker color background
      const speakerColor = speaker === 'josh' ? '#1565C0' : CueParser.getSpeakerColor(speaker);
      console.log(`⚪ Paragraph ${index} default color - speaker: ${speaker}`);
      return {
        backgroundColor: this.hexToRgba(speakerColor, 0.05),
        transition: 'background-color 0.2s ease'
      };
    },

    // Handle paragraph focus
    handleParagraphFocus(index) {
      console.log('🎯 Paragraph focused:', index);
      console.log('🎯 Previously edited?', this.paragraphEditStates[index]);
      console.log('🎯 All edit states:', this.paragraphEditStates);

      // Only show yellow highlight if this paragraph was previously edited
      // (i.e., user is coming back to edit existing content)
      if (this.paragraphEditStates[index]) {
        console.log('🟡 Re-editing existing paragraph - setting focusedParagraphIndex to', index);
        this.focusedParagraphIndex = index;
        console.log('🟡 focusedParagraphIndex is now:', this.focusedParagraphIndex);
      } else {
        console.log('⚪ First edit of paragraph - no highlight');
        this.focusedParagraphIndex = null;
      }

      // Debug: Check if the CSS class is being applied
      this.$nextTick(() => {
        const element = document.querySelector(`.seg-${index}`);
        console.log('🎯 Element found:', element);
        console.log('🎯 Element classes:', element?.classList.toString());
        console.log('🎯 Element computed background:', element ? window.getComputedStyle(element).backgroundColor : 'N/A');
      });
    },

    // Handle paragraph blur
    async handleParagraphBlur(index) {
      console.log('📝 Paragraph blurred:', index);
      this.focusedParagraphIndex = null;
      console.log('📝 focusedParagraphIndex cleared');

      // Mark this paragraph as having been edited at least once
      this.paragraphEditStates[index] = true;
      console.log('📝 Marked paragraph', index, 'as edited. Edit states:', this.paragraphEditStates);

      // Immediately trigger save on blur (cancel debounce timer)
      if (this.updateDebounceTimers[index]) {
        console.log('📝 Blur detected - canceling debounce timer and saving immediately');
        clearTimeout(this.updateDebounceTimers[index]);

        // Execute the save immediately
        if (this.segmentEditBuffer && this.segmentEditBuffer[index] !== undefined) {
          const segments = [...this.scriptSegments];

          if (segments[index] && segments[index].type === 'text') {
            segments[index].content = this.segmentEditBuffer[index];
            const newRawContent = this.reconstructRawContent(segments);
            this.rawScriptContent = newRawContent;

            // Clear buffer and timer
            delete this.segmentEditBuffer[index];
            delete this.updateDebounceTimers[index];

            // Persist to database and show visual feedback
            await this.persistCurrentItemToDatabase(index);
          }
        }
      }
    },

    // Handle save all button click
    handleSaveAll() {
      console.log('💾 Save All button clicked');

      // Emit save event to parent
      this.$emit('save-all');

      // Reset local unsaved changes flag
      this.hasLocalUnsavedChanges = false;

      console.log('✅ Local unsaved changes flag reset');
    },

    // Persist current item to database with visual feedback
    async persistCurrentItemToDatabase(segmentIndex) {
      console.log('💾 Persisting current item to database (autosave)...');

      try {
        // Emit save-current event to parent ContentEditor
        // This will trigger the saveCurrentItem method which persists to DB
        this.$emit('save-current');

        // Triple blue flash on success
        await this.flashParagraph(segmentIndex, 'success', 3);

        console.log('✅ Autosave successful');
      } catch (error) {
        console.error('❌ Autosave failed:', error);

        // Triple red flash on failure
        await this.flashParagraph(segmentIndex, 'error', 3);

        // Show urgent flash notification
        if (window.flashUrgent) {
          window.flashUrgent('Autosave Failed!', window.FLASH_COLORS.RED, 3000);
        }
      }
    },

    // Flash a paragraph with specified color and count
    async flashParagraph(index, type, count) {
      const flashClass = type === 'success' ? 'savedParagraphIndex' : 'errorParagraphIndex';

      for (let i = 0; i < count; i++) {
        this[flashClass] = index;
        await new Promise(resolve => setTimeout(resolve, 150));
        this[flashClass] = null;
        if (i < count - 1) {
          await new Promise(resolve => setTimeout(resolve, 150));
        }
      }
    },

    // Get dark border style for speaker header
    getSpeakerHeaderStyle(speaker) {
      const speakerColor = speaker === 'josh' ? '#1565C0' : CueParser.getSpeakerColor(speaker);
      return {
        borderBottomColor: this.darkenColor(speakerColor, 0.3)
      };
    },

    // Darken a hex color
    darkenColor(hex, amount) {
      const r = Math.max(0, parseInt(hex.slice(1, 3), 16) * (1 - amount));
      const g = Math.max(0, parseInt(hex.slice(3, 5), 16) * (1 - amount));
      const b = Math.max(0, parseInt(hex.slice(5, 7), 16) * (1 - amount));
      return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
    },

    // Convert hex to rgba
    hexToRgba(hex, alpha) {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    // Autoformat function to fix multiple paragraphs in single <p> tags
    autoformatContent() {
      if (!this.scriptContent || typeof this.scriptContent !== 'string') {
        return;
      }

      // Don't run autoformat while user is actively typing
      if (this.isActivelyTyping) {
        console.log('Autoformat skipped - user is actively typing');
        return false;
      }

      let hasChanges = false;
      let formattedContent = this.scriptContent;

      // Find all <p> tags with content
      const paragraphMatches = [...formattedContent.matchAll(/<p(?:\s+class="([^"]*)")?[^>]*>([\s\S]*?)<\/p>/g)];

      // Process each paragraph
      for (const match of paragraphMatches) {
        const fullMatch = match[0];
        const speaker = match[1] || 'josh';
        const content = match[2].trim();

        // Check if content contains multiple paragraphs (separated by double line breaks)
        const contentParagraphs = content.split(/\n\s*\n/).filter(p => p.trim());

        if (contentParagraphs.length > 1) {
          // Multiple paragraphs found - need to split
          const newParagraphs = contentParagraphs
            .map(paragraph => `<p class="${speaker}">${paragraph.trim()}</p>`)
            .join('\n\n');

          formattedContent = formattedContent.replace(fullMatch, newParagraphs);
          hasChanges = true;
        }
      }

      // Apply changes if any were made
      if (hasChanges) {
        console.log('Autoformat: Fixed multiple paragraphs in single <p> tags');
        this.$emit('update:scriptContent', formattedContent);
        return true;
      }

      return false;
    },

    // Run autoformat and show status
    runAutoformat() {
      const wasFormatted = this.autoformatContent();

      // YAML frontmatter validation and synchronization
      const yamlUpdated = this.validateAndSyncYamlFrontmatter();

      // Smart cleanup of orphaned cursor markers (only when safe)
      const cleanedMarkers = this.smartCleanupOrphanedCursorMarkers();

      this.lastAutoformatTime = new Date(); // Update timestamp regardless of whether changes were made

      if (wasFormatted || yamlUpdated || cleanedMarkers > 0) {
// Content change is handled automatically through rawScriptContent computed property
      }
    },

    // Smart cleanup that respects active cursor highlighting and modal usage
    smartCleanupOrphanedCursorMarkers() {
      const cursorChar = '█';

      // Safety checks - don't cleanup if user is actively working with cursor highlighting
      if (this.isUserActivelyHighlighting()) {
        console.log('🛡️ Auto-cleanup: Skipping - user is actively highlighting cursor position');
        return 0;
      }

      let totalCleaned = 0;
      console.log('🧹 Auto-cleanup: Safe to scan for orphaned cursor markers...');

      // 1. Clean cursor markers from script content (only if no active modals)
      if (this.scriptContent && this.scriptContent.includes(cursorChar)) {
        const originalLength = this.scriptContent.length;
        const cleanedContent = this.scriptContent.replace(new RegExp(cursorChar, 'g'), '');
        const removedFromScript = originalLength - cleanedContent.length;

        if (removedFromScript > 0) {
          this.$emit('update:scriptContent', cleanedContent);
          totalCleaned += removedFromScript;
          console.log(`🧹 Auto-cleanup: Removed ${removedFromScript} cursor markers from script content`);
        }
      }

      // 2. Raw markdown content cleanup removed (deprecated)

      // 3. Clean old/stale cursor elements from DOM (but not active ones)
      const staleCursors = document.querySelectorAll('.yellow-cursor-char:not(.active-cursor)');
      staleCursors.forEach((element, index) => {
        const text = element.textContent;
        if (text && (text === '█' || text.includes('█'))) {
          element.remove();
          totalCleaned++;
          console.log(`🧹 Auto-cleanup: Removed stale cursor element ${index + 1}`);
        }
      });

      if (totalCleaned > 0) {
        console.log(`✅ Auto-cleanup: Removed ${totalCleaned} total orphaned cursor markers`);
      }

      return totalCleaned;
    },

    // Check if user is actively using cursor highlighting (modal open, etc.)
    isUserActivelyHighlighting() {
      // Check if any modals are open
      const hasOpenModal = document.querySelector('.v-overlay--active .v-dialog') !== null;

      // Check if cursor positioning is active
      const hasCursorPositioning = this.cursorPositionHighlight !== null || this.showCuePlacement;

      // Check if thick cursor is showing (insertion mode)
      const hasThickCursor = this.thickCursor && this.thickCursor.show;

      // Check if user typed recently (within last 10 seconds)
      const recentActivity = this.lastAutoformatTime &&
        (new Date() - this.lastAutoformatTime) < 10000;

      // Check if any cue modals are open (IMG, GFX, SOT, etc.)
      const hasCueModal = document.querySelector('[class*="Modal"]:not([style*="display: none"])') !== null;

      return hasOpenModal || hasCursorPositioning || hasThickCursor || recentActivity || hasCueModal;
    },

    // Timer management for autoformat
    startAutoformatTimer() {
      this.stopAutoformatTimer(); // Clear any existing timer
      this.autoformatTimer = setInterval(() => {
        this.runAutoformat();
      }, 30000); // Run every 30 seconds
    },

    stopAutoformatTimer() {
      if (this.autoformatTimer) {
        clearInterval(this.autoformatTimer);
        this.autoformatTimer = null;
      }
    },

    // Debounced autoformat for content changes
    scheduleAutoformat() {
      this.clearAutoformatDebounce();
      this.autoformatDebounceTimer = setTimeout(() => {
        this.runAutoformat();
      }, 5000); // Run 5 seconds after last content change
    },

    clearAutoformatDebounce() {
      if (this.autoformatDebounceTimer) {
        clearTimeout(this.autoformatDebounceTimer);
        this.autoformatDebounceTimer = null;
      }
    },

    createParagraphFromBuffer() {
      if (this.typingBuffer.trim()) {
        // Split the buffer by line breaks to create separate paragraphs
        const lines = this.typingBuffer.split('\n').filter(line => line.trim());

        // Create a <p> tag for each line
        const newParagraphs = lines.map(line => `<p class="josh">${line.trim()}</p>`).join('\n\n');

        const newScriptContent = this.scriptContent
          ? this.scriptContent + '\n\n' + newParagraphs + '\n\n'
          : newParagraphs + '\n\n';

        this.$emit('update:scriptContent', newScriptContent);

        // Clear the buffer
        this.typingBuffer = '';

        // Keep focus on the input for continuous typing
        this.$nextTick(() => {
          if (this.$refs.typingInputRef) {
            this.$refs.typingInputRef.focus();
          }
        });
      }
    },

    // Universal Cue Insertion Workflow Methods
    showFlashMessage(cueType) {
      const flashMessage = `Insert ${cueType} CUE`;

      // Get the actual cue color from the theme system (same as button)
      const cueColor = this.getCueColor(cueType);

      // Create a fullscreen flash overlay using the exact button color
      const flashOverlay = document.createElement('div');
      flashOverlay.className = 'cue-flash-overlay';

      // Apply Winner-style fullscreen overlay with exact cue color
      flashOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(2px);
        background-color: ${cueColor}CC;
        animation: urgentFadeIn 0.05s ease-in;
      `;

      // Create text element with Winner-style formatting
      const flashText = document.createElement('div');
      flashText.textContent = flashMessage;
      flashText.style.cssText = `
        font-size: clamp(3rem, 8vw, 8rem);
        font-weight: 900;
        color: white;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        text-shadow:
          3px 3px 0px #000,
          -3px -3px 0px #000,
          3px -3px 0px #000,
          -3px 3px 0px #000,
          3px 0px 0px #000,
          -3px 0px 0px #000,
          0px 3px 0px #000,
          0px -3px 0px #000,
          5px 5px 10px rgba(0, 0, 0, 0.8);
        user-select: none;
        pointer-events: none;
        animation: textPulse 0.3s ease-in-out;
      `;

      flashOverlay.appendChild(flashText);
      document.body.appendChild(flashOverlay);

      // Add required CSS animations if not already present
      if (!document.getElementById('cue-flash-animations')) {
        const styleElement = document.createElement('style');
        styleElement.id = 'cue-flash-animations';
        styleElement.textContent = `
          @keyframes urgentFadeIn {
            from { opacity: 0; transform: scale(0.8); }
            to { opacity: 1; transform: scale(1); }
          }
          @keyframes urgentFadeOut {
            from { opacity: 1; transform: scale(1); }
            to { opacity: 0; transform: scale(0.95); }
          }
          @keyframes textPulse {
            0% { transform: scale(0.9); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
          }
        `;
        document.head.appendChild(styleElement);
      }

      // Start fade out after 300ms, complete removal after 800ms (matches UrgentFlash timing)
      setTimeout(() => {
        flashOverlay.style.animation = 'urgentFadeOut 0.5s ease-out forwards';
        setTimeout(() => {
          if (document.body.contains(flashOverlay)) {
            document.body.removeChild(flashOverlay);
          }
        }, 500);
      }, 300);
    },

    detectAndHighlightCursorPosition(cueType) {
      console.log("🎯 detectAndHighlightCursorPosition called with:", cueType);
      console.log("🎯 Current editorMode:", this.editorMode);

      // Get the currently focused element
      const activeElement = document.activeElement;
      console.log("🎯 activeElement:", activeElement);
      console.log("🎯 activeElement tagName:", activeElement?.tagName);
      console.log("🎯 activeElement className:", activeElement?.className);

      // Find the closest speaker paragraph
      const speakerParagraph = activeElement.closest('.speaker-paragraph');
      console.log("🎯 speakerParagraph found:", speakerParagraph);

      if (!speakerParagraph) {
        // Try to find ANY speaker paragraph as fallback
        const allParagraphs = document.querySelectorAll('.speaker-paragraph');
        console.log("🎯 Found", allParagraphs.length, "speaker paragraphs in total");
        if (allParagraphs.length > 0) {
          const firstParagraph = allParagraphs[0];
          console.log("🎯 Using first paragraph as fallback:", firstParagraph);
          this.highlightInsertionArea(firstParagraph);

          // Extract segment ID from class for script mode
          const segmentId = this.extractSegmentId(firstParagraph);

          return {
            type: 'paragraph',
            element: firstParagraph,
            segmentId: segmentId,
            cursorPosition: 0,
            characterOffset: 0
          };
        }
      }

      if (speakerParagraph) {
        // Extract segment ID from the paragraph-content div
        const segmentId = this.extractSegmentId(speakerParagraph);
        console.log("🎯 Extracted segment ID:", segmentId);

        // Highlight the paragraph with cue colors
        this.highlightInsertionArea(speakerParagraph);

        // For script mode, we just need segment ID, not cursor position
        if (this.editorMode === 'script') {
          return {
            type: 'segment',
            element: speakerParagraph,
            segmentId: segmentId
          };
        }

        // For code/scratch mode, also get cursor position
        const textarea = speakerParagraph.querySelector('textarea');
        const cursorPosition = textarea ? textarea.selectionStart : 0;

        // Add thick flashing cursor at exact cursor position
        this.showThickCursor(textarea, cursorPosition);

        return {
          type: 'paragraph',
          element: speakerParagraph,
          segmentId: segmentId,
          cursorPosition: cursorPosition,
          characterOffset: cursorPosition
        };
      } else {
        // No specific paragraph focus - default to end of content
        const paragraphs = document.querySelectorAll('.speaker-paragraph');
        const lastParagraph = paragraphs[paragraphs.length - 1];

        if (lastParagraph) {
          this.highlightInsertionArea(lastParagraph);
          const segmentId = this.extractSegmentId(lastParagraph);

          return {
            type: 'between',
            element: lastParagraph,
            segmentId: segmentId,
            cursorPosition: 0,
            insertAfter: true
          };
        }
      }

      return null;
    },

    extractSegmentId(paragraphElement) {
      // Find the paragraph-content div and extract segment index from seg-N class
      const paragraphContent = paragraphElement.querySelector('.paragraph-content');
      if (paragraphContent) {
        const classes = paragraphContent.className.split(' ');
        const segClass = classes.find(cls => cls.startsWith('seg-'));
        if (segClass) {
          const segmentId = parseInt(segClass.replace('seg-', ''));
          console.log("🎯 Extracted segment ID from class:", segClass, "→", segmentId);
          return segmentId;
        }
      }
      console.warn("🎯 Could not extract segment ID from paragraph");
      return null;
    },

    highlightInsertionArea(element) {
      // Clear any existing highlights
      this.clearInsertionHighlight();

      console.log("🎨 highlightInsertionArea called with element:", element);

      if (!element) {
        console.warn("🎨 No element provided to highlight");
        return;
      }

      // Get theme colors and resolve to hex values
      const dragLightColorName = getColorValue('DragLight') || 'blue-lighten-4';
      const droplineColorName = getColorValue('Dropline') || 'blue-darken-2';
      const highlightColorName = getColorValue('Highlight') || 'yellow-lighten-3';

      const dragLightColor = resolveVuetifyColor(dragLightColorName);
      const droplineColor = resolveVuetifyColor(droplineColorName);
      let highlightColor = resolveVuetifyColor(highlightColorName);

      // FORCE YELLOW COLOR - skip resolution, use direct yellow
      highlightColor = '#FFEB3B'; // Direct bright yellow

      console.log("🎨🟡 FORCED YELLOW COLOR:", highlightColor);

      console.log("🎨 Color resolution for highlighting:", {
        dragLightColorName,
        dragLightColor,
        droplineColorName,
        droplineColor,
        highlightColorName,
        highlightColor,
        'Expected yellow': '#FFF59D'
      });

      // Clear any existing selection styling first
      element.classList.remove('selected');

      // Store the original styles to restore later
      element._originalStyles = {
        backgroundColor: element.style.backgroundColor,
        border: element.style.border,
        boxShadow: element.style.boxShadow,
        transform: element.style.transform,
        transition: element.style.transition
      };

      // Apply highlight styling with maximum strength
      element.style.setProperty('background-color', dragLightColor, 'important');
      element.style.setProperty('border', `3px solid ${droplineColor}`, 'important');
      element.style.setProperty('box-shadow', `0 0 12px ${droplineColor}`, 'important');
      element.style.setProperty('transform', 'scale(1.05)', 'important');
      element.style.setProperty('transition', 'all 0.3s ease', 'important');

      // Store reference for cleanup
      this.highlightedElement = element;
      console.log("🎨 Highlight applied successfully to:", element.className);

      // Second level highlighting: precise cursor position within paragraph
      this.$nextTick(() => {
        this.addCursorPositionHighlight(element);
      });
    },

    showThickCursor(textarea, cursorPosition) {
      console.log("👆 showThickCursor called with textarea:", textarea, "cursorPosition:", cursorPosition);
      if (!textarea) return;

      // Create temporary span to measure text position
      const text = textarea.value;
      const beforeCursor = text.substring(0, cursorPosition);
      
      // Get textarea position and styling
      const textareaRect = textarea.getBoundingClientRect();
      const styles = window.getComputedStyle(textarea);
      const fontSize = parseFloat(styles.fontSize);
      const lineHeight = parseFloat(styles.lineHeight) || fontSize * 1.2;
      
      // Estimate character position (simplified calculation)
      const avgCharWidth = fontSize * 0.6; // Approximate character width
      const lines = beforeCursor.split("\n");
      const currentLine = lines.length - 1;
      const currentLineText = lines[lines.length - 1] || "";
      const charPosInLine = currentLineText.length;
      
      // Calculate position
      const x = textareaRect.left + parseFloat(styles.paddingLeft) + (charPosInLine * avgCharWidth);
      const y = textareaRect.top + parseFloat(styles.paddingTop) + (currentLine * lineHeight);
      
      // Position the thick cursor
      this.thickCursor = {
        show: true,
        style: {
          position: "fixed",
          left: `${x}px`,
          top: `${y}px`,
          width: "4px",
          height: `${lineHeight}px`,
          backgroundColor: getColorValue("Dropline") || "#1976D2",
          zIndex: 9999,
          borderRadius: "2px",
          animation: "blink 1s infinite"
        }
      };
      
      // Hide thick cursor after 500ms
      setTimeout(() => {
        this.thickCursor.show = false;
      }, 500);
    },

    clearInsertionHighlight() {
      if (this.highlightedElement) {
        console.log("🎨 Clearing highlight from:", this.highlightedElement.className);

        // Restore original styles if they were stored
        if (this.highlightedElement._originalStyles) {
          const original = this.highlightedElement._originalStyles;
          this.highlightedElement.style.backgroundColor = original.backgroundColor;
          this.highlightedElement.style.border = original.border;
          this.highlightedElement.style.boxShadow = original.boxShadow;
          this.highlightedElement.style.transform = original.transform;
          this.highlightedElement.style.transition = original.transition;
          delete this.highlightedElement._originalStyles;
        } else {
          // Fallback to removing properties
          this.highlightedElement.style.removeProperty('background-color');
          this.highlightedElement.style.removeProperty('border');
          this.highlightedElement.style.removeProperty('transition');
          this.highlightedElement.style.removeProperty('box-shadow');
          this.highlightedElement.style.removeProperty('transform');
        }

        this.highlightedElement = null;
      }
      // Also clear thick cursor
      this.thickCursor.show = false;

      // Clear cursor position highlight if it exists
      this.clearCursorPositionHighlight();
    },

    // Clean up any leftover cursor characters (█) from textarea content
    cleanupCursorCharacters() {
      console.log("🧹 STARTING cleanupCursorCharacters");

      // Get all textareas in the component
      const textareas = document.querySelectorAll('textarea');
      let totalCleaned = 0;

      textareas.forEach((textarea, index) => {
        const originalValue = textarea.value;
        const cursorChar = '█';

        if (originalValue && originalValue.includes(cursorChar)) {
          // Remove all cursor characters
          const cleanedValue = originalValue.replace(new RegExp(cursorChar, 'g'), '');
          const removedCount = originalValue.length - cleanedValue.length;

          // Update textarea value
          textarea.value = cleanedValue;

          // Trigger input event to notify Vue of the change
          textarea.dispatchEvent(new Event('input', { bubbles: true }));

          console.log(`🧹 Cleaned ${removedCount} cursor character(s) from textarea ${index + 1}`);
          totalCleaned += removedCount;
        }
      });

      // Also check for cursor characters that might be styled yellow using CSS
      const yellowCursors = document.querySelectorAll('.yellow-cursor-char');
      yellowCursors.forEach((element, index) => {
        const text = element.textContent;
        if (text === '█' || (text && text.includes('█'))) {
          element.remove();
          console.log(`🧹 Removed yellow-styled cursor element ${index + 1}`);
          totalCleaned++;
        }
      });

      if (totalCleaned > 0) {
        console.log(`🧹✅ Cleaned up ${totalCleaned} cursor character(s) total`);
      } else {
        console.log("🧹 No cursor characters found to clean up");
      }
    },

    // Add keyboard event handler to manually delete cursor characters
    handleCursorCharacterKeydown(event) {
      // If user presses Backspace or Delete while cursor character is present
      if (event.key === 'Backspace' || event.key === 'Delete') {
        const textarea = event.target;
        const cursorChar = '█';

        if (textarea && textarea.value && textarea.value.includes(cursorChar)) {
          console.log("🎹 Detected cursor character during delete - cleaning up");

          // Small delay to let the delete operation complete first
          setTimeout(() => {
            this.cleanupCursorCharacters();
          }, 10);
        }
      }
    },

    addCursorPositionHighlight(element) {
      console.log("🎯🔥 STARTING addCursorPositionHighlight - CLEARING ANY EXISTING FIRST");

      // CRITICAL: Clear any existing cursor highlights immediately before creating new one
      this.clearCursorPositionHighlight();

      console.log("🎯 Adding cursor position highlight within paragraph");

      // Find the textarea within the paragraph
      const textarea = element.querySelector('textarea');
      if (!textarea) {
        console.warn("🎯 No textarea found in element");
        return;
      }

      // Get current cursor position
      const cursorPosition = textarea.selectionStart || 0;
      console.log("🎯 Cursor position:", cursorPosition);

      // Store original text value
      const originalText = textarea.value;
      const textBeforeCursor = originalText.substring(0, cursorPosition);
      const textAfterCursor = originalText.substring(cursorPosition);

      // Insert a visible cursor character at the cursor position to displace text
      const cursorChar = '█'; // Block character that will be replaced with styled element
      const textWithCursor = textBeforeCursor + cursorChar + textAfterCursor;

      // Temporarily update the textarea to get exact positioning
      textarea.value = textWithCursor;

      // Force textarea to update its display
      textarea.dispatchEvent(new Event('input', { bubbles: true }));

      // Set cursor position to the inserted cursor character
      textarea.setSelectionRange(cursorPosition, cursorPosition + 1);

      // Focus the textarea to ensure selection works
      textarea.focus();
      textarea.setSelectionRange(cursorPosition, cursorPosition + 1);

      // Create a temporary span inside the textarea's parent to measure position
      const textareaRect = textarea.getBoundingClientRect();
      const textareaStyles = window.getComputedStyle(textarea);

      // Calculate character width and line height from textarea styles
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      context.font = `${textareaStyles.fontWeight} ${textareaStyles.fontSize} ${textareaStyles.fontFamily}`;
      const charWidth = context.measureText('W').width; // Use 'W' for consistent width
      const lineHeight = parseFloat(textareaStyles.lineHeight) || parseFloat(textareaStyles.fontSize) * 1.2;

      // Count lines and character position
      const lines = textBeforeCursor.split('\n');
      const currentLine = lines.length - 1;
      const charPositionInLine = lines[lines.length - 1].length;

      // Calculate exact position within textarea
      const paddingLeft = parseFloat(textareaStyles.paddingLeft) || 8;
      const paddingTop = parseFloat(textareaStyles.paddingTop) || 4;

      const cursorX = textareaRect.left + paddingLeft + (charPositionInLine * charWidth);
      const cursorY = textareaRect.top + paddingTop + (currentLine * lineHeight);

      // IMPROVED APPROACH: Replace the character with a styled span
      // Instead of trying to style the character in textarea, replace it with a visible element

      // First, restore original text immediately (don't keep the character in textarea)
      textarea.value = originalText;
      textarea.setSelectionRange(cursorPosition, cursorPosition);
      textarea.dispatchEvent(new Event('input', { bubbles: true }));

      // Now create a positioned yellow cursor that overlays the exact character position
      console.log("🎨 Creating positioned yellow cursor overlay at exact character location");

      // FORCE YELLOW COLOR FOR CURSOR HIGHLIGHT
      const finalYellowColor = '#FFEB3B'; // Bright yellow

      console.log("🎨🟡 Using CSS-based styling for cursor character:", {
        finalYellowColor,
        approach: 'direct-character-styling'
      });

      // Create BRIGHT YELLOW cursor highlight that's impossible to miss
      const cursorHighlight = document.createElement('div');
      cursorHighlight.className = 'cursor-position-highlight yellow-cursor-char';
      cursorHighlight.style.position = 'absolute';
      cursorHighlight.style.left = `${cursorX + window.scrollX}px`;
      cursorHighlight.style.top = `${cursorY + window.scrollY}px`;
      cursorHighlight.style.width = `${charWidth}px`;
      cursorHighlight.style.height = `${lineHeight}px`;

      // FORCE MAXIMUM YELLOW VISIBILITY
      cursorHighlight.style.backgroundColor = '#FFFF00'; // Pure bright yellow
      cursorHighlight.style.color = '#000000'; // Black text for contrast
      cursorHighlight.style.border = '2px solid #FFD700'; // Gold border
      cursorHighlight.style.borderRadius = '3px';
      cursorHighlight.style.zIndex = '10000'; // Higher z-index
      cursorHighlight.style.pointerEvents = 'none';
      cursorHighlight.style.boxShadow = '0 0 12px #FFFF00, inset 0 0 12px #FFD700'; // Double glow

      // Blinking animation to make it super obvious
      cursorHighlight.style.animation = 'yellowCursorBlink 0.8s ease-in-out infinite alternate';

      cursorHighlight.style.fontSize = textareaStyles.fontSize;
      cursorHighlight.style.lineHeight = `${lineHeight}px`;
      cursorHighlight.style.display = 'flex';
      cursorHighlight.style.alignItems = 'center';
      cursorHighlight.style.justifyContent = 'center';
      cursorHighlight.style.fontWeight = 'bold';
      cursorHighlight.style.fontFamily = 'monospace';

      // Use the block character for maximum visibility
      cursorHighlight.textContent = '█'; // Block character that's actually yellow

      // Remove any existing animation styles first
      const existingStyle = document.getElementById('cursor-highlight-animation');
      if (existingStyle) {
        existingStyle.remove();
      }

      // Add CSS animation with FORCED YELLOW COLOR
      const style = document.createElement('style');
      style.id = 'cursor-highlight-animation';
      style.textContent = `
        @keyframes rapidFlash {
          0% {
            opacity: 0.3;
            transform: scale(1);
            background-color: ${finalYellowColor} !important;
            border-color: ${finalYellowColor} !important;
            box-shadow: 0 0 8px ${finalYellowColor} !important;
          }
          100% {
            opacity: 1;
            transform: scale(1.1);
            background-color: ${finalYellowColor} !important;
            border-color: ${finalYellowColor} !important;
            box-shadow: 0 0 12px ${finalYellowColor} !important;
          }
        }
      `;
      document.head.appendChild(style);

      // Add to body for absolute positioning
      document.body.appendChild(cursorHighlight);

      // Store reference for cleanup
      this.cursorPositionHighlight = cursorHighlight;

      console.log("🎯 Cursor position highlight created at:", {
        left: `${cursorX}px`,
        top: `${cursorY}px`,
        cursorPosition: cursorPosition,
        line: currentLine,
        charInLine: charPositionInLine,
        charWidth: charWidth,
        lineHeight: lineHeight
      });

      // Remove highlight after 1000ms as requested
      this.cursorPositionTimeout = setTimeout(() => {
        this.clearCursorPositionHighlight();
        console.log("🎯 Cursor position highlight automatically cleared after 1000ms");
      }, 1000);
    },

    clearCursorPositionHighlight() {
      console.log("🎯🔥 STARTING clearCursorPositionHighlight - AGGRESSIVE CLEANUP");

      // Clear the timeout if it exists
      if (this.cursorPositionTimeout) {
        clearTimeout(this.cursorPositionTimeout);
        this.cursorPositionTimeout = null;
        console.log("🎯✅ Cleared cursor position timeout");
      } else {
        console.log("🎯⚠️ No timeout to clear");
      }

      // Remove the highlight element if it exists
      if (this.cursorPositionHighlight) {
        console.log("🎯🔥 Found cursorPositionHighlight element, attempting removal...");
        console.log("🎯📍 Element details:", {
          nodeName: this.cursorPositionHighlight.nodeName,
          className: this.cursorPositionHighlight.className,
          parentNode: this.cursorPositionHighlight.parentNode ? 'exists' : 'missing',
          isConnected: this.cursorPositionHighlight.isConnected
        });

        let removed = false;

        // Method 1: Check if element is still in the DOM
        if (this.cursorPositionHighlight.parentNode) {
          try {
            this.cursorPositionHighlight.parentNode.removeChild(this.cursorPositionHighlight);
            removed = true;
            console.log("🎯✅ Removed via parentNode.removeChild");
          } catch (error) {
            console.warn("🎯❌ parentNode.removeChild failed:", error);
          }
        }

        // Method 2: Try direct remove() method
        if (!removed) {
          try {
            this.cursorPositionHighlight.remove();
            removed = true;
            console.log("🎯✅ Removed via element.remove()");
          } catch (error) {
            console.warn("🎯❌ element.remove() failed:", error);
          }
        }

        // Method 3: Try document.body.removeChild as fallback
        if (!removed) {
          try {
            document.body.removeChild(this.cursorPositionHighlight);
            removed = true;
            console.log("🎯✅ Removed via document.body.removeChild");
          } catch (error) {
            console.warn("🎯❌ document.body.removeChild failed:", error);
          }
        }

        // Clear the reference regardless
        this.cursorPositionHighlight = null;
        console.log("🎯✅ Cleared cursorPositionHighlight reference");

        if (!removed) {
          console.error("🎯💥 FAILED TO REMOVE ELEMENT - ALL METHODS FAILED!");
        }
      } else {
        console.log("🎯⚠️ No cursorPositionHighlight element to clear");
      }

      // NUCLEAR OPTION: Find and destroy ALL cursor highlight elements by class
      const existingHighlights = document.querySelectorAll('.cursor-position-highlight');
      console.log("🎯🧹 NUCLEAR CLEANUP: Found", existingHighlights.length, "elements with cursor-position-highlight class");

      existingHighlights.forEach((element, index) => {
        try {
          console.log(`🎯🧹 Removing element ${index + 1}/${existingHighlights.length}`);
          element.remove();
          console.log(`🎯✅ Successfully removed element ${index + 1}`);
        } catch (error) {
          console.error(`🎯❌ Failed to remove element ${index + 1}:`, error);
          // Try alternative removal
          try {
            if (element.parentNode) {
              element.parentNode.removeChild(element);
              console.log(`🎯✅ Alternative removal successful for element ${index + 1}`);
            }
          } catch (altError) {
            console.error(`🎯💥 Alternative removal also failed for element ${index + 1}:`, altError);
          }
        }
      });

      // Remove any CSS animations that might be keeping references
      const styleElement = document.getElementById('cursor-highlight-animation');
      if (styleElement) {
        try {
          styleElement.remove();
          console.log("🎯🧹 Removed cursor highlight animation styles");
        } catch (error) {
          console.warn("🎯⚠️ Failed to remove animation styles:", error);
        }
      }

      console.log("🎯🏁 clearCursorPositionHighlight COMPLETE");
    },

    // AssetID Management Methods
    async requestNewEpisodeAssetID() {
      try {
        console.log('🆔 Requesting new Episode AssetID...');

        // Get current episode AssetID from metadata or fallback
        const currentEpisodeAssetID = this.currentEpisodeMetadata?.AssetID || this.currentEpisodeMetadata?.asset_id;

        if (!currentEpisodeAssetID) {
          alert('No episode AssetID found. Please ensure the episode is properly loaded.');
          return;
        }

        // Call the regeneration endpoint
        const response = await fetch('/assetid/regenerate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          },
          body: JSON.stringify({
            old_asset_id: currentEpisodeAssetID,
            entity_type: 'episode',
            reason: 'user_requested_episode_regeneration',
            context: {
              episode_number: this.currentEpisode,
              source: 'content_editor_more_options'
            }
          })
        });

        if (!response.ok) {
          throw new Error(`Failed to regenerate AssetID: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        alert(`Episode AssetID successfully regenerated!\n\nOld: ${result.old_asset_id}\nNew: ${result.new_asset_id}\n\nThe episode will be updated automatically.`);

        // Emit event to parent to update episode metadata
        this.$emit('asset-id-regenerated', {
          type: 'episode',
          old_asset_id: result.old_asset_id,
          new_asset_id: result.new_asset_id
        });

        console.log('✅ Episode AssetID regenerated:', result);

        // Refresh all AssetID displays
        await this.refreshAllAssetIDDisplays('episode', result.old_asset_id, result.new_asset_id);

      } catch (error) {
        console.error('❌ Failed to regenerate Episode AssetID:', error);
        alert(`Failed to regenerate Episode AssetID: ${error.message}`);
      }
    },

    // Regenerate AssetID for currently focused cue block (Alt+Shift+A hotkey)
    async regenerateCurrentCueAssetID() {
      try {
        console.log('🆔 Alt+Shift+A: Regenerating current cue AssetID...');

        // Find the currently focused cue block by analyzing cursor position
        const currentCue = this.getCurrentCueAtCursor();

        if (!currentCue) {
          alert('No cue block found at cursor position. Please place cursor within a cue block (e.g., [IMG id="..."] or <img cue=...>)');
          return;
        }

        console.log('Found cue for regeneration:', currentCue);

        // Call the regeneration endpoint
        const response = await fetch('/assetid/regenerate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          },
          body: JSON.stringify({
            old_asset_id: currentCue.assetId,
            entity_type: 'cue',
            reason: 'user_requested_cue_regeneration_hotkey',
            context: {
              cue_type: currentCue.type,
              episode_number: this.currentEpisode,
              source: 'alt_shift_a_hotkey',
              parent_item_asset_id: this.item?.asset_id
            }
          })
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ Cue AssetID regenerated successfully:', result);

        // Update the cue in the content with the new AssetID
        this.updateCueAssetIdInContent(currentCue, result.new_asset_id);

        // Refresh all AssetID displays
        await this.refreshAllAssetIDDisplays('cue', result.old_asset_id, result.new_asset_id);

        // Show success message
        alert(`Cue AssetID regenerated successfully!\nOld: ${result.old_asset_id}\nNew: ${result.new_asset_id}`);

      } catch (error) {
        console.error('❌ Failed to regenerate Cue AssetID:', error);
        alert(`Failed to regenerate Cue AssetID: ${error.message}`);
      }
    },

    // Find the cue block at the current cursor position
    getCurrentCueAtCursor() {
      // Get the currently active textarea (script or code mode)
      let activeTextarea = null;
      let content = '';

      if (this.editorMode === 'script') {
        // In script mode, check if we're in a speaker textarea or main content
        activeTextarea = document.activeElement;
        if (activeTextarea && activeTextarea.tagName === 'TEXTAREA') {
          content = activeTextarea.value;
        } else {
          // Fallback to script content
          content = this.scriptContent || '';
        }
      } else if (this.editorMode === 'code') {
        // In code mode, use script content
        content = this.scriptContent || '';
      } else {
        console.log('❌ Alt+Shift+A only works in Script or Code mode');
        return null;
      }

      if (!content) {
        console.log('❌ No content found in current editor mode');
        return null;
      }

      // Get cursor position
      let cursorPosition = 0;
      if (activeTextarea && typeof activeTextarea.selectionStart === 'number') {
        cursorPosition = activeTextarea.selectionStart;
      }

      // Find cue blocks near cursor position
      const cuePatterns = [
        // Markdown-style cues: [IMG id="ASSETID"]
        /\[(\w+)\s+id=["']([^"']+)["']\]/g,
        // HTML-style cues: <img cue="ASSETID" type="IMG">
        /<(\w+)\s+cue=["']([^"']+)["'][^>]*>/g,
        // Alternative patterns as needed
      ];

      for (const pattern of cuePatterns) {
        pattern.lastIndex = 0; // Reset regex
        let match;

        while ((match = pattern.exec(content)) !== null) {
          const matchStart = match.index;
          const matchEnd = match.index + match[0].length;

          // Check if cursor is within this cue block (with some tolerance)
          if (cursorPosition >= matchStart - 10 && cursorPosition <= matchEnd + 10) {
            return {
              type: match[1].toUpperCase(),
              assetId: match[2],
              fullMatch: match[0],
              start: matchStart,
              end: matchEnd,
              pattern: pattern
            };
          }
        }
      }

      console.log('❌ No cue block found near cursor position:', cursorPosition);
      return null;
    },

    // Update the cue AssetID in the content
    updateCueAssetIdInContent(cueInfo, newAssetId) {
      // Both Script and Code modes use scriptContent as single source of truth
      const content = this.scriptContent || '';

      // Replace the old AssetID with the new one in the matched pattern
      const updatedContent = content.substring(0, cueInfo.start) +
                            cueInfo.fullMatch.replace(cueInfo.assetId, newAssetId) +
                            content.substring(cueInfo.end);

      // Update the content (works for both Script and Code modes)
      this.$emit('update:scriptContent', updatedContent);

      console.log('✅ Updated cue AssetID in content:', cueInfo.assetId, '→', newAssetId);
    },

    // Comprehensive refresh system for all AssetID displays
    async refreshAllAssetIDDisplays(entityType, oldAssetId, newAssetId) {
      console.log(`🔄 Refreshing all AssetID displays: ${entityType} ${oldAssetId} → ${newAssetId}`);

      try {
        // 1. Emit to parent components for episode/rundown refreshes
        this.$emit('assetid-regenerated', {
          entityType: entityType,
          oldAssetId: oldAssetId,
          newAssetId: newAssetId,
          timestamp: new Date().toISOString()
        });

        // 2. Force reload episode metadata if it's an episode AssetID
        if (entityType === 'episode') {
          this.$emit('reload-episode-metadata', {
            newAssetId: newAssetId,
            reason: 'assetid_regenerated'
          });
        }

        // 3. Force rundown reload to refresh item AssetIDs in rundown panel
        if (entityType === 'segment' || entityType === 'episode') {
          this.$emit('reload-rundown', {
            reason: 'assetid_regenerated',
            affectedAssetId: newAssetId
          });
        }

        // 4. Trigger reactive updates for any watched properties
        await this.$nextTick();

        // 5. Emit global event for any other components listening
        if (window.eventBus) {
          window.eventBus.emit('assetid-refreshed', {
            entityType,
            oldAssetId,
            newAssetId
          });
        }

        console.log('✅ AssetID display refresh completed');

      } catch (error) {
        console.error('❌ Error during AssetID display refresh:', error);
      }
    },

    async showAssetIDInfo() {
      try {
        console.log('🆔 Showing AssetID info...');

        // Get current episode AssetID
        const episodeAssetID = this.currentEpisodeMetadata?.AssetID || this.currentEpisodeMetadata?.asset_id;
        const currentItemAssetID = this.currentItemMetadata?.AssetID || this.currentItemMetadata?.asset_id;

        let infoText = '🆔 Current AssetID Information:\n\n';

        if (episodeAssetID) {
          infoText += `📺 Episode AssetID: ${episodeAssetID}\n`;
        } else {
          infoText += `📺 Episode AssetID: Not found\n`;
        }

        if (currentItemAssetID) {
          infoText += `📝 Current Item AssetID: ${currentItemAssetID}\n`;
        } else {
          infoText += `📝 Current Item AssetID: No item selected\n`;
        }

        infoText += `\n📚 Episode: ${this.currentEpisode || 'Unknown'}`;

        alert(infoText);

      } catch (error) {
        console.error('❌ Failed to show AssetID info:', error);
        alert(`Failed to show AssetID info: ${error.message}`);
      }
    },

    // Toggle script reading (start or stop)
    toggleScriptReading() {
      if (this.isReadingScript) {
        this.stopReading();
      } else {
        this.startReadingScript();
      }
    },

    // Start reading the script from the beginning
    async startReadingScript() {
      if (!this.isXttsConfigured) {
        console.error('XTTS is not configured');
        return;
      }

      if (this.readableParagraphs.length === 0) {
        console.warn('No readable paragraphs found in script');
        return;
      }

      console.log('🔊 Starting script reading');
      this.isReadingScript = true;
      this.currentReadingIndex = 0;

      // Create audio element if it doesn't exist
      if (!this.audioElement) {
        this.audioElement = new Audio();
        this.audioElement.addEventListener('ended', this.handleAudioEnd);
        this.audioElement.addEventListener('error', this.handleAudioError);
      }

      // Start reading first paragraph
      await this.readCurrentParagraph();
    },

    // Read the current paragraph
    async readCurrentParagraph() {
      if (this.currentReadingIndex >= this.readableParagraphs.length) {
        console.log('🔊 Finished reading all paragraphs');
        this.stopReading();
        return;
      }

      const paragraph = this.readableParagraphs[this.currentReadingIndex];
      console.log(`🔊 Reading paragraph ${this.currentReadingIndex}:`, paragraph.content.substring(0, 50) + '...');

      try {
        // Request audio from XTTS
        // Note: Don't pass speaker - paragraph.speaker is a UI code (e.g., 'josh')
        // not an XTTS speaker name. Let XTTS use its configured default speaker.
        const audioBlob = await this.xttsInstance.synthesizeSpeech(paragraph.content);

        // Create object URL and play audio
        const audioUrl = URL.createObjectURL(audioBlob);
        this.audioElement.src = audioUrl;
        await this.audioElement.play();

        console.log(`🔊 Playing audio for paragraph ${this.currentReadingIndex}`);
      } catch (error) {
        console.error('Failed to synthesize or play audio:', error);
        // Continue to next paragraph on error
        this.currentReadingIndex++;
        if (this.isReadingScript) {
          setTimeout(() => this.readCurrentParagraph(), 100);
        }
      }
    },

    // Handle audio end event (move to next paragraph)
    handleAudioEnd() {
      console.log(`🔊 Finished playing paragraph ${this.currentReadingIndex}`);

      // Clean up the object URL
      if (this.audioElement && this.audioElement.src) {
        URL.revokeObjectURL(this.audioElement.src);
      }

      // Move to next paragraph
      this.currentReadingIndex++;

      // Read next paragraph if still reading
      if (this.isReadingScript) {
        setTimeout(() => this.readCurrentParagraph(), 500); // 500ms pause between paragraphs
      }
    },

    // Handle audio error
    handleAudioError(error) {
      console.error('Audio playback error:', error);
      // Try next paragraph
      this.currentReadingIndex++;
      if (this.isReadingScript) {
        setTimeout(() => this.readCurrentParagraph(), 100);
      }
    },

    // Stop reading the script
    stopReading() {
      console.log('🔊 Stopping script reading');
      this.isReadingScript = false;

      // Stop and clean up audio
      if (this.audioElement) {
        this.audioElement.pause();
        if (this.audioElement.src) {
          URL.revokeObjectURL(this.audioElement.src);
        }
        this.audioElement.src = '';
      }

      this.currentReadingIndex = 0;
    },

    // Toggle contextual reading (Ctrl+Shift+R hotkey)
    toggleContextualReading() {
      if (this.isReadingScript) {
        this.stopReading();
      } else {
        this.startContextualReading();
      }
    },

    // Start contextual reading based on what's highlighted
    async startContextualReading() {
      if (!this.isXttsConfigured) {
        console.error('XTTS is not configured');
        return;
      }

      const context = this.getReadingContext();
      if (!context) {
        console.warn('No content to read');
        return;
      }

      console.log('🔊 Starting contextual reading:', context);
      this.isReadingScript = true;

      try {
        // Build announcement text
        const announcement = this.buildAnnouncementText(context);

        // Play announcement with "alloy" voice (or fallback)
        await this.playAnnouncement(announcement);

        // Play content with user's preferred voice
        await this.playContent(context.content);

        console.log('✅ Contextual reading complete');
      } catch (error) {
        console.error('❌ Contextual reading failed:', error);
      } finally {
        this.stopReading();
      }
    },

    // Determine what's currently selected/highlighted
    getReadingContext() {
      // Check if a specific segment is selected via selectedSegmentIndex
      if (this.selectedSegmentIndex !== null && this.selectedSegmentIndex >= 0) {
        const segment = this.scriptSegments[this.selectedSegmentIndex];
        return {
          type: 'segment',
          index: this.selectedSegmentIndex,
          content: this.processContentForReading(segment.content),
          speaker: segment.speaker
        };
      }

      // Check if a specific paragraph is focused
      if (this.focusedParagraphIndex !== null && this.focusedParagraphIndex >= 0) {
        const paragraph = this.scriptSegments[this.focusedParagraphIndex];
        return {
          type: 'paragraph',
          index: this.focusedParagraphIndex,
          content: this.processContentForReading(paragraph.content),
          speaker: paragraph.speaker
        };
      }

      // Check if text is selected (could be region or partial)
      const selection = window.getSelection();
      if (selection && selection.toString().trim().length > 0) {
        // Try to detect if this is a region selection by checking for region markers
        const selectedText = selection.toString();
        const regionMatch = selectedText.match(/Block\s+([A-Z])/i);

        if (regionMatch) {
          return {
            type: 'region',
            regionName: regionMatch[1],
            content: this.processContentForReading(selectedText)
          };
        }

        return {
          type: 'selection',
          content: this.processContentForReading(selectedText)
        };
      }

      // Default to reading entire script
      const allContent = this.scriptSegments
        .map(seg => this.processContentForReading(seg.content))
        .join(' ');

      return {
        type: 'all',
        content: allContent
      };
    },

    // Process content for reading (replace cues with placeholder)
    processContentForReading(content) {
      if (!content) return '';

      // Replace cue blocks with "insert cue block here"
      let processed = content.replace(/\[\[CUE:[^\]]+\]\]/g, 'insert cue block here');

      // Clean up any remaining markup
      processed = processed.replace(/<[^>]+>/g, '');

      return processed.trim();
    },

    // Build announcement text based on context
    buildAnnouncementText(context) {
      const episodeNum = this.currentItemMetadata?.episode_number || 'unknown';
      const orderNum = this.currentItemMetadata?.order || 'unknown';
      const slug = this.currentItemMetadata?.slug || 'unknown';

      let announcement = `Beginning XTTS Reading: Episode ${episodeNum}`;

      // Handle different context types
      if (context.type === 'region') {
        // Reading a region/block
        announcement += `, Region: Block ${context.regionName}... begin!`;
      } else if (context.type === 'segment') {
        // Reading an entire segment
        announcement += `, Segment: ${orderNum}, ${slug}... begin!`;
      } else if (context.type === 'paragraph') {
        // Reading a specific paragraph within a segment
        announcement += `, Segment: ${orderNum}, ${slug}, Paragraph ${context.index + 1}... begin!`;
      } else if (context.type === 'selection') {
        // Reading selected text
        announcement += `, Selected text... begin!`;
      } else {
        // Reading entire script
        announcement += `, Full script... begin!`;
      }

      return announcement;
    },

    // Play announcement with shimmer voice
    async playAnnouncement(text) {
      console.log('📢 Playing announcement:', text);

      try {
        // Try to use "shimmer" voice for announcement at 1x speed
        const audioBlob = await this.xttsInstance.synthesizeSpeech(text, {
          speaker: 'shimmer',  // Use shimmer voice for announcements
          speed: 1.0  // Normal speed (1x)
        });

        return new Promise((resolve, reject) => {
          if (!this.audioElement) {
            this.audioElement = new Audio();
          }

          const audioUrl = URL.createObjectURL(audioBlob);
          this.audioElement.src = audioUrl;

          this.audioElement.onended = () => {
            URL.revokeObjectURL(audioUrl);
            resolve();
          };

          this.audioElement.onerror = (e) => {
            URL.revokeObjectURL(audioUrl);
            reject(e);
          };

          this.audioElement.play().catch(reject);
        });
      } catch (error) {
        // Fallback: try with default voice if shimmer fails
        console.warn('⚠️ Shimmer voice failed, using default:', error.message);
        const audioBlob = await this.xttsInstance.synthesizeSpeech(text, {
          speed: 1.0
        });

        return new Promise((resolve, reject) => {
          if (!this.audioElement) {
            this.audioElement = new Audio();
          }

          const audioUrl = URL.createObjectURL(audioBlob);
          this.audioElement.src = audioUrl;

          this.audioElement.onended = () => {
            URL.revokeObjectURL(audioUrl);
            resolve();
          };

          this.audioElement.onerror = (e) => {
            URL.revokeObjectURL(audioUrl);
            reject(e);
          };

          this.audioElement.play().catch(reject);
        });
      }
    },

    // Play content with user's preferred voice
    async playContent(text) {
      console.log('🔊 Playing content with preferred voice');

      const audioBlob = await this.xttsInstance.synthesizeSpeech(text);

      return new Promise((resolve, reject) => {
        if (!this.audioElement) {
          this.audioElement = new Audio();
        }

        const audioUrl = URL.createObjectURL(audioBlob);
        this.audioElement.src = audioUrl;

        this.audioElement.onended = () => {
          URL.revokeObjectURL(audioUrl);
          resolve();
        };

        this.audioElement.onerror = (e) => {
          URL.revokeObjectURL(audioUrl);
          reject(e);
        };

        this.audioElement.play().catch(reject);
      });
    }
  }
}
</script>

<style scoped>
.editor-panel {
  flex: 1;
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
  height: auto !important;
  max-height: none !important;
  min-height: 100vh !important;
}

/* Override any Vuetify fill-height constraints */
.editor-card.fill-height {
  height: auto !important;
  max-height: none !important;
  min-height: 100vh !important;
}

.editor-card .v-card-text {
  height: auto !important;
  max-height: none !important;
}

.editor-content {
  display: flex;
  flex-direction: column;
  overflow: visible;
  /* Remove overflow: hidden to allow proper scrolling */
}

.editor-content .fill-height {
  min-height: calc(100vh - 150px);
  height: auto;
  max-height: none;
  overflow: visible;
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
  gap: 8px;
  padding: 8px 16px 4px 16px;
  margin: 0 8px;
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
  min-width: 60px;
}

.script-save-button {
  flex: 0 0 auto;
  min-width: 70px;
  height: auto !important;
  align-self: stretch;
  font-size: 12px !important;
  font-weight: 500 !important;
  border-radius: 0 !important;
  padding: 0 8px !important;
}

.script-save-button :deep(.v-btn__content) {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.script-slug-field-inline :deep(.v-field__input),
.script-duration-field-inline :deep(.v-field__input) {
  font-size: 100% !important;
  color: #555555 !important;
  font-weight: 500 !important;
  padding: 6px 8px !important;
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
  padding-top: 8px !important;
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
  height: 36px !important;
  min-height: 36px !important;
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
  min-width: 260px;
}

.autosave-section {
  min-width: 80px;
}

.autosave-status {
  text-align: center;
  line-height: 1.1;
  min-width: 60px;
}

.autoformat-section {
  min-width: 80px;
}

.autoformat-status {
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

/* Toolbar Button Height Consistency */
.xtts-read-btn {
  height: 36px !important;
  min-height: 36px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.metadata-toggle-btn {
  height: 36px !important;
  min-height: 36px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.more-options-btn {
  height: 36px !important;
  min-height: 36px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

/* All toolbar buttons should have consistent height */
.editor-toolbar-sticky .v-btn {
  height: 36px !important;
  min-height: 36px !important;
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

/* Script Mode Container - Allow dynamic height growth */
.script-mode-container {
  height: auto !important;
  max-height: none !important;
  overflow: visible;
}

/* Multi-Selection Toolbar - Fixed Overlay */
.multi-selection-toolbar {
  position: fixed;
  top: 120px; /* Below the main toolbar and header */
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background-color: #e3f2fd;
  border: 1px solid #1976d2;
  border-radius: 4px;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
  max-width: calc(100% - 80px);
}

.selection-info {
  font-weight: 500;
  color: #1976d2;
  flex: 1;
}

/* Visual Script Mode Styling */
.visual-script-container {
  padding: 20px 40px 5em 40px;
  background-color: white;
  font-family: 'Times New Roman', serif;
  font-size: 14px;
  line-height: 1.5;
  height: auto;
  max-height: none;
  overflow: visible;
}

/* Speaker Paragraph Styling */
.speaker-paragraph {
  margin: 2px 0;
  background-color: white;
  cursor: pointer;
  position: relative;
  border: none;
  border-radius: 0;
  transition: none;
}

.speaker-paragraph:hover {
  /* No border or shadow effects */
}

.speaker-paragraph.selected {
  /* No border or shadow effects */
}

.speaker-paragraph.multi-selected {
  /* Fallback colors - actual colors set via inline styles from theme configuration */
  background-color: rgba(251, 140, 0, 0.25) !important; /* warning/selection color at 25% */
  border-left: 6px solid #FB8C00;
  box-shadow: 0 0 0 2px rgba(251, 140, 0, 0.2) !important;
}

/* Make textarea background transparent when paragraph is multi-selected */
.speaker-paragraph.multi-selected .speaker-textarea,
.speaker-paragraph.multi-selected .speaker-textarea :deep(.v-field),
.speaker-paragraph.multi-selected .speaker-textarea :deep(.v-field__input),
.speaker-paragraph.multi-selected .speaker-textarea :deep(textarea) {
  background-color: transparent !important;
}

/* Blink animation for swapped paragraphs */
@keyframes swapBlink {
  0%, 100% {
    background-color: transparent;
  }
  50% {
    background-color: rgba(76, 175, 80, 0.4);
  }
}

.speaker-paragraph.blinking-swap {
  animation: swapBlink 0.3s ease-in-out 5;
}

/* Exclude speaker header from blink animation */
.speaker-paragraph.blinking-swap .speaker-header {
  background-color: transparent !important;
  animation: none !important;
}

/* Make textarea background transparent during blink animation */
.speaker-paragraph.blinking-swap .speaker-textarea,
.speaker-paragraph.blinking-swap .speaker-textarea :deep(.v-field),
.speaker-paragraph.blinking-swap .speaker-textarea :deep(.v-field__input),
.speaker-paragraph.blinking-swap .speaker-textarea :deep(textarea) {
  background-color: transparent !important;
}

/* Speaker Header */
.speaker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: 300;
  border: none;
  border-bottom: 2px solid;
  border-radius: 0;
  background-color: transparent;
}

.speaker-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.speaker-icon {
  opacity: 0.9;
  color: #1565C0;
}

.speaker-name {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Helvetica Light', 'Helvetica', sans-serif;
  font-weight: 600;
  font-size: 1.5em;
}

.paragraph-actions {
  display: flex;
  gap: 2px;
  opacity: 0.8;
}

.action-btn {
  color: #1565C0 !important;
  font-family: 'Helvetica', sans-serif;
  font-size: 0.7rem;
  padding: 2px 6px;
  min-width: auto;
}

.action-btn:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.delete-btn:hover {
  background-color: rgba(244, 67, 54, 0.2) !important;
}

/* Paragraph content with proper padding and background */
.paragraph-content {
  padding: 5px 0;
  border-radius: 0;
  position: relative;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

/* Line numbers column */
.line-numbers-column {
  flex-shrink: 0;
  width: 45px;
  display: flex;
  flex-direction: column;
  padding-top: 5px;
  user-select: none;
}

.line-number {
  text-align: right;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  line-height: 1.5;
  height: 24px; /* Match textarea line height (16px font * 1.5) */
  padding-right: 8px;
  white-space: nowrap;
}

.speaker-textarea {
  flex: 1;
}

/* Speaker-specific backgrounds - all use light grey */
.speaker-bg-josh,
.speaker-bg-guest,
.speaker-bg-caller,
.speaker-bg-announcer,
.speaker-bg-narrator,
.speaker-bg-host {
  background-color: #fafafa;
}

/* Override speaker backgrounds when focused or saved - must be after speaker-bg classes */
.paragraph-content.paragraph-focused {
  background-color: rgba(255, 235, 59, 0.6) !important; /* Strong yellow when focused */
}

.paragraph-content.paragraph-saved {
  background-color: rgba(33, 150, 243, 0.4) !important; /* Light blue flash on save */
}

/* Force override with more specific selectors */
.paragraph-content.seg-0.paragraph-focused,
.paragraph-content.seg-1.paragraph-focused,
.paragraph-content.seg-2.paragraph-focused,
.paragraph-content.seg-3.paragraph-focused,
.paragraph-content.seg-4.paragraph-focused,
.paragraph-content.seg-5.paragraph-focused,
.paragraph-content.seg-6.paragraph-focused,
.paragraph-content.seg-7.paragraph-focused,
.paragraph-content.seg-8.paragraph-focused,
.paragraph-content.seg-9.paragraph-focused {
  background-color: rgba(255, 235, 59, 0.6) !important;
}

.paragraph-content.paragraph-saved-green {
  background-color: rgba(76, 175, 80, 0.5) !important; /* Green flash on final save confirmation */
}

/* Make textarea background transparent when paragraph is focused/saved to show parent background */
.paragraph-content.paragraph-focused .speaker-textarea,
.paragraph-content.paragraph-focused .speaker-textarea :deep(.v-field),
.paragraph-content.paragraph-focused .speaker-textarea :deep(.v-field__input),
.paragraph-content.paragraph-focused .speaker-textarea :deep(textarea) {
  background-color: transparent !important;
}

.paragraph-content.paragraph-saved .speaker-textarea,
.paragraph-content.paragraph-saved .speaker-textarea :deep(.v-field),
.paragraph-content.paragraph-saved .speaker-textarea :deep(.v-field__input),
.paragraph-content.paragraph-saved .speaker-textarea :deep(textarea) {
  background-color: transparent !important;
}

.paragraph-content.paragraph-saved-green .speaker-textarea,
.paragraph-content.paragraph-saved-green .speaker-textarea :deep(.v-field),
.paragraph-content.paragraph-saved-green .speaker-textarea :deep(.v-field__input),
.paragraph-content.paragraph-saved-green .speaker-textarea :deep(textarea) {
  background-color: transparent !important;
}

/* Paragraph hover action buttons */
.paragraph-delete-btn {
  position: absolute !important;
  right: -10px;
  top: 50%;
  transform: translateY(-50%);
  background-color: #f44336 !important;
  color: white !important;
  opacity: 0;
  animation: fadeIn 0.2s ease-in forwards;
  z-index: 10;
  width: 18px !important;
  height: 18px !important;
  border-radius: 50% !important;
  min-width: 18px !important;
  padding: 0 !important;
}

.paragraph-add-btn {
  position: absolute !important;
  left: 50%;
  bottom: -10px;
  transform: translateX(-50%);
  background-color: #2196f3 !important;
  color: white !important;
  opacity: 0;
  animation: fadeIn 0.2s ease-in forwards;
  z-index: 10;
  width: 18px !important;
  height: 18px !important;
  border-radius: 50% !important;
  min-width: 18px !important;
  padding: 0 !important;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 0.9;
  }
}

.paragraph-delete-btn:hover,
.paragraph-add-btn:hover {
  opacity: 1 !important;
}

/* Clean textarea styling */
.speaker-textarea {
  font-family: 'Helvetica', sans-serif;
  font-size: 16px;
  line-height: 1.5;
  padding: 0;
  background-color: #fafafa !important; /* Even lighter gray background */
}

/* Ensure speaker textareas auto-grow without scrollbars */
.speaker-textarea :deep(.v-input__control) {
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.speaker-textarea :deep(.v-field) {
  background-color: #fafafa !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  /* All height constraints removed - JavaScript controls everything */
}

.speaker-textarea :deep(.v-field__field) {
  /* All height constraints removed - JavaScript controls everything */
}

/* Remove any Vuetify overlays or pseudo-elements that might cause fading */
.speaker-textarea :deep(.v-field__overlay) {
  display: none !important;
}

.speaker-textarea :deep(.v-field::before),
.speaker-textarea :deep(.v-field::after) {
  display: none !important;
  opacity: 0 !important;
}

.speaker-textarea :deep(.v-field__outline) {
  display: none !important;
}

.speaker-textarea :deep(.v-field__input) {
  padding: 5px !important;
  background-color: #fafafa !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  /* All height constraints removed - JavaScript controls everything */
}

.speaker-textarea :deep(textarea) {
  resize: none !important;
  box-sizing: border-box !important;
  background-color: #fafafa !important;
  color: #000000 !important;
  font-family: 'Helvetica', sans-serif !important;
  font-size: 16px !important;
  padding: 0 !important;
  line-height: 1.5 !important;
  margin: 0 !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  overflow: hidden !important; /* Hidden to get accurate scrollHeight */
  /* NO height, min-height, or max-height - JavaScript controls all sizing */

  /* Hide scrollbars completely */
  scrollbar-width: none !important; /* Firefox */
  -ms-overflow-style: none !important; /* IE/Edge */
}

/* Hide scrollbar for Chrome/Safari/Opera */
.speaker-textarea :deep(textarea::-webkit-scrollbar) {
  display: none !important;
}

/* Speaker-specific text colors */
.speaker-josh :deep(textarea) {
  color: #000000 !important; /* Black text */
  font-weight: 400; /* Normal weight, not bold */
}

.speaker-guest :deep(textarea) {
  color: #388e3c;
  font-style: italic;
}

.speaker-caller :deep(textarea) {
  color: #f57c00;
  font-weight: 500;
}

.speaker-announcer :deep(textarea) {
  color: #7b1fa2;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 14px;
}

.speaker-narrator :deep(textarea) {
  color: #5d4037;
  font-style: italic;
  font-weight: 400;
}

.speaker-host :deep(textarea) {
  color: #1976d2;
  font-weight: 600;
}

.traditional-script-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-segment {
  margin: 0;
  padding: 0;
}

.text-segment {
  background-color: transparent;
  border: none;
  margin: 0;
  padding: 0;
}

.segment-textarea {
  font-family: 'Roboto', sans-serif !important;
  font-size: 16px !important;
  line-height: 1.6 !important;
  padding: 16px !important;
  min-height: 80px !important;
}

.segment-textarea :deep(.v-field) {
  min-height: 80px !important;
  max-height: none !important;
  overflow: visible !important;
}

.segment-textarea :deep(.v-field__input) {
  min-height: 80px !important;
  max-height: none !important;
  overflow: visible !important;
  padding: 16px !important;
}

.segment-textarea :deep(textarea) {
  font-family: 'Roboto', sans-serif !important;
  font-size: 16px !important;
  line-height: 1.6 !important;
  padding: 16px !important;
  min-height: 80px !important;
  max-height: none !important;
  overflow: hidden !important;
  background-color: white !important;
  border: none !important;
  outline: none !important;
  resize: none !important;
  vertical-align: top !important;
  box-sizing: border-box !important;
}

.cue-segment {
  margin: 16px 0;
}

.add-content-section {
  padding: 16px;
  text-align: center;
  border: 2px dashed rgba(var(--v-theme-outline), 0.3);
  border-radius: 8px;
  background-color: rgba(var(--v-theme-surface-variant), 0.1);
  margin-top: 16px;
}

.add-text-btn {
  border-radius: 24px !important;
  padding: 8px 24px !important;
  font-weight: 500 !important;
}

/* Responsive Design for Visual Mode */
@media (max-width: 600px) {
  .visual-script-container {
    padding: 0 8px 0 8px;
  }

  .content-segment {
    margin-bottom: 12px;
  }

  .segment-textarea :deep(textarea) {
    font-size: 14px !important;
    padding: 12px !important;
  }
}

/* Fluid typing area styles */
.fluid-typing-area {
  margin: 0;
  padding: 0 40px 5em 40px;
  background-color: white;
  font-family: 'Times New Roman', serif;
}

.typing-area {
  border: none;
  background-color: transparent;
  cursor: text;
  margin: 0;
  padding: 0;
}



.typing-textarea {
  font-family: 'Times New Roman', serif !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
  padding: 0 !important;
}

.typing-textarea :deep(.v-input__control) {
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.typing-textarea :deep(.v-field__field) {
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.typing-textarea :deep(.v-field) {
  background-color: transparent !important;
  box-shadow: none !important;
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.typing-textarea :deep(.v-field__input) {
  padding: 0 !important;
  margin: 0 !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
  overflow: visible !important;
}

.typing-textarea :deep(textarea) {
  font-family: 'Times New Roman', serif !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
  padding: 0 !important;
  margin: 0 !important;
  background-color: transparent !important;
  border: none !important;
  outline: none !important;
  resize: none !important;
  min-height: 24px !important;
  max-height: none !important;
  overflow: visible !important;
  color: #000000 !important;
  font-weight: normal !important;
}

.typing-textarea :deep(textarea::placeholder) {
  color: rgba(var(--v-theme-on-surface), 0.4) !important;
  font-style: italic;
}

/* Responsive Design for Typing Area */
@media (max-width: 600px) {
  .auto-text-section {
    margin: 0;
    padding: 6px 0 50vh 0;
    background-color: rgba(var(--v-theme-surface-variant), 0.1);
    min-height: calc(100vh - 200px);
  }

  .typing-area {
    margin: 4px;
  }


  .typing-textarea :deep(textarea) {
    font-size: 14px !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: auto !important;
    max-height: none !important;
    overflow: visible !important;
  }

}

/* Flash Message Styling */
.cue-flash-message {
  z-index: 2000 !important;
}

.cue-flash-message .v-snackbar__wrapper {
  width: 400px !important;
  max-width: 80vw !important;
}

.cue-flash-message .v-snackbar__content {
  font-size: 2rem !important;
  font-weight: 700 !important;
  text-align: center !important;
  padding: 24px !important;
  letter-spacing: 2px !important;
}

/* Yellow cursor character styling */
.yellow-cursor-highlight {
  /* Apply styles that will make the cursor character (█) appear yellow */
  background: linear-gradient(45deg, rgba(255, 235, 59, 0.3), rgba(255, 193, 7, 0.5)) !important;
  text-shadow: 0 0 4px #FFEB3B !important;
  caret-color: #FFEB3B !important;
}

/* Target the cursor character specifically when it appears in yellow-cursor-highlight textareas */
.yellow-cursor-highlight::selection {
  background-color: #FFEB3B !important;
  color: #000000 !important;
}

/* CSS class for styled cursor characters */
.yellow-cursor-char {
  background-color: #FFEB3B !important;
  color: #000000 !important;
  text-shadow: 0 0 3px #FFC107 !important;
  border-radius: 2px !important;
  padding: 0 1px !important;
  animation: cursorBlink 0.5s infinite alternate !important;
  font-weight: bold !important;
}

@keyframes cursorBlink {
  0% {
    background-color: #FFEB3B;
    opacity: 1;
  }
  100% {
    background-color: #FFC107;
    opacity: 0.8;
  }
}

/* High-visibility yellow cursor blinking animation */
@keyframes yellowCursorBlink {
  0% {
    background-color: #FFFF00;
    box-shadow: 0 0 12px #FFFF00, inset 0 0 12px #FFD700;
    opacity: 1;
    transform: scale(1);
  }
  100% {
    background-color: #FFD700;
    box-shadow: 0 0 20px #FFD700, inset 0 0 20px #FFFF00;
    opacity: 0.9;
    transform: scale(1.05);
  }
}

/* Alternative approach: Use CSS to target specific character patterns */
textarea.yellow-cursor-highlight {
  /* This applies special styling when the textarea has the cursor highlighting class */
  background-color: rgba(255, 235, 59, 0.05) !important;
  border: 2px solid #FFEB3B !important;
  box-shadow: 0 0 8px rgba(255, 235, 59, 0.4) !important;
}

/* Fix for fading text issue in v-field__input textareas */
:deep(.v-field__input) {
  padding-top: 16px !important;
  vertical-align: top !important;
  line-height: 1.5 !important;
  box-sizing: border-box !important;
  display: block !important;
}

/* Ensure textarea content is fully visible */
:deep(textarea.v-field__input) {
  padding-top: 16px !important;
  padding-bottom: 12px !important;
  vertical-align: top !important;
  overflow: visible !important;
  min-height: auto !important;
}
</style>
