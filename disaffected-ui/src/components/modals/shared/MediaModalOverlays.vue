<template>
  <!--
    MediaModalOverlays — shared outside-the-modal overlay layer for
    SotModal and VoModal. Renders OUTSIDE the v-dialog so it can sit
    at a higher z-index than the dialog itself (otherwise the dialog's
    own stacking context traps the overlays inside).

    Visible only when `show` is true AND `mediaLoaded` is true (no
    media → no overlays to show).
  -->
  <div
    v-if="show && mediaLoaded"
    class="overlay-info-display"
    style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10001;"
  >
    <!-- Top Center: Large Timecode Display -->
    <div class="timecode-overlay" style="position: absolute; top: 5px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.85); padding: 14px 20px; border-radius: 9px; text-align: center; border: 2px solid rgba(255, 255, 255, 0.3); min-width: 520px;">
      <div style="display: flex; gap: 12px; align-items: center; justify-content: center;">
        <div style="color: white; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(255, 255, 255, 0.5); width: 240px; display: inline-block; font-variant-numeric: tabular-nums;">{{ currentTimecode }}</div>
        <div style="padding: 8px 12px;">
          <div style="color: #F44336; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(244, 67, 54, 0.8); width: 240px; display: inline-block; font-variant-numeric: tabular-nums;">-{{ remainingTimecode }}</div>
        </div>
      </div>
      <div style="color: #90CAF9; font-size: 10px; font-weight: bold; font-family: 'Helvetica', Arial, sans-serif; margin-top: 6px;">{{ currentActionDisplay }}</div>

      <!-- Clip Duration Display (slides down when IN and OUT are set) -->
      <transition name="slide-down">
        <div v-if="trimStart && trimEnd && clipDuration" class="clip-duration-display" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255, 255, 255, 0.2);">
          <div style="color: #81C784; font-size: 12px; font-weight: bold; margin-bottom: 4px;">CLIP DURATION</div>
          <div style="color: #4CAF50; font-size: 32px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 3px; text-shadow: 0 0 15px rgba(76, 175, 80, 0.5);">{{ clipDuration }}</div>
        </div>
      </transition>
    </div>

    <!-- Playback Speed Indicator (Top Right) -->
    <transition name="speed-fade">
      <div v-if="showSpeedIndicator" class="speed-indicator" :style="`position: absolute; top: 20px; right: 50px; background: rgba(0, 0, 0, 0.9); padding: 20px; border-radius: 50%; width: 100px; height: 100px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 3px solid ${themeColors.speed}cc; box-shadow: 0 0 20px ${themeColors.speed}80;`">
        <div :style="`color: ${themeColors.speed}; font-size: 32px; font-weight: bold; font-family: 'Roboto Mono', monospace; text-shadow: 0 0 10px ${themeColors.speed}cc;`">{{ playbackSpeed.toFixed(2) }}×</div>
        <div style="color: #81C784; font-size: 10px; font-weight: bold; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;">{{ speedLabel }}</div>
      </div>
    </transition>

    <!-- Frame Counter (Bottom Center) -->
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
      <div class="in-point-display" :style="`background: ${themeColors.in}e6; padding: 14px 20px; border-radius: 9px; border-left: 6px solid ${themeColors.inDark}; border: 2px solid ${themeColors.in}80; min-width: 200px;`">
        <div style="color: rgba(255,255,255,0.8); font-size: 10px; font-weight: bold; margin-bottom: 4px;">◄ IN POINT</div>
        <div :style="`color: white; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px ${themeColors.in}80;`">{{ trimStart || '--:--:--:--' }}</div>
      </div>
    </div>

    <!-- Left Side: Hotkeys List -->
    <div style="position: absolute; top: 100px; left: 50px; bottom: 70px; z-index: 999999;">
      <div class="hotkeys-list" style="background: rgba(0, 0, 0, 0.92); padding: 15px; border-radius: 8px; width: 350px; height: 100%; display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        <div @click="$emit('update:showHotkeys', !showHotkeys)" style="color: white; font-size: 14px; font-weight: bold; border-bottom: 2px solid rgba(255, 255, 255, 0.3); padding-bottom: 6px; cursor: pointer; margin-bottom: 8px; pointer-events: auto;">
          ⌨️ HOTKEYS <span style="font-size: 10px; opacity: 0.6;">{{ showHotkeys ? '▼' : '▶' }}</span>
          <span style="color: rgba(255,255,255,0.5); font-size: 9px; margin-left: 10px;">CTRL+1</span>
        </div>
        <div v-show="showHotkeys" style="color: white; font-size: 11px; line-height: 1.6; font-family: 'Helvetica', Arial, sans-serif; flex: 1; overflow-y: auto; padding-right: 8px; pointer-events: auto;">
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
          <div v-if="showThumbnailHotkey" style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #9C27B0; font-weight: bold;">ALT+T</span><span style="color: #9C27B0;">Mark Thumb</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #FF9800; font-weight: bold;">CTRL+ENTER</span><span style="color: #FF9800;">Take Clip</span></div>
          <div v-if="clippingMethod === 'individual-clips'" style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #FFEB3B; font-weight: bold;">ENTER×2</span><span style="color: #FFEB3B;">Take Clip</span></div>
          <div v-if="showCutTypeRow" style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); margin-bottom: 6px; color: rgba(255,255,255,0.7); font-size: 10px;">TYPE OF CUT</div>
          <div v-if="showCutTypeRow" style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="color: #64B5F6; font-weight: bold;">N</span><span style="color: #64B5F6;">None</span></div>
          <div v-if="showCutTypeRow" style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="color: #64B5F6; font-weight: bold;">S</span><span style="color: #64B5F6;">Single Trim</span></div>
          <div v-if="showCutTypeRow" style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="color: #64B5F6; font-weight: bold;">M</span><span style="color: #64B5F6;">Multiple Clips</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);"><span style="color: #4CAF50; font-weight: bold;">ALT+ENTER</span><span style="color: #4CAF50;">Submit</span></div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #F44336; font-weight: bold;">ESC</span><span style="color: #F44336;">Cancel</span></div>
        </div>
      </div>
    </div>

    <!-- Top Right: OUT Point Display -->
    <div style="position: absolute; top: 5px; right: 50px;">
      <div class="out-point-display" :style="`background: ${themeColors.out}e6; padding: 14px 20px; border-radius: 9px; border-right: 6px solid ${themeColors.outDark}; border: 2px solid ${themeColors.out}80; min-width: 200px;`">
        <div style="color: rgba(255,255,255,0.8); font-size: 10px; font-weight: bold; margin-bottom: 4px; text-align: right;">OUT POINT ►</div>
        <div :style="`color: white; font-size: 30px; font-weight: bold; font-family: 'Orbitron', 'Courier New', monospace; letter-spacing: 3px; text-shadow: 0 0 15px ${themeColors.out}80; text-align: right;`">{{ trimEnd || '--:--:--:--' }}</div>
      </div>

      <!-- Thumbnail Marker Display -->
      <transition name="clip-drop">
        <div v-if="thumbnailTimecode && thumbnailTimecode !== '00:00:00:00'" class="thumbnail-marker-display" :style="`background: ${themeColors.thumb}e6; padding: 14px 18px; border-radius: 10px; border-right: 8px solid ${themeColors.thumbDark}; margin-top: 70px; margin-bottom: 15px; pointer-events: auto; max-width: 400px;`">
          <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 6px; text-align: right;">📸 THUMBNAIL</div>
          <div style="color: white; font-size: 20px; font-weight: bold; font-family: 'Roboto Mono', monospace; letter-spacing: 1px; text-align: right;">{{ thumbnailTimecode }}</div>
        </div>
      </transition>

      <!-- Individual Clip Boxes -->
      <transition-group name="clip-drop">
        <div
          v-for="(clip, index) in clips"
          :key="`clip-${index}`"
          class="clip-box"
          :style="{
            background: `${themeColors.clip}e6`,
            padding: '10px 15px',
            borderRadius: '10px',
            borderRight: `8px solid ${themeColors.clipDark}`,
            marginBottom: '8px',
            marginTop: (index === 0 && (!thumbnailTimecode || thumbnailTimecode === '00:00:00:00')) ? '70px' : '0',
            pointerEvents: 'auto',
            maxWidth: '560px'
          }"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="color: white; font-size: 18px; font-weight: bold;">CLIP {{ index + 1 }}</div>
            <button @click="$emit('remove-clip', index)" style="background: #f44336; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 13px; cursor: pointer; font-weight: bold; transition: all 0.2s;">✕</button>
          </div>
          <input
            :value="clip.slug"
            @input="$emit('update-clip-slug', { index, slug: $event.target.value })"
            placeholder="clip-slug-here"
            style="width: 100%; padding: 6px; margin-bottom: 6px; background: rgba(255, 255, 255, 0.2); border: 2px solid rgba(255, 255, 255, 0.4); border-radius: 6px; color: white; font-size: 16px; font-weight: bold; font-family: 'Roboto Mono', monospace;"
            @click.stop
          />
          <div style="color: white; font-size: 14px; font-family: 'Roboto Mono', monospace; margin-bottom: 2px;">{{ clip.time_start }} → {{ clip.time_end }}</div>
          <div style="color: rgba(255, 255, 255, 0.7); font-size: 13px; font-family: 'Roboto Mono', monospace;">Duration: {{ Math.round(clip.duration_seconds) }}s</div>
        </div>
      </transition-group>

      <!-- Single Trim Clip Card -->
      <transition name="clip-drop">
        <div
          v-if="clippingMethod === 'single-trim' && trimStart && trimEnd && clipDuration"
          key="single-trim-card"
          class="clip-box"
          :style="{
            background: `${themeColors.in}e6`,
            padding: '18px',
            borderRadius: '10px',
            borderRight: `8px solid ${themeColors.inDark}`,
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
</template>

<script setup>
// MediaModalOverlays — pure props/emit forwarder. Owns no state; the
// modal supplies every reactive value. See default themeColors below
// for the palette contract.

defineProps({
  show: { type: Boolean, required: true },
  mediaLoaded: { type: Boolean, default: false },

  currentTimecode: { type: String, default: '00:00:00:00' },
  remainingTimecode: { type: String, default: '00:00:00:00' },
  currentActionDisplay: { type: String, default: '' },

  trimStart: { type: String, default: '' },
  trimEnd: { type: String, default: '' },
  clipDuration: { type: [String, Number], default: 0 },

  // Playback speed indicator
  showSpeedIndicator: { type: Boolean, default: false },
  playbackSpeed: { type: Number, default: 1.0 },
  speedLabel: { type: String, default: 'Normal' },

  // Frame counter
  showFrameCounter: { type: Boolean, default: false },
  currentFrameNumber: { type: Number, default: 0 },
  totalFrames: { type: Number, default: 0 },
  frameStepDirection: { type: String, default: '' },

  // Thumbnail marker (set to '00:00:00:00' or empty to hide)
  thumbnailTimecode: { type: String, default: '' },

  // Clip state
  clippingMethod: { type: String, default: 'none' },
  clips: { type: Array, default: () => [] },
  clipSlug: { type: String, default: '' },
  slug: { type: String, default: '' },

  // Hotkeys sidebar
  showHotkeys: { type: Boolean, default: false },
  showCutTypeRow: { type: Boolean, default: true },
  showThumbnailHotkey: { type: Boolean, default: true },

  // Theme — each variant has a base color and a `-Dark` accent.
  // SOT defaults to the broadcast palette (blue IN, orange OUT,
  // orange clip, purple thumb, green speed).
  themeColors: {
    type: Object,
    default: () => ({
      in: '#2196F3', inDark: '#1976D2',
      out: '#FF5722', outDark: '#E64A19',
      clip: '#FF9800', clipDark: '#F57C00',
      thumb: '#9C27B0', thumbDark: '#7B1FA2',
      speed: '#4CAF50'
    })
  }
})

defineEmits(['update:showHotkeys', 'update-clip-slug', 'remove-clip'])
</script>

<style scoped>
/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.speed-fade-enter-active,
.speed-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.speed-fade-enter-from,
.speed-fade-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.frame-counter-fade-enter-active,
.frame-counter-fade-leave-active {
  transition: opacity 0.2s ease;
}
.frame-counter-fade-enter-from,
.frame-counter-fade-leave-to {
  opacity: 0;
}

.clip-drop-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.clip-drop-leave-active {
  transition: all 0.25s ease;
}
.clip-drop-enter-from {
  opacity: 0;
  transform: translateY(-30px) scale(0.95);
}
.clip-drop-leave-to {
  opacity: 0;
  transform: translateX(50px);
}
</style>
