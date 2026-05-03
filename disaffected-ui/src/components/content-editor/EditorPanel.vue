<template>
  <div :class="['editor-panel-content', !showRundownPanel ? 'full-width' : '']" :style="editorPanelCssVars">
    <!-- Other-user-on-this-segment banner -->
    <div v-if="otherUsersOnThisSegment.length > 0" class="presence-banner">
      <v-icon size="small" class="me-2" color="warning">mdi-account-multiple</v-icon>
      <span class="presence-banner-text">
        Also editing this segment:
        <span
          v-for="(u, i) in otherUsersOnThisSegment"
          :key="u.id"
          class="ms-1"
        >
          <v-chip
            :color="u.chip_color || 'primary'"
            size="x-small"
            variant="flat"
            class="presence-banner-chip"
          >
            <v-avatar start :color="u.chip_color || 'primary'" size="14" class="me-1">
              <v-img v-if="u.profile_picture" :src="u.profile_picture" />
              <span v-else style="font-size:8px;font-weight:600;color:#fff;">{{ presenceInitials(u) }}</span>
            </v-avatar>
            {{ u.display_name || u.username }}
          </v-chip>
          <span v-if="i < otherUsersOnThisSegment.length - 1">,</span>
        </span>
      </span>
    </div>

    <!-- Flash Message for Cue Insertion -->
    <v-snackbar
      v-model="flashMessage.show"
      :timeout="flashMessage.timeout || 500"
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

    <!-- Paste Processing Overlay -->
    <div v-if="isPasting" class="paste-processing-overlay">
      <div class="paste-processing-content">
        <v-progress-circular indeterminate size="48" color="amber" width="4" />
        <div class="paste-processing-title">De-Googleizing the bullshit from Google's bullshit clipboard mess.</div>
      </div>
    </div>

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

        <div class="btn-group-wrapper">
          <span class="btn-group-label">EDIT MODES</span>
          <v-btn-toggle
            :model-value="editorMode"
            @update:model-value="$emit('update:editorMode', $event)"
            mandatory
            class="editor-mode-toggle"
          >
            <v-btn value="script" size="small" class="mode-btn" rounded="0">
              <v-icon left size="small">mdi-script-text</v-icon>
              Script
            </v-btn>
            <v-btn value="code" size="small" class="mode-btn" rounded="0">
              <v-icon left size="small">mdi-code-braces</v-icon>
              Code
            </v-btn>
          </v-btn-toggle>
        </div>

        <v-spacer></v-spacer>

        <!-- Views Group (right side) -->
        <div class="btn-group-wrapper">
          <span class="btn-group-label">VIEWS</span>
          <div class="btn-group-buttons">
            <v-btn size="small" class="mode-btn" rounded="0" @click="openIpadMode" :disabled="!currentEpisodeNumber">
              <v-icon left size="small">mdi-tablet</v-icon>
              iPad
            </v-btn>
            <v-btn size="small" class="mode-btn" rounded="0" disabled>
              <v-icon left size="small">mdi-phone-outline</v-icon>
              Caller
            </v-btn>
            <v-btn size="small" class="mode-btn" rounded="0" disabled>
              <v-icon left size="small">mdi-monitor-eye</v-icon>
              Director
            </v-btn>
            <v-btn size="small" class="mode-btn" rounded="0" disabled>
              <v-icon left size="small">mdi-script-text</v-icon>
              Prompter
            </v-btn>
          </div>
        </div>

        <!-- Collapse Mode Indicator (centered, prominent) -->
        <div v-if="collapseMode && editorMode === 'script'" class="collapse-mode-indicator">
          <v-icon size="small" class="mr-1">mdi-arrow-collapse-vertical</v-icon>
          COLLAPSE MODE
          <v-tooltip activator="parent" location="bottom">
            Press Ctrl+Shift+C to exit collapse mode
          </v-tooltip>
        </div>

      </v-toolbar>

      <!-- Editor Content Area -->
      <v-card-text class="pa-0 editor-content">

        <!-- Script Mode - Enhanced Visual Editor with Cue Cards -->
        <div v-if="editorMode === 'script'" class="d-flex flex-column script-mode-container">

          <!-- Insert Cues Toolbar (collapsible, shared across modes) -->
          <div v-if="showCuesToolbar" class="editor-cues-toolbar cues-toolbar-sticky">
            <div class="cue-toolbar-row">
              <!-- ADD CUE trigger button -->
              <v-btn
                variant="flat"
                size="small"
                class="add-cue-trigger"
                :class="{ 'add-cue-active': cueMenuOpen }"
                color="grey-darken-3"
                @click="toggleCueMenu"
              >
                <v-icon size="small" class="mr-1" :class="{ 'rotate-90': cueMenuOpen }">mdi-plus</v-icon>
                <span class="add-cue-label">ADD CUE</span>
                <span class="add-cue-hotkey">ALT+C</span>
              </v-btn>

              <!-- Cue buttons (twirl out) -->
              <transition name="cue-expand">
                <div v-if="cueMenuOpen" class="cue-buttons-flex-container">
                  <v-btn
                    v-for="cue in cueDefinitions"
                    :key="cue.type"
                    variant="flat"
                    class="cue-btn-flex"
                    :class="[cue.btnClass, { 'cue-btn-flash': flashingCueType === cue.type }]"
                    :style="getCueButtonStyle(cue.type)"
                    @click="insertCueFromMenu(cue.type)"
                  >
                    <div class="cue-btn-content-flex">
                      <span class="cue-label">{{ cue.label }}</span>
                      <span class="hotkey-display">{{ cue.key.toUpperCase() }}</span>
                    </div>
                    <v-tooltip activator="parent" location="bottom">{{ cue.tooltip }} (Alt+{{ cue.key.toUpperCase() }})</v-tooltip>
                  </v-btn>
                </div>
              </transition>
            </div>
          </div>

          <!-- Text formatting styles flyout -->
          <div class="styles-flyout-container text-formatting-sticky">
            <v-btn
              size="x-small"
              variant="text"
              class="styles-toggle-btn"
              @click="showStylesFlyout = !showStylesFlyout"
            >
              <v-icon size="small" :class="{ 'rotate-90': showStylesFlyout }">mdi-chevron-right</v-icon>
              Styles
            </v-btn>
            <transition name="flyout">
              <div v-if="showStylesFlyout" class="styles-flyout-items">
                <span class="formatting-hotkey"><strong>CTRL+B</strong> Bold</span>
                <span class="formatting-hotkey"><strong>CTRL+I</strong> Italic</span>
                <span class="formatting-hotkey"><strong>CTRL+U</strong> Underline</span>
                <span class="formatting-hotkey"><strong>CTRL+ALT+H</strong> Highlight</span>
                <span class="formatting-hotkey"><strong>ALT+/</strong> Revise</span>
                <span class="formatting-hotkey"><strong>ALT+.</strong> Add</span>
                <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regen AssetID</span>
              </div>
            </transition>
          </div>

          <!-- Script Content Area with embedded fields -->
          <div class="script-content-container flex-grow-1">
            <!-- Multi-Selection Actions -->
            <div v-if="multiSelectionCount > 0" class="multi-selection-toolbar">
              <div class="selection-count">
                <span class="selection-count-number">{{ multiSelectionCount }}</span>
                <span class="selection-count-label">paragraph{{ multiSelectionCount > 1 ? 's' : '' }} selected</span>
              </div>
              <div class="selection-actions">
                <v-btn
                  v-if="multiSelectionCount === 2"
                  color="primary"
                  variant="flat"
                  size="small"
                  @click="swapSelectedParagraphs"
                  prepend-icon="mdi-swap-vertical"
                >
                  Swap
                </v-btn>
                <v-btn
                  v-if="multiSelectionCount >= 2"
                  color="info"
                  variant="flat"
                  size="small"
                  @click="joinSelectedParagraphs"
                  prepend-icon="mdi-set-merge"
                >
                  Join
                </v-btn>
                <v-btn
                  color="error"
                  variant="flat"
                  size="small"
                  @click="deleteMultipleSegments"
                  prepend-icon="mdi-delete"
                >
                  Delete {{ multiSelectionCount }} paragraph{{ multiSelectionCount > 1 ? 's' : '' }}
                </v-btn>
                <v-btn
                  variant="text"
                  size="small"
                  @click="clearMultiSelection"
                  prepend-icon="mdi-close"
                >
                  Cancel
                </v-btn>
              </div>
            </div>

            <!-- Segment Title -->
            <div v-if="useVisualScriptMode && !hasNoItem" class="segment-title-header" :class="{ 'segment-title-placeholder': !item?.title || /^Segment-\d+$/i.test(item.title) }">
              {{ item?.title && !/^Segment-\d+$/i.test(item.title) ? item.title : 'Enter a segment title' }}
            </div>

            <!-- Enhanced Script Content with Visual Cue Cards -->
            <div v-if="useVisualScriptMode && !hasNoItem" class="visual-script-container">
              <!-- Upper scroll zone indicator -->
              <div
                v-if="isDragging"
                class="scroll-zone-indicator scroll-zone-upper"
                title="Upper auto-scroll zone"
              ></div>

              <!-- Lower scroll zone indicator -->
              <div
                v-if="isDragging"
                class="scroll-zone-indicator scroll-zone-lower"
                title="Lower auto-scroll zone"
              ></div>

              <draggable
                v-model="draggableSegments"
                tag="div"
                :item-key="getSegmentKey"
                :animation="200"
                handle=".drag-handle"
                ghost-class="ghost-segment"
                chosen-class="chosen-segment"
                drag-class="drag-segment"
                :options="{ forceFallback: true, fallbackOnBody: true }"
                :scroll="true"
                :scroll-sensitivity="80"
                :scroll-speed="18"
                :bubble-scroll="true"
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
                          'paragraph-needs-attention': segment.needsAttention,
                          'paragraph-invalid-cue': hasInvalidCuePattern(index)
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
                        :data-seg-index="index"
                        contenteditable="true"
                        v-safe-html="{ content: getSegmentContent(index), editing: activelyEditingSegment === index }"
                        @input="handleContentEditableInput(index, $event)"
                        @keydown="handleContentEditableKeydown(index, $event)"
                        @paste="handleContentEditablePaste(index, $event)"
                        @mousedown="handleContentEditableMousedown(index, $event)"
                        @click="handleRevisionAction($event, index)"
                        @focus="setEditingFlags(index); handleParagraphFocus(index)"
                        @blur="handleParagraphBlur(index, $event)"
                        class="speaker-textarea speaker-contenteditable"
                        :class="`speaker-${segment.speaker}`"
                        :style="getSpeakerTextStyle(segment.speaker)"
                        :data-placeholder="`Enter ${getSpeakerDisplayName(segment.speaker)}'s dialogue here...`"
                      ></div>

                      <!-- Revision Entry Input (appears when proposing a revision) -->
                      <div v-if="activeRevision && activeRevision.index === index" class="rev-entry-bar">
                        <span class="rev-entry-label">
                          <v-icon size="x-small" class="mr-1">mdi-pencil</v-icon>
                          Replacement text (optional):
                        </span>
                        <input
                          ref="revEntryInput"
                          v-model="activeRevision.replacementText"
                          class="rev-entry-input"
                          placeholder="Type replacement text, or Enter for cut-only"
                          @keydown.esc.stop.prevent="cancelRevision()"
                          @keydown.enter.stop.prevent="finalizeRevision()"
                          autofocus
                        />
                        <v-btn size="x-small" variant="tonal" color="success" @click.stop="finalizeRevision()" class="ml-1" title="Confirm revision (Enter)">
                          <v-icon size="small">mdi-check</v-icon>
                        </v-btn>
                        <v-btn size="x-small" variant="tonal" color="error" @click.stop="cancelRevision()" class="ml-1" title="Cancel (ESC)">
                          <v-icon size="small">mdi-close</v-icon>
                        </v-btn>
                      </div>

                      <!-- Revision Toolbar (Accept All / Reject All) -->
                      <div v-if="getRevisionCount(index) > 0 && !(activeRevision && activeRevision.index === index)" class="rev-toolbar">
                        <span class="rev-toolbar-count">{{ getRevisionCount(index) }} revision{{ getRevisionCount(index) > 1 ? 's' : '' }}</span>
                        <v-btn
                          size="x-small"
                          variant="tonal"
                          color="success"
                          @click.stop="acceptAllRevisions(index)"
                        >
                          <v-icon start size="small">mdi-check-all</v-icon>
                          Accept All
                        </v-btn>
                        <v-btn
                          size="x-small"
                          variant="tonal"
                          color="error"
                          @click.stop="rejectAllRevisions(index)"
                        >
                          <v-icon start size="small">mdi-close-circle-outline</v-icon>
                          Reject All
                        </v-btn>
                      </div>

                      <!--
                        Invalid Cue Pattern Warning + Convert button.
                        Inline overlay that appears whenever the live content
                        of a paragraph contains a legacy {SOT/foo} or
                        (SOT/foo) token. The button is the same component
                        that renders on the flag-note panel — see
                        @/modules/legacyCueConvert/README.md.
                      -->
                      <div v-if="hasInvalidCuePattern(index)" class="invalid-cue-overlay">
                        <span class="invalid-cue-warning">*** Invalid code will cause the system to break ***</span>
                        <LegacyCueConvertButton
                          v-if="legacyCueConvertEnabled"
                          :paragraph-segment="segment"
                          :segment-index="index"
                          :episode="currentEpisode"
                          :segment-id="item?.id ?? null"
                          @converted="onLegacyCueConverted"
                        />
                      </div>

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
                            <!--
                              Legacy Cue Convert button — only renders when
                              this paragraph was flagged by Auto Scrub for
                              containing a legacy {SOT/foo} or (SOT/foo)
                              token AND the module is enabled in Settings.
                              See @/modules/legacyCueConvert/README.md.
                            -->
                            <LegacyCueConvertButton
                              v-if="legacyCueConvertEnabled && segment.flagNote === LEGACY_CUE_FLAG_LABEL"
                              :paragraph-segment="segment"
                              :segment-index="index"
                              :episode="currentEpisode"
                              :segment-id="item?.id ?? null"
                              @converted="onLegacyCueConverted"
                            />
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
                    { 'cue-collapsed': collapseMode },
                    { 'multi-selected': multiSelectedSegments.has(index) }
                  ]"
                  :style="multiSelectedSegments.has(index) ? {
                    'background-color': selectionBackgroundColor,
                    'border-left': `6px solid ${selectionColor}`,
                    'box-shadow': `0 0 0 2px ${selectionShadowColor}`
                  } : (focusedCueIndex === index ? { backgroundColor: highlightBackgroundColor } : {})"
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
                    @edit-gfx="handleEditGfx"
                    @relocate="handleRelocateCue(index)"
                    @apply-all-fsq="handleApplyAllFsq"
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

                  <!-- Add Paragraph Button (bottom center of cue) -->
                  <v-btn
                    v-if="hoveredCueIndex === index"
                    icon
                    size="small"
                    class="cue-add-paragraph-btn"
                    @click.stop="createNewParagraphAfter(index)"
                    tabindex="-1"
                  >
                    <v-icon size="medium">mdi-plus</v-icon>
                  </v-btn>
                  </template>
                </div>
                    </div>
                  </div>
                </template>
              </draggable>

              <!-- Trailing drop zone (after last segment) -->
              <div
                v-if="dropZoneActive"
                class="cue-drop-zone trailing-drop-zone"
                :class="{ 'drop-zone-selected': selectedDropZone === (draggableSegments || []).length }"
                @click="selectDropZone((draggableSegments || []).length)"
                @mouseenter="hoveredDropZone = (draggableSegments || []).length"
                @mouseleave="hoveredDropZone = null"
              >
                <div class="drop-zone-line"></div>
                <div class="drop-zone-label">
                  <v-icon size="small">mdi-plus-circle</v-icon>
                  Insert {{ pendingCueType }} here
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
          <!-- Insert Cues Toolbar (shared collapsible, same as script mode) -->
          <div v-if="showCuesToolbar" class="editor-cues-toolbar cues-toolbar-sticky">
            <div class="cue-toolbar-row">
              <v-btn variant="flat" size="small" class="add-cue-trigger" :class="{ 'add-cue-active': cueMenuOpen }" color="grey-darken-3" @click="toggleCueMenu">
                <v-icon size="small" class="mr-1" :class="{ 'rotate-90': cueMenuOpen }">mdi-plus</v-icon>
                <span class="add-cue-label">ADD CUE</span><span class="add-cue-hotkey">ALT+C</span>
              </v-btn>
              <transition name="cue-expand">
                <div v-if="cueMenuOpen" class="cue-buttons-flex-container">
                  <v-btn v-for="cue in cueDefinitions" :key="cue.type" variant="flat" class="cue-btn-flex" :class="[cue.btnClass, { 'cue-btn-flash': flashingCueType === cue.type }]" :style="getCueButtonStyle(cue.type)" @click="insertCueFromMenu(cue.type)">
                    <div class="cue-btn-content-flex"><span class="cue-label">{{ cue.label }}</span><span class="hotkey-display">{{ cue.key.toUpperCase() }}</span></div>
                    <v-tooltip activator="parent" location="bottom">{{ cue.tooltip }} (Alt+{{ cue.key.toUpperCase() }})</v-tooltip>
                  </v-btn>
                </div>
              </transition>
            </div>
          </div>

          <!-- Text formatting styles flyout -->
          <div class="styles-flyout-container text-formatting-sticky">
            <v-btn
              size="x-small"
              variant="text"
              class="styles-toggle-btn"
              @click="showStylesFlyout = !showStylesFlyout"
            >
              <v-icon size="small" :class="{ 'rotate-90': showStylesFlyout }">mdi-chevron-right</v-icon>
              Styles
            </v-btn>
            <transition name="flyout">
              <div v-if="showStylesFlyout" class="styles-flyout-items">
                <span class="formatting-hotkey"><strong>CTRL+B</strong> Bold</span>
                <span class="formatting-hotkey"><strong>CTRL+I</strong> Italic</span>
                <span class="formatting-hotkey"><strong>CTRL+U</strong> Underline</span>
                <span class="formatting-hotkey"><strong>CTRL+ALT+H</strong> Highlight</span>
                <span class="formatting-hotkey"><strong>ALT+/</strong> Revise</span>
                <span class="formatting-hotkey"><strong>ALT+.</strong> Add</span>
                <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regen AssetID</span>
              </div>
            </transition>
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
        <div v-else-if="editorMode === 'code'" class="code-mode-container d-flex flex-column">
          <!-- Insert Cues Toolbar (shared collapsible, same as script mode) -->
          <div v-if="showCuesToolbar" class="editor-cues-toolbar cues-toolbar-sticky">
            <div class="cue-toolbar-row">
              <v-btn variant="flat" size="small" class="add-cue-trigger" :class="{ 'add-cue-active': cueMenuOpen }" color="grey-darken-3" @click="toggleCueMenu">
                <v-icon size="small" class="mr-1" :class="{ 'rotate-90': cueMenuOpen }">mdi-plus</v-icon>
                <span class="add-cue-label">ADD CUE</span><span class="add-cue-hotkey">ALT+C</span>
              </v-btn>
              <transition name="cue-expand">
                <div v-if="cueMenuOpen" class="cue-buttons-flex-container">
                  <v-btn v-for="cue in cueDefinitions" :key="cue.type" variant="flat" class="cue-btn-flex" :class="[cue.btnClass, { 'cue-btn-flash': flashingCueType === cue.type }]" :style="getCueButtonStyle(cue.type)" @click="insertCueFromMenu(cue.type)">
                    <div class="cue-btn-content-flex"><span class="cue-label">{{ cue.label }}</span><span class="hotkey-display">{{ cue.key.toUpperCase() }}</span></div>
                    <v-tooltip activator="parent" location="bottom">{{ cue.tooltip }} (Alt+{{ cue.key.toUpperCase() }})</v-tooltip>
                  </v-btn>
                </div>
              </transition>
            </div>
          </div>

          <!-- Text formatting styles flyout -->
          <div class="styles-flyout-container text-formatting-sticky">
            <v-btn
              size="x-small"
              variant="text"
              class="styles-toggle-btn"
              @click="showStylesFlyout = !showStylesFlyout"
            >
              <v-icon size="small" :class="{ 'rotate-90': showStylesFlyout }">mdi-chevron-right</v-icon>
              Styles
            </v-btn>
            <transition name="flyout">
              <div v-if="showStylesFlyout" class="styles-flyout-items">
                <span class="formatting-hotkey"><strong>CTRL+B</strong> Bold</span>
                <span class="formatting-hotkey"><strong>CTRL+I</strong> Italic</span>
                <span class="formatting-hotkey"><strong>CTRL+U</strong> Underline</span>
                <span class="formatting-hotkey"><strong>CTRL+ALT+H</strong> Highlight</span>
                <span class="formatting-hotkey"><strong>ALT+/</strong> Revise</span>
                <span class="formatting-hotkey"><strong>ALT+.</strong> Add</span>
                <span class="formatting-hotkey"><strong>ALT+SHIFT+A</strong> Regen AssetID</span>
              </div>
            </transition>
          </div>

          <v-textarea
            v-model="rawScriptContent"
            :placeholder="hasNoItem ? noItemPlaceholder : 'Edit the script content in markdown format...'"
            :disabled="hasNoItem"
            variant="plain"
            hide-details
            auto-grow
            rows="20"
            class="code-textarea"
            :class="{ 'ghost-text': hasNoItem }"
            style="font-family: 'Roboto Mono', monospace;"
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

  <!-- Delete Cue Confirmation Dialog -->
  <v-dialog v-model="showDeleteCueConfirm" max-width="400">
    <v-card>
      <v-card-title class="text-h6 bg-red-darken-2 text-white pa-3">
        <v-icon class="me-2">mdi-delete-alert</v-icon>
        Delete Cue
      </v-card-title>
      <v-card-text class="pa-4">
        Delete <strong>{{ deletingCueData?.type }}</strong> cue
        <span v-if="deletingCueData?.slug"> &ldquo;{{ deletingCueData.slug }}&rdquo;</span>?
        <br><span class="text-caption text-grey">This cannot be undone.</span>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="cancelDeleteCue">Cancel</v-btn>
        <v-btn color="red" variant="flat" @click="confirmDeleteCue">Delete</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- TTS Read-Through Options Modal -->
  <v-dialog v-model="showTtsOptionsDialog" max-width="420" @keydown.enter.prevent="confirmTtsOptionsAndRead" @keydown.esc="cancelTtsOptionsDialog">
    <v-card>
      <v-card-title class="text-h6 bg-blue-darken-2 text-white pa-3">
        <v-icon class="me-2">mdi-text-to-speech</v-icon>
        TTS Read-Through Options
      </v-card-title>
      <v-card-text class="pa-4">
        <div class="text-caption text-grey mb-3">
          Press Enter to start with the values below, or pick a different voice / speed.
        </div>
        <v-select
          v-model="ttsOptionsForm.voice"
          :items="ttsAvailableVoices.length ? ttsAvailableVoices : ['josh-1']"
          :loading="ttsVoicesLoading"
          label="Voice"
          density="compact"
          variant="outlined"
          autofocus
          class="mb-2"
        />
        <v-text-field
          v-model.number="ttsOptionsForm.speed"
          type="number"
          step="0.1"
          min="0.5"
          max="2.0"
          label="Speed (1.0 = normal)"
          density="compact"
          variant="outlined"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="cancelTtsOptionsDialog">Cancel</v-btn>
        <v-btn color="blue" variant="flat" @click="confirmTtsOptionsAndRead">Start (Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Stub View Modal -->
  <v-dialog v-model="showStubModal" max-width="400">
    <v-card>
      <v-card-title class="text-h6">{{ stubViewName }}</v-card-title>
      <v-card-text>This function is not yet available.</v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="showStubModal = false">OK</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
/* eslint-disable no-unused-vars */
import { ref, computed, watch, onMounted, onBeforeUnmount, onUnmounted, nextTick, getCurrentInstance } from 'vue'
import { getColorValue, resolveVuetifyColor, loadColorsFromDatabase } from '../../utils/themeColorMap.js'
import draggable from 'vuedraggable'
import DeleteImgCueModal from './modals/DeleteImgCueModal.vue'
import ImageCueCard from './cards/ImageCueCard.vue'
import PlaceholderCueCard from './cards/PlaceholderCueCard.vue'
import SpeakerSelectorModal from './modals/SpeakerSelectorModal.vue'
import CueParser from '../../utils/cueParser.js'
import { useTts } from '../../composables/useTts.js'
import { useAsyncAnalysis } from '../../composables/useAsyncAnalysis.js'
import { useRequireEpisode } from '../../composables/useRequireEpisode.js'
import { useHotkeys } from '../../composables/useHotkeys.js'
import { useContentSanitizer } from '../../composables/useContentSanitizer.js'
import { useCollapseMode } from '../../composables/useCollapseMode.js'
import { useEditorPaste } from '../../composables/useEditorPaste.js'
import { useScriptCore } from '../../composables/useScriptCore.js'
import { useMessages } from '../../composables/useMessages.js'
import {
  LEGACY_CUE_REGEX,
  LEGACY_CUE_FLAG_LABEL,
  ConvertButton as LegacyCueConvertButton,
  useLegacyCueConvertEnabled,
} from '@/modules/legacyCueConvert'

// ============================================================================
// Custom directive: v-safe-html
// ============================================================================
const vSafeHtml = {
  mounted(el, binding) {
    const { content } = binding.value
    if (content !== undefined && content !== null) {
      el.innerHTML = content
    }
  },
  updated(el, binding) {
    const { content, editing } = binding.value
    if (editing) return
    if (el._pasteCooldown) return
    if (content !== undefined && content !== null && el.innerHTML !== content) {
      el.innerHTML = content
    }
  }
}

const instance = getCurrentInstance()

// ============================================================================
// Props
// ============================================================================
const props = defineProps({
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
currentEpisodeTitle: {
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

})

const emit = defineEmits([
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
    'show-script-compare-modal',
    'autoscrub-all-items',
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
    'showStingModal',
    'relocate-cue',
  ])

// ============================================================================
// Mode switch state preservation
// ============================================================================
// Cross-mode cursor/scroll preservation. We map caret locations between
// Script Mode (contenteditable paragraphs) and Code Mode (raw textarea) via
// an absolute character offset into `rawScriptContent`. When switching, we
// capture that offset from the outgoing mode and place the caret at the same
// offset in the incoming mode, then center the view on it — so it feels like
// switching views, not teleporting to the top of the document.
const modeSwitchState = {
  rawOffset: 0,         // absolute char offset in rawScriptContent
  scrollY: 0            // fallback scroll position if mapping fails
}

function getCaretOffsetInNode(root) {
  // Return the caret offset (in characters) within `root`, or null if no
  // selection lives inside it.
  const sel = window.getSelection && window.getSelection()
  if (!sel || sel.rangeCount === 0) return null
  const range = sel.getRangeAt(0)
  if (!root.contains(range.startContainer)) return null
  const pre = range.cloneRange()
  pre.selectNodeContents(root)
  pre.setEnd(range.startContainer, range.startOffset)
  return pre.toString().length
}

function setCaretAtOffsetInNode(root, offset) {
  // Place the caret `offset` characters into `root`'s text content.
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let remaining = Math.max(0, offset)
  let node = walker.nextNode()
  while (node) {
    const len = node.nodeValue.length
    if (remaining <= len) {
      const sel = window.getSelection()
      const range = document.createRange()
      range.setStart(node, remaining)
      range.collapse(true)
      sel.removeAllRanges()
      sel.addRange(range)
      return true
    }
    remaining -= len
    node = walker.nextNode()
  }
  // Fell off the end — put caret at the end of the last text node.
  const lastText = (() => {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
    let last = null, n = w.nextNode()
    while (n) { last = n; n = w.nextNode() }
    return last
  })()
  if (lastText) {
    const sel = window.getSelection()
    const range = document.createRange()
    range.setStart(lastText, lastText.nodeValue.length)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
    return true
  }
  return false
}

function captureModeState(mode) {
  modeSwitchState.scrollY = window.scrollY
  const raw = rawScriptContent.value || ''

  if (mode === 'code') {
    const ta = document.querySelector('.code-textarea textarea')
    if (ta) modeSwitchState.rawOffset = ta.selectionStart || 0
    return
  }

  if (mode === 'script') {
    // Find the focused paragraph (if any) and compute an absolute rawOffset
    // by searching for the paragraph's text in rawScriptContent + local caret.
    const sel = window.getSelection && window.getSelection()
    let paragraphEl = null
    if (sel && sel.rangeCount > 0) {
      let node = sel.getRangeAt(0).startContainer
      if (node && node.nodeType === Node.TEXT_NODE) node = node.parentElement
      paragraphEl = node && node.closest && node.closest('.speaker-paragraph')
    }
    if (!paragraphEl) {
      // No live selection — fall back to the currently "selected" paragraph.
      const idx = selectedSegmentIndex.value
      if (idx != null) {
        const all = document.querySelectorAll('.speaker-paragraph')
        paragraphEl = all[idx] || null
      }
    }
    if (!paragraphEl) return

    const localOffset = getCaretOffsetInNode(paragraphEl) ?? 0
    const paraText = (paragraphEl.innerText || paragraphEl.textContent || '').trim()
    if (!paraText) return
    // Use a distinctive slice for the search to avoid collisions on short lines.
    const needle = paraText.slice(0, Math.min(60, paraText.length))
    const found = raw.indexOf(needle)
    if (found >= 0) {
      modeSwitchState.rawOffset = found + Math.min(localOffset, paraText.length)
    }
  }
}

function scrollCenterY(y) {
  const target = Math.max(0, y - window.innerHeight / 2)
  window.scrollTo({ top: target, behavior: 'auto' })
}

function restoreModeState(mode) {
  const raw = rawScriptContent.value || ''
  const offset = Math.min(Math.max(0, modeSwitchState.rawOffset || 0), raw.length)

  if (mode === 'code') {
    const ta = document.querySelector('.code-textarea textarea')
    if (!ta) {
      window.scrollTo({ top: modeSwitchState.scrollY || 0 })
      return
    }
    try {
      ta.focus({ preventScroll: true })
      ta.setSelectionRange(offset, offset)
    } catch (e) { /* ignore */ }
    // Compute pixel y of the caret line and center the viewport on it.
    const cs = window.getComputedStyle(ta)
    const lineHeight = parseFloat(cs.lineHeight) || 20
    const paddingTop = parseFloat(cs.paddingTop) || 0
    const lineIndex = (raw.slice(0, offset).match(/\n/g) || []).length
    const rect = ta.getBoundingClientRect()
    const caretDocY = rect.top + window.scrollY + paddingTop + lineIndex * lineHeight
    scrollCenterY(caretDocY)
    return
  }

  if (mode === 'script') {
    // Find the .speaker-paragraph element whose text spans the saved offset
    // inside rawScriptContent, then place the caret + center scroll on it.
    const paragraphs = Array.from(document.querySelectorAll('.speaker-paragraph'))
    let best = null, bestLocal = 0
    for (const el of paragraphs) {
      const text = (el.innerText || el.textContent || '').trim()
      if (!text) continue
      const needle = text.slice(0, Math.min(60, text.length))
      const start = raw.indexOf(needle)
      if (start < 0) continue
      const end = start + text.length
      if (offset >= start && offset <= end) {
        best = el
        bestLocal = offset - start
        break
      }
      // Track nearest-above as fallback.
      if (start <= offset) { best = el; bestLocal = Math.min(offset - start, text.length) }
    }
    if (best) {
      try { setCaretAtOffsetInNode(best, bestLocal) } catch (e) { /* ignore */ }
      const rect = best.getBoundingClientRect()
      scrollCenterY(rect.top + window.scrollY + rect.height / 2)
    } else {
      window.scrollTo({ top: modeSwitchState.scrollY || 0 })
    }
  }
}

watch(() => props.editorMode, (newMode, oldMode) => {
  if (newMode === oldMode) return
  // Capture the mode we're leaving BEFORE the DOM swaps.
  captureModeState(oldMode)
  // Wait for the new mode's DOM to mount, then restore.
  nextTick(() => {
    // Double-tick: v-textarea auto-grow settles height on the next frame;
    // restoring scroll before that can land us short of the target.
    requestAnimationFrame(() => restoreModeState(newMode))
  })
})

// ============================================================================
// Composables
// ============================================================================
const { requireEpisode } = useRequireEpisode()
const sanitizer = useContentSanitizer()
const _msgApi = useMessages()

// Other online users currently editing the same segment as me.
// Powered by the public presence broadcast in useSessionResume.
const otherUsersOnThisSegment = computed(() => {
  const item = props.item
  if (!item) return []
  const itemId = item.asset_id || item.id
  if (!itemId) return []
  let myId = null
  try { myId = JSON.parse(localStorage.getItem('user-data') || '{}')?.id || null } catch { /* noop */ }
  return (_msgApi.users.value || []).filter(u =>
    u.id !== myId
    && u.online
    && u.current_location?.segment_id != null
    && String(u.current_location.segment_id) === String(itemId)
  )
})

function presenceInitials(u) {
  const name = u.display_name || u.username || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return (parts[0]?.slice(0, 2) || '??').toUpperCase()
}
const { stripRevisionMarkup, stripYamlFrontmatter, extractYamlFrontmatter } = sanitizer
const {
  hexToHsl, getCollapsedFirstWords, getCollapsedLastWords,
  getCollapsedCueStyle, getCollapsedOutcue, makeGetCollapsedLineRange
} = useCollapseMode()
const { parseGoogleDocsPaste, cleanGoogleDocsNode, parseGenericPaste } = useEditorPaste()

const { enabled: legacyCueConvertEnabled } = useLegacyCueConvertEnabled()

const core = useScriptCore(props, emit, sanitizer)
const {
  segmentEditBuffer, updateDebounceTimers,
  isActivelyEditing, isActivelyTyping, activelyEditingSegment,
  isRestoringCursor, savedCursorState, blockReactiveUpdates,
  cachedScriptSegments, lastParsedContent, segmentReparseKey,
  hasLocalUnsavedChanges, rawScriptContent, scriptSegments, draggableSegments,
  reconstructRawContent, flushPendingChanges, clearEditBuffer,
  shrinkGuardEnabled, setShrinkGuardEnabled, allowNextShrink,
  getEditBuffer, setEditBufferEntry, deleteEditBufferEntry,
  getDebounceTimers, clearDebounceTimers, syncContentEditableToSegment,
  detectMultipleFrontmatterBlocks, validateScriptContent,
  repairScriptContent, validateAndRepairBeforeSave,
  setPendingCueContextGetter, setDraggableSetHandler,
} = core
const _scriptCoreUpdateTextSegment = core.updateTextSegment
const _scriptCoreEmitScriptContent = core.emitScriptContent

// ============================================================================
// Template Refs
// ============================================================================
const slugFieldRef = ref(null)
const typingInputRef = ref(null)
const revEntryInput = ref(null)

// ============================================================================
// Non-reactive instance variables
// ============================================================================
let _lineCountObserver = null

// ============================================================================
// Reactive State
// ============================================================================
const showStylesFlyout = ref(false)
const showImgModal = ref(false)
const showDeleteImgModal = ref(false)
const showDeleteCueConfirm = ref(false)
const editingCueData = ref(null)
const deletingCueData = ref(null)
const deletingCueIndex = ref(null)
const selectedCueIndex = ref(null)
const selectedSegmentIndex = ref(null)
const pendingCueInsertionIndex = ref(null) // Snapshotted at cue-button-press time, survives modal interaction
const multiSelectedSegments = ref(new Set())
const showSpeakerSelector = ref(false)
const cueCardAlignment = ref('left') // Default alignment, loaded from settings
const currentSegmentSpeaker = ref('josh')
const editingSpeakerSegmentIndex = ref(null)
const showCuePlacement = ref(false)
const showSwapErrorDialog = ref(false)
const swapErrorMessage = ref('')
const blinkingParagraphs = ref(new Set()) // Track paragraphs that are blinking after swap
const pendingCueType = ref(null)
const pendingPlacement = ref(null)
const temporaryEpisode = ref(null) // For episode requirement callback
const pendingCueData = ref(null) // Store IMG cue data for post-modal placement
const useVisualScriptMode = ref(true) // Toggle for visual cue cards vs traditional text - RE-ENABLED, fixing visibility issue
const showStubModal = ref(false)
const stubViewName = ref('')
const hoveredParagraphIndex = ref(null) // Track which paragraph is being hovered
const hoveredCueIndex = ref(null) // Track which cue is being hovered (for flag button)
const activeFlagNoteIndex = ref(null) // Track which segment's flag note panel is open
const activeFlagNoteType = ref(null) // 'paragraph' or 'cue' - type of segment with open note
const flagNoteContent = ref('') // Content of the flag note being edited
const minimizedFlagNotes = ref({}) // Track which flag notes are minimized (by "type-index" key as object for Vue reactivity)
const paragraphRefs = ref({}) // Store refs to paragraph elements for flag note positioning
const flagNotePosUpdateTrigger = ref(0) // Trigger to force position recalculation on scroll
const focusedParagraphIndex = ref(null) // Track which paragraph has focus
const lastKnownParagraphIndex = ref(null) // Persist last focused paragraph for cue insertion (survives blur)
const focusedCueIndex = ref(null) // Track which cue row has focus (for tab navigation)
const savedParagraphIndex = ref(null) // Track paragraph that just saved (for green flash)
const errorParagraphIndex = ref(null) // Track paragraph with save error (for red flash)
const paragraphEditStates = ref({}) // Track if paragraph has been edited before (for re-edit detection)
// hasLocalUnsavedChanges — moved to useScriptCore composable
const typingBuffer = ref('') // Buffer for auto-expanding text input
const autoscrubTimer = ref(null) // Timer for periodic autoscrub
const autoscrubDebounceTimer = ref(null) // Debounce timer for content changes
const slugNeedsAttention = ref(false) // Track if slug field needs user attention (yellow highlight)
const slugFieldFocused = ref(false) // Track if slug field is currently focused
const titleFieldFocused = ref(false) // Track if title field is currently focused
const segmentUpdateTimer = ref(null) // Timer for debouncing segment updates
const lastAutoscrubTime = ref(null) // Timestamp of last autoscrub run
const altKeyPressed = ref(false) // Manual ALT key tracking for better browser compatibility
const cueMenuOpen = ref(false) // Cue selector mode — single-key dispatch when open
const flashingCueType = ref(null) // Which cue button to flash on keypress
const cueDefinitions = ref([
        { type: 'IMG', key: 'i', label: 'IMG', tooltip: 'Image/Photo', btnClass: 'img-btn' },
        { type: 'GFX', key: 'g', label: 'GFX', tooltip: 'Graphics & Lower Thirds', btnClass: 'gfx-btn' },
        { type: 'FSQ', key: 'q', label: 'FSQ', tooltip: 'Full Screen Quote', btnClass: 'fsq-btn' },
        { type: 'SOT', key: 's', label: 'SOT', tooltip: 'Sound on Tape', btnClass: 'sot-btn' },
        { type: 'VO', key: 'v', label: 'VO', tooltip: 'Voice Over', btnClass: 'vo-btn' },
        { type: 'NAT', key: 'n', label: 'NAT', tooltip: 'Natural Sound', btnClass: 'nat-btn' },
        { type: 'PKG', key: 'p', label: 'PKG', tooltip: 'Package', btnClass: 'pkg-btn' },
        { type: 'NOTE', key: 'd', label: 'NOTE', tooltip: 'Note', btnClass: 'dir-btn' },
        { type: 'BUMP', key: 'b', label: 'BUMP', tooltip: 'Bumper', btnClass: 'bump-btn' },
        { type: 'STING', key: 't', label: 'STING', tooltip: 'Stinger', btnClass: 'sting-btn' },
        { type: 'RIF', key: 'r', label: 'RIF', tooltip: 'Riff', btnClass: 'rif-btn' },
      ])
// isActivelyTyping, segmentEditBuffer, updateDebounceTimers, activelyEditingSegment,
// isActivelyEditing, isRestoringCursor, savedCursorState — moved to useScriptCore composable
const lastEnterState = ref({}) // Track Enter key state per segment for double Enter detection
// Universal cue insertion workflow
const pendingInsertionPoint = ref(null) // Store cursor position for insertion (script mode)
const pendingCursorPosition = ref(null) // Store cursor position for insertion (code mode)
const flashMessage = ref({
        show: false,
        text: '',
        color: '',
        timeout: 500
      })
const thickCursor = ref({
        show: false,
        style: {}
      })
const cursorPositionHighlight = ref(null) // Reference to cursor position highlight element
const cursorPositionTimeout = ref(null) // Timeout reference for cursor position highlight
const highlightedElement = ref(null) // Currently highlighted element for insertion preview
// TTS reading state
const isReadingScript = ref(false) // Whether script is currently being read
const currentReadingIndex = ref(0) // Current paragraph index being read
const audioElement = ref(null) // Audio element for playback
const ttsInstance = ref(null) // TTS composable instance
// Active reading options (set when user confirms the pre-read modal)
const activeReadingOptions = ref({ voice: 'josh-1', speed: 1.0 })
// Pre-read TTS options modal
const showTtsOptionsDialog = ref(false)
const ttsOptionsForm = ref({ voice: 'josh-1', speed: 1.0 })
const ttsAvailableVoices = ref([])
const ttsVoicesLoading = ref(false)
const segmentLineCounts = ref({}) // Cache of line counts per segment for reactivity
const isDragging = ref(false) // Track if segment is being dragged
const pendingCrossContent = ref(null) // Markdown content waiting to be placed in target segment
const pendingSegmentOrder = ref(null) // Store reordered segments during drag (processed after drag ends)
// cachedScriptSegments, lastParsedContent — moved to useScriptCore composable
// Revision system state
const activeRevision = ref(null) // { index, killText, replacementText, mode } - tracks active revision entry
const revisionEntryMode = ref(false) // Whether user is typing replacement text in a rev block
const pendingFocusSegmentIndex = ref(null) // Index of segment to focus after next render
// Drop zone state for cue insertion
const dropZoneActive = ref(false) // Whether drop zones are visible for cue insertion
const selectedDropZone = ref(null) // Which drop zone is currently selected (index)
const hoveredDropZone = ref(null) // Which drop zone is currently hovered (index)
// Generic flag to block @update:model-value handlers during programmatic operations
// Set this to true when performing operations that shouldn't trigger reactive updates
// Use cases: creating paragraphs, merging paragraphs, bulk operations, etc.
// blockReactiveUpdates — moved to useScriptCore composable
// Scroll position preservation for paragraph splitting
const savedScrollPosition = ref(undefined)
const savedContainerScroll = ref(undefined)
const scrollContainerRef = ref(null)
const scriptContainerRef = ref(null)
const colorLoadTrigger = ref(0) // Reactive trigger to force re-computation of color-dependent properties
const collapseMode = ref(false) // Collapse mode for easier drag-and-drop reordering
// segmentReparseKey — moved to useScriptCore composable
const isPasting = ref(false) // Show spinner overlay during Google Docs paste processing
const lastMultiSelectAnchor = ref(null) // Anchor index for shift+click range selection


// ============================================================================
// Computed Properties
// ============================================================================
// rawScriptContent — moved to useScriptCore composable

// Episode number for iPad mode
const currentEpisodeNumber = computed(function currentEpisodeNumber() {
  return props.currentEpisode
})

// scriptSegments, draggableSegments — moved to useScriptCore composable

// Calculate total duration of rundown item (cue durations + paragraph text durations)
// Calculate duration directly from rawScriptContent so it updates in real-time
// (not from scriptSegments which is cached during active editing)
const calculatedItemDuration = computed(function calculatedItemDuration() {
  const content = rawScriptContent.value;
  if (!content || !content.trim()) {
    return '00:00:00:00';
  }

  let totalSeconds = 0;
  const speakerWpm = props.item?.speaker_wpm || 150;

  // Strip YAML frontmatter
  const stripped = content.replace(/^---[\s\S]*?---\s*/, '');

  // Split into lines and process
  const lines = stripped.split('\n');
  let textBuffer = '';

  for (const line of lines) {
    // Check if line is a cue card (e.g. [GFX: ...] or ```cue blocks)
    const cueMatch = line.match(/^\s*\[(\w+)(?:\s*[:|].*?)?\]\s*$/);
    const cueDurationMatch = line.match(/duration[:\s]*(\d{2}:\d{2}:\d{2}(?::\d{2})?)/i);

    if (cueDurationMatch) {
      const dur = cueDurationMatch[1].includes(':') ? cueDurationMatch[1] : cueDurationMatch[1] + ':00';
      const parts = dur.split(':');
      if (parts.length >= 3) {
        totalSeconds += (parseInt(parts[0]) || 0) * 3600 + (parseInt(parts[1]) || 0) * 60 + (parseInt(parts[2]) || 0);
      }
    } else if (!cueMatch && !line.match(/^```/) && !line.match(/^\s*\w+\s*:/)) {
      // Regular text line — accumulate for word count
      textBuffer += ' ' + line;
    }
  }

  // Calculate text duration from word count
  const words = textBuffer.trim().split(/\s+/).filter(w => w.length > 0);
  if (words.length > 0) {
    totalSeconds += Math.ceil((words.length / speakerWpm) * 60);
  }

  return secondsToDuration(totalSeconds);
})

// Enhanced options for select fields
const statusOptions = computed(function statusOptions() {
  return [
    { title: 'Scheduled', value: 'scheduled' },
    { title: 'Draft', value: 'draft' },
    { title: 'In Production', value: 'production' },
    { title: 'Running', value: 'running' },
    { title: 'Completed', value: 'completed' }
  ]
})

const priorityOptions = computed(function priorityOptions() {
  return [
    { title: 'Low', value: 'low' },
    { title: 'Normal', value: 'normal' },
    { title: 'High', value: 'high' },
    { title: 'Urgent', value: 'urgent' }
  ]
})

// Detect custom fields that aren't part of the standard schema
const customFields = computed(function customFields() {
  if (!props.currentItemMetadata) return {}
  
  const standardFields = [
    'AssetID', 'title', 'type', 'slug', 'subtitle', 'description', 
    'duration', 'status', 'order', 'airdate', 'priority', 'guests', 
    'resources', 'tags', 'server_message', 'created_at'
  ]
  
  const custom = {}
  Object.keys(props.currentItemMetadata).forEach(key => {
    if (!standardFields.includes(key) && props.currentItemMetadata[key] !== null && props.currentItemMetadata[key] !== '') {
      custom[key] = props.currentItemMetadata[key]
    }
  })
  
  return custom
})

// Check if there are any custom fields to display
const hasCustomFields = computed(function hasCustomFields() {
  return Object.keys(customFields.value).length > 0
})

// Count fields with meaningful (non-null, non-empty) data
const meaningfulFieldCount = computed(function meaningfulFieldCount() {
  if (!props.currentItemMetadata) return 0
  return Object.keys(props.currentItemMetadata).filter(key => {
    const value = props.currentItemMetadata[key]
    return value !== null && value !== undefined && value !== ''
  }).length
})

// Show cues toolbar for Script, Scratch, and Code modes (not Metadata)
const showCuesToolbar = computed(function showCuesToolbar() {
  return ['script', 'scratch', 'code'].includes(props.editorMode)
})

// Detect when no rundown item is selected
const hasNoItem = computed(function hasNoItem() {
  return !props.item || props.item === null
})

// Ghost text for when no item is selected
const noItemPlaceholder = computed(function noItemPlaceholder() {
  return 'To begin editing your show content, add an item to your rundown.'
})

// Get the selection color from theme configuration
const selectionColor = computed(function selectionColor() {
  const colorName = getColorValue('selection');
  return resolveVuetifyColor(colorName);
})

// Multi-selection count — computed to guarantee Vue reactivity for v-if
const multiSelectionCount = computed(function multiSelectionCount() {
  return multiSelectedSegments.value.size;
})

// Get selection color with opacity for background
const selectionBackgroundColor = computed(function selectionBackgroundColor() {
  const hexColor = selectionColor.value;
  // Convert hex to RGB and add 25% opacity
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.25)`;
})

// Get selection color with opacity for shadow
const selectionShadowColor = computed(function selectionShadowColor() {
  const hexColor = selectionColor.value;
  // Convert hex to RGB and add 20% opacity
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.2)`;
})

// Get highlight color with opacity for background (uses existing highlightColor)
const highlightBackgroundColor = computed(function highlightBackgroundColor() {
  const hexColor = highlightColor.value;
  // Convert hex to RGB — 20% opacity for a light, see-through highlight
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.2)`;
})

// Check if TTS is properly configured
const isTtsConfigured = computed(function isTtsConfigured() {
  return ttsInstance.value?.isTtsAvailable() || false;
})

// Get text-only paragraphs for reading
const readableParagraphs = computed(function readableParagraphs() {
  if (!scriptSegments.value || scriptSegments.value.length === 0) return [];
  return scriptSegments.value
    .filter(segment => segment.type === 'text' && segment.content && segment.content.trim() !== '')
    .map(segment => ({
      index: segment.segmentIndex,
      content: segment.content,
      speaker: segment.speaker
    }));
})

// Paper color — warm background for script paragraphs
const paperBackgroundColor = computed(function paperBackgroundColor() {
  const colorName = getColorValue('paper') || 'amber-lighten-4';
  const hexColor = resolveVuetifyColor(colorName) || '#FFECB3';
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.08)`;
})

// Get highlight color from database for slug field attention
const highlightColor = computed(function highlightColor() {
  const colorName = getColorValue('highlight') || 'yellow-lighten-3';
  const resolved = resolveVuetifyColor(colorName);
  // Convert to rgba for animation
  return resolved || '#FFF9C4';
})

// Get needs-attention color from settings for flagged paragraphs
const needsAttentionColor = computed(function needsAttentionColor() {
  // Reference colorLoadTrigger to ensure re-computation when colors are loaded
  // eslint-disable-next-line no-unused-vars
  const _trigger = colorLoadTrigger.value;
  const colorName = getColorValue('needs-attention') || 'orange-lighten-3';
  const resolved = resolveVuetifyColor(colorName);
  console.log('🚩 needsAttentionColor computed:', { colorName, resolved });
  return resolved || '#FFCC80';
})

// Get needs-attention background color with 30% opacity
const needsAttentionBackgroundColor = computed(function needsAttentionBackgroundColor() {
  const hexColor = needsAttentionColor.value;
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.3)`;
})

// Get needs-attention border color (solid)
const needsAttentionBorderColor = computed(function needsAttentionBorderColor() {
  return needsAttentionColor.value;
})

// CSS variables for dynamic theming
const editorPanelCssVars = computed(function editorPanelCssVars() {
  // Calculate additional opacity variations for the needs-attention color
  const hexColor = needsAttentionColor.value;
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);

  return {
    '--needs-attention-bg': needsAttentionBackgroundColor.value,
    '--needs-attention-border': needsAttentionBorderColor.value,
    '--needs-attention-color': needsAttentionColor.value,
    '--needs-attention-btn-bg': `rgba(${r}, ${g}, ${b}, 0.15)`,
    '--needs-attention-btn-hover': `rgba(${r}, ${g}, ${b}, 0.4)`,
    '--needs-attention-btn-active': `rgba(${r}, ${g}, ${b}, 0.5)`
  };
})

// Validate slug: must be lowercase and 4 words or less
const isSlugValid = computed(function isSlugValid() {
  if (!props.item?.slug || props.item.slug.trim().length === 0) {
    return false;
  }

  const slug = props.item.slug.trim();

  // Check if slug is all lowercase (allowing hyphens, underscores, numbers)
  const isLowercase = slug === slug.toLowerCase();

  // Count words (split by spaces, hyphens, or underscores)
  const words = slug.split(/[\s\-_]+/).filter(w => w.length > 0);
  const wordCount = words.length;

  return isLowercase && wordCount <= 4;
})



// ============================================================================
// Methods
// ============================================================================
// stripRevisionMarkup — extracted to useContentSanitizer composable (available via setup())

/**
 * Open iPad Mode - launches iPad scroll view in new window
 */
function openIpadMode() {
  if (!currentEpisodeNumber.value) {
    console.warn('No episode number available for iPad mode')
    return
  }

  // Open iPad scroll view in new window/tab
  const url = `/ipad-scroll/${currentEpisodeNumber.value}`
  window.open(url, '_blank')
}

function openCallerView() {
  stubViewName.value = 'Caller View'
  showStubModal.value = true
}

function openDirectorView() {
  stubViewName.value = 'Director View'
  showStubModal.value = true
}

/**
 * Store reference to paragraph element for flag note positioning.
 */
function setParagraphRef(index, el) {
  if (el) {
    paragraphRefs.value[index] = el;
  } else {
    delete paragraphRefs.value[index];
  }
}

/**
 * Get style object for flag note panel positioning.
 * Uses the paragraph's bounding rect to position the panel next to it.
 */
// eslint-disable-next-line no-unused-vars
function getFlagNotePanelStyle(index, type) {
  // Force reactivity on scroll
  // eslint-disable-next-line no-unused-vars
  const _trigger = flagNotePosUpdateTrigger.value;

  const el = paragraphRefs.value[index];
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
}

/**
 * Handle scroll event to update flag note positions.
 */
function handleScrollForFlagNotes() {
  flagNotePosUpdateTrigger.value++;
}

/**
 * Format relative time from ISO date string for locked segment display.
 */
function formatRelativeTime(isoString) {
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
}

/**
 * Check if a flag note is minimized.
 * @param {string} type - 'paragraph' or 'cue'
 * @param {number} index - The segment index
 * @returns {boolean} - Whether the note is minimized
 */
function isFlagNoteMinimized(type, index) {
  const key = `${type}-${index}`;
  const isMinimized = !!minimizedFlagNotes.value[key];
  console.log('🚩 isFlagNoteMinimized:', { type, index, key, isMinimized, minimizedFlagNotes: { ...minimizedFlagNotes.value } });
  return isMinimized;
}

/**
 * Toggle the minimized state of a flag note.
 * @param {string} type - 'paragraph' or 'cue'
 * @param {number} index - The segment index
 */
function toggleFlagNoteMinimized(type, index) {
  const key = `${type}-${index}`;
  if (minimizedFlagNotes.value[key]) {
    delete minimizedFlagNotes.value[key];
  } else {
    minimizedFlagNotes.value[key] = true;
  }
}

/**
 * Toggle the needs-attention flag on a paragraph segment.
 * This persists when the script is saved.
 */
function toggleNeedsAttention(segmentIndex) {
  console.log('🚩 Toggle needs-attention for segment:', segmentIndex);

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  // Get current segments
  const segments = [...scriptSegments.value];

  if (!segments[segmentIndex] || segments[segmentIndex].type !== 'text') {
    console.warn('Cannot toggle needs-attention on non-text segment');
    return;
  }

  // Toggle the flag
  segments[segmentIndex].needsAttention = !segments[segmentIndex].needsAttention;

  console.log('🚩 New needsAttention value:', segments[segmentIndex].needsAttention);

  // Reconstruct and emit the updated script content
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);
}

/**
 * Toggle the needs-attention flag on a cue segment.
 * This persists when the script is saved via the cue's rawData.
 */
function toggleCueNeedsAttention(segmentIndex) {
  console.log('🚩 Toggle needs-attention for cue segment:', segmentIndex);

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  // Get current segments
  const segments = [...scriptSegments.value];

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
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);
}

/**
 * Open the flag note panel for a segment.
 * If segment is not flagged, flags it first.
 */
function openFlagNotePanel(index, type, segment) {
  console.log('🚩 Opening flag note panel:', { index, type });

  // Get the current flag note content
  let currentNote = '';
  if (type === 'paragraph') {
    currentNote = segment.flagNote || '';
    // If not already flagged, flag it now
    if (!segment.needsAttention) {
      toggleNeedsAttention(index);
    }
  } else if (type === 'cue') {
    currentNote = segment.data?.flagNote || '';
    // If not already flagged, flag it now
    if (!segment.data?.needsAttention) {
      toggleCueNeedsAttention(index);
    }
  }

  // Set the panel state
  activeFlagNoteIndex.value = index;
  activeFlagNoteType.value = type;
  flagNoteContent.value = currentNote;
}

/**
 * Close the flag note panel without saving.
 */
function closeFlagNotePanel() {
  console.log('🚩 Closing flag note panel');
  activeFlagNoteIndex.value = null;
  activeFlagNoteType.value = null;
  flagNoteContent.value = '';
}

/**
 * Save the flag note content to the segment.
 */
function saveFlagNote(index, type) {
  console.log('🚩 Saving flag note:', { index, type, content: flagNoteContent.value });

  hasLocalUnsavedChanges.value = true;
  const segments = [...scriptSegments.value];

  if (type === 'paragraph') {
    if (segments[index] && segments[index].type === 'text') {
      segments[index].flagNote = flagNoteContent.value;
    }
  } else if (type === 'cue') {
    if (segments[index] && segments[index].type === 'cue' && segments[index].data) {
      segments[index].data.flagNote = flagNoteContent.value;
      if (segments[index].data.rawData) {
        segments[index].data.rawData.flagNote = flagNoteContent.value;
      }
    }
  }

  // Reconstruct and emit the updated script content
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);

  // Close the panel
  closeFlagNotePanel();
}

/**
 * Resolve (unflag) the segment and close the panel.
 */
function resolveFlag(index, type) {
  console.log('🚩 Resolving flag:', { index, type });

  hasLocalUnsavedChanges.value = true;
  const segments = [...scriptSegments.value];

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
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);

  // Close the panel
  closeFlagNotePanel();
}

/**
 * Splice the LegacyCueConvertButton's replacement segments into
 * scriptSegments. The write goes through useScriptCore's
 * scriptSegments setter, which routes through safeEmitScriptContent
 * (cue-loss tripwire + cue-count regression + shrink guard) automatically.
 *
 * Payload shape (from @/modules/legacyCueConvert/ConvertButton.vue):
 *   { replacementSegments, segmentIndex, audit }
 *
 * Defensive snapshot:
 *   We compute the expected post-splice length and cue count against
 *   what actually lands. If they diverge, the splice itself went wrong
 *   (e.g. segmentIndex out-of-bounds, a non-Array cue mutation, etc.)
 *   — log a console.error before the setter runs so we can trace the
 *   smoking gun. The downstream safeEmitScriptContent guards will also
 *   refuse the emit, but this earlier signal narrows the failure window
 *   from "somewhere in reactivity" to "in this specific splice".
 */
function onLegacyCueConverted({ replacementSegments, segmentIndex }) {
  if (!Array.isArray(replacementSegments) || replacementSegments.length === 0) return;

  const before = scriptSegments.value;
  const beforeLen = before.length;
  const beforeCueCount = before.filter(s => s?.type === 'cue').length;

  const segments = [...before];
  segments.splice(segmentIndex, 1, ...replacementSegments);

  // Expected post-splice math: original minus the one removed plus the
  // replacements. The replaced segment is the flagged TEXT paragraph
  // (type='text'), so cue count should grow by the number of cue
  // segments in replacementSegments.
  const replacementCueCount = replacementSegments.filter(s => s?.type === 'cue').length;
  const expectedLen = beforeLen - 1 + replacementSegments.length;
  const expectedCueCount = beforeCueCount + replacementCueCount;

  const afterLen = segments.length;
  const afterCueCount = segments.filter(s => s?.type === 'cue').length;

  if (afterLen !== expectedLen || afterCueCount !== expectedCueCount) {
    console.error('🚨 onLegacyCueConverted: splice produced unexpected result', {
      segmentIndex,
      beforeLen,
      afterLen,
      expectedLen,
      beforeCueCount,
      afterCueCount,
      expectedCueCount,
      replacementSegmentTypes: replacementSegments.map(s => s?.type),
      replacedSegmentType: before[segmentIndex]?.type,
    });
  }

  scriptSegments.value = segments;
  hasLocalUnsavedChanges.value = true;
  closeFlagNotePanel();
}

/**
 * Update flag note for a paragraph segment (called on input change).
 */
function updateParagraphFlagNote(index, value) {
  hasLocalUnsavedChanges.value = true;
  const segments = [...scriptSegments.value];

  if (segments[index] && segments[index].type === 'text') {
    segments[index].flagNote = value;
  }

  // Reconstruct and emit the updated script content
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);
}

/**
 * Update flag note for a cue segment (called on input change).
 */
function updateCueFlagNote(index, value) {
  hasLocalUnsavedChanges.value = true;
  const segments = [...scriptSegments.value];

  if (segments[index] && segments[index].type === 'cue' && segments[index].data) {
    segments[index].data.flagNote = value;
    if (segments[index].data.rawData) {
      segments[index].data.rawData.flagNote = value;
    }
  }

  // Reconstruct and emit the updated script content
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);
}

/**
 * Handle flag button click - toggles flag on/off. Notes are always on by default.
 * Click on unflagged = flag it (note shows automatically)
 * Click on flagged = unflag it (if minimized, expand first; if visible, unflag)
 */
function handleFlagClick(index, type, segment) {
  const key = `${type}-${index}`;
  const isFlagged = type === 'paragraph' ? segment.needsAttention : segment.data?.needsAttention;

  console.log('🚩 handleFlagClick:', { index, type, isFlagged, key });

  if (!isFlagged) {
    // Not flagged - flag it (note shows automatically, always on by default)
    console.log('🚩 Flagging segment - note will show by default');
    if (type === 'paragraph') {
      toggleNeedsAttention(index);
    } else {
      toggleCueNeedsAttention(index);
    }
    // Ensure not minimized so note shows
    delete minimizedFlagNotes.value[key];
  } else if (minimizedFlagNotes.value[key]) {
    // Flagged but minimized - expand it (don't unflag)
    console.log('🚩 Expanding minimized note');
    delete minimizedFlagNotes.value[key];
  } else {
    // Flagged and visible - unflag it
    console.log('🚩 Unflagging segment');
    if (type === 'paragraph') {
      toggleNeedsAttention(index);
    } else {
      toggleCueNeedsAttention(index);
    }
    delete minimizedFlagNotes.value[key];
  }
}

/**
 * Minimize a flag note panel.
 */
function minimizeFlagNote(type, index) {
  const key = `${type}-${index}`;
  minimizedFlagNotes.value[key] = true;
}

/**
 * Get the first four words from paragraph content for flag note header.
 */
function getFirstFourWords(content) {
  if (!content) return 'Flagged paragraph';
  // Strip HTML tags and get plain text
  const plainText = content.replace(/<[^>]*>/g, '').trim();
  // Split by whitespace and get first 4 words
  const words = plainText.split(/\s+/).slice(0, 4);
  const result = words.join(' ');
  // Add ellipsis if there were more words
  return plainText.split(/\s+/).length > 4 ? result + '...' : result;
}

/**
 * Get a reference string for a cue segment for flag note header.
 */
function getCueReference(segment) {
  if (!segment || !segment.data) return 'Flagged cue';
  const cueType = segment.data.type || segment.data.cueType || 'CUE';
  const slug = segment.data.slug || segment.data.Slug || '';
  return slug ? `${cueType}: ${slug}` : cueType;
}

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
function getSafeInsertionPosition(content, position) {
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
}

/**
 * Find all content segments (paragraphs and cue blocks) with their positions.
 * Used for accurate segment-based insertion that accounts for both element types.
 *
 * @param {string} content - The script content to parse
 * @returns {Array} Array of segment objects with type, index, endIndex, and content
 */
function findAllContentSegments(content) {
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
}

/**
 * Load cue card alignment from settings
 */
async function loadCueCardAlignment() {
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
        cueCardAlignment.value = alignment;
        console.log('✅ Loaded cue card alignment:', cueCardAlignment.value);
      } else {
        console.log('⚠️ No cue card alignment found in settings, using default:', cueCardAlignment.value);
      }
    }
  } catch (error) {
    console.error('Failed to load cue card alignment:', error);
  }
}

// Focus and highlight slug field for newly created items
function focusSlugField() {
  console.log('🎯 focusSlugField() called')
  slugNeedsAttention.value = true
  nextTick(() => {
    const slugField = slugFieldRef.value
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
}

// Handle slug field blur - normalize to lowercase
function handleSlugBlur() {
  slugFieldFocused.value = false;

  if (props.item?.slug && props.item.slug.trim().length > 0) {
    const normalized = props.item.slug.toLowerCase().trim();

    // Only emit update if the slug actually changed
    if (normalized !== props.item.slug) {
      emit('update:slug', normalized);
    }
  }
}

// Parse HH:MM:SS:FF duration format to total seconds
function parseDurationToSeconds(duration) {
  if (!duration || typeof duration !== 'string') return 0;

  const parts = duration.split(':');
  if (parts.length !== 4) return 0;

  const hours = parseInt(parts[0]) || 0;
  const minutes = parseInt(parts[1]) || 0;
  const seconds = parseInt(parts[2]) || 0;
  // Ignore frames (parts[3]) for now

  return (hours * 3600) + (minutes * 60) + seconds;
}

// Convert total seconds to HH:MM:SS:FF duration format
function secondsToDuration(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:00`;
}

// Handle textarea input - update content and auto-resize
function handleTextareaInput(index, value) {
  console.log(`✏️ handleTextareaInput called for index ${index}, value length: ${value?.length}, blockReactiveUpdates: ${blockReactiveUpdates.value}`);

  // Skip update if blockReactiveUpdates is set
  // This prevents conflicting updates during programmatic operations (paragraph creation, merging, etc.)
  if (blockReactiveUpdates.value) {
    console.log('⏭️⏭️⏭️ SKIPPING handleTextareaInput - blockReactiveUpdates is active');
    console.log('⏭️ This prevents interference with paragraph creation/focus logic');
    return;
  }

  updateTextSegment(index, value);
  autoResizeTextarea(index);
}

// Handle contenteditable input - update content from innerHTML
function handleContentEditableInput(index, event) {
  const element = event.target;
  const htmlContent = element.innerHTML;
  console.log(`✏️ handleContentEditableInput called for index ${index}, html length: ${htmlContent?.length}`);

  // CRITICAL FIX: Mark this segment as actively being edited
  // This prevents getSegmentContent from returning buffered content,
  // which would cause Vue to re-render and reset cursor position (causing reverse typing)
  activelyEditingSegment.value = index;
  isActivelyEditing.value = true; // Block watchers during active editing

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

    savedCursorState.value = {
      segmentIndex: index,
      textOffset: textOffset,
      htmlContent: element.innerHTML // Save content to detect if it changed
    };
  }

  // Skip update if blockReactiveUpdates is set
  if (blockReactiveUpdates.value) {
    console.log('⏭️⏭️⏭️ SKIPPING handleContentEditableInput - blockReactiveUpdates is active');
    return;
  }

  // Clean up any browser-generated formatting quirks
  // Browsers wrap pasted lines in <div> or <p> tags - convert to newlines to preserve paragraphs
  // Note: <br[^>]*> catches <br>, <br/>, <br class="Apple-interchange-newline">, etc.
  let cleanedHtml = stripRevisionMarkup(htmlContent)
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

  updateTextSegment(index, cleanedHtml);
  hasLocalUnsavedChanges.value = true;
}

// flushPendingChanges — moved to useScriptCore composable

// Handle paste for contenteditable divs - detect paragraph breaks and split into multiple paragraphs
function handleContentEditablePaste(index, event) {
  event.preventDefault();

  // Set paste cooldown on the element to prevent v-safe-html from overwriting
  const el = event.target;
  el._pasteCooldown = true;
  clearTimeout(el._pasteCooldownTimer);
  el._pasteCooldownTimer = setTimeout(() => { el._pasteCooldown = false; }, 5000);

  const clipboardData = event.clipboardData || window.clipboardData;
  if (!clipboardData) {
    console.error('📋 PASTE FAILED: No clipboard data available');
    return;
  }
  const plainText = clipboardData.getData('text/plain');
  const htmlText = clipboardData.getData('text/html');

  console.log('📋 Paste detected in segment', index);
  console.log('📋 Plain text:', JSON.stringify(plainText?.substring(0, 200)));
  console.log('📋 HTML text:', JSON.stringify(htmlText?.substring(0, 500)));
  console.log('📋 Clipboard types available:', [...clipboardData.types]);

  // If clipboard is completely empty, bail
  if (!plainText && !htmlText) {
    console.error('📋 PASTE FAILED: Clipboard returned empty data for both text/plain and text/html');
    return;
  }

  // Capture cursor state before any async work
  const element = event.target;
  const selection = window.getSelection();
  let savedRange = null;
  if (selection && selection.rangeCount > 0 && element.contains(selection.anchorNode)) {
    savedRange = selection.getRangeAt(0).cloneRange();
  }

  // Detect Google Docs paste
  const isGoogleDocs = htmlText && htmlText.includes('docs-internal-guid');

  if (isGoogleDocs) {
    // Show spinner for Google Docs paste processing
    isPasting.value = true;
    console.log('📋 Google Docs paste detected — using DOM-walking parser');

    // Use requestAnimationFrame to let the spinner render before processing
    const spinnerStart = Date.now();
    requestAnimationFrame(() => {
      setTimeout(() => {
        const paragraphs = parseGoogleDocsPaste(htmlText, plainText);
        _applyPastedParagraphs(index, paragraphs, element, savedRange);

        // Clear paste cooldown and editing flags so v-safe-html can render the new content
        el._pasteCooldown = false;
        clearTimeout(el._pasteCooldownTimer);
        activelyEditingSegment.value = null;
        isActivelyEditing.value = false;

        // Force re-parse so Vue creates the new segment elements
        segmentReparseKey.value++;

        // Wait for minimum spinner time, then wait for Vue to finish rendering before dismissing
        // TODO: Bring this back down to 1000ms once paste rendering is confirmed reliable
        const elapsed = Date.now() - spinnerStart;
        const remaining = Math.max(0, 5000 - elapsed);
        setTimeout(() => {
          // $nextTick fires after Vue's reactivity flush — content is in the DOM
          nextTick(() => {
            isPasting.value = false;
          });
        }, remaining);
      }, 50); // Small delay so the overlay actually renders
    });
  } else {
    // Non-Google paste — process synchronously (fast path)
    const paragraphs = parseGenericPaste(htmlText, plainText);
    _applyPastedParagraphs(index, paragraphs, element, savedRange);
  }
}

// _parseGoogleDocsPaste — extracted to useEditorPaste composable (available as parseGoogleDocsPaste)
// _cleanGoogleDocsNode — extracted to useEditorPaste composable (available as cleanGoogleDocsNode)
// _parseGenericPaste — extracted to useEditorPaste composable (available as parseGenericPaste)

/**
 * Apply parsed paragraphs to the editor — handles both single and multi-paragraph paste.
 * Shared by both Google Docs and generic paste paths.
 */
function _applyPastedParagraphs(index, paragraphs, element, savedRange) {
  const currentSegment = scriptSegments.value[index];

  if (paragraphs.length === 1) {
    // Single paragraph - insert at cursor position in the DOM
    const sel = window.getSelection();
    let inserted = false;

    // Restore saved range if available
    if (savedRange && element.contains(savedRange.startContainer)) {
      try {
        sel.removeAllRanges();
        sel.addRange(savedRange);
        const range = sel.getRangeAt(0);
        range.deleteContents();
        const textNode = document.createTextNode(paragraphs[0]);
        range.insertNode(textNode);
        range.setStartAfter(textNode);
        range.setEndAfter(textNode);
        sel.removeAllRanges();
        sel.addRange(range);
        inserted = true;
      } catch (e) {
        console.warn('📋 Selection API insert failed:', e);
      }
    }
    if (!inserted) {
      const existing = element.textContent || '';
      element.textContent = existing + paragraphs[0];
    }

    // Capture into edit buffer (strip any revision markup)
    segmentEditBuffer[index] = stripRevisionMarkup(element.innerHTML);
    activelyEditingSegment.value = index;
    isActivelyEditing.value = true;
    hasLocalUnsavedChanges.value = true;

    // Reconstruct and emit so rawMarkdownContent stays in sync with the DOM.
    const segments = [...scriptSegments.value];
    if (segments[index]) {
      segments[index] = { ...segments[index], content: segmentEditBuffer[index] };
    }
    const newRawContent = reconstructRawContent(segments);
    emit('update:scriptContent', newRawContent);
    console.log('📋 Single paragraph pasted — DOM, buffer, and rawMarkdownContent all synced');
  } else {
    // Multiple paragraphs - need to split and create new paragraph segments
    console.log('📋 Multiple paragraphs detected - creating', paragraphs.length, 'segments');

    // Get cursor position to split current content
    let contentBefore = '';
    let contentAfter = '';

    if (savedRange && element.contains(savedRange.startContainer)) {
      try {
        // Restore range for content extraction
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(savedRange);

        // Get content BEFORE cursor
        const beforeRange = document.createRange();
        beforeRange.selectNodeContents(element);
        beforeRange.setEnd(savedRange.startContainer, savedRange.startOffset);
        const beforeFragment = beforeRange.cloneContents();
        const tempBefore = document.createElement('div');
        tempBefore.appendChild(beforeFragment);
        contentBefore = tempBefore.innerHTML.trim();

        // Get content AFTER cursor
        const afterRange = document.createRange();
        afterRange.selectNodeContents(element);
        afterRange.setStart(savedRange.endContainer, savedRange.endOffset);
        const afterFragment = afterRange.cloneContents();
        const tempAfter = document.createElement('div');
        tempAfter.appendChild(afterFragment);
        contentAfter = tempAfter.innerHTML.trim();
      } catch (e) {
        console.warn('📋 Range extraction failed, pasting at end:', e);
      }
    }

    // Build new segments array
    const segments = [...scriptSegments.value];
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

    // Set focus to end of pasted content
    pendingFocusSegmentIndex.value = index + paragraphs.length - (contentAfter ? 0 : 1);

    // Reconstruct, emit, and save immediately
    const newRawContent = reconstructRawContent(segments);
    emit('update:scriptContent', newRawContent);
    nextTick(() => emit('save-current'));
    hasLocalUnsavedChanges.value = true;

    console.log('📋 Created', newSegments.length, 'new paragraph segments, save triggered');
  }
}

// Handle keydown for contenteditable divs
function handleContentEditableKeydown(index, event) {
  console.log('🎹 ContentEditable key pressed:', event.key, 'in segment', index);

  // Allow space key to pass through naturally (browser handles insertion)
  if (event.key === ' ' || event.code === 'Space') {
    return;
  }

  // Ctrl+B: Toggle bold using execCommand
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'b') {
    event.preventDefault();
    document.execCommand('bold', false, null);
    syncContentEditableToSegment(index, event.target);
    return;
  }

  // Ctrl+I: Toggle italic using execCommand
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'i') {
    event.preventDefault();
    document.execCommand('italic', false, null);
    syncContentEditableToSegment(index, event.target);
    return;
  }

  // Ctrl+U: Toggle underline using execCommand
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'u') {
    event.preventDefault();
    document.execCommand('underline', false, null);
    syncContentEditableToSegment(index, event.target);
    return;
  }

  // Ctrl+S: Save all
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 's') {
    event.preventDefault();
    handleSaveAll();
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
    const lastEnterTime = lastEnterState.value[index]?.time || 0;
    const lastEnterPosition = lastEnterState.value[index]?.position || -1;
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
    lastEnterState.value[index] = { time: now, position: caretOffset };

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

      blockReactiveUpdates.value = true;

      // CRITICAL FIX: Clear active editing flags BEFORE creating new paragraph
      isActivelyEditing.value = false;
      activelyEditingSegment.value = null;
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
      if (updateDebounceTimers && updateDebounceTimers[index]) {
        clearTimeout(updateDebounceTimers[index]);
        delete updateDebounceTimers[index];
      }
      if (segmentEditBuffer && segmentEditBuffer[index]) {
        delete segmentEditBuffer[index];
      }

      // Create new paragraph with content after cursor
      createNewParagraphAfterWithContent(index, contentAfter, contentBefore);

      // Restore scroll and unlock after a delay
      setTimeout(() => {
        if (scrollWrapper) {
          scrollWrapper.style.overflow = '';
          scrollWrapper.scrollTop = savedWrapperScroll;
        }
        if (scriptContainer) {
          scriptContainer.scrollTop = savedContainerScroll;
        }
        blockReactiveUpdates.value = false;
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
          mergeParagraphWithPrevious(index);
        }
      }
    }
  }

  // Ctrl+Alt+H: Toggle highlight
  if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'h') {
    event.preventDefault();
    // Use custom highlight since execCommand doesn't have built-in highlight
    toggleHighlightContentEditable(index, event.target);
  }

  // Alt+/: Propose revision (cut or cut+replace)
  if (event.altKey && !event.ctrlKey && !event.shiftKey && event.key === '/') {
    event.preventDefault();
    event.stopPropagation();
    startRevisionMode(index);
    return;
  }

  // Alt+.: Propose addition (insert new text)
  if (event.altKey && !event.ctrlKey && !event.shiftKey && event.key === '.') {
    event.preventDefault();
    event.stopPropagation();
    startAdditionMode(index);
    return;
  }
}

// syncContentEditableToSegment — moved to useScriptCore composable

// Toggle highlight for contenteditable (mark tag)
function toggleHighlightContentEditable(index, element) {
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
      syncContentEditableToSegment(index, element);
      return;
    }
    parentMark = parentMark.parentNode;
  }

  // Not highlighted - add mark
  const mark = document.createElement('mark');
  try {
    range.surroundContents(mark);
    syncContentEditableToSegment(index, element);
  } catch (e) {
    console.warn('Could not apply highlight - selection spans multiple elements');
  }
}

// --- Revision System (Script Mode) ---

// Get current username from auth
function _getRevisionUser() {
  try {
    const userData = JSON.parse(localStorage.getItem('user-data') || '{}');
    return userData.username || 'unknown';
  } catch {
    return 'unknown';
  }
}

// Get current timestamp for revision
function _getRevisionTimestamp() {
  return new Date().toISOString().slice(0, 16);
}

// Build rev open tag with user and timestamp attributes
function _buildRevOpenTag() {
  const user = _getRevisionUser();
  const ts = _getRevisionTimestamp();
  return `<rev user="${user}" ts="${ts}">`;
}

// Calculate relative time string from ISO timestamp
function _relativeTime(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// Start revision mode: immediately wrap selected text in <rev>, then show replacement input bar
function startRevisionMode(index) {
  const selection = window.getSelection();
  if (!selection.rangeCount || selection.isCollapsed) {
    flashMessage.value.show = true;
    flashMessage.value.text = 'Select text to propose a revision';
    flashMessage.value.color = 'warning';
    flashMessage.value.timeout = 1500;
    return;
  }

  const selectedText = selection.toString();
  if (!selectedText.trim()) {
    flashMessage.value.show = true;
    flashMessage.value.text = 'Select text to propose a revision';
    flashMessage.value.color = 'warning';
    flashMessage.value.timeout = 1500;
    return;
  }

  // Immediately insert kill-only <rev> tag so strikethrough renders right away
  const segment = scriptSegments.value[index];
  if (!segment) return;
  let content = segment.content || '';
  const openTag = _buildRevOpenTag();
  const escapedText = selectedText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(escapedText);

  if (!regex.test(content)) return;

  content = content.replace(regex, `${openTag}${selectedText}</rev>`);
  updateTextSegment(index, content);
  hasLocalUnsavedChanges.value = true;

  // Now show the replacement input bar
  activeRevision.value = {
    index,
    killText: selectedText,
    replacementText: '',
    mode: 'revise',
    openTag // save so finalizeRevision can find the exact tag
  };
  revisionEntryMode.value = true;

  // Focus the input on next tick
  nextTick(() => {
    const input = revEntryInput.value;
    if (input) {
      const el = Array.isArray(input) ? input[0] : input;
      if (el) el.focus();
    }
  });
}

// Start addition mode: show replacement input bar (no kill text)
function startAdditionMode(index) {
  activeRevision.value = {
    index,
    killText: '',
    replacementText: '',
    mode: 'add'
  };
  revisionEntryMode.value = true;

  nextTick(() => {
    const input = revEntryInput.value;
    if (input) {
      const el = Array.isArray(input) ? input[0] : input;
      if (el) el.focus();
    }
  });
}

// Finalize revision: update existing <rev> tag with replacement text if provided
// hasReplacement: true if user confirmed (Enter/checkmark), false if cancelled (ESC/X)
// Confirm revision (Enter or checkmark). Commits kill-only or kill+replace.
function finalizeRevision() {
  if (!activeRevision.value) return;

  const { index, killText, replacementText, mode, openTag } = activeRevision.value;
  const segment = scriptSegments.value[index];
  if (!segment) {
    activeRevision.value = null;
    revisionEntryMode.value = false;
    return;
  }

  let content = segment.content || '';
  const addText = replacementText ? replacementText.trim() : '';

  if (mode === 'revise' && addText) {
    // Kill-only tag is already in content. Update it to include replacement.
    const escapedKill = killText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const tagPattern = new RegExp(
      `(<rev\\s+user="[^"]*"\\s+ts="[^"]*">)${escapedKill}</rev>`
    );
    content = content.replace(tagPattern, `$1${killText}|${addText}</rev>`);
    updateTextSegment(index, content);
    hasLocalUnsavedChanges.value = true;
  } else if (mode === 'add' && addText) {
    // Add-only: insert <rev>|addText</rev> at end of content
    const addOpenTag = openTag || _buildRevOpenTag();
    const revTag = `${addOpenTag}|${addText}</rev>`;
    content = content + revTag;
    updateTextSegment(index, content);
    hasLocalUnsavedChanges.value = true;
  }
  // If mode === 'revise' and no addText, kill-only tag is already in place — nothing more needed

  // Exit revision mode
  activeRevision.value = null;
  revisionEntryMode.value = false;
}

// Cancel revision (ESC or X button). Removes the <rev> tag, restores original text.
function cancelRevision() {
  if (!activeRevision.value) return;

  const { index, killText, mode } = activeRevision.value;
  const segment = scriptSegments.value[index];

  if (segment && mode === 'revise') {
    // Remove the kill-only <rev> tag that was already inserted, restoring original text
    let content = segment.content || '';
    const escapedKill = killText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const tagPattern = new RegExp(
      `<rev\\s+user="[^"]*"\\s+ts="[^"]*">${escapedKill}</rev>`
    );
    content = content.replace(tagPattern, killText);
    updateTextSegment(index, content);
  }

  // Exit revision mode
  activeRevision.value = null;
  revisionEntryMode.value = false;
}

// Transform <rev> tags in segment content to rendered HTML for display
// Uses custom elements (rev-block, rev-kill, rev-add, rev-meta, rev-btn) to avoid
// triggering the unwelcome HTML tag check which forbids <span>, <button>, etc.
function renderRevisionTags(content) {
  if (!content || !content.includes('<rev ')) return content;

  return content.replace(
    /<rev\s+user="([^"]*)"\s+ts="([^"]*)">([\s\S]*?)<\/rev>/g,
    (match, user, ts, inner) => {
      const pipeIdx = inner.indexOf('|');
      let killText = '';
      let addText = '';

      if (pipeIdx === -1) {
        killText = inner;
      } else {
        killText = inner.substring(0, pipeIdx);
        addText = inner.substring(pipeIdx + 1);
      }

      const relTime = _relativeTime(ts);
      const metaLabel = `${user} \u00B7 ${relTime}`;

      let html = '<rev-block contenteditable="false">';
      if (killText) {
        html += `<rev-kill>${killText}</rev-kill>`;
      }
      if (addText) {
        html += `<rev-add>${addText}</rev-add>`;
      }
      html += '<rev-actions>';
      html += `<rev-meta>${metaLabel}</rev-meta>`;
      html += '<rev-btn data-rev-action="accept" title="Accept revision">&#10003;</rev-btn>';
      html += '<rev-btn data-rev-action="reject" title="Reject revision">&#10007;</rev-btn>';
      html += '</rev-actions></rev-block>';
      return html;
    }
  );
}

// Count <rev> tags in a segment's content
function getRevisionCount(segmentIndex) {
  const segment = scriptSegments.value[segmentIndex];
  if (!segment) return 0;
  const content = segment.content || '';
  const matches = content.match(/<rev\s+/g);
  return matches ? matches.length : 0;
}

// Accept a single revision: replace <rev> block with replacement text
function acceptRevision(index, revBlockEl) {
  const element = revBlockEl.closest('[contenteditable="true"]');
  if (!element) return;

  // Find the raw <rev> tag in the segment content by matching position
  const segment = scriptSegments.value[index];
  if (!segment) return;

  let content = segment.content || '';
  // Replace the first <rev> tag found (we'll process one at a time)
  content = content.replace(
    /<rev\s+user="[^"]*"\s+ts="[^"]*">([\s\S]*?)<\/rev>/,
    (match, inner) => {
      const pipeIdx = inner.indexOf('|');
      if (pipeIdx === -1) return ''; // Kill only — remove entirely
      return inner.substring(pipeIdx + 1); // Return replacement text
    }
  );

  updateTextSegment(index, content);
  hasLocalUnsavedChanges.value = true;
  // Trigger immediate save
  nextTick(async () => {
    await flushPendingChanges();
    emit('save-all');
  });
}

// Reject a single revision: replace <rev> block with original text
function rejectRevision(index, revBlockEl) {
  const element = revBlockEl.closest('[contenteditable="true"]');
  if (!element) return;

  const segment = scriptSegments.value[index];
  if (!segment) return;

  let content = segment.content || '';
  content = content.replace(
    /<rev\s+user="[^"]*"\s+ts="[^"]*">([\s\S]*?)<\/rev>/,
    (match, inner) => {
      const pipeIdx = inner.indexOf('|');
      if (pipeIdx === -1) return inner; // Kill only — restore original
      return inner.substring(0, pipeIdx); // Return original text (left of pipe)
    }
  );

  updateTextSegment(index, content);
  hasLocalUnsavedChanges.value = true;
  nextTick(async () => {
    await flushPendingChanges();
    emit('save-all');
  });
}

// Accept all revisions in a segment
function acceptAllRevisions(index) {
  const segment = scriptSegments.value[index];
  if (!segment) return;

  let content = segment.content || '';
  content = content.replace(
    /<rev\s+user="[^"]*"\s+ts="[^"]*">([\s\S]*?)<\/rev>/g,
    (match, inner) => {
      const pipeIdx = inner.indexOf('|');
      if (pipeIdx === -1) return '';
      return inner.substring(pipeIdx + 1);
    }
  );

  updateTextSegment(index, content);
  hasLocalUnsavedChanges.value = true;
  nextTick(async () => {
    await flushPendingChanges();
    emit('save-all');
  });
}

// Reject all revisions in a segment
function rejectAllRevisions(index) {
  const segment = scriptSegments.value[index];
  if (!segment) return;

  let content = segment.content || '';
  content = content.replace(
    /<rev\s+user="[^"]*"\s+ts="[^"]*">([\s\S]*?)<\/rev>/g,
    (match, inner) => {
      const pipeIdx = inner.indexOf('|');
      if (pipeIdx === -1) return inner;
      return inner.substring(0, pipeIdx);
    }
  );

  updateTextSegment(index, content);
  hasLocalUnsavedChanges.value = true;
  nextTick(async () => {
    await flushPendingChanges();
    emit('save-all');
  });
}

// Handle click on revision accept/reject buttons (event delegation)
function handleRevisionAction(event, segmentIndex) {
  const btn = event.target.closest('rev-btn');
  if (!btn) return;

  const action = btn.getAttribute('data-rev-action');
  const revBlock = btn.closest('rev-block');
  if (!revBlock) return;

  event.preventDefault();
  event.stopPropagation();

  if (action === 'accept') {
    acceptRevision(segmentIndex, revBlock);
  } else if (action === 'reject') {
    rejectRevision(segmentIndex, revBlock);
  }
}

// --- Revision System (Code/Textarea Mode) ---

// Wrap selected text in <rev> tags (code mode)
function toggleRevisionSelection(segmentIndex, textarea) {
  const selectionStart = textarea.selectionStart;
  const selectionEnd = textarea.selectionEnd;

  if (selectionStart === selectionEnd) {
    flashMessage.value.show = true;
    flashMessage.value.text = 'Select text to propose a revision';
    flashMessage.value.color = 'warning';
    return;
  }

  const openTag = _buildRevOpenTag();
  toggleSelectionFormatting(segmentIndex, textarea, openTag, '</rev>', 'revision');
}

// Insert <rev>|</rev> at cursor position (code mode addition)
function insertAdditionTag(segmentIndex, textarea) {
  const pos = textarea.selectionStart;
  const content = textarea.value;
  const openTag = _buildRevOpenTag();
  const tag = `${openTag}|</rev>`;

  const newContent = content.substring(0, pos) + tag + content.substring(pos);
  textarea.value = newContent;

  // Place cursor after the pipe, inside the tag
  const cursorPos = pos + openTag.length + 1; // after the |
  textarea.setSelectionRange(cursorPos, cursorPos);

  updateTextSegment(segmentIndex, newContent);
  hasLocalUnsavedChanges.value = true;
}

// Custom auto-resize for textareas and contenteditable divs
function autoResizeTextarea(index) {
  nextTick(() => {
    const textareaRefArray = instance.proxy.$refs[`textareaRef-${index}`];

    // Template refs in v-for return arrays, so get the first element
    const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;

    if (!textareaRef) return;

    // Handle contenteditable div (direct HTMLElement)
    if (textareaRef instanceof HTMLElement && textareaRef.contentEditable === 'true') {
      // Contenteditable divs auto-size naturally, just update line count
      nextTick(() => {
        updateLineCount(index);
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

        nextTick(() => {
          updateLineCount(index);
        });
      }
    }
  });
}

// Calculate number of VISUAL lines in a textarea (based on rendered height)
function getLineCount(index) {
  // Return cached value if available
  if (segmentLineCounts.value[index]) {
    return segmentLineCounts.value[index];
  }

  const content = getSegmentContent(index);
  if (!content || content.trim() === '') return 1;

  // Fallback: count newlines
  const newlineCount = (content.match(/\n/g) || []).length;
  return newlineCount + 1;
}

// Update line count for a segment (called after resize)
function updateLineCount(index) {
  const textareaRefArray = instance.proxy.$refs[`textareaRef-${index}`];
  const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;

  if (!textareaRef) return;

  const lineHeight = 27; // 19px font * ~1.42 line-height (matches .speaker-contenteditable CSS)
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
    segmentLineCounts.value[index] = lineCount;
  }
}

// Calculate absolute line number across all paragraphs
function getAbsoluteLineNumber(segmentIndex, relativeLineNum) {
  let absoluteLine = 0;

  // Sum up all lines from previous segments
  for (let i = 0; i < segmentIndex; i++) {
    if (scriptSegments.value[i] && scriptSegments.value[i].type === 'text' && scriptSegments.value[i].needsParagraphTags) {
      absoluteLine += getLineCount(i);
    }
  }

  // Add the current relative line number
  return absoluteLine + relativeLineNum;
}

// ===== COLLAPSE MODE HELPER METHODS =====
// Extracted to useCollapseMode composable (available via setup()):
//   getCollapsedFirstWords, getCollapsedLastWords, getCollapsedCueStyle,
//   getCollapsedOutcue, hexToHsl
// getCollapsedLineRange remains here because it depends on component methods

/**
 * Get the line range for a collapsed paragraph display
 * Returns a string like "33-43" representing the absolute line numbers
 */
function getCollapsedLineRange(segmentIndex) {
  const startLine = getAbsoluteLineNumber(segmentIndex, 1);
  const lineCount = getLineCount(segmentIndex);
  const endLine = startLine + lineCount - 1;

  if (lineCount === 1) {
    return `${startLine}`;
  }
  return `${startLine}-${endLine}`;
}

// ===== END COLLAPSE MODE HELPER METHODS =====

// stripYamlFrontmatter — extracted to useContentSanitizer composable (available via setup())
// extractYamlFrontmatter — extracted to useContentSanitizer composable (available via setup())

// Generate current frontmatter from metadata
function generateCurrentFrontmatter() {
  if (!props.currentItemMetadata) return '';

  const metadata = props.currentItemMetadata;

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
}

// Reconstruct script content while preserving and updating frontmatter
function reconstructScriptContentWithFrontmatter(segments) {
  const bodyContent = CueParser.reconstructContent(segments);
  const currentFrontmatter = generateCurrentFrontmatter();

  if (currentFrontmatter) {
    return currentFrontmatter + '\n' + bodyContent;
  }

  return bodyContent;
}

// Comprehensive YAML frontmatter validation and synchronization
function validateAndSyncYamlFrontmatter() {
  if (!props.scriptContent || !props.currentItemMetadata) {
    return false; // No content or metadata to validate
  }

  try {
    // DEBUGGING: Log metadata to detect contamination
    if (props.currentItemMetadata.AssetID) {
      console.log(`🔍 YAML Validation - Current AssetID: ${props.currentItemMetadata.AssetID}, Title: ${props.currentItemMetadata.title}, Type: ${props.currentItemMetadata.type}, Order: ${props.currentItemMetadata.order}`);
    }

    // Check for multiple frontmatter blocks or malformed YAML first
    const multipleBlocksInfo = detectMultipleFrontmatterBlocks(props.scriptContent);
    if (multipleBlocksInfo.isMalformed) {
      if (multipleBlocksInfo.hasMultiple) {
        console.warn(`🚨 MULTIPLE FRONTMATTER BLOCKS DETECTED: ${multipleBlocksInfo.blockCount} blocks found`);
      }
      if (multipleBlocksInfo.hasYamlAfterClosing) {
        console.warn('🚨 MALFORMED YAML: Found YAML content after frontmatter closing ---');
      }
      console.warn('This indicates data contamination - will clean up automatically');

      // Force update to clean up malformed YAML
      const bodyContent = stripYamlFrontmatter(props.scriptContent);
      const correctFrontmatter = generateCurrentFrontmatter();
      const correctedContent = correctFrontmatter + '\n' + bodyContent;

      console.log('🧹 Cleaning up malformed YAML frontmatter');
      emit('update:scriptContent', correctedContent);
      return true; // Content was updated
    }

    // Extract current frontmatter from script content
    const existingFrontmatter = extractYamlFrontmatter(props.scriptContent);
    const bodyContent = stripYamlFrontmatter(props.scriptContent);

    // Generate what the frontmatter should be based on current metadata
    const correctFrontmatter = generateCurrentFrontmatter();

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
      if (existingFrontmatter && !isValidYaml(existingFrontmatter)) {
        updateReason = 'Invalid YAML frontmatter detected';
      }
    }

    if (needsUpdate) {
      console.log(`🔧 Auto Scrub: ${updateReason}`);

      // Reconstruct content with correct frontmatter
      const correctedContent = correctFrontmatter + '\n' + bodyContent;

      // Update the script content
      emit('update:scriptContent', correctedContent);

      return true; // Indicate that content was updated
    }

    return false; // No updates needed

  } catch (error) {
    console.error('Error validating YAML frontmatter:', error);
    return false;
  }
}

// Enhanced YAML validation - detects multiple frontmatter blocks
function isValidYaml(yamlString) {
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
}

// detectMultipleFrontmatterBlocks, validateScriptContent, repairScriptContent,
// validateAndRepairBeforeSave — moved to useScriptCore composable

// emitScriptContent — core logic moved to useScriptCore composable
// This wrapper adds the showRepairNotification callback for UI feedback
function emitScriptContent(content, skipValidation = false) {
  _scriptCoreEmitScriptContent(content, skipValidation, {
    onRepaired: (repairs) => showRepairNotification(repairs)
  });
}

/**
 * Show a subtle notification when content is auto-repaired
 * (Kept in component because it depends on flashMessage UI state)
 */
function showRepairNotification(repairs) {
  if (!repairs || repairs.length === 0) return;

  const repairDescriptions = repairs.map(r => r.description).join(', ');
  console.info(`Auto-repair applied: ${repairDescriptions}`);

  // Use flash message if available
  if (flashMessage.value) {
    flashMessage.value.show = true;
    flashMessage.value.text = `Auto-fixed: ${repairs.length} issue(s)`;
    flashMessage.value.color = 'warning';
  }
}

function updateMetadata(field, value) {
  // If slug is being updated, check if it's valid and clear attention highlight
  if (field === 'slug' && value && value.trim().length > 0) {
    // Check if slug passes validation rules
    const isValid = props.slugRules.every(rule => rule(value) === true)
    if (isValid) {
      slugNeedsAttention.value = false
      console.log('✅ Valid slug entered, clearing attention highlight')
    }
  }

  emit('metadata-change', { field, value })
}

// Determine if speaker header should be shown
function shouldShowSpeakerHeader(index, speaker) {
  // Only show header if:
  // 1.) It is the first paragraph of a segment, OR
  // 2.) The speaker changes with this <p>

  // Show header if it's the first segment
  if (index === 0) {
    return true;
  }

  // Show header if previous segment has different speaker
  const previousSegment = scriptSegments.value[index - 1];

  // If previous segment is a cue, this is first paragraph after cue (condition 1)
  if (previousSegment && previousSegment.type === 'cue') {
    return true;
  }

  // If previous segment is text with different speaker (condition 2)
  if (previousSegment && previousSegment.type === 'text' && previousSegment.speaker !== speaker) {
    return true;
  }

  return false;
}

// Format datetime for display
function formatDateTime(dateString) {
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
}

// Format field labels for custom fields (convert snake_case to Title Case)
function formatFieldLabel(fieldName) {
  return fieldName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Parse tags for display in combobox
function parseTagsForDisplay(tags) {
  if (!tags) return []
  if (Array.isArray(tags)) return tags
  if (typeof tags === 'string') {
    // Handle comma-separated string or YAML array-like format
    return tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
  }
  return []
}

// Update tags from combobox back to appropriate format
function updateTagsFromCombobox(tags) {
  // Convert array back to comma-separated string for consistency
  const tagString = Array.isArray(tags) ? tags.join(', ') : tags
  updateMetadata('tags', tagString)
}

// Format timestamp for autosave display
function formatTimestamp(date) {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Insert broadcast cue at cursor position
async function insertCue(cueType) {
  console.log('🎬 insertCue called with:', cueType);
  console.log('🎬 Current editorMode:', props.editorMode);

  // CODE MODE: Simpler workflow - insert at cursor position
  if (props.editorMode === 'code') {
    console.log('📝 Code mode detected - using cursor-based insertion');

    // Store cursor position from code textarea
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Stored cursor position:', pendingCursorPosition.value);
    }

    pendingCueType.value = cueType;

    // Show modal immediately for code mode - emit to parent for all cue types
    if (cueType === 'IMG') {
      emit('show-img-modal');
      return;
    }

    if (cueType === 'GFX') {
      emit('show-gfx-modal');
      return;
    }

    if (cueType === 'FSQ') {
      emit('show-fsq-modal');
      return;
    }

    if (cueType === 'SOT') {
      emit('show-sot-modal');
      return;
    }

    if (cueType === 'VO') {
      emit('show-vo-modal');
      return;
    }

    if (cueType === 'NAT') {
      emit('show-nat-modal');
      return;
    }

    if (cueType === 'RIF') {
      emit('show-rif-modal');
      return;
    }

    if (cueType === 'PKG') {
      emit('show-pkg-modal');
      return;
    }

    if (cueType === 'NOTE' || cueType === 'DIR') {
      emit('show-dir-modal');
      return;
    }

    if (cueType === 'BUMP') {
      emit('show-bump-modal');
      return;
    }

    if (cueType === 'STING') {
      emit('show-sting-modal');
      return;
    }

    // Fallback for other cue types
    const cueText = `**[${cueType}: ]**`;
    insertCueAtCursor(cueText);
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
  pendingCueType.value = cueType;

  // Snapshot insertion index NOW before modal opens and blur clears state
  if (selectedSegmentIndex.value !== null && selectedSegmentIndex.value >= 0) {
    pendingCueInsertionIndex.value = selectedSegmentIndex.value + 1;
  } else if (lastKnownParagraphIndex.value !== null && lastKnownParagraphIndex.value >= 0) {
    pendingCueInsertionIndex.value = lastKnownParagraphIndex.value + 1;
  } else {
    pendingCueInsertionIndex.value = scriptSegments.value.length; // End of ALL segments
  }
  console.log('📍 Snapshotted pendingCueInsertionIndex:', pendingCueInsertionIndex.value);

  // Small delay to let flash complete
  setTimeout(() => {
    // Open the appropriate modal
    if (cueType === 'SOT') {
      emit('show-sot-modal');
      console.log('🎬 SOT modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'IMG') {
      emit('show-img-modal');
      console.log('🎬 IMG modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'FSQ') {
      emit('show-fsq-modal');
      console.log('🎬 FSQ modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'GFX') {
      emit('show-gfx-modal');
      console.log('🎬 GFX modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'VO') {
      emit('show-vo-modal');
      console.log('🎬 VO modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'NAT') {
      emit('show-nat-modal');
      console.log('🎬 NAT modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'RIF') {
      emit('show-rif-modal');
      console.log('🎬 RIF modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'PKG') {
      emit('show-pkg-modal');
      console.log('🎬 PKG modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'NOTE' || cueType === 'DIR') {
      emit('show-dir-modal');
      console.log('🎬 NOTE modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'BUMP') {
      emit('show-bump-modal');
      console.log('🎬 BUMP modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'STING') {
      emit('show-sting-modal');
      console.log('🎬 STING modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'VOX') {
      emit('show-vox-modal');
      console.log('🎬 VOX modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'MUS') {
      emit('show-mus-modal');
      console.log('🎬 MUS modal opened - placement overlay will activate when modal closes');
      return;
    }

    if (cueType === 'LIVE') {
      emit('show-live-modal');
      console.log('🎬 LIVE modal opened - placement overlay will activate when modal closes');
      return;
    }

    // Fallback for other cue types
    const cueText = `**[${cueType}: ]**`;
    insertCueAtCursor(cueText);
  }, 250);
}

// Get theme color for cue type
function getCueColor(cueType) {
  const colorName = getColorValue(cueType.toLowerCase())
  return resolveVuetifyColor(colorName)
}

// Get cue button style object
function getContrastColor(bgColor) {
  // Parse hex or rgb color and return black or white for max contrast
  let r, g, b
  if (bgColor.startsWith('#')) {
    const hex = bgColor.replace('#', '')
    r = parseInt(hex.substr(0, 2), 16)
    g = parseInt(hex.substr(2, 2), 16)
    b = parseInt(hex.substr(4, 2), 16)
  } else if (bgColor.startsWith('rgb')) {
    const match = bgColor.match(/(\d+)/g)
    if (match) {
      r = parseInt(match[0]); g = parseInt(match[1]); b = parseInt(match[2])
    } else {
      return '#ffffff'
    }
  } else {
    return '#ffffff'
  }
  // Relative luminance (WCAG formula)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#000000' : '#ffffff'
}

function getCueButtonStyle(cueType) {
  const backgroundColor = getCueColor(cueType)
  const textColor = getContrastColor(backgroundColor)
  return {
    backgroundColor: backgroundColor,
    borderColor: backgroundColor,
    color: textColor
  }
}

function toggleCueMenu() {
  cueMenuOpen.value = !cueMenuOpen.value
}

function insertCueFromMenu(cueType) {
  // Flash the button, then insert
  flashingCueType.value = cueType
  setTimeout(() => {
    flashingCueType.value = null
    cueMenuOpen.value = false
  }, 200)
  insertCue(cueType)
}

// Normalize slug for filename
function normalizeSlug(slug) {
  return slug
    .toLowerCase() // Convert to lowercase
    .replace(/[^\w\s-]/g, '') // Remove punctuation except spaces and hyphens
    .replace(/\s+/g, '-') // Convert spaces to hyphens
    .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
    .replace(/^-|-$/g, '') // Remove leading/trailing hyphens
}

// Enhanced slug normalization for media filenames
function normalizeSlugForMedia(slug) {
  return slug
    .toLowerCase() // 1. Convert to lowercase
    .replace(/[^\w\s-]/g, '') // 2. Remove all punctuation except spaces and hyphens
    .replace(/\s+/g, '-') // 3. Replace spaces with dashes
    .replace(/-+/g, '-') // Replace multiple dashes with single dash
    .replace(/^-|-$/g, '') // Remove leading/trailing dashes
}

// Check if slug already exists in current episode's cues
function isSlugDuplicate(slug) {
  if (!props.scriptContent) return false;

  // Extract all existing slugs from cue blocks
  const slugPattern = /\[Slug:\s*([^\]]+)\]/gi;
  const matches = props.scriptContent.matchAll(slugPattern);

  const existingSlugs = [];
  for (const match of matches) {
    existingSlugs.push(match[1].trim().toLowerCase());
  }

  console.log('🔍 Existing slugs in episode:', existingSlugs);
  console.log('🔍 Checking slug:', slug.toLowerCase());

  return existingSlugs.includes(slug.toLowerCase());
}

// Get file extension from file object
function getFileExtension(file) {
  if (file.name) {
    const lastDot = file.name.lastIndexOf('.');
    return lastDot !== -1 ? file.name.slice(lastDot + 1).toLowerCase() : 'jpg';
  }
  // Fallback to MIME type
  const mimeType = file.type || 'image/jpeg';
  return mimeType.split('/')[1] || 'jpg';
}

// Handle IMG cue submission from modal
async function handleImgCueSubmit(imgCueData) {
  console.error('🚨🚨🚨 handleImgCueSubmit CALLED!!! 🚨🚨🚨');
  console.error('imgCueData:', imgCueData);
  try {
    console.log('🎬 Starting IMG cue submission workflow');
    console.log('🔍 Current item metadata:', props.currentItemMetadata);
    console.log('🔍 Current item AssetID:', props.currentItemMetadata?.AssetID);

    // Get parent AssetID from current rundown item
    let parentAssetId = props.currentItemMetadata?.AssetID;

    if (!parentAssetId) {
      console.warn('⚠️ No AssetID in currentItemMetadata, checking rundown items...');
      // Try to get from the current episode's rundown items
      if (currentItemId.value && rundownItems.value) { // eslint-disable-line no-undef
        const currentItem = rundownItems.value.find(item => item.id === currentItemId.value); // eslint-disable-line no-undef
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
    if (isSlugDuplicate(cueBlockSlug)) {
      throw new Error(`Slug "${cueBlockSlug}" already exists in this episode. Please use a unique slug.`);
    }

    // Slug for filename: lowercase + hyphens for spaces
    const filenameSlug = normalizeSlugForMedia(imgCueData.slug);
    const fileExtension = getFileExtension(imgCueData.imageFile);
    const newFilename = `${filenameSlug}.${fileExtension}`;

    // Get episode (required for upload)
    // Check if we have a temporary episode from callback first
    let episode = temporaryEpisode.value;
    if (episode) {
      console.log('✅ Using temporary episode from callback:', episode);
      temporaryEpisode.value = null; // Clear it
    } else {
      episode = requireEpisode(
        props.currentEpisode,
        'Upload Image',
        (selectedEpisode) => {
          // Callback: retry upload after episode selection
          console.log('📺 Episode selected, retrying IMG cue creation with:', selectedEpisode);
          // Store episode temporarily and retry
          temporaryEpisode.value = selectedEpisode;
          handleImgCueSubmit(imgCueData);
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
    pendingCueData.value = imgCueBlock;

    // Step 6: Handle insertion based on editor mode
    console.log('🎯 Step 6: Handling cue insertion for mode:', props.editorMode);
    console.log('🎯 editorMode type:', typeof props.editorMode);
    console.log('🎯 editorMode === "code":', props.editorMode === 'code');
    console.log('🎯 editorMode === "script":', props.editorMode === 'script');

    // CODE MODE: Insert directly at cursor position
    if (props.editorMode === 'code') {
      // Close the modal first for code mode
      showImgModal.value = false;
      console.log('📝 Code mode: Inserting at cursor position:', pendingCursorPosition.value);
      insertCueAtCursor(imgCueBlock);
      pendingCueData.value = null;
      pendingCursorPosition.value = null;
      pendingCueType.value = null;
      console.log('✅ IMG cue inserted in code mode');
      return;
    }

    // SCRIPT MODE: Insert based on selection (like SOT)
    console.log('📄 Script mode: Auto-inserting IMG based on selection');

    // Close the modal
    showImgModal.value = false;

    // Determine insertion point based on selection
    let insertionIndex;
    if (selectedSegmentIndex.value !== null && selectedSegmentIndex.value >= 0) {
      // Insert AFTER the selected segment (between zones)
      insertionIndex = selectedSegmentIndex.value + 1;
      console.log(`📍 Selected segment found at index ${selectedSegmentIndex.value}, inserting AFTER at between-zone ${insertionIndex}`);
    } else {
      // No selection - insert at bottom (after last paragraph)
      const paragraphCount = scriptSegments.value.filter(seg => seg.type === 'text').length;
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
    insertCueBetweenParagraphsInRawScript(placement, imgCueBlock);
    console.log('✅ IMG cue inserted at selected position in script mode');

    // Clear pending data
    pendingCueData.value = null;
    pendingCueType.value = null;

    console.log('IMG cue created:', imgCueData)
  } catch (error) {
    console.error('Error handling IMG cue submission:', error)
    // TODO: Show error message to user
  }
}

// Handle modal close events (including ESC key abort)
function handleImgModalClose(isVisible) {
  // When modal is closed (isVisible becomes false)
  if (!isVisible) {
    console.log('🎬🔥 IMG modal closed - EMERGENCY clearing ALL highlighting');

    // Force immediate cleanup of cursor position highlight
    console.log('🎯🔥 Force clearing cursor position highlight before anything else');
    clearCursorPositionHighlight();

    // Then clear insertion highlight (which should also call clearCursorPositionHighlight again)
    clearInsertionHighlight();

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
    cleanupCursorCharacters();
    // Clear pending data
    pendingCueType.value = null;
    pendingInsertionPoint.value = null;
    pendingCueData.value = null;
    editingCueData.value = null;

    console.log('🎬✅ Modal close cleanup COMPLETE');
  }
}

// Visual Script Mode Methods
// Single Source of Truth Editing Methods
function getSegmentContent(segmentIndex) {
  // CRITICAL FIX: If this segment is actively being edited, return the DOM's current innerHTML
  // This prevents Vue's v-html from overwriting content and resetting cursor position
  if (activelyEditingSegment.value === segmentIndex) {
    const refName = `textareaRef-${segmentIndex}`;
    const element = instance.proxy.$refs[refName];
    if (element && element.innerHTML !== undefined) {
      // Return the element's current innerHTML to prevent Vue from re-rendering it
      return element.innerHTML;
    }
  }

  // Return buffered content if it exists (user is actively editing)
  if (segmentEditBuffer && segmentEditBuffer[segmentIndex] !== undefined) {
    console.log('📝 getSegmentContent: returning BUFFERED content for segment', segmentIndex);
    // Strip trailing newlines and <br> to prevent blank lines at end of paragraph
    return segmentEditBuffer[segmentIndex]
      .replace(/(\s*<br\s*\/?\s*>\s*)+$/i, '')
      .replace(/\n+$/g, '');
  }

  // Otherwise return parsed content from single source of truth
  const segment = scriptSegments.value[segmentIndex];
  if (!segment) return '';
  // Strip trailing newlines and <br> from content before display
  let content = (segment.content || '')
    .replace(/(\s*<br\s*\/?\s*>\s*)+$/i, '')
    .replace(/\n+$/g, '');
  // Render <rev> tags as visual revision blocks in script mode
  content = renderRevisionTags(content);
  return content;
}

// Pattern source-of-truth: @/modules/legacyCueConvert/patterns.js
// (single import; matches both {SOT/foo} and (SOT/foo) variants).
function _invalidCuePatternRegex() {
  return LEGACY_CUE_REGEX
}

function hasInvalidCuePattern(segmentIndex) {
  // Skip check while user is actively editing this paragraph — contenteditable
  // produces transient <div> tags during rapid Enter presses that clear on their own
  if (isActivelyEditing.value && focusedParagraphIndex.value === segmentIndex) return false
  const segment = scriptSegments.value[segmentIndex]
  if (!segment || segment.type !== 'text') return false
  const content = segment.content || ''
  // Check for invalid cue patterns in plain text
  const plainText = content.replace(/<[^>]+>/g, '')
  if (_invalidCuePatternRegex().test(plainText)) return true
  // Strip contenteditable wrapper artifacts before checking for unwelcome HTML.
  // <div>, <p>, and <br> are browser-injected wrappers from Enter keystrokes,
  // not user-authored bad code. Matches the cleanup in handleContentEditableInput.
  const normalized = content
    .replace(/<\/?div\b[^>]*>/gi, '')
    .replace(/<\/?p\b[^>]*>/gi, '')
    .replace(/<br\s*\/?>/gi, '')
  // Check for unwelcome HTML tags inside the paragraph
  // Allowed: <b>, <i>, <u>, <em>, <strong>, <mark>, <sub>, <sup>
  const unwelcome = /<\/?(?:img|a|span|table|thead|tbody|tr|td|th|iframe|style|script|link|embed|object|svg|video|audio|source|picture|figure|figcaption|form|input|select|textarea|button|canvas|font|center|pre|code|blockquote|ol|ul|li|hr)\b[^>]*>/i
  return unwelcome.test(normalized)
}

// fixInvalidCuePattern — REMOVED. The inline overlay's "Fix" button
// now uses the LegacyCueConvertButton component (see template),
// which calls @/modules/legacyCueConvert/conversion.js — that flow
// preserves surrounding prose, generates an AssetID, finds + imports
// matching media, and produces a real cue block. The old behavior
// (delete the entire paragraph and pop a manual modal) is gone.

// updateTextSegment — core logic moved to useScriptCore composable
// This wrapper adds the persistCurrentItemToDatabase callback
function updateTextSegment(segmentIndex, newContent) {
  // Delegate to composable, providing the persist callback
  _scriptCoreUpdateTextSegment(segmentIndex, newContent, {
    onSaved: (idx) => persistCurrentItemToDatabase(idx)
  });
}

/**
 * Generic method to toggle formatting tags on selected text
 * @param {number} segmentIndex - Index of the segment being edited
 * @param {HTMLTextAreaElement} textarea - The textarea element
 * @param {string} openTag - Opening tag (e.g., '<strong>')
 * @param {string} closeTag - Closing tag (e.g., '</strong>')
 * @param {string} tagName - Tag name for logging (e.g., 'bold')
 */
function toggleSelectionFormatting(segmentIndex, textarea, openTag, closeTag, tagName) {
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
  updateTextSegment(segmentIndex, newContent);

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  console.log(`🎨 ${tagName} toggle complete`);
}

/**
 * Toggle bold (<strong>) on selected text - Ctrl+B
 */
function toggleBoldSelection(segmentIndex, textarea) {
  toggleSelectionFormatting(segmentIndex, textarea, '<strong>', '</strong>', 'bold');
}

/**
 * Toggle italic (<em>) on selected text - Ctrl+I
 */
function toggleItalicSelection(segmentIndex, textarea) {
  toggleSelectionFormatting(segmentIndex, textarea, '<em>', '</em>', 'italic');
}

/**
 * Toggle underline (<u>) on selected text - Ctrl+U
 */
function toggleUnderlineSelection(segmentIndex, textarea) {
  toggleSelectionFormatting(segmentIndex, textarea, '<u>', '</u>', 'underline');
}

/**
 * Toggle highlight (<mark>) on selected text in a textarea
 * Ctrl+H hotkey - wraps selection with <mark> tags or removes them if already highlighted
 */
function toggleHighlightSelection(segmentIndex, textarea) {
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
  updateTextSegment(segmentIndex, newContent);

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  console.log('🖍️ Highlight toggle complete');
}

// Handle keyboard events for Script mode behaviors that affect Code mode
function handleTextareaKeydown(segmentIndex, event) {
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
      blockReactiveUpdates.value = true;

      // Store the cleaned content (without trailing newline)
      const cleanedContent = currentContent.replace(/\n$/, '');

      // Clear any pending debounce for this segment
      if (updateDebounceTimers && updateDebounceTimers[segmentIndex]) {
        clearTimeout(updateDebounceTimers[segmentIndex]);
        delete updateDebounceTimers[segmentIndex];
      }
      if (segmentEditBuffer && segmentEditBuffer[segmentIndex]) {
        delete segmentEditBuffer[segmentIndex];
      }

      // Create new paragraph with cleaned content
      createNewParagraphAfter(segmentIndex, cleanedContent);

      // Clear the flag after a delay to allow the update and focus to complete
      // Must be long enough for focus retry logic (up to 10 attempts * 50ms = 500ms)
      setTimeout(() => {
        console.log('🎯 Clearing blockReactiveUpdates flag');
        blockReactiveUpdates.value = false;
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
      mergeParagraphWithPrevious(segmentIndex);
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
        mergeParagraphWithNext(segmentIndex);
      }, 0);
    }
  }

  // Ctrl+B: Toggle bold on selected text
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'b') {
    event.preventDefault();
    toggleBoldSelection(segmentIndex, event.target);
    return;
  }

  // Ctrl+I: Toggle italic on selected text
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'i') {
    event.preventDefault();
    toggleItalicSelection(segmentIndex, event.target);
    return;
  }

  // Ctrl+U: Toggle underline on selected text
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'u') {
    event.preventDefault();
    toggleUnderlineSelection(segmentIndex, event.target);
    return;
  }

  // Ctrl+S: Save all
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 's') {
    event.preventDefault();
    handleSaveAll();
    return;
  }

  // Ctrl+Alt+H: Toggle highlight on selected text
  if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'h') {
    event.preventDefault();
    toggleHighlightSelection(segmentIndex, event.target);
  }

  // Alt+/: Propose revision on selected text (code mode)
  if (event.altKey && !event.ctrlKey && !event.shiftKey && event.key === '/') {
    event.preventDefault();
    toggleRevisionSelection(segmentIndex, event.target);
    return;
  }

  // Alt+.: Insert addition tag at cursor (code mode)
  if (event.altKey && !event.ctrlKey && !event.shiftKey && event.key === '.') {
    event.preventDefault();
    insertAdditionTag(segmentIndex, event.target);
    return;
  }
}

// Script Mode Behavior: Create new <p> tag in Code mode
function createNewParagraphAfter(segmentIndex, cleanedContentForCurrentSegment = null) {
  console.log('📝📝📝 ========== CREATE NEW PARAGRAPH ==========');
  console.log('📝 Creating new paragraph after segment:', segmentIndex);
  console.log('📝 Current segments count:', scriptSegments.value?.length);
  console.log('📝 cleanedContentForCurrentSegment:', cleanedContentForCurrentSegment);

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  const segments = [...scriptSegments.value];
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
  pendingFocusSegmentIndex.value = segmentIndex + 1;
  console.log('📝📝📝 Set pendingFocusSegmentIndex to:', pendingFocusSegmentIndex.value);

  // Reconstruct raw content - this will create the new <p> tag in Code mode
  const newRawContent = reconstructRawContent(segments);
  console.log('📝 Reconstructed content length:', newRawContent.length);
  console.log('📝 Reconstructed content preview:', newRawContent.substring(0, 300));

  console.log('📝 Emitting update:scriptContent to parent...');
  emit('update:scriptContent', newRawContent);
  console.log('📝📝📝 ========== EMIT COMPLETE ==========');

  // Focus logic is now handled by scriptSegments watcher
  // which will focus pendingFocusSegmentIndex after Vue finishes re-rendering
}

// Create new paragraph after current one with specific content (for splitting)
// currentSegmentContent: optional - if provided, update current segment's content too (for mid-paragraph splits)
function createNewParagraphAfterWithContent(segmentIndex, newParagraphContent, currentSegmentContent = null) {
  console.log('📝📝📝 ========== CREATE NEW PARAGRAPH WITH CONTENT ==========');
  console.log('📝 Creating new paragraph after segment:', segmentIndex);
  console.log('📝 New paragraph content:', newParagraphContent);
  if (currentSegmentContent !== null) {
    console.log('📝 Updating current segment content to:', currentSegmentContent);
  }

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  const segments = [...scriptSegments.value];
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
  pendingFocusSegmentIndex.value = segmentIndex + 1;
  console.log('📝📝📝 Set pendingFocusSegmentIndex to:', pendingFocusSegmentIndex.value);

  // Reconstruct raw content
  const newRawContent = reconstructRawContent(segments);
  console.log('📝 Reconstructed content length:', newRawContent.length);

  console.log('📝 Emitting update:scriptContent to parent...');
  emit('update:scriptContent', newRawContent);
  console.log('📝📝📝 ========== EMIT COMPLETE ==========');
}

// Create initial paragraph for empty content
function createInitialParagraph() {
  console.log('🔧 createInitialParagraph called');

  // Check if content already has <p> tags
  const contentWithoutFrontmatter = stripYamlFrontmatter(rawScriptContent.value);
  if (contentWithoutFrontmatter && contentWithoutFrontmatter.includes('<p')) {
    console.log('❌ Content already has <p> tags, skipping');
    return; // Already has paragraph tags
  }

  console.log('✅ Creating initial paragraph');

  // Extract existing frontmatter (if any)
  const frontmatterMatch = rawScriptContent.value.match(/^(---\n[\s\S]*?\n---\n)/);
  const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';

  // Preserve any existing content after frontmatter (like ## Notes, ## Description, ## Script)
  const existingContent = contentWithoutFrontmatter || '';

  // Create initial empty paragraph after existing content
  const initialContent = frontmatter + existingContent + '\n<p class="josh"></p>\n';

  console.log('📝 Setting rawScriptContent with initial paragraph (triggers setter emit)');
  rawScriptContent.value = initialContent;

  // Note: Focus happens in scriptSegments watcher after content is rendered
}

// Script Mode Behavior: Merge paragraph with previous (Backspace at start)
function mergeParagraphWithPrevious(segmentIndex) {
  if (segmentIndex === 0) return; // Can't merge first paragraph

  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  const segments = [...scriptSegments.value];
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
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);

  // Focus previous paragraph at merge point
  nextTick(() => {
    const textareaRef = instance.proxy.$refs[`textareaRef-${segmentIndex - 1}`];
    const textarea = textareaRef?.[0]?.$el?.querySelector('textarea');
    if (textarea) {
      textarea.focus();
      textarea.setSelectionRange(cursorPosition, cursorPosition);
    }
  });
}

// Script Mode Behavior: Merge with next paragraph (Delete at end)
function mergeParagraphWithNext(segmentIndex) {
  // Mark as having unsaved changes
  hasLocalUnsavedChanges.value = true;

  const segments = [...scriptSegments.value];
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
  const newRawContent = reconstructRawContent(segments);
  emit('update:scriptContent', newRawContent);
}

// reconstructRawContent — moved to useScriptCore composable

function reconstructScriptContent(segments) {
  return CueParser.reconstructContent(segments);
}

function formatCueToMarkdown(cueData) {
  if (!cueData) return '';

  let cueBlock = '<!-- Begin Cue -->\n';

  // Add all fields from the original cue data
  Object.keys(cueData).forEach(key => {
    if (key !== 'imageTag' && key !== 'imageSrc' && cueData[key]) {
      const displayKey = formatFieldForDisplay(key);
      cueBlock += `[${displayKey}: ${cueData[key]}]\n`;
    }
  });

  // Add image tag if it exists
  if (cueData.imageTag) {
    cueBlock += `${cueData.imageTag}\n`;
  }

  cueBlock += '<!-- End Cue -->';
  return cueBlock;
}

function formatFieldForDisplay(camelCaseField) {
  // Convert camelCase back to Title Case for display
  return camelCaseField
    .replace(/([A-Z])/g, ' $1')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function selectCue(index) {
  selectedCueIndex.value = index;
}

function editCue(index, cueData) {
  console.log('Edit cue at index:', index, cueData);
  // Open appropriate modal based on cue type - emit to parent for all
  if (cueData.type === 'IMG') {
    // Emit event to parent (ContentEditor) to open IMG modal with cue data
    emit('edit-img-cue', cueData);
  } else if (cueData.type === 'SOT') {
    // Emit event to parent (ContentEditor) to open SOT modal with cue data
    emit('edit-sot-cue', cueData);
  } else if (cueData.type === 'FSQ') {
    // Emit event to parent (ContentEditor) to open FSQ modal with cue data
    emit('edit-fsq-cue', cueData);
  } else if (cueData.type === 'GFX') {
    // Emit event to parent (ContentEditor) to open GFX modal with cue data
    emit('edit-gfx-cue', cueData);
  } else if (cueData.type === 'DIR' || cueData.type === 'NOTE') {
    // Emit event to parent (ContentEditor) to open NOTE modal with cue data
    emit('edit-dir-cue', cueData);
  } else if (cueData.type === 'RIF') {
    // Emit event to parent (ContentEditor) to open RIF modal with cue data
    emit('edit-rif-cue', cueData);
  }
}

/**
 * Handle re-upload request for SOT cue
 * Opens SotModal with existing metadata but requires new video upload
 */
function handleReuploadSotCue(reuploadData) {
  console.log('📤 Re-upload SOT cue requested:', reuploadData);
  // Emit to parent (ContentEditor) which will open SotModal with pre-filled data
  emit('reupload-sot-cue', reuploadData);
}

function handleRelocateCue(segmentIndex) {
  const segment = draggableSegments.value?.[segmentIndex];
  if (!segment) return;
  const markdown = segmentToMarkdown(segment);
  emit('relocate-cue', { segmentIndex, markdown, type: segment.type });
}

/**
 * Handle FSQ edit request from PlaceholderCueCard
 * Emits to parent (ContentEditor) which will open FsqModal in edit mode
 */
function handleEditFsq(cueData) {
  console.log('📝 Edit FSQ cue requested:', cueData);
  emit('edit-fsq-cue', cueData);
}

function handleEditGfx(cueData) {
  console.log('📝 Edit GFX cue requested:', cueData);
  emit('edit-gfx-cue', cueData);
}

/**
 * Handle SOT job status change (especially completion)
 * Emits to ContentEditor to trigger content refresh
 */
function handleSotStatusChange({ status, assetId }) {
  console.log(`📊 SOT job status changed: ${assetId} → ${status}`);
  if (status === 'completed') {
    console.log('✅ SOT job completed - requesting content refresh');
    emit('sot-job-complete', { assetId });
  }
}

function handleMetaUpdate({ cueData, metadata }) {
  console.log('Meta update received:', metadata);

  // Find the cue segment in scriptSegments
  const segmentIndex = scriptSegments.value.findIndex(segment =>
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
  scriptSegments.value[segmentIndex].data = updatedCueData;
  scriptSegments.value[segmentIndex].rawContent = updatedCueLine;

  // Reconstruct raw content
  const newRawContent = reconstructRawContent(scriptSegments.value);
  emit('update:scriptContent', newRawContent);

  console.log('Meta updated successfully');
}

/**
 * Handle cue field update from PlaceholderCueCard
 * Format: { assetId, field, value }
 * Used for updating individual fields like mediaUrl after FSQ generation
 */
function handleCueFieldUpdate({ assetId, field, value }) {
  console.log(`📝 handleCueFieldUpdate: assetId=${assetId}, field=${field}, value=${value}`);

  // Find the cue segment by assetId
  const segmentIndex = scriptSegments.value.findIndex(segment =>
    segment.type === 'cue' &&
    (segment.data?.assetId === assetId || segment.data?.rawData?.assetId === assetId)
  );

  if (segmentIndex === -1) {
    console.error('❌ Could not find cue segment with assetId:', assetId);
    return;
  }

  const segment = scriptSegments.value[segmentIndex];
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
  scriptSegments.value.splice(segmentIndex, 1, {
    ...segment,
    data: updatedData,
    rawContent: updatedCueBlock
  });

  // Reconstruct and emit the updated script content
  const newRawContent = reconstructRawContent(scriptSegments.value);
  emit('update:scriptContent', newRawContent);

  console.log(`✅ Cue field '${field}' updated successfully for assetId: ${assetId}`);
}

/**
 * Apply a single FSQ style parameter to every FSQ cue in the episode.
 * Payload: { param: 'fontSize', value: 34 }
 */
function handleApplyAllFsq({ param, value }) {
  console.log(`🎨 Apply All FSQ: ${param} = ${value}`);

  let updateCount = 0;

  for (let i = 0; i < scriptSegments.value.length; i++) {
    const segment = scriptSegments.value[i];
    if (segment.type !== 'cue' || segment.data?.type !== 'FSQ') continue;

    const updatedData = { ...segment.data };
    const updatedRawData = { ...segment.data.rawData };

    updatedData[param] = value;
    updatedRawData[param] = value;
    updatedData.rawData = updatedRawData;

    const updatedCueBlock = CueParser.formatCueToMarkdown(updatedRawData);

    scriptSegments.value.splice(i, 1, {
      ...segment,
      data: updatedData,
      rawContent: updatedCueBlock
    });

    updateCount++;
  }

  if (updateCount > 0) {
    const newRawContent = reconstructRawContent(scriptSegments.value);
    emit('update:scriptContent', newRawContent);
    console.log(`✅ Applied ${param}=${value} to ${updateCount} FSQ cue(s)`);
  } else {
    console.log('⚠️ No FSQ cues found to update');
  }
}

function deleteCue(index) {
  const segment = scriptSegments.value[index];

  // If it's an IMG cue, show IMG-specific confirmation modal
  if (segment?.type === 'cue' && segment.data?.type === 'IMG') {
    deletingCueData.value = segment.data;
    deletingCueIndex.value = index;
    showDeleteImgModal.value = true;
    return;
  }

  // For all other cue types, show generic confirmation
  deletingCueData.value = segment?.data || null;
  deletingCueIndex.value = index;
  showDeleteCueConfirm.value = true;
}

function confirmDeleteCue() {
  if (deletingCueIndex.value != null) {
    performCueDeletion(deletingCueIndex.value, false);
  }
  showDeleteCueConfirm.value = false;
  deletingCueData.value = null;
  deletingCueIndex.value = null;
}

function cancelDeleteCue() {
  showDeleteCueConfirm.value = false;
  deletingCueData.value = null;
  deletingCueIndex.value = null;
}

function performCueDeletion(index, deleteAssets = false) {
  console.log('🗑️ performCueDeletion called for segment index:', index);

  // STRATEGY: Direct raw content manipulation.
  // Instead of parse → filter → reconstruct (which has caching edge cases),
  // identify which cue block in the raw content corresponds to this segment index,
  // then remove it directly from the string.

  // Step 1: Get the raw content
  const rawContent = props.scriptContent || '';
  console.log('🗑️ Raw content length before deletion:', rawContent.length);

  // Step 2: Find all cue block positions in the raw content.
  // CRITICAL: do NOT use a lazy regex like /<!-- Begin Cue -->[\s\S]*?<!-- End Cue -->/g.
  // If a cue is missing its End marker (common in pasted Google Docs imports), the lazy
  // match jumps forward to the *next* cue's End marker and silently consumes everything
  // in between. A subsequent X-click then deletes that giant span — wiping the document.
  // Instead, scan imperatively and reject any Begin without a matching End before the
  // next Begin. Malformed cues are flagged and skipped (length 0), keeping indices
  // aligned with what CueParser produces.
  const BEGIN = '<!-- Begin Cue -->';
  const END = '<!-- End Cue -->';
  const cuePositions = []; // { start, end, malformed }
  {
    let i = 0;
    while (i < rawContent.length) {
      const beginIdx = rawContent.indexOf(BEGIN, i);
      if (beginIdx === -1) break;
      const endIdx = rawContent.indexOf(END, beginIdx + BEGIN.length);
      const nextBeginIdx = rawContent.indexOf(BEGIN, beginIdx + BEGIN.length);
      if (endIdx === -1 || (nextBeginIdx !== -1 && nextBeginIdx < endIdx)) {
        cuePositions.push({ start: beginIdx, end: beginIdx + BEGIN.length, malformed: true });
        i = beginIdx + BEGIN.length;
      } else {
        cuePositions.push({ start: beginIdx, end: endIdx + END.length, malformed: false });
        i = endIdx + END.length;
      }
    }
  }
  const validCuePositions = cuePositions.filter(p => !p.malformed);

  // Step 3: Map segment index to cue occurrence index.
  // scriptSegments interleaves text and cue segments. We need to count
  // how many cue segments appear before (and including) the target index.
  // Clear caches first so scriptSegments returns fresh data.
  isActivelyEditing.value = false;
  activelyEditingSegment.value = null;
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;

  const segments = scriptSegments.value;
  const targetSegment = segments[index];

  if (!targetSegment || targetSegment.type !== 'cue') {
    console.error('🗑️ Target segment is not a cue:', targetSegment);
    return;
  }

  // Count which cue occurrence this is (0-based)
  let cueOccurrence = 0;
  for (let i = 0; i < index; i++) {
    if (segments[i]?.type === 'cue') {
      cueOccurrence++;
    }
  }

  console.log('🗑️ Target is cue occurrence #' + cueOccurrence + ' of ' + validCuePositions.length + ' valid cues (raw scan saw ' + cuePositions.length + ' Begin markers, ' + (cuePositions.length - validCuePositions.length) + ' malformed)');

  if (cueOccurrence >= validCuePositions.length) {
    console.error('🗑️ Cue occurrence index out of range');
    return;
  }

  // Step 4: Remove the cue block from raw content (plus surrounding whitespace)
  const { start, end } = validCuePositions[cueOccurrence];

  // SANITY GUARD: refuse to delete if the span is suspiciously large.
  // A real cue block is rarely > 8000 chars. If we're about to remove much more than
  // that, the position scan is wrong and we should abort rather than wipe the document.
  const spanLen = end - start;
  if (spanLen > 16000) {
    console.error('🗑️ ABORTING delete: cue span too large (' + spanLen + ' chars). Refusing to delete to protect document. This usually means a malformed cue earlier in the document — open Code Mode to repair.');
    if (typeof window !== 'undefined' && window.alert) {
      window.alert('Refusing to delete: this cue spans ' + spanLen + ' characters, which suggests a malformed cue elsewhere in the document. Open Code Mode to repair the cue markers.');
    }
    return;
  }

  // Also trim surrounding blank lines to avoid double-spacing
  let removeStart = start;
  let removeEnd = end;

  // Expand to consume preceding newlines
  while (removeStart > 0 && rawContent[removeStart - 1] === '\n') {
    removeStart--;
  }
  // Expand to consume following newlines
  while (removeEnd < rawContent.length && rawContent[removeEnd] === '\n') {
    removeEnd++;
  }

  const newRawContent = rawContent.substring(0, removeStart) +
    (removeStart > 0 && removeEnd < rawContent.length ? '\n\n' : '') +
    rawContent.substring(removeEnd);

  console.log('🗑️ Raw content length after deletion:', newRawContent.length);
  console.log('🗑️ Removed chars:', rawContent.length - newRawContent.length);

  // Step 5: Clear all caches and emit
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
  clearEditBuffer();
  emit('update:scriptContent', newRawContent);

  // Clear selection if the deleted cue was selected
  if (selectedCueIndex.value === index) {
    selectedCueIndex.value = null;
  }

  // CRITICAL: Save immediately after cue deletion — do not rely on the 2s debounce.
  // If the user switches items before the debounce fires, the deletion is lost
  // because the remote sync or item reload will overwrite with stale DB content.
  nextTick(() => {
    emit('save');
  });

  // TODO: If deleteAssets is true, also delete the media file via API
  if (deleteAssets && deletingCueData.value?.rawData?.mediaurl) {
    console.log('Would delete media file:', deletingCueData.value.rawData.mediaurl);
  }
}

function handleDeleteWithAssets() {
  if (deletingCueIndex.value !== null) {
    performCueDeletion(deletingCueIndex.value, true);
    deletingCueData.value = null;
    deletingCueIndex.value = null;
  }
}

function handleDeletePreserveAssets() {
  if (deletingCueIndex.value !== null) {
    performCueDeletion(deletingCueIndex.value, false);
    deletingCueData.value = null;
    deletingCueIndex.value = null;
  }
}

/**
 * Apply analysis recommendations to a cue
 * Handles actions like splitting FSQ quotes, cleaning SOT transcripts, etc.
 *
 * @param {string} assetId - Cue AssetID
 * @param {string} analysisId - Analysis ID from cueAnalysisStore
 */
async function applyAnalysisRecommendations(assetId, analysisId) {
  const { getRecommendations, markReviewed } = useAsyncAnalysis();
  const recommendations = getRecommendations(analysisId);

  if (!recommendations) {
    console.warn('No recommendations found for analysis:', analysisId);
    return;
  }

  console.log(`📋 Applying recommendations for ${assetId}:`, recommendations);

  // Find the cue in scriptSegments
  const cueIndex = scriptSegments.value.findIndex(
    segment => segment.type === 'cue' && segment.data?.assetId === assetId
  );

  if (cueIndex === -1) {
    console.error('Cue not found in script segments:', assetId);
    return;
  }

  const cueSegment = scriptSegments.value[cueIndex];
  const cueData = cueSegment.data;

  // Handle FSQ split recommendations
  if (recommendations.shouldSplit && recommendations.splitRecommendations) {
    console.log(`✂️ Splitting FSQ quote into ${recommendations.splitRecommendations.length} parts`);

    // Delete original cue
    const updatedSegments = [...scriptSegments.value];
    updatedSegments.splice(cueIndex, 1);

    // Insert split cues at the same position
    const splitCues = [];
    for (let i = 0; i < recommendations.splitRecommendations.length; i++) {
      const splitQuote = recommendations.splitRecommendations[i];

      // Generate AssetID for each split
      const splitAssetId = await generateAssetId();

      // Word count for duration calculation
      const wordCount = splitQuote.trim().split(/\s+/).filter(w => w.length > 0).length;
      const speakerWpm = props.item?.speaker_wpm || 150;
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
      const cueBlock = formatCueBlock(splitCueData);
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
    const newRawContent = reconstructRawContent(updatedSegments);
    emit('update:scriptContent', newRawContent);

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
    const updatedSegments = [...scriptSegments.value];
    updatedSegments[cueIndex] = {
      type: 'cue',
      cueType: cueData.type,
      data: {
        ...cueData,
        rawData: modifiedCueData
      }
    };

    // Update script content
    const newRawContent = reconstructRawContent(updatedSegments);
    emit('update:scriptContent', newRawContent);

    console.log('✅ Applied modifications to cue');
  }

  // Mark analysis as reviewed
  markReviewed(analysisId);
  console.log('✅ Analysis marked as reviewed:', analysisId);
}

/**
 * Format cue data to markdown cue block
 * @param {object} cueData - Cue data to format
 * @returns {string} Formatted cue block
 */
function formatCueBlock(cueData) {
  let cueBlock = '<!-- Begin Cue -->\n';

  Object.keys(cueData).forEach(key => {
    if (cueData[key]) {
      const displayKey = key.charAt(0).toUpperCase() + key.slice(1);
      cueBlock += `[${displayKey}: ${cueData[key]}]\n`;
    }
  });

  cueBlock += '<!-- End Cue -->';
  return cueBlock;
}

function extractOrderFromSlug(slug) {
  if (!slug) return null;

  // Extract number from slug like "20 kam-kam-harris" -> "20"
  const match = slug.match(/^(\d+)\s/);
  return match ? match[1] : null;
}

// Speaker-related methods
function selectSegment(index) {
  selectedSegmentIndex.value = index;
  selectedCueIndex.value = null; // Clear cue selection
}

function deleteSegment(index) {
  console.log('🗑️ Delete segment called with index:', index);

  // Route cue segments through performCueDeletion (direct raw content removal)
  // This avoids the parse→filter→reconstruct cycle which has caching edge cases
  isActivelyEditing.value = false;
  activelyEditingSegment.value = null;
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;

  const segments = scriptSegments.value;
  const targetSegment = segments[index];

  if (targetSegment?.type === 'cue') {
    console.log('🗑️ Routing cue deletion through performCueDeletion');
    hasLocalUnsavedChanges.value = true;
    performCueDeletion(index, false);
    if (selectedSegmentIndex.value === index) selectedSegmentIndex.value = null;
    multiSelectedSegments.value.delete(index);
    return;
  }

  console.log('🗑️ Total segments before:', segments.length);
  hasLocalUnsavedChanges.value = true;

  // For text segments, use the filter→reconstruct approach (works reliably for text)
  const updatedSegments = segments.filter((_, i) => i !== index);
  console.log('🗑️ Total segments after filter:', updatedSegments.length);
  const newScriptContent = reconstructScriptContentWithFrontmatter(updatedSegments);
  console.log('🗑️ New script content length:', newScriptContent.length);

  // Clear all caches before emitting
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
  clearEditBuffer();
  emit('update:scriptContent', newScriptContent);
  console.log('🗑️ Emitted update:scriptContent');

  if (selectedSegmentIndex.value === index) {
    selectedSegmentIndex.value = null;
  }
  multiSelectedSegments.value.delete(index);
}

function openSpeakerSelector(segmentIndex) {
  editingSpeakerSegmentIndex.value = segmentIndex;
  const segment = scriptSegments.value[segmentIndex];
  currentSegmentSpeaker.value = segment.speaker || 'josh';
  showSpeakerSelector.value = true;
}

function toggleMultiSelection(index) {
  console.log('Toggle multi-selection for index:', index);
  if (multiSelectedSegments.value.has(index)) {
    multiSelectedSegments.value.delete(index);
  } else {
    multiSelectedSegments.value.add(index);
  }
  console.log('Multi-selected segments:', Array.from(multiSelectedSegments.value));
}

/**
 * Select all segments in a range (inclusive). Used for Shift+Click.
 * Replaces current selection with the contiguous block from anchor to target.
 */
function _selectRange(anchorIndex, targetIndex) {
  const start = Math.min(anchorIndex, targetIndex);
  const end = Math.max(anchorIndex, targetIndex);
  multiSelectedSegments.value.clear();
  for (let i = start; i <= end; i++) {
    multiSelectedSegments.value.add(i);
  }
  console.log(`📦 Range selected: ${start}–${end} (${end - start + 1} segments)`);
}

function deleteMultipleSegments() {
  console.log('🗑️ Bulk delete called for segments:', Array.from(multiSelectedSegments.value));
  // Sort indices in descending order to delete from end to start (preserves indices)
  const sortedIndices = Array.from(multiSelectedSegments.value).sort((a, b) => b - a);
  console.log('🗑️ Deleting in order:', sortedIndices);

  let updatedSegments = [...scriptSegments.value];

  // Remove segments from end to start
  sortedIndices.forEach(index => {
    updatedSegments.splice(index, 1);
  });

  console.log('🗑️ Segments remaining after bulk delete:', updatedSegments.length);
  const newRawContent = reconstructRawContent(updatedSegments);
  emit('update:scriptContent', newRawContent);

  // Clear all selections
  clearMultiSelection();
  selectedSegmentIndex.value = null;
}

function swapSelectedParagraphs() {
  console.log('🔄 Swap called for segments:', Array.from(multiSelectedSegments.value));

  // Check if exactly 2 segments are selected
  if (multiSelectedSegments.value.size !== 2) {
    swapErrorMessage.value = `Swap requires exactly 2 selected paragraphs. Currently ${multiSelectedSegments.value.size} selected.`;
    showSwapErrorDialog.value = true;
    return;
  }

  // Get the two indices and sort them
  const indices = Array.from(multiSelectedSegments.value).sort((a, b) => a - b);
  const [index1, index2] = indices;

  console.log(`🔄 Swapping segments at indices ${index1} and ${index2}`);

  let updatedSegments = [...scriptSegments.value];

  // Swap the segments
  [updatedSegments[index1], updatedSegments[index2]] = [updatedSegments[index2], updatedSegments[index1]];

  console.log('🔄 Segments swapped, reconstructing content');

  // Update content
  const newRawContent = reconstructRawContent(updatedSegments);
  emit('update:scriptContent', newRawContent);

  // Clear selection
  clearMultiSelection();

  // Add blink effect to the swapped paragraphs
  nextTick(() => {
    blinkingParagraphs.value.add(index1);
    blinkingParagraphs.value.add(index2);

    // Remove blink effect after animation completes (5 blinks at 0.3s each = 1.5s)
    setTimeout(() => {
      blinkingParagraphs.value.delete(index1);
      blinkingParagraphs.value.delete(index2);
    }, 1500);
  });
}

function joinSelectedParagraphs() {
  console.log('🔗 Join called for segments:', Array.from(multiSelectedSegments.value));

  if (multiSelectedSegments.value.size < 2) {
    return;
  }

  // Sort indices ascending so we join in document order
  const sortedIndices = Array.from(multiSelectedSegments.value).sort((a, b) => a - b);
  const keepIndex = sortedIndices[0];

  let updatedSegments = [...scriptSegments.value];

  // Collect content from all selected segments in order
  const joinedContent = sortedIndices
    .map(i => (updatedSegments[i].content || '').trim())
    .filter(c => c.length > 0)
    .join(' ');

  // Set the first segment's content to the joined text
  updatedSegments[keepIndex] = {
    ...updatedSegments[keepIndex],
    content: joinedContent
  };

  // Remove the other segments from end to start (preserves indices)
  for (let i = sortedIndices.length - 1; i >= 1; i--) {
    updatedSegments.splice(sortedIndices[i], 1);
  }

  console.log('🔗 Joined into segment at index', keepIndex, '- segments remaining:', updatedSegments.length);

  const newRawContent = reconstructRawContent(updatedSegments);
  emit('update:scriptContent', newRawContent);

  // Clear selection
  clearMultiSelection();
  selectedSegmentIndex.value = null;

  // Add blink effect on the joined paragraph
  nextTick(() => {
    blinkingParagraphs.value.add(keepIndex);
    setTimeout(() => {
      blinkingParagraphs.value.delete(keepIndex);
    }, 1500);
  });
}

function clearMultiSelection() {
  console.log('🔄 Clearing multi-selection');
  multiSelectedSegments.value.clear();
  lastMultiSelectAnchor.value = null;
}

function handleCuePlacement(placement) {
  console.log('📍 Cue placement selected:', placement);
  console.log('📍 placement.cueType:', placement.cueType);
  console.log('📍 pendingCueData.value exists:', !!pendingCueData.value);
  console.log('📍 pendingCueType.value:', pendingCueType.value);

  pendingPlacement.value = placement;
  showCuePlacement.value = false;

  // Handle different cue types that come from modals with pre-generated data
  if (placement.cueType === 'IMG' || placement.cueType === 'FSQ' || placement.cueType === 'SOT') {
    console.log(`📍 ${placement.cueType} cue type detected`);
    if (pendingCueData.value) {
      // Check if pendingCueData is an array (multipart FSQ)
      if (Array.isArray(pendingCueData.value)) {
        console.log(`✅ Using pendingCueData array for ${placement.cueType} insertion (${pendingCueData.value.length} parts)`);
        // Insert each part sequentially at the same location
        pendingCueData.value.forEach((cueBlock, index) => {
          console.log(`📍 Inserting part ${index + 1}/${pendingCueData.value.length}`);
          insertCueAtPlacement(placement, cueBlock);
        });
      } else {
        console.log(`✅ Using pendingCueData for ${placement.cueType} insertion`);
        console.log('📍 pendingCueData preview:', pendingCueData.value.substring(0, 200));
        // We already have cue data from modal, insert it
        insertCueAtPlacement(placement, pendingCueData.value);
      }
      pendingCueData.value = null;
      pendingPlacement.value = null;
      pendingCueType.value = null;
    } else {
      console.warn(`⚠️ No pendingCueData found - opening ${placement.cueType} modal`);
      // No cue data yet, show modal first
      if (placement.cueType === 'IMG') {
        emit('show-img-modal');
      } else if (placement.cueType === 'FSQ') {
        emit('show-fsq-modal');
      } else if (placement.cueType === 'SOT') {
        emit('show-sot-modal');
      }
    }
  } else {
    console.log('📍 Non-IMG/FSQ/SOT cue type, generating cue block');
    // For other cue types, generate standard cue block and insert directly
    const cueContent = generateCueBlock(placement.cueType);
    insertCueAtPlacement(placement, cueContent);

    // Clear pending data
    pendingPlacement.value = null;
    pendingCueType.value = null;
  }
}

function cancelCuePlacement() {
  console.log('❌ Cue placement cancelled - clearing all pending data');
  showCuePlacement.value = false;
  pendingCueType.value = null;
  pendingPlacement.value = null;
  pendingCueData.value = null;
  pendingInsertionPoint.value = null;
  pendingCursorPosition.value = null;
  pendingCueInsertionIndex.value = null;
  console.log('✅ Drop locator terminated for this rundown/user');
}

async function handleSotCueSubmit(sotCueText) {
  console.log('🎬 SOT cue submitted to EditorPanel for placement-based insertion');

  // Store the cue data for later insertion
  pendingCueData.value = sotCueText;
  pendingCueType.value = 'SOT';

  // CODE MODE: Insert directly at cursor position
  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting SOT at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time, not stale position from button click
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      // Only use current cursor if textarea is still focused
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      // Textarea not focused (user clicked in modal) - insert at end
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(sotCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ SOT cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting SOT using snapshotted position');
  insertCueAtSnapshotPosition(sotCueText);

  // Clear pending data
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ SOT cue auto-inserted in script mode')
}

async function handleVoCueSubmit(voCueText) {
  console.log('🎬 VO cue submitted to EditorPanel for placement-based insertion');

  pendingCueData.value = voCueText;
  pendingCueType.value = 'VO';

  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting VO at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(voCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ VO cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting VO using snapshotted position');
  insertCueAtSnapshotPosition(voCueText);

  // Clear pending data
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ VO cue auto-inserted in script mode');
}

async function handleNatCueSubmit(natCueText) {
  console.log('🎬 NAT cue submitted to EditorPanel for placement-based insertion');

  pendingCueData.value = natCueText;
  pendingCueType.value = 'NAT';

  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting NAT at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(natCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ NAT cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting NAT using snapshotted position');
  insertCueAtSnapshotPosition(natCueText);

  // Clear pending data
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ NAT cue auto-inserted in script mode');
}

async function handleRifCueSubmit(rifCueText) {
  console.log('🎬 RIF cue submitted to EditorPanel for placement-based insertion');

  // Store the cue data for later insertion
  pendingCueData.value = rifCueText;
  pendingCueType.value = 'RIF';

  // CODE MODE: Insert directly at cursor position
  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting RIF at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(rifCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ RIF cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting RIF using snapshotted position');
  insertCueAtSnapshotPosition(rifCueText);

  // Clear pending data
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ RIF cue auto-inserted in script mode');
}

async function handlePkgCueSubmit(pkgCueText) {
  console.log('🎬 PKG cue submitted to EditorPanel for insertion');

  pendingCueData.value = pkgCueText;
  pendingCueType.value = 'PKG';

  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting PKG at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(pkgCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ PKG cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting PKG using snapshotted position');
  insertCueAtSnapshotPosition(pkgCueText);
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ PKG cue auto-inserted in script mode');
}

async function handleDirCueSubmit(dirCueText) {
  console.log('🎬 NOTE cue submitted to EditorPanel for insertion');

  pendingCueData.value = dirCueText;
  pendingCueType.value = 'NOTE';

  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting NOTE at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(dirCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ NOTE cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting NOTE using snapshotted position');
  insertCueAtSnapshotPosition(dirCueText);
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ NOTE cue auto-inserted in script mode');
}

async function handleBumpCueSubmit(bumpCueText) {
  console.log('🎬 BUMP cue submitted to EditorPanel for insertion');

  pendingCueData.value = bumpCueText;
  pendingCueType.value = 'BUMP';

  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting BUMP at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(bumpCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ BUMP cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting BUMP using snapshotted position');
  insertCueAtSnapshotPosition(bumpCueText);
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ BUMP cue auto-inserted in script mode');
}

async function handleStingCueSubmit(stingCueText) {
  console.log('🎬 STING cue submitted to EditorPanel for insertion');

  pendingCueData.value = stingCueText;
  pendingCueType.value = 'STING';

  if (props.editorMode === 'code') {
    console.log('📝 Code mode: Inserting STING at cursor position');

    // CRITICAL FIX: Get FRESH cursor position at submission time
    const codeTextarea = document.querySelector('.code-textarea textarea');
    if (codeTextarea && document.activeElement === codeTextarea) {
      pendingCursorPosition.value = codeTextarea.selectionStart;
      console.log('📝 Using current cursor position:', pendingCursorPosition.value);
    } else {
      pendingCursorPosition.value = null;
      console.log('📝 Textarea not focused - inserting at end');
    }

    insertCueAtCursor(stingCueText);
    pendingCueData.value = null;
    pendingCueType.value = null;
    console.log('✅ STING cue inserted in code mode');
    return;
  }

  // SCRIPT MODE: Auto-insert using snapshotted position
  console.log('📄 Script mode: Auto-inserting STING using snapshotted position');
  insertCueAtSnapshotPosition(stingCueText);
  pendingCueData.value = null;
  pendingCueType.value = null;
  console.log('✅ STING cue auto-inserted in script mode');
}

function generateCueBlock(cueType) {
  console.log('🏗️ Generating cue block for type:', cueType);

  // Generate unique asset ID for cues that need it
  const assetId = generateAssetId();

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
}

function generateAssetId() {
  // Simple asset ID generation - could be enhanced with proper ID generation logic
  return 'AST' + Date.now().toString().slice(-8) + Math.floor(Math.random() * 100).toString().padStart(2, '0');
}

function insertCueAtPlacement(placement, cueContent = null) {
  console.log('🎯 Step 7: Inserting cue at placement:', placement);

  // Clear any highlighting
  clearInsertionHighlight();

  if (placement.type === 'between') {
    // Insert between paragraphs - straightforward
    insertCueBetweenParagraphsInRawScript(placement, cueContent);
  } else if (placement.type === 'paragraph') {
    // Insert within paragraph - requires splitting
    insertCueWithinParagraphInRawScript(placement, cueContent);
  }

  // Clean up pending state
  pendingCueData.value = null;
  pendingPlacement.value = null;
  pendingCueType.value = null;
  pendingInsertionPoint.value = null;

  console.log('✅ Cue insertion complete - should render in script mode');
}

function insertCueBetweenParagraphs(placement, cueContent) {
  const insertIndex = placement.index + 1; // Insert after the specified paragraph

  if (cueContent) {
    // Add the cue content to script content
    const segments = [...scriptSegments.value];

    // Create cue segment
    const cueSegment = {
      type: 'cue',
      content: cueContent,
      cueType: placement.cueType
    };

    segments.splice(insertIndex, 0, cueSegment);

    const newScriptContent = reconstructScriptContentWithFrontmatter(segments);
    emit('update:scriptContent', newScriptContent);
  }
}

function insertCueWithinParagraph(placement, cueContent) {
  if (!cueContent) return;

  const paragraphIndex = placement.index;
  const characterPosition = placement.characterPosition || 0;

  const segments = [...scriptSegments.value];
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

    const newScriptContent = reconstructScriptContentWithFrontmatter(newSegments);
    emit('update:scriptContent', newScriptContent);
  }
}

// Code Mode: Insert cue at cursor position in raw textarea
function insertCueAtCursor(cueContent) {
  console.log('📝 Inserting cue at cursor position in code mode');

  if (!cueContent) {
    console.error('❌ No cue content provided for insertion');
    return;
  }

  // Get current script content
  let currentScript = props.scriptContent || '';

  // Use stored cursor position (or fallback to end)
  let cursorPosition = pendingCursorPosition.value !== null
    ? pendingCursorPosition.value
    : currentScript.length;

  console.log('📝 Original cursor position:', cursorPosition);

  // UNIVERSAL RULE: Ensure we never insert inside a cue block
  cursorPosition = getSafeInsertionPosition(currentScript, cursorPosition);
  console.log('📝 Safe insertion position:', cursorPosition);

  // Insert cue block at cursor position with proper spacing and blank paragraph
  const beforeCursor = currentScript.slice(0, cursorPosition);
  const afterCursor = currentScript.slice(cursorPosition);

  // Add newlines around cue block and blank paragraph for proper formatting
  const newScript = beforeCursor + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n' + afterCursor;

  console.log('📝 New script length:', newScript.length);

  // Update script content
  emit('update:scriptContent', newScript);

  // Clear cursor position
  pendingCursorPosition.value = null;

  console.log('✅ Cue inserted at cursor position');
}

// Unified cue insertion using snapshotted position (survives modal interaction)
function insertCueAtSnapshotPosition(cueContent) {
  let insertionIndex;
  if (pendingCueInsertionIndex.value !== null && pendingCueInsertionIndex.value >= 0) {
    insertionIndex = pendingCueInsertionIndex.value;
    console.log('📍 Using snapshotted pendingCueInsertionIndex:', insertionIndex);
  } else if (selectedSegmentIndex.value !== null && selectedSegmentIndex.value >= 0) {
    insertionIndex = selectedSegmentIndex.value + 1;
    console.log('📍 Using live selectedSegmentIndex + 1:', insertionIndex);
  } else {
    insertionIndex = scriptSegments.value.length; // ALL segments, not just text
    console.log('📍 No selection - inserting at end of all segments:', insertionIndex);
  }
  const placement = { type: 'between', index: insertionIndex };
  insertCueBetweenParagraphsInRawScript(placement, cueContent);
  pendingCueInsertionIndex.value = null;
}

// Raw Script Insertion Methods (Direct to Database)
function insertCueBetweenParagraphsInRawScript(placement, cueContent) {
  console.log('🎯 Inserting cue between segments in raw script');
  console.log('🎯 Placement index:', placement.index);

  // Get current script content
  let currentScript = props.scriptContent || '';

  // UNIVERSAL RULE: Find ALL content segments (paragraphs AND cue blocks)
  // This ensures we account for cue blocks when calculating insertion positions
  const segmentMatches = findAllContentSegments(currentScript);

  console.log('🎯 Found segments:', segmentMatches.length, segmentMatches.map(s => s.type));

  if (segmentMatches.length === 0) {
    // No segments found, append at end with blank paragraph
    const newScript = currentScript + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n';
    emit('update:scriptContent', newScript);
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
    emit('update:scriptContent', newScript);
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
  insertPosition = getSafeInsertionPosition(currentScript, insertPosition);
  console.log('🎯 Safe insertion position:', insertPosition);

  const beforeCue = currentScript.slice(0, insertPosition);
  const afterCue = currentScript.slice(insertPosition);

  const newScript = beforeCue + '\n\n' + cueContent + '\n\n<p class="josh"></p>\n\n' + afterCue;
  emit('update:scriptContent', newScript);
  console.log('🎯 Cue inserted — watcher will autosave');
}

function insertCueWithinParagraphInRawScript(placement, cueContent) {
  console.log('🎯 Inserting cue within paragraph in raw script');

  // Get current script content
  let currentScript = props.scriptContent || '';

  // UNIVERSAL RULE: First check if placement.index points to a cue block
  // If so, we should insert AFTER the cue block, not within it
  const allSegments = findAllContentSegments(currentScript);

  if (allSegments.length > 0 && placement.index < allSegments.length) {
    const targetSegment = allSegments[placement.index];

    // If the target is a cue block, redirect to between-segments insertion
    if (targetSegment.type === 'cue') {
      console.log('🎯 Target segment is a cue block - redirecting to between-segments insertion');
      // Insert after the cue block (placement.index + 1 in between-zone terms)
      insertCueBetweenParagraphsInRawScript({ index: placement.index + 1 }, cueContent);
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
    insertCueBetweenParagraphsInRawScript(placement, cueContent);
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
  emit('update:scriptContent', newScript);
}

function handleSpeakerChange(newSpeaker) {
  if (editingSpeakerSegmentIndex.value !== null) {
    // Update the segment's speaker
    const updatedSegments = [...scriptSegments.value];
    updatedSegments[editingSpeakerSegmentIndex.value].speaker = newSpeaker;

    // Reconstruct and emit updated content
    const newScriptContent = reconstructScriptContentWithFrontmatter(updatedSegments);
    emit('update:scriptContent', newScriptContent);

    // Clear editing state
    editingSpeakerSegmentIndex.value = null;
  }
}

function focusTypingInput() {
  // Focus the typing input when the typing area is clicked
  nextTick(() => {
    if (typingInputRef.value) {
      typingInputRef.value.focus();
    }
  });
}

function handleTypingInput() {
  // Auto-create paragraphs as user types
  if (typingBuffer.value.trim()) {
    // User is typing, keep the content in buffer
    // We'll convert to paragraph when they finish (on Enter or blur)
  }
}

function handleTypingKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    // Check if this is a double Enter (empty line followed by Enter)
    const currentValue = typingBuffer.value;
    const endsWithNewline = currentValue.endsWith('\n');

    if (endsWithNewline && currentValue.trim() !== '') {
      // Double Enter - create paragraph and start new one
      event.preventDefault();
      createParagraphFromCurrentLine();
    } else {
      // Single Enter - allow normal line break behavior
      // Don't prevent default, let the textarea handle it
    }
  }
}

function handleGlobalKeydown(event) {
  // Debug: trace any ctrl+alt+shift combo so we can see what reaches this handler
  if (event.ctrlKey && event.altKey && event.shiftKey) {
    console.log('🎹 ctrl+alt+shift+', { key: event.key, code: event.code });
  }

  // Skip all global hotkey processing while revision entry input is focused
  if (revisionEntryMode.value) {
    return;
  }

  // Allow space key to pass through to contenteditable elements
  if ((event.key === ' ' || event.code === 'Space') && event.target.isContentEditable) {
    return;
  }

  // Handle Ctrl+Alt+Shift+X for TTS reading.
  // Use event.code ('KeyX') because Alt+Ctrl on some layouts remaps event.key.
  if (event.ctrlKey && event.altKey && event.shiftKey &&
      (event.code === 'KeyX' || event.key?.toLowerCase() === 'x')) {
    console.log('CTRL+ALT+SHIFT+X triggered - opening TTS options or stopping');
    event.preventDefault();
    event.stopPropagation();
    if (isReadingScript.value) {
      stopReading();
    } else {
      openTtsOptionsDialog();
    }
    return;
  }

  // Handle Ctrl+Shift+C for collapse mode toggle
  if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'c') {
    console.log('✅ CTRL+SHIFT+C triggered - toggling collapse mode');
    event.preventDefault();
    collapseMode.value = !collapseMode.value;
    console.log('📦 Collapse mode:', collapseMode.value ? 'ACTIVE' : 'INACTIVE');
    return;
  }

  // Track ALT key state manually
  if (event.key === 'Alt') {
    altKeyPressed.value = true;
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
  if (altKeyPressed.value && event.shiftKey && event.key.toLowerCase() === 'a' && !isInInputField) {
    console.log('✅ ALT+SHIFT+A triggered - calling regenerateCurrentCueAssetID');
    event.preventDefault();
    regenerateCurrentCueAssetID();
    return;
  }

  // Handle ENTER key for placement acceptance (no ALT needed)
  if (event.key === 'Enter' && showCuePlacement.value) {
    const evTarget = event.target;
    const isCodeModeTextarea = evTarget.classList.contains('code-textarea') ||
                             evTarget.closest('.code-textarea');
    const isScriptModeTextarea = evTarget.classList.contains('speaker-textarea') ||
                               evTarget.closest('.speaker-paragraph');

    if (!isCodeModeTextarea && !isScriptModeTextarea) {
      handleEnterKeyForPlacement(event);
      return;
    }
  }

  // ── Cue selector mode (single-key dispatch when cue menu is open) ──
  if (cueMenuOpen.value && !event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    const key = event.key.toLowerCase();
    // ESC closes the cue menu
    if (key === 'escape') {
      event.preventDefault();
      cueMenuOpen.value = false;
      return;
    }
    // Match single key to cue definition
    const cue = cueDefinitions.value.find(c => c.key === key);
    if (cue) {
      event.preventDefault();
      event.stopPropagation();
      insertCueFromMenu(cue.type);
      return;
    }
  }

  // ── Alt+key cue hotkeys ──
  // Use manual ALT tracking instead of event.altKey for better browser compatibility
  if (!altKeyPressed.value || event.ctrlKey || event.shiftKey) {
    return;
  }

  // Skip hotkeys for input fields and contenteditable elements
  if (target.tagName === 'INPUT' ||
      (target.tagName === 'TEXTAREA' && !isInSpeakerParagraph) ||
      (target.isContentEditable && !isInSpeakerParagraph)) {
    return;
  }

  const hotkey = event.key.toLowerCase();

  // Alt+C toggles cue selector menu
  if (hotkey === 'c') {
    event.preventDefault();
    toggleCueMenu();
    return;
  }

  // Alt+key direct cue insertion (still works even without cue menu open)
  const cueDef = cueDefinitions.value.find(c => c.key === hotkey);
  if (cueDef) {
    event.preventDefault();
    if (cueMenuOpen.value) {
      insertCueFromMenu(cueDef.type);
    } else {
      insertCue(cueDef.type);
    }
  }
}

// Handle ENTER key to accept current highlighted location
function handleEnterKeyForPlacement(event) {
  if (showCuePlacement.value && pendingInsertionPoint.value && pendingCueData.value) {
    console.log('⏎ ENTER pressed - accepting current highlighted location');
    event.preventDefault();

    // Create placement object from our stored insertion point
    const placement = {
      type: pendingInsertionPoint.value.type,
      index: getElementIndex(pendingInsertionPoint.value.element),
      cueType: pendingCueType.value,
      characterOffset: pendingInsertionPoint.value.characterOffset || 0
    };

    // Insert at current location
    insertCueAtPlacement(placement, pendingCueData.value);
    showCuePlacement.value = false;
  }
}

// Get the index of an element among its siblings
function getElementIndex(element) {
  const paragraphs = document.querySelectorAll('.speaker-paragraph');
  return Array.from(paragraphs).indexOf(element);
}

function handleGlobalKeyup(event) {
  // Reset ALT key state on keyup
  if (event.key === 'Alt') {
    altKeyPressed.value = false;
    console.log('🔑 ALT key released - setting altKeyPressed = false');
  }
}

function handleWindowBlur() {
  // Reset ALT key state when window loses focus
  // This prevents the ALT key from getting "stuck" if user switches windows while holding ALT
  if (altKeyPressed.value) {
    altKeyPressed.value = false;
    console.log('🔑 Window blur - resetting altKeyPressed to prevent stuck modifier');
  }
}

function createParagraphFromCurrentLine() {
  if (typingBuffer.value.trim()) {
    // Create a new paragraph from the current buffer
    const newParagraph = `<p class="josh">${typingBuffer.value.trim()}</p>`;
    const newScriptContent = props.scriptContent
      ? props.scriptContent + '\n\n' + newParagraph + '\n\n'
      : newParagraph + '\n\n';
    emit('update:scriptContent', newScriptContent);

    // Clear the buffer for the next paragraph
    typingBuffer.value = '';

    // Keep focus on the input for continuous typing
    nextTick(() => {
      if (typingInputRef.value) {
        typingInputRef.value.focus();
      }
    });
  }
}

// Handle traditional script textarea updates while preserving frontmatter
function handleTraditionalScriptUpdate(newContent) {
  // Get existing frontmatter
  const existingFrontmatter = extractYamlFrontmatter(props.scriptContent);

  // Combine frontmatter with new content
  const fullContent = existingFrontmatter
    ? existingFrontmatter + '\n' + newContent
    : newContent;

  emit('update:scriptContent', fullContent);
}

// Handle paragraph click for selection and cursor position tracking
function handleContentEditableMousedown(index, event) {
  // Intercept Ctrl+Click and Shift+Click on contenteditable to enable multi-select
  // Without this, the browser's native Ctrl+Click (word select) or Shift+Click (range select) consumes the event
  if (event.ctrlKey || event.metaKey || event.shiftKey) {
    event.preventDefault();
    event.stopPropagation();
    handleParagraphClick(index, event);
  }
}

function handleParagraphClick(index, event) {
  // Always update lastKnownParagraphIndex for cue insertion positioning
  lastKnownParagraphIndex.value = index;
  console.log('🖱️ Paragraph clicked:', index, '- lastKnownParagraphIndex updated');

  if (event && event.shiftKey && lastMultiSelectAnchor.value !== null) {
    // Shift+click for range selection from anchor to clicked index
    _selectRange(lastMultiSelectAnchor.value, index);
  } else if (event && (event.ctrlKey || event.metaKey)) {
    // Ctrl+click for multi-selection (toggle individual)
    toggleMultiSelection(index);
    lastMultiSelectAnchor.value = index;
  } else {
    // Regular click - clear multi-selection and do single select
    if (multiSelectedSegments.value.size > 0) {
      multiSelectedSegments.value.clear();
    }
    lastMultiSelectAnchor.value = index;
    selectSegment(index);
  }
}

// Get speaker display name
function getSpeakerDisplayName(speaker) {
  const options = CueParser.getSpeakerOptions();
  const option = options.find(opt => opt.value === speaker);
  return option ? option.label : speaker.charAt(0).toUpperCase() + speaker.slice(1);
}

// Get explicit text color style for speaker
function getSpeakerTextStyle(/* speaker */) {
  return {
    color: '#000000 !important'
  };
}

// Get light background style for speaker
function getLightBackgroundStyle(speaker) {
  const speakerColor = speaker === 'josh' ? '#1565C0' : CueParser.getSpeakerColor(speaker);
  return {
    backgroundColor: hexToRgba(speakerColor, 0.05)
  };
}

// Get paragraph background style (with focus states)
function getParagraphBackgroundStyle(speaker, index) {
  console.log(`🎨 getParagraphBackgroundStyle called for index ${index}:`, {
    savedParagraphIndex: savedParagraphIndex.value,
    errorParagraphIndex: errorParagraphIndex.value,
    focusedParagraphIndex: focusedParagraphIndex.value,
    paragraphEditStates: paragraphEditStates.value
  });

  // If error (red flash), override with red
  if (errorParagraphIndex.value === index) {
    console.log(`🔴 Paragraph ${index} has ERROR - showing red`);
    return {
      backgroundColor: '#ffcdd2', // Light red
      transition: 'background-color 0.25s ease'
    };
  }

  // If saved (green flash), override with green
  if (savedParagraphIndex.value === index) {
    console.log(`💚 Paragraph ${index} is SAVED - showing green`);
    return {
      backgroundColor: '#c8e6c9', // Light green
      transition: 'background-color 0.25s ease'
    };
  }

  // If focused, use highlight color from config
  if (focusedParagraphIndex.value === index) {
    console.log(`🟡 Paragraph ${index} is FOCUSED - showing highlight color`);
    return {
      backgroundColor: highlightBackgroundColor.value,
      transition: 'background-color 0.2s ease'
    };
  }

  // Default: paper color background
  return {
    backgroundColor: paperBackgroundColor.value,
    transition: 'background-color 0.2s ease'
  };
}

// Handle paragraph focus
function handleParagraphFocus(index) {
  console.log('🎯 Paragraph focused:', index);

  // Always highlight the currently focused paragraph
  focusedParagraphIndex.value = index;
  // Also persist to lastKnownParagraphIndex for cue insertion (survives blur)
  lastKnownParagraphIndex.value = index;
  // Clear any cue focus when paragraph is focused
  focusedCueIndex.value = null;
  console.log('🟡 focusedParagraphIndex set to:', focusedParagraphIndex.value);
  console.log('🟡 lastKnownParagraphIndex set to:', lastKnownParagraphIndex.value);
}

// Handle cue row focus (for tab navigation)
function handleCueFocus(index) {
  console.log('🎯 Cue row focused:', index);
  focusedCueIndex.value = index;
  // Clear paragraph focus when cue is focused
  focusedParagraphIndex.value = null;
}

// Handle cue row blur
function handleCueBlur(index) {
  console.log('📝 Cue row blurred:', index);
  // Only clear if this cue is still the focused one
  if (focusedCueIndex.value === index) {
    focusedCueIndex.value = null;
  }
}

// Handle click on cue row (focus the row, not internal elements)
function handleCueRowClick(index, event) {
  // If clicking on a button inside the cue card, let it handle the event
  if (event.target.closest('button') || event.target.closest('.v-btn')) {
    return;
  }

  // Shift+click for range selection (works same as paragraphs)
  if (event.shiftKey && lastMultiSelectAnchor.value !== null) {
    event.preventDefault();
    _selectRange(lastMultiSelectAnchor.value, index);
    return;
  }

  // Ctrl+click for multi-selection (works same as paragraphs)
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault();
    toggleMultiSelection(index);
    lastMultiSelectAnchor.value = index;
    return;
  }

  // Regular click - clear multi-selection
  if (multiSelectedSegments.value.size > 0) {
    multiSelectedSegments.value.clear();
  }
  lastMultiSelectAnchor.value = index;

  // Focus the row itself
  focusedCueIndex.value = index;
  event.currentTarget.focus();
}

// Handle paragraph blur
async function handleParagraphBlur(index, event) {
  // CRITICAL: Detect whether this blur was caused by a deliberate user action
  // (clicking another element) or by a programmatic/reactive cause (autosave, Vue re-render).
  // relatedTarget is the element RECEIVING focus. If null, nothing is getting focus
  // intentionally — this is a programmatic blur we should fight against.
  const relatedTarget = event?.relatedTarget
  const blurredElement = event?.target

  // Check if focus is moving to another paragraph, a button, or any interactive element
  const isUserAction = relatedTarget && (
    relatedTarget.closest('.speaker-contenteditable') ||
    relatedTarget.closest('button') ||
    relatedTarget.closest('a') ||
    relatedTarget.closest('input') ||
    relatedTarget.closest('textarea') ||
    relatedTarget.closest('[tabindex]') ||
    relatedTarget.closest('.v-btn') ||
    relatedTarget.closest('.v-list-item') ||
    relatedTarget.closest('.rundown-panel') ||
    relatedTarget.closest('.metadata-panel') ||
    relatedTarget.closest('.v-dialog')
  )

  if (!isUserAction && isActivelyEditing.value && activelyEditingSegment.value === index) {
    // Programmatic blur (autosave, Vue re-render) — don't give up editing state.
    // The silent save path avoids reactive changes, but if a blur still sneaks through,
    // preserve all editing flags so the yellow highlight and cursor stay intact.
    // The element may have already lost DOM focus, so re-focus it synchronously.
    if (blurredElement && document.body.contains(blurredElement)) {
      blurredElement.focus()
    }
    return
  }

  console.log('📝 Paragraph blurred (user action):', index);
  focusedParagraphIndex.value = null;

  // Clear the actively editing segment flag to allow v-html to update again
  if (activelyEditingSegment.value === index) {
    activelyEditingSegment.value = null;
  }

  // Clear the master editing flag to allow watchers to run again
  isActivelyEditing.value = false;

  // Mark this paragraph as having been edited at least once
  paragraphEditStates.value[index] = true;

  // Immediately trigger save on blur (cancel debounce timer)
  if (updateDebounceTimers[index]) {
    console.log('📝 Blur detected - canceling debounce timer and saving immediately');
    clearTimeout(updateDebounceTimers[index]);

    // Execute the save immediately
    if (segmentEditBuffer && segmentEditBuffer[index] !== undefined) {
      const segments = [...scriptSegments.value];

      if (segments[index] && segments[index].type === 'text') {
        segments[index].content = segmentEditBuffer[index];
        const newRawContent = reconstructRawContent(segments);
        emit('update:scriptContent', newRawContent);

        // Clear buffer and timer
        delete segmentEditBuffer[index];
        delete updateDebounceTimers[index];

        // Persist to database and show visual feedback
        await persistCurrentItemToDatabase(index);
      }
    }
  }
}

// Handle save all button click
async function handleSaveAll() {
  console.log('💾 Save All button clicked');

  // CRITICAL: Flush any pending edits from the segment edit buffer BEFORE saving.
  // Without this, clicking Save while a debounce timer is pending would save
  // stale content (missing the user's most recent edits).
  await flushPendingChanges();

  // Emit save event to parent
  emit('save-all');

  // Reset local unsaved changes flag
  hasLocalUnsavedChanges.value = false;

  console.log('✅ Local unsaved changes flag reset');
}

// Persist current item to database with visual feedback
// Preserves cursor position and focus during save using pre-saved state
async function persistCurrentItemToDatabase(segmentIndex) {
  console.log('💾 Persisting current item to database (autosave)...');
  console.log('📍 Using pre-saved cursor state:', savedCursorState.value ? `segment ${savedCursorState.value.segmentIndex}` : 'none');

  try {
    // Emit save-current event to parent ContentEditor
    // This will trigger the saveCurrentItem method which persists to DB
    emit('save-current');

    // Single fade flash on success (CSS animation, no re-render)
    await flashParagraph(segmentIndex, 'success');

    console.log('✅ Autosave successful');
  } catch (error) {
    console.error('❌ Autosave failed:', error);

    // Single fade flash on failure
    await flashParagraph(segmentIndex, 'error');

    // Show urgent flash notification
    if (window.flashUrgent) {
      window.flashUrgent('Autosave Failed!', window.FLASH_COLORS.RED, 3000);
    }
  }

  // Restore cursor position and focus using the pre-saved state
  // This state was captured during typing in handleContentEditableInput
  // Note: isRestoringCursor flag was already set BEFORE emit in updateTextSegment
  // GUARD: Only restore cursor if user is still actively editing.
  // If they blurred (e.g., clicked another item), don't steal focus back.
  nextTick(() => {
    try {
      if (isActivelyEditing.value) {
        restoreCursorPosition();
      }
    } finally {
      // Clear flag after a brief delay to ensure Vue has finished processing
      setTimeout(() => {
        isRestoringCursor.value = false;
      }, 100);
    }
  });
}

// Set editing flags on focus (BEFORE any input events fire)
// This prevents the character reversal bug by ensuring v-html is disabled before typing starts
function setEditingFlags(index) {
  activelyEditingSegment.value = index;
  isActivelyEditing.value = true;
  console.log('🎯 Editing flags set on focus for segment', index);
}

// Restore cursor position from savedCursorState using text offset
// Called after autosave to return user to their editing position
function restoreCursorPosition() {
  if (!savedCursorState.value) {
    console.log('📍 No saved cursor state to restore');
    return;
  }

  const { segmentIndex, textOffset } = savedCursorState.value;
  const refName = `textareaRef-${segmentIndex}`;
  const targetElement = instance.proxy.$refs[refName];

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
    activelyEditingSegment.value = segmentIndex;
    isActivelyEditing.value = true;

    console.log('📍 Cursor restored to segment', segmentIndex, 'at offset', textOffset);
  } catch (e) {
    console.warn('📍 Could not restore cursor position:', e);
    // Ultimate fallback: just focus the element
    targetElement.focus();
    activelyEditingSegment.value = segmentIndex;
    isActivelyEditing.value = true;
  }
}

// Flash the currently focused paragraph green on successful autosave
// Called by ContentEditor after debounced autosave completes
function flashFocusedParagraphSaved() {
  console.log('💚 flashFocusedParagraphSaved called');
  console.log('💚 focusedParagraphIndex:', focusedParagraphIndex.value);
  console.log('💚 activelyEditingSegment:', activelyEditingSegment.value);

  // Try focusedParagraphIndex first, fall back to activelyEditingSegment
  let index = focusedParagraphIndex.value;
  if (index === null || index === undefined) {
    index = activelyEditingSegment.value;
  }

  if (index !== null && index !== undefined) {
    console.log('💚 Flashing paragraph', index, 'green for successful save');
    flashParagraph(index, 'success');
  } else {
    console.log('⚠️ No focused paragraph to flash - both focusedParagraphIndex and activelyEditingSegment are null');
  }
}

// Flash a paragraph with specified color
// Uses JavaScript-based animations to support dynamic colors from settings
// This prevents cursor loss during autosave by not triggering Vue re-renders
// eslint-disable-next-line no-unused-vars
async function flashParagraph(index, type, count = 1) {
  // TODO: All flashing effects temporarily paused - remove this early return to re-enable
  return;
  // eslint-disable-next-line no-unreachable
  const refName = `textareaRef-${index}`;
  let element = instance.proxy.$refs[refName];

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
      flashColor = hexToRgba(resolvedColor, 0.7);
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
}

// Get dark border style for speaker header
function getSpeakerHeaderStyle(speaker) {
  const speakerColor = speaker === 'josh' ? '#1565C0' : CueParser.getSpeakerColor(speaker);
  return {
    borderBottomColor: darkenColor(speakerColor, 0.3)
  };
}

// Darken a hex color
function darkenColor(hex, amount) {
  const r = Math.max(0, parseInt(hex.slice(1, 3), 16) * (1 - amount));
  const g = Math.max(0, parseInt(hex.slice(3, 5), 16) * (1 - amount));
  const b = Math.max(0, parseInt(hex.slice(5, 7), 16) * (1 - amount));
  return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
}

// Convert hex to rgba
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Auto Scrub function to fix multiple paragraphs in single <p> tags
function autoscrubContent() {
  if (!props.scriptContent || typeof props.scriptContent !== 'string') {
    return;
  }

  // Don't run autoscrub while user is actively typing
  if (isActivelyTyping.value) {
    console.log('Auto Scrub skipped - user is actively typing');
    return false;
  }

  // Read autoscrub settings from localStorage (with backwards compat for old 'autoformat' keys)
  const interfaceSettings = JSON.parse(localStorage.getItem('showbuild_interface_settings') || '{}');
  const stripSpans = (interfaceSettings.autoscrubStripSpans ?? interfaceSettings.autoformatStripSpans) !== false;
  // SUSPENDED: removeEmptyParagraphs - all empty paragraph manipulation disabled
  // const removeEmptyParagraphs = (interfaceSettings.autoscrubRemoveEmptyParagraphs ?? interfaceSettings.autoformatRemoveEmptyParagraphs) !== false;
  const removeLeadingDashes = (interfaceSettings.autoscrubRemoveLeadingDashes ?? interfaceSettings.autoformatRemoveLeadingDashes) !== false;
  const cleanWhitespace = (interfaceSettings.autoscrubCleanWhitespace ?? interfaceSettings.autoformatCleanWhitespace) !== false;

  let hasChanges = false;
  let formattedContent = props.scriptContent;

  // === STEP 0: Strip YAML frontmatter if present ===
  // Database-first architecture means frontmatter should never be in script_content
  if (formattedContent.trim().startsWith('---')) {
    const stripped = stripYamlFrontmatter(formattedContent);
    if (stripped !== formattedContent) {
      formattedContent = stripped;
      hasChanges = true;
      console.log('Auto Scrub: Stripped YAML frontmatter');
    }
  }

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

  // DISABLED: Do NOT remove empty paragraphs - users need them for spacing around cues
  // formattedContent = formattedContent.replace(/<p[^>]*>(\s|<br\s*\/?>)*<\/p>\s*/gi, '');

    if (formattedContent.length !== originalLength) {
      hasChanges = true;
      console.log('Auto Scrub: Stripped span tags and inline styles');
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
      console.log('Auto Scrub: Cleaned whitespace');
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
            console.log('Auto Scrub: Removed leading dash from paragraph');
          }
        }
      }
    }
  } // End if (removeLeadingDashes)

  // === STEP 3b: Detect and flag invalid content inside paragraphs ===
  // 1. Invalid cue patterns: {SOT/slug}, {VO/slug}, etc.
  // 2. Unwelcome HTML: <img>, <a>, <div>, <span>, <table>, <iframe>, <style>,
  //    <script>, <link>, <embed>, <object>, <svg>, <video>, <audio>, <source>,
  //    <picture>, <figure>, <form>, <input>, <select>, <textarea> tags
  // Allowed tags inside paragraphs: <b>, <i>, <u>, <em>, <strong>, <mark>, <br>, <sub>, <sup>
  {
    // Pattern source-of-truth: @/modules/legacyCueConvert/patterns.js
    const invalidCuePattern = LEGACY_CUE_REGEX;
    const unwelcomeHtmlPattern = /<\/?(?:img|a|div|span|table|thead|tbody|tr|td|th|iframe|style|script|link|embed|object|svg|video|audio|source|picture|figure|figcaption|form|input|select|textarea|button|canvas|map|area|meta|base|section|article|aside|nav|header|footer|main|details|summary|dialog|pre|code|blockquote|ol|ul|li|dl|dt|dd|hr|font|center)\b[^>]*>/i;
    const cueCheckMatches = [...formattedContent.matchAll(/<p(?:\s+class="([^"]*)")?[^>]*>([\s\S]*?)<\/p>/g)];

    for (const match of cueCheckMatches) {
      const fullMatch = match[0];
      const content = match[2];
      const plainContent = content.replace(/<[^>]+>/g, '');

      // Skip if already marked with ***
      if (plainContent.trim().startsWith('***')) continue;

      // Determine what kind of bad content we found
      let flagReason = null;
      if (invalidCuePattern.test(plainContent)) {
        flagReason = LEGACY_CUE_FLAG_LABEL;
      } else if (unwelcomeHtmlPattern.test(content)) {
        flagReason = 'Unwelcome HTML detected';
      }

      if (flagReason) {
        const speaker = match[1] || 'josh';
        const attrs = fullMatch.includes('data-needs-attention') ? '' : ' data-needs-attention="true"';
        const noteAttr = fullMatch.includes('data-flag-note') ? '' : ` data-flag-note="${flagReason}"`;
        const newTag = `<p class="${speaker}"${attrs}${noteAttr}>*** ${content}</p>`;
        formattedContent = formattedContent.replace(fullMatch, newTag);
        hasChanges = true;
        console.log(`Auto Scrub: Flagged paragraph - ${flagReason}`);
      }
    }
  }

  // === STEP 3c: Un-flag paragraphs that no longer contain bad content ===
  // If a paragraph was previously flagged by auto scrub (has *** prefix and auto-scrub flag note)
  // but the offending content has since been removed, clear the flag and *** prefix.
  {
    // Pattern source-of-truth: @/modules/legacyCueConvert/patterns.js
    // (must match invalidCuePattern in step 3a so flags clear when content is fixed).
    const invalidCuePattern2 = LEGACY_CUE_REGEX;
    const unwelcomeHtmlPattern2 = /<\/?(?:img|a|div|span|table|thead|tbody|tr|td|th|iframe|style|script|link|embed|object|svg|video|audio|source|picture|figure|figcaption|form|input|select|textarea|button|canvas|map|area|meta|base|section|article|aside|nav|header|footer|main|details|summary|dialog|pre|code|blockquote|ol|ul|li|dl|dt|dd|hr|font|center)\b[^>]*>/i;
    // Match paragraphs that have the auto-scrub flag note
    const flaggedMatches = [...formattedContent.matchAll(/<p\s+class="([^"]*)"([^>]*data-flag-note="(?:Invalid cue code|Unwelcome HTML detected)"[^>]*)>([\s\S]*?)<\/p>/g)];

    for (const match of flaggedMatches) {
      const fullMatch = match[0];
      const speaker = match[1] || 'josh';
      const content = match[3];
      const plainContent = content.replace(/<[^>]+>/g, '');

      // Check if the content still has the problem
      const stillHasCue = invalidCuePattern2.test(plainContent);
      const stillHasHtml = unwelcomeHtmlPattern2.test(content);

      if (!stillHasCue && !stillHasHtml) {
        // Problem is gone — remove *** prefix and flag attributes
        let cleanedContent = content.replace(/^\*\*\*\s*/, '');
        const newTag = `<p class="${speaker}">${cleanedContent}</p>`;
        formattedContent = formattedContent.replace(fullMatch, newTag);
        hasChanges = true;
        console.log('Auto Scrub: Cleared resolved flag from paragraph');
      }
    }
  }

  // === STEP 4: Clean up empty paragraphs and cue spacing ===
  // FULLY SUSPENDED: All empty paragraph manipulation disabled
  // This was causing issues where users couldn't add paragraphs around cues
  // The autoscrub was removing blank paragraphs that users need for spacing
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
    console.log('Auto Scrub: Content was formatted');
    emit('update:scriptContent', formattedContent);
    return true;
  }

  return false;
}

// Run autoscrub and show status
function runAutoscrub() {
  const wasFormatted = autoscrubContent();

  // YAML frontmatter validation and synchronization - DISABLED
  // Frontmatter is only generated during export, not during editing
  // const yamlUpdated = validateAndSyncYamlFrontmatter();
  const yamlUpdated = false;

  // Smart cleanup of orphaned cursor markers (only when safe)
  const cleanedMarkers = smartCleanupOrphanedCursorMarkers();

  lastAutoscrubTime.value = new Date(); // Update timestamp regardless of whether changes were made

  if (wasFormatted || yamlUpdated || cleanedMarkers > 0) {
// Content change is handled automatically through rawScriptContent computed property
  }

  // Also ask ContentEditor to scrub all other rundown items
  emit('autoscrub-all-items');
}

// Smart cleanup that respects active cursor highlighting and modal usage
function smartCleanupOrphanedCursorMarkers() {
  const cursorChar = '█';

  // Safety checks - don't cleanup if user is actively working with cursor highlighting
  if (isUserActivelyHighlighting()) {
    console.log('🛡️ Auto-cleanup: Skipping - user is actively highlighting cursor position');
    return 0;
  }

  let totalCleaned = 0;
  console.log('🧹 Auto-cleanup: Safe to scan for orphaned cursor markers...');

  // 1. Clean cursor markers from script content (only if no active modals)
  if (props.scriptContent && props.scriptContent.includes(cursorChar)) {
    const originalLength = props.scriptContent.length;
    const cleanedContent = props.scriptContent.replace(new RegExp(cursorChar, 'g'), '');
    const removedFromScript = originalLength - cleanedContent.length;

    if (removedFromScript > 0) {
      emit('update:scriptContent', cleanedContent);
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
}

// Check if user is actively using cursor highlighting (modal open, etc.)
function isUserActivelyHighlighting() {
  // Check if any modals are open
  const hasOpenModal = document.querySelector('.v-overlay--active .v-dialog') !== null;

  // Check if cursor positioning is active
  const hasCursorPositioning = cursorPositionHighlight.value !== null || showCuePlacement.value;

  // Check if thick cursor is showing (insertion mode)
  const hasThickCursor = thickCursor.value && thickCursor.value.show;

  // Check if user typed recently (within last 10 seconds)
  const recentActivity = lastAutoscrubTime.value &&
    (new Date() - lastAutoscrubTime.value) < 10000;

  // Check if any cue modals are open (IMG, GFX, SOT, etc.)
  const hasCueModal = document.querySelector('[class*="Modal"]:not([style*="display: none"])') !== null;

  return hasOpenModal || hasCursorPositioning || hasThickCursor || recentActivity || hasCueModal;
}

// Timer management for autoscrub
function startAutoscrubTimer() {
  stopAutoscrubTimer(); // Clear any existing timer

  // Read autoscrub settings from localStorage
  const interfaceSettings = JSON.parse(localStorage.getItem('showbuild_interface_settings') || '{}');
  const autoscrubEnabled = (interfaceSettings.autoscrubEnabled ?? interfaceSettings.autoformatEnabled) !== false; // Default to true
  const intervalSeconds = interfaceSettings.autoscrubInterval || interfaceSettings.autoformatInterval || 30;

  if (!autoscrubEnabled) {
    console.log('Auto Scrub disabled in settings');
    return;
  }

  autoscrubTimer.value = setInterval(() => {
    runAutoscrub();
  }, intervalSeconds * 1000);
  console.log(`Auto Scrub timer started (every ${intervalSeconds}s)`);
}

function stopAutoscrubTimer() {
  if (autoscrubTimer.value) {
    clearInterval(autoscrubTimer.value);
    autoscrubTimer.value = null;
  }
}

// Debounced autoscrub for content changes
function scheduleAutoscrub() {
  clearAutoscrubDebounce();
  autoscrubDebounceTimer.value = setTimeout(() => {
    runAutoscrub();
  }, 5000); // Run 5 seconds after last content change
}

function clearAutoscrubDebounce() {
  if (autoscrubDebounceTimer.value) {
    clearTimeout(autoscrubDebounceTimer.value);
    autoscrubDebounceTimer.value = null;
  }
}

function createParagraphFromBuffer() {
  if (typingBuffer.value.trim()) {
    // Split the buffer by line breaks to create separate paragraphs
    const lines = typingBuffer.value.split('\n').filter(line => line.trim());

    // Create a <p> tag for each line
    const newParagraphs = lines.map(line => `<p class="josh">${line.trim()}</p>`).join('\n\n');

    const newScriptContent = props.scriptContent
      ? props.scriptContent + '\n\n' + newParagraphs + '\n\n'
      : newParagraphs + '\n\n';

    emit('update:scriptContent', newScriptContent);

    // Clear the buffer
    typingBuffer.value = '';

    // Keep focus on the input for continuous typing
    nextTick(() => {
      if (typingInputRef.value) {
        typingInputRef.value.focus();
      }
    });
  }
}

// Universal Cue Insertion Workflow Methods
function showFlashMessage(cueType) {
  const flashMessage = `Insert ${cueType} CUE`;

  // Get the actual cue color from the theme system (same as button)
  const cueColor = getCueColor(cueType);

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
}

function detectAndHighlightCursorPosition(cueType) {
  console.log("🎯 detectAndHighlightCursorPosition called with:", cueType);
  console.log("🎯 Current editorMode:", props.editorMode);

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
      highlightInsertionArea(firstParagraph);

      // Extract segment ID from class for script mode
      const segmentId = extractSegmentId(firstParagraph);

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
    const segmentId = extractSegmentId(speakerParagraph);
    console.log("🎯 Extracted segment ID:", segmentId);

    // Highlight the paragraph with cue colors
    highlightInsertionArea(speakerParagraph);

    // For script mode, we just need segment ID, not cursor position
    if (props.editorMode === 'script') {
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
    showThickCursor(textarea, cursorPosition);

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
      highlightInsertionArea(lastParagraph);
      const segmentId = extractSegmentId(lastParagraph);

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
}

function extractSegmentId(paragraphElement) {
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
}

function highlightInsertionArea(element) {
  // Clear any existing highlights
  clearInsertionHighlight();

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
  highlightedElement.value = element;
  console.log("🎨 Highlight applied successfully to:", element.className);

  // Second level highlighting: precise cursor position within paragraph
  nextTick(() => {
    addCursorPositionHighlight(element);
  });
}

function showThickCursor(textarea, cursorPosition) {
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
  thickCursor.value = {
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
    thickCursor.value.show = false;
  }, 500);
}

function clearInsertionHighlight() {
  if (highlightedElement.value) {
    console.log("🎨 Clearing highlight from:", highlightedElement.value.className);

    // Restore original styles if they were stored
    if (highlightedElement.value._originalStyles) {
      const original = highlightedElement.value._originalStyles;
      highlightedElement.value.style.backgroundColor = original.backgroundColor;
      highlightedElement.value.style.border = original.border;
      highlightedElement.value.style.boxShadow = original.boxShadow;
      highlightedElement.value.style.transform = original.transform;
      highlightedElement.value.style.transition = original.transition;
      delete highlightedElement.value._originalStyles;
    } else {
      // Fallback to removing properties
      highlightedElement.value.style.removeProperty('background-color');
      highlightedElement.value.style.removeProperty('border');
      highlightedElement.value.style.removeProperty('transition');
      highlightedElement.value.style.removeProperty('box-shadow');
      highlightedElement.value.style.removeProperty('transform');
    }

    highlightedElement.value = null;
  }
  // Also clear thick cursor
  thickCursor.value.show = false;

  // Clear cursor position highlight if it exists
  clearCursorPositionHighlight();
}

// Clean up any leftover cursor characters (█) from textarea content
function cleanupCursorCharacters() {
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
}

// Add keyboard event handler to manually delete cursor characters
function handleCursorCharacterKeydown(event) {
  // If user presses Backspace or Delete while cursor character is present
  if (event.key === 'Backspace' || event.key === 'Delete') {
    const textarea = event.target;
    const cursorChar = '█';

    if (textarea && textarea.value && textarea.value.includes(cursorChar)) {
      console.log("🎹 Detected cursor character during delete - cleaning up");

      // Small delay to let the delete operation complete first
      setTimeout(() => {
        cleanupCursorCharacters();
      }, 10);
    }
  }
}

function addCursorPositionHighlight(element) {
  console.log("🎯🔥 STARTING addCursorPositionHighlight - CLEARING ANY EXISTING FIRST");

  // CRITICAL: Clear any existing cursor highlights immediately before creating new one
  clearCursorPositionHighlight();

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
  cursorPositionHighlight.value = cursorHighlight;

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
  cursorPositionTimeout.value = setTimeout(() => {
    clearCursorPositionHighlight();
    console.log("🎯 Cursor position highlight automatically cleared after 1000ms");
  }, 1000);
}

function clearCursorPositionHighlight() {
  console.log("🎯🔥 STARTING clearCursorPositionHighlight - AGGRESSIVE CLEANUP");

  // Clear the timeout if it exists
  if (cursorPositionTimeout.value) {
    clearTimeout(cursorPositionTimeout.value);
    cursorPositionTimeout.value = null;
    console.log("🎯✅ Cleared cursor position timeout");
  } else {
    console.log("🎯⚠️ No timeout to clear");
  }

  // Remove the highlight element if it exists
  if (cursorPositionHighlight.value) {
    console.log("🎯🔥 Found cursorPositionHighlight element, attempting removal...");
    console.log("🎯📍 Element details:", {
      nodeName: cursorPositionHighlight.value.nodeName,
      className: cursorPositionHighlight.value.className,
      parentNode: cursorPositionHighlight.value.parentNode ? 'exists' : 'missing',
      isConnected: cursorPositionHighlight.value.isConnected
    });

    let removed = false;

    // Method 1: Check if element is still in the DOM
    if (cursorPositionHighlight.value.parentNode) {
      try {
        cursorPositionHighlight.value.parentNode.removeChild(cursorPositionHighlight.value);
        removed = true;
        console.log("🎯✅ Removed via parentNode.removeChild");
      } catch (error) {
        console.warn("🎯❌ parentNode.removeChild failed:", error);
      }
    }

    // Method 2: Try direct remove() method
    if (!removed) {
      try {
        cursorPositionHighlight.value.remove();
        removed = true;
        console.log("🎯✅ Removed via element.remove()");
      } catch (error) {
        console.warn("🎯❌ element.remove() failed:", error);
      }
    }

    // Method 3: Try document.body.removeChild as fallback
    if (!removed) {
      try {
        document.body.removeChild(cursorPositionHighlight.value);
        removed = true;
        console.log("🎯✅ Removed via document.body.removeChild");
      } catch (error) {
        console.warn("🎯❌ document.body.removeChild failed:", error);
      }
    }

    // Clear the reference regardless
    cursorPositionHighlight.value = null;
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
}

// AssetID Management Methods
async function requestNewEpisodeAssetID() {
  try {
    console.log('🆔 Requesting new Episode AssetID...');

    // Get current episode AssetID from metadata or fallback
    const currentEpisodeAssetID = currentEpisodeMetadata.value?.AssetID || currentEpisodeMetadata.value?.asset_id; // eslint-disable-line no-undef

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
          episode_number: props.currentEpisode,
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
    emit('asset-id-regenerated', {
      type: 'episode',
      old_asset_id: result.old_asset_id,
      new_asset_id: result.new_asset_id
    });

    console.log('✅ Episode AssetID regenerated:', result);

    // Refresh all AssetID displays
    await refreshAllAssetIDDisplays('episode', result.old_asset_id, result.new_asset_id);

  } catch (error) {
    console.error('❌ Failed to regenerate Episode AssetID:', error);
    alert(`Failed to regenerate Episode AssetID: ${error.message}`);
  }
}

// Regenerate AssetID for currently focused cue block (Alt+Shift+A hotkey)
async function regenerateCurrentCueAssetID() {
  try {
    console.log('🆔 Alt+Shift+A: Regenerating current cue AssetID...');

    // Find the currently focused cue block by analyzing cursor position
    const currentCue = getCurrentCueAtCursor();

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
          episode_number: props.currentEpisode,
          source: 'alt_shift_a_hotkey',
          parent_item_asset_id: props.item?.asset_id
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ Cue AssetID regenerated successfully:', result);

    // Update the cue in the content with the new AssetID
    updateCueAssetIdInContent(currentCue, result.new_asset_id);

    // Refresh all AssetID displays
    await refreshAllAssetIDDisplays('cue', result.old_asset_id, result.new_asset_id);

    // Show success message
    alert(`Cue AssetID regenerated successfully!\nOld: ${result.old_asset_id}\nNew: ${result.new_asset_id}`);

  } catch (error) {
    console.error('❌ Failed to regenerate Cue AssetID:', error);
    alert(`Failed to regenerate Cue AssetID: ${error.message}`);
  }
}

// Find the cue block at the current cursor position
function getCurrentCueAtCursor() {
  // Get the currently active textarea (script or code mode)
  let activeTextarea = null;
  let content = '';

  if (props.editorMode === 'script') {
    // In script mode, check if we're in a speaker textarea or main content
    activeTextarea = document.activeElement;
    if (activeTextarea && activeTextarea.tagName === 'TEXTAREA') {
      content = activeTextarea.value;
    } else {
      // Fallback to script content
      content = props.scriptContent || '';
    }
  } else if (props.editorMode === 'code') {
    // In code mode, use script content
    content = props.scriptContent || '';
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
}

// Update the cue AssetID in the content
function updateCueAssetIdInContent(cueInfo, newAssetId) {
  // Both Script and Code modes use scriptContent as single source of truth
  const content = props.scriptContent || '';

  // Replace the old AssetID with the new one in the matched pattern
  const updatedContent = content.substring(0, cueInfo.start) +
                        cueInfo.fullMatch.replace(cueInfo.assetId, newAssetId) +
                        content.substring(cueInfo.end);

  // Update the content (works for both Script and Code modes)
  emit('update:scriptContent', updatedContent);

  console.log('✅ Updated cue AssetID in content:', cueInfo.assetId, '→', newAssetId);
}

// Comprehensive refresh system for all AssetID displays
async function refreshAllAssetIDDisplays(entityType, oldAssetId, newAssetId) {
  console.log(`🔄 Refreshing all AssetID displays: ${entityType} ${oldAssetId} → ${newAssetId}`);

  try {
    // 1. Emit to parent components for episode/rundown refreshes
    emit('assetid-regenerated', {
      entityType: entityType,
      oldAssetId: oldAssetId,
      newAssetId: newAssetId,
      timestamp: new Date().toISOString()
    });

    // 2. Force reload episode metadata if it's an episode AssetID
    if (entityType === 'episode') {
      emit('reload-episode-metadata', {
        newAssetId: newAssetId,
        reason: 'assetid_regenerated'
      });
    }

    // 3. Force rundown reload to refresh item AssetIDs in rundown panel
    if (entityType === 'segment' || entityType === 'episode') {
      emit('reload-rundown', {
        reason: 'assetid_regenerated',
        affectedAssetId: newAssetId
      });
    }

    // 4. Trigger reactive updates for any watched properties
    await nextTick();

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
}

async function showAssetIDInfo() {
  try {
    console.log('🆔 Showing AssetID info...');

    // Get current episode AssetID
    const episodeAssetID = currentEpisodeMetadata.value?.AssetID || currentEpisodeMetadata.value?.asset_id; // eslint-disable-line no-undef
    const currentItemAssetID = props.currentItemMetadata?.AssetID || props.currentItemMetadata?.asset_id;

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

    infoText += `\n📚 Episode: ${props.currentEpisode || 'Unknown'}`;

    alert(infoText);

  } catch (error) {
    console.error('❌ Failed to show AssetID info:', error);
    alert(`Failed to show AssetID info: ${error.message}`);
  }
}

// Toggle script reading (start or stop)
function toggleScriptReading() {
  if (isReadingScript.value) {
    stopReading();
  } else {
    startReadingScript();
  }
}

// Start reading the script from the beginning
async function startReadingScript() {
  if (!isTtsConfigured.value) {
    console.error('TTS is not configured');
    return;
  }

  if (readableParagraphs.value.length === 0) {
    console.warn('No readable paragraphs found in script');
    return;
  }

  console.log('Starting script reading');
  isReadingScript.value = true;
  currentReadingIndex.value = 0;

  // Create audio element if it doesn't exist
  if (!audioElement.value) {
    audioElement.value = new Audio();
    audioElement.value.addEventListener('ended', handleAudioEnd);
    audioElement.value.addEventListener('error', handleAudioError);
  }

  // Start reading first paragraph
  await readCurrentParagraph();
}

// Read the current paragraph
async function readCurrentParagraph() {
  if (currentReadingIndex.value >= readableParagraphs.value.length) {
    console.log('🔊 Finished reading all paragraphs');
    stopReading();
    return;
  }

  const paragraph = readableParagraphs.value[currentReadingIndex.value];
  console.log(`🔊 Reading paragraph ${currentReadingIndex.value}:`, paragraph.content.substring(0, 50) + '...');

  try {
    // Request audio from TTS
    // Note: Don't pass speaker - paragraph.speaker is a UI code (e.g., 'josh')
    // not a TTS speaker name. Let TTS use its configured default speaker.
    const audioBlob = await ttsInstance.value.synthesizeSpeech(paragraph.content);

    // Create object URL and play audio
    const audioUrl = URL.createObjectURL(audioBlob);
    audioElement.value.src = audioUrl;
    await audioElement.value.play();

    console.log(`🔊 Playing audio for paragraph ${currentReadingIndex.value}`);
  } catch (error) {
    console.error('Failed to synthesize or play audio:', error);
    // Continue to next paragraph on error
    currentReadingIndex.value++;
    if (isReadingScript.value) {
      setTimeout(() => readCurrentParagraph(), 100);
    }
  }
}

// Handle audio end event (move to next paragraph)
function handleAudioEnd() {
  console.log(`🔊 Finished playing paragraph ${currentReadingIndex.value}`);

  // Clean up the object URL
  if (audioElement.value && audioElement.value.src) {
    URL.revokeObjectURL(audioElement.value.src);
  }

  // Move to next paragraph
  currentReadingIndex.value++;

  // Read next paragraph if still reading
  if (isReadingScript.value) {
    setTimeout(() => readCurrentParagraph(), 500); // 500ms pause between paragraphs
  }
}

// Handle audio error
function handleAudioError(error) {
  console.error('Audio playback error:', error);
  // Try next paragraph
  currentReadingIndex.value++;
  if (isReadingScript.value) {
    setTimeout(() => readCurrentParagraph(), 100);
  }
}

// Stop reading the script
function stopReading() {
  console.log('🔊 Stopping script reading');
  isReadingScript.value = false;

  // Stop and clean up audio
  if (audioElement.value) {
    audioElement.value.pause();
    if (audioElement.value.src) {
      URL.revokeObjectURL(audioElement.value.src);
    }
    audioElement.value.src = '';
  }

  currentReadingIndex.value = 0;
}

// Toggle contextual reading (Ctrl+Shift+R hotkey)
function toggleContextualReading(options) {
  if (isReadingScript.value) {
    stopReading();
  } else {
    startContextualReading(options);
  }
}

// Open the pre-read options modal (loads voices on first open).
async function openTtsOptionsDialog() {
  if (!isTtsConfigured.value) {
    if (typeof window.notifyUserStandard === 'function') {
      window.notifyUserStandard('TTS is not configured — enable it in Settings → Voice', '#F44336', 4000);
    }
    return;
  }

  // Seed the form from the last-used options (or defaults)
  ttsOptionsForm.value = {
    voice: activeReadingOptions.value.voice || 'josh-1',
    speed: activeReadingOptions.value.speed || 1.0
  };

  showTtsOptionsDialog.value = true;

  // Lazy-load voice list
  if (!ttsAvailableVoices.value.length && !ttsVoicesLoading.value) {
    ttsVoicesLoading.value = true;
    try {
      if (ttsInstance.value && typeof ttsInstance.value.fetchSpeakers === 'function') {
        const speakers = await ttsInstance.value.fetchSpeakers();
        ttsAvailableVoices.value = Array.isArray(speakers) ? speakers : [];
      }
    } catch (err) {
      console.warn('Failed to fetch TTS voices:', err);
    } finally {
      ttsVoicesLoading.value = false;
    }
  }
}

function confirmTtsOptionsAndRead() {
  const opts = {
    voice: (ttsOptionsForm.value.voice || 'josh-1').toString().trim() || 'josh-1',
    speed: Number(ttsOptionsForm.value.speed) || 1.0
  };
  showTtsOptionsDialog.value = false;
  activeReadingOptions.value = opts;
  if (typeof window.notifyUserStandard === 'function') {
    window.notifyUserStandard(`Reading with ${opts.voice} @ ${opts.speed}x`, '#2196F3', 2000);
  }
  toggleContextualReading(opts);
}

function cancelTtsOptionsDialog() {
  showTtsOptionsDialog.value = false;
}

// Start contextual reading based on what's highlighted
async function startContextualReading(options) {
  if (!isTtsConfigured.value) {
    console.error('TTS is not configured');
    if (typeof window.notifyUserStandard === 'function') {
      window.notifyUserStandard('TTS is not configured — enable it in Settings → Voice', '#F44336', 4000);
    }
    return;
  }

  const context = getReadingContext();
  if (!context) {
    console.warn('No content to read');
    if (typeof window.notifyUserStandard === 'function') {
      window.notifyUserStandard('Nothing to read', '#FF9800', 2500);
    }
    return;
  }

  // Resolve playback options (modal selection wins; falls back to active default)
  const opts = {
    voice: (options?.voice || activeReadingOptions.value.voice || 'josh-1'),
    speed: Number(options?.speed || activeReadingOptions.value.speed || 1.0)
  };
  activeReadingOptions.value = opts;

  console.log('🔊 Starting contextual reading:', context, 'opts:', opts);
  isReadingScript.value = true;

  try {
    if (context.type === 'rundown_item') {
      // Rundown-item mode: episode preamble + each paragraph / cue summary,
      // with synthesis pipelined one step ahead of playback.
      await playPipelined(context.items, opts);
    } else {
      const announcement = buildAnnouncementText(context);
      await playAnnouncement(announcement);
      await playContent(context.content, opts);
    }

    console.log('✅ Contextual reading complete');
  } catch (error) {
    console.error('❌ Contextual reading failed:', error);
  } finally {
    stopReading();
  }
}

// Determine what's currently selected/highlighted
function getReadingContext() {
  // Check if a specific segment is selected via selectedSegmentIndex
  if (selectedSegmentIndex.value !== null && selectedSegmentIndex.value >= 0) {
    const segment = scriptSegments.value[selectedSegmentIndex.value];
    return {
      type: 'segment',
      index: selectedSegmentIndex.value,
      content: processContentForReading(segment.content),
      speaker: segment.speaker
    };
  }

  // Check if a specific paragraph is focused
  if (focusedParagraphIndex.value !== null && focusedParagraphIndex.value >= 0) {
    const paragraph = scriptSegments.value[focusedParagraphIndex.value];
    return {
      type: 'paragraph',
      index: focusedParagraphIndex.value,
      content: processContentForReading(paragraph.content),
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
        content: processContentForReading(selectedText)
      };
    }

    return {
      type: 'selection',
      content: processContentForReading(selectedText)
    };
  }

  // Default: a rundown item is selected but no paragraph/selection is focused.
  // Read episode preamble, then each paragraph one-at-a-time (pipelined by caller).
  return {
    type: 'rundown_item',
    items: buildRundownItemReadingItems()
  };
}

// Build the queue of items to speak for a rundown-item read-through.
// Entries: { kind: 'announcement' | 'content' | 'pause', text?, ms? }
function buildRundownItemReadingItems() {
  const items = [];
  const episodeNumber = (props.currentEpisode || '').toString().trim() || 'unknown';
  const episodeTitle = (props.currentEpisodeTitle || '').trim();

  items.push({ kind: 'announcement', text: `Episode Number ${episodeNumber}.` });
  if (episodeTitle) {
    items.push({ kind: 'announcement', text: `Episode Title: ${episodeTitle}.` });
  } else {
    items.push({ kind: 'announcement', text: 'Title yet to be determined.' });
  }
  items.push({ kind: 'pause', ms: 200 });
  items.push({ kind: 'announcement', text: 'Begin.' });

  const itemSlug = (props.currentItemMetadata?.slug || '').toString().trim();
  if (itemSlug) {
    items.push({ kind: 'pause', ms: 150 });
    items.push({ kind: 'announcement', text: `Slug: ${itemSlug}.` });
  }

  const segments = scriptSegments.value || [];
  console.log('🎙️ buildRundownItemReadingItems: scriptSegments count =', segments.length, segments);
  for (const seg of segments) {
    if (!seg) continue;
    if (seg.type === 'cue') {
      const cueType = seg.cueType || seg.data?.type || '';
      const cueName = getReadableCueName(cueType);
      const slug = (seg.data?.slug || '').toString().trim() || 'no slug';
      items.push({ kind: 'content', text: `Cue: ${cueName}. Slug: ${slug}.` });
    } else if (seg.type === 'text') {
      const cleaned = processContentForReading(seg.content);
      if (cleaned) {
        items.push({ kind: 'content', text: cleaned });
      } else {
        console.warn('🎙️ skipping text segment: empty after processContentForReading', seg);
      }
    } else {
      console.warn('🎙️ skipping segment: unknown type', seg.type, seg);
    }
  }

  console.log('🎙️ buildRundownItemReadingItems: final queue =', items);
  return items;
}

function getReadableCueName(cueType) {
  if (!cueType) return 'cue';
  const def = cueDefinitions.value.find(c => c.type === cueType.toString().toUpperCase());
  return def ? def.tooltip : cueType.toString().toUpperCase();
}

// Process content for reading (replace cues with placeholder)
function processContentForReading(content) {
  if (!content) return '';

  // Replace cue blocks with "insert cue block here"
  let processed = content.replace(/\[\[CUE:[^\]]+\]\]/g, 'insert cue block here');

  // Clean up any remaining markup
  processed = processed.replace(/<[^>]+>/g, '');

  return processed.trim();
}

// Build announcement text based on context
function buildAnnouncementText(context) {
  const episodeNum = props.currentItemMetadata?.episode_number || 'unknown';
  const orderNum = props.currentItemMetadata?.order || 'unknown';
  const slug = props.currentItemMetadata?.slug || 'unknown';

  let announcement = `Beginning TTS Reading: Episode ${episodeNum}`;

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
}

// Play announcement with shimmer voice
async function playAnnouncement(text) {
  console.log('📢 Playing announcement:', text);

  try {
    // Try to use "shimmer" voice for announcement at 1x speed
    const audioBlob = await ttsInstance.value.synthesizeSpeech(text, {
      speaker: 'shimmer',  // Use shimmer voice for announcements
      speed: 1.0  // Normal speed (1x)
    });

    return new Promise((resolve, reject) => {
      if (!audioElement.value) {
        audioElement.value = new Audio();
      }

      const audioUrl = URL.createObjectURL(audioBlob);
      audioElement.value.src = audioUrl;

      audioElement.value.onended = () => {
        URL.revokeObjectURL(audioUrl);
        resolve();
      };

      audioElement.value.onerror = (e) => {
        URL.revokeObjectURL(audioUrl);
        reject(e);
      };

      audioElement.value.play().catch(reject);
    });
  } catch (error) {
    // Fallback: try with default voice if shimmer fails
    console.warn('⚠️ Shimmer voice failed, using default:', error.message);
    const audioBlob = await ttsInstance.value.synthesizeSpeech(text, {
      speed: 1.0
    });

    return new Promise((resolve, reject) => {
      if (!audioElement.value) {
        audioElement.value = new Audio();
      }

      const audioUrl = URL.createObjectURL(audioBlob);
      audioElement.value.src = audioUrl;

      audioElement.value.onended = () => {
        URL.revokeObjectURL(audioUrl);
        resolve();
      };

      audioElement.value.onerror = (e) => {
        URL.revokeObjectURL(audioUrl);
        reject(e);
      };

      audioElement.value.play().catch(reject);
    });
  }
}

// Play content with user's preferred voice
async function playContent(text, options) {
  console.log('🔊 Playing content with preferred voice', options);
  const synthOpts = {};
  const voice = options?.voice || activeReadingOptions.value.voice;
  const speed = Number(options?.speed || activeReadingOptions.value.speed);
  if (voice) {
    synthOpts.speaker = voice;
    synthOpts.reference_id = voice;
  }
  if (speed && Number.isFinite(speed)) synthOpts.speed = speed;
  synthOpts.chunk_length = 800;
  const audioBlob = await ttsInstance.value.synthesizeSpeech(normalizeForTts(text), synthOpts);
  return playAudioBlob(audioBlob);
}

// Low-level: play a synthesized audio blob through the shared <audio> element.
function playAudioBlob(blob) {
  return new Promise((resolve, reject) => {
    if (!audioElement.value) audioElement.value = new Audio();
    const url = URL.createObjectURL(blob);
    audioElement.value.src = url;
    audioElement.value.onended = () => { URL.revokeObjectURL(url); resolve(); };
    audioElement.value.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
    audioElement.value.play().catch(reject);
  });
}

// Normalize text for TTS so the model has a clear end-of-utterance signal —
// otherwise Fish Speech often clips the final word when chunking. Strips
// trailing whitespace, ensures a sentence-final terminator, and appends a
// trailing space as tail padding.
function normalizeForTts(text) {
  if (!text) return '';
  let t = text.toString().replace(/\s+$/, '');
  if (!t) return '';
  if (!/[.!?…]$/.test(t)) t += '.';
  return t + ' ';
}

// Synthesize one queue item using the active voice/speed (chosen in the
// pre-read modal, defaulting to josh-1 @ 1.0x). Sends a generous
// chunk_length so most paragraphs fit in one chunk (avoids tail clipping
// at chunk boundaries).
async function synthesizeReadingItem(item, options) {
  const voice = options?.voice || activeReadingOptions.value.voice || 'josh-1';
  const speed = Number(options?.speed || activeReadingOptions.value.speed || 1.0);
  return await ttsInstance.value.synthesizeSpeech(normalizeForTts(item.text), {
    speaker: voice,
    reference_id: voice,
    speed,
    chunk_length: 800
  });
}

// Play a queue of items with synthesis pipelined two steps ahead of playback,
// and playback alternated across two <audio> elements so the next blob is
// already loaded/decoded by the time the current one ends — eliminating the
// load gap between paragraphs.
async function playPipelined(items, options) {
  if (!Array.isArray(items) || items.length === 0) return;

  // Find the next speakable item starting at fromIndex and kick off its synthesis.
  const primeSynthesis = (fromIndex) => {
    for (let i = fromIndex; i < items.length; i++) {
      if (items[i].kind !== 'pause') {
        return { index: i, promise: synthesizeReadingItem(items[i], options) };
      }
    }
    return null;
  };

  // Buffer of synthesized but not yet played items: queue of {index, promise}.
  // Keep up to BUFFER_AHEAD speakable items in flight so we stay ahead of playback.
  const BUFFER_AHEAD = 3;
  const buffer = [];
  let nextPrimeStart = 0;
  const primeUpTo = () => {
    while (buffer.length < BUFFER_AHEAD) {
      const primed = primeSynthesis(nextPrimeStart);
      if (!primed) break;
      buffer.push(primed);
      nextPrimeStart = primed.index + 1;
    }
  };
  primeUpTo();

  // Two alternating <audio> elements for gapless transitions.
  const audioA = audioElement.value || (audioElement.value = new Audio());
  const audioB = new Audio();
  let playEl = audioA;
  let preloadEl = audioB;

  const loadBlobInto = (el, blob) => {
    if (el.src) {
      try { URL.revokeObjectURL(el.src); } catch (e) { /* ignore */ }
    }
    el.src = URL.createObjectURL(blob);
    el.preload = 'auto';
    try { el.load(); } catch (e) { /* ignore */ }
  };

  const playLoaded = (el) => new Promise((resolve, reject) => {
    el.onended = () => resolve();
    el.onerror = (e) => reject(e);
    el.play().catch(reject);
  });

  for (let i = 0; i < items.length; i++) {
    if (!isReadingScript.value) break;
    const item = items[i];

    if (item.kind === 'pause') {
      console.log(`🎙️ [${i}] pause ${item.ms || 200}ms`);
      await new Promise(resolve => setTimeout(resolve, item.ms || 200));
      continue;
    }

    // Find this item in the buffer (it should be the head, but be defensive).
    let entryIdx = buffer.findIndex(b => b.index === i);
    let synthPromise;
    if (entryIdx >= 0) {
      synthPromise = buffer[entryIdx].promise;
      buffer.splice(entryIdx, 1);
    } else {
      synthPromise = synthesizeReadingItem(item, options);
    }
    primeUpTo();

    let blob;
    try {
      blob = await synthPromise;
    } catch (err) {
      console.error(`❌ TTS synthesis failed for item ${i}:`, err, item);
      continue;
    }
    if (!isReadingScript.value) break;

    // Load this blob into the current playback element and start playing.
    loadBlobInto(playEl, blob);

    // Kick off preload of the NEXT speakable item's blob into the other element
    // while this one plays — this is the gap-killer.
    const nextEntry = buffer[0];
    let preloadKick;
    if (nextEntry) {
      preloadKick = nextEntry.promise.then(nextBlob => {
        if (!isReadingScript.value) return;
        loadBlobInto(preloadEl, nextBlob);
      }).catch(() => { /* failures handled when consumed */ });
    }

    try {
      await playLoaded(playEl);
    } catch (err) {
      console.error(`❌ TTS playback failed for item ${i}:`, err, item);
    }
    if (preloadKick) await preloadKick.catch(() => {});

    // Swap elements so next iteration plays from the already-loaded one.
    const tmp = playEl;
    playEl = preloadEl;
    preloadEl = tmp;
  }

  // Cleanup any lingering object URLs on both elements
  for (const el of [audioA, audioB]) {
    if (el.src) {
      try { URL.revokeObjectURL(el.src); } catch (e) { /* ignore */ }
      el.src = '';
    }
  }
  console.log('🎙️ playPipelined: finished');
}

// Insert pending cue at specific index
function insertPendingCueAtIndex(index) {
  console.log('📍 Inserting pending cue at index:', index);

  const cueBlocks = Array.isArray(pendingCueData.value) ? pendingCueData.value : [pendingCueData.value];
  const frontmatter = extractYamlFrontmatter(rawScriptContent.value);
  const contentWithoutFrontmatter = stripYamlFrontmatter(rawScriptContent.value);

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
  emitScriptContent(newRawContent);
  emit('save-current');
}

// Draggable handlers - generate stable unique keys
// Note: VueDraggable only passes the segment item, not the index
function getSegmentKey(segment) {
  console.log('🔑 getSegmentKey called:', {
    type: segment.type,
    speaker: segment.speaker,
    contentLength: segment.content?.length,
    hasId: !!segment.id,
    segmentIndex: segment.segmentIndex,
    isDragging: isDragging.value
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
    const key = `cue-${segment.data.type || 'unknown'}-${simpleHash(JSON.stringify(segment.data))}`;
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

    // For non-empty content, include index for uniqueness even with duplicate content
    const contentHash = simpleHash(content);
    const key = `text-${speaker}-${contentHash}-${segment.segmentIndex}`;
    console.log('  → Using text hash key:', key);
    return key;
  }

  // Fallback: create hash from entire segment
  return `segment-${segment.type || 'unknown'}-${simpleHash(JSON.stringify(segment))}`;
}

// Simple string hash function for generating stable keys
function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36);
}

/**
 * Handle click on a drop zone between segments.
 * Used by cross-segment placement to insert moved content at the clicked position.
 */
function selectDropZone(index) {
  if (pendingCrossContent.value) {
    // Cross-segment relocate: insert the moved content at this position
    insertContentAtIndex(index, pendingCrossContent.value);
    pendingCrossContent.value = null;
    dropZoneActive.value = false;
    pendingCueType.value = null;
    emit('save-current');
  } else {
    selectedDropZone.value = index;
  }
}

/**
 * Insert raw markdown content at a specific segment index.
 * Rebuilds the script content with the new content inserted.
 */
function insertContentAtIndex(index, markdownContent) {
  const segments = draggableSegments.value || [];
  const frontmatter = extractYamlFrontmatter(rawScriptContent.value);
  let newContent = '';

  segments.forEach((seg, i) => {
    if (i === index) {
      newContent += markdownContent + '\n\n';
    }
    if (seg.type === 'text') {
      newContent += `<p class="${seg.speaker || 'josh'}">${seg.content || ''}</p>\n\n`;
    } else if (seg.type === 'cue' && seg.data?.rawData) {
      newContent += CueParser.formatCueToMarkdown(seg.data.rawData) + '\n\n';
    }
  });

  // If inserting at the end (index === segments.length)
  if (index >= segments.length) {
    newContent += markdownContent + '\n\n';
  }

  const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim();

  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
  emit('update:scriptContent', newRawContent);
}

/**
 * Convert a parsed segment back to its markdown representation.
 * Used for cross-segment drag-and-drop serialization.
 */
function segmentToMarkdown(segment) {
  if (segment.type === 'text') {
    const speaker = segment.speaker || 'josh';
    const content = segment.content || '';
    return `<p class="${speaker}">${content}</p>`;
  } else if (segment.type === 'cue' && segment.data?.rawData) {
    return CueParser.formatCueToMarkdown(segment.data.rawData);
  }
  return '';
}

/**
 * Extract a segment's markdown and remove it from the current script.
 * Returns the extracted markdown string.
 * Used by cross-segment drag-and-drop to move content between rundown items.
 */
function extractAndRemoveSegment(segmentIndex) {
  const segments = draggableSegments.value;
  if (!segments || segmentIndex < 0 || segmentIndex >= segments.length) return null;

  const segment = segments[segmentIndex];
  const markdown = segmentToMarkdown(segment);

  // Remove the segment by rebuilding content without it
  const remaining = segments.filter((_, i) => i !== segmentIndex);
  const frontmatter = extractYamlFrontmatter(rawScriptContent.value);
  let newContent = '';
  remaining.forEach(seg => {
    if (seg.type === 'text') {
      newContent += `<p class="${seg.speaker || 'josh'}">${seg.content || ''}</p>\n\n`;
    } else if (seg.type === 'cue' && seg.data?.rawData) {
      newContent += CueParser.formatCueToMarkdown(seg.data.rawData) + '\n\n';
    }
  });

  const newRawContent = frontmatter ? `${frontmatter}\n\n${newContent.trim()}` : newContent.trim();

  // Invalidate cache and emit
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
  emit('update:scriptContent', newRawContent);
  emit('save-current');

  return markdown;
}

/**
 * Enter cross-segment placement mode.
 * Shows drop zones so user can position the incoming content.
 * Called by ContentEditor after switching to the target rundown item.
 */
function enterCrossPlacementMode(markdownContent) {
  pendingCrossContent.value = markdownContent;
  dropZoneActive.value = true;
  pendingCueType.value = 'MOVE'; // Label shown in drop zone UI
}

function handleSegmentDragStart(evt) {
  console.log('🎯 Drag start, index:', evt.oldIndex);
  isDragging.value = true;
}

function handleSegmentDragEnd(evt) {
  console.log('🎯 Drag ended:', evt.oldIndex, '→', evt.newIndex);
  isDragging.value = false;

  // Process the pending segment order that was stored during drag
  if (pendingSegmentOrder.value && evt.oldIndex !== evt.newIndex) {
    console.log('📝 Processing pending segment reorder');

    // Filter out pending cues
    const realSegments = pendingSegmentOrder.value.filter(seg => !seg.isPending);

    // Reconstruct content from the new order
    const frontmatter = extractYamlFrontmatter(rawScriptContent.value);
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
    cachedScriptSegments.value = null;
    lastParsedContent.value = null;

    // Clear pending order
    pendingSegmentOrder.value = null;

    // Now emit the update after drag is complete (with validation)
    emitScriptContent(newRawContent);
    emit('save-current');
  }
}

/**
 * Force refresh of script segments by invalidating cache.
 * Called by parent (ContentEditor) when external content changes occur,
 * such as SOT processing completion updating the cue block data.
 */
function forceRefreshSegments() {
  console.log('🔄 forceRefreshSegments called - invalidating segment cache');
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
  // Force Vue to re-evaluate the computed property
  nextTick(() => {
    console.log('🔄 Segment cache invalidated, segments will re-parse on next access');
  });
}


// ============================================================================
// Watchers
// ============================================================================
watch(() => props.currentItemMetadata, (newVal) => {

console.log('EditorPanel currentItemMetadata changed:', newVal);

}, { deep: true, immediate: true })


// Watch for item changes to clear edit buffer and cached segments
watch(() => props.item, (newVal, oldVal) => {

// If item changed (different asset_id), flush pending changes then clear buffer
const newAssetId = newVal?.asset_id || newVal?.AssetID;
const oldAssetId = oldVal?.asset_id || oldVal?.AssetID;

if (newAssetId !== oldAssetId) {
  console.log('🔄 Item changed from', oldAssetId, 'to', newAssetId);

  // CRITICAL: Flush any pending changes before switching
  // This ensures edits are not lost when clicking to a different segment
  flushPendingChanges();

  // Now clear the buffer and cache for the new item
  console.log('🧹 Clearing edit buffer and cache');
  clearEditBuffer();
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
}

})


// Watch for empty content in Script Mode and initialize with first paragraph
watch(() => props.scriptContent, (newVal, oldVal) => {

console.log('🔔 scriptContent watcher fired:', {
  newLength: newVal?.length,
  oldLength: oldVal?.length,
  editorMode: props.editorMode,
  useVisualScriptMode: useVisualScriptMode.value,
  isActivelyEditing: isActivelyEditing.value
});

// CRITICAL GUARD: Skip disruptive operations while user is actively editing or restoring cursor
// This prevents cursor loss and focus stealing during autosave
if (isActivelyEditing.value || isRestoringCursor.value) {
  console.log('⏭️ Skipping scriptContent watcher - user is actively editing or restoring cursor');
  return;
}

// CRITICAL: Clear edit buffer and cache when content changes
// This prevents stale buffered content from a previous item being displayed.
// Previously only cleared on "significant" changes (>100 chars difference),
// but that missed item switches where both items had similar content lengths.
const contentDifferent = newVal !== oldVal && oldVal !== undefined;

if (contentDifferent) {
  console.log('🧹 Clearing segmentEditBuffer and cache - content changed');
  clearEditBuffer();
  // Clear cached segments to force re-parsing
  cachedScriptSegments.value = null;
  lastParsedContent.value = null;
}

if (props.editorMode === 'script' && useVisualScriptMode.value) {
  const contentWithoutFrontmatter = stripYamlFrontmatter(newVal || '');

  // Check if content has no actual script content (only markdown headings or empty)
  const hasNoScriptContent = !contentWithoutFrontmatter ||
                             contentWithoutFrontmatter.trim() === '' ||
                             !contentWithoutFrontmatter.includes('<p');

  console.log('  hasNoScriptContent:', hasNoScriptContent);

  if (hasNoScriptContent) {
    nextTick(() => {
      createInitialParagraph();
    });
  }
}

}, { immediate: true })


// Watch scriptSegments to focus textarea after initial paragraph is rendered
watch(scriptSegments, (newSegments, oldSegments) => {

console.log('📊📊📊 ========== SCRIPTSEGMENTS WATCHER FIRED ==========');
console.log('📊 Old segments length:', oldSegments?.length);
console.log('📊 New segments length:', newSegments?.length);
console.log('📊 pendingFocusSegmentIndex:', pendingFocusSegmentIndex.value);
console.log('📊 blockReactiveUpdates:', blockReactiveUpdates.value);

// Clear stale line counts before re-measuring
segmentLineCounts.value = {};

// Observe contenteditable elements for resize-based line counting
nextTick(() => {
  if (_lineCountObserver) {
    _lineCountObserver.disconnect();
  }
  if (newSegments && newSegments.length > 0) {
    newSegments.forEach((segment, index) => {
      if (segment.type === 'text' && segment.needsParagraphTags) {
        autoResizeTextarea(index);
        // Observe for resize
        const refArr = instance.proxy.$refs[`textareaRef-${index}`];
        const el = Array.isArray(refArr) ? refArr[0] : refArr;
        if (el instanceof HTMLElement && _lineCountObserver) {
          _lineCountObserver.observe(el);
        }
      }
    });
  }
});

// REMOVED: Auto-focus behavior
// Navigation mode now requires explicit Enter key to focus
// User can navigate with arrow keys without being pulled into editing mode

// Auto-resize all textareas after segments change
nextTick(() => {
  if (newSegments && newSegments.length > 0) {
    newSegments.forEach((segment, index) => {
      if (segment.type === 'text') {
        autoResizeTextarea(index);

        // Mark paragraphs with content as "already edited" so they show yellow highlight on first click
        if (segment.content && segment.content.trim() !== '') {
          paragraphEditStates.value[index] = true;
        }
      }
    });
  }

  // Focus pending segment if one was requested (e.g., after creating new paragraph)
  if (pendingFocusSegmentIndex.value !== null) {
    const segmentIndex = pendingFocusSegmentIndex.value;
    console.log('🎯🎯🎯 FOCUS LOGIC TRIGGERED for segment:', segmentIndex);
    console.log('🎯 Current segments count:', newSegments?.length);
    console.log('🎯 Target segment exists:', !!newSegments?.[segmentIndex]);
    console.log('🎯 All template refs:', Object.keys(instance.proxy.$refs).filter(k => k.startsWith('textareaRef')));

    // CRITICAL FIX: Clear the pending flag IMMEDIATELY to prevent multiple attempts
    // Store it locally for this focus attempt
    const targetIndex = segmentIndex;
    pendingFocusSegmentIndex.value = null;

    // Try multiple times to ensure textarea is fully rendered
    const tryFocus = (attempts = 0) => {
      if (attempts > 15) {
        console.log('❌❌❌ FAILED to focus segment', targetIndex, 'after 15 attempts');
        console.log('❌ Final refs check:', Object.keys(instance.proxy.$refs).filter(k => k.startsWith('textareaRef')));
        console.log('❌ Final segments count:', scriptSegments.value?.length);
        return;
      }

      const refName = `textareaRef-${targetIndex}`;
      const textareaRef = instance.proxy.$refs[refName];

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
    nextTick(() => {
      nextTick(() => {
        console.log('🎯 Starting focus retry loop after double nextTick');
        tryFocus();
      });
    });
  }
});

})


// Watch calculated duration and emit to parent for metadata update
watch(calculatedItemDuration, (newDuration) => {

emit('duration-calculated', newDuration);

}, { immediate: true })



// ============================================================================
// Lifecycle: onMounted
// ============================================================================
onMounted(() => {
  console.log('EditorPanel mounted with metadata:', props.currentItemMetadata);

  // Wire up useScriptCore draggable handlers
  setPendingCueContextGetter(() => ({
  pendingCueData: pendingCueData.value,
  showCuePlacement: showCuePlacement.value
  }));
  setDraggableSetHandler((newSegments) => {
  // CRITICAL FIX: Don't emit updates during active drag operations
  if (isDragging.value) {
    pendingSegmentOrder.value = newSegments;
    return;
  }

  // Check if pending cue was moved (no longer at end)
  const pendingIndex = newSegments.findIndex(seg => seg.isPending);

  if (pendingIndex !== -1 && pendingIndex < newSegments.length - 1) {
    insertPendingCueAtIndex(pendingIndex);
    pendingCueData.value = null;
    showCuePlacement.value = false;
  } else {
    // Normal reorder without pending cue
    const realSegments = newSegments.filter(seg => !seg.isPending);
    const frontmatter = extractYamlFrontmatter(rawScriptContent.value);
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
    emitScriptContent(newRawContent);
    emit('save-current');
  }
  });

  // Auto-resize all textareas on mount if scriptSegments exist
  nextTick(() => {
  if (scriptSegments.value && scriptSegments.value.length > 0) {
    scriptSegments.value.forEach((segment, index) => {
      if (segment.type === 'text' && segment.needsParagraphTags) {
        autoResizeTextarea(index);
      }
    });
  }
  });

  // Use ResizeObserver to keep line counts accurate — fires when contenteditable
  // elements actually change size (after layout settles, window resize, etc.)
  _lineCountObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    const el = entry.target;
    const segIndex = parseInt(el.dataset.segIndex, 10);
    if (isNaN(segIndex)) continue;
    const lineHeight = 27;
    const lineCount = Math.max(1, Math.round(entry.contentRect.height / lineHeight));
    if (segmentLineCounts.value[segIndex] !== lineCount) {
      segmentLineCounts.value[segIndex] = lineCount;
    }
  }
  });

  // Initialize TTS
  try {
  ttsInstance.value = useTts();
  if (ttsInstance.value && !ttsInstance.value.ttsConfig?.value?.enabled) {
    ttsInstance.value.loadTtsConfig().catch(err => {
      console.error('Failed to load TTS config:', err);
    });
  }
  } catch (error) {
  console.error('Failed to initialize TTS:', error);
  }

  // Start periodic autoscrub (every 30 seconds)
  startAutoscrubTimer();

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
  colorLoadTrigger.value++;
  console.log('🎨 Color load trigger incremented:', colorLoadTrigger.value);
  });

  // Register hotkeys with the global hotkey reference
  const { registerHotkeys, setActiveSection } = useHotkeys();
  setActiveSection('Content Editor');
  registerHotkeys('Content Editor', [
  { keys: 'Ctrl + S', description: 'Save all changes', category: 'Editing' },
  { keys: 'Ctrl + Z', description: 'Undo', category: 'Editing' },
  { keys: 'Ctrl + Y', description: 'Redo', category: 'Editing' },
  { keys: 'Ctrl + B', description: 'Bold text', category: 'Formatting' },
  { keys: 'Ctrl + I', description: 'Italic text', category: 'Formatting' },
  { keys: 'Ctrl + U', description: 'Underline text', category: 'Formatting' },
  { keys: 'Ctrl + Alt + H', description: 'Highlight text', category: 'Formatting' },
  { keys: 'Alt + /', description: 'Propose revision (cut/replace)', category: 'Editing' },
  { keys: 'Alt + .', description: 'Propose addition (insert text)', category: 'Editing' },
  { keys: 'Alt + C', description: 'Toggle cue selector menu', category: 'Cue Insertion' },
  { keys: 'Alt + D', description: 'Insert DIR cue', category: 'Cue Insertion' },
  { keys: 'Alt + F', description: 'Insert FSQ cue', category: 'Cue Insertion' },
  { keys: 'Alt + G', description: 'Insert GFX cue', category: 'Cue Insertion' },
  { keys: 'Alt + I', description: 'Insert IMG cue', category: 'Cue Insertion' },
  { keys: 'Alt + J', description: 'Insert LIVE cue', category: 'Cue Insertion' },
  { keys: 'Alt + M', description: 'Insert MUS cue', category: 'Cue Insertion' },
  { keys: 'Alt + N', description: 'Insert NAT cue', category: 'Cue Insertion' },
  { keys: 'Alt + P', description: 'Insert PKG cue', category: 'Cue Insertion' },
  { keys: 'Alt + R', description: 'Insert RIF cue', category: 'Cue Insertion' },
  { keys: 'Alt + S', description: 'Insert SOT cue', category: 'Cue Insertion' },
  { keys: 'Alt + V', description: 'Insert VO cue', category: 'Cue Insertion' },
  { keys: 'Alt + W', description: 'Insert VOX cue', category: 'Cue Insertion' },
  { keys: 'Alt + X', description: 'Insert STING cue', category: 'Cue Insertion' },
  { keys: 'Alt + Y', description: 'Insert BUMP cue', category: 'Cue Insertion' },
  { keys: 'Alt + Shift + A', description: 'Regenerate cue AssetID', category: 'Cue Insertion' },
  { keys: 'Ctrl + Shift + X', description: 'Toggle TTS script reading', category: 'Playback' },
  { keys: 'Ctrl + Shift + C', description: 'Toggle collapse mode', category: 'View' },
  { keys: 'Ctrl + Shift + [', description: 'Toggle left sidebar (rundown)', category: 'View' },
  { keys: 'Ctrl + Shift + ]', description: 'Toggle right sidebar (metadata)', category: 'View' },
  ]);

  // Add global hotkey listeners
  console.log('🎪 Adding global hotkey listeners');
  document.addEventListener('keydown', handleGlobalKeydown);
  document.addEventListener('keyup', handleGlobalKeyup);

  // Reset ALT key state when window loses focus (prevents stuck ALT key)
  window.addEventListener('blur', handleWindowBlur);

  // Add keyboard listener for cursor character cleanup
  document.addEventListener('keydown', handleCursorCharacterKeydown);

  // Load cue card alignment from settings (do this LAST to avoid reactivity loops)
  nextTick(() => {
  loadCueCardAlignment();
  });

  // Add scroll listener for flag note positioning
  window.addEventListener('scroll', handleScrollForFlagNotes, true);
})

// ============================================================================
// Lifecycle: onUnmounted
// ============================================================================
onUnmounted(() => {
  // Unregister hotkeys
  const { unregisterHotkeys } = useHotkeys();
  unregisterHotkeys('Content Editor');

  // Clean up ResizeObserver for line counts
  if (_lineCountObserver) {
  _lineCountObserver.disconnect();
  _lineCountObserver = null;
  }
  // Clean up scroll listener for flag notes
  window.removeEventListener('scroll', handleScrollForFlagNotes, true);
  // Clean up event listeners
  document.removeEventListener('keydown', handleGlobalKeydown);
  document.removeEventListener('keyup', handleGlobalKeyup);
  document.removeEventListener('keydown', handleCursorCharacterKeydown);
  window.removeEventListener('blur', handleWindowBlur);
  if (autoscrubTimer.value) {
  clearInterval(autoscrubTimer.value);
  }

  // Clean up audio element
  if (audioElement.value) {
  audioElement.value.pause();
  audioElement.value.removeEventListener('ended', handleAudioEnd);
  audioElement.value.removeEventListener('error', handleAudioError);
  if (audioElement.value.src) {
    URL.revokeObjectURL(audioElement.value.src);
  }
  audioElement.value = null;
  }

})

// ============================================================================
// Lifecycle: onBeforeUnmount
// ============================================================================
onBeforeUnmount(() => {
  // CRITICAL: Flush any pending changes before unmount to prevent data loss
  flushPendingChanges();

  // Clean up timers
  stopAutoscrubTimer();
  clearAutoscrubDebounce();
})

// ============================================================================
// Cursor memory: capture/restore the user's caret inside script-mode
// paragraphs so flicking between segments lands them where they left off.
// Called by ContentEditor on segment switch via the editorPanel ref.
// ============================================================================

function _findActiveParagraphElement() {
  // The browser's selection might be inside any descendant of a
  // .paragraph-content. Walk up to find the wrapper.
  const sel = window.getSelection && window.getSelection()
  if (!sel || sel.rangeCount === 0) return null
  let node = sel.anchorNode
  while (node && node !== document.body) {
    if (node.nodeType === 1 && node.classList && node.classList.contains('paragraph-content')) {
      return node
    }
    node = node.parentNode
  }
  return null
}

function _paragraphIndexOfElement(el) {
  if (!el) return null
  // Look for `seg-N` class set in the template (one of our paragraph classes).
  for (const cls of el.classList) {
    const m = /^seg-(\d+)$/.exec(cls)
    if (m) return Number(m[1])
  }
  // Fallback: index among siblings with the same class.
  const siblings = el.parentElement ? Array.from(el.parentElement.querySelectorAll('.paragraph-content')) : []
  const i = siblings.indexOf(el)
  return i >= 0 ? i : null
}

function _charOffsetWithin(el, anchorNode, anchorOffset) {
  // Walk text nodes in `el` and accumulate their lengths until we hit
  // the anchor. Returns total characters before the caret.
  if (!el) return 0
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null)
  let count = 0
  let node = walker.nextNode()
  while (node) {
    if (node === anchorNode) return count + anchorOffset
    count += node.nodeValue ? node.nodeValue.length : 0
    node = walker.nextNode()
  }
  return count
}

function captureCursorMemoryPosition() {
  try {
    const para = _findActiveParagraphElement()
    if (!para) return null
    const sel = window.getSelection()
    const paragraphIndex = _paragraphIndexOfElement(para) ?? focusedParagraphIndex.value
    const charOffset = _charOffsetWithin(para, sel.anchorNode, sel.anchorOffset)
    if (paragraphIndex == null) return null
    return { paragraphIndex, charOffset }
  } catch {
    return null
  }
}

function _findParagraphByIndex(index) {
  if (index == null) return null
  // Prefer exact seg-N class match.
  const exact = document.querySelector(`.paragraph-content.seg-${index}`)
  if (exact) return exact
  // Fallback by ordinal position.
  const all = document.querySelectorAll('.paragraph-content')
  return all[index] || null
}

function _setCaretAtCharOffset(el, targetOffset) {
  if (!el) return false
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null)
  let count = 0
  let node = walker.nextNode()
  while (node) {
    const len = node.nodeValue ? node.nodeValue.length : 0
    if (count + len >= targetOffset) {
      const range = document.createRange()
      range.setStart(node, Math.max(0, targetOffset - count))
      range.collapse(true)
      const sel = window.getSelection()
      sel.removeAllRanges()
      sel.addRange(range)
      return true
    }
    count += len
    node = walker.nextNode()
  }
  // Past the end → put at last position.
  el.focus && el.focus()
  return false
}

function restoreCursorMemoryPosition(position) {
  if (!position) return false
  const { paragraphIndex, charOffset } = position
  // Wait two ticks: one for Vue to render the new content, one for the
  // browser to lay it out so getBoundingClientRect / TreeWalker work.
  return new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const para = _findParagraphByIndex(paragraphIndex)
      if (!para) { resolve(false); return }
      // Make the contenteditable focusable; some paragraphs are wrappers
      // around an inner contenteditable. Find the editable child if needed.
      const editable = para.querySelector('[contenteditable="true"]') || para
      try { editable.focus() } catch { /* noop */ }
      const ok = _setCaretAtCharOffset(editable, charOffset || 0)
      // Track focused index so any UI affordances tied to it light up.
      focusedParagraphIndex.value = paragraphIndex
      lastKnownParagraphIndex.value = paragraphIndex
      resolve(ok)
    }))
  })
}

// ============================================================================
// defineExpose
// ============================================================================
defineExpose({
  activelyEditingSegment,
  cachedScriptSegments,
  captureSegmentCursor: captureCursorMemoryPosition,
  restoreSegmentCursor: restoreCursorMemoryPosition,
  enterCrossPlacementMode,
  extractAndRemoveSegment,
  flushPendingChanges,
  focusSlugField,
  focusedParagraphIndex,
  forceRefreshSegments,
  handleBumpCueSubmit,
  handleDirCueSubmit,
  handleNatCueSubmit,
  handlePkgCueSubmit,
  handleRifCueSubmit,
  handleSotCueSubmit,
  handleStingCueSubmit,
  handleVoCueSubmit,
  hasLocalUnsavedChanges,
  insertCueAtSnapshotPosition,
  isActivelyEditing,
  isReadingScript,
  isTtsConfigured,
  lastParsedContent,
  pendingCueData,
  pendingCueType,
  pendingPlacement,
  rawScriptContent,
  reconstructRawContent,
  requestNewEpisodeAssetID,
  restoreCursorPosition,
  savedCursorState,
  scriptSegments,
  segmentEditBuffer,
  segmentReparseKey,
  selectSegment,
  showAssetIDInfo,
  showCuePlacement,
  toggleCueMenu,
  toggleScriptReading,
  // Save-integrity controls
  shrinkGuardEnabled,
  setShrinkGuardEnabled,
  allowNextShrink,
  // Dynamically created by parent
  pendingCueDataArray: undefined,
  pendingFsqDataArray: undefined,
})
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

/* Banner shown when another user is currently editing the same segment.
   Sits flush at the top, gentle amber tint so it's noticeable but not
   alarming. */
.presence-banner {
  display: flex;
  align-items: center;
  background: rgba(255, 152, 0, 0.10);
  border-bottom: 1px solid rgba(255, 152, 0, 0.35);
  padding: 4px 10px;
  font-size: 0.78rem;
  color: #6d4c00;
  flex-wrap: wrap;
}
.presence-banner-text {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
}
.presence-banner-chip {
  font-weight: 600 !important;
  letter-spacing: 0.2px !important;
}

/* Segment Locked Overlay */
.paste-processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 30, 30, 0.88);
  backdrop-filter: blur(3px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.paste-processing-content {
  text-align: center;
  color: white;
  padding: 40px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 16px;
  border: 1px solid rgba(255, 193, 7, 0.3);
  max-width: 400px;
}

.paste-processing-title {
  font-size: 1.1rem;
  font-weight: 500;
  margin-top: 20px;
  line-height: 1.5;
  color: #ffc107;
}

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
  background-color: white !important;
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
  background-color: #f7f4ef;
  border: 1px dotted rgba(0, 0, 0, 0.2);
  margin: 4px;
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
  background: transparent !important;
  margin: 0 16px !important;
  min-height: calc(100vh - 200px) !important;
  overflow-y: auto !important;
  text-indent: 8px !important;
}

.editor-textarea.scratch-mode {
  font-family: 'Roboto', sans-serif !important;
  color: var(--v-medium-emphasis-opacity);
}

/* Make all Vuetify field wrappers transparent for paper effect */
:deep(.editor-textarea .v-field),
:deep(.editor-textarea .v-field__overlay),
:deep(.editor-textarea .v-input__control),
.editor-content :deep(.v-field),
.editor-content :deep(.v-field__overlay),
.editor-content :deep(.v-card),
.editor-content :deep(.v-card-text) {
  background: transparent !important;
}

/* Script Mode Header Fields */
.script-content-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 180px);
  background: transparent;
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

.code-mode-container {
  /* Fill remaining viewport height so short content still stretches to the
     bottom. Auto-grow will extend the textarea further when content is long,
     and the page (not the textarea) handles the overflow scroll. */
  min-height: calc(100vh - 220px);
  height: auto;
  display: flex;
  flex-direction: column;
}

.code-textarea {
  font-family: 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  padding: 0 !important;
  margin: 0 !important;
  background-color: white;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 260px);
}

/* Let the field wrapper fill the container and grow with content. */
.code-textarea :deep(.v-input__control),
.code-textarea :deep(.v-field),
.code-textarea :deep(.v-field__field),
.code-textarea :deep(.v-field__input) {
  height: auto !important;
  max-height: none !important;
  min-height: 100vh !important;
  overflow: visible !important;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.code-textarea :deep(textarea) {
  font-family: 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  padding: 16px 16px 50vh 16px !important; /* huge bottom padding keeps the
       editable region reaching the viewport bottom even when scrolled to the
       end of the content */
  min-height: 100vh !important;
  height: auto !important;
  overflow: hidden !important; /* auto-grow sizes it; page scrolls when long */
  resize: none !important;
  box-sizing: border-box !important;
  flex: 1 1 auto;
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
  background-color: white !important;
  border-bottom: none !important;
  padding: 6px 8px !important;
  box-shadow: none !important;
}

/* Sticky Cues Toolbar */
.cues-toolbar-sticky {
  position: sticky !important;
  top: 62px !important; /* Position below the main toolbar (48px + padding) */
  z-index: 9 !important;
  background-color: rgba(0, 0, 0, 0.03) !important;
  border-bottom: none !important;
  padding: 6px 8px !important;
  box-shadow: none !important;
}

/* Sticky Text Formatting Box */
.text-formatting-sticky {
  position: sticky !important;
  top: 120px !important;
  z-index: 8 !important;
  background-color: rgba(0, 0, 0, 0.03) !important;
}

/* Button Group Wrapper */
.btn-group-wrapper {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  margin: 0 4px;
}

.btn-group-label {
  font-size: 7px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #9e9e9e;
  line-height: 1;
  margin-bottom: 1px;
}

.btn-group-buttons {
  display: inline-flex;
  gap: 0;
}

.btn-group-buttons .mode-btn {
  min-width: 60px !important;
}

/* Toolbar Mode Button Styling */
.editor-mode-toggle {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
}

.mode-btn {
  background-color: #f5f5f5 !important;
  color: #757575 !important;
  border: 1px solid #bdbdbd !important;
  height: 24px !important;
  min-height: 24px !important;
  min-width: 80px !important;
  padding: 2px 8px !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
  font-size: 0.75rem !important;
}

.mode-btn:hover {
  background-color: #eeeeee !important;
  color: #424242 !important;
  border-color: #9e9e9e !important;
}

.mode-btn.v-btn--active {
  background-color: #4CAF50 !important;
  color: #ffffff !important;
  border: 1px solid #388E3C !important;
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

.autoscrub-section {
  min-width: 80px;
}

.autoscrub-status {
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
.tts-read-btn {
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
  color: inherit !important;
}

.hotkey-display strong {
  font-weight: 700 !important;
  color: inherit !important;
}

.cue-pipe {
  font-size: 0.6rem !important;
  opacity: 0.5;
  margin: 0 1px;
  color: inherit !important;
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
/* Styles flyout */
.styles-flyout-container {
  display: flex;
  align-items: center;
  padding: 2px 8px;
}

.styles-toggle-btn {
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  color: rgba(80, 80, 80, 0.8) !important;
  min-width: 0 !important;
  padding: 0 6px !important;
}

.styles-toggle-btn .v-icon {
  transition: transform 0.2s ease;
}

.styles-toggle-btn .rotate-90 {
  transform: rotate(90deg);
}

.styles-flyout-items {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: 4px;
}

.flyout-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.flyout-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.flyout-enter-from {
  opacity: 0;
  transform: translateX(-8px);
}
.flyout-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

.formatting-hotkey {
  font-family: 'Helvetica', 'Arial', sans-serif !important;
  font-size: 10px !important;
  font-weight: 500 !important;
  color: rgba(80, 80, 80, 0.9) !important;
  white-space: nowrap !important;
}

.formatting-hotkey strong {
  font-weight: 700 !important;
  color: rgba(60, 60, 60, 1) !important;
}

/* Auto-sizing Cue Toolbar inside Editor Content */
.editor-cues-toolbar {
  position: sticky !important;
  top: 62px !important; /* Below the mode toolbar (48px + padding) */
  z-index: 9 !important;
  width: 100% !important;
  background-color: rgba(0, 0, 0, 0.03) !important;
  border-bottom: none !important;
  padding: 6px 8px !important;
  box-shadow: none !important;
}

/* Cue toolbar row — trigger + expandable buttons */
.cue-toolbar-row {
  display: flex;
  align-items: stretch;
  gap: 4px;
  width: 100%;
}

.add-cue-trigger {
  flex-shrink: 0;
  min-width: 90px !important;
  height: auto !important;
  min-height: 24px !important;
  padding: 1px 8px !important;
  border-radius: 0 !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-size: 0.7rem !important;
  transition: all 0.2s ease !important;
}

.add-cue-trigger .add-cue-label {
  font-weight: 700;
  margin-right: 4px;
}

.add-cue-trigger .add-cue-hotkey {
  font-size: 0.55rem;
  opacity: 0.6;
}

.add-cue-trigger .v-icon {
  transition: transform 0.25s ease;
}

.add-cue-trigger .rotate-90 {
  transform: rotate(90deg);
}

.add-cue-active {
  background-color: rgba(255, 255, 255, 0.15) !important;
}

.cue-buttons-flex-container {
  display: flex;
  align-items: stretch;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

/* Expand transition */
.cue-expand-enter-active {
  transition: all 0.25s ease-out;
}
.cue-expand-leave-active {
  transition: all 0.15s ease-in;
}
.cue-expand-enter-from {
  opacity: 0;
  max-width: 0;
  transform: scaleX(0);
  transform-origin: left;
}
.cue-expand-enter-to {
  opacity: 1;
  max-width: 2000px;
  transform: scaleX(1);
}
.cue-expand-leave-from {
  opacity: 1;
  max-width: 2000px;
  transform: scaleX(1);
}
.cue-expand-leave-to {
  opacity: 0;
  max-width: 0;
  transform: scaleX(0);
  transform-origin: left;
}

/* Flash animation on single-key cue selection */
@keyframes cue-flash {
  0% { filter: brightness(1); transform: scale(1); }
  50% { filter: brightness(2); transform: scale(1.08); }
  100% { filter: brightness(1); transform: scale(1); }
}

.cue-btn-flash {
  animation: cue-flash 0.2s ease-out !important;
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
  height: auto !important;
  min-height: 24px !important;
  padding: 1px 3px !important;
  border-radius: 0 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.2s ease !important;
  overflow: hidden !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.cue-btn-flex .v-btn__content {
  width: 100%;
  height: 100%;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.cue-btn-flex:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
}

.cue-btn-content-flex {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  align-content: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 0 3px;
  overflow: hidden;
}

/* Pipe hidden inside flex buttons — gap provides separation */
.cue-btn-content-flex .cue-pipe {
  display: none;
}

.cue-btn-content-flex .cue-label {
  font-size: 0.75rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.3px !important;
  line-height: 1.2 !important;
  color: inherit !important;
  white-space: nowrap;
}

.cue-btn-content-flex .hotkey-display {
  font-size: 0.6rem !important;
  opacity: 1 !important;
  line-height: 1.2 !important;
  font-weight: 600 !important;
  color: inherit !important;
  text-shadow: none !important;
  letter-spacing: 0.3px !important;
  white-space: nowrap;
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
  background: transparent !important;
}

/* Multi-Selection Toolbar - Fixed Overlay */
.multi-selection-toolbar {
  position: fixed;
  top: 160px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background-color: rgba(30, 30, 30, 0.92);
  border: none;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  min-width: 280px;
}

.selection-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.selection-count-number {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

.selection-count-label {
  font-size: 0.85rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.7);
}

.selection-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Segment title at top of script area */
.segment-title-header {
  padding: 16px 40px 4px 40px;
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 1.4rem;
  font-weight: 700;
  color: #333;
  letter-spacing: -0.3px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  margin: 0 0 0 0;
  background-color: rgba(0, 0, 0, 0.03);
}

.segment-title-placeholder {
  color: #bbb;
  font-weight: 400;
  font-style: italic;
}

/* Visual Script Mode Styling */
.visual-script-container {
  padding: 20px 40px 20vh 40px;
  background-color: transparent;
  font-family: 'Times New Roman', serif;
  font-size: 14px;
  line-height: 1.5;
  height: auto;
  min-height: calc(100vh - 250px);
  max-height: none;
  overflow: visible;
}

/* Scroll zone indicators during drag */
.scroll-zone-indicator {
  position: fixed;
  left: 0;
  right: 0;
  background-color: #FFF9C4;
  pointer-events: none;
  z-index: 999;
}

.scroll-zone-upper {
  top: 0;
  height: 220px;
  border-bottom: 4px dotted #FFD54F;
}

.scroll-zone-lower {
  bottom: 0;
  height: 80px;
  border-top: 4px dotted #FFD54F;
}

/* Speaker Paragraph Styling */
.speaker-paragraph {
  margin: 0 0 21px 0;
  background-color: transparent;
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
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  /* Per-user knobs (Settings → Interface → Editor Display) */
  font-size: var(--editor-script-font-size, inherit);
  line-height: var(--editor-script-line-height, inherit);
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

/* Speaker-specific backgrounds - subtle tint on paper */
.speaker-bg-josh,
.speaker-bg-guest,
.speaker-bg-caller,
.speaker-bg-announcer,
.speaker-bg-narrator,
.speaker-bg-host {
  /* Paper color fallback — dynamic color applied via getParagraphBackgroundStyle */
  background-color: rgba(255, 236, 179, 0.08);
}

/* Override speaker backgrounds when focused or saved - must be after speaker-bg classes */
.paragraph-content.paragraph-focused {
  background-color: rgba(255, 235, 59, 0.2) !important; /* Light highlight when focused */
}

.paragraph-content.paragraph-saved {
  background-color: rgba(76, 175, 80, 0.5) !important; /* Green flash on save */
}

/* Invalid cue pattern: red background, white bold text */
.paragraph-content.paragraph-invalid-cue {
  background-color: #b71c1c !important;
  position: relative;
}

.paragraph-content.paragraph-invalid-cue .speaker-textarea,
.paragraph-content.paragraph-invalid-cue .speaker-contenteditable {
  color: white !important;
  font-weight: 700 !important;
}

.invalid-cue-overlay {
  position: absolute;
  bottom: 2px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 5;
}

.invalid-cue-warning {
  font-size: 0.7rem;
  font-weight: 700;
  color: #000 !important;
  letter-spacing: 0.03em;
}

.invalid-cue-fix-btn {
  font-size: 0.65rem !important;
  font-weight: 700;
}

/* LegacyCueConvertButton sits next to the warning span in the overlay.
   Force the label text to black so it pairs visually with the warning. */
.invalid-cue-overlay .legacy-cue-convert-btn,
.invalid-cue-overlay .legacy-cue-convert-btn :deep(.v-btn__content) {
  color: #000 !important;
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
  background-color: rgba(255, 235, 59, 0.2) !important;
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
.paragraph-add-btn:hover,
.cue-add-paragraph-btn:hover {
  opacity: 1 !important;
}

/* Add Paragraph button on cue blocks */
.cue-add-paragraph-btn {
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

/* Clean textarea styling */
.speaker-textarea {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 17pt;
  line-height: 1.5;
  padding: 0;
  background-color: transparent !important;
}

/* Contenteditable div styling - renders HTML formatting */
.speaker-contenteditable {
  flex: 1;
  min-width: 0;
  min-height: 1.5em;
  padding: 2px 5px !important;
  outline: none;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  cursor: text;
  font-family: 'Georgia', 'Times New Roman', serif;
  color: #000000 !important;
  font-weight: normal;
  -webkit-font-smoothing: auto;
  -moz-osx-font-smoothing: auto;
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
  color: #555;
  font-style: normal;
  font-weight: 400;
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

/* Revision toolbar (scoped — template element) */
.rev-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4px;
  margin-top: 2px;
  margin-left: 0;
}

.rev-toolbar-count {
  font-weight: 600;
  color: rgba(80, 80, 80, 0.9);
  font-size: 11px;
}

/* Revision entry bar — floats over content */
.rev-entry-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(240, 253, 240, 0.97);
  border: 1px solid rgba(76, 175, 80, 0.4);
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  position: absolute;
  left: 40px;
  right: 0;
  bottom: -44px;
  z-index: 10;
}

.rev-entry-label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(80, 80, 80, 0.9);
  white-space: nowrap;
}

.rev-entry-input {
  flex: 1;
  border: 1px solid rgba(76, 175, 80, 0.4);
  background: rgba(76, 175, 80, 0.1);
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 15px;
  outline: none;
  font-family: inherit;
  min-height: 36px;
}

.rev-entry-input:focus {
  border-color: #4caf50;
  background: rgba(76, 175, 80, 0.15);
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
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
  background-color: transparent;
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
  user-select: none;
  touch-action: none;
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

<!-- Unscoped: targets browser-injected DOM inside contenteditable (invisible to Vue scoping) -->
<style>
.speaker-contenteditable > br:last-child {
  display: none;
}

/* Revision system styles — unscoped so dynamically injected custom elements get styled */
.speaker-contenteditable rev-block {
  display: inline;
  position: relative;
}

.speaker-contenteditable rev-kill {
  text-decoration: line-through;
  background-color: rgba(244, 67, 54, 0.15);
  padding: 0 2px;
  border-radius: 2px;
}

.speaker-contenteditable rev-add {
  background-color: rgba(76, 175, 80, 0.2);
  padding: 0 2px;
  border-radius: 2px;
}

.speaker-contenteditable rev-actions {
  display: inline-flex;
  gap: 2px;
  margin-left: 4px;
  vertical-align: middle;
}

.speaker-contenteditable rev-meta {
  font-size: 10px;
  color: #888;
  font-style: italic;
  margin-right: 4px;
  vertical-align: middle;
}

.speaker-contenteditable rev-btn {
  cursor: pointer;
  border: none;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
  padding: 0;
  vertical-align: middle;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.speaker-contenteditable rev-btn[data-rev-action="accept"] {
  background-color: rgba(76, 175, 80, 0.3);
  color: #2e7d32;
}

.speaker-contenteditable rev-btn[data-rev-action="accept"]:hover {
  background-color: rgba(76, 175, 80, 0.5);
}

.speaker-contenteditable rev-btn[data-rev-action="reject"] {
  background-color: rgba(244, 67, 54, 0.2);
  color: #c62828;
}

.speaker-contenteditable rev-btn[data-rev-action="reject"]:hover {
  background-color: rgba(244, 67, 54, 0.4);
}
</style>
