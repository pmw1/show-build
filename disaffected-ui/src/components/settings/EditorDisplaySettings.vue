<template>
  <v-card variant="flat" class="editor-display-settings">
    <v-card-title class="d-flex align-center">
      <v-icon class="me-2">mdi-format-size</v-icon>
      Editor Display
      <v-chip size="x-small" color="primary" variant="tonal" class="ms-2">Per-user</v-chip>
    </v-card-title>

    <v-card-subtitle>
      Sizes and density used inside the content editor. Each control is
      personal to your account — others see their own values.
    </v-card-subtitle>

    <v-card-text>
      <!-- Live preview -->
      <div class="preview-wrap mb-4">
        <div class="preview-label">Preview</div>
        <div class="preview-script">
          The audience leans in. The host pauses for emphasis, then continues:
          this is what a paragraph looks like at your current settings.
        </div>
        <div class="preview-cue">
          <div class="preview-cue-tag">FSQ</div>
          <div class="preview-cue-body">
            Cue card text. Adjusts with both the cue font size and the density slider.
          </div>
        </div>
      </div>

      <!-- Knobs -->
      <div v-for="knob in knobs" :key="knob.key" class="knob-row">
        <div class="d-flex align-center mb-1">
          <OverridableDot :pref-key="knob.key" />
          <span class="knob-label ms-2">{{ labelFor(knob.key) }}</span>
          <v-spacer />
          <span class="knob-current text-caption text-grey">
            {{ formatValue(knob, valueFor[knob.key]) }}
          </span>
          <v-btn
            v-if="hasOverride(knob.key)"
            icon="mdi-restore"
            size="x-small"
            variant="text"
            class="ms-1"
            title="Reset to default"
            @click="resetKnob(knob.key)"
          />
        </div>

        <v-slider
          v-if="knob.densityToPad == null"
          :model-value="numeric(valueFor[knob.key], knob)"
          :min="knob.min"
          :max="knob.max"
          :step="knob.step"
          color="primary"
          density="compact"
          hide-details
          thumb-label
          @update:model-value="onSlider(knob, $event)"
        />
        <v-btn-toggle
          v-else
          :model-value="String(valueFor[knob.key] || knob.fallback)"
          mandatory
          divided
          density="compact"
          color="primary"
          @update:model-value="setKnob(knob.key, $event)"
        >
          <v-btn value="compact">Compact</v-btn>
          <v-btn value="comfortable">Comfortable</v-btn>
          <v-btn value="roomy">Roomy</v-btn>
        </v-btn-toggle>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useEditorDisplayPrefs } from '@/composables/useEditorDisplayPrefs'
import { useUserPrefs } from '@/composables/useUserPrefs'
import OverridableDot from '@/components/OverridableDot.vue'

const display = useEditorDisplayPrefs()
const prefs = useUserPrefs()

// Select-type knobs (e.g. font family) are rendered by TypesettingSettings, not
// here — this panel only handles sliders / density toggles.
const knobs = computed(() => display.listKnobs().filter(k => !k.options))
const valueFor = computed(() => display.valueFor.value)

function hasOverride(key) {
  return key in (prefs.cache.value || {})
}

function setKnob(key, value) {
  display.setKnob(key, value)
}

function resetKnob(key) {
  display.resetKnob(key)
}

function onSlider(knob, value) {
  // Slider always returns a number — convert to integer for px keys.
  const v = knob.step >= 1 ? Math.round(value) : value
  display.setKnob(knob.key, v)
}

function numeric(v, knob) {
  if (typeof v === 'number') return v
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : knob.fallback
}

function formatValue(knob, value) {
  if (knob.densityToPad) return String(value || knob.fallback)
  if (value == null) return `${knob.fallback}${knob.unit}`
  return `${value}${knob.unit}`
}

const LABELS = {
  'editor.display.scriptFontSize': 'Script paragraph text size',
  'editor.display.scriptLineHeight': 'Script line spacing',
  'editor.display.cueBlockFontSize': 'Cue card text size',
  'editor.display.cueBlockDensity': 'Cue card density',
  'editor.display.imageMaxHeight': 'Inline image max height',
  'editor.display.rundownItemFontSize': 'Rundown row text size',
}
function labelFor(key) {
  return LABELS[key] || key
}
</script>

<style scoped>
.editor-display-settings {
  padding-bottom: 16px;
}

.knob-row {
  margin-bottom: 22px;
}

.knob-label {
  font-size: 0.9rem;
  font-weight: 500;
}

.preview-wrap {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  padding: 12px 14px;
}

.preview-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: #888;
  margin-bottom: 8px;
}

.preview-script {
  font-size: var(--editor-script-font-size, 16px);
  line-height: var(--editor-script-line-height, 1.5);
  color: #1a1a1a;
  margin-bottom: 14px;
}

.preview-cue {
  display: flex;
  align-items: stretch;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-left: 4px solid #1976D2;
  border-radius: 4px;
  background: rgba(25, 118, 210, 0.04);
  font-size: var(--editor-cue-font-size, 13px);
}

.preview-cue-tag {
  background: #1976D2;
  color: #fff;
  font-weight: 700;
  font-size: 0.75em;
  letter-spacing: 0.6px;
  display: flex;
  align-items: center;
  padding: var(--editor-cue-density, 8px 10px);
}

.preview-cue-body {
  flex: 1;
  padding: var(--editor-cue-density, 8px 10px);
  color: #444;
}
</style>
