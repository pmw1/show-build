<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="purple">mdi-image-outline</v-icon>
        Create GFX Item
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text class="pb-2">
        <v-form ref="gfxFormRef" v-model="formValid">
          <!-- Slug (required) -->
          <v-text-field
            v-model="formData.slug"
            label="Slug"
            placeholder="short-descriptive-name"
            :rules="slugRules"
            required
            variant="outlined"
            density="comfortable"
            class="mb-3"
          >
            <template #append-inner>
              <span class="text-error">*</span>
            </template>
          </v-text-field>

          <!-- Title -->
          <v-text-field
            v-model="formData.title"
            label="Title"
            placeholder="GFX Title"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <!-- Duration -->
          <v-text-field
            v-model="formData.duration"
            label="Duration (HH:MM:SS:FF)"
            placeholder="00:00:00:00"
            :rules="durationRules"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <!-- Image Selection -->
          <div class="mb-4">
            <v-label class="text-subtitle-2 mb-2">Select Image <span class="text-error">*</span></v-label>
            
            <div class="d-flex gap-2 mb-3">
              <v-btn
                @click="handleClipboardPaste"
                color="primary"
                variant="outlined"
                prepend-icon="mdi-clipboard-outline"
              >
                Paste from Clipboard
              </v-btn>
              
              <v-btn
                @click="$refs.gfxFileInput.click()"
                color="secondary"
                variant="outlined"
                prepend-icon="mdi-folder-open"
              >
                Browse Files
              </v-btn>
            </div>

            <!-- Hidden file input -->
            <input
              ref="gfxFileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none;"
            />

            <!-- Image Preview -->
            <div v-if="imagePreview" class="image-preview-container">
              <v-img
                :src="imagePreview"
                max-width="300"
                max-height="200"
                class="rounded"
              />
              <v-chip
                size="small"
                color="success"
                class="mt-2"
              >
                {{ imageSource }}
              </v-chip>
            </div>

            <v-alert
              v-if="imageError"
              type="error"
              variant="tonal"
              class="mt-2"
            >
              {{ imageError }}
            </v-alert>
          </div>

          <!-- Description -->
          <v-textarea
            v-model="formData.description"
            label="Description"
            placeholder="Optional description of the graphic"
            variant="outlined"
            rows="3"
            auto-grow
            class="mb-3"
          />

          <!-- Error Display -->
          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            class="mb-3"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>
      
      <v-card-actions class="px-6 pb-4">
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel" variant="outlined">
          Cancel
        </v-btn>
        <v-btn 
          color="purple" 
          @click="createGFXItem"
          :disabled="!formValid || !hasImage"
          :loading="loading"
          variant="elevated"
          class="ml-2"
        >
          <v-icon left>mdi-plus</v-icon>
          Create GFX Item
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:show', 'submit']);

const $toast = getCurrentInstance()?.appContext.config.globalProperties.$toast;

// Template refs
const gfxFormRef = ref(null);
const gfxFileInput = ref(null);

// Data
const formValid = ref(false);
const loading = ref(false);
const error = ref('');
const imageError = ref('');
const imagePreview = ref(null);
const imageSource = ref('');
const imageBlob = ref(null);
const imageExtension = ref('');
const formData = reactive({
  slug: '',
  title: '',
  duration: '00:00:00:00',
  description: '',
  type: 'gfx',
  status: 'draft'
});

// Computed
const hasImage = computed(() => {
  return !!imageBlob.value;
});

const slugRules = computed(() => {
  return [
    v => !!v || 'Slug is required',
    v => /^[a-z0-9-]+$/.test(v) || 'Slug must contain only lowercase letters, numbers, and hyphens'
  ];
});

const durationRules = computed(() => {
  return [
    v => !v || /^\d{2}:\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS:FF format'
  ];
});

// Methods
function handleKeydown(event) {
  if (event.key === 'Escape' && props.show) {
    cancel();
  }
}

function handleGlobalKeydown(event) {
  if (event.ctrlKey && event.key === 'v' && props.show) {
    event.preventDefault();
    handleClipboardPaste();
  }
}

async function handleClipboardPaste() {
  imageError.value = '';

  try {
    const clipboardItems = await navigator.clipboard.read();

    for (const clipboardItem of clipboardItems) {
      for (const type of clipboardItem.types) {
        if (type.startsWith('image/')) {
          const blob = await clipboardItem.getType(type);
          const extension = type.split('/')[1] || 'png';

          imageBlob.value = blob;
          imageExtension.value = extension;
          imagePreview.value = URL.createObjectURL(blob);
          imageSource.value = 'Clipboard';

          $toast?.success('Image pasted from clipboard!');
          return;
        }
      }
    }

    imageError.value = 'No image found in clipboard';
  } catch (err) {
    console.error('Clipboard paste error:', err);
    imageError.value = 'Failed to access clipboard. Please try manually.';
  }
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  imageError.value = '';

  if (!file.type.startsWith('image/')) {
    imageError.value = 'Please select an image file';
    return;
  }

  imageBlob.value = file;
  imageExtension.value = file.name.split('.').pop() || 'png';
  imagePreview.value = URL.createObjectURL(file);
  imageSource.value = file.name;

  $toast?.success(`File selected: ${file.name}`);
}

async function createGFXItem() {
  if (!gfxFormRef.value.validate()) {
    return;
  }

  if (!hasImage.value) {
    error.value = 'Please select an image';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    const gfxItem = {
      ...formData,
      imageBlob: imageBlob.value,
      imageExtension: imageExtension.value,
      subtitle: '',
      airdate: '',
      priority: '',
      guests: '',
      tags: '',
      server_message: '',
      customer: '',
      link: ''
    };

    emit('submit', gfxItem);

    resetForm();
    cancel();
  } catch (err) {
    console.error('Error creating GFX item:', err);
    error.value = 'Failed to create GFX item. Please try again.';
  } finally {
    loading.value = false;
  }
}

function resetForm() {
  formData.slug = '';
  formData.title = '';
  formData.duration = '00:00:00:00';
  formData.description = '';
  formData.type = 'gfx';
  formData.status = 'draft';
  imagePreview.value = null;
  imageBlob.value = null;
  imageExtension.value = '';
  imageSource.value = '';
  error.value = '';
  imageError.value = '';

  if (gfxFileInput.value) {
    gfxFileInput.value.value = '';
  }
}

function cancel() {
  resetForm();
  emit('update:show', false);
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
  document.addEventListener('keydown', handleGlobalKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown);
  document.removeEventListener('keydown', handleGlobalKeydown);
});
</script>

<style scoped>
.image-preview-container {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.v-img {
  border: 1px solid #e0e0e0;
}
</style>