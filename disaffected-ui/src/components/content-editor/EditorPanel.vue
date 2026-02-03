<template>
  <div :class="['editor-panel-content', !showRundownPanel ? 'full-width' : '']" :style="editorPanelCssVars">
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

    <!-- Segment Locked Overlay -->
    <div v-if="isSegmentLocked" class="segment-locked-overlay">
      <div class="locked-content">
        <v-icon size="48" color="warning">mdi-lock</v-icon>
        <div class="locked-title">Segment Locked</div>
        <div class="locked-message">
          Currently being edited by<br>
          <strong>{{ lockInfo.lockedBy }}</strong>
        </div>
        <div v-if="lockInfo.lockedAt" class="locked-time">
          Started {{ formatRelativeTime(lockInfo.lockedAt) }}
        </div>
      </div>
    </div>

    <v-card class="editor-card" flat>
      <!-- Editor Mode and Controls Toolbar -->
      <v-toolbar density="comfortable" color="grey-lighten-4" class="editor-toolbar-sticky" style="min-height: 48px; padding: 6px 8px;">
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
          <v-btn value="code" size="small" class="mode-btn" rounded="0">
            <v-icon left size="small">mdi-code-braces</v-icon>
            Code
          </v-btn>
        </v-btn-toggle>

        <!-- iPad Mode Button -->
        <v-btn
          size="small"
          class="mode-btn ml-2"
          rounded="0"
          @click="openIpadMode"
          :disabled="!currentEpisodeNumber"
        >
          <v-icon left size="small">mdi-tablet</v-icon>
          iPad Mode
        </v-btn>

        <!-- Collapse Mode Indicator (centered, prominent) -->
        <div v-if="collapseMode && editorMode === 'script'" class="collapse-mode-indicator">
          <v-icon size="small" class="mr-1">mdi-arrow-collapse-vertical</v-icon>
          COLLAPSE MODE
          <v-tooltip activator="parent" location="bottom">
            Press Ctrl+Shift+C to exit collapse mode
          </v-tooltip>
        </div>

        <v-spacer></v-spacer>

        <!-- Save All Button - mirrors main Save All behavior -->
        <v-tooltip :text="saveState.tooltip" location="bottom">
          <template v-slot:activator="{ props }">
            <v-btn
              v-bind="props"
              :color="saveState.buttonColor"
              size="small"
              :variant="saveState.hasChanges ? 'flat' : 'tonal'"
              class="mr-2"
              :disabled="saveState.isDisabled"
              @click="handleSaveAll"
            >
              <v-icon left size="small">{{ saveState.buttonIcon }}</v-icon>
              {{ saveState.buttonText }}
            </v-btn>
          </template>
        </v-tooltip>

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
                  <span class="cue-label">PKG</span>
                  <span class="hotkey-display">[ALT+P]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Package</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex dir-btn"
                :style="getCueButtonStyle('DIR')"
                @click="insertCue('DIR')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">DIR</span>
                  <span class="hotkey-display">[ALT+D]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Director Note</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex bump-btn"
                :style="getCueButtonStyle('BUMP')"
                @click="insertCue('BUMP')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">BUMP</span>
                  <span class="hotkey-display">[ALT+B]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Bumper</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex sting-btn"
                :style="getCueButtonStyle('STING')"
                @click="insertCue('STING')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">STING</span>
                  <span class="hotkey-display">[ALT+T]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Stinger</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex rif-btn"
                :style="getCueButtonStyle('RIF')"
                @click="insertCue('RIF')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">RIF</span>
                  <span class="hotkey-display">[ALT+R]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Riff</v-tooltip>
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
            <span class="formatting-hotkey"><strong>CTRL+ALT+H</strong> Highlight</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>CTRL+S</strong> Save</span>
            <v-divider vertical class="hotkey-divider mx-4"></v-divider>
            <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regenerate Cue AssetID</span>
          </div>

          <!-- Script Content Area with embedded fields -->
          <div class="script-content-container flex-grow-1">
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
              <draggable
                v-model="draggableSegments"
                tag="div"
                :item-key="getSegmentKey"
                :animation="200"
                handle=".drag-handle"
                ghost-class="ghost-segment"
                chosen-class="chosen-segment"
                drag-class="drag-segment"
                @start="handleSegmentDragStart"
                @end="handleSegmentDragEnd"
              >
                <template #item="{ element: segment, index }">
                  <div class="segment-wrapper">
                    <!-- Drop Zone Indicator (before each segment) -->
                    <div
                      v-if="dropZoneActive"
                      class="cue-drop-zone"
                      :class="{ 'drop-zone-selected': selectedDropZone === index }"
                      @click="selectDropZone(index)"
                      @mouseenter="hoveredDropZone = index"
                      @mouseleave="hoveredDropZone = null"
                    >
                      <div class="drop-zone-line"></div>
                      <div class="drop-zone-label">
                        <v-icon size="small">mdi-plus-circle</v-icon>
                        Insert {{ pendingCueType }} here
                      </div>
                    </div>

                    <div class="content-segment">
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
                    <!-- COLLAPSE MODE: Compact single-line paragraph display -->
                    <div v-if="collapseMode" class="collapsed-paragraph" :class="`speaker-bg-${segment.speaker}`">
                      <div class="drag-handle-column drag-handle">
                        <v-icon size="small">mdi-drag</v-icon>
                      </div>
                      <div class="collapsed-paragraph-content">
                        <span class="collapsed-line-range">[{{ getCollapsedLineRange(index) }}]</span>
                        <span class="collapsed-text-left">{{ getCollapsedFirstWords(segment.content) }} ...</span>
                        <span class="collapsed-text-right">... {{ getCollapsedLastWords(segment.content) }}</span>
                      </div>
                      <v-btn
                        icon
                        size="x-small"
                        class="collapsed-delete-btn"
                        @click.stop="deleteSegment(index)"
                      >
                        <v-icon size="16">mdi-close</v-icon>
                      </v-btn>
                    </div>

                    <!-- NORMAL MODE: Full paragraph display -->
                    <template v-else>
                    <!-- Speaker Header -->
                    <div v-if="shouldShowSpeakerHeader(index, segment.speaker)" class="speaker-header" :style="getSpeakerHeaderStyle(segment.speaker)">
                      <div class="speaker-info">
                        <v-icon size="small" class="drag-handle" style="cursor: grab; margin-right: 4px;">
                          mdi-drag-vertical
                          <v-tooltip activator="parent" location="top">Drag to reorder paragraphs</v-tooltip>
                        </v-icon>
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
                      :ref="el => setParagraphRef(index, el)"
                      class="paragraph-content"
                      :class="[
                        `seg-${index}`,
                        `speaker-bg-${segment.speaker}`,
                        {
                          'paragraph-focused': focusedParagraphIndex === index,
                          'paragraph-saved': savedParagraphIndex === index,
                          'paragraph-needs-attention': segment.needsAttention
                        }
                      ]"
                      @mouseenter="hoveredParagraphIndex = index"
                      @mouseleave="hoveredParagraphIndex = null"
                      @click="handleParagraphClick(index, $event)"
                    >
                      <!-- Drag Handle Column (before line numbers) -->
                      <div class="drag-handle-column drag-handle">
                        <v-icon size="small">mdi-drag</v-icon>
                      </div>

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

                      <div
                        :ref="`textareaRef-${index}`"
                        contenteditable="true"
                        v-html="getSegmentContent(index)"
                        @input="handleContentEditableInput(index, $event)"
                        @keydown="handleContentEditableKeydown(index, $event)"
                        @paste="handleContentEditablePaste(index, $event)"
                        @focus="setEditingFlags(index); handleParagraphFocus(index)"
                        @blur="handleParagraphBlur(index)"
                        class="speaker-textarea speaker-contenteditable"
                        :class="`speaker-${segment.speaker}`"
                        :style="getSpeakerTextStyle(segment.speaker)"
                        :data-placeholder="`Enter ${getSpeakerDisplayName(segment.speaker)}'s dialogue here...`"
                      ></div>

                      <!-- Needs Attention Flag (right side, above delete) -->
                      <v-btn
                        v-if="hoveredParagraphIndex === index || segment.needsAttention"
                        icon
                        size="x-small"
                        class="paragraph-flag-btn"
                        :class="{ 'flag-active': segment.needsAttention }"
                        @click.stop="handleFlagClick(index, 'paragraph', segment)"
                        :title="segment.needsAttention ? (isFlagNoteMinimized('paragraph', index) ? 'Expand note' : 'Minimize note') : 'Flag for attention'"
                        tabindex="-1"
                      >
                        <v-icon size="18" :color="segment.needsAttention ? 'orange' : 'grey'">
                          {{ segment.needsAttention ? 'mdi-flag' : 'mdi-flag-outline' }}
                        </v-icon>
                      </v-btn>

                      <!-- Flag Note Panel (teleported to body, positioned dynamically) -->
                      <Teleport to="body">
                        <div
                          v-if="segment.needsAttention && !isFlagNoteMinimized('paragraph', index)"
                          class="flag-note-panel flag-note-teleported"
                          :style="{ ...editorPanelCssVars, ...getFlagNotePanelStyle(index, 'paragraph') }"
                          @click.stop
                        >
                          <div class="flag-note-header">
                            <v-icon size="16" :color="needsAttentionColor" class="mr-1">mdi-flag</v-icon>
                            <span class="flag-note-title">{{ getFirstFourWords(segment.content) }}</span>
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              @click.stop="minimizeFlagNote('paragraph', index)"
                              class="flag-note-minimize"
                              title="Minimize"
                            >
                              <v-icon size="16">mdi-minus</v-icon>
                            </v-btn>
                          </div>
                          <v-textarea
                            :model-value="segment.flagNote || ''"
                            @update:model-value="updateParagraphFlagNote(index, $event)"
                            placeholder="Why does this need attention?"
                            variant="outlined"
                            density="compact"
                            rows="2"
                            auto-grow
                            hide-details
                            class="flag-note-textarea"
                            @click.stop
                          />
                          <div class="flag-note-actions">
                            <v-btn
                              size="small"
                              :color="needsAttentionColor"
                              variant="tonal"
                              @click.stop="resolveFlag(index, 'paragraph')"
                            >
                              <v-icon size="16" start>mdi-check</v-icon>
                              Resolved
                            </v-btn>
                          </div>
                        </div>
                      </Teleport>

                      <!-- Delete Button (right middle) -->
                      <v-btn
                        v-if="hoveredParagraphIndex === index"
                        icon
                        size="x-small"
                        class="paragraph-delete-btn"
                        @click.stop="deleteSegment(index)"
                        tabindex="-1"
                      >
                        <v-icon size="18">mdi-close</v-icon>
                      </v-btn>

                      <!-- Add Paragraph Button (bottom center) -->
                      <v-btn
                        v-if="hoveredParagraphIndex === index"
                        icon
                        size="small"
                        class="paragraph-add-btn"
                        @click.stop="createNewParagraphAfter(index)"
                        tabindex="-1"
                      >
                        <v-icon size="medium">mdi-plus</v-icon>
                      </v-btn>
                    </div>
                    </template>
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
                <div
                  v-else-if="segment.type === 'cue'"
                  class="cue-segment"
                  :class="[
                    `cue-align-${cueCardAlignment}`,
                    { 'cue-focused': focusedCueIndex === index },
                    { 'cue-needs-attention': segment.data?.needsAttention },
                    { 'cue-collapsed': collapseMode }
                  ]"
                  :style="focusedCueIndex === index ? { backgroundColor: highlightBackgroundColor } : {}"
                  :data-pending="segment.isPending || null"
                  tabindex="0"
                  @focus="handleCueFocus(index)"
                  @blur="handleCueBlur(index)"
                  @click="handleCueRowClick(index, $event)"
                  @keydown.enter.prevent="editCue(index, segment.data)"
                  @mouseenter="hoveredCueIndex = index"
                  @mouseleave="hoveredCueIndex = null"
                >
                  <!-- COLLAPSE MODE: Compact cue display -->
                  <div v-if="collapseMode" class="collapsed-cue" :style="getCollapsedCueStyle(segment.data?.type)">
                    <div class="drag-handle-column drag-handle">
                      <v-icon size="small">mdi-drag</v-icon>
                    </div>
                    <div class="collapsed-cue-content">
                      <span v-if="segment.data?.enumerator" class="collapsed-cue-index">#{{ segment.data.enumerator }}</span>
                      <span class="collapsed-cue-type">{{ segment.data?.type || 'CUE' }}</span>
                      <span class="collapsed-cue-divider">|</span>
                      <span class="collapsed-cue-slug">{{ segment.data?.slug || segment.data?.title || '(no slug)' }}</span>
                      <span class="collapsed-cue-divider">|</span>
                      <span class="collapsed-cue-duration">{{ segment.data?.duration || '00:00:00:00' }}</span>
                      <template v-if="segment.data?.outcue || getCollapsedOutcue(segment.data)">
                        <span class="collapsed-cue-divider">|</span>
                        <span class="collapsed-cue-outcue">{{ segment.data?.outcue || getCollapsedOutcue(segment.data) }}</span>
                      </template>
                    </div>
                    <v-btn
                      icon
                      size="x-small"
                      class="collapsed-delete-btn"
                      @click.stop="deleteCue(index)"
                    >
                      <v-icon size="16">mdi-close</v-icon>
                    </v-btn>
                  </div>

                  <!-- NORMAL MODE: Full cue card display -->
                  <template v-else>
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
                    :current-episode="currentEpisode"
                    @select="selectCue(index)"
                    @edit="editCue(index, segment.data)"
                    @delete="deleteCue(index)"
                    @reupload-sot-cue="handleReuploadSotCue"
                    @status-changed="handleSotStatusChange"
                    @update-meta="handleCueFieldUpdate"
                    @edit-fsq="handleEditFsq"
                  />

                  <!-- Needs Attention Flag Button for Cue -->
                  <v-btn
                    v-if="hoveredCueIndex === index || segment.data?.needsAttention"
                    icon
                    size="x-small"
                    class="cue-flag-btn"
                    :class="{ 'flag-active': segment.data?.needsAttention }"
                    @click.stop="handleFlagClick(index, 'cue', segment)"
                    :title="segment.data?.needsAttention ? (isFlagNoteMinimized('cue', index) ? 'Expand note' : 'Minimize note') : 'Flag for attention'"
                    tabindex="-1"
                  >
                    <v-icon size="18" :color="segment.data?.needsAttention ? 'orange' : 'grey'">
                      {{ segment.data?.needsAttention ? 'mdi-flag' : 'mdi-flag-outline' }}
                    </v-icon>
                  </v-btn>

                  <!-- Flag Note Panel for Cue (teleported to body, positioned dynamically) -->
                  <Teleport to="body">
                    <div
                      v-if="segment.data?.needsAttention && !isFlagNoteMinimized('cue', index)"
                      class="flag-note-panel flag-note-teleported"
                      :style="{ ...editorPanelCssVars, ...getFlagNotePanelStyle(index, 'cue') }"
                      @click.stop
                    >
                      <div class="flag-note-header">
                        <v-icon size="16" :color="needsAttentionColor" class="mr-1">mdi-flag</v-icon>
                        <span class="flag-note-title">{{ getCueReference(segment) }}</span>
                        <v-btn
                          icon
                          size="x-small"
                          variant="text"
                          @click.stop="minimizeFlagNote('cue', index)"
                          class="flag-note-minimize"
                          title="Minimize"
                        >
                          <v-icon size="16">mdi-minus</v-icon>
                        </v-btn>
                      </div>
                      <v-textarea
                        :model-value="segment.data?.flagNote || ''"
                        @update:model-value="updateCueFlagNote(index, $event)"
                        placeholder="Why does this need attention?"
                        variant="outlined"
                        density="compact"
                        rows="2"
                        auto-grow
                        hide-details
                        class="flag-note-textarea"
                        @click.stop
                      />
                      <div class="flag-note-actions">
                        <v-btn
                          size="small"
                          :color="needsAttentionColor"
                          variant="tonal"
                          @click.stop="resolveFlag(index, 'cue')"
                        >
                          <v-icon size="16" start>mdi-check</v-icon>
                          Resolved
                        </v-btn>
                      </div>
                    </div>
                  </Teleport>
                  </template>
                </div>
                    </div>
                  </div>
                </template>
              </draggable>

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
                  <span class="cue-label">PKG</span>
                  <span class="hotkey-display">[ALT+P]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Package</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex dir-btn"
                :style="getCueButtonStyle('DIR')"
                @click="insertCue('DIR')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">DIR</span>
                  <span class="hotkey-display">[ALT+D]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Director Note</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex bump-btn"
                :style="getCueButtonStyle('BUMP')"
                @click="insertCue('BUMP')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">BUMP</span>
                  <span class="hotkey-display">[ALT+B]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Bumper</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex sting-btn"
                :style="getCueButtonStyle('STING')"
                @click="insertCue('STING')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">STING</span>
                  <span class="hotkey-display">[ALT+T]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Stinger</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex rif-btn"
                :style="getCueButtonStyle('RIF')"
                @click="insertCue('RIF')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">RIF</span>
                  <span class="hotkey-display">[ALT+R]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Riff</v-tooltip>
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
            <span class="formatting-hotkey"><strong>CTRL+ALT+H</strong> Highlight</span>
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
                      ref="slugFieldRef"
                      :model-value="currentItemMetadata.slug"
                      @update:model-value="updateMetadata('slug', $event)"
                      label="Enter slug first"
                      placeholder="my-segment-slug"
                      variant="outlined"
                      density="comfortable"
                      :rules="slugRules"
                      :class="{ 'slug-needs-attention': !currentItemMetadata.slug || currentItemMetadata.slug.trim().length === 0 }"
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
                  <span class="cue-label">PKG</span>
                  <span class="hotkey-display">[ALT+P]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Package</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex dir-btn"
                :style="getCueButtonStyle('DIR')"
                @click="insertCue('DIR')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">DIR</span>
                  <span class="hotkey-display">[ALT+D]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Director Note</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex bump-btn"
                :style="getCueButtonStyle('BUMP')"
                @click="insertCue('BUMP')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">BUMP</span>
                  <span class="hotkey-display">[ALT+B]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Bumper</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex sting-btn"
                :style="getCueButtonStyle('STING')"
                @click="insertCue('STING')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">STING</span>
                  <span class="hotkey-display">[ALT+T]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Stinger</v-tooltip>
              </v-btn>

              <v-btn
                variant="flat"
                class="cue-btn-flex rif-btn"
                :style="getCueButtonStyle('RIF')"
                @click="insertCue('RIF')"
              >
                <div class="cue-btn-content-flex">
                  <span class="cue-label">RIF</span>
                  <span class="hotkey-display">[ALT+R]</span>
                </div>
                <v-tooltip activator="parent" location="bottom">Riff</v-tooltip>
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
            <span class="formatting-hotkey"><strong>CTRL+ALT+H</strong> Highlight</span>
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

  <!-- IMG Cue Modal - REMOVED: Now handled by ContentEditor.vue -->
  <!-- All IMG cue operations emit to parent via 'show-img-modal' and 'edit-img-cue' events -->

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

  <!-- Cue Placement Overlay - DISABLED: Using draggable ghost segment instead -->
  <!-- <CuePlacementOverlay
    v-model:show="showCuePlacement"
    :cue-type="pendingCueType"
    @place-cue="handleCuePlacement"
    @cancel="cancelCuePlacement"
  /> -->
</template>

<script>
import { getColorValue, resolveVuetifyColor, loadColorsFromDatabase } from '../../utils/themeColorMap.js';
import draggable from 'vuedraggable';
// ImgCueModal - REMOVED: Now handled by ContentEditor.vue
import DeleteImgCueModal from './modals/DeleteImgCueModal.vue';
import ImageCueCard from './cards/ImageCueCard.vue';
import PlaceholderCueCard from './cards/PlaceholderCueCard.vue';
import SpeakerSelectorModal from './modals/SpeakerSelectorModal.vue';
// import CuePlacementOverlay from './CuePlacementOverlay.vue'; // DISABLED: Using draggable ghost segment instead
import CueParser from '../../utils/cueParser.js';
import { useXtts } from '../../composables/useXtts.js';
import { useAsyncAnalysis } from '../../composables/useAsyncAnalysis.js';
import { useRequireEpisode } from '../../composables/useRequireEpisode.js';

export default {
  name: 'EditorPanel',
  components: {
    draggable,
    // ImgCueModal - REMOVED: Now handled by ContentEditor.vue
    DeleteImgCueModal,
    ImageCueCard,
    PlaceholderCueCard,
    SpeakerSelectorModal
    // CuePlacementOverlay // DISABLED: Using draggable ghost segment instead
  },
  setup() {
    // Episode requirement system
    const { requireEpisode } = useRequireEpisode();
    return { requireEpisode };
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
      cueCardAlignment: 'left', // Default alignment, loaded from settings
      currentSegmentSpeaker: 'josh',
      editingSpeakerSegmentIndex: null,
      showCuePlacement: false,
      showSwapErrorDialog: false,
      swapErrorMessage: '',
      blinkingParagraphs: new Set(), // Track paragraphs that are blinking after swap
      pendingCueType: null,
      pendingPlacement: null,
      temporaryEpisode: null, // For episode requirement callback
      pendingCueData: null, // Store IMG cue data for post-modal placement
      useVisualScriptMode: true, // Toggle for visual cue cards vs traditional text - RE-ENABLED, fixing visibility issue
      hoveredParagraphIndex: null, // Track which paragraph is being hovered
      hoveredCueIndex: null, // Track which cue is being hovered (for flag button)
      activeFlagNoteIndex: null, // Track which segment's flag note panel is open
      activeFlagNoteType: null, // 'paragraph' or 'cue' - type of segment with open note
      flagNoteContent: '', // Content of the flag note being edited
      minimizedFlagNotes: {}, // Track which flag notes are minimized (by "type-index" key as object for Vue reactivity)
      paragraphRefs: {}, // Store refs to paragraph elements for flag note positioning
      flagNotePosUpdateTrigger: 0, // Trigger to force position recalculation on scroll
      focusedParagraphIndex: null, // Track which paragraph has focus
      lastKnownParagraphIndex: null, // Persist last focused paragraph for cue insertion (survives blur)
      focusedCueIndex: null, // Track which cue row has focus (for tab navigation)
      savedParagraphIndex: null, // Track paragraph that just saved (for green flash)
      errorParagraphIndex: null, // Track paragraph with save error (for red flash)
      paragraphEditStates: {}, // Track if paragraph has been edited before (for re-edit detection)
      hasLocalUnsavedChanges: false, // Track if script content has unsaved changes
      typingBuffer: '', // Buffer for auto-expanding text input
      autoformatTimer: null, // Timer for periodic autoformat
      autoformatDebounceTimer: null, // Debounce timer for content changes
      slugNeedsAttention: false, // Track if slug field needs user attention (yellow highlight)
      slugFieldFocused: false, // Track if slug field is currently focused
      titleFieldFocused: false, // Track if title field is currently focused
      segmentUpdateTimer: null, // Timer for debouncing segment updates
      lastAutoformatTime: null, // Timestamp of last autoformat run
      altKeyPressed: false, // Manual ALT key tracking for better browser compatibility
      isActivelyTyping: false, // Flag to prevent autoformat during typing
      lastEnterState: {}, // Track Enter key state per segment for double Enter detection
      segmentEditBuffer: {}, // Buffer for segment edits to prevent reactivity race conditions
      updateDebounceTimers: {}, // Debounce timers for each segment to prevent rapid updates
      activelyEditingSegment: null, // Track which segment is being actively typed in (prevents v-html re-render)
      isActivelyEditing: false, // Master flag to block watchers during active editing (prevents cursor loss on autosave)
      isRestoringCursor: false, // Flag to block watchers during cursor restoration
      savedCursorState: null, // Saved cursor position for restoration after autosave { segmentIndex, nodeIndex, offset }
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
      segmentLineCounts: {}, // Cache of line counts per segment for reactivity
      isDragging: false, // Track if segment is being dragged
      pendingSegmentOrder: null, // Store reordered segments during drag (processed after drag ends)
      cachedScriptSegments: null, // Cache parsed segments to maintain object stability during drag
      lastParsedContent: null, // Track when content changes to invalidate cache
      pendingFocusSegmentIndex: null, // Index of segment to focus after next render
      // Drop zone state for cue insertion
      dropZoneActive: false, // Whether drop zones are visible for cue insertion
      selectedDropZone: null, // Which drop zone is currently selected (index)
      hoveredDropZone: null, // Which drop zone is currently hovered (index)
      // Generic flag to block @update:model-value handlers during programmatic operations
      // Set this to true when performing operations that shouldn't trigger reactive updates
      // Use cases: creating paragraphs, merging paragraphs, bulk operations, etc.
      blockReactiveUpdates: false,
      // Scroll position preservation for paragraph splitting
      savedScrollPosition: undefined,
      savedContainerScroll: undefined,
      scrollContainerRef: null,
      scriptContainerRef: null,
      colorLoadTrigger: 0, // Reactive trigger to force re-computation of color-dependent properties
      collapseMode: false // Collapse mode for easier drag-and-drop reordering
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

    // Load colors from database and set drag/drop CSS variables
    loadColorsFromDatabase().then(() => {
      const draglightColorName = getColorValue('draglight') || 'cyan-lighten-4';
      const droplineColorName = getColorValue('dropline') || 'green-lighten-4';
      const draglightColor = resolveVuetifyColor(draglightColorName);
      const droplineColor = resolveVuetifyColor(droplineColorName);

      // Debug: Log needs-attention color
      const needsAttentionColorName = getColorValue('needs-attention');
      const needsAttentionResolved = resolveVuetifyColor(needsAttentionColorName);
      console.log('🚩 Needs-attention color loaded:', {
        colorName: needsAttentionColorName,
        resolvedHex: needsAttentionResolved
      });

      console.log('🎨 Setting drag/drop colors:', {
        draglightColorName,
        droplineColorName,
        draglightColor,
        droplineColor
      });

      document.documentElement.style.setProperty('--draglight-color', draglightColor);
      document.documentElement.style.setProperty('--dropline-color', droplineColor);

      // Increment trigger to force Vue to re-compute color-dependent computed properties
      this.colorLoadTrigger++;
      console.log('🎨 Color load trigger incremented:', this.colorLoadTrigger);
    });

    // Add global hotkey listeners
    console.log('🎪 Adding global hotkey listeners');
    document.addEventListener('keydown', this.handleGlobalKeydown);
    document.addEventListener('keyup', this.handleGlobalKeyup);

    // Reset ALT key state when window loses focus (prevents stuck ALT key)
    window.addEventListener('blur', this.handleWindowBlur);

    // Add keyboard listener for cursor character cleanup
    document.addEventListener('keydown', this.handleCursorCharacterKeydown);

    // Load cue card alignment from settings (do this LAST to avoid reactivity loops)
    this.$nextTick(() => {
      this.loadCueCardAlignment();
    });

    // Add scroll listener for flag note positioning
    window.addEventListener('scroll', this.handleScrollForFlagNotes, true);
  },
  unmounted() {
    // Clean up scroll listener for flag notes
    window.removeEventListener('scroll', this.handleScrollForFlagNotes, true);
    // Clean up event listeners
    document.removeEventListener('keydown', this.handleGlobalKeydown);
    document.removeEventListener('keyup', this.handleGlobalKeyup);
    document.removeEventListener('keydown', this.handleCursorCharacterKeydown);
    window.removeEventListener('blur', this.handleWindowBlur);
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
    // CRITICAL: Flush any pending changes before unmount to prevent data loss
    this.flushPendingChanges();

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

    // Watch for item changes to clear edit buffer and cached segments
    item: {
      handler(newVal, oldVal) {
        // If item changed (different asset_id), flush pending changes then clear buffer
        const newAssetId = newVal?.asset_id || newVal?.AssetID;
        const oldAssetId = oldVal?.asset_id || oldVal?.AssetID;

        if (newAssetId !== oldAssetId) {
          console.log('🔄 Item changed from', oldAssetId, 'to', newAssetId);

          // CRITICAL: Flush any pending changes before switching
          // This ensures edits are not lost when clicking to a different segment
          this.flushPendingChanges();

          // Now clear the buffer and cache for the new item
          console.log('🧹 Clearing edit buffer and cache');
          this.segmentEditBuffer = {};
          this.cachedScriptSegments = null;
          this.lastParsedContent = null;
        }
      },
      deep: false
    },

    // Watch for empty content in Script Mode and initialize with first paragraph
    scriptContent: {
      handler(newVal, oldVal) {
        console.log('🔔 scriptContent watcher fired:', {
          newLength: newVal?.length,
          oldLength: oldVal?.length,
          editorMode: this.editorMode,
          useVisualScriptMode: this.useVisualScriptMode,
          isActivelyEditing: this.isActivelyEditing
        });

        // CRITICAL GUARD: Skip disruptive operations while user is actively editing or restoring cursor
        // This prevents cursor loss and focus stealing during autosave
        if (this.isActivelyEditing || this.isRestoringCursor) {
          console.log('⏭️ Skipping scriptContent watcher - user is actively editing or restoring cursor');
          return;
        }

        // CRITICAL: Clear edit buffer when content changes significantly
        // This prevents stale buffered content from a previous item being displayed
        const significantChange = Math.abs((newVal?.length || 0) - (oldVal?.length || 0)) > 100;
        const contentDifferent = newVal !== oldVal && oldVal !== undefined;

        if (contentDifferent && (significantChange || !oldVal)) {
          console.log('🧹 Clearing segmentEditBuffer and cache - item appears to have changed');
          this.segmentEditBuffer = {};
          // CRITICAL: Also clear cached segments to force re-parsing
          // This prevents stale cue blocks from appearing across different items
          this.cachedScriptSegments = null;
          this.lastParsedContent = null;
        }

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
        console.log('📊📊📊 ========== SCRIPTSEGMENTS WATCHER FIRED ==========');
        console.log('📊 Old segments length:', oldSegments?.length);
        console.log('📊 New segments length:', newSegments?.length);
        console.log('📊 pendingFocusSegmentIndex:', this.pendingFocusSegmentIndex);
        console.log('📊 blockReactiveUpdates:', this.blockReactiveUpdates);

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

          // Focus pending segment if one was requested (e.g., after creating new paragraph)
          if (this.pendingFocusSegmentIndex !== null) {
            const segmentIndex = this.pendingFocusSegmentIndex;
            console.log('🎯🎯🎯 FOCUS LOGIC TRIGGERED for segment:', segmentIndex);
            console.log('🎯 Current segments count:', newSegments?.length);
            console.log('🎯 Target segment exists:', !!newSegments?.[segmentIndex]);
            console.log('🎯 All template refs:', Object.keys(this.$refs).filter(k => k.startsWith('textareaRef')));

            // CRITICAL FIX: Clear the pending flag IMMEDIATELY to prevent multiple attempts
            // Store it locally for this focus attempt
            const targetIndex = segmentIndex;
            this.pendingFocusSegmentIndex = null;

            // Try multiple times to ensure textarea is fully rendered
            const tryFocus = (attempts = 0) => {
              if (attempts > 15) {
                console.log('❌❌❌ FAILED to focus segment', targetIndex, 'after 15 attempts');
                console.log('❌ Final refs check:', Object.keys(this.$refs).filter(k => k.startsWith('textareaRef')));
                console.log('❌ Final segments count:', this.scriptSegments?.length);
                return;
              }

              const refName = `textareaRef-${targetIndex}`;
              const textareaRef = this.$refs[refName];

              console.log(`🎯 Focus attempt ${attempts + 1}/${15} for segment ${targetIndex}:`, {
                refName,
                refExists: !!textareaRef,
                refIsArray: Array.isArray(textareaRef),
                refLength: Array.isArray(textareaRef) ? textareaRef.length : 'N/A'
              });

              if (textareaRef) {
                const textareaComponent = Array.isArray(textareaRef) ? textareaRef[0] : textareaRef;
                const isHTMLElement = textareaComponent instanceof HTMLElement;
                console.log(`🎯 Textarea component:`, {
                  exists: !!textareaComponent,
                  hasEl: !!textareaComponent?.$el,
                  isHTMLElement: isHTMLElement,
                  componentType: isHTMLElement ? 'HTMLElement' : textareaComponent?.$?.type?.name
                });

                // Handle contenteditable div (direct HTMLElement ref)
                if (textareaComponent instanceof HTMLElement && textareaComponent.contentEditable === 'true') {
                  console.log('✅✅✅ FOUND CONTENTEDITABLE - Attempting focus on:', textareaComponent);

                  // Save ALL scroll positions before any focus operation
                  const scrollWrapper = document.querySelector('.scrollable-content-wrapper');
                  const scriptContainer = textareaComponent.closest('.script-content-container');
                  const savedScrolls = {
                    wrapper: scrollWrapper?.scrollTop || 0,
                    container: scriptContainer?.scrollTop || 0,
                    window: window.scrollY
                  };
                  console.log('📜 Saved scroll positions:', savedScrolls);

                  // Use preventScroll to avoid jumping to bottom
                  textareaComponent.focus({ preventScroll: true });

                  requestAnimationFrame(() => {
                    // Set cursor to beginning for contenteditable
                    const selection = window.getSelection();
                    const range = document.createRange();
                    range.selectNodeContents(textareaComponent);
                    range.collapse(true); // Collapse to start
                    selection.removeAllRanges();
                    selection.addRange(range);

                    // Restore scroll positions immediately after setting selection
                    if (scrollWrapper) scrollWrapper.scrollTop = savedScrolls.wrapper;
                    if (scriptContainer) scriptContainer.scrollTop = savedScrolls.container;
                    window.scrollTo(0, savedScrolls.window);
                    console.log('📜 Restored scroll positions');

                    const isFocused = document.activeElement === textareaComponent;
                    console.log('✅✅✅ Contenteditable focus complete:', {
                      isFocused: isFocused,
                      activeElement: document.activeElement?.tagName
                    });

                    if (!isFocused) {
                      console.log('⚠️  Contenteditable not focused, retrying...');
                      setTimeout(() => tryFocus(attempts + 1), 50);
                    }
                  });

                  return; // Success - exit retry loop
                }

                // Handle Vue component wrapping textarea (fallback for other textareas)
                if (textareaComponent && textareaComponent.$el) {
                  const textarea = textareaComponent.$el.querySelector('textarea');
                  console.log(`🎯 Native textarea element:`, {
                    exists: !!textarea,
                    isFocusable: textarea instanceof HTMLElement,
                    tagName: textarea?.tagName
                  });

                  if (textarea) {
                    console.log('✅✅✅ FOUND TEXTAREA - Attempting focus on:', textarea);

                    // Focus the textarea
                    textarea.focus();

                    // CRITICAL: Use requestAnimationFrame to ensure focus has been applied
                    // before setting cursor position
                    requestAnimationFrame(() => {
                      textarea.setSelectionRange(0, 0);
                      textarea.scrollTop = 0;

                      // Verify focus actually worked
                      const isFocused = document.activeElement === textarea;
                      console.log('✅✅✅ Focus complete:', {
                        cursorStart: textarea.selectionStart,
                        cursorEnd: textarea.selectionEnd,
                        scrollTop: textarea.scrollTop,
                        isFocused: isFocused,
                        activeElement: document.activeElement?.tagName
                      });

                      if (!isFocused) {
                        console.log('⚠️  Textarea not focused, retrying...');
                        setTimeout(() => tryFocus(attempts + 1), 50);
                      }
                    });

                    return; // Success - exit retry loop
                  }
                }
              }

              // Retry after delay
              console.log(`⏳ Retrying focus in 50ms... (attempt ${attempts + 1})`);
              setTimeout(() => tryFocus(attempts + 1), 50);
            };

            // Start focus attempts after two ticks to ensure DOM is fully updated
            this.$nextTick(() => {
              this.$nextTick(() => {
                console.log('🎯 Starting focus retry loop after double nextTick');
                tryFocus();
              });
            });
          }
        });
      }
    },

    // Watch calculated duration and emit to parent for metadata update
    calculatedItemDuration: {
      handler(newDuration) {
        console.log('⏱️ Calculated item duration:', newDuration);
        this.$emit('duration-calculated', newDuration);
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
    'update:title',
    'asset-drop',
    'metadata-change',
    'insert-cue',
    'show-img-modal',
    'show-gfx-modal',
    'show-fsq-modal',
    'show-sot-modal',
    'show-vo-modal',
    'show-nat-modal',
    'show-rif-modal',
    'show-pkg-modal',
    'show-vox-modal',
    'show-mus-modal',
    'show-live-modal',
    'toggleRundownPanel',
    'showAssetBrowserModal',
    'showTemplateManagerModal',
    'update:item',
    'duration-calculated',
    'save-current',
    'edit-sot-cue',
    'reupload-sot-cue',
    'edit-fsq-cue',
    'edit-gfx-cue',
    'edit-img-cue',
    'sot-job-complete',
    'showDirModal',
    'showBumpModal',
    'showStingModal'
  ],
  props: {
    context: {
      type: String,
      default: 'episode',
      validator: (value) => ['episode', 'library'].includes(value)
    },
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
    },
    // Segment locking props for concurrent editing protection
    isSegmentLocked: {
      type: Boolean,
      default: false
    },
    lockInfo: {
      type: Object,
      default: () => ({
        lockedBy: '',
        lockedAt: null
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

    // Episode number for iPad mode
    currentEpisodeNumber() {
      return this.currentEpisode
    },

    // Parse content into segments ONLY for Script mode display (no reactive loops)
    // eslint-disable-next-line vue/no-side-effects-in-computed-properties
    scriptSegments: {
      get() {
        console.log('🔄 scriptSegments getter called');
        console.log('  rawScriptContent length:', this.rawScriptContent?.length);
        console.log('  editorMode:', this.editorMode);
        console.log('  useVisualScriptMode:', this.useVisualScriptMode);

        if (!this.rawScriptContent || this.editorMode !== 'script' || !this.useVisualScriptMode) {
          console.log('  → Returning empty array (early exit)');
          // eslint-disable-next-line vue/no-side-effects-in-computed-properties
          this.cachedScriptSegments = null;
          // eslint-disable-next-line vue/no-side-effects-in-computed-properties
          this.lastParsedContent = null;
          return [];
        }

        // CRITICAL FIX: Return cached segments during drag to maintain object stability
        if (this.isDragging && this.cachedScriptSegments !== null) {
          console.log('  → Returning cached segments (drag in progress)');
          return this.cachedScriptSegments;
        }

        // Only re-parse if content has actually changed
        const currentContent = this.rawScriptContent;
        if (this.lastParsedContent === currentContent && this.cachedScriptSegments !== null) {
          console.log('  → Returning cached segments (content unchanged)');
          return this.cachedScriptSegments;
        }

        console.log('  → Re-parsing content (content changed)');
        try {
          // Strip YAML frontmatter for parsing
          const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);
          console.log('  contentWithoutFrontmatter:', contentWithoutFrontmatter?.substring(0, 100));

          // If content is empty or only whitespace, return empty paragraph segment
          if (!contentWithoutFrontmatter || contentWithoutFrontmatter.trim() === '') {
            console.log('  → Returning single empty text segment');
            const emptySegment = [{
              type: 'text',
              content: '',
              speaker: 'josh',
              needsParagraphTags: true,
              segmentIndex: 0
            }];
            // eslint-disable-next-line vue/no-side-effects-in-computed-properties
            this.cachedScriptSegments = emptySegment;
            // eslint-disable-next-line vue/no-side-effects-in-computed-properties
            this.lastParsedContent = currentContent;
            return emptySegment;
          }

          const segments = CueParser.parseContent(contentWithoutFrontmatter);

          const mappedSegments = segments.map((segment, index) => {
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

          // Cache the results
          // eslint-disable-next-line vue/no-side-effects-in-computed-properties
          this.cachedScriptSegments = mappedSegments;
          // eslint-disable-next-line vue/no-side-effects-in-computed-properties
          this.lastParsedContent = currentContent;
          return mappedSegments;
        } catch (error) {
          console.error('Error parsing script segments:', error);
          // Fallback: treat as single text segment
          const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);
          const fallbackSegment = [{
            type: 'text',
            content: contentWithoutFrontmatter,
            speaker: 'josh',
            needsParagraphTags: true,
            segmentIndex: 0
          }];
          // eslint-disable-next-line vue/no-side-effects-in-computed-properties
          this.cachedScriptSegments = fallbackSegment;
          // eslint-disable-next-line vue/no-side-effects-in-computed-properties
          this.lastParsedContent = currentContent;
          return fallbackSegment;
        }
      },
      set(newSegments) {
        console.log('🔄 scriptSegments setter called with', newSegments.length, 'segments');

        // Reconstruct the script content from reordered segments
        const frontmatter = this.extractYamlFrontmatter(this.rawScriptContent);
        let newContent = '';

        newSegments.forEach((segment) => {
          if (segment.type === 'text') {
            // Add speaker paragraph - KEEP empty paragraphs for proper editing
            const speaker = segment.speaker || 'josh';
            const content = segment.content || '';
            // Always add paragraph, even if empty (needed for new paragraph creation)
            newContent += `<p class="${speaker}">${content}</p>\n\n`;
          } else if (segment.type === 'cue') {
            // Reconstruct cue block from rawData
            if (segment.data && segment.data.rawData) {
              newContent += CueParser.formatCueToMarkdown(segment.data.rawData);
              newContent += '\n\n';
            }
          }
        });

        // Update rawScriptContent with frontmatter + reordered content
        const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim();
        this.$emit('update:scriptContent', newRawContent);
      }
    },

    // Draggable segments - combines scriptSegments with pending cue ghost
    draggableSegments: {
      get() {
        console.log('🔄🔄🔄 ========== DRAGGABLESEGMENTS GETTER CALLED ==========');
        console.log('  isDragging:', this.isDragging);
        console.log('  cachedScriptSegments:', this.cachedScriptSegments ? `${this.cachedScriptSegments.length} segments` : 'NULL');

        const segments = [...this.scriptSegments];

        console.log('  scriptSegments returned:', segments.length, 'segments');
        segments.forEach((seg, idx) => {
          console.log(`    [${idx}] type=${seg.type}, speaker=${seg.speaker}, contentLength=${seg.content?.length || 0}`);
        });

        console.log('  pendingCueData:', this.pendingCueData ? 'EXISTS' : 'NULL');
        console.log('  showCuePlacement:', this.showCuePlacement);

        // If there's a pending cue, add it as a ghost segment at the end
        if (this.pendingCueData && this.showCuePlacement) {
          console.log('✅ Adding pending cue(s) to draggable segments');
          // Parse the cue block to create a segment
          const cueBlocks = Array.isArray(this.pendingCueData) ? this.pendingCueData : [this.pendingCueData];

          cueBlocks.forEach((cueBlock, idx) => {
            console.log(`📦 Parsing cue block ${idx + 1}/${cueBlocks.length}:`, cueBlock.substring(0, 100));
            const cueData = CueParser.parseCueBlock(cueBlock);
            if (cueData) {
              console.log('✅ Cue data parsed successfully:', cueData.type, cueData.slug);
              segments.push({
                type: 'cue',
                data: CueParser.formatForCard(cueData),
                isPending: true, // Mark as pending for special styling
                segmentIndex: segments.length
              });
            } else {
              console.error('❌ Failed to parse cue block:', cueBlock.substring(0, 100));
            }
          });
          console.log('📊 Total segments after adding pending:', segments.length);
        } else {
          console.log('⏭️ No pending cues to add');
        }

        return segments;
      },
      set(newSegments) {
        console.log('🔄 draggableSegments setter called with', newSegments.length, 'segments');
        console.log('  isDragging:', this.isDragging);

        // CRITICAL FIX: Don't emit updates during active drag operations
        // This prevents Vue from re-parsing and losing track of elements
        if (this.isDragging) {
          console.log('⏸️ Drag in progress - storing new order but not emitting yet');
          // Store the new order for later processing
          this.pendingSegmentOrder = newSegments;
          return;
        }

        // Check if pending cue was moved (no longer at end)
        const pendingIndex = newSegments.findIndex(seg => seg.isPending);

        if (pendingIndex !== -1 && pendingIndex < newSegments.length - 1) {
          console.log('📍 Pending cue dragged to position:', pendingIndex);

          // Insert the pending cue at the dragged position
          this.insertPendingCueAtIndex(pendingIndex);

          // Clear pending state
          this.pendingCueData = null;
          this.showCuePlacement = false;
        } else {
          // Normal reorder without pending cue - use scriptSegments setter
          const realSegments = newSegments.filter(seg => !seg.isPending);
          console.log('📝 Normal reorder without pending cue');

          // Reconstruct content and update
          const frontmatter = this.extractYamlFrontmatter(this.rawScriptContent);
          let newContent = '';

          realSegments.forEach((segment) => {
            if (segment.type === 'text') {
              const speaker = segment.speaker || 'josh';
              const content = segment.content || '';
              // Always add paragraph, even if empty (needed for new paragraph creation)
              newContent += `<p class="${speaker}">${content}</p>\n\n`;
            } else if (segment.type === 'cue') {
              if (segment.data && segment.data.rawData) {
                newContent += CueParser.formatCueToMarkdown(segment.data.rawData);
                newContent += '\n\n';
              }
            }
          });

          const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim();
          // Use centralized emitter with validation
          this.emitScriptContent(newRawContent);
          this.$emit('save-current');
        }
      }
    },

    // Calculate total duration of rundown item (cue durations + paragraph text durations)
    calculatedItemDuration() {
      if (!this.scriptSegments || this.scriptSegments.length === 0) {
        return '00:00:00:00';
      }

      let totalSeconds = 0;
      const speakerWpm = this.item?.speaker_wpm || 150; // Get speaker WPM from item

      this.scriptSegments.forEach(segment => {
        if (segment.type === 'cue' && segment.data) {
          // Add cue duration (parse from HH:MM:SS:FF format)
          const duration = segment.data.duration || segment.data.Duration || '00:00:00:00';
          totalSeconds += this.parseDurationToSeconds(duration);
        } else if (segment.type === 'text' && segment.content) {
          // Calculate paragraph duration based on word count and speaker WPM
          const wordCount = segment.content.trim().split(/\s+/).filter(w => w.length > 0).length;
          const paragraphSeconds = Math.ceil((wordCount / speakerWpm) * 60);
          totalSeconds += paragraphSeconds;
        }
      });

      // Convert total seconds back to HH:MM:SS:FF format
      return this.secondsToDuration(totalSeconds);
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

    // Get highlight color with opacity for background (uses existing highlightColor)
    highlightBackgroundColor() {
      const hexColor = this.highlightColor;
      // Convert hex to RGB and add 40% opacity for visibility
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, 0.4)`;
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

    // Get highlight color from database for slug field attention
    highlightColor() {
      const colorName = getColorValue('highlight') || 'yellow-lighten-3';
      const resolved = resolveVuetifyColor(colorName);
      // Convert to rgba for animation
      return resolved || '#FFF9C4';
    },

    // Get needs-attention color from settings for flagged paragraphs
    needsAttentionColor() {
      // Reference colorLoadTrigger to ensure re-computation when colors are loaded
      // eslint-disable-next-line no-unused-vars
      const _trigger = this.colorLoadTrigger;
      const colorName = getColorValue('needs-attention') || 'orange-lighten-3';
      const resolved = resolveVuetifyColor(colorName);
      console.log('🚩 needsAttentionColor computed:', { colorName, resolved });
      return resolved || '#FFCC80';
    },

    // Get needs-attention background color with 30% opacity
    needsAttentionBackgroundColor() {
      const hexColor = this.needsAttentionColor;
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, 0.3)`;
    },

    // Get needs-attention border color (solid)
    needsAttentionBorderColor() {
      return this.needsAttentionColor;
    },

    // CSS variables for dynamic theming
    editorPanelCssVars() {
      // Calculate additional opacity variations for the needs-attention color
      const hexColor = this.needsAttentionColor;
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);

      return {
        '--needs-attention-bg': this.needsAttentionBackgroundColor,
        '--needs-attention-border': this.needsAttentionBorderColor,
        '--needs-attention-color': this.needsAttentionColor,
        '--needs-attention-btn-bg': `rgba(${r}, ${g}, ${b}, 0.15)`,
        '--needs-attention-btn-hover': `rgba(${r}, ${g}, ${b}, 0.4)`,
        '--needs-attention-btn-active': `rgba(${r}, ${g}, ${b}, 0.5)`
      };
    },

    // Validate slug: must be lowercase and 4 words or less
    isSlugValid() {
      if (!this.item?.slug || this.item.slug.trim().length === 0) {
        return false;
      }

      const slug = this.item.slug.trim();

      // Check if slug is all lowercase (allowing hyphens, underscores, numbers)
      const isLowercase = slug === slug.toLowerCase();

      // Count words (split by spaces, hyphens, or underscores)
      const words = slug.split(/[\s\-_]+/).filter(w => w.length > 0);
      const wordCount = words.length;

      return isLowercase && wordCount <= 4;
    },

  },
  methods: {
    /**
     * Open iPad Mode - launches iPad scroll view in new window
     */
    openIpadMode() {
      if (!this.currentEpisodeNumber) {
        console.warn('No episode number available for iPad mode')
        return
      }

      // Open iPad scroll view in new window/tab
      const url = `/ipad-scroll/${this.currentEpisodeNumber}`
      window.open(url, '_blank')
    },

    /**
     * Store reference to paragraph element for flag note positioning.
     */
    setParagraphRef(index, el) {
      if (el) {
        this.paragraphRefs[index] = el;
      } else {
        delete this.paragraphRefs[index];
      }
    },

    /**
     * Get style object for flag note panel positioning.
     * Uses the paragraph's bounding rect to position the panel next to it.
     */
    // eslint-disable-next-line no-unused-vars
    getFlagNotePanelStyle(index, type) {
      // Force reactivity on scroll
      // eslint-disable-next-line no-unused-vars
      const _trigger = this.flagNotePosUpdateTrigger;

      const el = this.paragraphRefs[index];
      if (!el) {
        // Fallback to default position if ref not available
        return {
          position: 'fixed',
          top: '100px',
          right: '20px'
        };
      }

      const rect = el.getBoundingClientRect();
      // Position to the right of the flag button (which is at right: -28px from paragraph)
      // The flag button is ~24px wide, so panel starts after the button with a small gap
      const leftPos = rect.right + 36; // 28px (button offset) + 8px gap

      return {
        position: 'fixed',
        top: `${Math.max(rect.top, 60)}px`, // Don't go above 60px (below toolbar)
        left: `${leftPos}px` // Position to the right of the flag button
        // No maxHeight - panel grows to fit content
      };
    },

    /**
     * Handle scroll event to update flag note positions.
     */
    handleScrollForFlagNotes() {
      this.flagNotePosUpdateTrigger++;
    },

    /**
     * Format relative time from ISO date string for locked segment display.
     */
    formatRelativeTime(isoString) {
      if (!isoString) return '';
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return 'just now';
      if (diffMins === 1) return '1 minute ago';
      if (diffMins < 60) return `${diffMins} minutes ago`;

      const diffHours = Math.floor(diffMins / 60);
      if (diffHours === 1) return '1 hour ago';
      return `${diffHours} hours ago`;
    },

    /**
     * Check if a flag note is minimized.
     * @param {string} type - 'paragraph' or 'cue'
     * @param {number} index - The segment index
     * @returns {boolean} - Whether the note is minimized
     */
    isFlagNoteMinimized(type, index) {
      const key = `${type}-${index}`;
      const isMinimized = !!this.minimizedFlagNotes[key];
      console.log('🚩 isFlagNoteMinimized:', { type, index, key, isMinimized, minimizedFlagNotes: { ...this.minimizedFlagNotes } });
      return isMinimized;
    },

    /**
     * Toggle the minimized state of a flag note.
     * @param {string} type - 'paragraph' or 'cue'
     * @param {number} index - The segment index
     */
    toggleFlagNoteMinimized(type, index) {
      const key = `${type}-${index}`;
      if (this.minimizedFlagNotes[key]) {
        delete this.minimizedFlagNotes[key];
      } else {
        this.minimizedFlagNotes[key] = true;
      }
    },

    /**
     * Toggle the needs-attention flag on a paragraph segment.
     * This persists when the script is saved.
     */
    toggleNeedsAttention(segmentIndex) {
      console.log('🚩 Toggle needs-attention for segment:', segmentIndex);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      // Get current segments
      const segments = [...this.scriptSegments];

      if (!segments[segmentIndex] || segments[segmentIndex].type !== 'text') {
        console.warn('Cannot toggle needs-attention on non-text segment');
        return;
      }

      // Toggle the flag
      segments[segmentIndex].needsAttention = !segments[segmentIndex].needsAttention;

      console.log('🚩 New needsAttention value:', segments[segmentIndex].needsAttention);

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(segments);
      this.$emit('update:scriptContent', newRawContent);
    },

    /**
     * Toggle the needs-attention flag on a cue segment.
     * This persists when the script is saved via the cue's rawData.
     */
    toggleCueNeedsAttention(segmentIndex) {
      console.log('🚩 Toggle needs-attention for cue segment:', segmentIndex);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      // Get current segments
      const segments = [...this.scriptSegments];

      if (!segments[segmentIndex] || segments[segmentIndex].type !== 'cue') {
        console.warn('Cannot toggle cue needs-attention on non-cue segment');
        return;
      }

      // Toggle the flag on the cue data
      const cueData = segments[segmentIndex].data;
      if (cueData) {
        cueData.needsAttention = !cueData.needsAttention;
        // Also update rawData if it exists
        if (cueData.rawData) {
          cueData.rawData.needsAttention = cueData.needsAttention;
        }
      }

      console.log('🚩 New cue needsAttention value:', cueData?.needsAttention);

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(segments);
      this.$emit('update:scriptContent', newRawContent);
    },

    /**
     * Open the flag note panel for a segment.
     * If segment is not flagged, flags it first.
     */
    openFlagNotePanel(index, type, segment) {
      console.log('🚩 Opening flag note panel:', { index, type });

      // Get the current flag note content
      let currentNote = '';
      if (type === 'paragraph') {
        currentNote = segment.flagNote || '';
        // If not already flagged, flag it now
        if (!segment.needsAttention) {
          this.toggleNeedsAttention(index);
        }
      } else if (type === 'cue') {
        currentNote = segment.data?.flagNote || '';
        // If not already flagged, flag it now
        if (!segment.data?.needsAttention) {
          this.toggleCueNeedsAttention(index);
        }
      }

      // Set the panel state
      this.activeFlagNoteIndex = index;
      this.activeFlagNoteType = type;
      this.flagNoteContent = currentNote;
    },

    /**
     * Close the flag note panel without saving.
     */
    closeFlagNotePanel() {
      console.log('🚩 Closing flag note panel');
      this.activeFlagNoteIndex = null;
      this.activeFlagNoteType = null;
      this.flagNoteContent = '';
    },

    /**
     * Save the flag note content to the segment.
     */
    saveFlagNote(index, type) {
      console.log('🚩 Saving flag note:', { index, type, content: this.flagNoteContent });

      this.hasLocalUnsavedChanges = true;
      const segments = [...this.scriptSegments];

      if (type === 'paragraph') {
        if (segments[index] && segments[index].type === 'text') {
          segments[index].flagNote = this.flagNoteContent;
        }
      } else if (type === 'cue') {
        if (segments[index] && segments[index].type === 'cue' && segments[index].data) {
          segments[index].data.flagNote = this.flagNoteContent;
          if (segments[index].data.rawData) {
            segments[index].data.rawData.flagNote = this.flagNoteContent;
          }
        }
      }

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(segments);
      this.$emit('update:scriptContent', newRawContent);

      // Close the panel
      this.closeFlagNotePanel();
    },

    /**
     * Resolve (unflag) the segment and close the panel.
     */
    resolveFlag(index, type) {
      console.log('🚩 Resolving flag:', { index, type });

      this.hasLocalUnsavedChanges = true;
      const segments = [...this.scriptSegments];

      if (type === 'paragraph') {
        if (segments[index] && segments[index].type === 'text') {
          segments[index].needsAttention = false;
          segments[index].flagNote = ''; // Clear the note
        }
      } else if (type === 'cue') {
        if (segments[index] && segments[index].type === 'cue' && segments[index].data) {
          segments[index].data.needsAttention = false;
          segments[index].data.flagNote = ''; // Clear the note
          if (segments[index].data.rawData) {
            segments[index].data.rawData.needsAttention = false;
            segments[index].data.rawData.flagNote = '';
          }
        }
      }

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(segments);
      this.$emit('update:scriptContent', newRawContent);

      // Close the panel
      this.closeFlagNotePanel();
    },

    /**
     * Update flag note for a paragraph segment (called on input change).
     */
    updateParagraphFlagNote(index, value) {
      this.hasLocalUnsavedChanges = true;
      const segments = [...this.scriptSegments];

      if (segments[index] && segments[index].type === 'text') {
        segments[index].flagNote = value;
      }

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(segments);
      this.$emit('update:scriptContent', newRawContent);
    },

    /**
     * Update flag note for a cue segment (called on input change).
     */
    updateCueFlagNote(index, value) {
      this.hasLocalUnsavedChanges = true;
      const segments = [...this.scriptSegments];

      if (segments[index] && segments[index].type === 'cue' && segments[index].data) {
        segments[index].data.flagNote = value;
        if (segments[index].data.rawData) {
          segments[index].data.rawData.flagNote = value;
        }
      }

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(segments);
      this.$emit('update:scriptContent', newRawContent);
    },

    /**
     * Handle flag button click - toggles flag on/off. Notes are always on by default.
     * Click on unflagged = flag it (note shows automatically)
     * Click on flagged = unflag it (if minimized, expand first; if visible, unflag)
     */
    handleFlagClick(index, type, segment) {
      const key = `${type}-${index}`;
      const isFlagged = type === 'paragraph' ? segment.needsAttention : segment.data?.needsAttention;

      console.log('🚩 handleFlagClick:', { index, type, isFlagged, key });

      if (!isFlagged) {
        // Not flagged - flag it (note shows automatically, always on by default)
        console.log('🚩 Flagging segment - note will show by default');
        if (type === 'paragraph') {
          this.toggleNeedsAttention(index);
        } else {
          this.toggleCueNeedsAttention(index);
        }
        // Ensure not minimized so note shows
        delete this.minimizedFlagNotes[key];
      } else if (this.minimizedFlagNotes[key]) {
        // Flagged but minimized - expand it (don't unflag)
        console.log('🚩 Expanding minimized note');
        delete this.minimizedFlagNotes[key];
      } else {
        // Flagged and visible - unflag it
        console.log('🚩 Unflagging segment');
        if (type === 'paragraph') {
          this.toggleNeedsAttention(index);
        } else {
          this.toggleCueNeedsAttention(index);
        }
        delete this.minimizedFlagNotes[key];
      }
    },

    /**
     * Minimize a flag note panel.
     */
    minimizeFlagNote(type, index) {
      const key = `${type}-${index}`;
      this.minimizedFlagNotes[key] = true;
    },

    /**
     * Get the first four words from paragraph content for flag note header.
     */
    getFirstFourWords(content) {
      if (!content) return 'Flagged paragraph';
      // Strip HTML tags and get plain text
      const plainText = content.replace(/<[^>]*>/g, '').trim();
      // Split by whitespace and get first 4 words
      const words = plainText.split(/\s+/).slice(0, 4);
      const result = words.join(' ');
      // Add ellipsis if there were more words
      return plainText.split(/\s+/).length > 4 ? result + '...' : result;
    },

    /**
     * Get a reference string for a cue segment for flag note header.
     */
    getCueReference(segment) {
      if (!segment || !segment.data) return 'Flagged cue';
      const cueType = segment.data.type || segment.data.cueType || 'CUE';
      const slug = segment.data.slug || segment.data.Slug || '';
      return slug ? `${cueType}: ${slug}` : cueType;
    },

    /**
     * UNIVERSAL RULE: Get safe insertion position that is NEVER inside a cue block or paragraph.
     * Cue blocks are independent elements that must exist BETWEEN other elements, never inside them.
     *
     * If the position falls inside:
     * - A cue block (<!-- Begin Cue --> ... <!-- End Cue -->): advance to after <!-- End Cue -->
     * - A paragraph (<p>...</p>): advance to after </p>
     *
     * @param {string} content - The script content to check against
     * @param {number} position - The proposed insertion position
     * @returns {number} Safe insertion position guaranteed to be outside any cue block or paragraph
     */
    getSafeInsertionPosition(content, position) {
      if (!content || position < 0) return position;

      let safePosition = position;

      // Check if position falls inside a cue block
      const cueBlockPattern = /<!-- Begin Cue -->[\s\S]*?<!-- End Cue -->/g;
      let match;

      while ((match = cueBlockPattern.exec(content)) !== null) {
        const blockStart = match.index;
        const blockEnd = match.index + match[0].length;

        if (safePosition > blockStart && safePosition < blockEnd) {
          console.log(`⚠️ Position ${safePosition} is inside cue block [${blockStart}-${blockEnd}], advancing to ${blockEnd}`);
          safePosition = blockEnd;
        }
      }

      // Check if position falls inside a paragraph tag
      const paragraphPattern = /<p[^>]*>[\s\S]*?<\/p>/g;

      while ((match = paragraphPattern.exec(content)) !== null) {
        const pStart = match.index;
        const pEnd = match.index + match[0].length;

        if (safePosition > pStart && safePosition < pEnd) {
          console.log(`⚠️ Position ${safePosition} is inside paragraph [${pStart}-${pEnd}], advancing to ${pEnd}`);
          safePosition = pEnd;
        }
      }

      return safePosition;
    },

    /**
     * Find all content segments (paragraphs and cue blocks) with their positions.
     * Used for accurate segment-based insertion that accounts for both element types.
     *
     * @param {string} content - The script content to parse
     * @returns {Array} Array of segment objects with type, index, endIndex, and content
     */
    findAllContentSegments(content) {
      if (!content) return [];

      const segments = [];
      // Match both paragraph tags and cue blocks
      const segmentPattern = /(<p[^>]*class="[^"]*"[^>]*>[\s\S]*?<\/p>|<!-- Begin Cue -->[\s\S]*?<!-- End Cue -->)/g;
      let match;

      while ((match = segmentPattern.exec(content)) !== null) {
        segments.push({
          content: match[0],
          index: match.index,
          endIndex: match.index + match[0].length,
          type: match[0].startsWith('<p') ? 'paragraph' : 'cue'
        });
      }

      return segments;
    },

    /**
     * Load cue card alignment from settings
     */
    async loadCueCardAlignment() {
      try {
        const response = await fetch('/api/settings/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        });

        if (response.ok) {
          const settings = await response.json();
          // Backend returns snake_case, check both formats
          const alignment = settings.interface?.cue_card_alignment || settings.interface?.cueCardAlignment;
          if (alignment) {
            this.cueCardAlignment = alignment;
            console.log('✅ Loaded cue card alignment:', this.cueCardAlignment);
          } else {
            console.log('⚠️ No cue card alignment found in settings, using default:', this.cueCardAlignment);
          }
        }
      } catch (error) {
        console.error('Failed to load cue card alignment:', error);
      }
    },

    // Focus and highlight slug field for newly created items
    focusSlugField() {
      console.log('🎯 focusSlugField() called')
      this.slugNeedsAttention = true
      this.$nextTick(() => {
        const slugField = this.$refs.slugFieldRef
        console.log('🎯 slugFieldRef:', slugField)
        if (slugField && slugField.$el) {
          const input = slugField.$el.querySelector('input')
          console.log('🎯 input element:', input)
          if (input) {
            input.focus()
            input.select()
            console.log('🎯 Slug field focused and selected, highlighted yellow')
          } else {
            console.warn('⚠️ Could not find input element in slug field')
          }
        } else {
          console.warn('⚠️ Slug field ref not available')
        }
      })
    },

    // Handle slug field blur - normalize to lowercase
    handleSlugBlur() {
      this.slugFieldFocused = false;

      if (this.item?.slug && this.item.slug.trim().length > 0) {
        const normalized = this.item.slug.toLowerCase().trim();

        // Only emit update if the slug actually changed
        if (normalized !== this.item.slug) {
          this.$emit('update:slug', normalized);
        }
      }
    },

    // Parse HH:MM:SS:FF duration format to total seconds
    parseDurationToSeconds(duration) {
      if (!duration || typeof duration !== 'string') return 0;

      const parts = duration.split(':');
      if (parts.length !== 4) return 0;

      const hours = parseInt(parts[0]) || 0;
      const minutes = parseInt(parts[1]) || 0;
      const seconds = parseInt(parts[2]) || 0;
      // Ignore frames (parts[3]) for now

      return (hours * 3600) + (minutes * 60) + seconds;
    },

    // Convert total seconds to HH:MM:SS:FF duration format
    secondsToDuration(totalSeconds) {
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;

      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:00`;
    },

    // Handle textarea input - update content and auto-resize
    handleTextareaInput(index, value) {
      console.log(`✏️ handleTextareaInput called for index ${index}, value length: ${value?.length}, blockReactiveUpdates: ${this.blockReactiveUpdates}`);

      // Skip update if blockReactiveUpdates is set
      // This prevents conflicting updates during programmatic operations (paragraph creation, merging, etc.)
      if (this.blockReactiveUpdates) {
        console.log('⏭️⏭️⏭️ SKIPPING handleTextareaInput - blockReactiveUpdates is active');
        console.log('⏭️ This prevents interference with paragraph creation/focus logic');
        return;
      }

      this.updateTextSegment(index, value);
      this.autoResizeTextarea(index);
    },

    // Handle contenteditable input - update content from innerHTML
    handleContentEditableInput(index, event) {
      const element = event.target;
      const htmlContent = element.innerHTML;
      console.log(`✏️ handleContentEditableInput called for index ${index}, html length: ${htmlContent?.length}`);

      // CRITICAL FIX: Mark this segment as actively being edited
      // This prevents getSegmentContent from returning buffered content,
      // which would cause Vue to re-render and reset cursor position (causing reverse typing)
      this.activelyEditingSegment = index;
      this.isActivelyEditing = true; // Block watchers during active editing

      // Save cursor state for restoration after autosave
      // Uses text offset instead of Range object so it survives DOM re-renders
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        // Calculate the text offset from start of contenteditable to cursor
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(element);
        preCaretRange.setEnd(range.startContainer, range.startOffset);
        const textOffset = preCaretRange.toString().length;

        this.savedCursorState = {
          segmentIndex: index,
          textOffset: textOffset,
          htmlContent: element.innerHTML // Save content to detect if it changed
        };
      }

      // Skip update if blockReactiveUpdates is set
      if (this.blockReactiveUpdates) {
        console.log('⏭️⏭️⏭️ SKIPPING handleContentEditableInput - blockReactiveUpdates is active');
        return;
      }

      // Clean up any browser-generated formatting quirks
      // Browsers wrap pasted lines in <div> or <p> tags - convert to newlines to preserve paragraphs
      // Note: <br[^>]*> catches <br>, <br/>, <br class="Apple-interchange-newline">, etc.
      let cleanedHtml = htmlContent
        // CRITICAL: Replace closing </div> and </p> with newlines BEFORE stripping opening tags
        // This preserves paragraph breaks when pasting multi-paragraph content
        .replace(/<\/div>/gi, '\n')
        .replace(/<\/p>/gi, '\n')
        .replace(/<div[^>]*>/gi, '')  // Strip opening div tags (including ones with attributes)
        .replace(/<p[^>]*>/gi, '')    // Strip opening p tags (including ones with classes)
        .replace(/<br[^>]*\/?>/gi, '\n')
        // Clean up multiple consecutive newlines (max 2 for paragraph breaks)
        .replace(/\n{3,}/g, '\n\n')
        .trim();

      this.updateTextSegment(index, cleanedHtml);
      this.hasLocalUnsavedChanges = true;
    },

    // Flush all pending changes from the edit buffer immediately
    // Called before switching items to ensure no edits are lost
    // Returns a Promise that resolves after the flush is complete
    async flushPendingChanges() {
      if (!this.segmentEditBuffer || Object.keys(this.segmentEditBuffer).length === 0) {
        console.log('💾 No pending changes to flush');
        return Promise.resolve();
      }

      console.log('💾 Flushing pending changes for', Object.keys(this.segmentEditBuffer).length, 'segments');

      // Clear any pending debounce timers
      if (this.updateDebounceTimers) {
        Object.keys(this.updateDebounceTimers).forEach(key => {
          clearTimeout(this.updateDebounceTimers[key]);
        });
        this.updateDebounceTimers = {};
      }

      // Get current segments and apply all buffered changes
      const segments = [...this.scriptSegments];
      let hasChanges = false;

      Object.keys(this.segmentEditBuffer).forEach(indexStr => {
        const index = parseInt(indexStr);
        if (segments[index] && segments[index].type === 'text') {
          console.log('💾 Applying buffered changes to segment', index);
          segments[index].content = this.segmentEditBuffer[index];
          hasChanges = true;
        }
      });

      if (hasChanges) {
        // Reconstruct and emit the updated content
        const newRawContent = this.reconstructRawContent(segments);
        this.$emit('update:scriptContent', newRawContent);
        console.log('💾 Flushed changes emitted to parent');

        // Clear the buffer AFTER emitting
        this.segmentEditBuffer = {};

        // Wait for Vue to process the emit and parent to update
        await this.$nextTick();
        await this.$nextTick();
        console.log('💾 Flush complete - Vue reactivity settled');
      }

      return Promise.resolve();
    },

    // Handle paste for contenteditable divs - detect paragraph breaks and split into multiple paragraphs
    handleContentEditablePaste(index, event) {
      event.preventDefault();

      const clipboardData = event.clipboardData || window.clipboardData;
      const plainText = clipboardData.getData('text/plain');
      const htmlText = clipboardData.getData('text/html');

      console.log('📋 Paste detected - analyzing content for paragraph breaks');
      console.log('📋 Plain text length:', plainText?.length, 'HTML length:', htmlText?.length);

      // Check user setting for plain text paste
      const interfaceSettings = JSON.parse(localStorage.getItem('showbuild_interface_settings') || '{}');
      const pastePlainTextOnly = interfaceSettings.pastePlainTextOnly === true;

      // Determine paragraphs from pasted content
      let paragraphs = [];

      if (pastePlainTextOnly || !htmlText) {
        // Plain text mode: split on double newlines (paragraph breaks)
        paragraphs = plainText.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 0);
        console.log('📋 Plain text mode - found', paragraphs.length, 'paragraphs');
      } else {
        // HTML mode: parse and extract paragraphs
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlText;

        // Clean up Google Docs cruft
        tempDiv.querySelectorAll('[id^="docs-internal-guid"]').forEach(el => {
          // Unwrap the span but keep its content
          while (el.firstChild) {
            el.parentNode.insertBefore(el.firstChild, el);
          }
          el.remove();
        });

        // Remove style attributes from all elements
        tempDiv.querySelectorAll('[style]').forEach(el => {
          el.removeAttribute('style');
        });

        // Also strip ALL span tags from the entire pasted content (catches unclosed spans)
        // Google Docs often creates unclosed <span> tags that corrupt content
        tempDiv.innerHTML = tempDiv.innerHTML
          .replace(/<span[^>]*>/gi, '')   // Remove ALL opening <span> tags
          .replace(/<\/span>/gi, '');     // Remove ALL closing </span> tags

        // Extract paragraphs from <p>, <div>, or split plain text by line breaks
        // Note: We query for <p> and <div> to find paragraph boundaries, but will strip
        // nested <div> tags from within paragraph content below
        const pElements = tempDiv.querySelectorAll('p, div');
        if (pElements.length > 0) {
          pElements.forEach(p => {
            // Strip any remaining span and div tags from individual paragraph content
            let content = p.innerHTML.trim()
              .replace(/<span[^>]*>/gi, '')
              .replace(/<\/span>/gi, '')
              .replace(/<div[^>]*>/gi, '')      // Remove nested <div> opening tags
              .replace(/<\/div>/gi, '')          // Remove nested </div> closing tags
              .replace(/&nbsp;/gi, ' ');
            if (content && content !== '<br>' && content !== '<br/>') {
              paragraphs.push(content);
            }
          });
        }

        // If no paragraph elements found, try splitting by <br><br> or double newlines
        if (paragraphs.length === 0) {
          const rawContent = tempDiv.innerHTML
            .replace(/<br\s*\/?>\s*<br\s*\/?>/gi, '\n\n')
            .replace(/<\/p>\s*<p[^>]*>/gi, '\n\n')
            .replace(/<\/div>\s*<div[^>]*>/gi, '\n\n');

          // Create temp element to get text content split by our markers
          const temp2 = document.createElement('div');
          temp2.innerHTML = rawContent;
          const textWithBreaks = temp2.textContent || temp2.innerText || '';
          paragraphs = textWithBreaks.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 0);
        }

        console.log('📋 HTML mode - found', paragraphs.length, 'paragraphs');
      }

      // If no paragraphs found, just insert the plain text
      if (paragraphs.length === 0) {
        paragraphs = [plainText.trim()];
      }

      const element = event.target;
      const currentSegment = this.scriptSegments[index];

      if (paragraphs.length === 1) {
        // Single paragraph - just insert at cursor
        document.execCommand('insertText', false, paragraphs[0]);
        this.syncContentEditableToSegment(index, element);
        this.hasLocalUnsavedChanges = true;
        console.log('📋 Single paragraph pasted');
      } else {
        // Multiple paragraphs - need to split and create new paragraph segments
        console.log('📋 Multiple paragraphs detected - creating', paragraphs.length, 'segments');

        // Get cursor position to split current content
        const selection = window.getSelection();
        let contentBefore = '';
        let contentAfter = '';

        if (selection.rangeCount > 0) {
          const range = selection.getRangeAt(0);

          // Get content BEFORE cursor
          const beforeRange = document.createRange();
          beforeRange.selectNodeContents(element);
          beforeRange.setEnd(range.startContainer, range.startOffset);
          const beforeFragment = beforeRange.cloneContents();
          const tempBefore = document.createElement('div');
          tempBefore.appendChild(beforeFragment);
          contentBefore = tempBefore.innerHTML.trim();

          // Get content AFTER cursor
          const afterRange = document.createRange();
          afterRange.selectNodeContents(element);
          afterRange.setStart(range.endContainer, range.endOffset);
          const afterFragment = afterRange.cloneContents();
          const tempAfter = document.createElement('div');
          tempAfter.appendChild(afterFragment);
          contentAfter = tempAfter.innerHTML.trim();
        }

        // Build new segments array
        const segments = [...this.scriptSegments];
        const speaker = currentSegment?.speaker || 'josh';

        // First paragraph: content before cursor + first pasted paragraph
        const firstParagraphContent = contentBefore + (contentBefore ? ' ' : '') + paragraphs[0];

        // Update current segment
        segments[index] = {
          ...currentSegment,
          content: firstParagraphContent
        };

        // Create new segments for remaining paragraphs
        const newSegments = [];
        for (let i = 1; i < paragraphs.length; i++) {
          newSegments.push({
            type: 'text',
            content: paragraphs[i],
            speaker: speaker,
            needsParagraphTags: true
          });
        }

        // Add segment for content after cursor (if any)
        if (contentAfter) {
          newSegments.push({
            type: 'text',
            content: contentAfter,
            speaker: speaker,
            needsParagraphTags: true
          });
        }

        // Insert new segments after current
        segments.splice(index + 1, 0, ...newSegments);

        // Set focus to end of pasted content (last new paragraph, or just after pasted if no content after)
        this.pendingFocusSegmentIndex = index + paragraphs.length - (contentAfter ? 0 : 1);

        // Reconstruct and emit
        const newRawContent = this.reconstructRawContent(segments);
        this.$emit('update:scriptContent', newRawContent);
        this.hasLocalUnsavedChanges = true;

        console.log('📋 Created', newSegments.length, 'new paragraph segments');
      }
    },

    // Handle keydown for contenteditable divs
    handleContentEditableKeydown(index, event) {
      console.log('🎹 ContentEditable key pressed:', event.key, 'in segment', index);

      // Allow space key to pass through naturally (browser handles insertion)
      if (event.key === ' ' || event.code === 'Space') {
        return;
      }

      // Ctrl+B: Toggle bold using execCommand
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        document.execCommand('bold', false, null);
        this.syncContentEditableToSegment(index, event.target);
        return;
      }

      // Ctrl+I: Toggle italic using execCommand
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'i') {
        event.preventDefault();
        document.execCommand('italic', false, null);
        this.syncContentEditableToSegment(index, event.target);
        return;
      }

      // Ctrl+U: Toggle underline using execCommand
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'u') {
        event.preventDefault();
        document.execCommand('underline', false, null);
        this.syncContentEditableToSegment(index, event.target);
        return;
      }

      // Ctrl+S: Save all
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 's') {
        event.preventDefault();
        this.handleSaveAll();
        return;
      }

      // Handle Enter key for paragraph creation (DOUBLE-ENTER required)
      // Single Enter = line break within segment
      // Double Enter (two Enters within 1 second) = split paragraph at cursor position
      if (event.key === 'Enter' && !event.shiftKey) {
        const element = event.target;
        const textContent = element.textContent || '';

        // Get cursor position
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        const range = selection.getRangeAt(0);

        // Calculate cursor offset in text content
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(element);
        preCaretRange.setEnd(range.startContainer, range.startOffset);
        const caretOffset = preCaretRange.toString().length;

        // Track Enter timing per segment for double-Enter detection
        // Double-Enter now works ANYWHERE in paragraph (not just at end)
        const now = Date.now();
        const lastEnterTime = this.lastEnterState[index]?.time || 0;
        const lastEnterPosition = this.lastEnterState[index]?.position || -1;
        const timeSinceLastEnter = now - lastEnterTime;
        // Double-enter detected if: within 1 second AND cursor hasn't moved much (within 5 chars)
        const isDoubleEnter = timeSinceLastEnter < 1000 && Math.abs(caretOffset - lastEnterPosition) <= 5;

        console.log('⏎ Enter pressed:', {
          textContent: textContent.substring(Math.max(0, caretOffset - 10), Math.min(textContent.length, caretOffset + 10)),
          caretOffset,
          totalLength: textContent.length,
          lastEnterPosition,
          timeSinceLastEnter,
          isDoubleEnter
        });

        // Update last Enter state for this segment
        this.lastEnterState[index] = { time: now, position: caretOffset };

        if (isDoubleEnter) {
          // DOUBLE ENTER: Split paragraph at cursor position
          event.preventDefault();
          console.log('⏎⏎ Double Enter detected - splitting paragraph at cursor');

          // Find scrollable containers
          const scrollWrapper = document.querySelector('.scrollable-content-wrapper');
          const scriptContainer = element.closest('.script-content-container');
          const savedWrapperScroll = scrollWrapper ? scrollWrapper.scrollTop : 0;
          const savedContainerScroll = scriptContainer ? scriptContainer.scrollTop : 0;

          if (scrollWrapper) {
            scrollWrapper.style.overflow = 'hidden';
          }

          this.blockReactiveUpdates = true;

          // CRITICAL FIX: Clear active editing flags BEFORE creating new paragraph
          this.isActivelyEditing = false;
          this.activelyEditingSegment = null;
          console.log('⏎⏎ Cleared isActivelyEditing and activelyEditingSegment for paragraph creation');

          // Split content at cursor position using Range API
          // Get content BEFORE cursor (stays in current paragraph)
          const beforeRange = document.createRange();
          beforeRange.selectNodeContents(element);
          beforeRange.setEnd(range.startContainer, range.startOffset);
          const beforeFragment = beforeRange.cloneContents();
          const tempBefore = document.createElement('div');
          tempBefore.appendChild(beforeFragment);
          let contentBefore = tempBefore.innerHTML
            .replace(/(<br[^>]*\/?>|\n|<div><br[^>]*\/?><\/div>|\s)+$/gi, '')
            .trim();

          // Get content AFTER cursor (goes to new paragraph)
          const afterRange = document.createRange();
          afterRange.selectNodeContents(element);
          afterRange.setStart(range.endContainer, range.endOffset);
          const afterFragment = afterRange.cloneContents();
          const tempAfter = document.createElement('div');
          tempAfter.appendChild(afterFragment);
          let contentAfter = tempAfter.innerHTML
            .replace(/^(<br[^>]*\/?>|\n|<div><br[^>]*\/?><\/div>|\s)+/gi, '')
            .trim();

          console.log('⏎⏎ Split content - before:', contentBefore.substring(0, 50), '... after:', contentAfter.substring(0, 50));

          // Update current element with content before cursor
          element.innerHTML = contentBefore;

          // Clear any pending debounce for this segment
          if (this.updateDebounceTimers && this.updateDebounceTimers[index]) {
            clearTimeout(this.updateDebounceTimers[index]);
            delete this.updateDebounceTimers[index];
          }
          if (this.segmentEditBuffer && this.segmentEditBuffer[index]) {
            delete this.segmentEditBuffer[index];
          }

          // Create new paragraph with content after cursor
          this.createNewParagraphAfterWithContent(index, contentAfter, contentBefore);

          // Restore scroll and unlock after a delay
          setTimeout(() => {
            if (scrollWrapper) {
              scrollWrapper.style.overflow = '';
              scrollWrapper.scrollTop = savedWrapperScroll;
            }
            if (scriptContainer) {
              scriptContainer.scrollTop = savedContainerScroll;
            }
            this.blockReactiveUpdates = false;
          }, 100);

          return;
        }

        // SINGLE ENTER: Allow default behavior (inserts line break)
        // Don't preventDefault - let browser insert the newline/br
        console.log('⏎ Single Enter - allowing line break');
        // Let the event propagate naturally
      }

      // Handle Backspace at beginning - merge with previous
      if (event.key === 'Backspace') {
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
          const range = selection.getRangeAt(0);
          // Check if cursor is at the very beginning
          if (range.startOffset === 0 && range.collapsed) {
            const element = event.target;
            // Check if there's no content before the cursor
            if (range.startContainer === element || range.startContainer === element.firstChild) {
              event.preventDefault();
              this.mergeParagraphWithPrevious(index);
            }
          }
        }
      }

      // Ctrl+Alt+H: Toggle highlight
      if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'h') {
        event.preventDefault();
        // Use custom highlight since execCommand doesn't have built-in highlight
        this.toggleHighlightContentEditable(index, event.target);
      }
    },

    // Sync contenteditable innerHTML back to segment data
    syncContentEditableToSegment(index, element) {
      this.$nextTick(() => {
        let html = element.innerHTML;
        // Normalize the HTML - browsers use different tags
        html = html
          .replace(/<b>/gi, '<strong>')
          .replace(/<\/b>/gi, '</strong>')
          .replace(/<i>/gi, '<em>')
          .replace(/<\/i>/gi, '</em>');

        // Clean up browser-inserted <div> tags from contenteditable
        // Browsers insert <div> when pressing Enter - convert to spaces or remove
        html = html
          .replace(/<div><br\s*\/?><\/div>/gi, '')           // Remove <div><br></div> (empty line)
          .replace(/<\/div>\s*<div[^>]*>/gi, ' ')            // Convert </div><div> to space (line break)
          .replace(/<div[^>]*>/gi, '')                        // Remove remaining opening <div> tags
          .replace(/<\/div>/gi, '');                          // Remove remaining closing </div> tags

        this.updateTextSegment(index, html);
        this.hasLocalUnsavedChanges = true;
      });
    },

    // Toggle highlight for contenteditable (mark tag)
    toggleHighlightContentEditable(index, element) {
      const selection = window.getSelection();
      if (!selection.rangeCount || selection.isCollapsed) {
        console.log('🖍️ No text selected for highlight');
        return;
      }

      const range = selection.getRangeAt(0);
      const selectedText = range.toString();

      if (!selectedText) return;

      // Check if selection is inside a mark element
      let parentMark = range.commonAncestorContainer;
      while (parentMark && parentMark !== element) {
        if (parentMark.nodeName === 'MARK') {
          // Already highlighted - remove the mark
          const textNode = document.createTextNode(parentMark.textContent);
          parentMark.parentNode.replaceChild(textNode, parentMark);
          this.syncContentEditableToSegment(index, element);
          return;
        }
        parentMark = parentMark.parentNode;
      }

      // Not highlighted - add mark
      const mark = document.createElement('mark');
      try {
        range.surroundContents(mark);
        this.syncContentEditableToSegment(index, element);
      } catch (e) {
        console.warn('Could not apply highlight - selection spans multiple elements');
      }
    },

    // Custom auto-resize for textareas and contenteditable divs
    autoResizeTextarea(index) {
      this.$nextTick(() => {
        const textareaRefArray = this.$refs[`textareaRef-${index}`];

        // Template refs in v-for return arrays, so get the first element
        const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;

        if (!textareaRef) return;

        // Handle contenteditable div (direct HTMLElement)
        if (textareaRef instanceof HTMLElement && textareaRef.contentEditable === 'true') {
          // Contenteditable divs auto-size naturally, just update line count
          this.$nextTick(() => {
            this.updateLineCount(index);
          });
          return;
        }

        // Handle Vue component wrapping textarea (fallback)
        if (textareaRef && textareaRef.$el) {
          const textarea = textareaRef.$el.querySelector('textarea');

          if (textarea) {
            textarea.style.overflow = 'hidden';
            textarea.style.minHeight = '0';
            textarea.style.maxHeight = 'none';
            textarea.style.height = '1px';

            const scrollHeight = textarea.scrollHeight;
            const newHeight = scrollHeight + 'px';
            textarea.style.height = newHeight;

            this.$nextTick(() => {
              this.updateLineCount(index);
            });
          }
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

      if (!textareaRef) return;

      const lineHeight = 24; // 16px font * 1.5 line-height
      let totalHeight = 0;

      // Handle contenteditable div (direct HTMLElement)
      if (textareaRef instanceof HTMLElement && textareaRef.contentEditable === 'true') {
        totalHeight = textareaRef.scrollHeight;
      }
      // Handle Vue component wrapping textarea
      else if (textareaRef && textareaRef.$el) {
        const textarea = textareaRef.$el.querySelector('textarea');
        if (textarea) {
          totalHeight = textarea.scrollHeight;
        }
      }

      if (totalHeight > 0) {
        const lineCount = Math.max(1, Math.round(totalHeight / lineHeight));
        this.segmentLineCounts[index] = lineCount;
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

    // ===== COLLAPSE MODE HELPER METHODS =====

    /**
     * Get the line range for a collapsed paragraph display
     * Returns a string like "33-43" representing the absolute line numbers
     */
    getCollapsedLineRange(segmentIndex) {
      const startLine = this.getAbsoluteLineNumber(segmentIndex, 1);
      const lineCount = this.getLineCount(segmentIndex);
      const endLine = startLine + lineCount - 1;

      if (lineCount === 1) {
        return `${startLine}`;
      }
      return `${startLine}-${endLine}`;
    },

    /**
     * Get the first 6 words of paragraph content for collapsed mode (left-aligned)
     */
    getCollapsedFirstWords(content) {
      if (!content) return '(empty)';

      // Strip HTML tags for word counting
      const textOnly = content.replace(/<[^>]*>/g, '').trim();
      if (!textOnly) return '(empty)';

      const words = textOnly.split(/\s+/).filter(w => w.length > 0);

      if (words.length <= 6) {
        return words.join(' ');
      }

      return words.slice(0, 6).join(' ');
    },

    /**
     * Get the last 6 words of paragraph content for collapsed mode (right-aligned)
     */
    getCollapsedLastWords(content) {
      if (!content) return '';

      // Strip HTML tags for word counting
      const textOnly = content.replace(/<[^>]*>/g, '').trim();
      if (!textOnly) return '';

      const words = textOnly.split(/\s+/).filter(w => w.length > 0);

      if (words.length <= 6) {
        return ''; // Don't show last words if content is short
      }

      return words.slice(-6).join(' ');
    },

    /**
     * Convert hex color to HSL
     */
    hexToHsl(hex) {
      // Remove # if present
      hex = hex.replace(/^#/, '');

      // Parse RGB values
      const r = parseInt(hex.substring(0, 2), 16) / 255;
      const g = parseInt(hex.substring(2, 4), 16) / 255;
      const b = parseInt(hex.substring(4, 6), 16) / 255;

      const max = Math.max(r, g, b);
      const min = Math.min(r, g, b);
      let h, s, l = (max + min) / 2;

      if (max === min) {
        h = s = 0; // achromatic
      } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
          case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
          case g: h = ((b - r) / d + 2) / 6; break;
          case b: h = ((r - g) / d + 4) / 6; break;
        }
      }

      return { h: h * 360, s: s * 100, l: l * 100 };
    },

    /**
     * Get the style for a collapsed cue based on its type
     * Uses the cue type colors for the border, darkened 30% for background
     */
    getCollapsedCueStyle(cueType) {
      const typeColors = {
        'IMG': '#4CAF50',
        'GFX': '#9C27B0',
        'FSQ': '#FF9800',
        'SOT': '#2196F3',
        'VO': '#00BCD4',
        'NAT': '#795548',
        'RIF': '#E91E63',
        'PKG': '#607D8B',
        'DIR': '#FF5722',
        'BUMP': '#3F51B5',
        'STING': '#8BC34A',
        'VOX': '#009688',
        'MUS': '#673AB7',
        'LIVE': '#F44336'
      };

      const color = typeColors[cueType] || '#757575';

      // Convert to HSL and darken by 30% (reduce lightness)
      const hsl = this.hexToHsl(color);
      // Darken: reduce lightness by 30% of its current value, then use with alpha for background
      const darkenedL = Math.max(0, hsl.l * 0.7); // 30% darker
      const bgColor = `hsla(${hsl.h}, ${hsl.s}%, ${darkenedL}%, 0.25)`;

      return {
        borderLeft: `4px solid ${color}`,
        backgroundColor: bgColor
      };
    },

    /**
     * Get the outcue from cue data (for SOT - last 5 words of transcription)
     */
    getCollapsedOutcue(cueData) {
      if (!cueData) return '';

      // If outcue is already set, use it
      if (cueData.outcue) return cueData.outcue;

      // For SOT, extract from transcription
      if (cueData.type === 'SOT' && cueData.transcription) {
        const words = cueData.transcription.trim().split(/\s+/);
        if (words.length > 5) {
          return '...' + words.slice(-5).join(' ');
        }
        return cueData.transcription;
      }

      return '';
    },

    // ===== END COLLAPSE MODE HELPER METHODS =====

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

    /**
     * Validate script content for common issues that cause data corruption
     * Returns an object with validation results and detected issues
     */
    validateScriptContent(content) {
      if (!content) return { isValid: true, issues: [] };

      const issues = [];

      // 1. Check for truncated HTML tags (e.g., </p instead of </p>)
      const truncatedTagMatch = content.match(/<\/[a-z]+[^>]*$/i);
      if (truncatedTagMatch) {
        issues.push({
          type: 'truncated_tag',
          description: `Truncated closing tag found: "${truncatedTagMatch[0]}"`,
          position: content.lastIndexOf(truncatedTagMatch[0])
        });
      }

      // 2. Check for unclosed paragraph tags
      const openPTags = (content.match(/<p\s/g) || []).length + (content.match(/<p>/g) || []).length;
      const closePTags = (content.match(/<\/p>/g) || []).length;
      if (openPTags !== closePTags) {
        issues.push({
          type: 'mismatched_tags',
          description: `Mismatched paragraph tags: ${openPTags} opening, ${closePTags} closing`,
          openCount: openPTags,
          closeCount: closePTags
        });
      }

      // 3. Check for duplicate content blocks (same paragraph appearing twice)
      const paragraphs = content.match(/<p[^>]*>[\s\S]*?<\/p>/g) || [];
      if (paragraphs.length > 10) {
        // Only check first 5 paragraphs for duplication (performance)
        const firstFiveParagraphs = paragraphs.slice(0, 5).join('|||');
        const contentAfterHalf = paragraphs.slice(Math.floor(paragraphs.length / 2));
        const secondHalfStart = contentAfterHalf.slice(0, 5).join('|||');

        if (firstFiveParagraphs === secondHalfStart && paragraphs.length > 20) {
          issues.push({
            type: 'duplicate_content',
            description: 'Content appears to be duplicated (first half matches second half)',
            totalParagraphs: paragraphs.length,
            estimatedOriginalLength: Math.floor(paragraphs.length / 2)
          });
        }
      }

      // 4. Check for multiple YAML frontmatter blocks
      const frontmatterCheck = this.detectMultipleFrontmatterBlocks(content);
      if (frontmatterCheck.isMalformed) {
        issues.push({
          type: 'malformed_frontmatter',
          description: `Multiple or malformed YAML frontmatter blocks detected`,
          blockCount: frontmatterCheck.blockCount
        });
      }

      return {
        isValid: issues.length === 0,
        issues: issues
      };
    },

    /**
     * Repair common content issues
     * Returns the repaired content and a log of repairs made
     */
    repairScriptContent(content) {
      if (!content) return { content: content, repairs: [] };

      let repairedContent = content;
      const repairs = [];

      // 1. Fix truncated closing tags (</p, </div, etc.)
      const truncatedTagPattern = /<\/([a-z]+)$/i;
      const truncatedMatch = repairedContent.match(truncatedTagPattern);
      if (truncatedMatch) {
        repairedContent = repairedContent.replace(truncatedTagPattern, `</${truncatedMatch[1]}>`);
        repairs.push({
          type: 'truncated_tag_fixed',
          description: `Fixed truncated tag: </${truncatedMatch[1]}> was missing >`
        });
      }

      // 2. Remove duplicate content (if detected)
      const paragraphs = repairedContent.match(/<p[^>]*>[\s\S]*?<\/p>/g) || [];
      if (paragraphs.length > 20) {
        const firstFive = paragraphs.slice(0, 5).map(p => p.trim()).join('|||');
        const halfPoint = Math.floor(paragraphs.length / 2);
        const atHalfFive = paragraphs.slice(halfPoint, halfPoint + 5).map(p => p.trim()).join('|||');

        if (firstFive === atHalfFive) {
          // Content is duplicated - extract frontmatter and first half of body
          const frontmatterMatch = repairedContent.match(/^(---[\s\S]*?---\n)/);
          const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';
          const bodyContent = frontmatterMatch ? repairedContent.slice(frontmatter.length) : repairedContent;

          // Find the position where duplication starts
          const bodyParagraphs = bodyContent.match(/<p[^>]*>[\s\S]*?<\/p>/g) || [];
          const halfBodyParagraphs = bodyParagraphs.slice(0, Math.floor(bodyParagraphs.length / 2));

          // Reconstruct content with just the first half
          const uniqueBody = halfBodyParagraphs.join('\n\n');
          repairedContent = frontmatter + uniqueBody;

          repairs.push({
            type: 'duplicate_content_removed',
            description: `Removed duplicate content block (${paragraphs.length} paragraphs reduced to ${halfBodyParagraphs.length})`
          });
        }
      }

      // 3. Fix multiple frontmatter blocks - keep only the first one
      const frontmatterCheck = this.detectMultipleFrontmatterBlocks(repairedContent);
      if (frontmatterCheck.blockCount > 1) {
        // Keep only content up to end of first frontmatter block
        const firstBlockEnd = repairedContent.indexOf('---', 3) + 3;
        const afterFirstBlock = repairedContent.slice(firstBlockEnd);
        const bodyStart = afterFirstBlock.search(/<p|<!-- Begin Cue/);

        if (bodyStart > -1) {
          const cleanBody = afterFirstBlock.slice(bodyStart);
          // Remove any additional frontmatter from body
          const cleanedBody = cleanBody.replace(/\n---[\s\S]*?---\n/g, '\n');
          repairedContent = repairedContent.slice(0, firstBlockEnd) + '\n' + cleanedBody;

          repairs.push({
            type: 'multiple_frontmatter_fixed',
            description: `Removed ${frontmatterCheck.blockCount - 1} extra frontmatter block(s)`
          });
        }
      }

      return {
        content: repairedContent,
        repairs: repairs,
        wasRepaired: repairs.length > 0
      };
    },

    /**
     * Validate and repair content before saving
     * Called automatically before emitting save events
     */
    validateAndRepairBeforeSave(content) {
      const validation = this.validateScriptContent(content);

      if (!validation.isValid) {
        console.warn('⚠️ Content validation issues detected:', validation.issues);

        const repair = this.repairScriptContent(content);

        if (repair.wasRepaired) {
          console.log('🔧 Content repaired:', repair.repairs);
          return {
            content: repair.content,
            wasRepaired: true,
            repairs: repair.repairs,
            originalIssues: validation.issues
          };
        }
      }

      return {
        content: content,
        wasRepaired: false,
        repairs: [],
        originalIssues: validation.issues
      };
    },

    /**
     * Centralized method for emitting script content updates
     * Validates and repairs content before emitting to prevent corruption
     * @param {string} content - The content to emit
     * @param {boolean} skipValidation - Skip validation (for raw edits, default false)
     */
    emitScriptContent(content, skipValidation = false) {
      if (!content) {
        this.$emit('update:scriptContent', content);
        return;
      }

      if (skipValidation) {
        this.$emit('update:scriptContent', content);
        return;
      }

      // Validate and repair before emitting
      const result = this.validateAndRepairBeforeSave(content);

      if (result.wasRepaired) {
        console.log('📝 Content was auto-repaired before save:', result.repairs);
        // Show a subtle notification to user
        this.showRepairNotification(result.repairs);
      }

      this.$emit('update:scriptContent', result.content);
    },

    /**
     * Show a subtle notification when content is auto-repaired
     */
    showRepairNotification(repairs) {
      if (!repairs || repairs.length === 0) return;

      const repairDescriptions = repairs.map(r => r.description).join(', ');
      console.info(`🔧 Auto-repair applied: ${repairDescriptions}`);

      // Use flash message if available
      if (this.flashMessage) {
        this.flashMessage.show = true;
        this.flashMessage.text = `Auto-fixed: ${repairs.length} issue(s)`;
        this.flashMessage.color = 'warning';
      }
    },

    updateMetadata(field, value) {
      // If slug is being updated, check if it's valid and clear attention highlight
      if (field === 'slug' && value && value.trim().length > 0) {
        // Check if slug passes validation rules
        const isValid = this.slugRules.every(rule => rule(value) === true)
        if (isValid) {
          this.slugNeedsAttention = false
          console.log('✅ Valid slug entered, clearing attention highlight')
        }
      }

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

        // Show modal immediately for code mode - emit to parent for all cue types
        if (cueType === 'IMG') {
          this.$emit('show-img-modal');
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

        if (cueType === 'RIF') {
          this.$emit('show-rif-modal');
          return;
        }

        if (cueType === 'PKG') {
          this.$emit('show-pkg-modal');
          return;
        }

        if (cueType === 'DIR') {
          this.$emit('show-dir-modal');
          return;
        }

        if (cueType === 'BUMP') {
          this.$emit('show-bump-modal');
          return;
        }

        if (cueType === 'STING') {
          this.$emit('show-sting-modal');
          return;
        }

        // Fallback for other cue types
        const cueText = `**[${cueType}: ]**`;
        this.insertCueAtCursor(cueText);
        return;
      }

      // SCRIPT MODE: Flash screen with cue color, then open modal
      console.log('📄 Script mode detected - flashing screen then opening modal');

      // Import flash utility dynamically
      import('@/composables/useScreenFlash').then(({ useScreenFlash }) => {
        const { flashForCue } = useScreenFlash();
        flashForCue(cueType, 250); // Fast flash with cue type color
      });

      // All cue types now use the same workflow: flash -> modal -> placement
      this.pendingCueType = cueType;

      // Small delay to let flash complete
      setTimeout(() => {
        // Open the appropriate modal
        if (cueType === 'SOT') {
          this.$emit('show-sot-modal');
          console.log('🎬 SOT modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'IMG') {
          this.$emit('show-img-modal');
          console.log('🎬 IMG modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'FSQ') {
          this.$emit('show-fsq-modal');
          console.log('🎬 FSQ modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'GFX') {
          this.$emit('show-gfx-modal');
          console.log('🎬 GFX modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'VO') {
          this.$emit('show-vo-modal');
          console.log('🎬 VO modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'NAT') {
          this.$emit('show-nat-modal');
          console.log('🎬 NAT modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'RIF') {
          this.$emit('show-rif-modal');
          console.log('🎬 RIF modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'PKG') {
          this.$emit('show-pkg-modal');
          console.log('🎬 PKG modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'DIR') {
          this.$emit('show-dir-modal');
          console.log('🎬 DIR modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'BUMP') {
          this.$emit('show-bump-modal');
          console.log('🎬 BUMP modal opened - placement overlay will activate when modal closes');
          return;
        }

        if (cueType === 'STING') {
          this.$emit('show-sting-modal');
          console.log('🎬 STING modal opened - placement overlay will activate when modal closes');
          return;
        }

        // Fallback for other cue types
        const cueText = `**[${cueType}: ]**`;
        this.insertCueAtCursor(cueText);
      }, 250);
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

        // Get episode (required for upload)
        // Check if we have a temporary episode from callback first
        let episode = this.temporaryEpisode;
        if (episode) {
          console.log('✅ Using temporary episode from callback:', episode);
          this.temporaryEpisode = null; // Clear it
        } else {
          episode = this.requireEpisode(
            this.currentEpisode,
            'Upload Image',
            (selectedEpisode) => {
              // Callback: retry upload after episode selection
              console.log('📺 Episode selected, retrying IMG cue creation with:', selectedEpisode);
              // Store episode temporarily and retry
              this.temporaryEpisode = selectedEpisode;
              this.handleImgCueSubmit(imgCueData);
            }
          );

          if (!episode) {
            console.log('⏸️ IMG cue creation paused - waiting for episode selection');
            return; // Modal will show, callback will retry
          }
        }

        // Upload and relocate image to episode-specific location
        const formData = new FormData();
        formData.append('file', imgCueData.imageFile);
        formData.append('episode', episode);
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
        const episodeSpecificMediaUrl = `episodes/${episode}/assets/images/${newFilename}`;

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

        // SCRIPT MODE: Insert based on selection (like SOT)
        console.log('📄 Script mode: Auto-inserting IMG based on selection');

        // Close the modal
        this.showImgModal = false;

        // Determine insertion point based on selection
        let insertionIndex;
        if (this.selectedSegmentIndex !== null && this.selectedSegmentIndex >= 0) {
          // Insert AFTER the selected segment (between zones)
          insertionIndex = this.selectedSegmentIndex + 1;
          console.log(`📍 Selected segment found at index ${this.selectedSegmentIndex}, inserting AFTER at between-zone ${insertionIndex}`);
        } else {
          // No selection - insert at bottom (after last paragraph)
          const paragraphCount = this.scriptSegments.filter(seg => seg.type === 'text').length;
          insertionIndex = paragraphCount;
          console.log(`📍 No segment selected, inserting at bottom (between-zone ${insertionIndex})`);
        }

        // Create placement object for between-paragraph insertion
        const placement = {
          type: 'between',
          index: insertionIndex,
          cueType: 'IMG'
        };

        // Insert IMG at determined location
        this.insertCueBetweenParagraphsInRawScript(placement, imgCueBlock);
        console.log('✅ IMG cue inserted at selected position in script mode');

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
      // CRITICAL FIX: If this segment is actively being edited, return the DOM's current innerHTML
      // This prevents Vue's v-html from overwriting content and resetting cursor position
      if (this.activelyEditingSegment === segmentIndex) {
        const refName = `textareaRef-${segmentIndex}`;
        const element = this.$refs[refName];
        if (element && element.innerHTML !== undefined) {
          // Return the element's current innerHTML to prevent Vue from re-rendering it
          return element.innerHTML;
        }
      }

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

        // CRITICAL: Set restoration flag BEFORE emit to block watchers during the entire save cycle
        this.isRestoringCursor = true;

        // Update single source of truth
        this.$emit('update:scriptContent', newRawContent);

        // Clear buffer and timer
        delete this.segmentEditBuffer[segmentIndex];
        delete this.updateDebounceTimers[segmentIndex];

        // IMPORTANT: Do NOT clear editing flags here!
        // Keep isActivelyEditing=true so user can continue typing after autosave
        // Flags are only cleared on blur (when user clicks away from paragraph)
        console.log('📝 Autosave complete - keeping editing flags active for continued typing');

        // Persist to database and show visual feedback
        await this.persistCurrentItemToDatabase(segmentIndex);
      }, 1500); // 1.5 second debounce - reduced from 5s to minimize data loss window
    },

    /**
     * Generic method to toggle formatting tags on selected text
     * @param {number} segmentIndex - Index of the segment being edited
     * @param {HTMLTextAreaElement} textarea - The textarea element
     * @param {string} openTag - Opening tag (e.g., '<strong>')
     * @param {string} closeTag - Closing tag (e.g., '</strong>')
     * @param {string} tagName - Tag name for logging (e.g., 'bold')
     */
    toggleSelectionFormatting(segmentIndex, textarea, openTag, closeTag, tagName) {
      console.log(`🎨 toggleSelectionFormatting (${tagName}) called for segment`, segmentIndex);

      const selectionStart = textarea.selectionStart;
      const selectionEnd = textarea.selectionEnd;
      const content = textarea.value;

      // If no selection, do nothing
      if (selectionStart === selectionEnd) {
        console.log(`🎨 No text selected, nothing to ${tagName}`);
        return;
      }

      const selectedText = content.substring(selectionStart, selectionEnd);
      console.log(`🎨 Selected text for ${tagName}:`, selectedText);

      let newContent;
      let newCursorStart;
      let newCursorEnd;

      const beforeSelection = content.substring(0, selectionStart);
      const afterSelection = content.substring(selectionEnd);

      // Pattern 1: Selection includes the tags
      if (selectedText.startsWith(openTag) && selectedText.endsWith(closeTag)) {
        // Remove the tags from selection
        const unwrappedText = selectedText.slice(openTag.length, -closeTag.length);
        newContent = beforeSelection + unwrappedText + afterSelection;
        newCursorStart = selectionStart;
        newCursorEnd = selectionStart + unwrappedText.length;
        console.log(`🎨 Removed ${tagName} (pattern 1 - tags in selection)`);
      }
      // Pattern 2: Tags are outside the selection
      else if (beforeSelection.endsWith(openTag) && afterSelection.startsWith(closeTag)) {
        // Remove the surrounding tags
        const newBefore = beforeSelection.slice(0, -openTag.length);
        const newAfter = afterSelection.slice(closeTag.length);
        newContent = newBefore + selectedText + newAfter;
        newCursorStart = newBefore.length;
        newCursorEnd = newBefore.length + selectedText.length;
        console.log(`🎨 Removed ${tagName} (pattern 2 - tags outside selection)`);
      }
      // Pattern 3: Not formatted - add tags
      else {
        newContent = beforeSelection + openTag + selectedText + closeTag + afterSelection;
        newCursorStart = selectionStart;
        newCursorEnd = selectionEnd + openTag.length + closeTag.length;
        console.log(`🎨 Added ${tagName}`);
      }

      // Update the textarea value
      textarea.value = newContent;

      // Restore selection
      textarea.setSelectionRange(newCursorStart, newCursorEnd);

      // Trigger the update through the normal flow
      this.updateTextSegment(segmentIndex, newContent);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      console.log(`🎨 ${tagName} toggle complete`);
    },

    /**
     * Toggle bold (<strong>) on selected text - Ctrl+B
     */
    toggleBoldSelection(segmentIndex, textarea) {
      this.toggleSelectionFormatting(segmentIndex, textarea, '<strong>', '</strong>', 'bold');
    },

    /**
     * Toggle italic (<em>) on selected text - Ctrl+I
     */
    toggleItalicSelection(segmentIndex, textarea) {
      this.toggleSelectionFormatting(segmentIndex, textarea, '<em>', '</em>', 'italic');
    },

    /**
     * Toggle underline (<u>) on selected text - Ctrl+U
     */
    toggleUnderlineSelection(segmentIndex, textarea) {
      this.toggleSelectionFormatting(segmentIndex, textarea, '<u>', '</u>', 'underline');
    },

    /**
     * Toggle highlight (<mark>) on selected text in a textarea
     * Ctrl+H hotkey - wraps selection with <mark> tags or removes them if already highlighted
     */
    toggleHighlightSelection(segmentIndex, textarea) {
      console.log('🖍️ toggleHighlightSelection called for segment', segmentIndex);

      const selectionStart = textarea.selectionStart;
      const selectionEnd = textarea.selectionEnd;
      const content = textarea.value;

      // If no selection, do nothing
      if (selectionStart === selectionEnd) {
        console.log('🖍️ No text selected, nothing to highlight');
        return;
      }

      const selectedText = content.substring(selectionStart, selectionEnd);
      console.log('🖍️ Selected text:', selectedText);

      let newContent;
      let newCursorStart;
      let newCursorEnd;

      // Check if selection is already wrapped in <mark> tags
      const beforeSelection = content.substring(0, selectionStart);
      const afterSelection = content.substring(selectionEnd);

      // Pattern 1: Selection includes the mark tags
      if (selectedText.startsWith('<mark>') && selectedText.endsWith('</mark>')) {
        // Remove the mark tags from selection
        const unwrappedText = selectedText.slice(6, -7); // Remove <mark> and </mark>
        newContent = beforeSelection + unwrappedText + afterSelection;
        newCursorStart = selectionStart;
        newCursorEnd = selectionStart + unwrappedText.length;
        console.log('🖍️ Removed highlight (pattern 1 - tags in selection)');
      }
      // Pattern 2: Mark tags are outside the selection
      else if (beforeSelection.endsWith('<mark>') && afterSelection.startsWith('</mark>')) {
        // Remove the surrounding mark tags
        const newBefore = beforeSelection.slice(0, -6); // Remove trailing <mark>
        const newAfter = afterSelection.slice(7); // Remove leading </mark>
        newContent = newBefore + selectedText + newAfter;
        newCursorStart = newBefore.length;
        newCursorEnd = newBefore.length + selectedText.length;
        console.log('🖍️ Removed highlight (pattern 2 - tags outside selection)');
      }
      // Pattern 3: Not highlighted - add mark tags
      else {
        newContent = beforeSelection + '<mark>' + selectedText + '</mark>' + afterSelection;
        newCursorStart = selectionStart;
        newCursorEnd = selectionEnd + 13; // +13 for <mark></mark>
        console.log('🖍️ Added highlight');
      }

      // Update the textarea value
      textarea.value = newContent;

      // Restore selection
      textarea.setSelectionRange(newCursorStart, newCursorEnd);

      // Trigger the update through the normal flow
      this.updateTextSegment(segmentIndex, newContent);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      console.log('🖍️ Highlight toggle complete');
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

          console.log('🎯 Double Enter detected - activating blockReactiveUpdates');
          this.blockReactiveUpdates = true;

          // Store the cleaned content (without trailing newline)
          const cleanedContent = currentContent.replace(/\n$/, '');

          // Clear any pending debounce for this segment
          if (this.updateDebounceTimers && this.updateDebounceTimers[segmentIndex]) {
            clearTimeout(this.updateDebounceTimers[segmentIndex]);
            delete this.updateDebounceTimers[segmentIndex];
          }
          if (this.segmentEditBuffer && this.segmentEditBuffer[segmentIndex]) {
            delete this.segmentEditBuffer[segmentIndex];
          }

          // Create new paragraph with cleaned content
          this.createNewParagraphAfter(segmentIndex, cleanedContent);

          // Clear the flag after a delay to allow the update and focus to complete
          // Must be long enough for focus retry logic (up to 10 attempts * 50ms = 500ms)
          setTimeout(() => {
            console.log('🎯 Clearing blockReactiveUpdates flag');
            this.blockReactiveUpdates = false;
          }, 1000);
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

      // Ctrl+B: Toggle bold on selected text
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        this.toggleBoldSelection(segmentIndex, event.target);
        return;
      }

      // Ctrl+I: Toggle italic on selected text
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'i') {
        event.preventDefault();
        this.toggleItalicSelection(segmentIndex, event.target);
        return;
      }

      // Ctrl+U: Toggle underline on selected text
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'u') {
        event.preventDefault();
        this.toggleUnderlineSelection(segmentIndex, event.target);
        return;
      }

      // Ctrl+S: Save all
      if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 's') {
        event.preventDefault();
        this.handleSaveAll();
        return;
      }

      // Ctrl+Alt+H: Toggle highlight on selected text
      if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'h') {
        event.preventDefault();
        this.toggleHighlightSelection(segmentIndex, event.target);
      }
    },

    // Script Mode Behavior: Create new <p> tag in Code mode
    createNewParagraphAfter(segmentIndex, cleanedContentForCurrentSegment = null) {
      console.log('📝📝📝 ========== CREATE NEW PARAGRAPH ==========');
      console.log('📝 Creating new paragraph after segment:', segmentIndex);
      console.log('📝 Current segments count:', this.scriptSegments?.length);
      console.log('📝 cleanedContentForCurrentSegment:', cleanedContentForCurrentSegment);

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      const segments = [...this.scriptSegments];
      const currentSegment = segments[segmentIndex];

      if (!currentSegment) {
        console.error('❌ Current segment not found at index:', segmentIndex);
        return;
      }

      console.log('📝 Current segment before update:', {
        type: currentSegment.type,
        speaker: currentSegment.speaker,
        contentLength: currentSegment.content?.length
      });

      // If cleaned content was provided (from double-enter), update current segment
      if (cleanedContentForCurrentSegment !== null) {
        console.log('📝 Updating current segment content (removing trailing newline)');
        console.log('📝 Old content:', JSON.stringify(segments[segmentIndex].content));
        segments[segmentIndex].content = cleanedContentForCurrentSegment;
        console.log('📝 New content:', JSON.stringify(segments[segmentIndex].content));
      }

      // Create new empty text segment that will become a new <p> tag
      const newSegment = {
        type: 'text',
        content: '', // Empty content for new paragraph
        speaker: currentSegment.speaker || 'josh', // Inherit speaker from current paragraph
        needsParagraphTags: true // This ensures it becomes <p class="speaker">content</p>
      };

      console.log('📝 New segment to insert:', newSegment);

      // Insert after current segment
      segments.splice(segmentIndex + 1, 0, newSegment);
      console.log('📝 Segments count after splice:', segments.length);

      // Set the focus index to the newly created paragraph
      this.pendingFocusSegmentIndex = segmentIndex + 1;
      console.log('📝📝📝 Set pendingFocusSegmentIndex to:', this.pendingFocusSegmentIndex);

      // Reconstruct raw content - this will create the new <p> tag in Code mode
      const newRawContent = this.reconstructRawContent(segments);
      console.log('📝 Reconstructed content length:', newRawContent.length);
      console.log('📝 Reconstructed content preview:', newRawContent.substring(0, 300));

      console.log('📝 Emitting update:scriptContent to parent...');
      this.$emit('update:scriptContent', newRawContent);
      console.log('📝📝📝 ========== EMIT COMPLETE ==========');

      // Focus logic is now handled by scriptSegments watcher
      // which will focus pendingFocusSegmentIndex after Vue finishes re-rendering
    },

    // Create new paragraph after current one with specific content (for splitting)
    // currentSegmentContent: optional - if provided, update current segment's content too (for mid-paragraph splits)
    createNewParagraphAfterWithContent(segmentIndex, newParagraphContent, currentSegmentContent = null) {
      console.log('📝📝📝 ========== CREATE NEW PARAGRAPH WITH CONTENT ==========');
      console.log('📝 Creating new paragraph after segment:', segmentIndex);
      console.log('📝 New paragraph content:', newParagraphContent);
      if (currentSegmentContent !== null) {
        console.log('📝 Updating current segment content to:', currentSegmentContent);
      }

      // Mark as having unsaved changes
      this.hasLocalUnsavedChanges = true;

      const segments = [...this.scriptSegments];
      const currentSegment = segments[segmentIndex];

      if (!currentSegment) {
        console.error('❌ Current segment not found at index:', segmentIndex);
        return;
      }

      // If currentSegmentContent is provided, update the current segment (for mid-paragraph splits)
      if (currentSegmentContent !== null) {
        segments[segmentIndex] = {
          ...currentSegment,
          content: currentSegmentContent
        };
        console.log('📝 Updated current segment content');
      }

      // Create new text segment with the provided content
      const newSegment = {
        type: 'text',
        content: newParagraphContent || '',
        speaker: currentSegment.speaker || 'josh',
        needsParagraphTags: true
      };

      console.log('📝 New segment to insert:', newSegment);

      // Insert after current segment
      segments.splice(segmentIndex + 1, 0, newSegment);
      console.log('📝 Segments count after splice:', segments.length);

      // Set the focus index to the newly created paragraph
      this.pendingFocusSegmentIndex = segmentIndex + 1;
      console.log('📝📝📝 Set pendingFocusSegmentIndex to:', this.pendingFocusSegmentIndex);

      // Reconstruct raw content
      const newRawContent = this.reconstructRawContent(segments);
      console.log('📝 Reconstructed content length:', newRawContent.length);

      console.log('📝 Emitting update:scriptContent to parent...');
      this.$emit('update:scriptContent', newRawContent);
      console.log('📝📝📝 ========== EMIT COMPLETE ==========');
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
      this.$emit('update:scriptContent', newRawContent);

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
      this.$emit('update:scriptContent', newRawContent);
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
      // Open appropriate modal based on cue type - emit to parent for all
      if (cueData.type === 'IMG') {
        // Emit event to parent (ContentEditor) to open IMG modal with cue data
        this.$emit('edit-img-cue', cueData);
      } else if (cueData.type === 'SOT') {
        // Emit event to parent (ContentEditor) to open SOT modal with cue data
        this.$emit('edit-sot-cue', cueData);
      } else if (cueData.type === 'FSQ') {
        // Emit event to parent (ContentEditor) to open FSQ modal with cue data
        this.$emit('edit-fsq-cue', cueData);
      } else if (cueData.type === 'GFX') {
        // Emit event to parent (ContentEditor) to open GFX modal with cue data
        this.$emit('edit-gfx-cue', cueData);
      } else if (cueData.type === 'DIR') {
        // Emit event to parent (ContentEditor) to open DIR modal with cue data
        this.$emit('edit-dir-cue', cueData);
      }
      // Add other cue type modals as needed
    },

    /**
     * Handle re-upload request for SOT cue
     * Opens SotModal with existing metadata but requires new video upload
     */
    handleReuploadSotCue(reuploadData) {
      console.log('📤 Re-upload SOT cue requested:', reuploadData);
      // Emit to parent (ContentEditor) which will open SotModal with pre-filled data
      this.$emit('reupload-sot-cue', reuploadData);
    },

    /**
     * Handle FSQ edit request from PlaceholderCueCard
     * Emits to parent (ContentEditor) which will open FsqModal in edit mode
     */
    handleEditFsq(cueData) {
      console.log('📝 Edit FSQ cue requested:', cueData);
      this.$emit('edit-fsq-cue', cueData);
    },

    /**
     * Handle SOT job status change (especially completion)
     * Emits to ContentEditor to trigger content refresh
     */
    handleSotStatusChange({ status, assetId }) {
      console.log(`📊 SOT job status changed: ${assetId} → ${status}`);
      if (status === 'completed') {
        console.log('✅ SOT job completed - requesting content refresh');
        this.$emit('sot-job-complete', { assetId });
      }
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
      this.$emit('update:scriptContent', newRawContent);

      console.log('Meta updated successfully');
    },

    /**
     * Handle cue field update from PlaceholderCueCard
     * Format: { assetId, field, value }
     * Used for updating individual fields like mediaUrl after FSQ generation
     */
    handleCueFieldUpdate({ assetId, field, value }) {
      console.log(`📝 handleCueFieldUpdate: assetId=${assetId}, field=${field}, value=${value}`);

      // Find the cue segment by assetId
      const segmentIndex = this.scriptSegments.findIndex(segment =>
        segment.type === 'cue' &&
        (segment.data?.assetId === assetId || segment.data?.rawData?.assetId === assetId)
      );

      if (segmentIndex === -1) {
        console.error('❌ Could not find cue segment with assetId:', assetId);
        return;
      }

      const segment = this.scriptSegments[segmentIndex];
      console.log('Found segment at index:', segmentIndex, segment);

      // Update the specific field in both data and rawData
      // Use Vue reactivity-friendly approach
      const updatedData = { ...segment.data };
      const updatedRawData = { ...segment.data.rawData };

      // Set the field value (supports camelCase field names)
      updatedData[field] = value;
      updatedRawData[field] = value;

      // For mediaUrl, also set the lowercase version for parser compatibility
      if (field === 'mediaUrl') {
        updatedRawData.mediaurl = value;
      }

      updatedData.rawData = updatedRawData;

      // Rebuild the cue block markdown using CueParser
      const updatedCueBlock = CueParser.formatCueToMarkdown(updatedRawData);

      // Update the segment
      this.scriptSegments.splice(segmentIndex, 1, {
        ...segment,
        data: updatedData,
        rawContent: updatedCueBlock
      });

      // Reconstruct and emit the updated script content
      const newRawContent = this.reconstructRawContent(this.scriptSegments);
      this.$emit('update:scriptContent', newRawContent);

      console.log(`✅ Cue field '${field}' updated successfully for assetId: ${assetId}`);
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
      this.$emit('update:scriptContent', newRawContent);

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

    /**
     * Apply analysis recommendations to a cue
     * Handles actions like splitting FSQ quotes, cleaning SOT transcripts, etc.
     *
     * @param {string} assetId - Cue AssetID
     * @param {string} analysisId - Analysis ID from cueAnalysisStore
     */
    async applyAnalysisRecommendations(assetId, analysisId) {
      const { getRecommendations, markReviewed } = useAsyncAnalysis();
      const recommendations = getRecommendations(analysisId);

      if (!recommendations) {
        console.warn('No recommendations found for analysis:', analysisId);
        return;
      }

      console.log(`📋 Applying recommendations for ${assetId}:`, recommendations);

      // Find the cue in scriptSegments
      const cueIndex = this.scriptSegments.findIndex(
        segment => segment.type === 'cue' && segment.data?.assetId === assetId
      );

      if (cueIndex === -1) {
        console.error('Cue not found in script segments:', assetId);
        return;
      }

      const cueSegment = this.scriptSegments[cueIndex];
      const cueData = cueSegment.data;

      // Handle FSQ split recommendations
      if (recommendations.shouldSplit && recommendations.splitRecommendations) {
        console.log(`✂️ Splitting FSQ quote into ${recommendations.splitRecommendations.length} parts`);

        // Delete original cue
        const updatedSegments = [...this.scriptSegments];
        updatedSegments.splice(cueIndex, 1);

        // Insert split cues at the same position
        const splitCues = [];
        for (let i = 0; i < recommendations.splitRecommendations.length; i++) {
          const splitQuote = recommendations.splitRecommendations[i];

          // Generate AssetID for each split
          const splitAssetId = await this.generateAssetId();

          // Word count for duration calculation
          const wordCount = splitQuote.trim().split(/\s+/).filter(w => w.length > 0).length;
          const speakerWpm = this.item?.speaker_wpm || 150;
          const durationInSeconds = Math.ceil((wordCount / speakerWpm) * 60);
          const hours = Math.floor(durationInSeconds / 3600);
          const minutes = Math.floor((durationInSeconds % 3600) / 60);
          const seconds = durationInSeconds % 60;
          const duration = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:00`;

          // Create split cue data
          const splitCueData = {
            type: cueData.type,
            assetId: splitAssetId,
            slug: `${cueData.slug}-part-${i + 1}`,
            quote: splitQuote,
            style: cueData.style || cueData.rawData?.style,
            fontFamily: cueData.fontFamily || cueData.rawData?.fontfamily,
            fontSize: cueData.fontSize || cueData.rawData?.fontsize,
            renderMode: cueData.renderMode || cueData.rawData?.rendermode,
            duration: duration,
            wordCount: wordCount,
            part: `${i + 1}x${recommendations.splitRecommendations.length}`,
            source: cueData.source || cueData.rawData?.source,
            includeAttribution: cueData.includeAttribution || cueData.rawData?.includeattribution
          };

          // Format to cue block markdown
          const cueBlock = this.formatCueBlock(splitCueData);
          splitCues.push(cueBlock);
        }

        // Insert split cues with spacing
        const insertPosition = cueIndex;
        updatedSegments.splice(insertPosition, 0, ...splitCues.map(block => ({
          type: 'cue',
          cueType: 'FSQ',
          data: CueParser.parseCueBlock(block)
        })));

        // Update script content
        const newRawContent = this.reconstructRawContent(updatedSegments);
        this.$emit('update:scriptContent', newRawContent);

        console.log(`✅ Applied FSQ split: ${recommendations.splitRecommendations.length} quotes inserted`);
      }

      // Handle other recommendation types (SOT cleanup, PKG optimization, etc.)
      else if (recommendations.action === 'modify' || recommendations.modifications) {
        console.log('🔧 Applying field modifications:', recommendations.modifications);

        // Update cue data with modifications
        const modifiedCueData = { ...cueData.rawData };

        if (recommendations.modifications) {
          recommendations.modifications.forEach(mod => {
            if (mod.field && mod.newValue !== undefined) {
              modifiedCueData[mod.field] = mod.newValue;
            }
          });
        }

        // Update the cue in segments
        const updatedSegments = [...this.scriptSegments];
        updatedSegments[cueIndex] = {
          type: 'cue',
          cueType: cueData.type,
          data: {
            ...cueData,
            rawData: modifiedCueData
          }
        };

        // Update script content
        const newRawContent = this.reconstructRawContent(updatedSegments);
        this.$emit('update:scriptContent', newRawContent);

        console.log('✅ Applied modifications to cue');
      }

      // Mark analysis as reviewed
      markReviewed(analysisId);
      console.log('✅ Analysis marked as reviewed:', analysisId);
    },

    /**
     * Format cue data to markdown cue block
     * @param {object} cueData - Cue data to format
     * @returns {string} Formatted cue block
     */
    formatCueBlock(cueData) {
      let cueBlock = '<!-- Begin Cue -->\n';

      Object.keys(cueData).forEach(key => {
        if (cueData[key]) {
          const displayKey = key.charAt(0).toUpperCase() + key.slice(1);
          cueBlock += `[${displayKey}: ${cueData[key]}]\n`;
        }
      });

      cueBlock += '<!-- End Cue -->';
      return cueBlock;
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
      this.$emit('update:scriptContent', newRawContent);

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
      this.$emit('update:scriptContent', newRawContent);

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
          // Check if pendingCueData is an array (multipart FSQ)
          if (Array.isArray(this.pendingCueData)) {
            console.log(`✅ Using pendingCueData array for ${placement.cueType} insertion (${this.pendingCueData.length} parts)`);
            // Insert each part sequentially at the same location
            this.pendingCueData.forEach((cueBlock, index) => {
              console.log(`📍 Inserting part ${index + 1}/${this.pendingCueData.length}`);
              this.insertCueAtPlacement(placement, cueBlock);
            });
          } else {
            console.log(`✅ Using pendingCueData for ${placement.cueType} insertion`);
            console.log('📍 pendingCueData preview:', this.pendingCueData.substring(0, 200));
            // We already have cue data from modal, insert it
            this.insertCueAtPlacement(placement, this.pendingCueData);
          }
          this.pendingCueData = null;
          this.pendingPlacement = null;
          this.pendingCueType = null;
        } else {
          console.warn(`⚠️ No pendingCueData found - opening ${placement.cueType} modal`);
          // No cue data yet, show modal first
          if (placement.cueType === 'IMG') {
            this.$emit('show-img-modal');
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

        // CRITICAL FIX: Get FRESH cursor position at submission time, not stale position from button click
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          // Only use current cursor if textarea is still focused
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          // Textarea not focused (user clicked in modal) - insert at end
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(sotCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ SOT cue inserted in code mode');
        return;
      }

      // SCRIPT MODE: Auto-insert based on selection
      console.log('📄 Script mode: Auto-inserting SOT based on selection');

      // Determine insertion point based on selection
      let insertionIndex;
      if (this.selectedSegmentIndex !== null && this.selectedSegmentIndex >= 0) {
        // Insert AFTER the selected segment (between zones)
        insertionIndex = this.selectedSegmentIndex + 1;
        console.log(`📍 Selected segment found at index ${this.selectedSegmentIndex}, inserting AFTER at between-zone ${insertionIndex}`);
      } else {
        // No selection - insert at bottom (after last paragraph)
        const paragraphCount = this.scriptSegments.filter(seg => seg.type === 'text').length;
        insertionIndex = paragraphCount;
        console.log(`📍 No segment selected, inserting at bottom (between-zone ${insertionIndex})`);
      }

      // Create placement object for between-paragraph insertion
      const placement = {
        type: 'between',  // CRITICAL: Always use 'between' for SOT, never 'paragraph'
        index: insertionIndex,
        cueType: 'SOT'
      };

      // Insert SOT at determined location
      this.insertCueBetweenParagraphsInRawScript(placement, sotCueText);

      // Clear pending data
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ SOT cue auto-inserted in script mode')
    },

    async handleVoCueSubmit(voCueText) {
      console.log('🎬 VO cue submitted to EditorPanel for placement-based insertion');

      this.pendingCueData = voCueText;
      this.pendingCueType = 'VO';

      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting VO at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(voCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ VO cue inserted in code mode');
        return;
      }

      // SCRIPT MODE: Auto-insert based on selection (same behavior as SOT)
      console.log('📄 Script mode: Auto-inserting VO based on selection');

      // Determine insertion point based on selection
      let insertionIndex;
      if (this.selectedSegmentIndex !== null && this.selectedSegmentIndex >= 0) {
        // Insert AFTER the selected segment (between zones)
        insertionIndex = this.selectedSegmentIndex + 1;
        console.log(`📍 Selected segment found at index ${this.selectedSegmentIndex}, inserting AFTER at between-zone ${insertionIndex}`);
      } else {
        // No selection - insert at bottom (after last paragraph)
        const paragraphCount = this.scriptSegments.filter(seg => seg.type === 'text').length;
        insertionIndex = paragraphCount;
        console.log(`📍 No segment selected, inserting at bottom (between-zone ${insertionIndex})`);
      }

      // Create placement object for between-paragraph insertion
      const placement = {
        type: 'between',  // CRITICAL: Always use 'between' for VO, never 'paragraph'
        index: insertionIndex,
        cueType: 'VO'
      };

      // Insert VO at determined location
      this.insertCueBetweenParagraphsInRawScript(placement, voCueText);

      // Clear pending data
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ VO cue auto-inserted in script mode');
    },

    async handleNatCueSubmit(natCueText) {
      console.log('🎬 NAT cue submitted to EditorPanel for placement-based insertion');

      this.pendingCueData = natCueText;
      this.pendingCueType = 'NAT';

      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting NAT at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(natCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ NAT cue inserted in code mode');
        return;
      }

      console.log('📄 Script mode: Activating placement overlay for NAT insertion');
      this.showCuePlacement = true;
      console.log('📍 Placement overlay activated - waiting for user to click drop zone');
    },

    async handleRifCueSubmit(rifCueText) {
      console.log('🎬 RIF cue submitted to EditorPanel for placement-based insertion');

      // Store the cue data for later insertion
      this.pendingCueData = rifCueText;
      this.pendingCueType = 'RIF';

      // CODE MODE: Insert directly at cursor position
      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting RIF at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(rifCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ RIF cue inserted in code mode');
        return;
      }

      // SCRIPT MODE: Auto-insert based on selection (same as SOT)
      console.log('📄 Script mode: Auto-inserting RIF based on selection');

      // Determine insertion point based on selection
      let insertionIndex;
      if (this.selectedSegmentIndex !== null && this.selectedSegmentIndex >= 0) {
        // Insert AFTER the selected segment (between zones)
        insertionIndex = this.selectedSegmentIndex + 1;
        console.log(`📍 Selected segment found at index ${this.selectedSegmentIndex}, inserting AFTER at between-zone ${insertionIndex}`);
      } else {
        // No selection - insert at bottom (after last paragraph)
        const paragraphCount = this.scriptSegments.filter(seg => seg.type === 'text').length;
        insertionIndex = paragraphCount;
        console.log(`📍 No segment selected, inserting at bottom (between-zone ${insertionIndex})`);
      }

      // Create placement object for between-paragraph insertion
      const placement = {
        type: 'between',
        index: insertionIndex,
        cueType: 'RIF'
      };

      // Insert RIF at determined location
      this.insertCueBetweenParagraphsInRawScript(placement, rifCueText);

      // Clear pending data
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ RIF cue auto-inserted in script mode');
    },

    async handlePkgCueSubmit(pkgCueText) {
      console.log('🎬 PKG cue submitted to EditorPanel for insertion');

      this.pendingCueData = pkgCueText;
      this.pendingCueType = 'PKG';

      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting PKG at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(pkgCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ PKG cue inserted in code mode');
        return;
      }

      // Script mode: Insert at end of script (placement overlay is disabled)
      console.log('📄 Script mode: Inserting PKG at end of script');
      this.insertCueAtCursor(pkgCueText);
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ PKG cue inserted at end of script');
    },

    async handleDirCueSubmit(dirCueText) {
      console.log('🎬 DIR cue submitted to EditorPanel for insertion');

      this.pendingCueData = dirCueText;
      this.pendingCueType = 'DIR';

      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting DIR at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(dirCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ DIR cue inserted in code mode');
        return;
      }

      // Script mode: Insert at end of script (placement overlay is disabled)
      console.log('📄 Script mode: Inserting DIR at end of script');
      this.insertCueAtCursor(dirCueText);
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ DIR cue inserted at end of script');
    },

    async handleBumpCueSubmit(bumpCueText) {
      console.log('🎬 BUMP cue submitted to EditorPanel for insertion');

      this.pendingCueData = bumpCueText;
      this.pendingCueType = 'BUMP';

      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting BUMP at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(bumpCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ BUMP cue inserted in code mode');
        return;
      }

      // Script mode: Insert at end of script (placement overlay is disabled)
      console.log('📄 Script mode: Inserting BUMP at end of script');
      this.insertCueAtCursor(bumpCueText);
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ BUMP cue inserted at end of script');
    },

    async handleStingCueSubmit(stingCueText) {
      console.log('🎬 STING cue submitted to EditorPanel for insertion');

      this.pendingCueData = stingCueText;
      this.pendingCueType = 'STING';

      if (this.editorMode === 'code') {
        console.log('📝 Code mode: Inserting STING at cursor position');

        // CRITICAL FIX: Get FRESH cursor position at submission time
        const codeTextarea = document.querySelector('.code-textarea textarea');
        if (codeTextarea && document.activeElement === codeTextarea) {
          this.pendingCursorPosition = codeTextarea.selectionStart;
          console.log('📝 Using current cursor position:', this.pendingCursorPosition);
        } else {
          this.pendingCursorPosition = null;
          console.log('📝 Textarea not focused - inserting at end');
        }

        this.insertCueAtCursor(stingCueText);
        this.pendingCueData = null;
        this.pendingCueType = null;
        console.log('✅ STING cue inserted in code mode');
        return;
      }

      // Script mode: Insert at end of script (placement overlay is disabled)
      console.log('📄 Script mode: Inserting STING at end of script');
      this.insertCueAtCursor(stingCueText);
      this.pendingCueData = null;
      this.pendingCueType = null;
      console.log('✅ STING cue inserted at end of script');
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
      let cursorPosition = this.pendingCursorPosition !== null
        ? this.pendingCursorPosition
        : currentScript.length;

      console.log('📝 Original cursor position:', cursorPosition);

      // UNIVERSAL RULE: Ensure we never insert inside a cue block
      cursorPosition = this.getSafeInsertionPosition(currentScript, cursorPosition);
      console.log('📝 Safe insertion position:', cursorPosition);

      // Insert cue block at cursor position with proper spacing and blank paragraph
      const beforeCursor = currentScript.slice(0, cursorPosition);
      const afterCursor = currentScript.slice(cursorPosition);

      // Add newlines around cue block and blank paragraph for proper formatting
      const newScript = beforeCursor + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n' + afterCursor;

      console.log('📝 New script length:', newScript.length);

      // Update script content
      this.$emit('update:scriptContent', newScript);

      // Clear cursor position
      this.pendingCursorPosition = null;

      console.log('✅ Cue inserted at cursor position');
    },

    // Raw Script Insertion Methods (Direct to Database)
    insertCueBetweenParagraphsInRawScript(placement, cueContent) {
      console.log('🎯 Inserting cue between segments in raw script');
      console.log('🎯 Placement index:', placement.index);

      // Get current script content
      let currentScript = this.scriptContent || '';

      // UNIVERSAL RULE: Find ALL content segments (paragraphs AND cue blocks)
      // This ensures we account for cue blocks when calculating insertion positions
      const segmentMatches = this.findAllContentSegments(currentScript);

      console.log('🎯 Found segments:', segmentMatches.length, segmentMatches.map(s => s.type));

      if (segmentMatches.length === 0) {
        // No segments found, append at end with blank paragraph
        const newScript = currentScript + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n';
        this.$emit('update:scriptContent', newScript);
        return;
      }

      // Between-zone index mapping:
      // index 0 = before first segment
      // index 1 = after segment 0
      // index 2 = after segment 1
      // etc.
      const betweenZoneIndex = placement.index;

      let insertPosition;

      if (betweenZoneIndex === 0) {
        // Insert before first segment
        insertPosition = segmentMatches[0].index;
        console.log('🎯 Inserting before first segment at position:', insertPosition);
      } else if (betweenZoneIndex > segmentMatches.length) {
        // Insert at end with blank paragraph after cue
        const newScript = currentScript + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n';
        this.$emit('update:scriptContent', newScript);
        console.log('🎯 Inserted at end with blank paragraph');
        return;
      } else {
        // Insert after segment[betweenZoneIndex - 1]
        const segmentIndex = betweenZoneIndex - 1;
        const targetSegment = segmentMatches[segmentIndex];
        insertPosition = targetSegment.endIndex;
        console.log(`🎯 Inserting after segment ${segmentIndex} (${targetSegment.type}) at position:`, insertPosition);
      }

      // UNIVERSAL RULE: Ensure we never insert inside a cue block
      insertPosition = this.getSafeInsertionPosition(currentScript, insertPosition);
      console.log('🎯 Safe insertion position:', insertPosition);

      const beforeCue = currentScript.slice(0, insertPosition);
      const afterCue = currentScript.slice(insertPosition);

      const newScript = beforeCue + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n' + afterCue;
      this.$emit('update:scriptContent', newScript);
      console.log('🎯 Cue inserted successfully');
    },

    insertCueWithinParagraphInRawScript(placement, cueContent) {
      console.log('🎯 Inserting cue within paragraph in raw script');

      // Get current script content
      let currentScript = this.scriptContent || '';

      // UNIVERSAL RULE: First check if placement.index points to a cue block
      // If so, we should insert AFTER the cue block, not within it
      const allSegments = this.findAllContentSegments(currentScript);

      if (allSegments.length > 0 && placement.index < allSegments.length) {
        const targetSegment = allSegments[placement.index];

        // If the target is a cue block, redirect to between-segments insertion
        if (targetSegment.type === 'cue') {
          console.log('🎯 Target segment is a cue block - redirecting to between-segments insertion');
          // Insert after the cue block (placement.index + 1 in between-zone terms)
          this.insertCueBetweenParagraphsInRawScript({ index: placement.index + 1 }, cueContent);
          return;
        }
      }

      // Find all paragraph elements (only paragraphs, since we already handled cue blocks)
      const paragraphMatches = [...currentScript.matchAll(/<p[^>]*class="[^"]*"[^>]*>(.*?)<\/p>/gs)];

      // Find which paragraph index this segment corresponds to
      // We need to count only paragraphs up to the segment index
      let paragraphIndex = 0;
      for (let i = 0; i < placement.index && i < allSegments.length; i++) {
        if (allSegments[i].type === 'paragraph') {
          paragraphIndex++;
        }
      }

      if (paragraphMatches.length === 0 || !paragraphMatches[paragraphIndex]) {
        // Fallback to between segments
        this.insertCueBetweenParagraphsInRawScript(placement, cueContent);
        return;
      }

      const paragraphMatch = paragraphMatches[paragraphIndex];
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

      // Always add blank paragraph after cue
      newParagraphContent += `<p class="${paragraphClass}"></p>\n\n`;

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
      // Allow space key to pass through to contenteditable elements
      if ((event.key === ' ' || event.code === 'Space') && event.target.isContentEditable) {
        return;
      }

      // Handle Ctrl+Shift+X for XTTS reading
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'x') {
        console.log('✅ CTRL+SHIFT+X triggered - toggling XTTS reading');
        event.preventDefault();
        this.toggleContextualReading();
        return;
      }

      // Handle Ctrl+Shift+C for collapse mode toggle
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'c') {
        console.log('✅ CTRL+SHIFT+C triggered - toggling collapse mode');
        event.preventDefault();
        this.collapseMode = !this.collapseMode;
        console.log('📦 Collapse mode:', this.collapseMode ? 'ACTIVE' : 'INACTIVE');
        return;
      }

      // Track ALT key state manually
      if (event.key === 'Alt') {
        this.altKeyPressed = true;
        return;
      }

      // EARLY CHECK: Don't trigger hotkeys when typing in input fields (except our own speaker textareas)
      // This check must happen BEFORE any shortcut handling to prevent shortcuts from firing in form fields
      const target = event.target;
      const isInSpeakerParagraph = target.closest && target.closest('.speaker-paragraph');
      const isInInputField = target.tagName === 'INPUT' ||
                             target.tagName === 'SELECT' ||
                             (target.tagName === 'TEXTAREA' && !isInSpeakerParagraph) ||
                             target.isContentEditable;

      // Handle Alt+Shift+A for AssetID regeneration (special case) - but NOT in input fields
      if (this.altKeyPressed && event.shiftKey && event.key.toLowerCase() === 'a' && !isInInputField) {
        console.log('✅ ALT+SHIFT+A triggered - calling regenerateCurrentCueAssetID');
        event.preventDefault();
        this.regenerateCurrentCueAssetID();
        return;
      }

      // Use manual ALT tracking instead of event.altKey for better browser compatibility
      if (!this.altKeyPressed || event.ctrlKey || event.shiftKey) {
        return;
      }

      // Skip hotkeys for input fields and contenteditable elements
      // Allow hotkeys in speaker textareas by checking if textarea is inside a speaker-paragraph
      // CRITICAL: Must exclude contentEditable to prevent hotkeys triggering while typing

      if (target.tagName === 'INPUT' ||
          (target.tagName === 'TEXTAREA' && !isInSpeakerParagraph) ||
          target.isContentEditable) {
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
          console.log('✅ ALT+G triggered - calling insertCue(GFX)');
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
        case 'r':
          console.log('✅ ALT+R triggered - calling insertCue(RIF)');
          event.preventDefault();
          this.insertCue('RIF');
          break;
        case 'p':
          event.preventDefault();
          this.insertCue('PKG');
          break;
        case 'd':
          console.log('✅ ALT+D triggered - calling insertCue(DIR)');
          event.preventDefault();
          this.insertCue('DIR');
          break;
        case 'b':
          event.preventDefault();
          this.insertCue('BUMP');
          break;
        case 't':
          event.preventDefault();
          this.insertCue('STING');
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

    handleWindowBlur() {
      // Reset ALT key state when window loses focus
      // This prevents the ALT key from getting "stuck" if user switches windows while holding ALT
      if (this.altKeyPressed) {
        this.altKeyPressed = false;
        console.log('🔑 Window blur - resetting altKeyPressed to prevent stuck modifier');
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

    // Handle paragraph click for selection and cursor position tracking
    handleParagraphClick(index, event) {
      // Always update lastKnownParagraphIndex for cue insertion positioning
      this.lastKnownParagraphIndex = index;
      console.log('🖱️ Paragraph clicked:', index, '- lastKnownParagraphIndex updated');

      if (event && (event.ctrlKey || event.metaKey)) {
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

    // Get explicit text color style for speaker
    getSpeakerTextStyle(/* speaker */) {
      // Use black text for readability - speaker is identified by background color
      return {
        color: '#000000 !important'
      };
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

      // If saved (green flash), override with green
      if (this.savedParagraphIndex === index) {
        console.log(`💚 Paragraph ${index} is SAVED - showing green`);
        return {
          backgroundColor: '#c8e6c9', // Light green
          transition: 'background-color 0.25s ease'
        };
      }

      // If focused, use highlight color from config
      if (this.focusedParagraphIndex === index) {
        console.log(`🟡 Paragraph ${index} is FOCUSED - showing highlight color`);
        return {
          backgroundColor: this.highlightBackgroundColor,
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

      // Always highlight the currently focused paragraph
      this.focusedParagraphIndex = index;
      // Also persist to lastKnownParagraphIndex for cue insertion (survives blur)
      this.lastKnownParagraphIndex = index;
      // Clear any cue focus when paragraph is focused
      this.focusedCueIndex = null;
      console.log('🟡 focusedParagraphIndex set to:', this.focusedParagraphIndex);
      console.log('🟡 lastKnownParagraphIndex set to:', this.lastKnownParagraphIndex);
    },

    // Handle cue row focus (for tab navigation)
    handleCueFocus(index) {
      console.log('🎯 Cue row focused:', index);
      this.focusedCueIndex = index;
      // Clear paragraph focus when cue is focused
      this.focusedParagraphIndex = null;
    },

    // Handle cue row blur
    handleCueBlur(index) {
      console.log('📝 Cue row blurred:', index);
      // Only clear if this cue is still the focused one
      if (this.focusedCueIndex === index) {
        this.focusedCueIndex = null;
      }
    },

    // Handle click on cue row (focus the row, not internal elements)
    handleCueRowClick(index, event) {
      // If clicking on a button inside the cue card, let it handle the event
      if (event.target.closest('button') || event.target.closest('.v-btn')) {
        return;
      }
      // Otherwise focus the row itself
      this.focusedCueIndex = index;
      event.currentTarget.focus();
    },

    // Handle paragraph blur
    async handleParagraphBlur(index) {
      console.log('📝 Paragraph blurred:', index);
      this.focusedParagraphIndex = null;
      console.log('📝 focusedParagraphIndex cleared');

      // Clear the actively editing segment flag to allow v-html to update again
      if (this.activelyEditingSegment === index) {
        this.activelyEditingSegment = null;
        console.log('📝 activelyEditingSegment cleared');
      }

      // Clear the master editing flag to allow watchers to run again
      this.isActivelyEditing = false;
      console.log('📝 isActivelyEditing cleared - watchers re-enabled');

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
            this.$emit('update:scriptContent', newRawContent);

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
    // Preserves cursor position and focus during save using pre-saved state
    async persistCurrentItemToDatabase(segmentIndex) {
      console.log('💾 Persisting current item to database (autosave)...');
      console.log('📍 Using pre-saved cursor state:', this.savedCursorState ? `segment ${this.savedCursorState.segmentIndex}` : 'none');

      try {
        // Emit save-current event to parent ContentEditor
        // This will trigger the saveCurrentItem method which persists to DB
        this.$emit('save-current');

        // Single fade flash on success (CSS animation, no re-render)
        await this.flashParagraph(segmentIndex, 'success');

        console.log('✅ Autosave successful');
      } catch (error) {
        console.error('❌ Autosave failed:', error);

        // Single fade flash on failure
        await this.flashParagraph(segmentIndex, 'error');

        // Show urgent flash notification
        if (window.flashUrgent) {
          window.flashUrgent('Autosave Failed!', window.FLASH_COLORS.RED, 3000);
        }
      }

      // Restore cursor position and focus using the pre-saved state
      // This state was captured during typing in handleContentEditableInput
      // Note: isRestoringCursor flag was already set BEFORE emit in updateTextSegment
      this.$nextTick(() => {
        try {
          this.restoreCursorPosition();
        } finally {
          // Clear flag after a brief delay to ensure Vue has finished processing
          setTimeout(() => {
            this.isRestoringCursor = false;
          }, 100);
        }
      });
    },

    // Set editing flags on focus (BEFORE any input events fire)
    // This prevents the character reversal bug by ensuring v-html is disabled before typing starts
    setEditingFlags(index) {
      this.activelyEditingSegment = index;
      this.isActivelyEditing = true;
      console.log('🎯 Editing flags set on focus for segment', index);
    },

    // Restore cursor position from savedCursorState using text offset
    // Called after autosave to return user to their editing position
    restoreCursorPosition() {
      if (!this.savedCursorState) {
        console.log('📍 No saved cursor state to restore');
        return;
      }

      const { segmentIndex, textOffset } = this.savedCursorState;
      const refName = `textareaRef-${segmentIndex}`;
      const targetElement = this.$refs[refName];

      if (!targetElement || !document.body.contains(targetElement)) {
        console.warn('📍 Target element not found for cursor restore');
        return;
      }

      try {
        // Focus the element first
        targetElement.focus();

        // Restore cursor position using text offset
        // This works even after DOM re-renders because we're using character count
        const selection = window.getSelection();
        selection.removeAllRanges();

        // Create a range and find the position matching the text offset
        const range = document.createRange();

        // Walk through text nodes to find the right position
        let currentOffset = 0;
        let found = false;

        const walker = document.createTreeWalker(
          targetElement,
          NodeFilter.SHOW_TEXT,
          null,
          false
        );

        let node = walker.nextNode();
        while (node) {
          const nodeLength = node.textContent.length;
          if (currentOffset + nodeLength >= textOffset) {
            // Found the right node
            range.setStart(node, textOffset - currentOffset);
            range.collapse(true);
            found = true;
            break;
          }
          currentOffset += nodeLength;
          node = walker.nextNode();
        }

        if (!found) {
          // Couldn't find exact position, place cursor at end
          console.log('📍 Text offset not found, placing cursor at end');
          range.selectNodeContents(targetElement);
          range.collapse(false); // false = collapse to end
        }

        selection.addRange(range);

        // Re-enable editing flags since we're still in the element
        this.activelyEditingSegment = segmentIndex;
        this.isActivelyEditing = true;

        console.log('📍 Cursor restored to segment', segmentIndex, 'at offset', textOffset);
      } catch (e) {
        console.warn('📍 Could not restore cursor position:', e);
        // Ultimate fallback: just focus the element
        targetElement.focus();
        this.activelyEditingSegment = segmentIndex;
        this.isActivelyEditing = true;
      }
    },

    // Flash the currently focused paragraph green on successful autosave
    // Called by ContentEditor after debounced autosave completes
    flashFocusedParagraphSaved() {
      console.log('💚 flashFocusedParagraphSaved called');
      console.log('💚 focusedParagraphIndex:', this.focusedParagraphIndex);
      console.log('💚 activelyEditingSegment:', this.activelyEditingSegment);

      // Try focusedParagraphIndex first, fall back to activelyEditingSegment
      let index = this.focusedParagraphIndex;
      if (index === null || index === undefined) {
        index = this.activelyEditingSegment;
      }

      if (index !== null && index !== undefined) {
        console.log('💚 Flashing paragraph', index, 'green for successful save');
        this.flashParagraph(index, 'success');
      } else {
        console.log('⚠️ No focused paragraph to flash - both focusedParagraphIndex and activelyEditingSegment are null');
      }
    },

    // Flash a paragraph with specified color
    // Uses JavaScript-based animations to support dynamic colors from settings
    // This prevents cursor loss during autosave by not triggering Vue re-renders
    // eslint-disable-next-line no-unused-vars
    async flashParagraph(index, type, count = 1) {
      const refName = `textareaRef-${index}`;
      let element = this.$refs[refName];

      console.log(`🎨 flashParagraph called: index=${index}, type=${type}, refName=${refName}`);

      // In Vue 3, refs inside v-for return arrays
      if (Array.isArray(element)) {
        element = element[0];
      }

      if (!element) {
        console.warn(`🎨 No element found for ref: ${refName}`);
        return;
      }

      // Find the parent paragraph-content div
      const paragraphDiv = element.closest('.paragraph-content');
      if (!paragraphDiv) {
        console.warn(`🎨 Could not find .paragraph-content parent for element`);
        return;
      }

      // Get flash color from settings or use defaults
      let flashColor;
      if (type === 'success') {
        // Get autosave color from settings, default to green
        const autosaveColorName = getColorValue('autosave');
        console.log(`🎨 autosave color from settings: "${autosaveColorName}"`);
        const colorToResolve = autosaveColorName || 'green';
        let resolvedColor = resolveVuetifyColor(colorToResolve);
        console.log(`🎨 resolved color: "${resolvedColor}"`);
        resolvedColor = resolvedColor || '#4CAF50';
        // Add alpha for flash effect - handle both hex and rgba/rgb
        if (resolvedColor.startsWith('rgba') || resolvedColor.startsWith('rgb')) {
          flashColor = resolvedColor;
        } else {
          // Ensure hex has # prefix for hexToRgba
          if (!resolvedColor.startsWith('#')) {
            resolvedColor = '#' + resolvedColor;
          }
          flashColor = this.hexToRgba(resolvedColor, 0.7);
        }
      } else {
        // Error color - red
        flashColor = 'rgba(244, 67, 54, 0.6)';
      }

      console.log(`🎨 Flash color: ${flashColor}`);

      // Store original state
      const originalTransition = paragraphDiv.style.transition || '';
      const hadFocusClass = paragraphDiv.classList.contains('paragraph-focused');

      // Find the inner contenteditable element (the text area that may have its own background)
      const innerTextArea = paragraphDiv.querySelector('.speaker-contenteditable, .speaker-textarea');
      const innerOriginalTransition = innerTextArea ? innerTextArea.style.transition : '';

      // Temporarily remove focus class to prevent yellow override
      if (hadFocusClass) {
        paragraphDiv.classList.remove('paragraph-focused');
        console.log(`🎨 Temporarily removed paragraph-focused class`);
      }

      // Set smooth transition for fade effect
      paragraphDiv.style.transition = 'background-color 0.25s ease-out';
      if (innerTextArea) {
        innerTextArea.style.transition = 'background-color 0.25s ease-out';
      }

      // Single flash with fade-out
      // Flash on - use !important to override speaker backgrounds on both elements
      paragraphDiv.style.setProperty('background-color', flashColor, 'important');
      if (innerTextArea) {
        innerTextArea.style.setProperty('background-color', flashColor, 'important');
      }
      await new Promise(resolve => setTimeout(resolve, 250)); // 250ms fade duration

      // Flash off - remove background (will fade out smoothly due to transition)
      paragraphDiv.style.removeProperty('background-color');
      if (innerTextArea) {
        innerTextArea.style.removeProperty('background-color');
      }

      // Restore original styles
      paragraphDiv.style.transition = originalTransition;
      if (innerTextArea) {
        innerTextArea.style.transition = innerOriginalTransition;
      }

      // Restore focus class if it was present
      if (hadFocusClass) {
        paragraphDiv.classList.add('paragraph-focused');
        console.log(`🎨 Restored paragraph-focused class`);
      }

      console.log(`🎨 Flash animation complete`);
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

      // Read autoformat settings from localStorage
      const interfaceSettings = JSON.parse(localStorage.getItem('showbuild_interface_settings') || '{}');
      const stripSpans = interfaceSettings.autoformatStripSpans !== false; // Default true
      // SUSPENDED: removeEmptyParagraphs - all empty paragraph manipulation disabled
      // const removeEmptyParagraphs = interfaceSettings.autoformatRemoveEmptyParagraphs !== false;
      const removeLeadingDashes = interfaceSettings.autoformatRemoveLeadingDashes !== false;
      const cleanWhitespace = interfaceSettings.autoformatCleanWhitespace !== false;

      let hasChanges = false;
      let formattedContent = this.scriptContent;

      // === STEP 1: Strip ALL span tags and inline styles FIRST ===
      if (stripSpans) {
      // Google Docs pastes often have unclosed <span> tags that corrupt content
      // We aggressively strip ALL span tags (open and close) regardless of matching
      const originalLength = formattedContent.length;

      // Remove Google Docs span IDs
      formattedContent = formattedContent.replace(/<span id="docs-internal-guid-[^"]*">/gi, '');

      // Remove nested <p dir="ltr"...> tags from Google Docs (keep content)
      formattedContent = formattedContent.replace(/<p dir="ltr"[^>]*>/gi, '');

      // Convert font-weight: 700 spans to <b> tags BEFORE stripping (preserve bold)
      // Must match the full tag pair first to preserve formatting
      formattedContent = formattedContent.replace(/<span[^>]*font-weight:\s*700[^>]*>([\s\S]*?)<\/span>/gi, '<b>$1</b>');
      formattedContent = formattedContent.replace(/<span[^>]*font-weight:\s*bold[^>]*>([\s\S]*?)<\/span>/gi, '<b>$1</b>');

      // Convert font-style: italic spans to <i> tags (preserve italic formatting)
      formattedContent = formattedContent.replace(/<span[^>]*font-style:\s*italic[^>]*>([\s\S]*?)<\/span>/gi, '<i>$1</i>');

      // CRITICAL: Strip ALL remaining span tags - both opening AND closing
      // This catches unclosed spans from Google Docs pastes
      formattedContent = formattedContent.replace(/<span[^>]*>/gi, '');  // Remove ALL opening <span> tags
      formattedContent = formattedContent.replace(/<\/span>/gi, '');     // Remove ALL closing </span> tags

      // Also strip any HTML-escaped span tags that might appear in content
      formattedContent = formattedContent.replace(/&lt;span[^&]*&gt;/gi, '');
      formattedContent = formattedContent.replace(/&lt;\/span&gt;/gi, '');

      // Strip <div> tags that browsers insert in contenteditable and from Google pastes
      // Empty <div></div> tags cause extra blank lines at the bottom of paragraphs
      formattedContent = formattedContent.replace(/<div><\/div>/gi, '');           // Remove empty <div></div>
      formattedContent = formattedContent.replace(/<div><br\s*\/?><\/div>/gi, ''); // Remove <div><br></div>
      formattedContent = formattedContent.replace(/<div[^>]*>/gi, '');             // Remove ALL opening <div> tags
      formattedContent = formattedContent.replace(/<\/div>/gi, '');                // Remove ALL closing </div> tags

      // Clean up whitespace inside paragraph tags that may be left after stripping spans
      // This catches: <p class="josh">  text  </p> -> <p class="josh">text</p>
      formattedContent = formattedContent.replace(/<p([^>]*)>\s+/gi, '<p$1>');
      formattedContent = formattedContent.replace(/\s+<\/p>/gi, '</p>');

      // Remove paragraphs that are now empty or contain only whitespace/br
      formattedContent = formattedContent.replace(/<p[^>]*>(\s|<br\s*\/?>)*<\/p>\s*/gi, '');

        if (formattedContent.length !== originalLength) {
          hasChanges = true;
          console.log('Autoformat: Stripped span tags and inline styles');
        }
      } // End if (stripSpans)

      // === STEP 1b: Clean whitespace (separate from span stripping) ===
      if (cleanWhitespace) {
        const beforeWhitespace = formattedContent.length;

        // Clean &nbsp; to regular spaces
        formattedContent = formattedContent.replace(/&nbsp;/gi, ' ');

        // Clean multiple consecutive spaces (but preserve single spaces)
        formattedContent = formattedContent.replace(/  +/g, ' ');

        if (formattedContent.length !== beforeWhitespace) {
          hasChanges = true;
          console.log('Autoformat: Cleaned whitespace');
        }
      } // End if (cleanWhitespace)

      // === STEP 2: Split multiple paragraphs in single <p> tags ===
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

      // === STEP 3: Remove leading dashes from paragraphs (unless part of a list) ===
      if (removeLeadingDashes) {
        // Re-match paragraphs after potential changes above
        const dashCheckMatches = [...formattedContent.matchAll(/<p(?:\s+class="([^"]*)")?[^>]*>([\s\S]*?)<\/p>/g)];

        for (const match of dashCheckMatches) {
          const fullMatch = match[0];
          const speaker = match[1] || 'josh';
          const content = match[2];

          // Check if content starts with a dash (possibly with whitespace)
          if (/^\s*[-–—]/.test(content)) {
            // Check if this is a list (multiple lines starting with dashes)
            const lines = content.split('\n').filter(l => l.trim());
            const dashLines = lines.filter(l => /^\s*[-–—]/.test(l));

            // It's a list if 2+ consecutive lines start with dashes
            const isListContent = dashLines.length >= 2 && dashLines.length === lines.length;

            if (!isListContent) {
              // Not a list - remove the leading dash
              const cleanedContent = content.replace(/^\s*[-–—]\s*/, '');
              const newTag = `<p class="${speaker}">${cleanedContent}</p>`;

              if (newTag !== fullMatch) {
                formattedContent = formattedContent.replace(fullMatch, newTag);
                hasChanges = true;
                console.log('Autoformat: Removed leading dash from paragraph');
              }
            }
          }
        }
      } // End if (removeLeadingDashes)

      // === STEP 4: Clean up empty paragraphs and cue spacing ===
      // FULLY SUSPENDED: All empty paragraph manipulation disabled
      // This was causing issues where users couldn't add paragraphs around cues
      // The autoformat was removing blank paragraphs that users need for spacing
      //
      // if (removeEmptyParagraphs) {
      //   // Remove empty paragraphs after cue blocks
      //   const cueEndPattern = /(<!-- End Cue -->)\s*(<p(?:\s+class="[^"]*")?[^>]*>\s*<\/p>)\s*(?=<p(?:\s+class="[^"]*")?[^>]*>[^<]+<\/p>|<!-- Begin Cue -->)/gi;
      //   formattedContent = formattedContent.replace(cueEndPattern, '$1\n\n');
      //
      //   // Collapse multiple consecutive empty paragraphs into one
      //   const emptyParagraphPattern = /(<p(?:\s+class="[^"]*")?[^>]*>\s*<\/p>\s*){2,}/gi;
      //   formattedContent = formattedContent.replace(emptyParagraphPattern, (match) => {
      //     const classMatch = match.match(/<p(?:\s+class="([^"]*)")?/);
      //     const className = classMatch && classMatch[1] ? classMatch[1] : 'josh';
      //     return `<p class="${className}"></p>\n`;
      //   });
      // }
      // END SUSPENDED BLOCK

      // Apply changes if any were made
      if (hasChanges) {
        console.log('Autoformat: Content was formatted');
        this.$emit('update:scriptContent', formattedContent);
        return true;
      }

      return false;
    },

    // Run autoformat and show status
    runAutoformat() {
      const wasFormatted = this.autoformatContent();

      // YAML frontmatter validation and synchronization - DISABLED
      // Frontmatter is only generated during export, not during editing
      // const yamlUpdated = this.validateAndSyncYamlFrontmatter();
      const yamlUpdated = false;

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

      // Read autoformat settings from localStorage
      const interfaceSettings = JSON.parse(localStorage.getItem('showbuild_interface_settings') || '{}');
      const autoformatEnabled = interfaceSettings.autoformatEnabled !== false; // Default to true
      const intervalSeconds = interfaceSettings.autoformatInterval || 30;

      if (!autoformatEnabled) {
        console.log('Autoformat disabled in settings');
        return;
      }

      this.autoformatTimer = setInterval(() => {
        this.runAutoformat();
      }, intervalSeconds * 1000);
      console.log(`Autoformat timer started (every ${intervalSeconds}s)`);
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
    },

    // Insert pending cue at specific index
    insertPendingCueAtIndex(index) {
      console.log('📍 Inserting pending cue at index:', index);

      const cueBlocks = Array.isArray(this.pendingCueData) ? this.pendingCueData : [this.pendingCueData];
      const frontmatter = this.extractYamlFrontmatter(this.rawScriptContent);
      const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);

      // Parse current segments
      const segments = CueParser.parseContent(contentWithoutFrontmatter);

      // Insert cue blocks at the specified index
      cueBlocks.forEach((cueBlock, i) => {
        segments.splice(index + i, 0, {
          type: 'cue',
          content: cueBlock,
          data: CueParser.parseCueBlock(cueBlock)
        });
      });

      // Reconstruct content
      const newContent = CueParser.reconstructContent(segments);
      const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent}` : newContent;

      // Use centralized emitter with validation
      this.emitScriptContent(newRawContent);
      this.$emit('save-current');
    },

    // Draggable handlers - generate stable unique keys
    // Note: VueDraggable only passes the segment item, not the index
    getSegmentKey(segment) {
      console.log('🔑 getSegmentKey called:', {
        type: segment.type,
        speaker: segment.speaker,
        contentLength: segment.content?.length,
        hasId: !!segment.id,
        segmentIndex: segment.segmentIndex,
        isDragging: this.isDragging
      });

      // If segment has an ID, use that (most reliable)
      if (segment.id) {
        const key = `seg-${segment.id}`;
        console.log('  → Using ID key:', key);
        return key;
      }

      // For cue segments, use assetId or slug for stable key
      if (segment.type === 'cue' && segment.data) {
        if (segment.data.assetId) {
          const key = `cue-asset-${segment.data.assetId}`;
          console.log('  → Using cue assetId key:', key);
          return key;
        }
        if (segment.data.slug) {
          const key = `cue-slug-${segment.data.slug}`;
          console.log('  → Using cue slug key:', key);
          return key;
        }
        // Fallback for cue: use type and a simple hash
        const key = `cue-${segment.data.type || 'unknown'}-${this.simpleHash(JSON.stringify(segment.data))}`;
        console.log('  → Using cue hash key:', key);
        return key;
      }

      // For text segments, create a stable hash from content + speaker
      if (segment.type === 'text') {
        const content = segment.content || '';
        const speaker = segment.speaker || 'unknown';

        // CRITICAL FIX: For empty paragraphs, include index to ensure unique keys
        // This prevents duplicate keys that cause Vue's virtual DOM to lose track during drag
        if (content === '') {
          const key = `text-${speaker}-empty-${segment.segmentIndex}`;
          console.log('  → Using text empty key with index:', key);
          return key;
        }

        // For non-empty content, use hash-based key
        const contentHash = this.simpleHash(content);
        const key = `text-${speaker}-${contentHash}`;
        console.log('  → Using text hash key:', key);
        return key;
      }

      // Fallback: create hash from entire segment
      return `segment-${segment.type || 'unknown'}-${this.simpleHash(JSON.stringify(segment))}`;
    },

    // Simple string hash function for generating stable keys
    simpleHash(str) {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
      }
      return Math.abs(hash).toString(36);
    },

    handleSegmentDragStart(evt) {
      console.log('🎯🎯🎯 ========== DRAG START ==========');
      console.log('  oldIndex:', evt.oldIndex);
      console.log('  draggableSegments count:', this.draggableSegments?.length);
      console.log('  cachedScriptSegments:', this.cachedScriptSegments ? `${this.cachedScriptSegments.length} segments` : 'NULL');
      this.isDragging = true;
      console.log('  isDragging set to:', this.isDragging);
    },

    handleSegmentDragEnd(evt) {
      console.log('🎯 Drag ended:', evt.oldIndex, '→', evt.newIndex);
      this.isDragging = false;

      // Process the pending segment order that was stored during drag
      if (this.pendingSegmentOrder && evt.oldIndex !== evt.newIndex) {
        console.log('📝 Processing pending segment reorder');

        // Filter out pending cues
        const realSegments = this.pendingSegmentOrder.filter(seg => !seg.isPending);

        // Reconstruct content from the new order
        const frontmatter = this.extractYamlFrontmatter(this.rawScriptContent);
        let newContent = '';

        realSegments.forEach((segment) => {
          if (segment.type === 'text') {
            const speaker = segment.speaker || 'josh';
            const content = segment.content || '';
            newContent += `<p class="${speaker}">${content}</p>\n\n`;
          } else if (segment.type === 'cue') {
            if (segment.data && segment.data.rawData) {
              newContent += CueParser.formatCueToMarkdown(segment.data.rawData);
              newContent += '\n\n';
            }
          }
        });

        const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim();

        // CRITICAL: Invalidate cache after reorder to force re-parse with new order
        this.cachedScriptSegments = null;
        this.lastParsedContent = null;

        // Clear pending order
        this.pendingSegmentOrder = null;

        // Now emit the update after drag is complete (with validation)
        this.emitScriptContent(newRawContent);
        this.$emit('save-current');
      }
    },

    /**
     * Force refresh of script segments by invalidating cache.
     * Called by parent (ContentEditor) when external content changes occur,
     * such as SOT processing completion updating the cue block data.
     */
    forceRefreshSegments() {
      console.log('🔄 forceRefreshSegments called - invalidating segment cache');
      this.cachedScriptSegments = null;
      this.lastParsedContent = null;
      // Force Vue to re-evaluate the computed property
      this.$nextTick(() => {
        console.log('🔄 Segment cache invalidated, segments will re-parse on next access');
      });
    }
  }
}
</script>

<style scoped>
/* Yellow highlight for slug field that needs attention */
.slug-needs-attention :deep(.v-field) {
  background-color: rgba(255, 235, 59, 0.25) !important;
}

.slug-needs-attention :deep(.v-field__outline) {
  border-color: rgba(255, 235, 59, 0.6) !important;
}

/* Editor panel content - no scrolling, parent wrapper handles it */
.editor-panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: visible !important; /* Required for sticky children to work */
  position: relative; /* Required for segment locked overlay positioning */
}

.editor-panel-content.full-width {
  width: 100%;
}

/* Segment Locked Overlay */
.segment-locked-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(128, 128, 128, 0.85);
  backdrop-filter: blur(2px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.locked-content {
  text-align: center;
  color: white;
  padding: 32px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 12px;
  min-width: 280px;
}

.locked-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
}

.locked-message {
  font-size: 1rem;
  line-height: 1.6;
  opacity: 0.9;
}

.locked-message strong {
  font-size: 1.1rem;
  display: block;
  margin-top: 4px;
}

.locked-time {
  font-size: 0.85rem;
  opacity: 0.7;
  margin-top: 12px;
}

/* Ensure v-card uses flex layout properly */
.editor-card {
  display: flex !important;
  flex-direction: column !important;
  height: auto !important;
  max-height: none !important;
  min-height: 0 !important;
  overflow: visible !important; /* Required for sticky children to work */
}

/* Override any Vuetify fill-height constraints */
.editor-card.fill-height {
  height: auto !important;
  max-height: none !important;
  min-height: 0 !important;
}

.editor-card .v-card-text {
  height: auto !important;
  max-height: none !important;
  overflow: visible !important; /* Required for sticky children */
}

.editor-content {
  display: flex;
  flex-direction: column;
  overflow: visible !important; /* Required for sticky children */
  min-height: calc(100vh - 180px);
}

.editor-content .fill-height {
  min-height: 0; /* Allow content to expand naturally */
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
  min-height: calc(100vh - 180px);
}

.slug-field-toolbar-container {
  margin-left: 16px;
  display: flex;
  gap: 12px;
}

.slug-field-with-validation {
  display: flex;
  align-items: center;
  gap: 4px;
  position: relative;
}

.slug-validation-icon {
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%) scale(0.75);
}

.script-slug-field-inline,
.script-title-field-inline {
  flex: 0 0 auto;
  max-width: 300px;
  min-width: 188px;
  transform: scale(0.75);
  transform-origin: left center;
}

/* Remove rounded corners */
.script-slug-field-inline :deep(.v-field),
.script-title-field-inline :deep(.v-field) {
  border-radius: 0 !important;
}

/* Disable all label transitions */
.script-slug-field-inline :deep(.v-label),
.script-title-field-inline :deep(.v-label) {
  transition: none !important;
}

/* Make floating label larger when floated and move down */
.script-slug-field-inline :deep(.v-label--floating),
.script-title-field-inline :deep(.v-label--floating) {
  font-size: 15px !important;
  transform: translateY(-0.3em) scale(0.85) !important;
  transition: none !important;
}

/* Also target the label in focused state */
.script-slug-field-inline :deep(.v-field--focused .v-label),
.script-title-field-inline :deep(.v-field--focused .v-label) {
  transform: translateY(-0.3em) scale(0.85) !important;
  transition: none !important;
}

/* Specifically target title field label in all states */
.script-title-field-inline :deep(.v-field--focused .v-label--floating),
.script-title-field-inline :deep(.v-field .v-label--floating) {
  font-size: 15px !important;
  transform: translateY(-0.3em) scale(0.85) !important;
  transition: none !important;
}

/* Yellow highlight when inline slug field is empty */
.script-slug-field-inline.slug-needs-attention :deep(.v-field) {
  background-color: rgba(255, 235, 59, 0.25) !important;
}

/* Yellow highlight when inline title field is empty */
.script-title-field-inline.title-needs-attention :deep(.v-field) {
  background-color: rgba(255, 235, 59, 0.25) !important;
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
  z-index: 100 !important; /* High z-index to stay above cues toolbar */
  background-color: #f5f5f5 !important;
  border-bottom: 1px solid #e0e0e0 !important;
  padding: 6px 8px !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important; /* Slightly stronger shadow */
}

/* Sticky Cues Toolbar */
.cues-toolbar-sticky {
  position: sticky !important;
  top: 62px !important; /* Position below the main toolbar (48px + padding) */
  z-index: 9 !important;
  background-color: #f5f5f5 !important;
  border-bottom: 1px solid #e0e0e0 !important;
  padding: 6px 8px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

/* Sticky Text Formatting Box */
.text-formatting-sticky {
  position: sticky !important;
  top: 120px !important; /* Position below main toolbar (60px) + cues toolbar (60px) */
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
  height: 48px !important;
  min-height: 48px !important;
  min-width: 100px !important;
  padding: 2px 4px !important;
  border-radius: 0 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.2s ease !important;
}

.mode-btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
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
  height: 48px !important;
  min-height: 48px !important;
}

.save-all-btn:disabled {
  background-color: rgb(var(--v-theme-success)) !important;
  color: white !important;
  opacity: 1 !important;
}

/* Toolbar Button Height Consistency */
.xtts-read-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.metadata-toggle-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.more-options-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

/* All toolbar buttons should have consistent height */
.editor-toolbar-sticky .v-btn {
  height: 48px !important;
  min-height: 48px !important;
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
  top: 62px !important; /* Below the mode toolbar (48px + padding) */
  z-index: 9 !important;
  width: 100% !important;
  background-color: #f5f5f5 !important;
  border-bottom: 1px solid #e0e0e0 !important;
  padding: 6px 8px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
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
  font-size: 0.65rem !important;
  opacity: 1 !important;
  line-height: 1 !important;
  font-weight: 700 !important;
  color: #000000 !important;
  text-shadow: 0 0 3px rgba(255, 255, 255, 0.9), 0 0 1px rgba(255, 255, 255, 1) !important;
  letter-spacing: 0.3px !important;
}

.cue-btn-content-flex .v-icon {
  font-size: 16px !important;
}

/* DIR button - increase text contrast */
.dir-btn .cue-label,
.dir-btn .hotkey-display,
.dir-btn .v-icon {
  color: #000000 !important;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
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
  overflow: visible !important; /* Required for sticky children */
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
  padding: 20px 40px 20vh 40px;
  background-color: white;
  font-family: 'Times New Roman', serif;
  font-size: 14px;
  line-height: 1.5;
  height: auto;
  min-height: calc(100vh - 250px);
  max-height: none;
  overflow: visible;
}

/* Speaker Paragraph Styling */
.speaker-paragraph {
  margin: 0 0 8px 0;
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
  font-size: 1.125em;  /* Reduced by 25% from 1.5em */
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
  padding: 0;
  border-radius: 0;
  position: relative;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: flex-start;
  gap: 0px;
}

/* Invisible hover extension to reach action buttons positioned outside */
.paragraph-content::after {
  content: '';
  position: absolute;
  top: 0;
  right: -40px; /* Extend past the buttons (at -28px with 24px width = -52px edge, so -40px gives overlap) */
  width: 40px;
  height: 100%;
  pointer-events: auto; /* Capture mouse events */
}

/* Line numbers column */
.line-numbers-column {
  flex-shrink: 0;
  width: 50px;
  display: flex;
  flex-direction: column;
  padding-top: 2px;
  user-select: none;
  margin-left: 4px;
}

.line-number {
  text-align: right;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  line-height: 27px; /* Must match .speaker-contenteditable line-height */
  height: 27px;
  padding-right: 8px;
  white-space: nowrap;
  box-sizing: border-box;
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
  background-color: rgba(76, 175, 80, 0.5) !important; /* Green flash on save */
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

/* Needs Attention Flag styling - uses CSS variables from settings */
.paragraph-content.paragraph-needs-attention {
  background-color: var(--needs-attention-bg, rgba(255, 152, 0, 0.3)) !important;
  border-left: 4px solid var(--needs-attention-border, #FF9800) !important;
}

/* Override speaker backgrounds when needs attention - must be specific */
.paragraph-content.seg-0.paragraph-needs-attention,
.paragraph-content.seg-1.paragraph-needs-attention,
.paragraph-content.seg-2.paragraph-needs-attention,
.paragraph-content.seg-3.paragraph-needs-attention,
.paragraph-content.seg-4.paragraph-needs-attention,
.paragraph-content.seg-5.paragraph-needs-attention,
.paragraph-content.seg-6.paragraph-needs-attention,
.paragraph-content.seg-7.paragraph-needs-attention,
.paragraph-content.seg-8.paragraph-needs-attention,
.paragraph-content.seg-9.paragraph-needs-attention {
  background-color: var(--needs-attention-bg, rgba(255, 152, 0, 0.3)) !important;
}

/* Make textarea background transparent when paragraph needs attention */
.paragraph-content.paragraph-needs-attention .speaker-textarea,
.paragraph-content.paragraph-needs-attention .speaker-textarea :deep(.v-field),
.paragraph-content.paragraph-needs-attention .speaker-textarea :deep(.v-field__input),
.paragraph-content.paragraph-needs-attention .speaker-textarea :deep(textarea),
.paragraph-content.paragraph-needs-attention .speaker-contenteditable {
  background-color: transparent !important;
}

/* Flag button positioning - outside segment, above delete button */
.paragraph-flag-btn,
.paragraph-flag-btn.v-btn,
.paragraph-flag-btn.v-btn--icon {
  position: absolute !important;
  right: -28px !important; /* Outside segment, touching edge */
  top: 50% !important;
  transform: translateY(-105%) !important; /* Position above the delete button */
  opacity: 0.7;
  z-index: 10;
  min-width: 24px !important;
  max-width: 24px !important;
  width: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  height: 24px !important;
  background-color: var(--needs-attention-btn-bg, rgba(255, 152, 0, 0.15)) !important;
  border-radius: 4px !important;
  padding: 0 !important;
}

.paragraph-flag-btn:hover {
  opacity: 1;
  background-color: var(--needs-attention-btn-hover, rgba(255, 152, 0, 0.4)) !important;
}

.paragraph-flag-btn.flag-active {
  opacity: 1;
  background-color: var(--needs-attention-btn-active, rgba(255, 152, 0, 0.5)) !important;
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

/* CSS Animation-based flash effects (non-reactive, preserves cursor/focus) */
/* 3 distinct flashes over 1.2s - each flash is 200ms on, 200ms off */
@keyframes flash-save {
  0% { background-color: inherit; }
  /* Flash 1 */
  8% { background-color: rgba(76, 175, 80, 0.7); }
  16% { background-color: inherit; }
  /* Flash 2 */
  33% { background-color: rgba(76, 175, 80, 0.7); }
  50% { background-color: inherit; }
  /* Flash 3 */
  66% { background-color: rgba(76, 175, 80, 0.7); }
  83% { background-color: inherit; }
  100% { background-color: inherit; }
}

@keyframes flash-error {
  0% { background-color: inherit; }
  /* Flash 1 */
  8% { background-color: rgba(244, 67, 54, 0.6); }
  16% { background-color: inherit; }
  /* Flash 2 */
  33% { background-color: rgba(244, 67, 54, 0.6); }
  50% { background-color: inherit; }
  /* Flash 3 */
  66% { background-color: rgba(244, 67, 54, 0.6); }
  83% { background-color: inherit; }
  100% { background-color: inherit; }
}

.paragraph-content.flash-save-animation {
  animation: flash-save 1.2s ease-in-out;
}

.paragraph-content.flash-error-animation {
  animation: flash-error 1.2s ease-in-out;
}

/* Ensure textarea stays transparent during flash animation */
.paragraph-content.flash-save-animation .speaker-textarea,
.paragraph-content.flash-save-animation .speaker-contenteditable,
.paragraph-content.flash-error-animation .speaker-textarea,
.paragraph-content.flash-error-animation .speaker-contenteditable {
  background-color: transparent !important;
}

/* Paragraph hover action buttons */
.paragraph-delete-btn,
.paragraph-delete-btn.v-btn,
.paragraph-delete-btn.v-btn--icon {
  position: absolute !important;
  right: -28px !important; /* Outside segment, touching edge */
  top: 50% !important;
  transform: translateY(5%) !important; /* Below center, under the flag */
  background-color: #f44336 !important;
  min-width: 24px !important;
  max-width: 24px !important;
  width: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  height: 24px !important;
  color: white !important;
  opacity: 0;
  animation: fadeIn 0.2s ease-in forwards;
  z-index: 10;
  border-radius: 4px !important;
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 17pt;
  line-height: 1.5;
  padding: 0;
  background-color: #fafafa !important; /* Even lighter gray background */
}

/* Contenteditable div styling - renders HTML formatting */
.speaker-contenteditable {
  min-height: 1.5em;
  padding: 2px 5px !important;
  outline: none;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  cursor: text;
  /* Match line-height with line numbers for proper alignment */
  font-size: 19px;
  line-height: 27px; /* Must match .line-number height */
  /* Force LTR text direction to prevent RTL character input issues */
  direction: ltr !important;
  unicode-bidi: plaintext !important;
  text-align: left !important;
}

/* Placeholder for empty contenteditable */
.speaker-contenteditable:empty::before {
  content: attr(data-placeholder);
  color: #9e9e9e;
  font-style: italic;
  pointer-events: none;
}

/* Formatting styles inside contenteditable */
.speaker-contenteditable strong,
.speaker-contenteditable b {
  font-weight: bold;
}

.speaker-contenteditable em,
.speaker-contenteditable i {
  font-style: italic;
}

.speaker-contenteditable u {
  text-decoration: underline;
}

.speaker-contenteditable mark {
  background-color: #ffeb3b;
  padding: 0 2px;
  border-radius: 2px;
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
  font-size: 17pt !important;
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
  position: relative; /* For absolute positioning of flag note panels */
}

.text-segment {
  background-color: transparent;
  border: none;
  margin: 0;
  padding: 0;
}

.segment-textarea {
  font-family: 'Roboto', sans-serif !important;
  font-size: 17pt !important;
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
  font-size: 17pt !important;
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
  display: flex;
  width: 100%;
  padding: 8px 12px;
  margin-left: -12px;
  margin-right: -12px;
  width: calc(100% + 24px);
  border-radius: 4px;
  transition: background-color 0.2s ease;
  position: relative; /* For flag button positioning */
}

/* Invisible hover extension to reach flag button positioned outside */
.cue-segment::after {
  content: '';
  position: absolute;
  top: 0;
  right: -40px;
  width: 40px;
  height: 100%;
  pointer-events: auto;
}

.cue-segment.cue-focused {
  /* Full row highlight when cue is selected */
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);
}

/* Cue segment needs-attention highlight - full row */
.cue-segment.cue-needs-attention {
  background-color: var(--needs-attention-bg, rgba(255, 152, 0, 0.3)) !important;
  border-left: 4px solid var(--needs-attention-border, #FF9800) !important;
}

/* Cue flag button positioning */
.cue-flag-btn,
.cue-flag-btn.v-btn,
.cue-flag-btn.v-btn--icon {
  position: absolute !important;
  right: -28px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  opacity: 0.7;
  z-index: 10;
  min-width: 24px !important;
  max-width: 24px !important;
  width: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  height: 24px !important;
  background-color: var(--needs-attention-btn-bg, rgba(255, 152, 0, 0.15)) !important;
  border-radius: 4px !important;
  padding: 0 !important;
}

.cue-flag-btn:hover {
  opacity: 1;
  background-color: var(--needs-attention-btn-hover, rgba(255, 152, 0, 0.4)) !important;
}

.cue-flag-btn.flag-active {
  opacity: 1;
  background-color: var(--needs-attention-btn-active, rgba(255, 152, 0, 0.5)) !important;
}

/* Flag Note Panel - base styles */
.flag-note-panel {
  width: 280px;
  background-color: #fff;
  border: 2px solid var(--needs-attention-border, #FF9800);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  z-index: 100;
  padding: 0;
  overflow: visible; /* Allow content to determine height */
}

/* Teleported flag note panel - positioned via JavaScript */
.flag-note-panel.flag-note-teleported {
  z-index: 9999; /* High enough to appear above everything except modals */
}

.flag-note-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: var(--needs-attention-bg, rgba(255, 152, 0, 0.15));
  border-bottom: 1px solid var(--needs-attention-border, #FF9800);
}

.flag-note-title {
  flex: 1;
  font-weight: 600;
  font-size: 13px;
  color: #333;
}

.flag-note-close {
  opacity: 0.6;
}

.flag-note-close:hover {
  opacity: 1;
}

.flag-note-minimize {
  margin-left: auto;
  opacity: 0.6;
}

.flag-note-minimize:hover {
  opacity: 1;
}

.flag-note-textarea {
  margin: 12px;
}

.flag-note-textarea :deep(.v-field) {
  background-color: #fafafa;
}

.flag-note-textarea :deep(textarea) {
  font-size: 13px;
  line-height: 1.4;
  max-height: none !important; /* Allow unlimited growth */
  overflow-y: visible !important; /* No scrollbar */
}

.flag-note-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 12px 12px;
}

.cue-segment:focus {
  outline: none;
}

.cue-segment:focus-visible {
  outline: 2px solid rgba(var(--v-theme-primary), 0.5);
  outline-offset: 2px;
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
  min-height: 200px;
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

/* Drag handle column - appears before line numbers */
.drag-handle-column {
  flex-shrink: 0;
  width: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
  transition: all 0.2s ease;
  cursor: grab;
  align-self: stretch;
  min-height: 100%;
}

.drag-handle-column:hover {
  opacity: 1;
  background: rgba(33, 150, 243, 0.08);
  border-radius: 6px;
}

.drag-handle-column:active {
  cursor: grabbing;
}

.drag-handle-column .v-icon {
  color: rgba(0, 0, 0, 0.4);
  transition: color 0.2s ease;
}

.drag-handle-column:hover .v-icon {
  color: rgb(33, 150, 243);
}

.speaker-paragraph {
  position: relative;
}

/* Draggable states (for speaker header drag handle) */
.drag-handle {
  transition: all 0.2s ease;
  opacity: 0.6;
  color: rgba(0, 0, 0, 0.4);
}

.drag-handle:hover {
  opacity: 1;
  color: rgb(var(--v-theme-primary)) !important;
  transform: scale(1.2);
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.content-segment {
  transition: opacity 0.2s ease, transform 0.2s ease, max-height 0.2s ease;
}

.ghost-segment {
  height: 60px !important;
  min-height: 60px !important;
  background: var(--draglight-color, rgba(33, 150, 243, 0.15)) !important;
  border: 3px dashed var(--dropline-color, rgb(33, 150, 243)) !important;
  border-radius: 4px !important;
  position: relative !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  visibility: visible !important;
}

.ghost-segment::before {
  content: "DROP HERE";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--dropline-color, rgb(33, 150, 243));
  font-family: Helvetica, Arial, sans-serif;
  font-weight: 700;
  font-size: 22px;
  letter-spacing: 3px;
  text-transform: uppercase;
  opacity: 0.25;
  z-index: 10;
}

/* Hide the actual content inside the ghost placeholder */
.ghost-segment > * {
  visibility: hidden !important;
}

.chosen-segment {
  opacity: 0.9;
  cursor: grabbing !important;
  outline: 2px solid var(--dropline-color, rgb(33, 150, 243)) !important;
  outline-offset: 2px;
}

.drag-segment {
  opacity: 0.8;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Collapse cue cards to title bar only when actively being dragged (not on mousedown) */
.drag-segment .cue-card .v-card-text,
.drag-segment .cue-card .v-card-actions {
  display: none !important;
}

.drag-segment .cue-card {
  max-height: 60px !important;
  overflow: hidden !important;
}

/* Keep paragraph content visible but slightly transparent when dragging */
.drag-segment .paragraph-content {
  opacity: 0.6 !important;
}

/* Pending cue styling - highlight and pulse */
.content-segment:has([data-pending="true"]) {
  animation: pending-pulse 2s ease-in-out infinite;
  border: 3px dashed rgb(var(--v-theme-primary));
  border-radius: 8px;
  background: rgba(var(--v-theme-primary), 0.05);
}

@keyframes pending-pulse {
  0%, 100% {
    border-color: rgb(var(--v-theme-primary));
    box-shadow: 0 0 0 0 rgba(var(--v-theme-primary), 0.4);
  }
  50% {
    border-color: rgba(var(--v-theme-primary), 0.6);
    box-shadow: 0 0 0 8px rgba(var(--v-theme-primary), 0);
  }
}

/* Cue Card Alignment Classes */
.cue-segment.cue-align-left {
  display: flex;
  justify-content: flex-start;
}

.cue-segment.cue-align-center {
  display: flex;
  justify-content: center;
}

.cue-segment.cue-align-right {
  display: flex;
  justify-content: flex-end;
}

/* Ensure cue cards have appropriate max-width for alignment */
.cue-segment .cue-card,
.cue-segment .image-cue-card,
.cue-segment .placeholder-cue-card {
  max-width: 800px;
  width: 100%;
}

/* ===== COLLAPSE MODE STYLES ===== */

/* Collapse mode indicator in toolbar */
.collapse-mode-indicator {
  display: flex;
  align-items: center;
  padding: 4px 12px;
  margin: 0 16px;
  background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
  color: white;
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 1px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.4);
  animation: collapse-pulse 2s ease-in-out infinite;
}

@keyframes collapse-pulse {
  0%, 100% { box-shadow: 0 2px 8px rgba(255, 152, 0, 0.4); }
  50% { box-shadow: 0 2px 16px rgba(255, 152, 0, 0.7); }
}

/* Collapsed paragraph styling - 25% shorter than original 36px */
.collapsed-paragraph {
  display: flex;
  align-items: center;
  padding: 4px 12px;
  margin: 2px 0;
  border-radius: 4px;
  min-height: 27px;
  transition: all 0.2s ease;
  position: relative;
}

.collapsed-paragraph:hover {
  background-color: rgba(0, 0, 0, 0.08) !important;
}

.collapsed-paragraph-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
}

.collapsed-line-range {
  font-weight: 700;
  color: #1976D2;
  background: rgba(25, 118, 210, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
  min-width: 55px;
  text-align: center;
  flex-shrink: 0;
}

.collapsed-text-left {
  color: #424242;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
}

.collapsed-text-right {
  color: #616161;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  margin-left: auto;
}

/* Collapsed cue styling */
.collapsed-cue {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  margin: 2px 0;
  border-radius: 4px;
  min-height: 40px;
  transition: all 0.2s ease;
  position: relative;
}

.collapsed-cue:hover {
  filter: brightness(0.95);
}

.collapsed-cue-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
}

.collapsed-cue-index {
  font-weight: 700;
  color: #9C27B0;
  background: rgba(156, 39, 176, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
}

.collapsed-cue-type {
  font-weight: 700;
  text-transform: uppercase;
  min-width: 50px;
}

.collapsed-cue-divider {
  color: #9E9E9E;
  font-weight: 300;
}

.collapsed-cue-slug {
  color: #424242;
  font-weight: 500;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed-cue-duration {
  color: #757575;
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
}

.collapsed-cue-outcue {
  color: #1976D2;
  font-style: italic;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Shared delete button for collapsed elements */
.collapsed-delete-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #F44336 !important;
}

.collapsed-paragraph:hover .collapsed-delete-btn,
.collapsed-cue:hover .collapsed-delete-btn {
  opacity: 1;
}

/* Cue segment in collapsed mode - full width, override alignment */
.cue-segment.cue-collapsed {
  padding: 0;
  margin: 0;
  display: block !important;
  justify-content: flex-start !important;
}

.cue-segment.cue-collapsed .collapsed-cue {
  width: 100%;
  max-width: 100%;
}

/* Drag handle adjustments for collapsed mode */
.collapsed-paragraph .drag-handle-column,
.collapsed-cue .drag-handle-column {
  width: 24px;
  opacity: 0.6;
}

.collapsed-paragraph:hover .drag-handle-column,
.collapsed-cue:hover .drag-handle-column {
  opacity: 1;
}

/* ===== END COLLAPSE MODE STYLES ===== */
</style>
