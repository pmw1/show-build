<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Natural Sound (NAT) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>
        <v-textarea v-model="description" label="Description" required :rules="[v => !!v || 'Description is required']" rows="4"></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug || !description || !duration">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue'
import { registerModalEsc } from '@/composables/useModalStack'
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug'
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
    default: 'nat'
  },
  prefillData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:show', 'submit', 'abort'])

// Template refs
const slugField = ref(null)

// Data
const slug = ref('')
const description = ref('')
const duration = ref('')
const timestamp = ref('')
const file = ref(null)
// When reinserting a pooled file, its existing URL is used in place of a new upload.
const prefilledMediaUrl = ref('')
const prefilledAssetId = ref('')

// Keyboard handler reference
let keydownHandler = null

// Toast access
const instance = getCurrentInstance()
const toast = instance?.proxy?.$toast

// --- Inlined mixin: computed ---

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

// --- Inlined mixin: keyboard handlers ---

// ESC is handled by global modal stack (calls handleAbort).
registerModalEsc(() => props.show, () => handleAbort(), 'NatModal')
useDoubleEnterToSlug(() => props.show, slugField)

function setupKeyboardHandlers() {
  keydownHandler = (event) => {
    if (event.shiftKey && event.key === 'Enter') {
      event.preventDefault()
      event.stopPropagation()
      handleSubmit()
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

function focusSlugField() {
  const el = slugField.value
  if (el) {
    const input = el.$el?.querySelector('input') || el
    if (input && input.focus) {
      input.focus()
    }
  }
}

// --- Component methods ---

function reset() {
  slug.value = ''
  description.value = ''
  duration.value = ''
  timestamp.value = ''
  file.value = null
  prefilledMediaUrl.value = ''
  prefilledAssetId.value = ''
  emit('update:show', false)
}

// Populate from a pooled file being reinserted (existing media, no upload needed).
function applyPrefill() {
  const pf = props.prefillData
  if (!pf) return
  prefilledMediaUrl.value = pf.mediaUrl || ''
  prefilledAssetId.value = pf.assetId || ''
  if (pf.slug) slug.value = pf.slug
  if (pf.title && !description.value) description.value = pf.title
  // The Submit button requires a duration; seed a default so a reinserted
  // pooled file can be submitted without forcing the user to type one.
  if (!duration.value) duration.value = '00:00:00'
}

function handleAbort() {
  const { flashUrgent } = useScreenFlash()
  flashUrgent('ABORT', '#F44336', 500)
  emit('update:show', false)
  emit('abort')
  reset()
}

async function handleSubmit() {
  if (!slug.value || !description.value || !duration.value) {
    return
  }
  await submit()
}

async function submit() {
  const normalizedSlug = slug.value.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-')
  try {
    // Reinserting an existing pooled file: reuse its asset ID + media URL, skip upload.
    if (prefilledMediaUrl.value) {
      emit('submit', {
        description: description.value,
        duration: duration.value,
        timestamp: timestamp.value,
        slug: normalizedSlug,
        assetID: prefilledAssetId.value,
        mediaURL: prefilledMediaUrl.value
      })
      if (toast) toast.success('NAT cue added')
      reset()
      return
    }
    const formData = new FormData()
    formData.append('type', 'nat')
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
      uploadForm.append('type', 'nat')
      uploadForm.append('episode', props.episode)
      uploadForm.append('asset_id', assetID)
      uploadForm.append('file', file.value)
      uploadForm.append('slug', normalizedSlug)
      uploadForm.append('duration', duration.value)
      uploadForm.append('timestamp', timestamp.value || '00:00:00')
      await axios.post('http://192.168.51.210:8888/preproc_nat', uploadForm, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
      })
      mediaURL = `episodes/${props.episode}/assets/audio/${normalizedSlug}.${file.value.name.split('.').pop()}`
    }
    emit('submit', { description: description.value, duration: duration.value, timestamp: timestamp.value, slug: normalizedSlug, assetID, mediaURL })
    if (toast) {
      toast.success('NAT cue added')
    } else {
      console.log('NAT cue added')
    }
    reset()
  } catch (error) {
    if (toast) {
      toast.error('Failed to add NAT cue')
    } else {
      console.error('Failed to add NAT cue')
    }
  }
}

// --- Watch & lifecycle (merged from mixin + component) ---

watch(() => props.show, (newVal) => {
  if (newVal) {
    setupKeyboardHandlers()
    applyPrefill()
    nextTick(() => {
      focusSlugField()
    })
  } else {
    removeKeyboardHandlers()
    reset()
  }
}, { immediate: true })

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
<style scoped>.v-card { padding: 16px; }</style>
