<template>
  <v-container fluid class="reusables-studio pa-4">
    <v-row no-gutters>
      <!-- Main List Panel -->
      <v-col :cols="editorOpen ? 6 : 12" class="transition-all">
        <v-card class="h-100">
          <v-card-title class="d-flex align-center py-3">
            <v-icon class="mr-2" color="primary">mdi-content-copy</v-icon>
            <span>Reusables Studio</span>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="createNewItem">
              <v-icon class="mr-1">mdi-plus</v-icon>
              New Item
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Filters -->
            <v-row class="mb-4" dense>
              <v-col cols="4">
                <v-select
                  v-model="filterType"
                  label="Type"
                  :items="typeOptions"
                  clearable
                  variant="outlined"
                  density="compact"
                  hide-details
                ></v-select>
              </v-col>
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
                  v-model="filterStatus"
                  label="Status"
                  :items="statusOptions"
                  variant="outlined"
                  density="compact"
                  hide-details
                ></v-select>
              </v-col>
            </v-row>

            <!-- Library Items Table -->
            <v-data-table
              :headers="tableHeaders"
              :items="filteredItems"
              :loading="loading"
              class="elevation-1"
              density="compact"
              hover
              @click:row="handleRowClick"
            >
              <template #[`item.item_type`]="{ item }">
                <v-chip :color="getTypeColor(item.item_type)" size="small" label>
                  {{ formatTypeName(item.item_type) }}
                </v-chip>
              </template>

              <template #[`item.title`]="{ item }">
                <span :class="{ 'font-weight-bold': selectedItem?.asset_id === item.asset_id }">
                  {{ item.title }}
                </span>
              </template>

              <template #[`item.is_active`]="{ item }">
                <v-icon :color="item.is_active ? 'success' : 'grey'" size="small">
                  {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                </v-icon>
              </template>

              <template #[`item.valid_range`]="{ item }">
                <span class="text-caption">
                  {{ formatDateRange(item.valid_from, item.valid_until) }}
                </span>
              </template>

              <template #[`item.placement_count`]="{ item }">
                <v-chip v-if="item.placement_count > 0" color="primary" size="x-small">
                  {{ item.placement_count }}
                </v-chip>
                <span v-else class="text-grey-darken-1">-</span>
              </template>

              <template #[`item.actions`]="{ item }">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click.stop="editItem(item)"
                  title="Edit"
                >
                  <v-icon size="small">mdi-pencil</v-icon>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click.stop="viewUsage(item)"
                  title="View Usage"
                >
                  <v-icon size="small">mdi-history</v-icon>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click.stop="toggleItemActive(item)"
                  :title="item.is_active ? 'Deactivate' : 'Activate'"
                >
                  <v-icon size="small" :color="item.is_active ? 'grey' : 'success'">
                    {{ item.is_active ? 'mdi-eye-off' : 'mdi-eye' }}
                  </v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Slide-Out Editor Panel -->
      <v-col v-if="editorOpen" cols="6" class="pl-2">
        <ReusablesStudioEditor
          :item="selectedItem"
          :isNew="isNewItem"
          @close="closeEditor"
          @saved="handleItemSaved"
          @deleted="handleItemDeleted"
        />
      </v-col>
    </v-row>

    <!-- Usage History Dialog -->
    <v-dialog v-model="usageDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-history</v-icon>
          Usage History: {{ usageItem?.title }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="!usageHistory.length" type="info" variant="tonal">
            This item has not been placed in any rundowns yet.
          </v-alert>
          <v-list v-else density="compact">
            <v-list-item
              v-for="placement in usageHistory"
              :key="placement.id"
              :class="{ 'text-decoration-line-through': placement.removed_at }"
            >
              <template #prepend>
                <v-icon :color="placement.removed_at ? 'grey' : 'success'" size="small">
                  {{ placement.removed_at ? 'mdi-close-circle' : 'mdi-check-circle' }}
                </v-icon>
              </template>
              <v-list-item-title>
                Episode {{ placement.episode_number }}
              </v-list-item-title>
              <v-list-item-subtitle>
                Placed: {{ formatDateTime(placement.placed_at) }}
                <span v-if="placement.removed_at" class="text-error">
                  | Removed: {{ formatDateTime(placement.removed_at) }}
                </span>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="usageDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create New Item Dialog -->
    <v-dialog v-model="createDialog" max-width="400">
      <v-card>
        <v-card-title>Create New Reusable Item</v-card-title>
        <v-card-text>
          <v-select
            v-model="newItemType"
            label="Item Type"
            :items="reusableTypeOptions"
            variant="outlined"
            density="compact"
          ></v-select>
          <v-text-field
            v-model="newItemTitle"
            label="Title"
            variant="outlined"
            density="compact"
            class="mt-2"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="createDialog = false">Cancel</v-btn>
          <v-btn color="primary" :disabled="!newItemType || !newItemTitle" @click="confirmCreateItem">
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import ReusablesStudioEditor from '@/components/settings/ReusablesStudioEditor.vue'
import axios from 'axios'

export default {
  name: 'ReusablesStudioView',
  components: {
    ReusablesStudioEditor
  },
  setup() {
    // Data
    const loading = ref(false)
    const libraryItems = ref([])
    const typeSettings = ref([])

    // Filters
    const filterType = ref(null)
    const searchQuery = ref('')
    const filterStatus = ref('active')

    // Editor state
    const editorOpen = ref(false)
    const selectedItem = ref(null)
    const isNewItem = ref(false)

    // Create dialog
    const createDialog = ref(false)
    const newItemType = ref('')
    const newItemTitle = ref('')

    // Usage dialog
    const usageDialog = ref(false)
    const usageItem = ref(null)
    const usageHistory = ref([])

    // Computed
    const typeOptions = computed(() => {
      const types = [...new Set(libraryItems.value.map(item => item.item_type))]
      return types.map(type => ({
        title: formatTypeName(type),
        value: type
      }))
    })

    const reusableTypeOptions = computed(() => {
      return typeSettings.value
        .filter(ts => ts.is_reusable)
        .map(ts => ({
          title: ts.display_name,
          value: ts.type_name
        }))
    })

    const statusOptions = [
      { title: 'Active', value: 'active' },
      { title: 'All', value: 'all' },
      { title: 'Inactive', value: 'inactive' }
    ]

    const tableHeaders = [
      { title: 'Type', key: 'item_type', width: '120px' },
      { title: 'Title', key: 'title' },
      { title: 'Customer', key: 'customer_name', width: '150px' },
      { title: 'Duration', key: 'duration', width: '80px' },
      { title: 'Valid Range', key: 'valid_range', width: '180px' },
      { title: 'Used', key: 'placement_count', width: '60px', align: 'center' },
      { title: 'Active', key: 'is_active', width: '60px', align: 'center' },
      { title: 'Actions', key: 'actions', width: '120px', sortable: false }
    ]

    const filteredItems = computed(() => {
      let items = [...libraryItems.value]

      // Filter by type
      if (filterType.value) {
        items = items.filter(item => item.item_type === filterType.value)
      }

      // Filter by status
      if (filterStatus.value === 'active') {
        items = items.filter(item => item.is_active)
      } else if (filterStatus.value === 'inactive') {
        items = items.filter(item => !item.is_active)
      }

      // Filter by search
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        items = items.filter(item =>
          item.title?.toLowerCase().includes(query) ||
          item.customer_name?.toLowerCase().includes(query)
        )
      }

      return items
    })

    // Helper for auth headers
    const getAuthHeaders = () => {
      const token = localStorage.getItem('auth-token')
      return token ? { 'Authorization': `Bearer ${token}` } : {}
    }

    // Methods
    const loadLibraryItems = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/content-library/', {
          headers: getAuthHeaders(),
          params: {
            is_active: filterStatus.value === 'active' ? true : null,
            limit: 500
          }
        })
        libraryItems.value = response.data.items || []
      } catch (error) {
        console.error('Failed to load library items:', error)
      } finally {
        loading.value = false
      }
    }

    const loadTypeSettings = async () => {
      try {
        const response = await axios.get('/api/content-library/type-settings/', {
          headers: getAuthHeaders()
        })
        typeSettings.value = response.data.settings || []
      } catch (error) {
        console.error('Failed to load type settings:', error)
      }
    }

    const formatTypeName = (typeName) => {
      if (!typeName) return ''
      return typeName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
    }

    const getTypeColor = (typeName) => {
      const colorMap = {
        advertisement: 'green',
        promo: 'purple',
        cta: 'orange',
        transition: 'blue-grey',
        segment: 'blue',
        interview: 'teal'
      }
      return colorMap[typeName] || 'grey'
    }

    const formatDateRange = (from, until) => {
      if (!from && !until) return 'Always valid'
      const formatDate = (dateStr) => {
        if (!dateStr) return ''
        return new Date(dateStr).toLocaleDateString()
      }
      if (from && until) return `${formatDate(from)} - ${formatDate(until)}`
      if (from) return `From ${formatDate(from)}`
      if (until) return `Until ${formatDate(until)}`
      return ''
    }

    const formatDateTime = (dateStr) => {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleString()
    }

    const handleRowClick = (event, { item }) => {
      editItem(item)
    }

    const editItem = async (item) => {
      try {
        // Fetch full item data including script_content and scratch_content
        const response = await axios.get(`/api/content-library/${item.asset_id}`, {
          headers: getAuthHeaders()
        })
        selectedItem.value = response.data
        isNewItem.value = false
        editorOpen.value = true
      } catch (error) {
        console.error('Failed to load item:', error)
      }
    }

    const createNewItem = () => {
      newItemType.value = ''
      newItemTitle.value = ''
      createDialog.value = true
    }

    const confirmCreateItem = async () => {
      try {
        const response = await axios.post('/api/content-library/', {
          item_type: newItemType.value,
          title: newItemTitle.value,
          script_content: '',
          duration: '00:00:30'
        }, {
          headers: getAuthHeaders()
        })

        createDialog.value = false

        // Reload and open the new item
        await loadLibraryItems()
        const newItem = libraryItems.value.find(i => i.asset_id === response.data.asset_id)
        if (newItem) {
          editItem(newItem)
        }
      } catch (error) {
        console.error('Failed to create item:', error)
        console.error('Response:', error.response?.data)
        console.error('Token present:', !!localStorage.getItem('auth-token'))
        alert(`Failed to create item: ${error.response?.data?.detail || error.message}`)
      }
    }

    const closeEditor = () => {
      editorOpen.value = false
      selectedItem.value = null
      isNewItem.value = false
    }

    const handleItemSaved = async () => {
      await loadLibraryItems()
    }

    const handleItemDeleted = async () => {
      closeEditor()
      await loadLibraryItems()
    }

    const viewUsage = async (item) => {
      usageItem.value = item
      try {
        const response = await axios.get(`/api/content-library/${item.asset_id}/usage`, {
          headers: getAuthHeaders()
        })
        usageHistory.value = response.data.placements || []
        usageDialog.value = true
      } catch (error) {
        console.error('Failed to load usage:', error)
        usageHistory.value = []
      }
    }

    const toggleItemActive = async (item) => {
      try {
        await axios.patch(`/api/content-library/${item.asset_id}`, {
          is_active: !item.is_active
        }, {
          headers: getAuthHeaders()
        })
        await loadLibraryItems()
      } catch (error) {
        console.error('Failed to toggle item:', error)
      }
    }

    // Lifecycle
    onMounted(() => {
      loadLibraryItems()
      loadTypeSettings()
    })

    return {
      // Data
      loading,
      libraryItems,
      typeSettings,
      filterType,
      searchQuery,
      filterStatus,
      editorOpen,
      selectedItem,
      isNewItem,
      createDialog,
      newItemType,
      newItemTitle,
      usageDialog,
      usageItem,
      usageHistory,
      // Computed
      typeOptions,
      reusableTypeOptions,
      statusOptions,
      tableHeaders,
      filteredItems,
      // Methods
      formatTypeName,
      getTypeColor,
      formatDateRange,
      formatDateTime,
      handleRowClick,
      editItem,
      createNewItem,
      confirmCreateItem,
      closeEditor,
      handleItemSaved,
      handleItemDeleted,
      viewUsage,
      toggleItemActive
    }
  }
}
</script>

<style scoped>
.reusables-studio {
  height: calc(100vh - 64px);
}

.transition-all {
  transition: all 0.3s ease;
}

.h-100 {
  height: 100%;
}
</style>
