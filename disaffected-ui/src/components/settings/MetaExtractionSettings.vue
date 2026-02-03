<template>
  <v-card variant="outlined" class="mb-4">
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-brain</v-icon>
      Meta Extraction Settings
    </v-card-title>
    <v-card-subtitle>
      Configure which rundown item types are eligible for LLM metadata extraction
    </v-card-subtitle>
    <v-divider />
    <v-card-text>
      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        Select which item types should appear in the MetaFactory extraction tool.
        Unselected types will be hidden from the extraction list.
      </v-alert>

      <div class="text-subtitle-2 mb-2">Eligible Item Types</div>

      <v-row>
        <v-col
          v-for="itemType in allItemTypes"
          :key="itemType.value"
          cols="12"
          sm="6"
          md="4"
        >
          <v-checkbox
            v-model="selectedTypes"
            :value="itemType.value"
            :label="itemType.title"
            density="compact"
            hide-details
            class="item-type-checkbox"
          >
            <template v-slot:label>
              <div class="d-flex align-center">
                <v-icon :color="itemType.color" size="small" class="mr-2">
                  {{ itemType.icon }}
                </v-icon>
                <span>{{ itemType.title }}</span>
              </div>
            </template>
          </v-checkbox>
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <div class="d-flex align-center ga-2">
        <v-btn
          color="primary"
          variant="flat"
          @click="saveSettings"
          :loading="saving"
          :disabled="!hasChanges"
        >
          Save Changes
        </v-btn>
        <v-btn
          variant="tonal"
          @click="resetToDefaults"
          :disabled="saving"
        >
          Reset to Defaults
        </v-btn>
        <v-spacer />
        <v-chip
          v-if="hasChanges"
          color="warning"
          variant="tonal"
          size="small"
        >
          Unsaved changes
        </v-chip>
        <v-chip
          v-else-if="lastSaved"
          color="success"
          variant="tonal"
          size="small"
        >
          Saved
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { CORE_ITEM_TYPES } from '@/config/itemTypes'
import axios from 'axios'

export default {
  name: 'MetaExtractionSettings',

  setup() {
    // All available item types from the config
    const allItemTypes = ref([...CORE_ITEM_TYPES])

    // Currently selected types
    const selectedTypes = ref([])

    // Original types (for change detection)
    const originalTypes = ref([])

    // Default types from API
    const defaultTypes = ref([])

    // State
    const loading = ref(false)
    const saving = ref(false)
    const lastSaved = ref(false)

    // Computed
    const hasChanges = computed(() => {
      if (selectedTypes.value.length !== originalTypes.value.length) return true
      return !selectedTypes.value.every(t => originalTypes.value.includes(t))
    })

    // Methods
    function getAuthHeaders() {
      const token = localStorage.getItem('auth-token')
      return token ? { 'Authorization': `Bearer ${token}` } : {}
    }

    async function loadSettings() {
      loading.value = true
      try {
        const response = await axios.get('/api/settings/meta_extraction', {
          headers: getAuthHeaders()
        })

        if (response.data?.item_types) {
          selectedTypes.value = [...response.data.item_types]
          originalTypes.value = [...response.data.item_types]
        }

        if (response.data?.defaults) {
          defaultTypes.value = [...response.data.defaults]
        }
      } catch (error) {
        console.error('Failed to load meta extraction settings:', error)
      } finally {
        loading.value = false
      }
    }

    async function saveSettings() {
      saving.value = true
      lastSaved.value = false
      try {
        await axios.post('/api/settings/meta_extraction', {
          item_types: selectedTypes.value
        }, {
          headers: getAuthHeaders()
        })

        originalTypes.value = [...selectedTypes.value]
        lastSaved.value = true

        // Auto-hide saved indicator after 3 seconds
        setTimeout(() => {
          lastSaved.value = false
        }, 3000)
      } catch (error) {
        console.error('Failed to save meta extraction settings:', error)
      } finally {
        saving.value = false
      }
    }

    function resetToDefaults() {
      selectedTypes.value = [...defaultTypes.value]
    }

    onMounted(() => {
      loadSettings()
    })

    return {
      allItemTypes,
      selectedTypes,
      defaultTypes,
      loading,
      saving,
      lastSaved,
      hasChanges,
      loadSettings,
      saveSettings,
      resetToDefaults
    }
  }
}
</script>

<style scoped>
.item-type-checkbox {
  margin-bottom: 4px;
}
</style>
