<template>
  <v-dialog v-model="dialog" max-width="600px" persistent>
    <template v-slot:activator="{ props }">
      <v-btn
        color="primary" 
        variant="elevated"
        prepend-icon="mdi-plus-circle"
        v-bind="props"
        :loading="creating"
      >
        Create New Episode
      </v-btn>
    </template>

    <v-card class="modal-container">
      <v-card-title class="d-flex align-center">
        <v-icon class="me-2">mdi-television-play</v-icon>
        <span>Create New Episode</span>
        <v-spacer></v-spacer>
        <v-btn 
          icon="mdi-close" 
          variant="text" 
          @click="closeDialog"
          :disabled="creating"
        ></v-btn>
      </v-card-title>

      <v-card-text>
        <v-form ref="form" v-model="formValid" @submit.prevent="createEpisode">
          <!-- Episode Number -->
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="episodeNumber"
                label="Episode Number"
                hint="Leave blank to auto-generate next number"
                persistent-hint
                :rules="episodeNumberRules"
                :loading="checkingNumber"
                :error="!numberAvailable && episodeNumber !== ''"
                :error-messages="numberAvailable === false ? 'Episode number already exists' : []"
                @input="debounceCheckNumber"
                clearable
              >
                <template v-slot:append-inner>
                  <v-btn
                    v-if="!episodeNumber"
                    icon="mdi-refresh"
                    variant="text"
                    size="small"
                    @click="getNextNumber"
                    :loading="loadingNextNumber"
                    title="Get next available number"
                  ></v-btn>
                </template>
              </v-text-field>
            </v-col>

            <!-- Template Selection -->
            <v-col cols="12" md="6">
              <v-select
                v-model="selectedTemplate"
                :items="templates"
                item-title="name"
                item-value="id"
                label="Episode Template"
                :rules="[v => !!v || 'Template is required']"
                :loading="loadingTemplates"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props" :subtitle="item.raw.description">
                    <template v-slot:prepend>
                      <v-chip 
                        v-if="item.raw.is_default" 
                        size="x-small" 
                        color="primary"
                      >
                        DEFAULT
                      </v-chip>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
          </v-row>

          <!-- Episode Metadata -->
          <v-row>
            <v-col cols="12" md="8">
              <v-text-field
                v-model="episodeTitle"
                label="Episode Title"
                hint="Optional - can be set later"
                persistent-hint
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="episodeDuration"
                label="Duration"
                hint="HH:MM:SS format"
                persistent-hint
                placeholder="01:00:00"
                :rules="durationRules"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="airDate"
                label="Air Date"
                type="date"
                hint="Optional - when episode will air"
                persistent-hint
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-textarea
                v-model="episodeDescription"
                label="Description"
                rows="2"
                hint="Optional - brief description"
                persistent-hint
              ></v-textarea>
            </v-col>
          </v-row>

          <!-- Directory Structure Preview -->
          <v-row v-if="selectedTemplate">
            <v-col cols="12">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel
                  title="Directory Structure Preview"
                  text="Preview of folders and files that will be created"
                >
                  <template v-slot:text>
                    <v-card variant="outlined" class="mt-2">
                      <v-card-text>
                        <div class="text-body-2 font-family-monospace">
                          <div class="d-flex align-center mb-2">
                            <v-icon size="small" class="me-2">mdi-folder</v-icon>
                            <strong>episodes/{{ episodeNumber || 'XXXX' }}/</strong>
                          </div>
                          <div class="ms-4">
                            <div class="d-flex align-center mb-1">
                              <v-icon size="small" class="me-2">mdi-folder</v-icon>
                              assets/
                            </div>
                            <div class="ms-4">
                              <div class="ms-2">
                              <div class="d-flex align-center mb-1">
                                <v-icon size="small" class="me-2">mdi-folder</v-icon>
                                audio/
                              </div>
                              <div class="d-flex align-center mb-1">
                                <v-icon size="small" class="me-2">mdi-folder</v-icon>
                                video/
                              </div>
                              <div class="d-flex align-center mb-1">
                                <v-icon size="small" class="me-2">mdi-folder</v-icon>
                                graphics/
                              </div>
                              <div class="d-flex align-center mb-1">
                                <v-icon size="small" class="me-2">mdi-folder</v-icon>
                                images/
                              </div>
                              <div class="d-flex align-center">
                                <v-icon size="small" class="me-2">mdi-folder</v-icon>
                                quotes/
                              </div>
                            </div>
                            </div>
                            <div class="d-flex align-center mb-1">
                              <v-icon size="small" class="me-2">mdi-folder</v-icon>
                              rundown/
                            </div>
                            <div class="d-flex align-center mb-1">
                              <v-icon size="small" class="me-2">mdi-folder</v-icon>
                              exports/
                            </div>
                            <div class="d-flex align-center mb-1">
                              <v-icon size="small" class="me-2">mdi-folder</v-icon>
                              distribute/
                            </div>
                            <div class="d-flex align-center">
                              <v-icon size="small" class="me-2">mdi-file-document</v-icon>
                              info.md
                            </div>
                          </div>
                        </div>
                      </v-card-text>
                    </v-card>
                  </template>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn 
          variant="text" 
          @click="closeDialog"
          :disabled="creating"
        >
          Cancel
        </v-btn>
        <v-btn 
          color="primary" 
          variant="elevated"
          @click="createEpisode"
          :loading="creating"
          :disabled="!formValid || (episodeNumber && !numberAvailable)"
        >
          Create Episode
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

// Props and emits
const emit = defineEmits(['episode-created'])

// Reactive data
const dialog = ref(false)
const formValid = ref(false)
const creating = ref(false)
const loadingTemplates = ref(false)
const loadingNextNumber = ref(false)
const checkingNumber = ref(false)

// Form data
const episodeNumber = ref('')
const selectedTemplate = ref(null)
const episodeTitle = ref('')
const episodeDescription = ref('')
const episodeDuration = ref('01:00:00')
const airDate = ref('')
const numberAvailable = ref(null)

// Templates data
const templates = ref([])

// Form validation
const episodeNumberRules = [
  (v) => {
    if (!v) return true // Optional field
    if (!/^\d{4}$/.test(v)) return 'Episode number must be 4 digits (e.g., 0001)'
    return true
  }
]

const durationRules = [
  (v) => {
    if (!v) return true // Optional field
    if (!/^\d{2}:\d{2}:\d{2}$/.test(v)) return 'Duration must be in HH:MM:SS format (e.g., 01:30:00)'
    return true
  }
]

// Router for navigation
const router = useRouter()

// Debounced number checking
let checkNumberTimeout = null

const debounceCheckNumber = () => {
  if (checkNumberTimeout) {
    clearTimeout(checkNumberTimeout)
  }
  
  if (!episodeNumber.value) {
    numberAvailable.value = null
    return
  }
  
  checkNumberTimeout = setTimeout(() => {
    checkEpisodeNumber()
  }, 500)
}

// API calls
const loadTemplates = async () => {
  try {
    loadingTemplates.value = true
    const response = await axios.get('/api/episodes/templates')
    templates.value = response.data
    
    // Auto-select default template and set duration
    const defaultTemplate = templates.value.find(t => t.is_default)
    if (defaultTemplate) {
      selectedTemplate.value = defaultTemplate.id
      
      // Set duration from template metadata
      if (defaultTemplate.template_metadata?.duration) {
        episodeDuration.value = defaultTemplate.template_metadata.duration
      }
    }
  } catch (error) {
    console.error('Error loading templates:', error)
  } finally {
    loadingTemplates.value = false
  }
}

const getNextNumber = async () => {
  try {
    loadingNextNumber.value = true
    const response = await axios.get('/api/episodes/next-number')
    episodeNumber.value = response.data.next_episode_number
    numberAvailable.value = true
  } catch (error) {
    console.error('Error getting next episode number:', error)
  } finally {
    loadingNextNumber.value = false
  }
}

const checkEpisodeNumber = async () => {
  if (!episodeNumber.value) {
    numberAvailable.value = null
    return
  }
  
  try {
    checkingNumber.value = true
    const response = await axios.get(`/api/episodes/validate-number/${episodeNumber.value}`)
    numberAvailable.value = response.data.is_available
  } catch (error) {
    console.error('Error checking episode number:', error)
    numberAvailable.value = false
  } finally {
    checkingNumber.value = false
  }
}

const createEpisode = async () => {
  if (!formValid.value || creating.value) return
  
  try {
    creating.value = true
    
    const payload = {
      episode_number: episodeNumber.value || undefined,
      template_id: selectedTemplate.value,
      title: episodeTitle.value || undefined,
      description: episodeDescription.value || undefined,
      episode_metadata: {
        duration: episodeDuration.value,
        air_date: airDate.value || undefined
      }
    }
    
    const response = await axios.post('/api/episodes/create', payload)
    const createdEpisode = response.data
    
    // Emit success event
    emit('episode-created', createdEpisode)
    
    // Show success message
    console.log(`Episode ${createdEpisode.episode_number} created successfully!`)
    
    // Navigate to the new episode
    router.push(`/episodes/${createdEpisode.episode_number}`)
    
    // Close dialog
    closeDialog()
    
  } catch (error) {
    console.error('Error creating episode:', error)
    
    // Show error message
    const errorMessage = error.response?.data?.detail || 'Failed to create episode'
    alert(`Error: ${errorMessage}`)
    
  } finally {
    creating.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  // Reset form
  episodeNumber.value = ''
  selectedTemplate.value = null
  episodeTitle.value = ''
  episodeDescription.value = ''
  episodeDuration.value = '01:00:00'
  airDate.value = ''
  numberAvailable.value = null
}

// Watch for template change to update duration
watch(selectedTemplate, (newTemplateId) => {
  if (newTemplateId) {
    const template = templates.value.find(t => t.id === newTemplateId)
    if (template?.template_metadata?.duration) {
      episodeDuration.value = template.template_metadata.duration
    }
  }
})

// Watch for dialog open to load data
watch(dialog, async (isOpen) => {
  if (isOpen) {
    loadTemplates()
    await getNextNumber()
  }
})

// Load templates on mount
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.font-family-monospace {
  font-family: 'Roboto Mono', monospace;
}

.modal-container {
  border: 1px solid #9E9E9E !important;
  border-radius: 8px !important;
}

:deep(.v-text-field .v-field__input) {
  padding-left: 16px !important;
  padding-top: 14px !important;
  padding-bottom: 14px !important;
  min-height: 40px !important;
}

:deep(.v-text-field .v-field--variant-outlined .v-field__input) {
  padding-left: 16px !important;
}

:deep(.v-text-field[type="date"] .v-field__input) {
  padding-left: 16px !important;
  padding-top: 14px !important;
  padding-bottom: 14px !important;
}

/* Fix select field label positioning */
:deep(.v-select .v-field__input) {
  padding-left: 16px !important;
  padding-top: 14px !important;
  padding-bottom: 14px !important;
  min-height: 40px !important;
}

/* Fix floating label for select fields */
:deep(.v-select .v-field-label) {
  transform: none !important;
  position: absolute !important;
  top: -8px !important;
  left: 12px !important;
  font-size: 12px !important;
  background: white !important;
  padding: 0 4px !important;
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity)) !important;
}

/* Fix floating label for date fields */
:deep(.v-text-field[type="date"] .v-field-label) {
  transform: none !important;
  position: absolute !important;
  top: -8px !important;
  left: 12px !important;
  font-size: 12px !important;
  background: white !important;
  padding: 0 4px !important;
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity)) !important;
}

/* Ensure labels stay positioned when field has value */
:deep(.v-select.v-field--active .v-field-label),
:deep(.v-text-field[type="date"].v-field--active .v-field-label) {
  transform: none !important;
  top: -8px !important;
  font-size: 12px !important;
}
</style>