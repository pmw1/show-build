<template>
  <div class="customer-manager">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-domain</v-icon>
        Customer / Sponsor Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openCreateDialog">
          <v-icon class="mr-2">mdi-plus</v-icon>
          Add Customer
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Filters -->
        <v-row class="mb-4">
          <v-col cols="4">
            <v-text-field
              v-model="searchQuery"
              label="Search"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-text-field>
          </v-col>
          <v-col cols="4">
            <v-select
              v-model="filterType"
              label="Type"
              :items="typeOptions"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-select>
          </v-col>
          <v-col cols="4">
            <v-select
              v-model="filterStatus"
              label="Status"
              :items="statusOptions"
              variant="outlined"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
        </v-row>

        <!-- Customers Table -->
        <v-data-table
          :headers="headers"
          :items="filteredCustomers"
          :loading="loading"
          class="elevation-1"
          density="compact"
          @click:row="(e, { item }) => editCustomer(item)"
        >
          <template #[`item.customer_type`]="{ item }">
            <v-chip :color="getTypeColor(item.customer_type)" size="small" label>
              {{ formatType(item.customer_type) }}
            </v-chip>
          </template>

          <template #[`item.tier`]="{ item }">
            <v-chip :color="getTierColor(item.tier)" size="x-small" variant="outlined">
              {{ item.tier }}
            </v-chip>
          </template>

          <template #[`item.is_active`]="{ item }">
            <v-icon :color="item.is_active ? 'success' : 'grey'" size="small">
              {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
            </v-icon>
          </template>

          <template #[`item.actions`]="{ item }">
            <v-btn icon size="small" @click.stop="editCustomer(item)">
              <v-icon size="small">mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon size="small" @click.stop="toggleActive(item)">
              <v-icon size="small" :color="item.is_active ? 'grey' : 'success'">
                {{ item.is_active ? 'mdi-eye-off' : 'mdi-eye' }}
              </v-icon>
            </v-btn>
            <v-btn icon size="small" color="error" @click.stop="confirmDelete(item)">
              <v-icon size="small">mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialogOpen" max-width="600" persistent>
      <v-card>
        <v-card-title>
          {{ editingCustomer ? 'Edit Customer' : 'Add Customer' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="formRef">
            <v-text-field
              v-model="formData.company_name"
              label="Company Name *"
              variant="outlined"
              density="compact"
              :rules="[v => !!v || 'Company name is required']"
            ></v-text-field>

            <v-text-field
              v-model="formData.display_name"
              label="Display Name (optional)"
              variant="outlined"
              density="compact"
              hint="Short name for dropdown display"
              persistent-hint
            ></v-text-field>

            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="formData.customer_type"
                  label="Type"
                  :items="typeOptions"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="formData.tier"
                  label="Tier"
                  :items="tierOptions"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
            </v-row>

            <v-text-field
              v-model="formData.industry"
              label="Industry"
              variant="outlined"
              density="compact"
            ></v-text-field>

            <v-divider class="my-3"></v-divider>
            <div class="text-subtitle-2 mb-2">Primary Contact</div>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.contact_name"
                  label="Contact Name"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.contact_title"
                  label="Title"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.contact_email"
                  label="Email"
                  variant="outlined"
                  density="compact"
                  type="email"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.contact_phone"
                  label="Phone"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-divider class="my-3"></v-divider>
            <div class="text-subtitle-2 mb-2">Billing</div>

            <v-text-field
              v-model="formData.billing_email"
              label="Billing Email"
              variant="outlined"
              density="compact"
              type="email"
            ></v-text-field>

            <v-textarea
              v-model="formData.billing_address"
              label="Billing Address"
              variant="outlined"
              density="compact"
              rows="2"
            ></v-textarea>

            <v-textarea
              v-model="formData.notes"
              label="Notes"
              variant="outlined"
              density="compact"
              rows="2"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="dialogOpen = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveCustomer">
            {{ editingCustomer ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialogOpen" max-width="400">
      <v-card>
        <v-card-title>Delete Customer?</v-card-title>
        <v-card-text>
          Are you sure you want to permanently delete <strong>{{ deletingCustomer?.company_name }}</strong>?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialogOpen = false">Cancel</v-btn>
          <v-btn color="error" :loading="deleting" @click="deleteCustomer">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error/Success Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="bottom"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'CustomerManager',
  setup() {
    // State
    const loading = ref(false)
    const saving = ref(false)
    const deleting = ref(false)
    const customers = ref([])
    const searchQuery = ref('')
    const filterType = ref(null)
    const filterStatus = ref('active')
    const dialogOpen = ref(false)
    const deleteDialogOpen = ref(false)
    const editingCustomer = ref(null)
    const deletingCustomer = ref(null)
    const formRef = ref(null)

    // Snackbar state
    const snackbar = ref({
      show: false,
      message: '',
      color: 'error',
      timeout: 5000
    })

    const showSnackbar = (message, color = 'error') => {
      snackbar.value.message = message
      snackbar.value.color = color
      snackbar.value.show = true
    }

    const formData = ref({
      company_name: '',
      display_name: '',
      customer_type: 'advertiser',
      tier: 'standard',
      industry: '',
      contact_name: '',
      contact_email: '',
      contact_phone: '',
      contact_title: '',
      billing_email: '',
      billing_address: '',
      notes: ''
    })

    // Options
    const typeOptions = [
      { title: 'Advertiser', value: 'advertiser' },
      { title: 'Sponsor', value: 'sponsor' },
      { title: 'Partner', value: 'partner' }
    ]

    const tierOptions = [
      { title: 'Premium', value: 'premium' },
      { title: 'Standard', value: 'standard' },
      { title: 'Basic', value: 'basic' }
    ]

    const statusOptions = [
      { title: 'Active', value: 'active' },
      { title: 'Inactive', value: 'inactive' },
      { title: 'All', value: 'all' }
    ]

    const headers = [
      { title: 'Company', key: 'company_name', sortable: true },
      { title: 'Type', key: 'customer_type', sortable: true, width: 120 },
      { title: 'Tier', key: 'tier', sortable: true, width: 100 },
      { title: 'Contact', key: 'contact_name', sortable: true },
      { title: 'Email', key: 'contact_email', sortable: false },
      { title: 'Active', key: 'is_active', sortable: true, width: 80 },
      { title: 'Actions', key: 'actions', sortable: false, width: 140 }
    ]

    // Auth helper
    const getAuthHeaders = () => {
      const token = localStorage.getItem('auth-token')
      return token ? { 'Authorization': `Bearer ${token}` } : {}
    }

    // Computed
    const filteredCustomers = computed(() => {
      let items = [...customers.value]

      if (filterStatus.value === 'active') {
        items = items.filter(c => c.is_active)
      } else if (filterStatus.value === 'inactive') {
        items = items.filter(c => !c.is_active)
      }

      if (filterType.value) {
        items = items.filter(c => c.customer_type === filterType.value)
      }

      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        items = items.filter(c =>
          c.company_name?.toLowerCase().includes(query) ||
          c.contact_name?.toLowerCase().includes(query) ||
          c.contact_email?.toLowerCase().includes(query)
        )
      }

      return items
    })

    // Methods
    const loadCustomers = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/customers/', {
          headers: getAuthHeaders(),
          params: { is_active: null, limit: 500 }
        })
        customers.value = response.data.customers || []
      } catch (error) {
        console.error('Failed to load customers:', error)
      } finally {
        loading.value = false
      }
    }

    const openCreateDialog = () => {
      editingCustomer.value = null
      formData.value = {
        company_name: '',
        display_name: '',
        customer_type: 'advertiser',
        tier: 'standard',
        industry: '',
        contact_name: '',
        contact_email: '',
        contact_phone: '',
        contact_title: '',
        billing_email: '',
        billing_address: '',
        notes: ''
      }
      dialogOpen.value = true
    }

    const editCustomer = (customer) => {
      editingCustomer.value = customer
      formData.value = { ...customer }
      dialogOpen.value = true
    }

    const saveCustomer = async () => {
      if (!formData.value.company_name) {
        return
      }

      saving.value = true
      try {
        if (editingCustomer.value) {
          await axios.patch(`/api/customers/${editingCustomer.value.asset_id}`, formData.value, {
            headers: getAuthHeaders()
          })
        } else {
          await axios.post('/api/customers/', formData.value, {
            headers: getAuthHeaders()
          })
        }
        dialogOpen.value = false
        await loadCustomers()
      } catch (error) {
        console.error('Failed to save customer:', error)
        showSnackbar(`Failed to save: ${error.response?.data?.detail || error.message}`)
      } finally {
        saving.value = false
      }
    }

    const toggleActive = async (customer) => {
      try {
        await axios.patch(`/api/customers/${customer.asset_id}`, {
          is_active: !customer.is_active
        }, {
          headers: getAuthHeaders()
        })
        await loadCustomers()
      } catch (error) {
        console.error('Failed to toggle customer:', error)
      }
    }

    const confirmDelete = (customer) => {
      deletingCustomer.value = customer
      deleteDialogOpen.value = true
    }

    const deleteCustomer = async () => {
      if (!deletingCustomer.value) return

      deleting.value = true
      try {
        await axios.delete(`/api/customers/${deletingCustomer.value.asset_id}`, {
          headers: getAuthHeaders(),
          params: { hard_delete: true }
        })
        deleteDialogOpen.value = false
        deletingCustomer.value = null
        await loadCustomers()
      } catch (error) {
        console.error('Failed to delete customer:', error)
        showSnackbar(`Failed to delete: ${error.response?.data?.detail || error.message}`)
      } finally {
        deleting.value = false
      }
    }

    const formatType = (type) => {
      if (!type) return ''
      return type.charAt(0).toUpperCase() + type.slice(1)
    }

    const getTypeColor = (type) => {
      const colors = {
        advertiser: 'green',
        sponsor: 'purple',
        partner: 'blue'
      }
      return colors[type] || 'grey'
    }

    const getTierColor = (tier) => {
      const colors = {
        premium: 'amber',
        standard: 'blue-grey',
        basic: 'grey'
      }
      return colors[tier] || 'grey'
    }

    // Lifecycle
    onMounted(() => {
      loadCustomers()
    })

    return {
      loading,
      saving,
      deleting,
      customers,
      searchQuery,
      filterType,
      filterStatus,
      dialogOpen,
      deleteDialogOpen,
      editingCustomer,
      deletingCustomer,
      formRef,
      formData,
      typeOptions,
      tierOptions,
      statusOptions,
      headers,
      filteredCustomers,
      openCreateDialog,
      editCustomer,
      saveCustomer,
      toggleActive,
      confirmDelete,
      deleteCustomer,
      formatType,
      getTypeColor,
      getTierColor,
      snackbar,
      showSnackbar
    }
  }
}
</script>

<style scoped>
.customer-manager {
  max-width: 1200px;
}
</style>
