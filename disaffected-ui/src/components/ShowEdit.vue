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
    <v-form v-else-if="show" ref="form" v-model="formValid" @submit.prevent="saveShow">
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

<script>
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

export default {
  name: 'ShowEdit',
  data() {
    return {
      loading: true,
      saving: false,
      creating: false,
      error: null,
      formValid: false,
      show: null,
      originalData: null,
      showSuccessMessage: false,
      allShows: [],
      selectedShowId: null,
      isAdmin: false,
      showNewShowDialog: false,
      newShowValid: false,
      newShowName: '',
      newShowDescription: '',
      form: {
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
      },
      formatOptions: [
        'Talk Show',
        'News',
        'Music',
        'Podcast',
        'Interview',
        'Documentary',
        'Live',
        'Other'
      ],
      categoryOptions: [
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
    }
  },
  computed: {
    hasChanges() {
      if (!this.originalData) return false
      return JSON.stringify(this.form) !== JSON.stringify(this.originalData)
    },
    settingsJson: {
      get() {
        return JSON.stringify(this.form.settings || {}, null, 2)
      },
      set(value) {
        try {
          this.form.settings = value ? JSON.parse(value) : {}
        } catch (e) {
          // Keep the text as is if it's invalid JSON
        }
      }
    },
    apiKeysJson: {
      get() {
        return JSON.stringify(this.form.api_keys || {}, null, 2)
      },
      set(value) {
        try {
          this.form.api_keys = value ? JSON.parse(value) : {}
        } catch (e) {
          // Keep the text as is if it's invalid JSON
        }
      }
    },
    socialLinksJson: {
      get() {
        return JSON.stringify(this.form.social_links || {}, null, 2)
      },
      set(value) {
        try {
          this.form.social_links = value ? JSON.parse(value) : {}
        } catch (e) {
          // Keep the text as is if it's invalid JSON
        }
      }
    }
  },
  async mounted() {
    // Check if user is admin
    const { currentUser } = useAuth()
    this.isAdmin = currentUser.value?.access_level === 'admin'
    
    await this.loadShows()
  },
  methods: {
    async loadShows() {
      try {
        this.loading = true
        this.error = null
        
        const response = await axios.get('/api/shows/')
        
        if (response.data && response.data.length > 0) {
          this.allShows = response.data
          
          // Load the first show (user's own for regular users, first available for admins)
          this.show = response.data[0]
          this.selectedShowId = this.show.id
          this.populateForm()
        } else {
          this.error = 'No shows found'
        }
      } catch (error) {
        console.error('Failed to load shows:', error)
        this.error = error.response?.data?.detail || 'Failed to load shows'
      } finally {
        this.loading = false
      }
    },

    async switchShow() {
      if (!this.isAdmin) return
      
      try {
        this.loading = true
        this.error = null
        
        const selectedShow = this.allShows.find(show => show.id === this.selectedShowId)
        if (selectedShow) {
          this.show = selectedShow
          this.populateForm()
        }
      } catch (error) {
        console.error('Failed to switch show:', error)
        this.error = error.response?.data?.detail || 'Failed to switch show'
      } finally {
        this.loading = false
      }
    },

    populateForm() {
      // Populate form with show data
      this.form.name = this.show.name || ''
      this.form.description = this.show.description || ''
      this.form.format = this.show.format || ''
      this.form.logo = this.show.logo || ''
      this.form.poster = this.show.poster || ''
      this.form.host = this.show.host || ''
      this.form.schedule = this.show.schedule || ''
      this.form.category = this.show.category || ''
      this.form.trailer = this.show.trailer || ''
      this.form.website = this.show.website || ''
      this.form.contact_name = this.show.contact_name || ''
      this.form.contact_phone = this.show.contact_phone || ''
      this.form.contact_email = this.show.contact_email || ''
      this.form.social_links = this.show.social_links || {}
      this.form.api_keys = this.show.api_keys || {}
      this.form.settings = this.show.settings || {}
      
      // Store original data for change detection
      this.originalData = { ...this.form }
    },

    async saveShow() {
      if (!this.$refs.form.validate()) return
      
      try {
        this.saving = true
        
        // Only send changed fields
        const changes = {}
        Object.keys(this.form).forEach(key => {
          if (JSON.stringify(this.form[key]) !== JSON.stringify(this.originalData[key])) {
            changes[key] = this.form[key]
          }
        })
        
        if (Object.keys(changes).length === 0) {
          return // No changes to save
        }
        
        const response = await axios.put(
          `/api/shows/${this.show.id}`,
          changes
        )
        
        this.show = response.data
        this.populateForm() // Update form with latest data
        this.showSuccessMessage = true
        
      } catch (error) {
        console.error('Failed to save show:', error)
        this.$emit('error', error.response?.data?.detail || 'Failed to save show')
      } finally {
        this.saving = false
      }
    },

    resetForm() {
      this.populateForm()
    },

    async createNewShow() {
      if (!this.$refs.newShowForm.validate()) return
      
      try {
        this.creating = true
        
        const newShowData = {
          name: this.newShowName,
          description: this.newShowDescription || ''
        }
        
        const response = await axios.post('/api/shows/', newShowData)
        
        // Add the new show to the list
        this.allShows.push(response.data)
        
        // Switch to the new show
        this.show = response.data
        this.selectedShowId = response.data.id
        this.populateForm()
        
        // Close the dialog and reset form
        this.closeNewShowDialog()
        
        // Show success message
        this.showSuccessMessage = true
        
      } catch (error) {
        console.error('Failed to create show:', error)
        this.error = error.response?.data?.detail || 'Failed to create show'
      } finally {
        this.creating = false
      }
    },

    closeNewShowDialog() {
      this.showNewShowDialog = false
      this.newShowName = ''
      this.newShowDescription = ''
      this.newShowValid = false
      if (this.$refs.newShowForm) {
        this.$refs.newShowForm.resetValidation()
      }
    }
  }
}
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