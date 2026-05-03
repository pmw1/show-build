<template>
  <!-- Overlay Information Display (OUTSIDE v-dialog to avoid stacking context issues) -->
  <div v-if="show && mediaUrl" class="overlay-info-display" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10001;">
    <!-- Top Center: Large Timecode Display -->
    <div class="timecode-overlay" style="position: absolute; top: 5px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.85); padding: 25px 50px; border-radius: 12px; text-align: center; border: 2px solid rgba(255, 255, 255, 0.3);">
      <div style="color: white; font-size: 72px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 8px; text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);">{{ currentTimecode }}</div>
      <div style="color: #90CAF9; font-size: 18px; font-weight: bold; font-family: 'Helvetica', Arial, sans-serif; margin-top: 10px;">{{ currentActionDisplay }}</div>
    </div>

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
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);"><span style="color: #4CAF50; font-weight: bold;">ALT+ENTER</span><span style="color: #4CAF50;">Submit</span></div>
        </div>
      </div>
    </div>

    <!-- Top Right: OUT Point Display -->
    <div style="position: absolute; top: 150px; right: 50px;">
      <div class="out-point-display" style="background: rgba(255, 87, 34, 0.9); padding: 30px; border-radius: 12px; border-right: 8px solid #E64A19; margin-bottom: 15px;">
        <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px; text-align: right;">OUT POINT ►</div>
        <div style="color: white; font-size: 48px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 2px; text-align: right;">{{ trimEnd || '--:--:--:--' }}</div>
      </div>

      <!-- Clips List -->
      <div v-if="clips && clips.length > 0" class="clips-list" style="background: rgba(0, 0, 0, 0.85); padding: 20px; border-radius: 8px; max-width: 350px; max-height: 500px; overflow-y: auto; pointer-events: auto;">
        <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 12px; border-bottom: 2px solid rgba(255, 255, 255, 0.3); padding-bottom: 8px;">
          📋 CLIPS ({{ clips.length }})
        </div>
        <div v-for="(clip, index) in clips" :key="index" class="clip-item" style="background: rgba(255, 255, 255, 0.1); padding: 12px; margin-bottom: 12px; border-radius: 6px; transition: all 0.2s;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="color: #FFB74D; font-size: 14px; font-weight: bold;">Clip {{ index + 1 }}</div>
            <button @click="removeClip(index)" style="background: #f44336; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px; cursor: pointer; font-weight: bold;">✕</button>
          </div>
          <div style="color: white; font-size: 12px; font-family: 'Roboto Mono', monospace; margin-bottom: 5px;">{{ clip.start }} → {{ clip.end }}</div>
          <div style="color: #aaa; font-size: 11px; margin-bottom: 8px;">Duration: {{ clip.duration }}</div>
          <textarea
            v-model="clip.transcript"
            placeholder="Transcript for this clip..."
            style="width: 100%; min-height: 60px; padding: 6px; background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 4px; color: white; font-size: 11px; font-family: 'Helvetica', Arial, sans-serif; resize: vertical;"
            @click.stop
          ></textarea>
        </div>
      </div>
    </div>

    <!-- Bottom Center: Set Thumbnail Button -->
    <div class="thumbnail-marker" style="position: absolute; bottom: 100px; left: 50%; transform: translateX(-50%); pointer-events: auto;">
      <button @click="setThumbnailTimecode" style="background: #9C27B0; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 12px rgba(156, 39, 176, 0.5); transition: all 0.2s;">
        📸 MARK THUMBNAIL AT {{ currentTimecode }}
      </button>
    </div>
  </div>

  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    max-width="800px"
    persistent
    class="vo-modal"
    style="z-index: 9999;"
  >
    <!-- Full Modal Container with 70% transparent overlay -->
    <v-card class="vo-modal-card" style="max-height: 80vh; overflow: hidden;">
      <!-- Collapsible Error at Top -->
      <div
        ref="topErrorEl"
        class="top-error"
        style="background: #ff4444; color: white; height: 0; overflow: hidden; transition: all 0.3s ease; font-weight: bold; text-align: center; border-radius: 4px 4px 0 0;"
      ></div>

      <!-- Header with Title and Close Buttons -->
      <div class="modal-header d-flex justify-space-between align-center pa-3" style="padding: 10px 15px;">
        <h2 class="text-uppercase font-weight-bold ma-0" style="font-size: 1.2em;">ADD VOICE OVER (VO) MONTAGE</h2>
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
        <v-form ref="voFormRef">
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

          <!-- Select Video Buttons -->
          <div class="mb-3">
            <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">
              Select Video:
            </label>
            <div class="d-flex" style="gap: 3px;">
              <button
                @click="triggerFileInput"
                class="cue-modal-button-small"
                type="button"
                style="padding: 15px 30px; font-size: 14px; min-width: 120px; background: #87CEEB; color: white; border: 1px solid #87CEEB; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;"
                title="Browse for video file"
              >Load Video</button>
              <button
                @click="clearVideo"
                class="cue-modal-button-small"
                type="button"
                :disabled="!mediaUrl"
                style="padding: 15px 30px; font-size: 14px; min-width: 120px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer; transition: background-color 0.2s ease;"
                :style="{ opacity: !mediaUrl ? 0.5 : 1, cursor: !mediaUrl ? 'not-allowed' : 'pointer' }"
                title="Clear current video"
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

            <!-- Live Timecode Display (Black Bar Above Video) -->
            <div
              ref="timecodeDisplay"
              class="timecode-display"
              style="width: 100%; background: #000; border: 2px solid #ccc; border-bottom: none; position: relative; z-index: 15; margin-bottom: 0; border-radius: 4px 4px 0 0;"
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
              <!-- Row 1: Mark In/Out, Go In/Out -->
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

              <!-- Row 3: Empty cells, Preview, Add Clip -->
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

                <!-- Add Clip Button (Cells 23-24, 25% width) -->
                <div
                  ref="addClipBtn"
                  class="grid-btn add-clip"
                  @click="handleAddClip"
                  @mouseenter="e => hoverButton(e, '#4CAF50')"
                  @mouseleave="e => unhoverButton(e, '#4CAF50')"
                  style="width: calc(25% + 1px); height: 55px; display: flex; flex-direction: column; background: #4CAF50; border: none; cursor: pointer; transition: all 0.2s ease; font-family: Helvetica, Arial, sans-serif; overflow: hidden;"
                  title="Add clip to montage (Ctrl+Enter)"
                >
                  <div style="background: #388E3C; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">ADD CLIP</div>
                  <div style="background: #4CAF50; color: white; height: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">✚</div>
                </div>
              </div>
            </div>

            <!-- Trim Times Display -->
            <div class="d-flex mb-3" style="gap: 10px;">
              <div style="flex: 1;">
                <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">In Point:</label>
                <div style="font-family: monospace; font-size: 14px; color: #1976D2; font-weight: bold; padding: 8px 12px; background: #E3F2FD; border-radius: 4px; border: 2px solid #2196F3;">{{ trimStart }}</div>
              </div>
              <div style="flex: 1;">
                <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">Out Point:</label>
                <div style="font-family: monospace; font-size: 14px; color: #E64A19; font-weight: bold; padding: 8px 12px; background: #FFEBEE; border-radius: 4px; border: 2px solid #FF5722;">{{ trimEnd }}</div>
              </div>
            </div>
          </div>

          <!-- Clips Collection Display (Badges) -->
          <div v-if="clips.length > 0" class="mb-3">
            <label class="cue-modal-label mb-2 d-block" style="font-size: 14px; font-weight: 500; color: #555;">
              Montage Clips ({{ clips.length }}):
            </label>
            <div class="clips-badges" style="display: flex; flex-wrap: wrap; gap: 8px;">
              <div
                v-for="(clip, index) in clips"
                :key="`clip-${index}`"
                class="clip-badge"
                style="display: inline-flex; align-items: center; background: #e3f2fd; border: 1px solid #90caf9; border-radius: 16px; padding: 6px 12px; font-size: 13px; gap: 8px;"
              >
                <span style="font-weight: 500; color: #1976d2;">{{ index + 1 }}. {{ clip.filename }}</span>
                <span style="color: #666; font-family: monospace; font-size: 11px;">{{ clip.trimStart }} → {{ clip.trimEnd }}</span>
                <button
                  @click="removeClip(index)"
                  type="button"
                  style="background: none; border: none; color: #f44336; cursor: pointer; font-size: 16px; line-height: 1; padding: 0; margin-left: 4px;"
                  title="Remove clip"
                >×</button>
              </div>
            </div>
          </div>

          <!-- Upload Progress -->
          <div v-if="uploadProgress > 0 && uploadProgress < 100" class="mb-3">
            <label class="cue-modal-label mb-1 d-block" style="font-size: 14px; font-weight: 500; color: #555;">
              Uploading to server: {{ uploadProgress }}%
            </label>
            <div style="height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden;">
              <div :style="{ width: uploadProgress + '%', height: '100%', background: '#4CAF50', transition: 'width 0.3s ease' }"></div>
            </div>
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
              @click="handleSubmit"
              :disabled="!slug || (!uploadComplete && clips.length === 0)"
              class="cue-modal-button"
              style="flex: 1; padding: 20px 40px; font-size: 16px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background-color 0.2s;"
              :style="{ opacity: (!slug || (!uploadComplete && clips.length === 0)) ? 0.5 : 1, cursor: (!slug || (!uploadComplete && clips.length === 0)) ? 'not-allowed' : 'pointer' }"
            >{{ clips.length > 0 ? `Create VO Montage (${clips.length} clip${clips.length !== 1 ? 's' : ''})` : 'Create VO Cue' }}</button>
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'

const props = defineProps({
  show: Boolean,
  episode: String,
  duplicateSlugs: {
    type: Array,
    default: () => []
  },
  cueType: {
    type: String,
    default: 'vo'
  }
})

const emit = defineEmits(['update:show', 'submit'])

const toast = useToast()

    // Form refs
    const voFormRef = ref(null)
    const fileInputRef = ref(null)
    const videoPlayerRef = ref(null)
    const topErrorEl = ref(null)
    const timecodeDisplay = ref(null)
    const videoInfoOverlay = ref(null)
    const slugField = ref(null)

    // Button refs for keyboard shortcuts
    const markInBtn = ref(null)
    const markOutBtn = ref(null)
    const goToInBtn = ref(null)
    const goToOutBtn = ref(null)
    const playPauseBtn = ref(null)
    const previewBtn = ref(null)
    const addClipBtn = ref(null)
    const step10sBackBtn = ref(null)
    const step1sBackBtn = ref(null)
    const step1fBackBtn = ref(null)
    const step10sForwardBtn = ref(null)
    const step1sForwardBtn = ref(null)
    const step1fForwardBtn = ref(null)

    // Form data
    const assetId = ref('Generated on save') // eslint-disable-line no-unused-vars
    const slug = ref('')
    const mediaUrl = ref('')
    const duration = ref('')
    const currentVideoFile = ref(null)
    const trimStart = ref('00:00:00:00')
    const trimEnd = ref('00:00:00:00')

    // Background upload state (like SOT)
    const uploadProgress = ref(0)
    const tempJobId = ref(null)
    const uploadComplete = ref(false)

    // Clips collection for montage
    const clips = ref([])

    // Video state
    const currentFramerate = ref(30)
    const isPlaying = ref(false)
    const currentTimecode = ref('00:00:00:00')
    const durationTimecode = ref('00:00:00:00')
    const remainingTimecode = ref('00:00:00:00')
    const previewInterval = ref(null)
    const videoSpecs = ref({})
    const blobUrl = ref('')

    // Keyboard handler
    const keyboardHandler = ref(null)

    // Overlay display state
    const currentActionDisplay = ref('READY')
    const thumbnailTimecode = ref('')

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
      trimStart.value = secondsToTimecode(videoPlayerRef.value.currentTime, true)
      animateButtonPress(markInBtn.value)

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
      trimEnd.value = secondsToTimecode(videoPlayerRef.value.currentTime, true)
      animateButtonPress(markOutBtn.value)

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

    const performStepBackFrame = () => {
      if (!videoPlayerRef.value) return
      const frameDuration = 1 / currentFramerate.value
      videoPlayerRef.value.currentTime = Math.max(0, videoPlayerRef.value.currentTime - frameDuration)
      currentActionDisplay.value = 'REVERSE 1 FRAME ◄|'
      animateButtonPress(step1fBackBtn.value)
    }

    const performStepForwardFrame = () => {
      if (!videoPlayerRef.value) return
      const frameDuration = 1 / currentFramerate.value
      videoPlayerRef.value.currentTime = Math.min(videoPlayerRef.value.duration || 0, videoPlayerRef.value.currentTime + frameDuration)
      currentActionDisplay.value = 'FORWARD 1 FRAME |►'
      animateButtonPress(step1fForwardBtn.value)
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
        if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
          return
        }

        if (!videoPlayerRef.value) return

        let handled = true

        switch(event.key) {
          case ' ':
            event.preventDefault()
            if (event.shiftKey) {
              performPreviewAction()
            } else {
              performPlayPauseAction()
            }
            break

          case 'i':
          case 'I':
            event.preventDefault()
            performMarkInAction()
            break

          case 'o':
          case 'O':
            event.preventDefault()
            performMarkOutAction()
            break

          case 'q':
          case 'Q':
            event.preventDefault()
            performGoToInAction()
            break

          case 'w':
          case 'W':
            event.preventDefault()
            performGoToOutAction()
            break

          case 'k':
          case 'K':
            event.preventDefault()
            performPlayPauseAction()
            break

          case 'j':
          case 'J':
            event.preventDefault()
            performStepBackSecond()
            break

          case 'l':
          case 'L':
            event.preventDefault()
            performStepForwardSecond()
            break

          case 'ArrowLeft':
            event.preventDefault()
            if (event.ctrlKey) {
              performJumpBackTenSeconds()
            } else if (event.shiftKey) {
              if (videoPlayerRef.value) {
                videoPlayerRef.value.currentTime = Math.max(0, videoPlayerRef.value.currentTime - (10 / currentFramerate.value))
              }
            } else {
              performStepBackFrame()
            }
            break

          case 'ArrowRight':
            event.preventDefault()
            if (event.ctrlKey) {
              performJumpForwardTenSeconds()
            } else if (event.shiftKey) {
              if (videoPlayerRef.value) {
                const videoDuration = videoPlayerRef.value.duration || 0
                videoPlayerRef.value.currentTime = Math.min(videoDuration, videoPlayerRef.value.currentTime + (10 / currentFramerate.value))
              }
            } else {
              performStepForwardFrame()
            }
            break

          case 'Enter': // Ctrl+Enter - Add Clip, Alt+Enter - Submit/Inject
            if (event.ctrlKey) {
              event.preventDefault()
              handleAddClip()
            } else if (event.altKey) {
              event.preventDefault()
              handleSubmit() // Submit and close modal
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

          case 'PageDown': // Page Down - Scroll to bottom of modal
            event.preventDefault()
            scrollToBottomOfModal()
            break

          case 'Escape':
            event.preventDefault()
            emit('update:show', false)
            resetForm()
            break

          default:
            handled = false
            break
        }

        if (handled) {
          event.stopPropagation()
        }
      }

      document.addEventListener('keydown', keyboardHandler.value, true)
    }

    // Video metadata handling
    const handleVideoMetadataLoaded = () => {
      if (!videoPlayerRef.value) return

      const videoDuration = videoPlayerRef.value.duration
      const videoWidth = videoPlayerRef.value.videoWidth
      const videoHeight = videoPlayerRef.value.videoHeight

      currentFramerate.value = 30

      videoSpecs.value = {
        resolution: videoWidth && videoHeight ? `${videoWidth}×${videoHeight}` : null,
        width: videoWidth || null,
        height: videoHeight || null,
        aspectRatio: videoWidth && videoHeight ? (videoWidth / videoHeight).toFixed(3) : null,
        duration: videoDuration || null,
        framerate: currentFramerate.value,
        fileSize: currentVideoFile.value?.size || null,
        filename: currentVideoFile.value?.name || null
      }

      if (videoDuration && videoDuration > 0) {
        duration.value = secondsToTimecode(videoDuration, false)
        trimEnd.value = secondsToTimecode(videoDuration, true)
      }

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

      currentVideoFile.value = file

      const objectURL = URL.createObjectURL(file)
      blobUrl.value = objectURL
      mediaUrl.value = objectURL

      await nextTick()
      if (videoPlayerRef.value) {
        videoPlayerRef.value.src = objectURL
        videoPlayerRef.value.load()
      }

      // Reset trim points for new video
      trimStart.value = '00:00:00:00'
      uploadProgress.value = 0
      uploadComplete.value = false
      tempJobId.value = null

      toast.success(`Video loaded: ${file.name}`)

      // Start background upload to VO endpoint (like SOT)
      startBackgroundUpload(file)
    }

    const startBackgroundUpload = async (file) => {
      try {
        const formData = new FormData()
        formData.append('file', file)

        const xhr = new XMLHttpRequest()

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            uploadProgress.value = Math.round((e.loaded / e.total) * 100)
          }
        })

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText)
            tempJobId.value = response.temp_job_id
            uploadComplete.value = true
            uploadProgress.value = 100
            toast.success('Video uploaded to server')
          } else {
            toast.error('Upload failed: ' + xhr.statusText)
            uploadProgress.value = 0
          }
        })

        xhr.addEventListener('error', () => {
          uploadProgress.value = 0
          toast.error('Upload failed - network error')
        })

        const token = localStorage.getItem('auth-token')
        const apiKey = localStorage.getItem('api_key')

        xhr.open('POST', '/api/vo/upload/background', true)

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
      currentVideoFile.value = null
      trimStart.value = '00:00:00:00'
      trimEnd.value = '00:00:00:00'

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

    // Clip management
    const handleAddClip = () => {
      if (!currentVideoFile.value) {
        toast.warning('Please load a video first')
        return
      }

      const startSec = timecodeToSeconds(trimStart.value)
      const endSec = timecodeToSeconds(trimEnd.value)

      if (endSec <= startSec) {
        toast.warning('Out point must be after In point')
        return
      }

      // Add clip to collection
      clips.value.push({
        file: currentVideoFile.value,
        filename: currentVideoFile.value.name,
        start: trimStart.value,
        end: trimEnd.value,
        trimStart: trimStart.value,
        trimEnd: trimEnd.value,
        duration: `${Math.round(endSec - startSec)}s`,
        durationSeconds: endSec - startSec,
        transcript: '' // Initialize empty transcript for this clip
      })

      toast.success(`Clip added: ${currentVideoFile.value.name} (${clips.value.length} total)`)
      animateButtonPress(addClipBtn.value)

      // Clear current video to prepare for next clip
      clearVideo()
    }

    const removeClip = (index) => {
      const removedClip = clips.value[index]
      clips.value.splice(index, 1)
      toast.info(`Removed clip: ${removedClip.filename}`)
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

    const handleSubmit = async () => {
      hideTopError()

      if (!slug.value.trim()) {
        showTopError('ERROR: Slug is required')
        return
      }

      // Single video mode: require background upload to be complete
      if (clips.value.length === 0) {
        if (!tempJobId.value) {
          showTopError('ERROR: Please upload a video file first')
          return
        }
        if (!uploadComplete.value) {
          showTopError('ERROR: Video upload still in progress')
          return
        }
      }

      const normalizedSlug = slug.value.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-')

      try {
        // Generate AssetID
        const formData = new FormData()
        formData.append('type', 'vo')
        formData.append('slug', normalizedSlug)
        const assetResponse = await axios.post('/assetid/generate-legacy', formData, {
          headers: {
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        })
        const generatedAssetId = assetResponse.data.id

        // Single video processing (like SOT)
        if (clips.value.length === 0 && tempJobId.value) {
          // Trigger VO processing via new endpoint
          const token = localStorage.getItem('auth-token')
          const apiKey = localStorage.getItem('api_key')
          const headers = {
            'Content-Type': 'application/json'
          }
          if (token) {
            headers['Authorization'] = `Bearer ${token}`
          } else if (apiKey) {
            headers['X-API-Key'] = apiKey
          }

          const processResponse = await axios.post('/api/vo/process', {
            temp_job_id: tempJobId.value,
            episode: props.episode,
            slug: normalizedSlug,
            asset_id: generatedAssetId,
            trim_start: trimStart.value.split(':').slice(0, 3).join(':'),  // HH:MM:SS format
            trim_end: trimEnd.value.split(':').slice(0, 3).join(':')
          }, { headers })

          const mediaURL = `episodes/${props.episode}/assets/video/${normalizedSlug}.mp4`

          emit('submit', {
            duration: duration.value,
            slug: normalizedSlug,
            assetID: generatedAssetId,
            mediaURL,
            tempJobId: tempJobId.value,
            trimStart: trimStart.value,
            trimEnd: trimEnd.value,
            taskId: processResponse.data.task_id
          })
          toast.success('VO processing started')
          emit('update:show', false)
          resetForm()
        } else if (clips.value.length > 0) {
          // Montage mode - upload all clips (legacy behavior)
          const uploadForm = new FormData()
          uploadForm.append('type', 'vo-montage')
          uploadForm.append('episode', props.episode)
          uploadForm.append('asset_id', generatedAssetId)
          uploadForm.append('slug', normalizedSlug)
          uploadForm.append('clip_count', clips.value.length.toString())

          clips.value.forEach((clip, index) => {
            uploadForm.append(`clip_${index}_file`, clip.file)
            uploadForm.append(`clip_${index}_trim_start`, clip.trimStart)
            uploadForm.append(`clip_${index}_trim_end`, clip.trimEnd)
          })

          await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          })

          const mediaURL = `episodes/${props.episode}/assets/video/${normalizedSlug}.mp4`

          emit('submit', {
            duration: '',
            slug: normalizedSlug,
            assetID: generatedAssetId,
            mediaURL,
            clipCount: clips.value.length
          })
          toast.success(`VO montage created with ${clips.value.length} clips`)
          emit('update:show', false)
          resetForm()
        }
      } catch (error) {
        console.error('VO submit error:', error)
        showTopError('Failed to create VO: ' + (error.response?.data?.detail || error.message))
        toast.error('Failed to create VO')
      }
    }

    const cancel = () => {
      emit('update:show', false)
      resetForm()
    }

    const resetForm = () => {
      slug.value = ''
      duration.value = ''
      currentVideoFile.value = null
      mediaUrl.value = ''
      blobUrl.value = ''
      trimStart.value = '00:00:00:00'
      trimEnd.value = '00:00:00:00'
      clips.value = []

      // Clear upload state
      uploadProgress.value = 0
      tempJobId.value = null
      uploadComplete.value = false

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

    onBeforeUnmount(() => {
      if (keyboardHandler.value) {
        document.removeEventListener('keydown', keyboardHandler.value, true)
      }

      if (previewInterval.value) {
        clearInterval(previewInterval.value)
      }

      if (blobUrl.value) {
        URL.revokeObjectURL(blobUrl.value)
      }
    })

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');

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
</style>
