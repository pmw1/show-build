<template>
  <v-container fluid class="pa-6">
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <v-icon size="large" color="primary" class="me-3">mdi-domain</v-icon>
      <div>
        <h1 class="text-h4 font-weight-bold text-primary">
          {{ organization?.name || 'Organization' }}
        </h1>
        <p class="text-subtitle-1 text-medium-emphasis ma-0">
          AssetID: {{ organization?.asset_id }}
        </p>
      </div>
      <v-spacer />
      
      
      <v-btn
        color="success"
        prepend-icon="mdi-content-save"
        :loading="saving"
        :disabled="!hasChanges"
        @click="saveOrganization"
      >
        Save Changes
      </v-btn>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary" size="64" />
      <p class="mt-4 text-body-1">Loading organization...</p>
    </div>

    <!-- Edit Form -->
    <v-form v-else-if="organization" ref="form" v-model="formValid" @submit.prevent="saveOrganization">
      <v-row>
        <!-- Basic Information -->
        <v-col cols="12" md="4">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-information</v-icon>
              Basic Information
            </v-card-title>
            
            <v-text-field
              v-model="form.name"
              label="Display Name"
              hint="Name used for display purposes"
              persistent-hint
              variant="outlined"
              class="mb-3"
              :rules="[v => !!v || 'Display name is required']"
            />

            <v-text-field
              v-model="form.legal_name"
              label="Legal Name"
              hint="Official registered business name"
              persistent-hint
              variant="outlined"
              class="mb-3"
              :rules="[v => !!v || 'Legal name is required']"
            />

            <v-text-field
              v-model="form.trade_name"
              label="Trade Name / DBA"
              hint="Doing business as, trade name, or alias"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-select
              v-model="form.organization_type"
              label="Organization Type"
              :items="organizationTypes"
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.industry"
              label="Industry"
              hint="Primary industry or business sector"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-select
              v-model="form.status"
              label="Status"
              :items="statusOptions"
              variant="outlined"
              class="mb-3"
              :rules="[v => !!v || 'Status is required']"
            />
          </v-card>
        </v-col>

        <!-- Contact Information -->
        <v-col cols="12" md="4">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-card-account-details</v-icon>
              Contact Information
            </v-card-title>
            
            <v-text-field
              v-model="form.address_line1"
              label="Address Line 1"
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.address_line2"
              label="Address Line 2"
              variant="outlined"
              class="mb-3"
            />

            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.city"
                  label="City"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.state_province"
                  label="State/Province"
                  variant="outlined"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.postal_code"
                  label="Postal Code"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="form.country"
                  label="Country"
                  :items="countries"
                  variant="outlined"
                />
              </v-col>
            </v-row>

            <v-text-field
              v-model="form.phone"
              label="Phone"
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.email"
              label="Email"
              type="email"
              variant="outlined"
              class="mb-3"
              :rules="emailRules"
            />

            <v-text-field
              v-model="form.website"
              label="Website"
              type="url"
              hint="Include https://"
              persistent-hint
              variant="outlined"
            />
          </v-card>
        </v-col>

        <!-- Business Details -->
        <v-col cols="12" md="4">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-briefcase</v-icon>
              Business Details
            </v-card-title>
            
            <v-text-field
              v-model="form.registration_number"
              label="Registration Number"
              hint="Business registration or license number"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="form.tax_id"
              label="Tax ID / EIN"
              hint="Tax identification number"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="foundedDateText"
              label="Founded Date"
              type="date"
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model.number="form.number_of_employees"
              label="Number of Employees"
              type="number"
              min="0"
              variant="outlined"
              class="mb-3"
            />

            <v-text-field
              v-model="annualRevenueText"
              label="Annual Revenue"
              type="number"
              min="0"
              step="1000"
              hint="Enter amount in dollars"
              persistent-hint
              variant="outlined"
              prefix="$"
            />
          </v-card>
        </v-col>

        <!-- Notes -->
        <v-col cols="12" md="6">
          <v-card class="pa-4">
            <v-card-title class="text-h6 pb-3">
              <v-icon class="me-2" color="primary">mdi-note-text</v-icon>
              Notes
            </v-card-title>
            
            <v-textarea
              v-model="form.notes"
              label="Internal Notes"
              hint="Internal notes about this organization"
              persistent-hint
              variant="outlined"
              rows="8"
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
      Organization updated successfully!
    </v-snackbar>
  </v-container>
</template>

<script>
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

export default {
  name: 'OrganizationEdit',
  data() {
    return {
      loading: true,
      saving: false,
      error: null,
      formValid: false,
      organization: null,
      originalData: null,
      showSuccessMessage: false,
      allOrganizations: [],
      selectedOrgId: null,
      isAdmin: false,
      form: {
        name: '',
        legal_name: '',
        trade_name: '',
        organization_type: '',
        industry: '',
        sector: '',
        registration_number: '',
        tax_id: '',
        address_line1: '',
        address_line2: '',
        city: '',
        state_province: '',
        postal_code: '',
        country: 'United States',
        phone: '',
        email: '',
        website: '',
        founded_date: null,
        number_of_employees: null,
        annual_revenue: null,
        status: 'active',
        notes: ''
      },
      organizationTypes: [
        'LLC',
        'Corporation',
        'Partnership',
        'Nonprofit',
        'Sole Proprietorship',
        'Other'
      ],
      statusOptions: [
        { title: 'Active', value: 'active' },
        { title: 'Inactive', value: 'inactive' },
        { title: 'Suspended', value: 'suspended' }
      ],
      countries: [
        'United States',
        'Canada',
        'United Kingdom',
        'Other'
      ],
      emailRules: [
        v => !v || /.+@.+\..+/.test(v) || 'E-mail must be valid'
      ]
    }
  },
  computed: {
    hasChanges() {
      if (!this.originalData) return false
      return JSON.stringify(this.form) !== JSON.stringify(this.originalData)
    },
    foundedDateText: {
      get() {
        return this.form.founded_date ? this.form.founded_date.split('T')[0] : ''
      },
      set(value) {
        this.form.founded_date = value || null
      }
    },
    annualRevenueText: {
      get() {
        return this.form.annual_revenue ? this.form.annual_revenue / 100 : ''
      },
      set(value) {
        this.form.annual_revenue = value ? Math.round(parseFloat(value) * 100) : null
      }
    }
  },
  async mounted() {
    // Check if user is admin
    const { currentUser } = useAuth()
    this.isAdmin = currentUser.value?.access_level === 'admin'
    
    await this.loadOrganizations()
  },
  methods: {
    async loadOrganizations() {
      try {
        this.loading = true
        this.error = null
        
        const response = await axios.get('/api/organizations/')
        
        if (response.data && response.data.length > 0) {
          this.allOrganizations = response.data
          
          // Load Polaris Broadcasting by default (look for name containing "Polaris")
          let defaultOrg = response.data.find(org => 
            org.name.toLowerCase().includes('polaris') || 
            org.legal_name?.toLowerCase().includes('polaris')
          )
          
          // Fallback to first organization if Polaris not found
          if (!defaultOrg) {
            defaultOrg = response.data[0]
          }
          
          this.organization = defaultOrg
          this.selectedOrgId = this.organization.id
          this.populateForm()
        } else {
          this.error = 'No organizations found'
        }
      } catch (error) {
        console.error('Failed to load organizations:', error)
        this.error = error.response?.data?.detail || 'Failed to load organizations'
      } finally {
        this.loading = false
      }
    },

    async switchOrganization() {
      if (!this.isAdmin) return
      
      try {
        this.loading = true
        this.error = null
        
        const selectedOrg = this.allOrganizations.find(org => org.id === this.selectedOrgId)
        if (selectedOrg) {
          this.organization = selectedOrg
          this.populateForm()
        }
      } catch (error) {
        console.error('Failed to switch organization:', error)
        this.error = error.response?.data?.detail || 'Failed to switch organization'
      } finally {
        this.loading = false
      }
    },

    populateForm() {
      // Populate form with organization data
      Object.keys(this.form).forEach(key => {
        if (Object.prototype.hasOwnProperty.call(this.organization, key)) {
          this.form[key] = this.organization[key] || this.form[key]
        }
      })
      
      // Store original data for change detection
      this.originalData = { ...this.form }
    },

    async saveOrganization() {
      if (!this.$refs.form.validate()) return
      
      try {
        this.saving = true
        
        // Only send changed fields
        const changes = {}
        Object.keys(this.form).forEach(key => {
          if (this.form[key] !== this.originalData[key]) {
            changes[key] = this.form[key]
          }
        })
        
        if (Object.keys(changes).length === 0) {
          return // No changes to save
        }
        
        const response = await axios.put(
          `/api/organizations/${this.organization.id}`,
          changes
        )
        
        this.organization = response.data
        this.populateForm() // Update form with latest data
        this.showSuccessMessage = true
        
      } catch (error) {
        console.error('Failed to save organization:', error)
        this.$emit('error', error.response?.data?.detail || 'Failed to save organization')
      } finally {
        this.saving = false
      }
    },

    resetForm() {
      this.populateForm()
    }
  }
}
</script>

<style scoped>
.gap-3 {
  gap: 12px;
}

/* Make all text fields 30% smaller and boost text size */
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

/* Reduce spacing between form fields */
:deep(.mb-3) {
  margin-bottom: 4px !important;
}

/* Adjust textarea specifically */
:deep(.v-textarea .v-field) {
  transform: scale(0.7);
}

/* Adjust select fields */
:deep(.v-select .v-field) {
  transform: scale(0.7);
}
</style>