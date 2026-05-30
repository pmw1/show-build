<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="700">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Bumper from Media Repository</v-card-title>

      <!-- Mode Selection Tabs -->
      <v-tabs v-model="selectedTab" class="mb-3">
        <v-tab value="existing">Select from Repository</v-tab>
        <v-tab value="new">Create New</v-tab>
      </v-tabs>

      <v-card-text>
        <v-window v-model="selectedTab">
          <!-- Select from Library Tab -->
          <v-window-item value="existing">
            <v-text-field
              ref="slugField"
              v-model="slug"
              label="Slug"
              required
              :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
              hint="Unique identifier for this instance"
              persistent-hint
              class="mb-2"
            ></v-text-field>

            <v-select
              v-model="selectedLibraryItem"
              :items="libraryItems"
              item-title="name"
              item-value="id"
              label="Select Bumper from Repository"
              return-object
              @update:model-value="onLibraryItemSelected"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props">
                  <template v-slot:title>
                    <strong>{{ item.raw.name }}</strong>
                  </template>
                  <template v-slot:subtitle>
                    AssetID: {{ item.raw.assetId }} | Duration: {{ item.raw.duration }}
                  </template>
                </v-list-item>
              </template>
            </v-select>

            <!-- Preview of selected library item -->
            <v-card v-if="selectedLibraryItem" variant="outlined" class="mt-3 pa-3">
              <div class="text-subtitle-2 mb-2">Preview</div>
              <div><strong>Name:</strong> {{ selectedLibraryItem.name }}</div>
              <div><strong>AssetID:</strong> {{ selectedLibraryItem.assetId }}</div>
              <div><strong>Duration:</strong> {{ selectedLibraryItem.duration }}</div>
              <div><strong>Media URL:</strong> {{ selectedLibraryItem.mediaUrl || 'N/A' }}</div>
              <div><strong>Alpha:</strong> {{ selectedLibraryItem.alpha ? 'Yes' : 'No' }}</div>
              <div><strong>Audio:</strong> {{ selectedLibraryItem.audio ? 'Yes' : 'No' }}</div>
            </v-card>
          </v-window-item>

          <!-- Create New Tab -->
          <v-window-item value="new">
            <v-text-field
              v-model="slug"
              label="Slug"
              required
              :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
            ></v-text-field>
            <v-text-field
              v-model="assetId"
              label="AssetID"
              required
              :rules="[v => !!v || 'AssetID is required']"
              hint="Associated asset identifier"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="name"
              label="Name"
              required
              :rules="[v => !!v || 'Name is required']"
              hint="Bumper name or description"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="duration"
              label="Duration (HH:MM:SS)"
              required
              :rules="[v => !!v || 'Duration is required', v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
              hint="Duration never changes"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="mediaUrl"
              label="Media URL"
              hint="Link to media file or sequence"
              persistent-hint
            ></v-text-field>
            <v-checkbox
              v-model="alpha"
              label="Alpha Channel"
              hint="Has alpha/transparency"
              persistent-hint
            ></v-checkbox>
            <v-checkbox
              v-model="audio"
              label="Audio"
              hint="Has audio track"
              persistent-hint
            ></v-checkbox>
            <v-checkbox
              v-model="saveToLibrary"
              label="Save to Repository"
              hint="Save this bumper to Media Repository for reuse"
              persistent-hint
            ></v-checkbox>
          </v-window-item>
        </v-window>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn
          color="success"
          @click="handleSubmit"
          :disabled="!isValid"
        >
          Submit (Shift+Enter)
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { registerModalEsc } from '@/composables/useModalStack';
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug';
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap';
import { useScreenFlash } from '@/composables/useScreenFlash';

const props = defineProps({
  show: Boolean,
  episode: String,
  duplicateSlugs: {
    type: Array,
    default: () => []
  },
  cueType: {
    type: String,
    default: 'bump'
  }
});

const emit = defineEmits(['update:show', 'submit', 'abort']);

// Template refs
const slugField = ref(null);

// Data
const selectedTab = ref('existing');
const slug = ref('');
const assetId = ref('');
const name = ref('');
const duration = ref('');
const mediaUrl = ref('');
const alpha = ref(false);
const audio = ref(true);
const saveToLibrary = ref(false);
const libraryItems = ref([]);
const selectedLibraryItem = ref(null);
const loadingLibrary = ref(false); // eslint-disable-line no-unused-vars

// Mixin: cueModalMixin inlined
let keydownHandler = null;

const cueColor = computed(() => {
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

const isValid = computed(() => {
  if (selectedTab.value === 'existing') {
    return !!slug.value && !!selectedLibraryItem.value;
  } else {
    return !!slug.value && !!assetId.value && !!name.value && !!duration.value;
  }
});

// Methods
function focusSlugField() {
  const field = slugField.value;
  if (field) {
    const input = field.$el?.querySelector('input') || field;
    if (input && input.focus) {
      input.focus();
    }
  }
}

// ESC is handled by global modal stack (calls handleAbort).
registerModalEsc(() => props.show, () => handleAbort(), 'BumpModal');
useDoubleEnterToSlug(() => props.show, slugField);

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

async function handleSubmit() {
  if (!isValid.value) {
    return;
  }

  if (selectedTab.value === 'existing' && selectedLibraryItem.value) {
    assetId.value = selectedLibraryItem.value.assetId;
    name.value = selectedLibraryItem.value.name;
    duration.value = selectedLibraryItem.value.duration;
    mediaUrl.value = selectedLibraryItem.value.mediaUrl || '';
    alpha.value = selectedLibraryItem.value.alpha;
    audio.value = selectedLibraryItem.value.audio;
  }

  await submit();
}

async function submit() {
  const cueBlockContent = buildCueBlock();

  if (selectedTab.value === 'new' && saveToLibrary.value) {
    await saveToLibraryDatabase();
  }

  emit('submit', cueBlockContent);
  reset();
}

async function saveToLibraryDatabase() {
  try {
    const response = await fetch('/api/repo', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'bump',
        assetId: assetId.value,
        name: name.value,
        duration: duration.value,
        mediaUrl: mediaUrl.value,
        alpha: alpha.value,
        audio: audio.value
      })
    });

    if (response.ok) {
      console.log('Bumper saved to repository');
      await fetchLibraryItems();
    }
  } catch (error) {
    console.error('Failed to save to repository:', error);
  }
}

async function fetchLibraryItems() {
  loadingLibrary.value = true;
  try {
    const response = await fetch('/api/repo?type=bump');
    if (response.ok) {
      const data = await response.json();
      libraryItems.value = data.items || [];
    }
  } catch (error) {
    console.error('Failed to fetch repository items:', error);
    libraryItems.value = [];
  } finally {
    loadingLibrary.value = false;
  }
}

function onLibraryItemSelected(item) {
  if (item) {
    console.log('Library item selected:', item);
  }
}

function buildCueBlock() {
  let block = '<!-- Begin Cue -->\n';
  block += `[Type: ${props.cueType}]\n`;
  block += `[Slug: ${slug.value}]\n`;
  block += `[AssetID: ${assetId.value}]\n`;
  block += `[Name: ${name.value}]\n`;
  block += `[Duration: ${duration.value}]\n`;
  block += `[Alpha: ${alpha.value}]\n`;
  block += `[Audio: ${audio.value}]\n`;
  if (mediaUrl.value) {
    block += `[Media URL: ${mediaUrl.value}]\n`;
  }
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
  slug.value = '';
  assetId.value = '';
  name.value = '';
  duration.value = '';
  mediaUrl.value = '';
  alpha.value = false;
  audio.value = true;
  saveToLibrary.value = false;
  selectedLibraryItem.value = null;
  selectedTab.value = 'existing';
}

// Watchers
watch(() => props.show, (newVal) => {
  if (newVal) {
    fetchLibraryItems();
    setupKeyboardHandlers();
    nextTick(() => {
      focusSlugField();
    });
  } else {
    removeKeyboardHandlers();
    reset();
  }
}, { immediate: true });

// Lifecycle
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
/* Fix text visibility - add proper padding */
.v-card-text {
  padding-top: 32px !important;
}

/* Ensure text fields have proper spacing and prevent label cutoff */
.v-text-field,
.v-textarea,
.v-select,
.v-checkbox {
  margin-bottom: 16px;
  margin-top: 8px;
}

/* Prevent label from being cut off */
:deep(.v-field__field) {
  padding-top: 12px;
  padding-bottom: 12px;
}

/* Fix textarea input fading/cutoff issue */
:deep(.v-field__input) {
  padding-top: 8px !important;
  min-height: auto !important;
}

:deep(textarea.v-field__input) {
  padding-top: 8px !important;
  line-height: 1.5 !important;
}
</style>
