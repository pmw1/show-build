<template>
  <!-- Overlay Information Display (OUTSIDE v-dialog to avoid stacking context issues) -->
  <div v-if="show && mediaUrl" class="overlay-info-display" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10001;">
    <!-- Top Center: Large Timecode Display -->
    <div class="timecode-overlay" style="position: absolute; top: 5px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.85); padding: 14px 28px; border-radius: 9px; text-align: center; border: 2px solid rgba(255, 255, 255, 0.3); min-width: 380px;">
      <div style="color: white; font-size: 40px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 4px; text-shadow: 0 0 15px rgba(255, 255, 255, 0.5); width: 340px; display: inline-block; font-variant-numeric: tabular-nums;">{{ currentTimecode }}</div>
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
    <div style="position: absolute; top: 150px; left: 50px;">
      <div class="in-point-display" style="background: rgba(33, 150, 243, 0.9); padding: 30px; border-radius: 12px; border-left: 8px solid #1976D2; margin-bottom: 15px;">
        <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;">◄ IN POINT</div>
        <div style="color: white; font-size: 48px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 2px;">{{ trimStart || '--:--:--:--' }}</div>
      </div>

      <!-- Hotkeys List -->
      <div class="hotkeys-list" style="background: rgba(0, 0, 0, 0.85); padding: 20px; border-radius: 8px; max-width: 300px;">
        <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 12px; border-bottom: 2px solid rgba(255, 255, 255, 0.3); padding-bottom: 8px;">
          ⌨️ HOTKEYS
        </div>
        <div style="color: white; font-size: 12px; line-height: 1.8; font-family: 'Helvetica', Arial, sans-serif;">
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
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);"><span style="color: #4CAF50; font-weight: bold;">ALT+ENTER</span><span style="color: #4CAF50;">Submit</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #F44336; font-weight: bold;">ESC</span><span style="color: #F44336;">Cancel</span></div>
        </div>
      </div>
    </div>

    <!-- Top Right: OUT Point Display -->
    <div style="position: absolute; top: 150px; right: 50px;">
      <div class="out-point-display" style="background: rgba(255, 87, 34, 0.9); padding: 30px; border-radius: 12px; border-right: 8px solid #E64A19; margin-bottom: 15px;">
        <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px; text-align: right;">OUT POINT ►</div>
        <div style="color: white; font-size: 48px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 2px; text-align: right;">{{ trimEnd || '--:--:--:--' }}</div>
      </div>

      <!-- Thumbnail Marker Display -->
      <div class="thumbnail-marker-display" style="background: rgba(156, 39, 176, 0.9); padding: 20px; border-radius: 12px; border-right: 8px solid #7B1FA2; margin-bottom: 15px; pointer-events: auto;">
        <div style="color: white; font-size: 14px; font-weight: bold; margin-bottom: 8px; text-align: right;">THUMBNAIL</div>
        <div style="color: white; font-size: 24px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 1px; text-align: right; margin-bottom: 8px;">{{ thumbnailTimecode || '--:--:--:--' }}</div>
        <button @click="setThumbnailTimecode" style="background: rgba(255, 255, 255, 0.2); color: white; padding: 10px 20px; border: 2px solid rgba(255, 255, 255, 0.4); border-radius: 6px; font-size: 13px; font-weight: bold; cursor: pointer; width: 100%; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px;">
          <span>📸 MARK (ALT+T)</span>
        </button>
      </div>

      <!-- Individual Clip Boxes (drop in under thumbnail) -->
      <transition-group name="clip-drop">
        <div
          v-for="(clip, index) in clips"
          :key="`clip-${index}`"
          class="clip-box"
          style="background: rgba(255, 152, 0, 0.9); padding: 15px; border-radius: 10px; border-right: 8px solid #F57C00; margin-bottom: 12px; pointer-events: auto; max-width: 350px;"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="color: white; font-size: 16px; font-weight: bold;">CLIP {{ index + 1 }}</div>
            <button @click="removeClip(index)" style="background: #f44336; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 11px; cursor: pointer; font-weight: bold; transition: all 0.2s;">✕</button>
          </div>
          <input
            v-model="clip.slug"
            placeholder="clip-slug-here"
            style="width: 100%; padding: 8px; margin-bottom: 8px; background: rgba(255, 255, 255, 0.2); border: 2px solid rgba(255, 255, 255, 0.4); border-radius: 6px; color: white; font-size: 14px; font-weight: bold; font-family: 'Roboto Mono', monospace;"
            @click.stop
          />
          <div style="color: white; font-size: 12px; font-family: 'Roboto Mono', monospace; margin-bottom: 4px;">{{ clip.time_start }} → {{ clip.time_end }}</div>
          <div style="color: rgba(255, 255, 255, 0.7); font-size: 11px; font-family: 'Roboto Mono', monospace;">Duration: {{ Math.round(clip.duration_seconds) }}s</div>
        </div>
      </transition-group>
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
    <v-card class="sot-modal-card" style="max-height: 80vh; overflow: hidden;">
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
            style="color: white; min-width: 30px; height: 36px; font-size: 16px; font-weight: bold;"
            title="Close modal"
          >✕</v-btn>
          <v-btn
            @click="cancel"
            size="x-small"
            color="#666"
            variant="flat"
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
          <!-- Slug (Required) -->
          <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">
            Slug: <span style="color: red;">*</span>
          </label>
          <input
            ref="slugField"
            v-model="slug"
            class="cue-modal-input mb-3"
            type="text"
            placeholder="short-descriptive-name"
            style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
          />

          <!-- Select Video and Duration Row -->
          <div class="d-flex mb-3" style="gap: 20px;">
            <!-- Select Video Buttons (Left, flex: 2) -->
            <div style="flex: 2;">
              <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">
                Select Video: <span style="color: red;">*</span>
              </label>
              <div class="d-flex" style="gap: 3px;">
                <button
                  @click="triggerFileInput"
                  class="cue-modal-button-small"
                  type="button"
                  style="padding: 15px 30px; font-size: 14px; min-width: 120px; background: #87CEEB; color: white; border: 1px solid #87CEEB; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;"
                  title="Browse for video file"
                >Local File</button>
                <button
                  @click="clearVideo"
                  class="cue-modal-button-small"
                  type="button"
                  style="padding: 15px 30px; font-size: 14px; min-width: 120px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;"
                  title="Clear selected video"
                >Clear</button>
              </div>
              <input
                ref="fileInputRef"
                type="file"
                accept="video/*"
                style="display: none;"
                @change="handleFileUpload"
              />
            </div>

            <!-- Duration Display (Right, flex: 1) -->
            <div style="flex: 1;">
              <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Duration:</label>
              <div
                class="duration-display"
                style="font-family: monospace; font-size: 14px; color: #666; padding: 8px 12px; background: #f8f8f8; border-radius: 4px; border: 1px solid #ddd;"
              >{{ duration || 'Pending...' }}</div>
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
            <div class="video-container" style="width: 100%; max-width: 100%; background: #000; border: 2px solid #ccc; border-top: none; border-radius: 0 0 4px 4px; overflow: hidden; position: relative; z-index: 10; margin-bottom: 15px;">
              <video
                ref="videoPlayerRef"
                class="video-player"
                controls
                controlsList="nodownload"
                style="width: 100% !important; height: 300px !important; max-width: 100% !important; position: relative; z-index: 11; display: block; border: none; border-radius: 0; object-fit: contain;"
                preload="metadata"
                @loadedmetadata="handleVideoMetadataLoaded"
                @timeupdate="updateTimecode"
                @play="updatePlayPauseState"
                @pause="updatePlayPauseState"
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
                  style="width: calc(25% + 1px); height: 55px; display: flex; flex-direction: column; background: #2196F3; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Mark In point (I key)"
                >
                  <div style="background: #1976D2; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">MARK IN</div>
                  <div style="background: #2196F3; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">I</div>
                </div>

                <!-- Go to In Button (Cell 3, 12.5% width) -->
                <div
                  ref="goToInBtn"
                  class="grid-btn go-to"
                  @click="performGoToInAction"
                  @mouseenter="e => hoverButton(e, '#64B5F6')"
                  @mouseleave="e => unhoverButton(e, '#64B5F6')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #64B5F6; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Go to In point (Q key)"
                >
                  <div style="background: #42A5F5; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">GO IN</div>
                  <div style="background: #64B5F6; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">Q</div>
                </div>

                <!-- Empty cells 4-5 (25% total) -->
                <div v-for="cellNum in [4, 5]" :key="`r1-${cellNum}`" class="grid-cell-empty" style="width: 12.5%; height: 55px; background: #d3d3d3; color: #666; display: flex; align-items: center; justify-content: center; border: none; margin-right: 1px; font-size: 14px; font-weight: bold; font-family: Helvetica, Arial, sans-serif; cursor: pointer; transition: all 0.2s ease;">{{ cellNum }}</div>

                <!-- Go to Out Button (Cell 6, 12.5% width) -->
                <div
                  ref="goToOutBtn"
                  class="grid-btn go-to"
                  @click="performGoToOutAction"
                  @mouseenter="e => hoverButton(e, '#FFAB91')"
                  @mouseleave="e => unhoverButton(e, '#FFAB91')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #FFAB91; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Go to Out point (W key)"
                >
                  <div style="background: #FF8A65; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">GO OUT</div>
                  <div style="background: #FFAB91; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">W</div>
                </div>

                <!-- Mark Out Button (Cells 7-8, 25% width) -->
                <div
                  ref="markOutBtn"
                  class="grid-btn mark-out"
                  @click="performMarkOutAction"
                  @mouseenter="e => hoverButton(e, '#FF5722')"
                  @mouseleave="e => unhoverButton(e, '#FF5722')"
                  style="width: calc(25% + 1px); height: 55px; display: flex; flex-direction: column; background: #FF5722; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Mark Out point (O key)"
                >
                  <div style="background: #E64A19; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">MARK OUT</div>
                  <div style="background: #FF5722; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">O</div>
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
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #E65100; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Jump back 10 seconds"
                >
                  <div style="background: #BF360C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;">-10s</div>
                  <div style="background: #E65100; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">◄◄</div>
                </div>

                <!-- -1s (Cell 10) -->
                <div
                  ref="step1sBackBtn"
                  class="grid-btn step orange"
                  @click="performStepBackSecond"
                  @mouseenter="e => hoverButton(e, '#FF9800')"
                  @mouseleave="e => unhoverButton(e, '#FF9800')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #FF9800; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step back 1 second (J key)"
                >
                  <div style="background: #F57C00; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;">-1s</div>
                  <div style="background: #FF9800; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">◄</div>
                </div>

                <!-- -1f (Cell 11) -->
                <div
                  ref="step1fBackBtn"
                  class="grid-btn step light-orange"
                  @click="performStepBackFrame"
                  @mouseenter="e => hoverButton(e, '#FFB74D')"
                  @mouseleave="e => unhoverButton(e, '#FFB74D')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #FFB74D; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step back 1 frame (← key)"
                >
                  <div style="background: #FFA726; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;">-1f</div>
                  <div style="background: #FFB74D; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">|◄</div>
                </div>

                <!-- Play/Pause (Cells 12-13, 25% width) -->
                <div
                  ref="playPauseBtn"
                  class="grid-btn play-pause"
                  @click="performPlayPauseAction"
                  @mouseenter="e => hoverButton(e, '#4CAF50')"
                  @mouseleave="e => unhoverButton(e, '#4CAF50')"
                  style="width: calc(25% + 1px); height: 55px; display: flex; flex-direction: column; background: #4CAF50; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Play/Pause - Toggle playback (Space or K)"
                >
                  <div style="background: #388E3C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">PLAY/PAUSE</div>
                  <div style="background: #4CAF50; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">{{ isPlaying ? '⏸' : '▶' }}</div>
                </div>

                <!-- +1f (Cell 14) -->
                <div
                  ref="step1fForwardBtn"
                  class="grid-btn step light-orange"
                  @click="performStepForwardFrame"
                  @mouseenter="e => hoverButton(e, '#FFB74D')"
                  @mouseleave="e => unhoverButton(e, '#FFB74D')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #FFB74D; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step forward 1 frame (→ key)"
                >
                  <div style="background: #FFA726; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;">+1f</div>
                  <div style="background: #FFB74D; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">►|</div>
                </div>

                <!-- +1s (Cell 15) -->
                <div
                  ref="step1sForwardBtn"
                  class="grid-btn step orange"
                  @click="performStepForwardSecond"
                  @mouseenter="e => hoverButton(e, '#FF9800')"
                  @mouseleave="e => unhoverButton(e, '#FF9800')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #FF9800; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Step forward 1 second (L key)"
                >
                  <div style="background: #F57C00; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;">+1s</div>
                  <div style="background: #FF9800; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">►</div>
                </div>

                <!-- +10s (Cell 16) -->
                <div
                  ref="step10sForwardBtn"
                  class="grid-btn step dark-orange"
                  @click="performJumpForwardTenSeconds"
                  @mouseenter="e => hoverButton(e, '#E65100')"
                  @mouseleave="e => unhoverButton(e, '#E65100')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #E65100; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif;"
                  title="Jump forward 10 seconds"
                >
                  <div style="background: #BF360C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;">+10s</div>
                  <div style="background: #E65100; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">►►</div>
                </div>
              </div>

              <!-- Row 3: Empty cells, Preview, Take -->
              <div class="control-row d-flex">
                <!-- Empty cells 17-20 -->
                <div v-for="cellNum in [17, 18, 19, 20]" :key="`r3-${cellNum}`" class="grid-cell-empty" style="width: 12.5%; height: 55px; background: #d3d3d3; color: #666; display: flex; align-items: center; justify-content: center; border: none; margin-right: 1px; font-size: 14px; font-weight: bold; font-family: Helvetica, Arial, sans-serif; cursor: pointer; transition: all 0.2s ease;">{{ cellNum }}</div>

                <!-- Preview Button (Cell 21) -->
                <div
                  ref="previewBtn"
                  class="grid-btn preview"
                  @click="performPreviewAction"
                  @mouseenter="e => hoverButton(e, '#9C27B0')"
                  @mouseleave="e => unhoverButton(e, '#9C27B0')"
                  style="width: 12.5%; height: 55px; display: flex; flex-direction: column; background: #9C27B0; border: none; margin-right: 1px; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Preview - Play from In to Out (Shift+Space)"
                >
                  <div style="background: #7B1FA2; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">PREVIEW</div>
                  <div style="background: #9C27B0; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">▶|</div>
                </div>

                <!-- Empty cell 22 -->
                <div class="grid-cell-empty" style="width: 12.5%; height: 55px; background: #d3d3d3; color: #666; display: flex; align-items: center; justify-content: center; border: none; margin-right: 1px; font-size: 14px; font-weight: bold; font-family: Helvetica, Arial, sans-serif; cursor: pointer; transition: all 0.2s ease;">22</div>

                <!-- Take Button (Cells 23-24, 25% width) -->
                <div
                  ref="takeBtn"
                  class="grid-btn take"
                  @click="performTakeAction"
                  @mouseenter="e => hoverButton(e, '#4CAF50')"
                  @mouseleave="e => unhoverButton(e, '#4CAF50')"
                  style="width: calc(25% + 1px); height: 55px; display: flex; flex-direction: column; background: #4CAF50; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Take - Commit current cut (Ctrl+Enter)"
                >
                  <div style="background: #388E3C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">TAKE</div>
                  <div style="background: #4CAF50; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✂</div>
                </div>
              </div>
            </div>
          </div>

          <!-- ============================================================ -->
          <!-- CLIPPING TOOLS SECTION -->
          <!-- ============================================================ -->
          <div style="border-top: 2px solid #999; margin: 25px 0 20px 0;"></div>

          <div class="clipping-tools-section mb-4">
            <h3 class="text-uppercase font-weight-bold mb-3" style="font-size: 1.1em; color: #333;">CLIPPING TOOLS</h3>

            <!-- Clipping Method Button Grid (1x10) -->
            <div class="mb-3">
              <label class="cue-modal-label mb-2 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Clipping Method:</label>

              <!-- 1x10 Grid Container -->
              <div class="clipping-grid-container" style="width: 100%; margin-bottom: 15px;">
                <div class="clipping-row d-flex mb-0" style="gap: 1px;">

                  <!-- None Button -->
                  <div
                    @click="clippingMethod = 'none'"
                    @mouseenter="e => hoverButton(e, '#2196F3')"
                    @mouseleave="e => unhoverButton(e, '#2196F3')"
                    class="grid-btn clipping-btn"
                    :style="{
                      width: '25%',
                      height: '55px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: clippingMethod === 'none' ? '#1565C0' : '#2196F3',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontFamily: 'Helvetica, Arial, sans-serif',
                      overflow: 'hidden',
                      boxShadow: clippingMethod === 'none' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                      transform: clippingMethod === 'none' ? 'translateY(2px)' : 'none',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                    }"
                    title="No clipping - use full video"
                  >
                    NONE
                  </div>

                  <!-- Single Trim Button -->
                  <div
                    @click="clippingMethod = 'single-trim'"
                    @mouseenter="e => hoverButton(e, '#2196F3')"
                    @mouseleave="e => unhoverButton(e, '#2196F3')"
                    class="grid-btn clipping-btn"
                    :style="{
                      width: '25%',
                      height: '55px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: clippingMethod === 'single-trim' ? '#1565C0' : '#2196F3',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontFamily: 'Helvetica, Arial, sans-serif',
                      overflow: 'hidden',
                      boxShadow: clippingMethod === 'single-trim' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                      transform: clippingMethod === 'single-trim' ? 'translateY(2px)' : 'none',
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                    }"
                    title="Single trim - extract one clip from video"
                  >
                    SINGLE TRIM
                  </div>

                  <!-- Individual Clips Button -->
                  <div
                    @click="clippingMethod = 'individual-clips'"
                    @mouseenter="e => hoverButton(e, '#2196F3')"
                    @mouseleave="e => unhoverButton(e, '#2196F3')"
                    class="grid-btn clipping-btn"
                    :style="{
                      width: '25%',
                      height: '55px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: clippingMethod === 'individual-clips' ? '#1565C0' : '#2196F3',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontFamily: 'Helvetica, Arial, sans-serif',
                      overflow: 'hidden',
                      boxShadow: clippingMethod === 'individual-clips' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                      transform: clippingMethod === 'individual-clips' ? 'translateY(2px)' : 'none',
                      color: 'white',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                    }"
                    title="Individual clips - extract multiple separate clips"
                  >
                    INDIVIDUAL CLIPS
                  </div>

                  <!-- Montage Button -->
                  <div
                    @click="clippingMethod = 'montage'"
                    @mouseenter="e => hoverButton(e, '#2196F3')"
                    @mouseleave="e => unhoverButton(e, '#2196F3')"
                    class="grid-btn clipping-btn"
                    :style="{
                      width: '25%',
                      height: '55px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: clippingMethod === 'montage' ? '#1565C0' : '#2196F3',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontFamily: 'Helvetica, Arial, sans-serif',
                      overflow: 'hidden',
                      boxShadow: clippingMethod === 'montage' ? 'inset 0 3px 8px rgba(0,0,0,0.4)' : 'none',
                      transform: clippingMethod === 'montage' ? 'translateY(2px)' : 'none',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                    }"
                    title="Montage - combine multiple clips into single video"
                  >
                    MONTAGE
                  </div>

                </div>
              </div>
            </div>

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
                  ref="trimStartInputRef"
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
                  ref="trimEndInputRef"
                  v-model="trimEnd"
                  class="cue-modal-input"
                  type="text"
                  placeholder="HH:MM:SS"
                  :disabled="clippingMethod === 'none'"
                  style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box;"
                />
              </div>

              <!-- Take Button -->
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

            <!-- Clips Collection Display (Badges) -->
            <div v-if="clips.length > 0" class="mb-3">
              <label class="cue-modal-label mb-2 d-block" style="font-size: 14px; font-weight: 500; color: #555;">
                Clips ({{ clips.length }}):
              </label>
              <div class="clips-badges" style="display: flex; flex-wrap: wrap; gap: 8px;">
                <div
                  v-for="(clip, index) in clips"
                  :key="`clip-${index}`"
                  class="clip-badge"
                  style="display: inline-flex; align-items: center; background: #e3f2fd; border: 1px solid #90caf9; border-radius: 16px; padding: 6px 12px; font-size: 13px; gap: 8px;"
                >
                  <span style="font-weight: 500; color: #1976d2;">{{ clip.slug }}</span>
                  <span style="color: #666; font-family: monospace; font-size: 11px;">{{ clip.time_start }} → {{ clip.time_end }}</span>
                  <button
                    @click="removeClip(index)"
                    type="button"
                    style="background: none; border: none; color: #f44336; cursor: pointer; font-size: 16px; line-height: 1; padding: 0; margin-left: 4px;"
                    title="Remove clip"
                  >×</button>
                </div>
              </div>
            </div>
          </div>

          <div style="border-bottom: 2px solid #999; margin: 20px 0 25px 0;"></div>
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
            <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Description:</label>
            <textarea
              v-model="description"
              class="cue-modal-textarea"
              rows="2"
              placeholder="Brief description of the SOT content and context..."
              style="width: 100%; height: 75px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; resize: none;"
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
  emits: ['update:show', 'submit'],
  setup(props, { emit }) {
    const toast = useToast()

    // Form refs
    const sotFormRef = ref(null)
    const fileInputRef = ref(null)
    const videoPlayerRef = ref(null)
    const trimStartInputRef = ref(null)
    const trimEndInputRef = ref(null)
    const topErrorEl = ref(null)
    const timecodeDisplay = ref(null)
    const videoInfoOverlay = ref(null)
    const creditsListRef = ref(null)
    const slugField = ref(null)

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

    // Clipping tools state
    const clippingMethod = ref('none')
    const clipSlug = ref('')
    const clips = ref([])
    const clipCounter = ref(1)

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

    // Keyboard shortcuts setup
    const setupKeyboardShortcuts = () => {
      keyboardHandler.value = (event) => {
        // ESC key - always handle with confirmation modal
        if (event.key === 'Escape') {
          event.preventDefault()
          event.stopPropagation()
          event.stopImmediatePropagation()
          handleEscapeKey()
          return
        }

        // Don't interfere with typing in input fields (except trim inputs with arrow keys)
        if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
          if (!(event.target === trimStartInputRef.value || event.target === trimEndInputRef.value) ||
              !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
            return
          }
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

          case 'Enter': // Ctrl+Enter - Take, Alt+Enter - Submit/Inject
            if (event.ctrlKey) {
              event.preventDefault()
              performTakeAction()
            } else if (event.altKey) {
              event.preventDefault()
              handleAddCue() // Submit and close modal
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
      hideTopError()

      // Validate required fields
      if (!slug.value.trim()) {
        console.log('❌ Validation failed: Slug is required')
        showTopError('ERROR: Slug is required')
        return
      }

      // Determine job type based on clipping method
      let jobType = SOT_JOB_TYPES.FULL_PROCESS // Default to full processing
      if (clippingMethod.value === 'none' || clippingMethod.value === 'single-trim') {
        jobType = SOT_JOB_TYPES.SINGLE_TRIM
      } else if (clippingMethod.value === 'individual-clips') {
        jobType = SOT_JOB_TYPES.INDIVIDUAL_CLIPS
      } else if (clippingMethod.value === 'montage') {
        jobType = SOT_JOB_TYPES.MONTAGE
      }

      // Show loading toast while generating AssetID
      const loadingToast = toast.info('⏳ Assigning AssetID...', {
        timeout: false,  // Don't auto-dismiss
        closeButton: false
      })

      // Generate AssetID early (needed for both cue creation and processing)
      const generatedAssetId = await generateAssetId()

      // Dismiss loading toast
      toast.dismiss(loadingToast)

      // NOTE: Processing will be triggered AFTER cue insertion by ContentEditor
      // Don't start processing here - user hasn't inserted cue into script yet!

      // Format credits as JSON
      const creditsFormatted = credits.value
        .filter(c => c.key.trim() && c.value.trim())
        .reduce((acc, c) => {
          acc[c.key] = c.value
          return acc
        }, {})

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
        tempJobId: tempJobId.value,  // Include job ID for tracking
        clippingMethod: clippingMethod.value,
        clips: clips.value.length > 0 ? JSON.stringify(clips.value) : null,
        jobType: jobType  // Backend will use this to route processing
      }

      console.log('SOT cue data:', sotData)
      console.log('✅ Submitting SOT cue and closing modal')
      emit('submit', sotData)
      emit('update:show', false)

      // Reset form
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
      transcription.value = ''
      credits.value = []
      originalFile.value = null

      // Reset clipping tools
      clippingMethod.value = 'none'
      clipSlug.value = ''
      clips.value = []
      clipCounter.value = 1

      if (videoPlayerRef.value) {
        videoPlayerRef.value.pause()
        videoPlayerRef.value.src = ''
      }

      if (previewInterval.value) {
        clearInterval(previewInterval.value)
        previewInterval.value = null
      }
    }

    // Lifecycle
    onMounted(() => {
      setupKeyboardShortcuts()
    })

    // Watch for modal visibility changes
    watch(
      () => props.show,
      (newValue, oldValue) => {
        console.log(`🔔 SOT Modal visibility changed: ${oldValue} → ${newValue}`)
        if (!newValue && oldValue) {
          console.log('🚪 Modal closed - checking why...')
          console.trace('Modal close stack trace')
        }
        // Auto-focus slug field when modal opens
        if (newValue && !oldValue) {
          nextTick(() => {
            if (slugField.value) {
              slugField.value.focus()
              console.log('🎯 Auto-focused slug field')
            }
          })
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
      handleVideoMetadataLoaded
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');

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
