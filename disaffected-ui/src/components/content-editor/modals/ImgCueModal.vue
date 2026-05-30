<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="purple-lighten-2">mdi-image</v-icon>
        {{ editData ? 'Edit Image Cue' : 'Insert Image Cue' }}
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        
        <!-- Slug Input -->
        <v-text-field
          v-model="formData.slug"
          label="Slug *"
          placeholder="e.g., un-women-journalists"
          variant="outlined"
          density="comfortable"
          class="mb-4"
          :rules="[rules.required]"
          hint="Unique identifier for this image (no spaces, use hyphens)"
          persistent-hint
          color="error"
          ref="slugInput"
          autofocus
        ></v-text-field>

        <!-- Description Input -->
        <v-text-field
          v-model="formData.description"
          label="Description"
          placeholder="Brief description of the image"
          variant="outlined"
          density="comfortable"
          class="mb-4"
        ></v-text-field>

        <!-- Credit Input -->
        <v-text-field
          v-model="formData.credit"
          label="Photo Credit"
          placeholder="e.g., AP Photo, Reuters, Getty Images"
          variant="outlined"
          density="comfortable"
          class="mb-4"
        ></v-text-field>

        <!-- Caption Input -->
        <v-textarea
          v-model="formData.caption"
          label="Caption"
          placeholder="Image caption for display"
          variant="outlined"
          density="comfortable"
          rows="2"
          class="mb-4"
        ></v-textarea>

        <!-- Image Upload Section -->
        <div class="mb-4">
          <h6 class="text-h6 mb-2">Add Image</h6>
          
          <!-- Image Preview -->
          <div v-if="previewUrl" class="mb-3">
            <v-card variant="outlined" class="pa-2">
              <img
                :src="previewUrl"
                alt="Image preview"
                style="max-width: 100%; max-height: 200px; object-fit: contain;"
                class="mx-auto d-block"
              />
              <div class="d-flex justify-space-between align-center mt-2 px-2">
                <v-chip size="small" color="success">{{ fileName }}</v-chip>
                <v-btn
                  color="error"
                  variant="flat"
                  size="small"
                  @click="clearImage"
                  :prepend-icon="'mdi-delete'"
                  style="color: white;"
                >
                  Clear
                </v-btn>
              </div>
            </v-card>
          </div>

          <!-- Upload Buttons -->
          <div class="d-flex gap-3 justify-center">
            <v-btn
              @click="pasteFromClipboard"
              :color="clipboardDetection.buttonColor.value"
              variant="outlined"
              :prepend-icon="'mdi-clipboard-outline'"
              :loading="clipboardDetection.isProcessing.value"
              :disabled="!!previewUrl"
              ref="pasteTarget"
              tabindex="0"
            >
              {{ clipboardDetection.buttonLabel.value }}
              <v-tooltip activator="parent" location="bottom">
                {{ pasteShortcut }} - {{ clipboardDetection.statusMessage.value || 'Paste image from clipboard' }}
              </v-tooltip>
            </v-btn>

            <v-btn
              @click="selectFile"
              color="primary"
              variant="outlined"
              :prepend-icon="'mdi-file-image'"
              :disabled="!!previewUrl"
            >
              Select File
              <v-tooltip activator="parent" location="bottom">
                {{ fileSelectShortcut }}
              </v-tooltip>
            </v-btn>
          </div>

          <!-- Hidden file input -->
          <input
            ref="imgFileInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>

        <!-- Error Messages -->
        <v-alert
          v-if="errorMessage"
          type="error"
          variant="text"
          class="mb-4"
        >
          {{ errorMessage }}
        </v-alert>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
        <v-btn
          color="primary"
          @click="submit"
          :disabled="!canSubmit"
          :loading="submitLoading"
        >
          {{ editData ? 'Update IMG Cue' : 'Insert IMG Cue' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { useRequireEpisode } from '@/composables/useRequireEpisode'
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'
import { registerModalEsc } from '@/composables/useModalStack'
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  currentEpisode: {
    type: String,
    default: ''
  },
  editData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:show', 'submit'])

const { requireEpisode } = useRequireEpisode()
const clipboardDetection = useClipboardImageDetection({
  autoProbeClipboard: false,
  onImageReady: null
})

// Template refs
const slugInput = ref(null)
const imgFileInput = ref(null)

// Data
const formData = ref({
  slug: '',
  description: '',
  credit: '',
  caption: ''
})
const imageFile = ref(null)
const previewUrl = ref('')
const fileName = ref('')
const pasteLoading = ref(false)
const submitLoading = ref(false)
const errorMessage = ref('')
const temporaryEpisode = ref(null)
const rules = {
  required: value => !!value || 'This field is required'
}

// Computed
const canSubmit = computed(() => {
  if (props.editData) {
    const result = formData.value.slug.trim() && (imageFile.value || previewUrl.value)
    console.error('canSubmit (EDIT mode):', {
      result,
      slug: formData.value.slug,
      imageFile: !!imageFile.value,
      previewUrl: !!previewUrl.value
    })
    return result
  }
  const result = formData.value.slug.trim() && imageFile.value
  console.error('canSubmit (CREATE mode):', {
    result,
    slug: formData.value.slug,
    imageFile: !!imageFile.value,
    imageFileName: fileName.value
  })
  return result
})

const isMac = computed(() => {
  return typeof navigator !== 'undefined' && navigator.platform && navigator.platform.toUpperCase().indexOf('MAC') >= 0
})

const pasteShortcut = computed(() => {
  return isMac.value ? 'Cmd+V' : 'Ctrl+V'
})

const fileSelectShortcut = computed(() => {
  return isMac.value ? 'Cmd+O' : 'Ctrl+O'
})

// Watch
watch(() => props.show, (newVal) => {
  if (newVal) {
    clipboardDetection.probeClipboard()

    if (props.editData) {
      formData.value = {
        slug: props.editData.rawData?.slug || props.editData.slug || '',
        description: props.editData.rawData?.description || '',
        credit: props.editData.rawData?.credit || '',
        caption: props.editData.rawData?.caption || ''
      }

      const mediaUrl = props.editData.rawData?.mediaurl
      if (mediaUrl) {
        previewUrl.value = mediaUrl
        fileName.value = mediaUrl.split('/').pop() || 'existing-image'
      }
    } else {
      resetForm()
    }

    nextTick(() => {
      if (slugInput.value) {
        slugInput.value.focus()
      }
    })
  }
})

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('paste', handleGlobalPaste)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('paste', handleGlobalPaste)
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
})

// ESC handled by global modal stack
registerModalEsc(() => props.show, () => cancel(), 'ImgCueModal')
useDoubleEnterToSlug(() => props.show, slugInput)

// Methods
function handleKeydown(event) {
  if (!props.show) return

  // Don't intercept Ctrl+V / Cmd+V here — let the native paste event fire
  // so handleGlobalPaste receives the actual clipboardData from the browser.
  // Intercepting keydown + calling pasteFromClipboard() bypasses the paste event
  // and forces use of navigator.clipboard.read() which often lacks permission.

  const isValidFileSelect = isMac.value
    ? (event.metaKey && event.key === 'o' && !event.ctrlKey && !event.altKey)
    : (event.ctrlKey && event.key === 'o' && !event.altKey && !event.metaKey)

  if (isValidFileSelect) {
    if (!['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
      event.preventDefault()
      if (!previewUrl.value) {
        selectFile()
      }
    }
    return
  }
}

async function pasteFromClipboard() {
  try {
    const result = await clipboardDetection.pasteImage()

    if (result && result.file) {
      await processImageFile(result.file, result.filename)
    }
  } catch (error) {
    console.error('Paste failed:', error)
    errorMessage.value = error.message || 'Failed to paste image from clipboard'
  }
}

function getPasteInstructions() { // eslint-disable-line no-unused-vars
  return `Press ${pasteShortcut.value} to paste your image`
}

async function handleGlobalPaste(event) {
  console.log('Global paste event fired:', {
    modalOpen: props.show,
    target: event.target?.tagName || 'unknown'
  })

  if (!props.show) {
    console.log('Ignoring paste - modal not open')
    return
  }

  event.preventDefault()

  try {
    const result = await clipboardDetection.pasteImage(event)

    if (result && result.file) {
      await processImageFile(result.file, result.filename)
    }
  } catch (error) {
    console.error('Paste failed:', error)
    errorMessage.value = error.message || 'Failed to paste image from clipboard'
  }
}

function selectFile() {
  imgFileInput.value.click()
}

async function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    await processImageFile(file, file.name)
  }
  event.target.value = ''
}

async function processImageFile(file, name) {
  console.error('processImageFile called:', { name, type: file.type, size: file.size })

  if (!file.type.startsWith('image/')) {
    errorMessage.value = 'Please select a valid image file.'
    console.error('Invalid file type:', file.type)
    return
  }

  if (file.size > 20 * 1024 * 1024) {
    errorMessage.value = 'Image file must be smaller than 20MB.'
    console.error('File too large:', file.size)
    return
  }

  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }

  imageFile.value = file
  fileName.value = name
  previewUrl.value = URL.createObjectURL(file)
  errorMessage.value = ''

  console.error('Image processed successfully:', {
    fileName: fileName.value,
    imageFile: !!imageFile.value,
    previewUrl: !!previewUrl.value
  })
}

function clearImage() {
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  imageFile.value = null
  previewUrl.value = ''
  fileName.value = ''
  errorMessage.value = ''
}

function getFileExtension() {
  if (imageFile.value && imageFile.value.type) {
    const mimeType = imageFile.value.type
    if (mimeType === 'image/jpeg') return 'jpg'
    if (mimeType === 'image/png') return 'png'
    if (mimeType === 'image/gif') return 'gif'
    if (mimeType === 'image/webp') return 'webp'
    return mimeType.split('/')[1] || 'png'
  }
  return 'png'
}

function sanitizeSlug(slug) {
  return slug
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function getCurrentEpisode() {
  const episode = requireEpisode(
    props.currentEpisode,
    'Upload Image',
    (selectedEpisode) => {
      console.log('Episode selected from modal, retrying upload with:', selectedEpisode)
      temporaryEpisode.value = selectedEpisode
      submit()
    }
  )

  if (episode) {
    console.log('Episode available for upload:', episode)
    return episode
  }

  if (temporaryEpisode.value) {
    const temp = temporaryEpisode.value
    temporaryEpisode.value = null
    return temp
  }

  console.log('No episode - modal will prompt user')
  return null
}

async function uploadImage(filename) {
  try {
    const episode = getCurrentEpisode()
    if (!episode) {
      console.log('Upload paused - waiting for episode selection')
      return { success: false, message: 'Waiting for episode selection' }
    }

    const uploadFormData = new FormData()
    uploadFormData.append('file', imageFile.value)
    uploadFormData.append('filename', filename)
    uploadFormData.append('episode', episode)

    const response = await axios.post('/api/upload/image', uploadFormData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data && response.data.status === 'success') {
      return {
        success: true,
        filepath: response.data.filepath,
        filename: response.data.filename
      }
    } else {
      return {
        success: false,
        error: response.data?.message || 'Upload failed'
      }
    }
  } catch (error) {
    console.error('Image upload error:', error)
    return {
      success: false,
      error: error.response?.data?.detail || 'Network error during upload'
    }
  }
}

async function submit() {
  console.error('ImgCueModal submit() called')
  console.error('canSubmit:', canSubmit.value)

  if (!canSubmit.value) {
    console.error('Submit blocked - canSubmit is false')
    return
  }

  submitLoading.value = true
  errorMessage.value = ''

  try {
    let filename
    let filepath

    // In edit mode without a newly-selected file, keep the existing image
    // (just metadata/slug edits). Otherwise upload the new file.
    const isEditWithoutNewFile = !!props.editData && !imageFile.value
    if (isEditWithoutNewFile) {
      filepath = props.editData.rawData?.mediaurl || previewUrl.value
      filename = filepath ? filepath.split('/').pop() : ''
      console.error('Edit mode, no new file — reusing existing media:', filepath)
    } else {
      console.error('Generating filename...')
      const fileExtension = getFileExtension()
      const sanitizedSlug = sanitizeSlug(formData.value.slug)
      filename = `${sanitizedSlug}.${fileExtension}`
      console.error('Filename:', filename)

      console.error('Uploading image...')
      const uploadResult = await uploadImage(filename)
      console.error('Upload result:', uploadResult)

      if (!uploadResult.success) {
        if (uploadResult.message === 'Waiting for episode selection') {
          console.log('Upload paused - episode modal will handle retry')
          return
        }
        console.error('Upload failed:', uploadResult.error)
        errorMessage.value = uploadResult.error || 'Failed to upload image'
        return
      }
      filepath = uploadResult.filepath
    }

    const imgCueData = {
      type: 'IMG',
      slug: formData.value.slug,
      description: formData.value.description,
      credit: formData.value.credit,
      caption: formData.value.caption,
      filename: filename,
      filepath: filepath,
      imageFile: imageFile.value
    }
    console.error('Created imgCueData:', imgCueData)

    console.error('Emitting submit event to parent...')
    emit('submit', imgCueData)
    console.error('Submit event emitted!')

    cancel()
  } catch (error) {
    console.error('Submit error:', error)
    errorMessage.value = 'Failed to create IMG cue. Please try again.'
  } finally {
    submitLoading.value = false
  }
}

function resetForm() {
  formData.value = {
    slug: '',
    description: '',
    credit: '',
    caption: ''
  }
  clearImage()
  errorMessage.value = ''
  submitLoading.value = false
  pasteLoading.value = false
}

function cancel() {
  console.error('ImgCueModal cancel() called - closing modal')
  emit('update:show', false)
}
</script>

<style scoped>
.gap-3 {
  gap: 12px;
}
</style>