<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Note Cue</v-card-title>
      <v-card-text>
        <v-select
          v-model="noteFor"
          :items="productionRoles"
          item-title="name"
          item-value="name"
          label="Note For"
          clearable
          hint="Who is this note intended for?"
          persistent-hint
          class="mb-3"
        ></v-select>
        <v-textarea
          ref="noteField"
          v-model="noteText"
          label="Note"
          required
          :rules="[v => !!v || 'Note text is required']"
          rows="4"
          hint="Special note or instruction for the director/crew"
          persistent-hint
        ></v-textarea>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!noteText">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { registerModalEsc } from '@/composables/useModalStack';
import axios from 'axios';
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap';
import { useScreenFlash } from '@/composables/useScreenFlash';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  episode: String,
  duplicateSlugs: {
    type: Array,
    default: () => []
  },
  cueType: {
    type: String,
    default: 'NOTE'
  },
  editingCueData: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:show', 'submit', 'abort']);

// Template refs
const noteField = ref(null);

// Data
const noteText = ref('');
const noteFor = ref(null);
const productionRoles = ref([]);
let keydownHandler = null;

// Mixin-inlined computed: color theming
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

const modalStyles = computed(() => ({
  backgroundColor: cueColorLight.value
}));

const headerStyles = computed(() => ({
  backgroundColor: cueColor.value,
  color: 'white'
}));

// ESC is handled by global modal stack (calls handleAbort).
registerModalEsc(() => props.show, () => handleAbort(), 'DirModal');

// Mixin-inlined: keyboard handlers (Shift+Enter only)
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

// Mixin-inlined: focus slug field (uses noteField ref for this modal)
function focusSlugField() {
  const field = noteField.value;
  if (field) {
    const input = field.$el?.querySelector('input') || field.$el?.querySelector('textarea') || field;
    if (input && input.focus) {
      input.focus();
    }
  }
}

// Methods
async function loadProductionRoles() {
  try {
    const token = localStorage.getItem('auth-token');
    const response = await axios.get('/api/production-roles/', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    if (response.data && response.data.data) {
      productionRoles.value = response.data.data;
    }
  } catch (err) {
    console.warn('Failed to load production roles:', err);
  }
}

async function handleSubmit() {
  if (!noteText.value) {
    return;
  }
  await submit();
}

async function submit() {
  const cueBlockContent = buildCueBlock();
  emit('submit', cueBlockContent);
  reset();
}

function buildCueBlock() {
  let block = '<!-- Begin Cue -->\n';
  block += '[Type: NOTE]\n';
  if (noteFor.value) {
    block += `[Note For: ${noteFor.value}]\n`;
  }
  block += `[Note Text: ${noteText.value}]\n`;
  block += '<!-- End Cue -->';
  return block;
}

function handleAbort() {
  const { flashUrgent } = useScreenFlash();
  flashUrgent('ABORT', '#F44336', 500);
  emit('update:show', false);
  emit('abort');
  reset();
}

function reset() {
  noteText.value = '';
  noteFor.value = null;
}

// Watch
watch(() => props.show, (newVal) => {
  if (newVal) {
    // Populate fields when opening in edit mode
    if (props.editingCueData) {
      noteText.value = props.editingCueData.noteText || '';
      noteFor.value = props.editingCueData.noteFor || null;
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

onMounted(async () => {
  if (props.show) {
    setupKeyboardHandlers();
    nextTick(() => {
      focusSlugField();
    });
  }
  await loadProductionRoles();
});

onBeforeUnmount(() => {
  removeKeyboardHandlers();
});
</script>

<style scoped>
/* Fix text visibility - add proper padding */
.v-card-text {
  padding-top: 32px !important;
}

/* Ensure text fields have proper spacing and prevent label cutoff */
.v-text-field,
.v-textarea {
  margin-bottom: 16px;
  margin-top: 8px;
}

/* Prevent label from being cut off */
:deep(.v-field__field) {
  padding-top: 12px;
  padding-bottom: 12px;
}

/* Fix textarea input fading/cutoff issue (Vuetify clip-path bug) */
:deep(.v-field),
:deep(.v-field__field),
:deep(.v-field__input),
:deep(textarea) {
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  overflow: visible !important;
}

:deep(.v-field__input) {
  padding-top: 8px !important;
  min-height: auto !important;
}

:deep(textarea.v-field__input) {
  padding-top: 8px !important;
  line-height: 1.5 !important;
}
</style>
