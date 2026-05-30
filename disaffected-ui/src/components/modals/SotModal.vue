<template>
  <!-- Outside-the-modal overlays — extracted into MediaModalOverlays
       shared component. Renders only when show && mediaUrl. -->
  <MediaModalOverlays
    :show="show"
    :media-loaded="!!mediaUrl"
    :current-timecode="currentTimecode"
    :remaining-timecode="remainingTimecode"
    :current-action-display="currentActionDisplay"
    :trim-start="trimStart"
    :trim-end="trimEnd"
    :clip-duration="clipDuration"
    :show-speed-indicator="showSpeedIndicator"
    :playback-speed="playbackSpeed"
    :speed-label="speedLabel"
    :show-frame-counter="showFrameCounter"
    :current-frame-number="currentFrameNumber"
    :total-frames="totalFrames"
    :frame-step-direction="frameStepDirection"
    :thumbnail-timecode="thumbnailTimecode"
    :clipping-method="clippingMethod"
    :clips="clips"
    :clip-slug="clipSlug"
    :slug="slug"
    v-model:show-hotkeys="showHotkeys"
    @remove-clip="removeClip"
    @update-clip-slug="(p) => { clips[p.index].slug = p.slug }"
  />

  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    max-width="800px"
    persistent
    class="sot-modal"
    style="z-index: 9999;"
  >
    <!-- Full Modal Container with 70% transparent overlay -->
    <v-card ref="modalCardRef" class="sot-modal-card" style="max-height: 80vh; overflow: hidden;">
      <!-- Collapsible Error at Top -->
      <div
        ref="topErrorEl"
        class="top-error"
        style="background: #ff4444; color: white; height: 0; overflow: hidden; transition: all 0.3s ease; font-weight: bold; text-align: center; border-radius: 4px 4px 0 0;"
      ></div>

      <!-- Header with Title and Close Buttons -->
      <div class="modal-header d-flex justify-space-between align-center pa-3" style="padding: 10px 15px;">
        <h2 class="text-uppercase font-weight-bold ma-0" style="font-size: 1.2em;">{{ editMode ? 'EDIT SOT CUE' : 'NEW SOT CUE' }}</h2>
        <div class="d-flex" style="gap: 5px;">
          <v-btn
            @click="cancel"
            size="x-small"
            color="#ff4444"
            variant="flat"
            tabindex="-1"
            style="color: white; min-width: 30px; height: 36px; font-size: 16px; font-weight: bold;"
            title="Close modal"
          >✕</v-btn>
          <v-btn
            @click="cancel"
            size="x-small"
            color="#666"
            variant="flat"
            tabindex="-1"
            style="color: white; height: 36px; font-size: 10px; font-weight: bold; padding: 6px 11px;"
            title="Press ESC to close"
          >ESC</v-btn>
        </div>
      </div>

      <!-- Interior Container with light grey background -->
      <v-card-text
        class="pa-5 interior-container"
        style="background-color: #f0f0f0; max-height: calc(80vh - 60px); overflow-y: auto; padding: 20px !important;"
      >
        <v-form ref="sotFormRef">
          <!-- Type of Cut Selection (moved to top for workflow clarity) -->
          <div class="mb-4">
            <label class="cue-modal-label mb-2 d-block" style="font-size: 14px; font-weight: 600; color: #333;">Type of Cut:</label>

            <!-- Helper text (shown when Tab-navigating through buttons) -->
            <transition name="fade">
              <div
                v-if="showCutModeHelp && focusedCutMode"
                style="color: #1976D2; font-size: 12px; margin-bottom: 6px; font-style: italic; min-height: 18px;"
              >{{ cutModeDescriptions[focusedCutMode] }}</div>
            </transition>

            <div class="clipping-grid-container" style="width: 100%;">
              <div class="clipping-row d-flex mb-0" style="gap: 1px;">
                <!-- None Button -->
                <div
                  ref="firstCutModeButtonRef"
                  tabindex="0"
                  @click="selectCutMode('none')"
                  @focus="handleCutModeFocus('none')"
                  @blur="handleCutModeBlur"
                  @keydown="handleCutModeKeydown($event, 'none')"
                  @mouseenter="e => hoverButton(e, '#2196F3')"
                  @mouseleave="e => unhoverButton(e, '#2196F3')"
                  class="grid-btn clipping-btn"
                  :style="{
                    width: '20%',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: focusedCutMode === 'none' ? selectionColor : (clippingMethod === 'none' ? '#1565C0' : '#2196F3'),
                    border: focusedCutMode === 'none' ? '2px solid white' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    overflow: 'hidden',
                    boxShadow: clippingMethod === 'none' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                    transform: clippingMethod === 'none' ? 'translateY(2px)' : 'none',
                    color: focusedCutMode === 'none' ? 'black' : 'white',
                    fontSize: '13px',
                    fontWeight: 'bold',
                    textShadow: focusedCutMode === 'none' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                    outline: 'none'
                  }"
                  title="No clipping - use full video [N]"
                ><span style="text-decoration: underline;">N</span>ONE</div>
                <!-- Single Trim Button -->
                <div
                  tabindex="0"
                  @click="selectCutMode('single-trim')"
                  @focus="handleCutModeFocus('single-trim')"
                  @blur="handleCutModeBlur"
                  @keydown="handleCutModeKeydown($event, 'single-trim')"
                  @mouseenter="e => hoverButton(e, '#2196F3')"
                  @mouseleave="e => unhoverButton(e, '#2196F3')"
                  class="grid-btn clipping-btn"
                  :style="{
                    width: '20%',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: focusedCutMode === 'single-trim' ? selectionColor : (clippingMethod === 'single-trim' ? '#1565C0' : '#2196F3'),
                    border: focusedCutMode === 'single-trim' ? '2px solid white' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    overflow: 'hidden',
                    boxShadow: clippingMethod === 'single-trim' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                    transform: clippingMethod === 'single-trim' ? 'translateY(2px)' : 'none',
                    color: focusedCutMode === 'single-trim' ? 'black' : 'white',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    textShadow: focusedCutMode === 'single-trim' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                    outline: 'none'
                  }"
                  title="Single trim - extract one clip from video [S]"
                ><span style="text-decoration: underline;">S</span>INGLE TRIM</div>
                <!-- Multiple Clips Button (hidden in edit mode — splitting an existing
                     SOT into N independent cues with N new AssetIDs would orphan the
                     original) -->
                <div
                  v-if="!editMode || initialData?.isReupload"
                  tabindex="0"
                  @click="selectCutMode('individual-clips')"
                  @focus="handleCutModeFocus('individual-clips')"
                  @blur="handleCutModeBlur"
                  @keydown="handleCutModeKeydown($event, 'individual-clips')"
                  @mouseenter="e => hoverButton(e, '#2196F3')"
                  @mouseleave="e => unhoverButton(e, '#2196F3')"
                  class="grid-btn clipping-btn"
                  :style="{
                    width: '20%',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: focusedCutMode === 'individual-clips' ? selectionColor : (clippingMethod === 'individual-clips' ? '#1565C0' : '#2196F3'),
                    border: focusedCutMode === 'individual-clips' ? '2px solid white' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    overflow: 'hidden',
                    boxShadow: clippingMethod === 'individual-clips' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                    transform: clippingMethod === 'individual-clips' ? 'translateY(2px)' : 'none',
                    color: focusedCutMode === 'individual-clips' ? 'black' : 'white',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    textShadow: focusedCutMode === 'individual-clips' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                    outline: 'none'
                  }"
                  title="Multiple clips - extract multiple separate clips [M]"
                ><span style="text-decoration: underline;">M</span>ULTIPLE CLIPS</div>
                <!-- Removal Button (Disabled - Coming Soon) -->
                <div
                  tabindex="0"
                  @click="selectCutMode('removal')"
                  @focus="handleCutModeFocus('removal')"
                  @blur="handleCutModeBlur"
                  @keydown="handleCutModeKeydown($event, 'removal')"
                  class="grid-btn clipping-btn"
                  :style="{
                    width: '20%',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: focusedCutMode === 'removal' ? selectionColor : '#9E9E9E',
                    border: focusedCutMode === 'removal' ? '2px solid white' : 'none',
                    cursor: 'not-allowed',
                    transition: 'all 0.2s ease',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    overflow: 'hidden',
                    opacity: focusedCutMode === 'removal' ? 1 : 0.6,
                    color: focusedCutMode === 'removal' ? 'black' : 'white',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    textShadow: focusedCutMode === 'removal' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                    outline: 'none'
                  }"
                  title="Removal - remove sections from video (Coming Soon) [R]"
                ><span style="text-decoration: underline;">R</span>EMOVAL</div>
                <!-- Montage Button (Disabled - Coming Soon) -->
                <div
                  tabindex="0"
                  @click="selectCutMode('montage')"
                  @focus="handleCutModeFocus('montage')"
                  @blur="handleCutModeBlur"
                  @keydown="handleCutModeKeydown($event, 'montage')"
                  class="grid-btn clipping-btn"
                  :style="{
                    width: '20%',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: focusedCutMode === 'montage' ? selectionColor : '#9E9E9E',
                    border: focusedCutMode === 'montage' ? '2px solid white' : 'none',
                    cursor: 'not-allowed',
                    transition: 'all 0.2s ease',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    overflow: 'hidden',
                    opacity: focusedCutMode === 'montage' ? 1 : 0.6,
                    color: focusedCutMode === 'montage' ? 'black' : 'white',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    textShadow: focusedCutMode === 'montage' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                    outline: 'none'
                  }"
                  title="Montage - combine multiple clips into single video (Coming Soon) [G]"
                >MONTA<span style="text-decoration: underline;">G</span>E</div>
              </div>
            </div>
          </div>

          <!-- Select Video Row (moved up, same styling as Type of Cut) -->
          <div class="mb-4">
            <label class="cue-modal-label mb-2 d-block" style="font-size: 14px; font-weight: 600; color: #333;">
              Select Video: <span style="color: red;">*</span>
            </label>
            <div class="d-flex" style="gap: 1px;">
              <!-- Browse Button -->
              <div
                ref="localFileButtonRef"
                tabindex="0"
                @click="triggerFileInput"
                @keydown.enter="triggerFileInput"
                @keydown.space.prevent="triggerFileInput"
                @focus="handleVideoButtonFocus('browse')"
                @blur="handleVideoButtonBlur"
                class="grid-btn"
                :style="{
                  flex: '1',
                  height: '50px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: focusedVideoButton === 'browse' ? selectionColor : '#2196F3',
                  border: focusedVideoButton === 'browse' ? '2px solid white' : 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontFamily: 'Helvetica, Arial, sans-serif',
                  overflow: 'hidden',
                  color: focusedVideoButton === 'browse' ? 'black' : 'white',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  textShadow: focusedVideoButton === 'browse' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                  outline: 'none'
                }"
                title="Browse for video file [B]"
              ><span style="text-decoration: underline;">B</span>ROWSE</div>
              <!-- YouTube Button (Disabled) -->
              <div
                tabindex="0"
                @focus="handleVideoButtonFocus('youtube')"
                @blur="handleVideoButtonBlur"
                class="grid-btn"
                :style="{
                  flex: '1',
                  height: '50px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: focusedVideoButton === 'youtube' ? selectionColor : '#9E9E9E',
                  border: focusedVideoButton === 'youtube' ? '2px solid white' : 'none',
                  cursor: 'not-allowed',
                  transition: 'all 0.2s ease',
                  fontFamily: 'Helvetica, Arial, sans-serif',
                  overflow: 'hidden',
                  opacity: focusedVideoButton === 'youtube' ? 1 : 0.6,
                  color: focusedVideoButton === 'youtube' ? 'black' : 'white',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  textShadow: focusedVideoButton === 'youtube' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                  outline: 'none'
                }"
                title="Import from YouTube (Coming Soon) [Y]"
              ><span style="text-decoration: underline;">Y</span>OUTUBE</div>
              <!-- X Button (Disabled) -->
              <div
                tabindex="0"
                @focus="handleVideoButtonFocus('x')"
                @blur="handleVideoButtonBlur"
                class="grid-btn"
                :style="{
                  flex: '0.6',
                  height: '50px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: focusedVideoButton === 'x' ? selectionColor : '#9E9E9E',
                  border: focusedVideoButton === 'x' ? '2px solid white' : 'none',
                  cursor: 'not-allowed',
                  transition: 'all 0.2s ease',
                  fontFamily: 'Helvetica, Arial, sans-serif',
                  overflow: 'hidden',
                  opacity: focusedVideoButton === 'x' ? 1 : 0.6,
                  color: focusedVideoButton === 'x' ? 'black' : 'white',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  textShadow: focusedVideoButton === 'x' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                  outline: 'none'
                }"
                title="Import from X/Twitter (Coming Soon) [X]"
              ><span style="text-decoration: underline;">X</span></div>
              <!-- TikTok Button (Disabled) -->
              <div
                tabindex="0"
                @focus="handleVideoButtonFocus('tiktok')"
                @blur="handleVideoButtonBlur"
                class="grid-btn"
                :style="{
                  flex: '1',
                  height: '50px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: focusedVideoButton === 'tiktok' ? selectionColor : '#9E9E9E',
                  border: focusedVideoButton === 'tiktok' ? '2px solid white' : 'none',
                  cursor: 'not-allowed',
                  transition: 'all 0.2s ease',
                  fontFamily: 'Helvetica, Arial, sans-serif',
                  overflow: 'hidden',
                  opacity: focusedVideoButton === 'tiktok' ? 1 : 0.6,
                  color: focusedVideoButton === 'tiktok' ? 'black' : 'white',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  textShadow: focusedVideoButton === 'tiktok' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                  outline: 'none'
                }"
                title="Import from TikTok (Coming Soon) [T]"
              ><span style="text-decoration: underline;">T</span>IKTOK</div>
              <!-- Clear Button -->
              <div
                tabindex="0"
                @click="clearVideo"
                @keydown.enter="clearVideo"
                @keydown.space.prevent="clearVideo"
                @focus="handleVideoButtonFocus('clear')"
                @blur="handleVideoButtonBlur"
                class="grid-btn"
                :style="{
                  flex: '0.8',
                  height: '50px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: focusedVideoButton === 'clear' ? selectionColor : '#757575',
                  border: focusedVideoButton === 'clear' ? '2px solid white' : 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontFamily: 'Helvetica, Arial, sans-serif',
                  overflow: 'hidden',
                  color: focusedVideoButton === 'clear' ? 'black' : 'white',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  textShadow: focusedVideoButton === 'clear' ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
                  outline: 'none'
                }"
                title="Clear selected video"
              >CLEAR</div>
            </div>
            <input
              ref="fileInputRef"
              type="file"
              accept="video/*"
              style="display: none;"
              @change="handleFileUpload"
            />
            <!-- Duration Display (inline, right-aligned) -->
            <div v-if="duration" class="mt-2" style="text-align: right;">
              <span style="font-size: 12px; color: #666;">Duration: </span>
              <span style="font-family: monospace; font-size: 14px; color: #333; font-weight: 500;">{{ duration }}</span>
            </div>
          </div>

          <!-- Slug (Required - shown only when NOT in multiple clips mode) -->
          <div v-if="clippingMethod !== 'individual-clips'" class="mb-3">
            <label class="cue-modal-label mb-1 d-block" style="font-size: 12px; font-weight: 500; color: #555;">
              Slug: <span style="color: red;">*</span>
            </label>
            <input
              ref="slugField"
              v-model="slug"
              class="cue-modal-input"
              type="text"
              placeholder="short-descriptive-name"
              style="width: 100%; padding: 10px; border: 1px solid #ddd; borderRadius: 4px; fontSize: 16px; boxSizing: border-box;"
            />
          </div>

          <!-- Multiple Clips Mode: Clip tools shown here instead of slug -->
          <div v-if="clippingMethod === 'individual-clips'" class="mb-3">
            <div class="d-flex mb-2" style="gap: 10px; align-items: flex-end;">
              <!-- Clip Slug -->
              <div style="flex: 2;">
                <label
                  ref="clipSlugLabelRef"
                  class="cue-modal-label mb-1 d-block"
                  :style="{
                    fontSize: '12px',
                    fontWeight: '500',
                    color: clipSlugNeedsAttention ? needsAttentionColor : '#555',
                    transition: 'color 0.2s ease'
                  }"
                >Clip Slug:</label>
                <input
                  ref="clipSlugInputRef"
                  v-model="clipSlug"
                  class="cue-modal-input"
                  :class="{ 'clip-slug-attention': clipSlugNeedsAttention }"
                  type="text"
                  placeholder="clip-name (auto-generated if empty)"
                  :style="{
                    width: '100%',
                    padding: '8px',
                    border: clipSlugNeedsAttention ? `2px solid ${needsAttentionColor}` : '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    transition: 'border-color 0.2s ease, box-shadow 0.2s ease'
                  }"
                  @input="handleClipSlugInput"
                  @keydown.enter="handleClipSlugEnter"
                />
              </div>
              <!-- Time Start -->
              <div style="flex: 1;">
                <label class="cue-modal-label mb-1 d-block" style="font-size: 12px; font-weight: 500; color: #555;">Time Start:</label>
                <input
                  ref="trimStartInputRef"
                  v-model="trimStart"
                  class="cue-modal-input"
                  type="text"
                  placeholder="HH:MM:SS"
                  style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
                />
              </div>
              <!-- Time End -->
              <div style="flex: 1;">
                <label class="cue-modal-label mb-1 d-block" style="font-size: 12px; font-weight: 500; color: #555;">Time End:</label>
                <input
                  ref="trimEndInputRef"
                  v-model="trimEnd"
                  class="cue-modal-input"
                  type="text"
                  placeholder="HH:MM:SS"
                  style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
                />
              </div>
              <!-- Take Button -->
              <div style="flex: 0 0 80px;">
                <button
                  @click="handleTakeClip"
                  class="cue-modal-button-small"
                  type="button"
                  style="width: 100%; height: 36px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;"
                  title="Take clip (Ctrl+Enter)"
                >TAKE</button>
              </div>
            </div>
            <!-- Clips Collection Display (Badges) -->
            <div v-if="clips.length > 0">
              <label class="cue-modal-label mb-1 d-block" style="font-size: 12px; font-weight: 500; color: #555;">
                Clips ({{ clips.length }}):
              </label>
              <div class="clips-badges" style="display: flex; flex-wrap: wrap; gap: 6px;">
                <div
                  v-for="(clip, index) in clips"
                  :key="`clip-top-${index}`"
                  class="clip-badge"
                  style="display: inline-flex; align-items: center; background: #e3f2fd; border: 1px solid #90caf9; border-radius: 16px; padding: 4px 10px; font-size: 12px; gap: 6px;"
                >
                  <span style="font-weight: 500; color: #1976d2;">{{ clip.slug }}</span>
                  <span style="color: #666; font-family: monospace; font-size: 10px;">{{ clip.time_start }} → {{ clip.time_end }}</span>
                  <button
                    @click="removeClip(index)"
                    type="button"
                    style="background: none; border: none; color: #f44336; cursor: pointer; font-size: 14px; line-height: 1; padding: 0; margin-left: 2px;"
                    title="Remove clip"
                  >×</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Video Player Container with Topgrid, Timecode, and Control Grid -->
          <div v-if="mediaUrl" class="video-wrapper mb-3" style="position: relative; z-index: 10;">
            <!-- 1x8 Topgrid (Above Video) -->
            <div class="topgrid-container mb-0" style="width: 100%; position: relative; z-index: 14;">
              <div class="topgrid-row d-flex" style="gap: 1px; margin-bottom: 1px;">
                <div
                  v-for="cellNum in 8"
                  :key="`topgrid-${cellNum}`"
                  class="topgrid-cell"
                  style="flex: 1; height: 27.5px; background: #d3d3d3; border-radius: 0px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: #888; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; box-shadow: 0 1px 3px rgba(0,0,0,0.1);"
                  @mouseenter="e => { e.target.style.background = '#bbb'; e.target.style.transform = 'scale(1.02)'; }"
                  @mouseleave="e => { e.target.style.background = '#d3d3d3'; e.target.style.transform = 'scale(1)'; }"
                >{{ cellNum }}</div>
              </div>
            </div>

            <!-- Upload Progress Bar (Subtle 5px green bar) -->
            <div
              v-if="uploadProgress > 0 && uploadProgress < 100"
              class="upload-progress-bar"
              style="width: 100%; height: 5px; background: #e0e0e0; border-radius: 4px 4px 0 0; overflow: hidden; position: relative; z-index: 16; margin-bottom: 0;"
            >
              <div
                class="progress-fill"
                :style="{
                  width: uploadProgress + '%',
                  height: '100%',
                  background: '#4caf50',
                  transition: 'width 0.3s ease'
                }"
              ></div>
            </div>

            <!-- Live Timecode Display (Black Bar Above Video) -->
            <div
              ref="timecodeDisplay"
              class="timecode-display"
              style="width: 100%; background: #000; border: 2px solid #ccc; border-bottom: none; position: relative; z-index: 15; margin-bottom: 0;"
              :style="{ borderRadius: uploadProgress > 0 && uploadProgress < 100 ? '0' : '4px 4px 0 0' }"
            >
              <div class="d-flex justify-space-between align-center pa-2" style="padding: 5px 15px;">
                <div style="font-size: 18px; font-weight: bold; font-family: monospace; color: white;">{{ currentTimecode }}</div>
                <div style="font-size: 12px; color: #ccc; font-family: monospace;">{{ durationTimecode }} | -{{ remainingTimecode }} | {{ currentFramerate }}fps</div>
              </div>
            </div>

            <!-- Video Player with Metadata Overlay -->
            <div class="video-container" style="width: 100%; max-width: 100%; background: #000; border: 2px solid #ccc; border-top: none; border-radius: 0 0 4px 4px; overflow: hidden; position: relative; z-index: 10; margin-bottom: 0;">
              <video
                ref="videoPlayerRef"
                class="video-player"
                controls
                controlsList="nodownload"
                tabindex="-1"
                style="width: 100% !important; height: 300px !important; max-width: 100% !important; position: relative; z-index: 11; display: block; border: none; border-radius: 0; object-fit: contain;"
                preload="metadata"
                @loadedmetadata="handleVideoMetadataLoaded"
                @timeupdate="updateTimecode"
                @play="updatePlayPauseState"
                @pause="updatePlayPauseState"
                @keydown="handleVideoKeydown"
                @focus="$event.target.blur()"
              ></video>

              <!-- Video Info Overlay (Bottom-left corner) -->
              <div
                ref="videoInfoOverlay"
                class="video-info-overlay"
                style="position: absolute; bottom: 35px; left: 10px; background: rgba(0, 0, 0, 0.8); color: white; padding: 8px 10px; border-radius: 3px; font-family: monospace; z-index: 20; max-width: 200px; pointer-events: none; font-size: 11px; line-height: 1.3;"
              >
                <div><strong>Loading...</strong></div>
                <div>Resolution: --</div>
                <div>Duration: --</div>
              </div>
            </div>

            <!-- Audio Waveform (Slide-up animation) - Interactive scrubber -->
            <!-- Visible whenever a video is loaded; bars stay empty for silent videos but markers/duration/playhead still render. -->
            <transition name="waveform-slide">
              <div v-if="showWaveform" class="waveform-wrapper" style="width: 100%; margin-bottom: 15px;">
                <AudioWaveform
                  :waveform-data="waveformData"
                  :current-time="videoPlayerRef?.currentTime || 0"
                  :duration="videoPlayerRef?.duration || 0"
                  :height="60"
                  background-color="rgba(0, 0, 0, 0.7)"
                  wave-color="#4CAF50"
                  progress-color="#81C784"
                  playhead-color="#FF5722"
                  :in-point="inPointSeconds"
                  :out-point="outPointSeconds"
                  region-color="#000000"
                  region-background="rgba(255, 255, 255, 0.35)"
                  @seek="handleWaveformSeek"
                />
              </div>
            </transition>

            <!-- 3x8 Control Grid Below Video -->
            <div class="control-grid-container" style="width: 100%; margin-top: 1px; margin-bottom: 15px; position: relative; z-index: 13;">
              <!-- Row 1: Mark In (1-2), Go In (3), Empty (4-5), Go Out (6), Mark Out (7-8) -->
              <div class="control-row d-flex mb-0" style="margin-bottom: 1px;">
                <!-- Mark In Button (Cells 1-2, 25% width) -->
                <div
                  ref="markInBtn"
                  class="grid-btn mark-in"
                  @click="performMarkInAction"
                  @mouseenter="e => hoverButton(e, '#2196F3')"
                  @mouseleave="e => unhoverButton(e, '#2196F3')"
                  style="width: calc(25% + 1px); height: 65px; display: flex; flex-direction: column; background: #2196F3; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Mark In point (I key)"
                >
                  <div style="background: #1976D2; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">MARK IN</div>
                  <div style="background: #2196F3; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">I</div>
                </div>

                <!-- Go to In Button (Cell 3, 12.5% width) -->
                <div
                  ref="goToInBtn"
                  class="grid-btn go-to"
                  @click="performGoToInAction"
                  @mouseenter="e => hoverButton(e, '#64B5F6')"
                  @mouseleave="e => unhoverButton(e, '#64B5F6')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #64B5F6; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Go to In point (Q key)"
                >
                  <div style="background: #42A5F5; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">GO IN</div>
                  <div style="background: #64B5F6; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">Q</div>
                </div>

                <!-- Empty cells 4-5 (25% total) -->
                <div v-for="cellNum in [4, 5]" :key="`r1-${cellNum}`" class="grid-cell-empty" style="width: 12.5%; height: 65px; background: #d3d3d3; color: #666; display: flex; align-items: center; justify-content: center; border: none; margin-right: 1px; font-size: 18px; font-weight: bold; font-family: Helvetica, Arial, sans-serif; cursor: pointer; transition: all 0.2s ease;">{{ cellNum }}</div>

                <!-- Go to Out Button (Cell 6, 12.5% width) -->
                <div
                  ref="goToOutBtn"
                  class="grid-btn go-to"
                  @click="performGoToOutAction"
                  @mouseenter="e => hoverButton(e, '#FFAB91')"
                  @mouseleave="e => unhoverButton(e, '#FFAB91')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #FFAB91; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Go to Out point (W key)"
                >
                  <div style="background: #FF8A65; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">GO OUT</div>
                  <div style="background: #FFAB91; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">W</div>
                </div>

                <!-- Mark Out Button (Cells 7-8, 25% width) -->
                <div
                  ref="markOutBtn"
                  class="grid-btn mark-out"
                  @click="performMarkOutAction"
                  @mouseenter="e => hoverButton(e, '#FF5722')"
                  @mouseleave="e => unhoverButton(e, '#FF5722')"
                  style="width: calc(25% + 1px); height: 65px; display: flex; flex-direction: column; background: #FF5722; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Mark Out point (O key)"
                >
                  <div style="background: #E64A19; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">MARK OUT</div>
                  <div style="background: #FF5722; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">O</div>
                </div>
              </div>

              <!-- Row 2: Step controls and Play/Pause -->
              <div class="control-row d-flex mb-0" style="margin-bottom: 1px;">
                <!-- -10s (Cell 9) -->
                <div
                  ref="step10sBackBtn"
                  class="grid-btn step dark-orange"
                  @click="performJumpBackTenSeconds"
                  @mouseenter="e => hoverButton(e, '#E65100')"
                  @mouseleave="e => unhoverButton(e, '#E65100')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #E65100; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Jump back 10 seconds"
                >
                  <div style="background: #BF360C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;">-10s</div>
                  <div style="background: #E65100; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">◄◄</div>
                </div>

                <!-- -1s (Cell 10) -->
                <div
                  ref="step1sBackBtn"
                  class="grid-btn step orange"
                  @click="performStepBackSecond"
                  @mouseenter="e => hoverButton(e, '#FF9800')"
                  @mouseleave="e => unhoverButton(e, '#FF9800')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #FF9800; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step back 1 second (J key)"
                >
                  <div style="background: #F57C00; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;">-1s</div>
                  <div style="background: #FF9800; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">◄</div>
                </div>

                <!-- -1f (Cell 11) -->
                <div
                  ref="step1fBackBtn"
                  class="grid-btn step light-orange"
                  @click="performStepBackFrame"
                  @mouseenter="e => hoverButton(e, '#FFB74D')"
                  @mouseleave="e => unhoverButton(e, '#FFB74D')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #FFB74D; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step back 1 frame (← key)"
                >
                  <div style="background: #FFA726; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;">-1f</div>
                  <div style="background: #FFB74D; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">|◄</div>
                </div>

                <!-- Play/Pause (Cells 12-13, 25% width) -->
                <div
                  ref="playPauseBtn"
                  class="grid-btn play-pause"
                  @click="performPlayPauseAction"
                  @mouseenter="e => hoverButton(e, '#4CAF50')"
                  @mouseleave="e => unhoverButton(e, '#4CAF50')"
                  style="width: calc(25% + 1px); height: 65px; display: flex; flex-direction: column; background: #4CAF50; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Play/Pause - Toggle playback (Space or K)"
                >
                  <div style="background: #388E3C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">PLAY/PAUSE</div>
                  <div style="background: #4CAF50; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">{{ isPlaying ? '⏸' : '▶' }}</div>
                </div>

                <!-- +1f (Cell 14) -->
                <div
                  ref="step1fForwardBtn"
                  class="grid-btn step light-orange"
                  @click="performStepForwardFrame"
                  @mouseenter="e => hoverButton(e, '#FFB74D')"
                  @mouseleave="e => unhoverButton(e, '#FFB74D')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #FFB74D; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step forward 1 frame (→ key)"
                >
                  <div style="background: #FFA726; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;">+1f</div>
                  <div style="background: #FFB74D; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">►|</div>
                </div>

                <!-- +1s (Cell 15) -->
                <div
                  ref="step1sForwardBtn"
                  class="grid-btn step orange"
                  @click="performStepForwardSecond"
                  @mouseenter="e => hoverButton(e, '#FF9800')"
                  @mouseleave="e => unhoverButton(e, '#FF9800')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #FF9800; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step forward 1 second (L key)"
                >
                  <div style="background: #F57C00; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;">+1s</div>
                  <div style="background: #FF9800; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">►</div>
                </div>

                <!-- +10s (Cell 16) -->
                <div
                  ref="step10sForwardBtn"
                  class="grid-btn step dark-orange"
                  @click="performJumpForwardTenSeconds"
                  @mouseenter="e => hoverButton(e, '#E65100')"
                  @mouseleave="e => unhoverButton(e, '#E65100')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #E65100; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Jump forward 10 seconds"
                >
                  <div style="background: #BF360C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;">+10s</div>
                  <div style="background: #E65100; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">►►</div>
                </div>
              </div>

              <!-- Row 3: Empty cells, Preview, Take -->
              <div class="control-row d-flex">
                <!-- Empty cells 17-20 -->
                <div v-for="cellNum in [17, 18, 19, 20]" :key="`r3-${cellNum}`" class="grid-cell-empty" style="width: 12.5%; height: 65px; background: #d3d3d3; color: #666; display: flex; align-items: center; justify-content: center; border: none; margin-right: 1px; font-size: 18px; font-weight: bold; font-family: Helvetica, Arial, sans-serif; cursor: pointer; transition: all 0.2s ease;">{{ cellNum }}</div>

                <!-- Preview Button (Cell 21) -->
                <div
                  ref="previewBtn"
                  class="grid-btn preview"
                  @click="performPreviewAction"
                  @mouseenter="e => hoverButton(e, '#9C27B0')"
                  @mouseleave="e => unhoverButton(e, '#9C27B0')"
                  style="width: 12.5%; height: 65px; display: flex; flex-direction: column; background: #9C27B0; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Preview - Play from In to Out (Shift+Space)"
                >
                  <div style="background: #7B1FA2; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">PREVIEW</div>
                  <div style="background: #9C27B0; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">▶|</div>
                </div>

                <!-- Empty cell 22 -->
                <div class="grid-cell-empty" style="width: 12.5%; height: 65px; background: #d3d3d3; color: #666; display: flex; align-items: center; justify-content: center; border: none; margin-right: 1px; font-size: 18px; font-weight: bold; font-family: Helvetica, Arial, sans-serif; cursor: pointer; transition: all 0.2s ease;">22</div>

                <!-- Take Button (Cells 23-24, 25% width) -->
                <div
                  ref="takeBtn"
                  class="grid-btn take"
                  @click="performTakeAction"
                  @mouseenter="e => hoverButton(e, '#4CAF50')"
                  @mouseleave="e => unhoverButton(e, '#4CAF50')"
                  style="width: calc(25% + 1px); height: 65px; display: flex; flex-direction: column; background: #4CAF50; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Take - Commit current cut (Ctrl+Enter)"
                >
                  <div style="background: #388E3C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">TAKE</div>
                  <div style="background: #4CAF50; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✂</div>
                </div>
              </div>
            </div>
          </div>

          <!-- ============================================================ -->
          <!-- CLIPPING TOOLS SECTION (hidden in multiple clips mode - tools shown at top) -->
          <!-- ============================================================ -->
          <div v-if="clippingMethod !== 'individual-clips'">
            <div style="border-top: 2px solid #999; margin: 25px 0 20px 0;"></div>

            <div class="clipping-tools-section mb-4">
              <h3 class="text-uppercase font-weight-bold mb-3" style="font-size: 1.1em; color: #333;">CLIPPING TOOLS</h3>

              <!-- Clip Slug, Time Start, Time End, and Take Button (Inline) -->
              <div class="d-flex mb-3" style="gap: 10px; align-items: flex-end;">
                <!-- Clip Slug -->
                <div style="flex: 2;">
                  <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Clip Slug:</label>
                  <input
                    v-model="clipSlug"
                    class="cue-modal-input"
                    type="text"
                    placeholder="clip-name (auto-generated if empty)"
                    :disabled="clippingMethod === 'none'"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
                  />
                </div>

                <!-- Time Start -->
                <div style="flex: 1;">
                  <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Time Start:</label>
                  <input
                    v-model="trimStart"
                    class="cue-modal-input"
                    type="text"
                    placeholder="HH:MM:SS"
                    :disabled="clippingMethod === 'none'"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
                  />
                </div>

                <!-- Time End -->
                <div style="flex: 1;">
                  <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Time End:</label>
                  <input
                    v-model="trimEnd"
                    class="cue-modal-input"
                    type="text"
                    placeholder="HH:MM:SS"
                    :disabled="clippingMethod === 'none'"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
                  />
                </div>

                <!-- Take Button (disabled for none and single-trim) -->
                <div style="flex: 0 0 80px;">
                  <button
                    @click="handleTakeClip"
                    :disabled="clippingMethod === 'none' || clippingMethod === 'single-trim'"
                    class="cue-modal-button-small"
                    type="button"
                    style="width: 100%; height: 38px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; transition: background-color 0.2s;"
                    :style="{ opacity: (clippingMethod === 'none' || clippingMethod === 'single-trim') ? 0.5 : 1, cursor: (clippingMethod === 'none' || clippingMethod === 'single-trim') ? 'not-allowed' : 'pointer' }"
                    title="Take clip (Ctrl+Enter)"
                  >TAKE</button>
                </div>
              </div>
            </div>

            <div style="border-bottom: 2px solid #999; margin: 20px 0 25px 0;"></div>
          </div>
          <!-- ============================================================ -->
          <!-- END CLIPPING TOOLS SECTION -->
          <!-- ============================================================ -->

          <!-- Credits/Lower Thirds (Dynamic Key-Value) -->
          <div class="mb-3">
            <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Credits/Lower Thirds:</label>
            <div class="credits-container pa-2" style="border: 1px solid #ddd; border-radius: 4px; background: white;">
              <div ref="creditsListRef" class="credits-list mb-2">
                <div
                  v-for="(credit, index) in credits"
                  :key="`credit-${index}`"
                  class="d-flex mb-2"
                  style="gap: 10px; align-items: center;"
                >
                  <input
                    v-model="credit.key"
                    class="cue-modal-input"
                    type="text"
                    placeholder="Key (e.g., speaker)"
                    style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; margin-bottom: 0;"
                  />
                  <input
                    v-model="credit.value"
                    class="cue-modal-input"
                    type="text"
                    placeholder="Value (e.g., Dr. Jane Smith)"
                    style="flex: 2; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; margin-bottom: 0;"
                  />
                  <button
                    @click="removeCredit(index)"
                    class="cue-modal-button-small"
                    type="button"
                    style="background-color: #ff4444; color: white; min-width: 70px; padding: 6px 12px; font-size: 12px; border: none; border-radius: 3px; cursor: pointer;"
                  >Remove</button>
                </div>
              </div>
              <button
                @click="addCredit"
                class="cue-modal-button-small"
                type="button"
                style="background-color: #4CAF50; color: white; padding: 6px 12px; font-size: 12px; border: none; border-radius: 3px; cursor: pointer;"
              >+ Add Credit</button>
            </div>
          </div>

          <!-- Description -->
          <div class="mb-3">
            <label class="cue-modal-label mb-1 d-block" style="font-size: 12px; font-weight: 500; color: #555;">Description:</label>
            <textarea
              v-model="description"
              class="cue-modal-textarea"
              rows="4"
              placeholder="Brief description of the SOT content and context..."
              style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; box-sizing: border-box; resize: none;"
            ></textarea>
          </div>

          <!-- Transcription (only shown if transcript exists) -->
          <div v-if="transcription" class="mb-3">
            <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Transcription:</label>
            <textarea
              v-model="transcription"
              class="cue-modal-textarea"
              rows="4"
              placeholder="Full transcription of the audio/video content..."
              style="width: 100%; height: 150px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; resize: vertical;"
            ></textarea>
          </div>

          <!-- Buttons -->
          <div class="d-flex" style="gap: 10px; margin-top: 20px;">
            <button
              type="button"
              @click="cancel"
              class="cue-modal-button cancel"
              style="flex: 1; padding: 20px 40px; font-size: 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s;"
            >Cancel</button>
            <button
              type="button"
              @click="handleAddCue"
              class="cue-modal-button"
              style="flex: 1; padding: 20px 40px; font-size: 16px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s;"
            >{{ clippingMethod !== 'none' ? 'Insert and Begin Processing' : 'Insert SOT Cue' }}</button>
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios' // eslint-disable-line no-unused-vars
import AudioWaveform from '../AudioWaveform.vue' // eslint-disable-line no-unused-vars
import { useWaveform } from '../../composables/useWaveform'
import { useTrimmableMediaModal } from '../../composables/useTrimmableMediaModal'
import { useMediaModalKeyboard } from '../../composables/useMediaModalKeyboard'
import { useMediaModalClips } from '../../composables/useMediaModalClips'
import { useFocusTrap } from '../../composables/useFocusTrap'
import { uploadVideoInBackground } from '../../utils/mediaUpload'
import { registerModalEsc } from '../../composables/useModalStack'
import { useDoubleEnterToSlug } from '../../composables/useDoubleEnterToSlug'
import MediaModalOverlays from './shared/MediaModalOverlays.vue'
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap'

// SOT Processing Job Types
// These define what type of processing the backend should perform
const SOT_JOB_TYPES = {
  SINGLE_TRIM: 'single_trim',           // Standard SOT with optional trim
  INDIVIDUAL_CLIPS: 'individual_clips', // Extract multiple separate clips
  MONTAGE: 'montage',                   // Combine clips into single video
  FULL_PROCESS: 'full_process'          // Complete normalization pipeline
}

const props = defineProps({
  show: Boolean,
  episodeNumber: String,
  segmentName: String,
  editMode: {
    type: Boolean,
    default: false
  },
  initialData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:show', 'submit', 'submit-multiple'])

const toast = useToast()

// Waveform composable
const { waveformData, isAnalyzing, extractWaveform, clearWaveform } = useWaveform() // eslint-disable-line no-unused-vars

// Form refs
const sotFormRef = ref(null) // eslint-disable-line no-unused-vars
const modalCardRef = ref(null)
const fileInputRef = ref(null)
const videoPlayerRef = ref(null)
const trimStartInputRef = ref(null)
const trimEndInputRef = ref(null)
const topErrorEl = ref(null)
const timecodeDisplay = ref(null)
const videoInfoOverlay = ref(null)
const creditsListRef = ref(null)
const slugField = ref(null)
const firstCutModeButtonRef = ref(null)

// Button refs for keyboard shortcuts
const markInBtn = ref(null)
const markOutBtn = ref(null)
const goToInBtn = ref(null)
const goToOutBtn = ref(null)
const playPauseBtn = ref(null)
const previewBtn = ref(null)
const takeBtn = ref(null)
const step10sBackBtn = ref(null)
const step1sBackBtn = ref(null)
const step1fBackBtn = ref(null)
const step10sForwardBtn = ref(null)
const step1sForwardBtn = ref(null)
const step1fForwardBtn = ref(null)

// ---------------------------------------------------------------------
// Trim / timecode / playback / multi-clip state — owned by the composable.
// Destructured here so existing template/script references resolve.
// ---------------------------------------------------------------------
const trim = useTrimmableMediaModal({
  videoPlayerRef,
  defaultFramerate: 30,
  toast,
  emitActionFeedback: true,
})
const {
  // Trim points
  trimStart, trimEnd, duration,
  // Playback / display
  currentFramerate, isPlaying, currentTimecode, durationTimecode,
  remainingTimecode, currentActionDisplay, thumbnailTimecode,
  // Speed
  playbackSpeed, showSpeedIndicator, speedLabel,
  // Frame counter
  showFrameCounter, currentFrameNumber, totalFrames, frameStepDirection,
  // Multi-clip state
  clippingMethod, clipSlug, clips, clipCounter,
  // Computed
  clipDuration, inPointSeconds, outPointSeconds,
  // Pure utilities
  secondsToTimecode, timecodeToSeconds, formatFileSize,
  // UI feedback
  hoverButton, unhoverButton, animateButtonPress, // eslint-disable-line no-unused-vars
  // Mark / go-to
  performMarkInAction, performMarkOutAction,
  performGoToInAction, performGoToOutAction,
  handleWaveformSeek,
  // Play / pause / preview
  performPlayPauseAction, performPreviewAction,
  // Frame stepping
  performStepBackFrame, performStepForwardFrame,
  performStepBackSecond, performStepForwardSecond,
  performJumpBackTenSeconds, performJumpForwardTenSeconds,
  // Thumbnail / speed actions are invoked via the trim composable
  // by useMediaModalKeyboard internally; not needed as locals here.
  // Live updates
  updateTimecode, updatePlayPauseState,
} = trim

// Form data (SOT-specific)
const assetId = ref('Generated on save') // eslint-disable-line no-unused-vars
const slug = ref('')
const mediaUrl = ref('')
const thumbnailUrl = ref('')
const description = ref('')
const airTime = ref('') // eslint-disable-line no-unused-vars
const airDate = ref('') // eslint-disable-line no-unused-vars
const transcription = ref('')
const credits = ref([])

// Video state (SOT-specific)
const previewInterval = ref(null) // eslint-disable-line no-unused-vars
const videoSpecs = ref({})
const blobUrl = ref('')
const fileExtension = ref('') // eslint-disable-line no-unused-vars
const originalFile = ref(null)

// Background upload state
const uploadProgress = ref(0)
const tempJobId = ref(null)
const uploadComplete = ref(false) // eslint-disable-line no-unused-vars
const isSubmitting = ref(false) // Debounce flag for Alt+Enter
let uploadAbortFn = null // captures the abort() returned by uploadVideoInBackground

// Type of Cut keyboard navigation
const focusedCutMode = ref(null)
const focusedVideoButton = ref(null)
const showCutModeHelp = ref(false)

// Cut mode descriptions (shown when Tab-navigating)
const cutModeDescriptions = { // eslint-disable-line no-unused-vars
  'none': 'Insert SOT cue without video processing',
  'single-trim': 'Extract one clip from video with IN/OUT points',
  'individual-clips': 'Extract multiple separate clips, each as its own SOT',
  'removal': 'Remove sections from video (Coming Soon)',
  'montage': 'Combine multiple clips into single video (Coming Soon)'
}

// Double-Enter TAKE functionality — clipSlugNeedsAttention and
// pendingTakeOnSlug come from useMediaModalClips below
const clipSlugInputRef = ref(null)
const clipSlugLabelRef = ref(null) // eslint-disable-line no-unused-vars
const localFileButtonRef = ref(null)
const SPEED_PRESETS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0] // eslint-disable-line no-unused-vars

// Waveform state
const showWaveform = ref(false) // eslint-disable-line no-unused-vars

// Hotkeys visibility state (starts collapsed)
const showHotkeys = ref(false)

// Computed: Color values for validation feedback
const locatorFlashColor = computed(() => {
  const colorName = getColorValue('locatorflash') || getColorValue('locatorflash-interface') || 'deep-orange-accent-2'
  return resolveVuetifyColor(colorName)
})

const needsAttentionColor = computed(() => {
  const colorName = getColorValue('needs-attention') || 'orange-lighten-3'
  return resolveVuetifyColor(colorName)
})

// Multi-clip actions (provides clipSlugNeedsAttention/pendingTakeOnSlug
// state via the composable's returned refs)
const clipsApi = useMediaModalClips({
  videoPlayerRef,
  trim,
  toast,
  clipSlugInputRef,
  locatorFlashColor,
  slug,
})
const {
  clipSlugNeedsAttention,
  pendingTakeOnSlug, // eslint-disable-line no-unused-vars
  handleTakeClip, // eslint-disable-line no-unused-vars
  removeClip, // eslint-disable-line no-unused-vars
  handleDoubleEnterTake,
  handleClipSlugInput, // eslint-disable-line no-unused-vars
  handleClipSlugEnter, // eslint-disable-line no-unused-vars
} = clipsApi

// Selection color for focused UI elements (Tab navigation highlight)
const selectionColor = computed(() => {
  const colorName = getColorValue('selection') || 'warning'
  return resolveVuetifyColor(colorName)
})

// Utility + button-effect functions now come from the trim composable
// (secondsToTimecode, timecodeToSeconds, formatFileSize, hoverButton,
// unhoverButton, animateButtonPress). Destructured at the top.

// Type of Cut keyboard navigation handlers
const handleCutModeFocus = (mode) => { // eslint-disable-line no-unused-vars
  focusedCutMode.value = mode
  showCutModeHelp.value = true
}

const handleCutModeBlur = () => { // eslint-disable-line no-unused-vars
  focusedCutMode.value = null
  // Delay hiding help text to allow for Tab to next button
  setTimeout(() => {
    if (!focusedCutMode.value) {
      showCutModeHelp.value = false
    }
  }, 100)
}

// Video source button focus/blur handlers
const handleVideoButtonFocus = (button) => { // eslint-disable-line no-unused-vars
  focusedVideoButton.value = button
}

const handleVideoButtonBlur = () => { // eslint-disable-line no-unused-vars
  focusedVideoButton.value = null
}

const selectCutMode = (mode, fromKeyboard = false) => { // eslint-disable-line no-unused-vars
  // Check if mode is disabled
  if (mode === 'removal' || mode === 'montage') {
    toast.warning(`${mode.charAt(0).toUpperCase() + mode.slice(1)} mode coming soon!`)
    return false
  }

  clippingMethod.value = mode
  showCutModeHelp.value = false
  focusedCutMode.value = null

  if (fromKeyboard) {
    // After selecting cut mode, transport user to video source selection
    // Focus on the Local File button
    nextTick(() => {
      if (localFileButtonRef.value) {
        localFileButtonRef.value.focus()
        console.log(`✂️ Cut mode ${mode.toUpperCase()} selected, focused on video source`)
      }
    })
  }

  return true
}

const handleCutModeKeydown = (event, mode) => { // eslint-disable-line no-unused-vars
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    selectCutMode(mode, true)
  }
}

// Video control actions
// Mark, go-to, play/pause, preview, step, jump, thumbnail, and speed
// actions all come from the trim composable (destructured at the top).
// Only performTakeAction (SOT-only row-3 button) remains here.

const performTakeAction = () => { // eslint-disable-line no-unused-vars
  console.log('[SOT Modal] Take action - commit current cut')
  toast.info('Take: Current cut committed')
  animateButtonPress(takeBtn.value)
  // TODO: Implement multiple cuts storage system
}

// Scroll to bottom of modal
const scrollToBottomOfModal = () => {
  const interiorContainer = document.querySelector('.interior-container')
  if (interiorContainer) {
    interiorContainer.scrollTop = interiorContainer.scrollHeight
    toast.info('Scrolled to bottom', { timeout: 1000 })
  }
}

// Handle keydown on video element to prevent HTML5 player default shortcuts
// HTML5 video has built-in shortcuts: Space (play/pause), arrows (seek), M (mute), F (fullscreen)
// We intercept these to use our own handlers instead
const handleVideoKeydown = (event) => { // eslint-disable-line no-unused-vars
  // Keys that HTML5 video handles by default that we want to override
  const interceptedKeys = [
    ' ',           // Space - play/pause (we handle this)
    'ArrowLeft',   // Seek backward (we use for frame stepping)
    'ArrowRight',  // Seek forward (we use for frame stepping)
    'ArrowUp',     // Volume up (we don't use, but prevent for consistency)
    'ArrowDown',   // Volume down (we don't use, but prevent for consistency)
    'Home',        // Go to start (we handle this)
    'End',         // Go to end (we handle this)
    'm',           // Mute toggle
    'M',
    'f',           // Fullscreen toggle
    'F',
    'k',           // Play/pause (YouTube-style)
    'K',
    'j',           // Seek backward 10s (YouTube-style)
    'J',
    'l',           // Seek forward 10s (YouTube-style)
    'L'
  ]

  if (interceptedKeys.includes(event.key)) {
    // Prevent the video player's default handling
    event.preventDefault()
    event.stopPropagation()
    // Let the event bubble up to our document-level handler
    // which will handle the action properly
  }
}

// Keyboard shortcuts now live in useMediaModalKeyboard composable.
// The setupKeyboardShortcuts / removeKeyboardShortcuts wrappers below
// preserve the watcher's call sites; the actual switch lives in the
// composable.
const kbd = useMediaModalKeyboard({
  show: () => props.show,
  videoPlayerRef,
  trim,
  onSubmit: () => handleAddCue(),
  onTake: () => performTakeAction(),
  onPreviewIntoOut: () => performPreviewAction(),
  onDoubleEnterTake: () => handleDoubleEnterTake(),
  onCutModeSelect: (mode) => selectCutMode(mode, true),
  onBrowseFile: () => triggerFileInput(),
  onToggleHotkeys: () => { showHotkeys.value = !showHotkeys.value },
  onScrollToBottom: () => scrollToBottomOfModal(),
  onEscape: () => handleEscapeKey(),
  trimStartInputRef,
  trimEndInputRef,
  clippingMethod,
})

const setupKeyboardShortcuts = () => kbd.install()
const removeKeyboardShortcuts = () => kbd.uninstall()

// (Original inline keyboard switch ~280 lines removed — handled by
// useMediaModalKeyboard above.)

// Video metadata handling
const handleVideoMetadataLoaded = () => { // eslint-disable-line no-unused-vars
  if (!videoPlayerRef.value) return

  const videoDuration = videoPlayerRef.value.duration
  const videoWidth = videoPlayerRef.value.videoWidth
  const videoHeight = videoPlayerRef.value.videoHeight

  // Detect framerate (simplified - defaults to 30fps)
  currentFramerate.value = 30

  // Store video specs
  videoSpecs.value = {
    resolution: videoWidth && videoHeight ? `${videoWidth}×${videoHeight}` : null,
    width: videoWidth || null,
    height: videoHeight || null,
    aspectRatio: videoWidth && videoHeight ? (videoWidth / videoHeight).toFixed(3) : null,
    duration: videoDuration || null,
    framerate: currentFramerate.value,
    framerateSource: 'assumed',
    fileSize: originalFile.value?.size || null,
    filename: originalFile.value?.name || null
  }

  // Auto-populate duration with frame-accurate timecode
  if (videoDuration && videoDuration > 0) {
    duration.value = secondsToTimecode(videoDuration, true)
    toast.success(`Duration auto-detected: ${duration.value} @ ${currentFramerate.value}fps`)
  }

  // Update video info overlay
  if (videoInfoOverlay.value) {
    const resolution = videoSpecs.value.resolution || 'Unknown'
    const aspectRatio = videoSpecs.value.aspectRatio || 'Unknown'
    const fileSizeText = videoSpecs.value.fileSize ? formatFileSize(videoSpecs.value.fileSize) : 'Unknown'

    videoInfoOverlay.value.innerHTML = `
      <div><strong>${videoSpecs.value.filename || 'Video'}</strong></div>
      <div>Resolution: ${resolution}</div>
      <div>Aspect: ${aspectRatio}:1</div>
      <div>Duration: ${secondsToTimecode(videoDuration, true)}</div>
      <div>Framerate: ${currentFramerate.value}fps</div>
      <div>Size: ${fileSizeText}</div>
    `
  }

  // Extract waveform asynchronously
  setTimeout(async () => {
    try {
      console.log('[SOT Modal] Starting waveform extraction...')
      await extractWaveform(videoPlayerRef.value, 500)

      // Show waveform with delay for slide-up animation
      setTimeout(() => {
        showWaveform.value = true
        console.log('[SOT Modal] Waveform displayed')
      }, 300)
    } catch (error) {
      console.error('[SOT Modal] Waveform extraction failed:', error)
    }
  }, 500)
}

// updateTimecode and updatePlayPauseState come from the trim composable
// (destructured at the top). The template wires them to the <video>
// element's @timeupdate / @play / @pause events directly.

// File handling
const triggerFileInput = () => { // eslint-disable-line no-unused-vars
  fileInputRef.value?.click()
}

const handleFileUpload = async (event) => { // eslint-disable-line no-unused-vars
  const file = event.target.files?.[0]
  if (!file) return

  originalFile.value = file
  fileExtension.value = file.name.split('.').pop() || 'mp4'

  // Create blob URL for preview
  const objectURL = URL.createObjectURL(file)
  blobUrl.value = objectURL
  mediaUrl.value = objectURL

  // Set video player source
  await nextTick()
  if (videoPlayerRef.value) {
    videoPlayerRef.value.src = objectURL
    videoPlayerRef.value.load()
  }

  toast.success(`Video selected: ${file.name}`)

  // Start background upload immediately
  startBackgroundUpload(file)
}

const startBackgroundUpload = async (file) => {
  uploadProgress.value = 1
  uploadComplete.value = false
  const { promise, abort } = uploadVideoInBackground(file, '/api/sot/upload/background', {
    onProgress: (p) => { uploadProgress.value = p }
  })
  uploadAbortFn = abort
  try {
    const response = await promise
    tempJobId.value = response.temp_job_id
    uploadComplete.value = true
    uploadProgress.value = 100
    setTimeout(() => { uploadProgress.value = 0 }, 1000)
    toast.success('Upload complete - ready to process')
  } catch (error) {
    if (error?.message === 'aborted') {
      uploadProgress.value = 0
      return // silent on user-initiated abort
    }
    console.error('Background upload error:', error)
    uploadProgress.value = 0
    toast.error('Upload failed: ' + error.message)
  } finally {
    uploadAbortFn = null
  }
}

const clearVideo = () => { // eslint-disable-line no-unused-vars
  // Cancel any in-flight upload so its stale onload doesn't write
  // to a reset modal.
  if (uploadAbortFn) {
    try { uploadAbortFn() } catch (_) { /* noop */ }
    uploadAbortFn = null
  }

  if (videoPlayerRef.value) {
    videoPlayerRef.value.pause()
    videoPlayerRef.value.src = ''
  }

  mediaUrl.value = ''
  blobUrl.value = ''
  duration.value = ''
  originalFile.value = null

  // Clear upload state
  uploadProgress.value = 0
  tempJobId.value = null
  uploadComplete.value = false

  if (previewInterval.value) {
    clearInterval(previewInterval.value)
    previewInterval.value = null
  }

  // Clear waveform
  showWaveform.value = false
  clearWaveform()

  toast.info('Video cleared')
}

// Clipping tools functions come from useMediaModalClips (destructured
// near the top): handleTakeClip, removeClip, handleDoubleEnterTake,
// handleClipSlugInput, handleClipSlugEnter, plus clipSlugNeedsAttention
// and pendingTakeOnSlug refs.


// Credits management
const addCredit = () => { // eslint-disable-line no-unused-vars
  credits.value.push({ key: `credit${credits.value.length + 1}`, value: '' })

  // Focus the new key input
  nextTick(() => {
    const inputs = creditsListRef.value?.querySelectorAll('input[type="text"]')
    if (inputs && inputs.length > 0) {
      const lastKeyInput = inputs[inputs.length - 2]
      lastKeyInput?.focus()
      lastKeyInput?.select()
    }
  })
}

const removeCredit = (index) => { // eslint-disable-line no-unused-vars
  credits.value.splice(index, 1)
}

// Form actions
const showTopError = (message) => {
  if (!topErrorEl.value) return
  topErrorEl.value.textContent = message
  topErrorEl.value.style.height = 'auto'
  topErrorEl.value.style.padding = '12px 20px'
  topErrorEl.value.style.marginBottom = '10px'

  setTimeout(() => {
    hideTopError()
  }, 10000)
}

const hideTopError = () => {
  if (!topErrorEl.value) return
  topErrorEl.value.style.height = '0'
  topErrorEl.value.style.padding = '0'
  topErrorEl.value.style.marginBottom = '0'
}

const generateAssetId = async () => {
  try {
    console.log('Requesting AssetID for SOT cue')

    // Create a slug from the SOT slug field
    const slugForAssetId = slug.value.trim()
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '') // Remove punctuation except spaces and hyphens
      .replace(/\s+/g, '-') // Convert spaces to hyphens
      .replace(/-+/g, '-') // Collapse multiple hyphens
      .replace(/^-+|-+$/g, '') // Remove leading/trailing hyphens
      .substring(0, 50) // Limit length

    // Create form data for the API call
    const formData = new FormData()
    formData.append('slug', slugForAssetId || 'sot-cue')
    formData.append('type', 'sot')

    // Try the legacy endpoint first (most reliable)
    const response = await axios.post('/assetid/generate-legacy', formData, {
      headers: {
        'Accept': 'application/json',
        'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
      }
    })

    if (response.data && response.data.id) {
      console.log('Successfully generated AssetID:', response.data.id)
      return response.data.id
    } else {
      throw new Error('Invalid response format: missing id field')
    }
  } catch (error) {
    console.warn('AssetID generation failed, using fallback:', error)

    // Fallback to local generation if server fails
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    let result = 'LOCAL_SOT_'
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    console.log('Generated local fallback AssetID:', result)
    return result
  }
}

const handleAddCue = async () => { // eslint-disable-line no-unused-vars
  console.log('🎬 handleAddCue called - slug:', slug.value)

  // Debounce protection: prevent double-submission
  if (isSubmitting.value) {
    console.log('⚠️ Already submitting, ignoring duplicate call')
    return
  }

  hideTopError()

  // Validate required fields
  // For individual-clips mode, main slug is not required - each clip has its own slug
  if (clippingMethod.value === 'individual-clips') {
    // Validate that we have clips
    if (clips.value.length === 0) {
      console.log('❌ Validation failed: No clips defined for individual-clips mode')
      showTopError('ERROR: Please add at least one clip using the TAKE button')
      return
    }
    // Validate each clip has a slug
    const clipsWithoutSlugs = clips.value.filter(c => !c.slug || !c.slug.trim())
    if (clipsWithoutSlugs.length > 0) {
      console.log('❌ Validation failed: Some clips are missing slugs')
      showTopError(`ERROR: ${clipsWithoutSlugs.length} clip(s) are missing slugs. Each clip needs a unique slug.`)
      return
    }
  } else if (!slug.value.trim()) {
    console.log('❌ Validation failed: Slug is required')
    showTopError('ERROR: Slug is required')
    return
  }

  // Validate video upload - must have either a completed background upload (tempJobId)
  // or an existing mediaUrl (for edit mode on already-processed SOTs)
  if (!tempJobId.value && !mediaUrl.value) {
    console.log('❌ Validation failed: No video uploaded')
    showTopError('ERROR: Please upload a video file before submitting')
    return
  }

  // If we have a blob URL but no tempJobId, the upload hasn't completed yet
  if (blobUrl.value && !tempJobId.value && !uploadComplete.value) {
    console.log('❌ Validation failed: Upload still in progress')
    showTopError('ERROR: Video upload still in progress. Please wait...')
    return
  }

  // Set submitting flag
  isSubmitting.value = true

  // Format credits as JSON (used for all modes)
  const creditsFormatted = credits.value
    .filter(c => c.key.trim() && c.value.trim())
    .reduce((acc, c) => {
      acc[c.key] = c.value
      return acc
    }, {})

  // INDIVIDUAL CLIPS MODE: Generate separate SOT for each clip
  if (clippingMethod.value === 'individual-clips') {
    console.log(`🎬 INDIVIDUAL CLIPS MODE: Processing ${clips.value.length} clips as independent SOTs`)

    // Show loading toast while generating AssetIDs
    const loadingToast = toast.info(`⏳ Assigning ${clips.value.length} AssetIDs...`, {
      timeout: false,
      closeButton: false
    })

    try {
      // Generate an AssetID for EACH clip
      const multipleSots = []
      for (const clip of clips.value) {
        const clipAssetId = await generateAssetId()
        console.log(`🆔 Generated AssetID for clip "${clip.slug}": ${clipAssetId}`)

        // Build complete SOT data for this clip
        const clipSotData = {
          assetId: clipAssetId,
          slug: clip.slug,
          description: description.value,
          mediaUrl: mediaUrl.value,
          duration: (() => {
            const s = timecodeToSeconds(clip.time_start || '00:00:00')
            const e = timecodeToSeconds(clip.time_end || '00:00:00')
            return e > s ? secondsToTimecode(e - s, true) : ''
          })(),
          trimStart: clip.time_start || '00:00:00',
          trimEnd: clip.time_end || '00:00:00',
          transcription: '', // Will be filled during processing
          thumbnailUrl: '', // Will be generated during processing
          credits: JSON.stringify(creditsFormatted),
          tempJobId: tempJobId.value,
          sourceJobId: tempJobId.value, // Reference to original upload for re-trimming
          originalTrimStart: clip.time_start || '00:00:00',
          originalTrimEnd: clip.time_end || '00:00:00',
          jobType: SOT_JOB_TYPES.SINGLE_TRIM, // Each clip processes independently
          clippingMethod: 'single-trim' // Process as simple single trim
        }

        multipleSots.push(clipSotData)
      }

      toast.dismiss(loadingToast)

      console.log(`📦 Emitting ${multipleSots.length} independent SOT cues:`, multipleSots)
      emit('submit-multiple', multipleSots)
      emit('update:show', false)

      toast.success(`🎬 ${multipleSots.length} clips queued for processing`)

    } catch (error) {
      toast.dismiss(loadingToast)
      console.error('❌ Failed to generate AssetIDs for clips:', error)
      showTopError(`ERROR: Failed to generate AssetIDs: ${error.message}`)
      isSubmitting.value = false
      return
    }

    resetForm()
    return
  }

  // STANDARD MODE (none, single-trim, montage): Single SOT emit
  let jobType = SOT_JOB_TYPES.FULL_PROCESS
  if (clippingMethod.value === 'none' || clippingMethod.value === 'single-trim') {
    jobType = SOT_JOB_TYPES.SINGLE_TRIM
  } else if (clippingMethod.value === 'montage') {
    jobType = SOT_JOB_TYPES.MONTAGE
  }

  // In standard edit mode (not re-upload), reuse the original AssetID so
  // the on-disk video and job records stay bound. Re-upload still mints a
  // new AssetID because the underlying media is being replaced.
  const isStandardEdit = props.editMode && !props.initialData?.isReupload && assetId.value
  let generatedAssetId
  if (isStandardEdit) {
    generatedAssetId = assetId.value
  } else {
    const loadingToast = toast.info('⏳ Assigning AssetID...', {
      timeout: false,
      closeButton: false
    })
    generatedAssetId = await generateAssetId()
    toast.dismiss(loadingToast)
  }

  // Build SOT cue data — use clipped duration when trim points are set
  const sotData = {
    assetId: generatedAssetId,
    slug: slug.value.trim(),
    description: description.value,
    mediaUrl: mediaUrl.value,
    duration: clipDuration.value || duration.value,
    trimStart: trimStart.value,
    trimEnd: trimEnd.value,
    transcription: transcription.value,
    thumbnailUrl: thumbnailUrl.value,
    credits: JSON.stringify(creditsFormatted),
    tempJobId: tempJobId.value,
    clippingMethod: clippingMethod.value,
    clips: clips.value.length > 0 ? JSON.stringify(clips.value) : null,
    jobType: jobType
  }

  console.log('SOT cue data:', sotData)
  console.log('✅ Submitting SOT cue and closing modal')
  emit('submit', sotData)
  emit('update:show', false)

  // Reset form (includes clearing isSubmitting flag)
  resetForm()
}

const cancel = () => { // eslint-disable-line no-unused-vars
  console.log('❌ User cancelled - closing modal')
  emit('update:show', false)
  resetForm()
}

// Handle ESC key with confirmation modal
const handleEscapeKey = () => { // eslint-disable-line no-unused-vars
  // ESC closes the SOT modal directly (no confirmation prompt). User
  // request: ESC should always close the topmost modal in focus.
  // If work is in progress (uploaded file, trim points, clips, form
  // data), `cancel()` still calls `resetForm()` which clears it.
  console.log('⎋ ESC pressed - closing SOT modal')
  cancel()
}

const resetForm = () => {
  slug.value = ''
  mediaUrl.value = ''
  blobUrl.value = ''
  duration.value = ''
  trimStart.value = '00:00:00'
  trimEnd.value = '00:00:00'
  description.value = ''
  airTime.value = ''
  airDate.value = ''
  transcription.value = ''
  credits.value = []
  originalFile.value = null

  // Reset clipping tools
  clippingMethod.value = 'none'
  clipSlug.value = ''
  clips.value = []
  clipCounter.value = 1

  // Reset debounce flag
  isSubmitting.value = false

  if (videoPlayerRef.value) {
    videoPlayerRef.value.pause()
    videoPlayerRef.value.src = ''
  }

  if (previewInterval.value) {
    clearInterval(previewInterval.value)
    previewInterval.value = null
  }
}

// Focus trap now lives in useFocusTrap composable.
const focusTrap = useFocusTrap(modalCardRef)
const setupFocusTrap = () => focusTrap.install()
const removeFocusTrap = () => focusTrap.uninstall()

// ESC handled by global modal stack — uniform with the other 20 modals.
// useMediaModalKeyboard no longer handles ESC itself.
registerModalEsc(() => props.show, () => handleEscapeKey(), 'SotModal')
useDoubleEnterToSlug(() => props.show, slugField)

// Lifecycle - DON'T setup keyboard shortcuts here, only when modal is shown
onMounted(() => {
  // Only setup if modal is already showing (edge case)
  if (props.show) {
    setupKeyboardShortcuts()
    nextTick(() => {
      setupFocusTrap()
    })
  }
})

// Watch for modal visibility changes
watch(
  () => props.show,
  (newValue, oldValue) => {
    console.log(`🔔 SOT Modal visibility changed: ${oldValue} → ${newValue}`)
    if (newValue && !oldValue) {
      // Modal opening - setup keyboard shortcuts and focus trap
      setupKeyboardShortcuts()
      nextTick(() => {
        setupFocusTrap()
        // Auto-focus first cut mode button when modal opens (follows tab order)
        // Use setTimeout to ensure DOM is fully rendered and focus trap is ready
        setTimeout(() => {
          if (firstCutModeButtonRef.value) {
            firstCutModeButtonRef.value.focus()
            // Also trigger the visual focus state
            handleCutModeFocus('none')
            console.log('🎯 Auto-focused first cut mode button (NONE)')
          } else if (slugField.value) {
            // Fallback to slug field if button ref not available
            slugField.value.focus()
            console.log('🎯 Fallback: Auto-focused slug field')
          }
        }, 100)
      })
    } else if (!newValue && oldValue) {
      // Modal closing - remove keyboard shortcuts and focus trap
      console.log('🚪 Modal closed - removing keyboard shortcuts and focus trap')
      removeKeyboardShortcuts()
      removeFocusTrap()
    }
  }
)

// Watch for edit mode - pre-populate form with initialData
watch(
  () => props.initialData,
  (newData) => {
    if (newData && props.editMode) {
      console.log('📝 Pre-populating SOT modal with:', newData)

      // Populate basic fields
      if (newData.assetId) assetId.value = newData.assetId
      if (newData.slug) slug.value = newData.slug
      if (newData.description) description.value = newData.description
      if (newData.duration) duration.value = newData.duration

      // Populate URLs
      if (newData.mediaUrl) mediaUrl.value = newData.mediaUrl
      if (newData.thumbnailUrl) thumbnailUrl.value = newData.thumbnailUrl

      // Populate trim times if available
      if (newData.trimStart) trimStart.value = newData.trimStart
      if (newData.trimEnd) trimEnd.value = newData.trimEnd

      // Populate transcription if available
      if (newData.transcription) transcription.value = newData.transcription

      // Populate credits if available
      if (newData.credits && Array.isArray(newData.credits)) {
        credits.value = [...newData.credits]
      }

      // Note: We don't populate clipping data since editing should work on the existing clip
      console.log('✅ SOT modal pre-populated')
    }
  },
  { immediate: true }
)

// Auto-populate Clip Slug for Single Trim mode
watch(
  [() => slug.value, () => clippingMethod.value],
  ([newSlug, newMethod]) => {
    // Only auto-populate when in Single Trim mode
    if (newMethod === 'single-trim') {
      clipSlug.value = newSlug
    }
  }
)

onBeforeUnmount(() => {
  // Keyboard handler, focus trap, preview interval, speed indicator
  // and frame counter timers all clean themselves up via their
  // composables' own onBeforeUnmount hooks. Only the blob URL is
  // owned here.
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value)
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');

/* Disable video player scrubber/timeline - use waveform instead */
:deep(video::-webkit-media-controls-timeline) {
  display: none !important;
  pointer-events: none !important;
}

:deep(video::-webkit-media-controls-current-time-display),
:deep(video::-webkit-media-controls-time-remaining-display) {
  display: none !important;
}

/* Firefox - hide timeline */
:deep(video::-moz-progress-bar) {
  display: none !important;
}

/* Fade animation for cut mode helper text */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide-down animation for clip duration */
.slide-down-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.slide-down-leave-active {
  transition: all 0.3s ease-in;
}

.slide-down-enter-from {
  transform: translateY(-20px);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

/* Clip box drop-in animation */
.clip-drop-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.clip-drop-leave-active {
  transition: all 0.3s ease-in;
}

.clip-drop-enter-from {
  transform: translateY(-30px) scale(0.8);
  opacity: 0;
}

.clip-drop-leave-to {
  transform: translateY(-15px) scale(0.9);
  opacity: 0;
}

.clip-drop-move {
  transition: transform 0.4s ease;
}

/* Speed indicator fade animation */
.speed-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.speed-fade-leave-active {
  transition: all 0.3s ease-out;
}

.speed-fade-enter-from {
  transform: scale(0.8);
  opacity: 0;
}

.speed-fade-leave-to {
  transform: scale(0.9);
  opacity: 0;
}

/* Frame counter fade animation */
.frame-counter-fade-enter-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.frame-counter-fade-leave-active {
  transition: all 0.2s ease-out;
}

.frame-counter-fade-enter-from {
  transform: translateX(-50%) translateY(20px);
  opacity: 0;
}

.frame-counter-fade-leave-to {
  transform: translateX(-50%) translateY(10px);
  opacity: 0;
}

/* Waveform slide-up animation */
.waveform-slide-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.waveform-slide-leave-active {
  transition: all 0.3s ease-in;
}

.waveform-slide-enter-from {
  transform: translateY(30px);
  opacity: 0;
}

.waveform-slide-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* Modal overlay with 70% transparency */
.v-overlay {
  background-color: rgba(0, 0, 0, 0.7) !important;
}

/* Custom toast styling for Mark IN (blue, from left) */
:deep(.mark-in-toast) {
  background-color: #2196F3 !important;
  border-left: 5px solid #1976D2 !important;
}

:deep(.mark-in-toast-body) {
  color: white !important;
  font-weight: bold !important;
  font-family: 'Helvetica', Arial, sans-serif !important;
}

/* Custom toast styling for Mark OUT (orange/red, from right) */
:deep(.mark-out-toast) {
  background-color: #FF5722 !important;
  border-right: 5px solid #E64A19 !important;
}

:deep(.mark-out-toast-body) {
  color: white !important;
  font-weight: bold !important;
  font-family: 'Helvetica', Arial, sans-serif !important;
}

/* Custom toast styling for Thumbnail marker (purple) */
:deep(.thumbnail-toast) {
  background-color: #9C27B0 !important;
  border-bottom: 5px solid #7B1FA2 !important;
}

:deep(.thumbnail-toast-body) {
  color: white !important;
  font-weight: bold !important;
  font-family: 'Helvetica', Arial, sans-serif !important;
}

/* Push toast container down to appear below IN/OUT point displays */
:global(.Vue-Toastification__container) {
  top: 140px !important;
}

/* Clip item hover effect */
.clip-item:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  transform: scale(1.03);
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.4);
}

/* Interior container scrollbar styling */
.interior-container::-webkit-scrollbar {
  width: 8px;
}

.interior-container::-webkit-scrollbar-track {
  background: #e0e0e0;
  border-radius: 4px;
}

.interior-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.interior-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Grid cell hover effects */
.grid-cell-empty:hover {
  background: #bbb !important;
  transform: scale(1.02);
  z-index: 100;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

.topgrid-cell:hover {
  background: #bbb !important;
  transform: scale(1.02);
  z-index: 100;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

/* Button hover effects handled in template inline styles */
</style>
