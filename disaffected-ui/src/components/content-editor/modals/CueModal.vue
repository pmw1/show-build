<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600">
    <v-card>
      <v-card-title>Add {{ cueType.toUpperCase() }} ({{ cueTypeLabel }})</v-card-title>
      <v-card-text>
        <v-form ref="cueForm" v-model="formValid">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                ref="slugFieldRef"
                v-model="slug"
                label="Slug"
                variant="outlined"
                density="comfortable"
                :rules="slugRules"
                required
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-text-field
                v-model="duration"
                label="Duration"
                variant="outlined"
                density="comfortable"
                placeholder="MM:SS"
                :rules="durationRules"
              ></v-text-field>
            </v-col>
            
            <v-col cols="12">
              <v-textarea
                v-model="description"
                label="Description"
                variant="outlined"
                density="comfortable"
                rows="3"
                auto-grow
                required
                :rules="descriptionRules"
              ></v-textarea>
            </v-col>
            
            <!-- Type-specific fields -->
            <template v-if="cueType === 'sot'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="sourceFile"
                  label="Source File"
                  variant="outlined"
                  density="comfortable"
                  hint="Path to video/audio file"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="timecode"
                  label="Timecode"
                  variant="outlined"
                  density="comfortable"
                  placeholder="HH:MM:SS:FF"
                  hint="Start timecode"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </template>
            
            <template v-if="cueType === 'vo'">
              <v-col cols="12">
                <v-textarea
                  v-model="voScript"
                  label="Voice Over Script"
                  variant="outlined"
                  density="comfortable"
                  rows="4"
                  auto-grow
                  hint="Script to be read by talent"
                  persistent-hint
                ></v-textarea>
              </v-col>
            </template>
            
            <template v-if="cueType === 'fsq'">
              <v-col cols="12">
                <v-textarea
                  v-model="quoteText"
                  label="Quote Text"
                  variant="outlined"
                  density="comfortable"
                  rows="3"
                  auto-grow
                  hint="Text to display full screen"
                  persistent-hint
                  required
                  :rules="quoteRules"
                ></v-textarea>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="attribution"
                  label="Attribution"
                  variant="outlined"
                  density="comfortable"
                  hint="Source or author"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="fontStyle"
                  :items="fontStyles"
                  label="Font Style"
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
            </template>
            
            <template v-if="cueType === 'nat'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="location"
                  label="Location"
                  variant="outlined"
                  density="comfortable"
                  hint="Where the sound was recorded"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="ambientType"
                  :items="ambientTypes"
                  label="Ambient Type"
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
            </template>
            
            <template v-if="cueType === 'pkg'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="reporter"
                  label="Reporter"
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="pkgDuration"
                  label="Package Duration"
                  variant="outlined"
                  density="comfortable"
                  placeholder="MM:SS"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="packageNotes"
                  label="Package Notes"
                  variant="outlined"
                  density="comfortable"
                  rows="2"
                  auto-grow
                  hint="Additional production notes"
                  persistent-hint
                ></v-textarea>
              </v-col>
            </template>

            <template v-if="cueType === 'dir'">
              <v-col cols="12">
                <v-textarea
                  v-model="noteText"
                  label="Director Note"
                  variant="outlined"
                  density="comfortable"
                  rows="4"
                  auto-grow
                  hint="Special note or instruction for the director"
                  persistent-hint
                  required
                  :rules="noteRules"
                ></v-textarea>
              </v-col>
            </template>
          </v-row>
        </v-form>
        
        <!-- Preview -->
        <v-divider class="my-4"></v-divider>
        <v-row>
          <v-col cols="12">
            <h4 class="text-subtitle-1 mb-2">Preview</h4>
            <v-card outlined class="pa-3">
              <div class="cue-preview">
                <v-chip 
                  :color="cueColor" 
                  size="small" 
                  class="mb-2"
                >
                  {{ cueType.toUpperCase() }}
                </v-chip>
                <h5 class="text-subtitle-1">{{ slug || 'Unnamed Cue' }}</h5>
                <p class="text-body-2 mb-2">{{ description || 'No description' }}</p>
                <small class="text-caption text-medium-emphasis">Duration: {{ duration || 'Not specified' }}</small>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn 
          color="primary" 
          @click="submit"
          :disabled="!formValid"
        >
          Insert
        </v-btn>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { registerModalEsc } from '@/composables/useModalStack'
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  cueType: {
    type: String,
    required: true,
    validator: (value) => ['fsq', 'sot', 'vo', 'nat', 'pkg', 'dir'].includes(value)
  }
})

const emit = defineEmits(['update:show', 'submit'])

// Site-wide ESC-closes-modal behavior (registered via the global modal stack).
registerModalEsc(() => props.show, () => emit('update:show', false), 'CueModal')
const slugFieldRef = ref(null)
useDoubleEnterToSlug(() => props.show, slugFieldRef)

const formValid = ref(false)
const slug = ref('')
const duration = ref('')
const description = ref('')
// SOT specific
const sourceFile = ref('')
const timecode = ref('')
// VO specific
const voScript = ref('')
// FSQ specific
const quoteText = ref('')
const attribution = ref('')
const fontStyle = ref('normal')
// NAT specific
const location = ref('')
const ambientType = ref('outdoor')
// PKG specific
const reporter = ref('')
const pkgDuration = ref('')
const packageNotes = ref('')
// DIR specific
const noteText = ref('')

// Validation rules
const slugRules = [
  v => !!v || 'Slug is required',
  v => (v && v.length >= 2) || 'Slug must be at least 2 characters'
]
const descriptionRules = [
  v => !!v || 'Description is required',
  v => (v && v.length >= 5) || 'Description must be at least 5 characters'
]
const durationRules = [
  v => !v || /^\d{1,2}:\d{2}$/.test(v) || 'Duration must be in MM:SS format'
]
const quoteRules = [
  v => !!v || 'Quote text is required'
]
const noteRules = [
  v => !!v || 'Director note is required'
]

// Select options
const fontStyles = [
  'normal',
  'bold',
  'italic',
  'large',
  'small'
]
const ambientTypes = [
  'outdoor',
  'indoor',
  'crowd',
  'traffic',
  'nature',
  'office',
  'restaurant',
  'street',
  'other'
]

const cueTypeLabel = computed(() => {
  const labels = {
    fsq: 'Full Screen Quote',
    sot: 'Sound on Tape',
    vo: 'Voice Over',
    nat: 'Natural Sound',
    pkg: 'Package',
    dir: 'Director Note'
  }
  return labels[props.cueType] || props.cueType
})

const cueColor = computed(() => {
  const colors = {
    fsq: 'green-darken-3',
    sot: 'purple-darken-3',
    vo: 'deep-orange-darken-3',
    nat: 'teal-darken-3',
    pkg: 'red-darken-3',
    dir: 'amber-darken-3'
  }
  return colors[props.cueType] || 'grey'
})

function reset() {
  slug.value = ''
  duration.value = ''
  description.value = ''
  sourceFile.value = ''
  timecode.value = ''
  voScript.value = ''
  quoteText.value = ''
  attribution.value = ''
  fontStyle.value = 'normal'
  location.value = ''
  ambientType.value = 'outdoor'
  reporter.value = ''
  pkgDuration.value = ''
  packageNotes.value = ''
  noteText.value = ''
  formValid.value = false
}

function submit() {
  const baseData = {
    type: props.cueType,
    slug: slug.value,
    duration: duration.value,
    description: description.value
  }

  // Add type-specific data
  const typeSpecificData = {}

  if (props.cueType === 'sot') {
    typeSpecificData.sourceFile = sourceFile.value
    typeSpecificData.timecode = timecode.value
  } else if (props.cueType === 'vo') {
    typeSpecificData.script = voScript.value
  } else if (props.cueType === 'fsq') {
    typeSpecificData.quoteText = quoteText.value
    typeSpecificData.attribution = attribution.value
    typeSpecificData.fontStyle = fontStyle.value
  } else if (props.cueType === 'nat') {
    typeSpecificData.location = location.value
    typeSpecificData.ambientType = ambientType.value
  } else if (props.cueType === 'pkg') {
    typeSpecificData.reporter = reporter.value
    typeSpecificData.pkgDuration = pkgDuration.value
    typeSpecificData.notes = packageNotes.value
  } else if (props.cueType === 'dir') {
    typeSpecificData.noteText = noteText.value
  }

  emit('submit', { ...baseData, ...typeSpecificData })
  reset()
}

function cancel() {
  emit('update:show', false)
  reset()
}

watch(() => props.show, (newVal) => {
  if (!newVal) {
    reset()
  }
})
</script>

<style scoped>
.cue-preview {
  min-height: 80px;
}
</style>
