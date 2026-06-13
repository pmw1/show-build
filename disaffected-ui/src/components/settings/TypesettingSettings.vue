<template>
  <v-card variant="flat" class="typesetting-settings">
    <v-card-title class="d-flex align-center">
      <v-icon class="me-2">mdi-format-font</v-icon>
      Typesetting &amp; Characters
      <v-chip size="x-small" color="primary" variant="tonal" class="ms-2">Per-user</v-chip>
    </v-card-title>

    <v-card-subtitle>
      The font, size and spacing used for Script Mode text, plus a palette of
      special characters. Each setting is personal to your account.
    </v-card-subtitle>

    <v-card-text>
      <!-- Live preview -->
      <div class="preview-wrap mb-6">
        <div class="preview-label">Preview</div>
        <div class="preview-script">
          The audience leans in. The host pauses for emphasis, then continues —
          this is what Script Mode text looks like at your current settings.
        </div>
      </div>

      <!-- Typesetting knobs -->
      <h4 class="section-head">Typesetting</h4>

      <!-- Font family (select) -->
      <div class="knob-row">
        <div class="d-flex align-center mb-1">
          <OverridableDot :pref-key="familyKnob.key" />
          <span class="knob-label ms-2">Font family</span>
        </div>
        <v-select
          :model-value="valueFor[familyKnob.key]"
          :items="familyKnob.options"
          density="compact"
          hide-details
          variant="outlined"
          @update:model-value="setKnob(familyKnob.key, $event)"
        />
      </div>

      <!-- Slider knobs (size, line spacing) -->
      <div v-for="knob in sliderKnobs" :key="knob.key" class="knob-row">
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
      </div>

      <v-divider class="my-6" />

      <!-- Special characters -->
      <h4 class="section-head">Special characters</h4>
      <p class="text-body-2 text-grey mb-3">
        Click a character to copy it to the clipboard, then paste it into the
        editor. Star a character to pin it to your favorites.
      </p>

      <!-- Favorites -->
      <div class="char-group mb-4">
        <div class="char-group-label">Favorites</div>
        <div v-if="charFavorites.length" class="char-grid">
          <button
            v-for="ch in charFavorites"
            :key="'fav-' + ch"
            type="button"
            class="char-cell char-cell--fav"
            :title="'Copy ' + ch + ' (click) · unstar (right-click)'"
            @click="copyChar(ch)"
            @contextmenu.prevent="removeCharFavorite(ch)"
          >
            <span class="char-glyph">{{ ch }}</span>
            <v-icon class="char-star" size="12">mdi-star</v-icon>
          </button>
        </div>
        <div v-else class="char-empty">
          No favorites yet — star a character below to pin it here.
        </div>
      </div>

      <!-- Preset palette -->
      <div class="char-group">
        <div class="char-group-label">All characters</div>
        <div class="char-grid">
          <button
            v-for="preset in presets"
            :key="'preset-' + preset.char"
            type="button"
            class="char-cell"
            :class="{ 'char-cell--pinned': isFavorite(preset.char) }"
            :title="preset.name + ' — copy (click) · ' + (isFavorite(preset.char) ? 'unstar' : 'star') + ' (right-click)'"
            @click="copyChar(preset.char)"
            @contextmenu.prevent="toggleFavorite(preset.char)"
          >
            <span class="char-glyph">{{ preset.char }}</span>
            <v-icon
              class="char-star"
              size="12"
              :color="isFavorite(preset.char) ? 'amber' : undefined"
            >
              {{ isFavorite(preset.char) ? 'mdi-star' : 'mdi-star-outline' }}
            </v-icon>
          </button>
        </div>
      </div>

      <v-snackbar v-model="snackbar" :timeout="1200" location="bottom">
        Copied {{ copied }}
      </v-snackbar>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useEditorDisplayPrefs } from '@/composables/useEditorDisplayPrefs'
import { useUserPrefs } from '@/composables/useUserPrefs'
import OverridableDot from '@/components/OverridableDot.vue'

const display = useEditorDisplayPrefs()
const prefs = useUserPrefs()

const valueFor = computed(() => display.valueFor.value)
const allKnobs = computed(() => display.listKnobs())

// Only the script-text knobs belong in this section (family, size, line height).
const familyKnob = computed(
  () => allKnobs.value.find(k => k.key === 'editor.display.scriptFontFamily') || { key: '', options: [] }
)
const sliderKnobs = computed(() =>
  allKnobs.value.filter(k =>
    k.key === 'editor.display.scriptFontSize' || k.key === 'editor.display.scriptLineHeight'
  )
)

const presets = computed(() => display.listCharPresets())
const charFavorites = computed(() => display.charFavorites.value)

function hasOverride(key) {
  return key in (prefs.cache.value || {})
}
function setKnob(key, value) {
  if (key) display.setKnob(key, value)
}
function resetKnob(key) {
  display.resetKnob(key)
}
function onSlider(knob, value) {
  const v = knob.step >= 1 ? Math.round(value) : value
  display.setKnob(knob.key, v)
}
function numeric(v, knob) {
  if (typeof v === 'number') return v
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : knob.fallback
}
function formatValue(knob, value) {
  if (value == null) return `${knob.fallback}${knob.unit}`
  return `${value}${knob.unit}`
}

const LABELS = {
  'editor.display.scriptFontSize': 'Font size',
  'editor.display.scriptLineHeight': 'Line spacing',
}
function labelFor(key) {
  return LABELS[key] || key
}

// ── Special characters ───────────────────────────────────────────────────────
function isFavorite(ch) {
  return charFavorites.value.includes(ch)
}
function toggleFavorite(ch) {
  if (isFavorite(ch)) display.removeCharFavorite(ch)
  else display.addCharFavorite(ch)
}
function removeCharFavorite(ch) {
  display.removeCharFavorite(ch)
}

const snackbar = ref(false)
const copied = ref('')
async function copyChar(ch) {
  try {
    await navigator.clipboard.writeText(ch)
  } catch {
    // Fallback for browsers without async clipboard access.
    const ta = document.createElement('textarea')
    ta.value = ch
    document.body.appendChild(ta)
    ta.select()
    try { document.execCommand('copy') } catch { /* ignore */ }
    document.body.removeChild(ta)
  }
  copied.value = ch
  snackbar.value = true
}
</script>

<style scoped>
.typesetting-settings {
  padding-bottom: 16px;
}

.section-head {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 16px;
}

.knob-row {
  margin-bottom: 22px;
  max-width: 480px;
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
  font-family: var(--editor-script-font-family, monospace);
  color: #1a1a1a;
}

/* Special characters */
.char-group-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: #999;
  margin-bottom: 8px;
}
.char-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.char-cell {
  position: relative;
  width: 46px;
  height: 46px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 6px;
  background: #fafafa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s, border-color 0.12s;
}
.char-cell:hover {
  background: #eef3ff;
  border-color: #1976d2;
}
.char-cell--pinned {
  border-color: rgba(255, 193, 7, 0.7);
}
.char-cell--fav {
  background: #fff8e1;
  border-color: rgba(255, 193, 7, 0.7);
}
.char-glyph {
  font-size: 20px;
  line-height: 1;
  color: #1a1a1a;
}
.char-star {
  position: absolute;
  top: 2px;
  right: 2px;
  opacity: 0.55;
}
.char-empty {
  font-size: 0.85rem;
  color: #999;
  font-style: italic;
}
</style>
