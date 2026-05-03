<template>
  <v-container fluid class="pa-6">
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <v-icon size="large" color="primary" class="me-3">mdi-television-play</v-icon>
      <div>
        <h1 class="text-h4 font-weight-bold text-primary">
          {{ show?.name || 'Show' }}
        </h1>
        <p class="text-subtitle-1 text-medium-emphasis ma-0">
          AssetID: {{ show?.asset_id }} | Organization: {{ show?.organization_name }}
        </p>
      </div>
      <v-spacer />
      
      <!-- Admin Show Selector -->
      <div v-if="isAdmin && allShows.length > 1" class="me-4">
        <v-select
          v-model="selectedShowId"
          :items="allShows"
          item-title="name"
          item-value="id"
          label="Switch Show"
          variant="outlined"
          density="compact"
          style="min-width: 250px;"
          @update:model-value="switchShow"
        />
      </div>

      <!-- New Show Button -->
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        variant="outlined"
        class="me-3"
        @click="showNewShowDialog = true"
      >
        New Show
      </v-btn>
      
      <v-btn
        color="success"
        prepend-icon="mdi-content-save"
        :loading="saving"
        :disabled="!hasChanges || !show"
        @click="saveShow"
      >
        Save Changes
      </v-btn>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary" size="64" />
      <p class="mt-4 text-body-1">Loading show...</p>
    </div>

    <!-- Edit Form -->
    <v-form v-else-if="show" ref="showFormRef" v-model="formValid" @submit.prevent="saveShow">
      <v-row>
        <!-- Basic Information -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-information</v-icon>
              Basic Information
            </v-card-title>
            
            <v-text-field
              v-model="form.name"
              label="Show Name"
              hint="Display name for the show"
              persistent-hint
              variant="outlined"
              class="mb-3"
              :rules="[v => !!v || 'Show name is required']"
            />

            <v-textarea
              v-model="form.description"
              label="Description"
              hint="Brief description of the show"
              persistent-hint
              variant="outlined"
              rows="3"
              class="mb-3"
            />

            <v-select
              v-model="form.format"
              label="Format"
              :items="formatOptions"
              hint="Type of show format"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-select
              v-model="form.category"
              label="Category"
              :items="categoryOptions"
              hint="Show category or genre"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />
          </v-card>
        </v-col>

        <!-- Media & People -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-account-group</v-icon>
              Media & People
            </v-card-title>
            
            <v-text-field
              v-model="form.host"
              label="Host"
              hint="Main host or presenter"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.logo"
              label="Logo URL"
              hint="URL to show logo image"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.poster"
              label="Poster URL"
              hint="URL to 1000x1000 show poster image"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.trailer"
              label="Trailer URL"
              hint="URL to show trailer video"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.schedule"
              label="Schedule"
              hint="When the show airs (e.g., 'Mon-Fri 8:00 AM')"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.website"
              label="Website URL"
              hint="Official show website URL"
              persistent-hint
              variant="outlined"
              type="url"
              class="mb-3"
            />
          </v-card>
        </v-col>

        <!-- Contact Information -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-card-account-phone</v-icon>
              Contact Information
            </v-card-title>
            
            <v-text-field
              v-model="form.contact_name"
              label="Contact Name"
              hint="Primary contact person for the show"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.contact_phone"
              label="Contact Phone"
              hint="Phone number for show contact"
              persistent-hint
              variant="outlined"
              type="tel"
              class="mb-3"
            />

            <v-text-field
              v-model="form.contact_email"
              label="Contact Email"
              hint="Email address for show contact"
              persistent-hint
              variant="outlined"
              type="email"
              class="mb-3"
            />
          </v-card>
        </v-col>

        <!-- Social Links -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-share-variant</v-icon>
              Social Links
            </v-card-title>
            
            <v-textarea
              v-model="socialLinksJson"
              label="Social Links (JSON)"
              hint="Social media URLs and handles"
              persistent-hint
              variant="outlined"
              rows="6"
              placeholder='{"twitter": "https://twitter.com/show", "instagram": "@showname", "facebook": "https://facebook.com/show"}'
            />
          </v-card>
        </v-col>

        <!-- API Keys -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-key-variant</v-icon>
              API Keys
            </v-card-title>
            
            <v-textarea
              v-model="apiKeysJson"
              label="API Keys (JSON)"
              hint="External API credentials and tokens"
              persistent-hint
              variant="outlined"
              rows="6"
              placeholder='{"spotify": "token123", "youtube": "key456"}'
            />
          </v-card>
        </v-col>

        <!-- Settings -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-cog</v-icon>
              Show Settings
            </v-card-title>
            
            <v-textarea
              v-model="settingsJson"
              label="Settings (JSON)"
              hint="Show-specific configuration settings"
              persistent-hint
              variant="outlined"
              rows="6"
              placeholder='{"theme": "dark", "default_length": "60min"}'
            />
          </v-card>
        </v-col>
      </v-row>

      <!-- Action Buttons -->
      <div class="d-flex justify-end mt-6 gap-3">
        <v-btn
          color="grey"
          variant="outlined"
          @click="resetForm"
          :disabled="saving"
        >
          Reset
        </v-btn>
        <v-btn
          color="success"
          prepend-icon="mdi-content-save"
          :loading="saving"
          :disabled="!hasChanges"
          type="submit"
        >
          Save Changes
        </v-btn>
      </div>
    </v-form>

    <!-- Error State -->
    <v-alert v-else-if="error" type="error" class="mt-4">
      {{ error }}
    </v-alert>

    <!-- Success Snackbar -->
    <v-snackbar
      v-model="showSuccessMessage"
      color="success"
      timeout="3000"
    >
      Show updated successfully!
    </v-snackbar>

    <!-- New Show Dialog -->
    <v-dialog v-model="showNewShowDialog" max-width="500px">
      <v-card>
        <v-card-title>
          <span class="text-h5">Create New Show</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="newShowForm" v-model="newShowValid">
            <v-text-field
              v-model="newShowName"
              label="Show Name"
              :rules="[v => !!v || 'Show name is required']"
              variant="outlined"
              class="mb-3"
            />
            <v-textarea
              v-model="newShowDescription"
              label="Description (Optional)"
              variant="outlined"
              rows="3"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeNewShowDialog">
            Cancel
          </v-btn>
          <v-btn 
            color="primary" 
            variant="flat"
            :loading="creating"
            :disabled="!newShowValid"
            @click="createNewShow"
          >
            Create Show
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

const emit = defineEmits(['error'])

// Template refs
const showFormRef = ref(null)
const newShowForm = ref(null)

// Reactive state
const loading = ref(true)
const saving = ref(false)
const creating = ref(false)
const error = ref(null)
const formValid = ref(false)
const show = ref(null)
const originalData = ref(null)
const showSuccessMessage = ref(false)
const allShows = ref([])
const selectedShowId = ref(null)
const isAdmin = ref(false)
const showNewShowDialog = ref(false)
const newShowValid = ref(false)
const newShowName = ref('')
const newShowDescription = ref('')

const form = reactive({
  name: '',
  description: '',
  format: '',
  logo: '',
  poster: '',
  host: '',
  schedule: '',
  category: '',
  trailer: '',
  website: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  social_links: {},
  api_keys: {},
  settings: {}
})

const formatOptions = [
  'Talk Show',
  'News',
  'Music',
  'Podcast',
  'Interview',
  'Documentary',
  'Live',
  'Other'
]

const categoryOptions = [
  'Entertainment',
  'News & Politics',
  'Sports',
  'Music',
  'Technology',
  'Business',
  'Comedy',
  'Education',
  'Health',
  'Other'
]

// Computed
const hasChanges = computed(() => {
  if (!originalData.value) return false
  return JSON.stringify(form) !== JSON.stringify(originalData.value)
})

const settingsJson = computed({
  get() {
    return JSON.stringify(form.settings || {}, null, 2)
  },
  set(value) {
    try {
      form.settings = value ? JSON.parse(value) : {}
    } catch (e) {
      // Keep the text as is if it's invalid JSON
    }
  }
})

const apiKeysJson = computed({
  get() {
    return JSON.stringify(form.api_keys || {}, null, 2)
  },
  set(value) {
    try {
      form.api_keys = value ? JSON.parse(value) : {}
    } catch (e) {
      // Keep the text as is if it's invalid JSON
    }
  }
})

const socialLinksJson = computed({
  get() {
    return JSON.stringify(form.social_links || {}, null, 2)
  },
  set(value) {
    try {
      form.social_links = value ? JSON.parse(value) : {}
    } catch (e) {
      // Keep the text as is if it's invalid JSON
    }
  }
})

// Methods
async function loadShows() {
  try {
    loading.value = true
    error.value = null

    const response = await axios.get('/api/shows/')

    if (response.data && response.data.length > 0) {
      allShows.value = response.data

      // Load the first show (user's own for regular users, first available for admins)
      show.value = response.data[0]
      selectedShowId.value = show.value.id
      populateForm()
    } else {
      error.value = 'No shows found'
    }
  } catch (err) {
    console.error('Failed to load shows:', err)
    error.value = err.response?.data?.detail || 'Failed to load shows'
  } finally {
    loading.value = false
  }
}

async function switchShow() {
  if (!isAdmin.value) return

  try {
    loading.value = true
    error.value = null

    const selectedShow = allShows.value.find(s => s.id === selectedShowId.value)
    if (selectedShow) {
      show.value = selectedShow
      populateForm()
    }
  } catch (err) {
    console.error('Failed to switch show:', err)
    error.value = err.response?.data?.detail || 'Failed to switch show'
  } finally {
    loading.value = false
  }
}

function populateForm() {
  // Populate form with show data
  form.name = show.value.name || ''
  form.description = show.value.description || ''
  form.format = show.value.format || ''
  form.logo = show.value.logo || ''
  form.poster = show.value.poster || ''
  form.host = show.value.host || ''
  form.schedule = show.value.schedule || ''
  form.category = show.value.category || ''
  form.trailer = show.value.trailer || ''
  form.website = show.value.website || ''
  form.contact_name = show.value.contact_name || ''
  form.contact_phone = show.value.contact_phone || ''
  form.contact_email = show.value.contact_email || ''
  form.social_links = show.value.social_links || {}
  form.api_keys = show.value.api_keys || {}
  form.settings = show.value.settings || {}

  // Store original data for change detection
  originalData.value = { ...form }
}

async function saveShow() {
  if (!showFormRef.value.validate()) return

  try {
    saving.value = true

    // Only send changed fields
    const changes = {}
    Object.keys(form).forEach(key => {
      if (JSON.stringify(form[key]) !== JSON.stringify(originalData.value[key])) {
        changes[key] = form[key]
      }
    })

    if (Object.keys(changes).length === 0) {
      return // No changes to save
    }

    const response = await axios.put(
      `/api/shows/${show.value.id}`,
      changes
    )

    show.value = response.data
    populateForm() // Update form with latest data
    showSuccessMessage.value = true

  } catch (err) {
    console.error('Failed to save show:', err)
    emit('error', err.response?.data?.detail || 'Failed to save show')
  } finally {
    saving.value = false
  }
}

function resetForm() {
  populateForm()
}

async function createNewShow() {
  if (!newShowForm.value.validate()) return

  try {
    creating.value = true

    const newShowData = {
      name: newShowName.value,
      description: newShowDescription.value || ''
    }

    const response = await axios.post('/api/shows/', newShowData)

    // Add the new show to the list
    allShows.value.push(response.data)

    // Switch to the new show
    show.value = response.data
    selectedShowId.value = response.data.id
    populateForm()

    // Close the dialog and reset form
    closeNewShowDialog()

    // Show success message
    showSuccessMessage.value = true

  } catch (err) {
    console.error('Failed to create show:', err)
    error.value = err.response?.data?.detail || 'Failed to create show'
  } finally {
    creating.value = false
  }
}

function closeNewShowDialog() {
  showNewShowDialog.value = false
  newShowName.value = ''
  newShowDescription.value = ''
  newShowValid.value = false
  if (newShowForm.value) {
    newShowForm.value.resetValidation()
  }
}

// Lifecycle
onMounted(async () => {
  // Check if user is admin
  const { currentUser } = useAuth()
  isAdmin.value = currentUser.value?.access_level === 'admin'

  await loadShows()
})
</script>

<style scoped>
.gap-3 {
  gap: 12px;
}

/* Apply same compact styling as OrganizationEdit */
:deep(.v-field) {
  transform: scale(0.7);
  transform-origin: top left;
  margin-bottom: -30px;
  margin-right: -30%;
  width: 100% !important;
}

:deep(.v-field__input) {
  font-size: 1.32em;
  padding: 1px 2px 1px 0.3em !important;
}

:deep(.v-label) {
  font-size: 0.9em;
}

:deep(.v-field__field) {
  padding-top: 1px !important;
  padding-bottom: 1px !important;
}

:deep(.v-field__overlay) {
  padding: 0 !important;
}

:deep(.v-messages) {
  font-size: 0.7em;
  margin-top: -12px;
}

:deep(.mb-3) {
  margin-bottom: 4px !important;
}

:deep(.v-textarea .v-field) {
  transform: scale(0.7);
}

:deep(.v-select .v-field) {
  transform: scale(0.7);
}

/* Fix for New Show dialog - prevent text fade to white and scaling issues */
:deep(.v-dialog .v-textarea .v-field),
:deep(.v-dialog .v-text-field .v-field) {
  transform: none !important;
  transform-origin: top left !important;
  margin-bottom: 16px !important;
  margin-right: 0 !important;
  width: 100% !important;
  height: auto !important;
}

:deep(.v-dialog .v-field__input) {
  font-size: 1em !important;
  padding: 12px !important;
  color: rgba(var(--v-theme-on-surface), var(--v-high-emphasis-opacity)) !important;
  opacity: 1 !important;
  -webkit-text-fill-color: currentColor !important;
}

:deep(.v-dialog .v-field__field) {
  opacity: 1 !important;
  background: transparent !important;
  padding-top: 16px !important;
}

:deep(.v-dialog .v-field__overlay) {
  opacity: 1 !important;
  background: none !important;
}

:deep(.v-dialog .v-messages) {
  font-size: 0.875em !important;
  margin-top: 4px !important;
}

/* Ensure textarea content is fully visible - more specific rules */
:deep(.v-dialog .v-textarea textarea) {
  opacity: 1 !important;
  color: inherit !important;
  -webkit-text-fill-color: currentColor !important;
  margin-top: 0 !important;
  padding-top: 8px !important;
}

/* Remove any gradient masks */
:deep(.v-dialog .v-field::before),
:deep(.v-dialog .v-field::after) {
  display: none !important;
}
</style>