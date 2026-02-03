<template>
  <!-- Overlay Information Display (OUTSIDE v-dialog to avoid stacking context issues) -->
  <div v-if="show && mediaUrl" class="overlay-info-display" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10001;">
    <!-- Top Center: Large Timecode Display -->
    <div class="timecode-overlay" style="position: absolute; top: 5px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.85); padding: 14px 20px; border-radius: 9px; text-align: center; border: 2px solid rgba(255, 255, 255, 0.3); min-width: 520px;">
      <div style="display: flex; gap: 12px; align-items: center; justify-content: center;">
        <!-- Current Timecode (75% size) -->
        <div style="color: white; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(255, 255, 255, 0.5); width: 240px; display: inline-block; font-variant-numeric: tabular-nums;">{{ currentTimecode }}</div>
        <!-- Countdown Timecode (75% size, red text only) -->
        <div style="padding: 8px 12px;">
          <div style="color: #F44336; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(244, 67, 54, 0.8); width: 240px; display: inline-block; font-variant-numeric: tabular-nums;">-{{ remainingTimecode }}</div>
        </div>
      </div>
      <div style="color: #90CAF9; font-size: 10px; font-weight: bold; font-family: 'Helvetica', Arial, sans-serif; margin-top: 6px;">{{ currentActionDisplay }}</div>

      <!-- Clip Duration Display (slides down from behind timecode when IN and OUT are set) -->
      <transition name="slide-down">
        <div v-if="trimStart && trimEnd && clipDuration" class="clip-duration-display" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255, 255, 255, 0.2);">
          <div style="color: #81C784; font-size: 12px; font-weight: bold; margin-bottom: 4px;">CLIP DURATION</div>
          <div style="color: #4CAF50; font-size: 32px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(76, 175, 80, 0.5);">{{ clipDuration }}</div>
        </div>
      </transition>
    </div>

    <!-- Playback Speed Indicator (Top Right, appears on speed change) -->
    <transition name="speed-fade">
      <div v-if="showSpeedIndicator" class="speed-indicator" style="position: absolute; top: 20px; right: 50px; background: rgba(0, 0, 0, 0.9); padding: 20px; border-radius: 50%; width: 100px; height: 100px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 3px solid rgba(76, 175, 80, 0.8); box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);">
        <div style="color: #4CAF50; font-size: 32px; font-weight: bold; font-family: 'Roboto Mono', monospace; text-shadow: 0 0 10px rgba(76, 175, 80, 0.8);">{{ playbackSpeed.toFixed(2) }}×</div>
        <div style="color: #81C784; font-size: 10px; font-weight: bold; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;">{{ speedLabel }}</div>
      </div>
    </transition>

    <!-- Frame Counter (Bottom Center, appears during frame stepping) -->
    <transition name="frame-counter-fade">
      <div v-if="showFrameCounter" class="frame-counter" style="position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.9); padding: 15px 30px; border-radius: 8px; border: 2px solid rgba(156, 39, 176, 0.8); box-shadow: 0 0 20px rgba(156, 39, 176, 0.5);">
        <div style="color: #9C27B0; font-size: 12px; font-weight: bold; margin-bottom: 4px; text-align: center; text-transform: uppercase; letter-spacing: 1px;">Frame</div>
        <div style="color: white; font-size: 28px; font-weight: bold; font-family: 'Roboto Mono', monospace; text-shadow: 0 0 10px rgba(156, 39, 176, 0.8); text-align: center;">
          {{ currentFrameNumber }} <span style="color: rgba(255,255,255,0.5); font-size: 18px;">/</span> {{ totalFrames }}
        </div>
        <div style="color: #CE93D8; font-size: 10px; font-weight: bold; margin-top: 4px; text-align: center; font-family: 'Helvetica', Arial, sans-serif;">{{ frameStepDirection }}</div>
      </div>
    </transition>

    <!-- Top Left: IN Point Display -->
    <div style="position: absolute; top: 5px; left: 50px;">
      <div class="in-point-display" style="background: rgba(33, 150, 243, 0.9); padding: 14px 20px; border-radius: 9px; border-left: 6px solid #1976D2; border: 2px solid rgba(33, 150, 243, 0.5); min-width: 200px;">
        <div style="color: rgba(255,255,255,0.8); font-size: 10px; font-weight: bold; margin-bottom: 4px;">◄ IN POINT</div>
        <div style="color: white; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(33, 150, 243, 0.5);">{{ trimStart || '--:--:--:--' }}</div>
      </div>
    </div>

    <!-- Left Side: Hotkeys List (below center timecode, extends to bottom) -->
    <div style="position: absolute; top: 100px; left: 50px; bottom: 70px; z-index: 999999;">
      <div class="hotkeys-list" style="background: rgba(0, 0, 0, 0.92); padding: 15px; border-radius: 8px; width: 350px; height: 100%; display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        <!-- Header at top -->
        <div @click="showHotkeys = !showHotkeys" style="color: white; font-size: 14px; font-weight: bold; border-bottom: 2px solid rgba(255, 255, 255, 0.3); padding-bottom: 6px; cursor: pointer; margin-bottom: 8px;">
          ⌨️ HOTKEYS <span style="font-size: 10px; opacity: 0.6;">{{ showHotkeys ? '▼' : '▶' }}</span>
          <span style="color: rgba(255,255,255,0.5); font-size: 9px; margin-left: 10px;">CTRL+1</span>
        </div>
        <!-- Content expands downward to fill available space -->
        <div v-show="showHotkeys" style="color: white; font-size: 11px; line-height: 1.6; font-family: 'Helvetica', Arial, sans-serif; flex: 1; overflow-y: auto; padding-right: 8px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">SPACE</span><span>Play/Pause</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">SHIFT+SPACE</span><span>Preview</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">I</span><span>Mark IN</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">O</span><span>Mark OUT</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">Q</span><span>Go to IN</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">W</span><span>Go to OUT</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">K</span><span>Play/Pause</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">J / L</span><span>-1s / +1s</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">← / →</span><span>-1f / +1f</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #90CAF9; font-weight: bold;">↑ / ↓</span><span>-10s / +10s</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #4CAF50; font-weight: bold;">[ / ]</span><span style="color: #4CAF50;">Speed -/+</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #4CAF50; font-weight: bold;">\</span><span style="color: #4CAF50;">Speed 1×</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #9C27B0; font-weight: bold;">ALT+T</span><span style="color: #9C27B0;">Mark Thumb</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #FF9800; font-weight: bold;">CTRL+ENTER</span><span style="color: #FF9800;">Take Clip</span></div>
          <div v-if="clippingMethod === 'individual-clips'" style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #FFEB3B; font-weight: bold;">ENTER×2</span><span style="color: #FFEB3B;">Take Clip</span></div>
          <!-- Type of Cut Hotkeys -->
          <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); margin-bottom: 6px; color: rgba(255,255,255,0.7); font-size: 10px;">TYPE OF CUT</div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="color: #64B5F6; font-weight: bold;">N</span><span style="color: #64B5F6;">None</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="color: #64B5F6; font-weight: bold;">S</span><span style="color: #64B5F6;">Single Trim</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="color: #64B5F6; font-weight: bold;">M</span><span style="color: #64B5F6;">Multiple Clips</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);"><span style="color: #4CAF50; font-weight: bold;">ALT+ENTER</span><span style="color: #4CAF50;">Submit</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #F44336; font-weight: bold;">ESC</span><span style="color: #F44336;">Cancel</span></div>
        </div>
      </div>
    </div>

    <!-- Top Right: OUT Point Display (aligned with center timecode) -->
    <div style="position: absolute; top: 5px; right: 50px;">
      <div class="out-point-display" style="background: rgba(255, 87, 34, 0.9); padding: 14px 20px; border-radius: 9px; border-right: 6px solid #E64A19; border: 2px solid rgba(255, 87, 34, 0.5); min-width: 200px;">
        <div style="color: rgba(255,255,255,0.8); font-size: 10px; font-weight: bold; margin-bottom: 4px; text-align: right;">OUT POINT ►</div>
        <div style="color: white; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(255, 87, 34, 0.5); text-align: right;">{{ trimEnd || '--:--:--:--' }}</div>
      </div>

      <!-- Thumbnail Marker Display (only when thumbnail is set) - pushed down to clear toast area -->
      <transition name="clip-drop">
        <div v-if="thumbnailTimecode && thumbnailTimecode !== '00:00:00:00'" class="thumbnail-marker-display" style="background: rgba(156, 39, 176, 0.9); padding: 14px 18px; border-radius: 10px; border-right: 8px solid #7B1FA2; margin-top: 70px; margin-bottom: 15px; pointer-events: auto; max-width: 400px;">
          <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 6px; text-align: right;">📸 THUMBNAIL</div>
          <div style="color: white; font-size: 20px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 1px; text-align: right;">{{ thumbnailTimecode }}</div>
        </div>
      </transition>

      <!-- Individual Clip Boxes (drop in under thumbnail) - first clip has margin-top to clear toast if no thumbnail -->
      <transition-group name="clip-drop">
        <div
          v-for="(clip, index) in clips"
          :key="`clip-${index}`"
          class="clip-box"
          :style="{
            background: 'rgba(255, 152, 0, 0.9)',
            padding: '10px 15px',
            borderRadius: '10px',
            borderRight: '8px solid #F57C00',
            marginBottom: '8px',
            marginTop: (index === 0 && (!thumbnailTimecode || thumbnailTimecode === '00:00:00:00')) ? '70px' : '0',
            pointerEvents: 'auto',
            maxWidth: '560px'
          }"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="color: white; font-size: 18px; font-weight: bold;">CLIP {{ index + 1 }}</div>
            <button @click="removeClip(index)" style="background: #f44336; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 13px; cursor: pointer; font-weight: bold; transition: all 0.2s;">✕</button>
          </div>
          <input
            v-model="clip.slug"
            placeholder="clip-slug-here"
            style="width: 100%; padding: 6px; margin-bottom: 6px; background: rgba(255, 255, 255, 0.2); border: 2px solid rgba(255, 255, 255, 0.4); border-radius: 6px; color: white; font-size: 16px; font-weight: bold; font-family: 'Roboto Mono', monospace;"
            @click.stop
          />
          <div style="color: white; font-size: 14px; font-family: 'Roboto Mono', monospace; margin-bottom: 2px;">{{ clip.time_start }} → {{ clip.time_end }}</div>
          <div style="color: rgba(255, 255, 255, 0.7); font-size: 13px; font-family: 'Roboto Mono', monospace;">Duration: {{ Math.round(clip.duration_seconds) }}s</div>
        </div>
      </transition-group>

      <!-- Single Trim Clip Card (shows when in single-trim mode with IN/OUT set) - has margin-top to clear toast if no thumbnail -->
      <transition name="clip-drop">
        <div
          v-if="clippingMethod === 'single-trim' && trimStart && trimEnd && clipDuration"
          key="single-trim-card"
          class="clip-box"
          :style="{
            background: 'rgba(33, 150, 243, 0.9)',
            padding: '18px',
            borderRadius: '10px',
            borderRight: '8px solid #1976D2',
            marginTop: (!thumbnailTimecode || thumbnailTimecode === '00:00:00:00') ? '70px' : '0',
            marginBottom: '12px',
            pointerEvents: 'auto',
            maxWidth: '400px'
          }"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="color: white; font-size: 18px; font-weight: bold;">SINGLE TRIM</div>
          </div>
          <div style="color: white; font-size: 16px; font-weight: bold; font-family: 'Roboto Mono', monospace; margin-bottom: 8px;">{{ clipSlug || slug || 'untitled' }}</div>
          <div style="color: white; font-size: 14px; font-family: 'Roboto Mono', monospace; margin-bottom: 4px;">{{ trimStart }} → {{ trimEnd }}</div>
          <div style="color: rgba(255, 255, 255, 0.7); font-size: 13px; font-family: 'Roboto Mono', monospace;">Duration: {{ clipDuration }}</div>
        </div>
      </transition>
    </div>
  </div>

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
                <!-- Multiple Clips Button -->
                <div
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
            <transition name="waveform-slide">
              <div v-if="showWaveform && waveformData.length > 0" class="waveform-wrapper" style="width: 100%; margin-bottom: 15px;">
                <AudioWaveform
                  :waveform-data="waveformData"
                  :current-time="videoPlayerRef?.currentTime || 0"
                  :duration="videoPlayerRef?.duration || 0"
                  :height="60"
                  background-color="rgba(0, 0, 0, 0.7)"
                  wave-color="#4CAF50"
                  progress-color="#81C784"
                  playhead-color="#FF5722"
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

          <!-- Transcription -->
          <div class="mb-3">
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

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import AudioWaveform from '../AudioWaveform.vue'
import { useWaveform } from '../../composables/useWaveform'
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap'

// SOT Processing Job Types
// These define what type of processing the backend should perform
const SOT_JOB_TYPES = {
  SINGLE_TRIM: 'single_trim',           // Standard SOT with optional trim
  INDIVIDUAL_CLIPS: 'individual_clips', // Extract multiple separate clips
  MONTAGE: 'montage',                   // Combine clips into single video
  FULL_PROCESS: 'full_process'          // Complete normalization pipeline
}

export default {
  name: 'SotModal',
  components: {
    AudioWaveform
  },
  props: {
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
  },
  emits: ['update:show', 'submit', 'submit-multiple'],
  setup(props, { emit }) {
    const toast = useToast()

    // Waveform composable
    const { waveformData, isAnalyzing, extractWaveform, clearWaveform } = useWaveform()

    // Form refs
    const sotFormRef = ref(null)
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

    // Form data
    const assetId = ref('Generated on save')
    const slug = ref('')
    const mediaUrl = ref('')
    const thumbnailUrl = ref('')
    const duration = ref('')
    const trimStart = ref('00:00:00')
    const trimEnd = ref('00:00:00')
    const description = ref('')
    const airTime = ref('')
    const airDate = ref('')
    const transcription = ref('')
    const credits = ref([])

    // Video state
    const currentFramerate = ref(30)
    const isPlaying = ref(false)
    const currentTimecode = ref('00:00:00:00')
    const durationTimecode = ref('00:00:00:00')
    const remainingTimecode = ref('00:00:00:00')
    const previewInterval = ref(null)
    const videoSpecs = ref({})
    const blobUrl = ref('')
    const fileExtension = ref('')
    const originalFile = ref(null)

    // Background upload state
    const uploadProgress = ref(0)
    const tempJobId = ref(null)
    const uploadComplete = ref(false)
    const isSubmitting = ref(false) // Debounce flag for Alt+Enter

    // Clipping tools state
    const clippingMethod = ref('none')
    const clipSlug = ref('')
    const clips = ref([])
    const clipCounter = ref(1)

    // Type of Cut keyboard navigation
    const focusedCutMode = ref(null) // Tracks which button is focused during Tab navigation
    const focusedVideoButton = ref(null) // Tracks which video source button is focused
    const showCutModeHelp = ref(false) // Show helper text when Tab-navigating

    // Cut mode descriptions (shown when Tab-navigating)
    const cutModeDescriptions = {
      'none': 'Insert SOT cue without video processing',
      'single-trim': 'Extract one clip from video with IN/OUT points',
      'individual-clips': 'Extract multiple separate clips, each as its own SOT',
      'removal': 'Remove sections from video (Coming Soon)',
      'montage': 'Combine multiple clips into single video (Coming Soon)'
    }

    // Double-Enter TAKE functionality
    const clipSlugInputRef = ref(null)
    const clipSlugLabelRef = ref(null)
    const localFileButtonRef = ref(null)
    const lastEnterTime = ref(0)
    const pendingTakeOnSlug = ref(false) // Auto-retry TAKE when slug is entered
    const clipSlugNeedsAttention = ref(false) // For styling the input when validation fails
    const DOUBLE_ENTER_THRESHOLD = 400 // milliseconds

    // Keyboard handler
    const keyboardHandler = ref(null)

    // Overlay display state
    const currentActionDisplay = ref('READY')
    const thumbnailTimecode = ref('')

    // Playback speed state
    const playbackSpeed = ref(1.0)
    const showSpeedIndicator = ref(false)
    const speedIndicatorTimer = ref(null)
    const SPEED_PRESETS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]

    // Frame counter state
    const showFrameCounter = ref(false)
    const frameCounterTimer = ref(null)
    const currentFrameNumber = ref(0)
    const totalFrames = ref(0)
    const frameStepDirection = ref('')

    // Waveform state
    const showWaveform = ref(false)

    // Hotkeys visibility state (starts collapsed)
    const showHotkeys = ref(false)

    // Computed: Clip duration display
    const clipDuration = computed(() => {
      if (!trimStart.value || !trimEnd.value) return null
      const startSeconds = timecodeToSeconds(trimStart.value)
      const endSeconds = timecodeToSeconds(trimEnd.value)
      const durationSeconds = endSeconds - startSeconds
      if (durationSeconds <= 0) return null
      return secondsToTimecode(durationSeconds, true)
    })

    // Computed: Speed label
    const speedLabel = computed(() => {
      if (playbackSpeed.value < 1.0) return 'Slow Motion'
      if (playbackSpeed.value > 1.0) return 'Fast Forward'
      return 'Normal Speed'
    })

    // Computed: Color values for validation feedback
    const locatorFlashColor = computed(() => {
      const colorName = getColorValue('locatorflash') || getColorValue('locatorflash-interface') || 'deep-orange-accent-2'
      return resolveVuetifyColor(colorName)
    })

    const needsAttentionColor = computed(() => {
      const colorName = getColorValue('needs-attention') || 'orange-lighten-3'
      return resolveVuetifyColor(colorName)
    })

    // Selection color for focused UI elements (Tab navigation highlight)
    const selectionColor = computed(() => {
      const colorName = getColorValue('selection') || 'warning'
      return resolveVuetifyColor(colorName)
    })

    // Utility functions
    const secondsToTimecode = (seconds, showFrames = true) => {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      const frames = Math.floor((seconds % 1) * currentFramerate.value)

      if (showFrames) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`
      } else {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }
    }

    const timecodeToSeconds = (timecode) => {
      const parts = timecode.split(':').map(p => parseInt(p, 10))
      if (parts.length === 3) {
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
      } else if (parts.length === 4) {
        const frames = parts[3] / currentFramerate.value
        return parts[0] * 3600 + parts[1] * 60 + parts[2] + frames
      }
      return 0
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
    }

    const getDarkerColor = (color) => {
      // Simple darkening - reduce brightness
      const hex = color.replace('#', '')
      const r = Math.max(0, parseInt(hex.substr(0, 2), 16) - 30)
      const g = Math.max(0, parseInt(hex.substr(2, 2), 16) - 30)
      const b = Math.max(0, parseInt(hex.substr(4, 2), 16) - 30)
      return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
    }

    // Button hover effects
    const hoverButton = (e, baseColor) => {
      const darkerColor = getDarkerColor(baseColor)
      e.currentTarget.querySelectorAll('div').forEach((div, idx) => {
        if (idx === 0) div.style.background = getDarkerColor(darkerColor)
        else div.style.background = darkerColor
      })
      e.currentTarget.style.transform = 'scale(1.05)'
      e.currentTarget.style.zIndex = '100'
      e.currentTarget.style.boxShadow = `0 4px 12px ${baseColor}66`
    }

    const unhoverButton = (e, baseColor) => {
      const sections = e.currentTarget.querySelectorAll('div')
      if (sections.length >= 2) {
        sections[0].style.background = getDarkerColor(baseColor)
        sections[1].style.background = baseColor
      }
      e.currentTarget.style.transform = 'scale(1)'
      e.currentTarget.style.zIndex = '13'
      e.currentTarget.style.boxShadow = 'none'
    }

    const animateButtonPress = (button) => {
      if (!button) return
      button.style.transform = 'scale(0.95)'
      setTimeout(() => {
        button.style.transform = 'scale(1)'
      }, 100)
    }

    // Type of Cut keyboard navigation handlers
    const handleCutModeFocus = (mode) => {
      focusedCutMode.value = mode
      showCutModeHelp.value = true
    }

    const handleCutModeBlur = () => {
      focusedCutMode.value = null
      // Delay hiding help text to allow for Tab to next button
      setTimeout(() => {
        if (!focusedCutMode.value) {
          showCutModeHelp.value = false
        }
      }, 100)
    }

    // Video source button focus/blur handlers
    const handleVideoButtonFocus = (button) => {
      focusedVideoButton.value = button
    }

    const handleVideoButtonBlur = () => {
      focusedVideoButton.value = null
    }

    const selectCutMode = (mode, fromKeyboard = false) => {
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

    const handleCutModeKeydown = (event, mode) => {
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault()
        event.stopPropagation()
        selectCutMode(mode, true)
      }
    }

    // Video control actions
    const performMarkInAction = () => {
      if (!videoPlayerRef.value) return
      trimStart.value = secondsToTimecode(videoPlayerRef.value.currentTime, true)  // Frame-accurate
      animateButtonPress(markInBtn.value)

      // Auto-switch to single-trim mode if currently "none"
      if (clippingMethod.value === 'none') {
        clippingMethod.value = 'single-trim'
        toast('Clipping mode switched to SINGLE TRIM', {
          type: 'success',
          position: 'top-center',
          timeout: 2500,
          icon: '✂️',
        })
      }

      // Show toast notification - blue color, slide from left
      toast(`IN point set: ${trimStart.value}`, {
        type: 'info',
        position: 'top-left',
        timeout: 2000,
        toastClassName: 'mark-in-toast',
        bodyClassName: 'mark-in-toast-body',
        icon: '◄',
      })
    }

    const performMarkOutAction = () => {
      if (!videoPlayerRef.value) return
      trimEnd.value = secondsToTimecode(videoPlayerRef.value.currentTime, true)  // Frame-accurate
      animateButtonPress(markOutBtn.value)

      // Auto-switch to single-trim mode if currently "none"
      if (clippingMethod.value === 'none') {
        clippingMethod.value = 'single-trim'
        toast('Clipping mode switched to SINGLE TRIM', {
          type: 'success',
          position: 'top-center',
          timeout: 2500,
          icon: '✂️',
        })
      }

      // Show toast notification - orange/red color, slide from right
      toast(`OUT point set: ${trimEnd.value}`, {
        type: 'warning',
        position: 'top-right',
        timeout: 2000,
        toastClassName: 'mark-out-toast',
        bodyClassName: 'mark-out-toast-body',
        icon: '►',
      })
    }

    const performGoToInAction = () => {
      if (!videoPlayerRef.value) return
      const seconds = timecodeToSeconds(trimStart.value)
      videoPlayerRef.value.currentTime = seconds
      animateButtonPress(goToInBtn.value)
    }

    const performGoToOutAction = () => {
      if (!videoPlayerRef.value) return
      const seconds = timecodeToSeconds(trimEnd.value)
      videoPlayerRef.value.currentTime = seconds
      animateButtonPress(goToOutBtn.value)
    }

    // Handle waveform scrubber seek
    const handleWaveformSeek = (time) => {
      if (!videoPlayerRef.value) return
      videoPlayerRef.value.currentTime = time
      updateTimecode()
    }

    const performPlayPauseAction = () => {
      if (!videoPlayerRef.value) return
      if (videoPlayerRef.value.paused) {
        videoPlayerRef.value.play()
        currentActionDisplay.value = 'PLAYING ▶'
      } else {
        videoPlayerRef.value.pause()
        currentActionDisplay.value = 'PAUSED ⏸'
      }
      animateButtonPress(playPauseBtn.value)
    }

    const performPreviewAction = () => {
      if (!videoPlayerRef.value) return

      // Clear any existing preview interval
      if (previewInterval.value) {
        clearInterval(previewInterval.value)
        previewInterval.value = null
      }

      const inPoint = timecodeToSeconds(trimStart.value)
      const outPoint = timecodeToSeconds(trimEnd.value)

      if (outPoint <= inPoint) {
        toast.warning('Out point must be after In point')
        return
      }

      currentActionDisplay.value = 'PREVIEW MODE 👁'
      videoPlayerRef.value.currentTime = inPoint
      videoPlayerRef.value.play()

      // Monitor playback and pause at Out point
      previewInterval.value = setInterval(() => {
        if (videoPlayerRef.value.currentTime >= outPoint) {
          videoPlayerRef.value.pause()
          currentActionDisplay.value = 'PREVIEW ENDED ⏹'
          clearInterval(previewInterval.value)
          previewInterval.value = null
        }
      }, 100)

      animateButtonPress(previewBtn.value)
    }

    const performTakeAction = () => {
      console.log('[SOT Modal] Take action - commit current cut')
      toast.info('Take: Current cut committed')
      animateButtonPress(takeBtn.value)
      // TODO: Implement multiple cuts storage system
    }

    const performStepBackFrame = () => {
      if (!videoPlayerRef.value) return
      const frameDuration = 1 / currentFramerate.value
      videoPlayerRef.value.currentTime = Math.max(0, videoPlayerRef.value.currentTime - frameDuration)
      currentActionDisplay.value = 'REVERSE 1 FRAME ◄|'
      animateButtonPress(step1fBackBtn.value)
      showFrameCounterBriefly('◄ BACKWARD')
    }

    const performStepForwardFrame = () => {
      if (!videoPlayerRef.value) return
      const frameDuration = 1 / currentFramerate.value
      videoPlayerRef.value.currentTime = Math.min(videoPlayerRef.value.duration || 0, videoPlayerRef.value.currentTime + frameDuration)
      currentActionDisplay.value = 'FORWARD 1 FRAME |►'
      animateButtonPress(step1fForwardBtn.value)
      showFrameCounterBriefly('FORWARD ►')
    }

    const performStepBackSecond = () => {
      if (!videoPlayerRef.value) return
      videoPlayerRef.value.currentTime = Math.max(0, videoPlayerRef.value.currentTime - 1)
      currentActionDisplay.value = 'BACK 1 SECOND ◄◄'
      animateButtonPress(step1sBackBtn.value)
    }

    const performStepForwardSecond = () => {
      if (!videoPlayerRef.value) return
      videoPlayerRef.value.currentTime = Math.min(videoPlayerRef.value.duration || 0, videoPlayerRef.value.currentTime + 1)
      currentActionDisplay.value = 'FORWARD 1 SECOND ►►'
      animateButtonPress(step1sForwardBtn.value)
    }

    const performJumpBackTenSeconds = () => {
      if (!videoPlayerRef.value) return
      videoPlayerRef.value.currentTime = Math.max(0, videoPlayerRef.value.currentTime - 10)
      currentActionDisplay.value = 'JUMP BACK 10s ◄◄◄'
      animateButtonPress(step10sBackBtn.value)
    }

    const performJumpForwardTenSeconds = () => {
      if (!videoPlayerRef.value) return
      videoPlayerRef.value.currentTime = Math.min(videoPlayerRef.value.duration || 0, videoPlayerRef.value.currentTime + 10)
      currentActionDisplay.value = 'JUMP FORWARD 10s ►►►'
      animateButtonPress(step10sForwardBtn.value)
    }

    // Thumbnail marker function
    const setThumbnailTimecode = () => {
      if (!videoPlayerRef.value) return
      thumbnailTimecode.value = currentTimecode.value
      toast.success(`📸 Thumbnail marker set at ${thumbnailTimecode.value}`, {
        position: 'bottom-center',
        timeout: 2000,
        toastClassName: 'thumbnail-toast',
        bodyClassName: 'thumbnail-toast-body',
      })
      currentActionDisplay.value = '📸 THUMBNAIL MARKED'
    }

    // Playback speed control functions
    const setPlaybackSpeed = (speed) => {
      if (!videoPlayerRef.value) return

      // Clamp speed between 0.25x and 4.0x
      const clampedSpeed = Math.max(0.25, Math.min(4.0, speed))
      playbackSpeed.value = clampedSpeed
      videoPlayerRef.value.playbackRate = clampedSpeed

      // Show speed indicator with auto-hide
      showSpeedIndicatorBriefly()

      // Update action display
      if (clampedSpeed < 1.0) {
        currentActionDisplay.value = `SLOW MOTION ${clampedSpeed.toFixed(2)}×`
      } else if (clampedSpeed > 1.0) {
        currentActionDisplay.value = `FAST FORWARD ${clampedSpeed.toFixed(2)}×`
      } else {
        currentActionDisplay.value = 'NORMAL SPEED 1.00×'
      }

      console.log(`🎬 Playback speed set to ${clampedSpeed.toFixed(2)}×`)
    }

    const increasePlaybackSpeed = () => {
      // Find next preset speed above current
      const currentSpeed = playbackSpeed.value
      const nextSpeed = SPEED_PRESETS.find(s => s > currentSpeed) || 4.0
      setPlaybackSpeed(nextSpeed)
      toast.info(`Speed: ${nextSpeed.toFixed(2)}×`, {
        position: 'top-center',
        timeout: 1500,
        toastClassName: 'speed-toast'
      })
    }

    const decreasePlaybackSpeed = () => {
      // Find next preset speed below current
      const currentSpeed = playbackSpeed.value
      const previousSpeed = SPEED_PRESETS.slice().reverse().find(s => s < currentSpeed) || 0.25
      setPlaybackSpeed(previousSpeed)
      toast.info(`Speed: ${previousSpeed.toFixed(2)}×`, {
        position: 'top-center',
        timeout: 1500,
        toastClassName: 'speed-toast'
      })
    }

    const resetPlaybackSpeed = () => {
      setPlaybackSpeed(1.0)
      toast.success('Speed reset to 1.0×', {
        position: 'top-center',
        timeout: 1500,
        toastClassName: 'speed-toast'
      })
    }

    const showSpeedIndicatorBriefly = () => {
      // Clear any existing timer
      if (speedIndicatorTimer.value) {
        clearTimeout(speedIndicatorTimer.value)
      }

      // Show indicator
      showSpeedIndicator.value = true

      // Hide after 2 seconds
      speedIndicatorTimer.value = setTimeout(() => {
        showSpeedIndicator.value = false
        speedIndicatorTimer.value = null
      }, 2000)
    }

    const showFrameCounterBriefly = (direction) => {
      if (!videoPlayerRef.value) return

      // Calculate current frame and total frames
      const currentTime = videoPlayerRef.value.currentTime
      const duration = videoPlayerRef.value.duration || 0
      const fps = currentFramerate.value

      currentFrameNumber.value = Math.floor(currentTime * fps)
      totalFrames.value = Math.floor(duration * fps)
      frameStepDirection.value = direction

      // Clear any existing timer
      if (frameCounterTimer.value) {
        clearTimeout(frameCounterTimer.value)
      }

      // Show counter
      showFrameCounter.value = true

      // Hide after 1.5 seconds
      frameCounterTimer.value = setTimeout(() => {
        showFrameCounter.value = false
        frameCounterTimer.value = null
      }, 1500)
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
    const handleVideoKeydown = (event) => {
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

    // Keyboard shortcuts setup
    const setupKeyboardShortcuts = () => {
      keyboardHandler.value = (event) => {
        // SAFETY CHECK: Only handle keyboard events when modal is visible
        // This prevents blocking space keys when the modal is mounted but not shown
        if (!props.show) {
          return
        }

        // ESC key - always handle with confirmation modal
        if (event.key === 'Escape') {
          event.preventDefault()
          event.stopPropagation()
          event.stopImmediatePropagation()
          handleEscapeKey()
          return
        }

        // Don't interfere with typing in input fields, EXCEPT for these shortcuts:
        // - Ctrl+Enter (TAKE)
        // - Shift+Space (Preview in-to-out)
        // - Alt+Enter (Submit for processing)
        // - Arrow keys in trim inputs
        if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
          // Allow Ctrl+Enter (TAKE) from any input
          if (event.key === 'Enter' && event.ctrlKey) {
            // Let it through to the switch statement
          }
          // Allow Alt+Enter (Submit) from any input
          else if (event.key === 'Enter' && event.altKey) {
            // Let it through to the switch statement
          }
          // Allow Shift+Space (Preview) from any input
          else if (event.key === ' ' && event.shiftKey) {
            // Let it through to the switch statement
          }
          // Allow arrow keys in trim inputs
          else if ((event.target === trimStartInputRef.value || event.target === trimEndInputRef.value) &&
              ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) {
            // Let it through to the switch statement
          }
          // Block all other keys when in input fields
          else {
            return
          }
        }

        // CRITICAL: Always prevent default for space to avoid page scroll
        // This must happen BEFORE the videoPlayerRef check, so even if no video is loaded,
        // pressing space won't scroll the page
        // Using stopPropagation and stopImmediatePropagation to fully block the event
        // from reaching the scrollable v-card-text container
        if (event.key === ' ') {
          event.preventDefault()
          event.stopPropagation()
          event.stopImmediatePropagation()
        }

        // CRITICAL: Handle Ctrl+1 BEFORE videoPlayerRef check to toggle hotkeys menu
        // This must work even when no video is loaded
        if (event.key === '1' && event.ctrlKey) {
          event.preventDefault()
          event.stopPropagation()
          event.stopImmediatePropagation()
          showHotkeys.value = !showHotkeys.value
          return // Fully handled, don't continue
        }

        if (!videoPlayerRef.value) return

        let handled = true

        switch(event.key) {
          case ' ': // Space - Play/Pause or Preview with Shift
            event.preventDefault()
            if (event.shiftKey) {
              performPreviewAction()
            } else {
              performPlayPauseAction()
            }
            break

          case 'j':
          case 'J': // J - Step back 1 second
            event.preventDefault()
            performStepBackSecond()
            break

          case 'k':
          case 'K': // K - Play/Pause
            event.preventDefault()
            performPlayPauseAction()
            break

          case 'l':
          case 'L': // L - Step forward 1 second
            event.preventDefault()
            performStepForwardSecond()
            break

          case 'ArrowLeft': // Left Arrow - Frame/second/10-second step back
            event.preventDefault()
            if (event.ctrlKey) {
              performJumpBackTenSeconds()
            } else if (event.shiftKey) {
              // Step back 10 frames
              if (videoPlayerRef.value) {
                videoPlayerRef.value.currentTime = Math.max(0, videoPlayerRef.value.currentTime - (10 / currentFramerate.value))
              }
            } else {
              performStepBackFrame()
            }
            break

          case 'ArrowRight': // Right Arrow - Frame/second/10-second step forward
            event.preventDefault()
            if (event.ctrlKey) {
              performJumpForwardTenSeconds()
            } else if (event.shiftKey) {
              // Step forward 10 frames
              if (videoPlayerRef.value) {
                const duration = videoPlayerRef.value.duration || 0
                videoPlayerRef.value.currentTime = Math.min(duration, videoPlayerRef.value.currentTime + (10 / currentFramerate.value))
              }
            } else {
              performStepForwardFrame()
            }
            break

          case 'ArrowUp': // Up Arrow - Jump forward 10 seconds
            event.preventDefault()
            performJumpForwardTenSeconds()
            break

          case 'ArrowDown': // Down Arrow - Jump back 10 seconds
            event.preventDefault()
            performJumpBackTenSeconds()
            break

          case 'i':
          case 'I': // I - Mark In
            event.preventDefault()
            performMarkInAction()
            break

          case 'o':
          case 'O': // O - Mark Out
            event.preventDefault()
            performMarkOutAction()
            break

          case 'q':
          case 'Q': // Q - Go to In
            event.preventDefault()
            performGoToInAction()
            break

          case 'w':
          case 'W': // W - Go to Out
            event.preventDefault()
            performGoToOutAction()
            break

          case 'Enter': // Ctrl+Enter - Take, Alt+Enter - Submit/Inject, Double-Enter - Take (multiple clips mode)
            if (event.ctrlKey) {
              event.preventDefault()
              performTakeAction()
            } else if (event.altKey) {
              event.preventDefault()
              handleAddCue() // Submit and close modal
            } else if (!event.shiftKey && clippingMethod.value === 'individual-clips') {
              // Double-Enter detection for multiple clips mode
              const now = Date.now()
              const timeSinceLastEnter = now - lastEnterTime.value

              if (timeSinceLastEnter < DOUBLE_ENTER_THRESHOLD) {
                // Double-Enter detected!
                event.preventDefault()
                event.stopPropagation()
                console.log('🎬 Double-Enter detected - triggering TAKE')
                handleDoubleEnterTake()
                lastEnterTime.value = 0 // Reset to prevent triple-enter issues
              } else {
                // First Enter - record time
                lastEnterTime.value = now
                // Don't prevent default for single Enter (allow normal typing in fields)
              }
            }
            break

          case 't':
          case 'T': // Alt+T - Set Thumbnail
            if (event.altKey) {
              event.preventDefault()
              setThumbnailTimecode()
            } else {
              handled = false
            }
            break

          case '.': // Alt+. - Set Thumbnail
            if (event.altKey) {
              event.preventDefault()
              setThumbnailTimecode()
            } else {
              handled = false
            }
            break

          case '[': // [ - Decrease playback speed
            event.preventDefault()
            decreasePlaybackSpeed()
            break

          case ']': // ] - Increase playback speed
            event.preventDefault()
            increasePlaybackSpeed()
            break

          case '\\': // \ - Reset playback speed to 1x
            event.preventDefault()
            resetPlaybackSpeed()
            break

          case 'PageDown': // Page Down - Scroll to bottom of modal
            event.preventDefault()
            scrollToBottomOfModal()
            break

          // Type of Cut hotkeys (N, S, M, R, G)
          case 'n':
          case 'N': // N - None mode
            event.preventDefault()
            selectCutMode('none', true)
            break

          case 's':
          case 'S': // S - Single Trim mode
            event.preventDefault()
            selectCutMode('single-trim', true)
            break

          case 'm':
          case 'M': // M - Multiple Clips mode
            event.preventDefault()
            selectCutMode('individual-clips', true)
            break

          case 'r':
          case 'R': // R - Removal mode (disabled)
            event.preventDefault()
            selectCutMode('removal', true)
            break

          case 'g':
          case 'G': // G - Montage mode (disabled)
            event.preventDefault()
            selectCutMode('montage', true)
            break

          case 'b':
          case 'B': // B - Browse for local file
            event.preventDefault()
            triggerFileInput()
            break

          default:
            handled = false
            break
        }

        // CRITICAL: Stop ALL keyboard events from propagating when SOT modal is open
        // This prevents global shortcuts from interfering with video editing
        if (handled) {
          event.preventDefault()
          event.stopPropagation()
          event.stopImmediatePropagation()
        }
      }

      // Use capture phase to intercept ALL keyboard events before other handlers
      document.addEventListener('keydown', keyboardHandler.value, true)
    }

    // Video metadata handling
    const handleVideoMetadataLoaded = () => {
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

    const updateTimecode = () => {
      if (!videoPlayerRef.value || !timecodeDisplay.value) return

      const current = videoPlayerRef.value.currentTime
      const videoDuration = videoPlayerRef.value.duration || 0
      const remaining = videoDuration - current

      currentTimecode.value = secondsToTimecode(current, true)
      durationTimecode.value = secondsToTimecode(videoDuration, true)
      remainingTimecode.value = secondsToTimecode(remaining, true)
    }

    const updatePlayPauseState = () => {
      if (!videoPlayerRef.value) return
      isPlaying.value = !videoPlayerRef.value.paused
    }

    // File handling
    const triggerFileInput = () => {
      fileInputRef.value?.click()
    }

    const handleFileUpload = async (event) => {
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
      try {
        uploadProgress.value = 1 // Show progress bar
        uploadComplete.value = false

        const formData = new FormData()
        formData.append('file', file)

        const xhr = new XMLHttpRequest()

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            uploadProgress.value = Math.round((e.loaded / e.total) * 100)
          }
        })

        // Handle completion
        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText)
            tempJobId.value = response.temp_job_id
            uploadComplete.value = true
            uploadProgress.value = 100

            // Hide progress bar after 1 second
            setTimeout(() => {
              uploadProgress.value = 0
            }, 1000)

            toast.success('Upload complete - ready to process')
          } else {
            uploadProgress.value = 0
            toast.error('Upload failed: ' + xhr.statusText)
          }
        })

        // Handle errors
        xhr.addEventListener('error', () => {
          uploadProgress.value = 0
          toast.error('Upload failed - network error')
        })

        // Get auth token
        const token = localStorage.getItem('auth-token')
        const apiKey = localStorage.getItem('api_key')

        xhr.open('POST', '/api/sot/upload/background', true)

        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        } else if (apiKey) {
          xhr.setRequestHeader('X-API-Key', apiKey)
        }

        xhr.send(formData)

      } catch (error) {
        console.error('Background upload error:', error)
        uploadProgress.value = 0
        toast.error('Upload failed: ' + error.message)
      }
    }

    const clearVideo = () => {
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

    // Clipping tools functions
    const handleTakeClip = () => {
      // Validate time inputs
      if (!trimStart.value || !trimEnd.value) {
        toast.warning('Please set both time start and time end')
        return
      }

      // Validate time end is after time start
      const startSec = timecodeToSeconds(trimStart.value)
      const endSec = timecodeToSeconds(trimEnd.value)

      if (endSec <= startSec) {
        toast.warning('Time end must be after time start')
        return
      }

      // Get frame-accurate timecodes (with frames)
      let timeStartWithFrames = trimStart.value
      let timeEndWithFrames = trimEnd.value

      // If using video player, get exact frame-accurate timecodes
      if (videoPlayerRef.value) {
        // Already has frame info if in format HH:MM:SS:FF
        if (trimStart.value.split(':').length < 4) {
          timeStartWithFrames = secondsToTimecode(startSec, true)
        }
        if (trimEnd.value.split(':').length < 4) {
          timeEndWithFrames = secondsToTimecode(endSec, true)
        }
      }

      // Auto-generate clip slug if empty
      let finalClipSlug = clipSlug.value.trim()

      if (!finalClipSlug) {
        const baseSlug = slug.value.trim() || 'clip'

        if (clippingMethod.value === 'individual-clips') {
          finalClipSlug = `${baseSlug}_CLIP_${clipCounter.value}`
          clipCounter.value++
        } else if (clippingMethod.value === 'montage') {
          finalClipSlug = `${baseSlug}_MONTAGE`
        }
      }

      // Add clip to collection
      clips.value.push({
        slug: finalClipSlug,
        time_start: timeStartWithFrames,
        time_end: timeEndWithFrames,
        duration_seconds: endSec - startSec,
        transcript: '' // Initialize empty transcript for this clip
      })

      toast.success(`Clip "${finalClipSlug}" added`)

      // Clear fields for next clip
      if (clippingMethod.value === 'individual-clips') {
        clipSlug.value = '' // Clear to auto-generate next
      }
      // For montage, keep the slug

      trimStart.value = '00:00:00'
      trimEnd.value = '00:00:00'
    }

    const removeClip = (index) => {
      const removedClip = clips.value[index]
      clips.value.splice(index, 1)
      toast.info(`Removed clip "${removedClip.slug}"`)
    }

    // Triple-blink the clip slug input field with locator flash color
    const blinkClipSlugInput = async () => {
      const input = clipSlugInputRef.value
      if (!input) return

      const flashColor = locatorFlashColor.value
      const originalBorder = input.style.border
      const originalBoxShadow = input.style.boxShadow

      for (let i = 0; i < 3; i++) {
        // Flash on
        input.style.border = `3px solid ${flashColor}`
        input.style.boxShadow = `0 0 15px ${flashColor}, 0 0 30px ${flashColor}80`
        await new Promise(resolve => setTimeout(resolve, 120))

        // Flash off
        input.style.border = originalBorder || '1px solid #ddd'
        input.style.boxShadow = originalBoxShadow || 'none'
        await new Promise(resolve => setTimeout(resolve, 80))
      }
    }

    // Handle double-Enter TAKE with validation
    const handleDoubleEnterTake = async () => {
      // Check if we're in multiple clips mode
      if (clippingMethod.value !== 'individual-clips') {
        return false
      }

      // Check if we have IN and OUT points
      if (!trimStart.value || !trimEnd.value ||
          trimStart.value === '00:00:00' || trimEnd.value === '00:00:00') {
        toast.warning('Please set IN and OUT points first (I and O keys)')
        return false
      }

      // Check if we have a slug
      const hasSlug = clipSlug.value.trim().length > 0

      if (!hasSlug) {
        // Validation failed - no slug
        console.log('⚠️ Double-Enter TAKE failed: No clip slug provided')

        // Set needs attention state
        clipSlugNeedsAttention.value = true
        pendingTakeOnSlug.value = true

        // Triple blink with locator color
        await blinkClipSlugInput()

        // Focus on the clip slug input
        nextTick(() => {
          if (clipSlugInputRef.value) {
            clipSlugInputRef.value.focus()
            clipSlugInputRef.value.select()
          }
        })

        toast.warning('Please enter a clip slug to TAKE')
        return false
      }

      // All validation passed - execute TAKE
      handleTakeClip()
      return true
    }

    // Handle input changes in clip slug field - auto-retry if pending
    const handleClipSlugInput = () => {
      // Clear the needs attention state when user starts typing
      if (clipSlugNeedsAttention.value && clipSlug.value.trim().length > 0) {
        clipSlugNeedsAttention.value = false
      }
    }

    // Handle Enter keypress in clip slug field - auto-retry TAKE if pending
    const handleClipSlugEnter = (event) => {
      if (pendingTakeOnSlug.value && clipSlug.value.trim().length > 0) {
        event.preventDefault()
        event.stopPropagation()

        console.log('🎬 Auto-retrying TAKE after slug entered')

        // Clear pending state
        pendingTakeOnSlug.value = false
        clipSlugNeedsAttention.value = false

        // Execute the TAKE
        handleTakeClip()

        // Defocus the input and return focus to modal for keyboard shortcuts
        nextTick(() => {
          if (clipSlugInputRef.value) {
            clipSlugInputRef.value.blur()
          }
        })
      }
    }

    // Credits management
    const addCredit = () => {
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

    const removeCredit = (index) => {
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

    const handleAddCue = async () => {
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
      if (blobUrl.value && !tempJobId.value && uploadProgress.value < 100) {
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
              duration: '', // Will be calculated during processing
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

      // Show loading toast while generating AssetID
      const loadingToast = toast.info('⏳ Assigning AssetID...', {
        timeout: false,
        closeButton: false
      })

      // Generate AssetID
      const generatedAssetId = await generateAssetId()

      toast.dismiss(loadingToast)

      // Build SOT cue data
      const sotData = {
        assetId: generatedAssetId,
        slug: slug.value.trim(),
        description: description.value,
        mediaUrl: mediaUrl.value,
        duration: duration.value,
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

    const cancel = () => {
      console.log('❌ User cancelled - closing modal')
      emit('update:show', false)
      resetForm()
    }

    // Handle ESC key with confirmation modal
    const handleEscapeKey = () => {
      // Check if any work has been done that needs cleanup
      const hasUploadedFile = mediaUrl.value || blobUrl.value || originalFile.value
      const hasTrimPoints = trimStart.value !== '00:00:00' || trimEnd.value !== '00:00:00'
      const hasClips = clips.value && clips.value.length > 0
      const hasFormData = slug.value || description.value || transcription.value

      const hasAnyWork = hasUploadedFile || hasTrimPoints || hasClips || hasFormData

      if (!hasAnyWork) {
        // No work done, just close
        cancel()
        return
      }

      // Show confirmation dialog
      const confirmed = window.confirm(
        '⚠️ CLOSE SOT EDITOR?\n\n' +
        'This will:\n' +
        '• Discard all unsaved changes\n' +
        '• Clear uploaded video from memory\n' +
        '• Remove trim points and clips\n' +
        '• Cancel any pending processing\n\n' +
        'Are you sure you want to close?'
      )

      if (confirmed) {
        console.log('🗑️ User confirmed ESC - cleaning up and closing')
        // TODO: Add API call to clean up any temporary database entries or uploaded files
        // For now, just reset the form and close
        cancel()
      } else {
        console.log('🔄 User cancelled ESC - staying in modal')
      }
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

    // Remove keyboard shortcuts (for when modal closes)
    const removeKeyboardShortcuts = () => {
      if (keyboardHandler.value) {
        document.removeEventListener('keydown', keyboardHandler.value, true)
        keyboardHandler.value = null
        console.log('⌨️ SOT Modal keyboard shortcuts removed')
      }
    }

    // Focus trap handler reference
    const focusTrapHandler = ref(null)

    // Setup focus trap to keep Tab within the modal
    const setupFocusTrap = () => {
      if (focusTrapHandler.value) return // Already set up

      focusTrapHandler.value = (e) => {
        if (e.key !== 'Tab') return

        // Get the modal card element
        const modalEl = modalCardRef.value?.$el || modalCardRef.value
        if (!modalEl) return

        // Get all focusable elements within the modal
        const focusableSelectors = [
          'button:not([disabled])',
          'input:not([disabled])',
          'select:not([disabled])',
          'textarea:not([disabled])',
          '[tabindex]:not([tabindex="-1"]):not([disabled])',
          'a[href]'
        ].join(', ')

        const focusableElements = modalEl.querySelectorAll(focusableSelectors)
        const focusableArray = Array.from(focusableElements).filter(el => {
          // Filter out hidden elements
          return el.offsetParent !== null && !el.closest('[style*="display: none"]')
        })

        if (focusableArray.length === 0) return

        const firstElement = focusableArray[0]
        const lastElement = focusableArray[focusableArray.length - 1]

        // Check if current focus is outside the modal
        const currentFocus = document.activeElement
        const isInModal = modalEl.contains(currentFocus)

        if (!isInModal) {
          // Focus is outside modal, bring it back
          e.preventDefault()
          firstElement.focus()
          return
        }

        if (e.shiftKey) {
          // Shift+Tab: if on first element, go to last
          if (currentFocus === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          // Tab: if on last element, go to first
          if (currentFocus === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }

      // Use capture phase to intercept before other handlers
      document.addEventListener('keydown', focusTrapHandler.value, true)
      console.log('🔒 Focus trap enabled for SOT modal')
    }

    // Remove focus trap
    const removeFocusTrap = () => {
      if (focusTrapHandler.value) {
        document.removeEventListener('keydown', focusTrapHandler.value, true)
        focusTrapHandler.value = null
        console.log('🔓 Focus trap disabled for SOT modal')
      }
    }

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
      if (keyboardHandler.value) {
        document.removeEventListener('keydown', keyboardHandler.value, true)
      }

      // Clean up focus trap
      if (focusTrapHandler.value) {
        document.removeEventListener('keydown', focusTrapHandler.value, true)
      }

      if (previewInterval.value) {
        clearInterval(previewInterval.value)
      }

      if (speedIndicatorTimer.value) {
        clearTimeout(speedIndicatorTimer.value)
      }

      if (frameCounterTimer.value) {
        clearTimeout(frameCounterTimer.value)
      }

      // Clean up blob URL
      if (blobUrl.value) {
        URL.revokeObjectURL(blobUrl.value)
      }
    })

    return {
      // Refs
      sotFormRef,
      modalCardRef,
      fileInputRef,
      videoPlayerRef,
      trimStartInputRef,
      trimEndInputRef,
      topErrorEl,
      timecodeDisplay,
      videoInfoOverlay,
      creditsListRef,
      slugField,
      markInBtn,
      markOutBtn,
      goToInBtn,
      goToOutBtn,
      playPauseBtn,
      previewBtn,
      takeBtn,
      step10sBackBtn,
      step1sBackBtn,
      step1fBackBtn,
      step10sForwardBtn,
      step1sForwardBtn,
      step1fForwardBtn,

      // Form data
      assetId,
      slug,
      mediaUrl,
      thumbnailUrl,
      duration,
      trimStart,
      trimEnd,
      description,
      airTime,
      airDate,
      transcription,
      credits,

      // Video state
      currentFramerate,
      isPlaying,
      currentTimecode,
      durationTimecode,
      remainingTimecode,
      clipDuration,

      // Upload state
      uploadProgress,
      tempJobId,
      uploadComplete,

      // Clipping tools state
      clippingMethod,
      clipSlug,
      clips,
      clipSlugInputRef,
      clipSlugLabelRef,
      clipSlugNeedsAttention,
      needsAttentionColor,
      selectionColor,
      firstCutModeButtonRef,
      handleClipSlugInput,
      handleClipSlugEnter,
      localFileButtonRef,

      // Type of Cut keyboard navigation
      focusedCutMode,
      showCutModeHelp,
      cutModeDescriptions,
      handleCutModeFocus,
      handleCutModeBlur,
      selectCutMode,
      handleCutModeKeydown,
      focusedVideoButton,
      handleVideoButtonFocus,
      handleVideoButtonBlur,

      // Overlay display state
      currentActionDisplay,
      thumbnailTimecode,

      // Playback speed state
      playbackSpeed,
      showSpeedIndicator,
      speedLabel,

      // Frame counter state
      showFrameCounter,
      currentFrameNumber,
      totalFrames,
      frameStepDirection,

      // Waveform state
      showWaveform,
      waveformData,
      isAnalyzing,

      // Hotkeys visibility
      showHotkeys,

      // Actions
      triggerFileInput,
      handleFileUpload,
      clearVideo,
      handleTakeClip,
      removeClip,
      addCredit,
      removeCredit,
      handleAddCue,
      cancel,
      handleEscapeKey,
      hoverButton,
      unhoverButton,
      performMarkInAction,
      performMarkOutAction,
      performGoToInAction,
      performGoToOutAction,
      performPlayPauseAction,
      performPreviewAction,
      performTakeAction,
      handleWaveformSeek,
      performStepBackFrame,
      performStepForwardFrame,
      performStepBackSecond,
      performStepForwardSecond,
      performJumpBackTenSeconds,
      performJumpForwardTenSeconds,
      setThumbnailTimecode,
      increasePlaybackSpeed,
      decreasePlaybackSpeed,
      resetPlaybackSpeed,
      scrollToBottomOfModal,
      updateTimecode,
      updatePlayPauseState,
      handleVideoMetadataLoaded,
      handleVideoKeydown
    }
  }
}
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
