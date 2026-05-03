<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Package (PKG) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>
        <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Video File (optional)" accept="video/mp4,video/mpeg" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug || !title || !duration">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, getCurrentInstance } from 'vue'
import axios from 'axios'
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'
import { useScreenFlash } from '@/composables/useScreenFlash'

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
    default: 'pkg'
  }
})

const emit = defineEmits(['update:show', 'submit', 'abort'])

// Toast helper
const instance = getCurrentInstance()
const toast = instance?.appContext.config.globalProperties.$toast || {
  success: (msg) => console.log('[toast:success]', msg),
  error: (msg) => console.log('[toast:error]', msg)
}

// Template refs
const slugField = ref(null)

// Reactive data
const slug = ref('')
const title = ref('')
const duration = ref('')
const timestamp = ref('')
const file = ref(null)

// Keyboard handler reference
let keydownHandler = null

// --- Inlined cueModalMixin computed ---

const cueColor = computed(() => {
  const colorName = getColorValue(props.cueType.toLowerCase())
  return resolveVuetifyColor(colorName)
})

const cueColorLight = computed(() => {
  const color = cueColor.value
  if (!color || !color.startsWith('#')) return '#f5f5f5'

  const hex = color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  const lighten = (c) => Math.round(c + (255 - c) * 0.8)

  const newR = lighten(r).toString(16).padStart(2, '0')
  const newG = lighten(g).toString(16).padStart(2, '0')
  const newB = lighten(b).toString(16).padStart(2, '0')

  return `#${newR}${newG}${newB}`
})

const modalStyles = computed(() => ({
  backgroundColor: cueColorLight.value
}))

const headerStyles = computed(() => ({
  backgroundColor: cueColor.value,
  color: 'white'
}))

// --- Inlined cueModalMixin keyboard handlers ---

function setupKeyboardHandlers() {
  keydownHandler = (event) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      event.stopPropagation()
      handleAbort()
      return
    }
    if (event.shiftKey && event.key === 'Enter') {
      event.preventDefault()
      event.stopPropagation()
      handleSubmit()
      return
    }
  }
  document.addEventListener('keydown', keydownHandler, true)
}

function removeKeyboardHandlers() {
  if (keydownHandler) {
    document.removeEventListener('keydown', keydownHandler, true)
    keydownHandler = null
  }
}

function handleAbort() {
  const { flashUrgent } = useScreenFlash()
  flashUrgent('ABORT', '#F44336', 500)
  emit('update:show', false)
  emit('abort')
}

function focusSlugField() {
  const field = slugField.value
  if (field) {
    const input = field.$el?.querySelector('input') || field
    if (input && input.focus) {
      input.focus()
    }
  }
}

// --- Component methods ---

async function handleSubmit() {
  if (!slug.value || !title.value || !duration.value) {
    return
  }
  await submit()
}

async function submit() {
  const normalizedSlug = slug.value.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-')
  try {
    const formData = new FormData()
    formData.append('type', 'pkg')
    formData.append('slug', normalizedSlug)
    const response = await axios.post('/assetid/generate-legacy', formData, {
      headers: {
        'Accept': 'application/json',
        'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
      }
    })
    const assetID = response.data.id
    let mediaURL = ''
    if (file.value) {
      const uploadForm = new FormData()
      uploadForm.append('type', 'pkg')
      uploadForm.append('episode', props.episode)
      uploadForm.append('asset_id', assetID)
      uploadForm.append('file', file.value)
      uploadForm.append('slug', normalizedSlug)
      uploadForm.append('duration', duration.value)
      uploadForm.append('timestamp', timestamp.value || '00:00:00')
      await axios.post('http://192.168.51.210:8888/preproc_pkg', uploadForm, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
      })
      mediaURL = `episodes/${props.episode}/assets/video/${normalizedSlug}.${file.value.name.split('.').pop()}`
    }
    emit('submit', { title: title.value, duration: duration.value, timestamp: timestamp.value, slug: normalizedSlug, assetID, mediaURL })
    toast.success('PKG cue added')
    reset()
  } catch (error) { toast.error('Failed to add PKG cue') }
}

function reset() {
  slug.value = ''
  title.value = ''
  duration.value = ''
  timestamp.value = ''
  file.value = null
  emit('update:show', false)
}

// --- Watches ---

watch(() => props.show, (newVal) => {
  if (newVal) {
    setupKeyboardHandlers()
    nextTick(() => {
      focusSlugField()
    })
  } else {
    removeKeyboardHandlers()
    reset()
  }
}, { immediate: true })

// --- Lifecycle ---

onMounted(() => {
  if (props.show) {
    setupKeyboardHandlers()
    nextTick(() => {
      focusSlugField()
    })
  }
})

onBeforeUnmount(() => {
  removeKeyboardHandlers()
})
</script>
<style scoped>
.v-card {
  padding: 16px;
}

/* Fix text visibility - add proper padding */
.v-card-text {
  padding-top: 32px !important;
}

/* Ensure text fields have proper spacing and prevent label cutoff */
.v-text-field,
.v-textarea,
.v-file-input {
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
