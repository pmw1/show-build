<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card class="rif-modal-card">
      <v-card-title class="rif-modal-header">{{ editCueData ? 'Edit' : 'Add' }} Riff (RIF) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>

        <div class="duration-label">Duration</div>
        <div class="time-spinner">
          <div class="time-segment">
            <v-btn icon size="x-small" variant="text" @click="incrementHours" tabindex="-1">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <input
              type="text"
              class="time-input"
              :value="hours"
              maxlength="2"
              @input="onHoursInput"
              @keydown="handleTimeKeydown($event, 'hours')"
            />
            <v-btn icon size="x-small" variant="text" @click="decrementHours" tabindex="-1">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <div class="time-label">HRS</div>
          </div>
          <span class="time-colon">:</span>
          <div class="time-segment">
            <v-btn icon size="x-small" variant="text" @click="incrementMinutes" tabindex="-1">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <input
              type="text"
              class="time-input"
              :value="minutes"
              maxlength="2"
              @input="onMinutesInput"
              @keydown="handleTimeKeydown($event, 'minutes')"
            />
            <v-btn icon size="x-small" variant="text" @click="decrementMinutes" tabindex="-1">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <div class="time-label">MIN</div>
          </div>
          <span class="time-colon">:</span>
          <div class="time-segment">
            <v-btn icon size="x-small" variant="text" @click="incrementSeconds" tabindex="-1">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <input
              type="text"
              class="time-input"
              :value="seconds"
              maxlength="2"
              @input="onSecondsInput"
              @keydown="handleTimeKeydown($event, 'seconds')"
            />
            <v-btn icon size="x-small" variant="text" @click="decrementSeconds" tabindex="-1">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <div class="time-label">SEC</div>
          </div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, getCurrentInstance, onMounted, onBeforeUnmount } from 'vue';
import { registerModalEsc } from '@/composables/useModalStack';
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug';
import axios from 'axios';
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap';
import { useScreenFlash } from '@/composables/useScreenFlash';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  episode: String, // eslint-disable-line no-unused-vars
  duplicateSlugs: {
    type: Array,
    default: () => []
  },
  editCueData: {
    type: Object,
    default: null
  },
  cueType: {
    type: String,
    default: 'rif'
  }
});

const emit = defineEmits(['update:show', 'submit', 'abort']);

// $toast access
const $toast = getCurrentInstance()?.appContext.config.globalProperties.$toast;

// Template refs
const slugField = ref(null);

// Data
const slug = ref('');
const hours = ref('00');
const minutes = ref('01');
const seconds = ref('00');
let keydownHandler = null;

// Computed
const duration = computed(() => `${hours.value}:${minutes.value}:${seconds.value}`);

// Mixin-inlined computed: color theming (unused in template but kept for consistency)
const cueColor = computed(() => { // eslint-disable-line no-unused-vars
  const colorName = getColorValue(props.cueType.toLowerCase());
  return resolveVuetifyColor(colorName);
});

const cueColorLight = computed(() => { // eslint-disable-line no-unused-vars
  const color = cueColor.value;
  if (!color || !color.startsWith('#')) return '#f5f5f5';
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const lighten = (c) => Math.round(c + (255 - c) * 0.8);
  const newR = lighten(r).toString(16).padStart(2, '0');
  const newG = lighten(g).toString(16).padStart(2, '0');
  const newB = lighten(b).toString(16).padStart(2, '0');
  return `#${newR}${newG}${newB}`;
});

// --- Time spinner methods ---
function pad(val) {
  return String(val).padStart(2, '0');
}

function clamp(val, min, max) {
  const n = parseInt(val, 10);
  if (isNaN(n)) return min;
  return Math.min(Math.max(n, min), max);
}

function onHoursInput(e) {
  const raw = e.target.value.replace(/\D/g, '');
  hours.value = pad(clamp(raw, 0, 99));
}

function onMinutesInput(e) {
  const raw = e.target.value.replace(/\D/g, '');
  minutes.value = pad(clamp(raw, 0, 59));
}

function onSecondsInput(e) {
  const raw = e.target.value.replace(/\D/g, '');
  seconds.value = pad(clamp(raw, 0, 59));
}

function incrementHours() { hours.value = pad(clamp(parseInt(hours.value) + 1, 0, 99)); }
function decrementHours() { hours.value = pad(clamp(parseInt(hours.value) - 1, 0, 99)); }
function incrementMinutes() { minutes.value = pad((parseInt(minutes.value) + 1) % 60); }
function decrementMinutes() { minutes.value = pad((parseInt(minutes.value) + 59) % 60); }
function incrementSeconds() { seconds.value = pad((parseInt(seconds.value) + 1) % 60); }
function decrementSeconds() { seconds.value = pad((parseInt(seconds.value) + 59) % 60); }

function handleTimeKeydown(event, field) {
  if (event.key === 'ArrowUp') {
    event.preventDefault();
    if (field === 'hours') incrementHours();
    else if (field === 'minutes') incrementMinutes();
    else incrementSeconds();
  } else if (event.key === 'ArrowDown') {
    event.preventDefault();
    if (field === 'hours') decrementHours();
    else if (field === 'minutes') decrementMinutes();
    else decrementSeconds();
  }
}

function parseDuration(dur) {
  if (!dur) return;
  const parts = dur.split(':');
  if (parts.length === 3) {
    hours.value = pad(clamp(parts[0], 0, 99));
    minutes.value = pad(clamp(parts[1], 0, 59));
    seconds.value = pad(clamp(parts[2], 0, 59));
  }
}

// ESC is handled by global modal stack (calls handleAbort).
registerModalEsc(() => props.show, () => handleAbort(), 'RifModal');
useDoubleEnterToSlug(() => props.show, slugField);

// Mixin-inlined: keyboard handlers (Shift+Enter only — ESC handled above)
function setupKeyboardHandlers() {
  keydownHandler = (event) => {
    if (event.shiftKey && event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      handleSubmit();
    }
  };
  document.addEventListener('keydown', keydownHandler, true);
}

function removeKeyboardHandlers() {
  if (keydownHandler) {
    document.removeEventListener('keydown', keydownHandler, true);
    keydownHandler = null;
  }
}

// Mixin-inlined: focus slug field
function focusSlugField() {
  const field = slugField.value;
  if (field) {
    const input = field.$el?.querySelector('input') || field;
    if (input && input.focus) {
      input.focus();
    }
  }
}

// Mixin-inlined: abort with flash
function handleAbort() {
  const { flashUrgent } = useScreenFlash();
  flashUrgent('ABORT', '#F44336', 500);
  emit('update:show', false);
  emit('abort');
}

// --- Submit / Reset ---
async function handleSubmit() {
  if (!slug.value) return;
  await submit();
}

async function submit() {
  const normalizedSlug = slug.value.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
  try {
    const formData = new FormData();
    formData.append('type', 'rif');
    formData.append('slug', normalizedSlug);
    const response = await axios.post('/assetid/generate-legacy', formData, {
      headers: {
        'Accept': 'application/json',
        'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
      }
    });
    const assetID = response.data.id;

    emit('submit', {
      slug: normalizedSlug,
      duration: duration.value,
      assetID
    });
    $toast?.success('RIF cue added');
    reset();
  } catch (error) {
    console.error('Failed to add RIF cue:', error);
    $toast?.error('Failed to add RIF cue');
  }
}

function reset() {
  slug.value = '';
  hours.value = '00';
  minutes.value = '01';
  seconds.value = '00';
  emit('update:show', false);
}

// Watch
watch(() => props.show, (val) => {
  if (val) {
    if (props.editCueData) {
      slug.value = props.editCueData.slug || '';
      parseDuration(props.editCueData.duration);
    }
    setupKeyboardHandlers();
    nextTick(() => {
      focusSlugField();
    });
  } else {
    removeKeyboardHandlers();
    reset();
  }
});

onMounted(() => {
  if (props.show) {
    setupKeyboardHandlers();
    nextTick(() => {
      focusSlugField();
    });
  }
});

onBeforeUnmount(() => {
  removeKeyboardHandlers();
});
</script>

<style scoped>
.rif-modal-card {
  padding: 16px;
  background-color: #EDE7F6 !important;
}

.rif-modal-header {
  background-color: #5C6BC0;
  color: white;
  border-radius: 4px;
  padding: 12px 16px;
  font-weight: 600;
}

.v-card-text {
  padding-top: 24px !important;
}

.v-text-field {
  margin-bottom: 8px;
  margin-top: 8px;
}

:deep(.v-field__field) {
  padding-top: 12px;
  padding-bottom: 12px;
}

:deep(.v-field__input) {
  padding-top: 8px !important;
  min-height: auto !important;
}

/* Duration label */
.duration-label {
  font-size: 0.85rem;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 8px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* Time spinner */
.time-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 0;
}

.time-segment {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.time-input {
  width: 52px;
  height: 48px;
  text-align: center;
  font-size: 1.6rem;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
  border: 2px solid rgba(92, 107, 192, 0.4);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.85);
  color: #311B92;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
}

.time-input:focus {
  border-color: #5C6BC0;
  background: rgba(255, 255, 255, 0.95);
}

.time-colon {
  font-size: 2rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.4);
  padding: 0 2px;
  margin-top: -16px;
}

.time-label {
  font-size: 0.65rem;
  color: rgba(0, 0, 0, 0.45);
  letter-spacing: 1px;
  font-weight: 600;
  margin-top: 2px;
}

.time-segment :deep(.v-btn) {
  color: #5C6BC0 !important;
}

.time-segment :deep(.v-btn:hover) {
  color: #311B92 !important;
}
</style>
